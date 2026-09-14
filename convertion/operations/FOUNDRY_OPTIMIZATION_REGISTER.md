# Foundry Optimization Register — repo analysed against the 2026 research

What this is: the whole kit read against the research decision record in
`../enterprise/ENTERPRISE_BLUEPRINT.md` §2 (LZ/PRJ/ORC/MDL/STO/NET/CMK/ID/RAI/
SEC/PUR/LOG/POL/COST/SP/CP/API/MEM) and the platform's own runtime behaviour,
looking for one thing: **where does this platform spend more than it needs to,
and where does spending less cost accuracy?**

Every finding carries the evidence that produced it, so the next reviewer can
re-run the check rather than re-derive the judgement. Findings that were
examined and needed no change are recorded too — an empty row is not proof
that nobody looked.

Analysed: 2026-09-13, against the kit at that date.
Review cadence: with the monthly tier-tuning loop
(`../governance/MODEL_ROUTING.md` §Token-economy rules 7).

## 1. Applied in this pass

### F1 — Evidence was re-read in full at every reassessment (requirement d2)

**Finding.** `tpa-evidence-analyzer` is the heaviest recurring run in the
platform: a whole supplier tree under `Infosec Assurance/GRC/TPA/Active` read
on the reasoning tier (`reasoning_effort: high`) with the chunked
full-coverage method. Between two assessments of the same supplier almost none
of those files change — a certificate issued last year is the same bytes this
quarter — yet every reassessment re-read all of them.

**Applied.** Delta re-analysis, keyed on the SharePoint **eTag**:

| Piece | Where |
|---|---|
| Read side (agent tool, GET) | `GET /api/evidence_cache`, spec `../integrations/openapi/evidence-cache.yaml`, attached read-only to the analyzer |
| Write side (pipeline, post-approval) | `POST /api/evidence_cache` from `If_evidence_cache_records` in `../workflows/report-delivery-pipeline.json` |
| Store | SharePoint list `TPA Evidence Cache` (`../sharepoint/README.md`), written only by the delivery Function |
| Contract | `cacheRecords` in `../templates/evidence_summary.schema.json` |
| Rules | `../agents/tpa-evidence-analyzer_instructions.md` §"Evidence already extracted" |

**Why it cannot go stale, and why it cannot launder a draft:**

- Three invalidations: changed eTag (the file moved), changed `ExtractorRef`
  (a newer charter reads documents differently), and age
  (`EVIDENCE_CACHE_MAX_AGE_DAYS`, default 180 — nothing is trusted forever).
- **No time-dependent value is cached.** VALID / EXPIRING ≤90 days / EXPIRED /
  period-gap are recomputed against each report date. A certificate valid in
  March is not valid in September, and a cached status would quietly assert
  that it is.
- The write happens **after** the verifier passes and a human approves, so an
  unapproved extraction can never enter the cache and be reused later.
- A cached finding that would drive a HIGH or CRITICAL verdict must be
  re-read before it decides anything (charter rule 5): the cheap path does not
  get to settle an expensive question.
- Every inventory row says `fresh` or `reused:<runId>`, so the approver signs
  off on evidence whose provenance they can see.

**Effect.** A reassessment costs the delta, not the tree. The saving scales
with how static the evidence is, and the run reports its own reuse ratio, so
the effect is measured rather than assumed.

### F2 — Agents ran on service defaults

No agent set a temperature, reasoning effort, output ceiling or retrieval
width. Applied: `../governance/INFERENCE_PROFILES.md` +
`../integrations/inference-profiles.json`, resolved per model family and
applied at agent save, tier application and per request. Scoring and
extraction agents now sample at 0.0 (reproducible), routing spends `low`
effort, advisory keeps `high`. CI gate `[4c2]`.

### F3 — 365 days of *interactive* log retention for tables nothing queries

Nothing queries beyond 30 days. Applied: interactive 90 days,
`totalRetentionInDays` 365 per evidence table (archive ≈ a tenth of the
price). The DORA Art. 28 horizon is unchanged. The ingestion cap stays **off**
deliberately — a cap drops telemetry, including the `AppDependencies` the
egress detector reads. `../operations/OPTIMIZATION_REVIEW.md` §2.

### F4 — Two `Foreach` loops with no concurrency bound

A Logic Apps `Foreach` defaults to 20 parallel branches; `jira-finding-sync`
and the `mailbox-intake` attachment loop ran unbounded against rate-limited
APIs, so the excess came back as 429s the connector retried — slower *and*
dearer than two steady branches. Bounded, documented per limit, and guarded by
CI gate `[4b2]` (`../ci/tests/test_workflow_efficiency.py`).

### F5 — CI re-downloaded its toolchain and re-resolved pip mid-job

Pip wheels and the pinned Bicep CLI are cached across runs; dependencies
install once. The full skill conversion still runs on every PR **on purpose**:
it is the byte-fidelity proof, and caching it would cache away the check.

## 2. Examined, already optimal — no change made

| # | Checked | Evidence | Why no change |
|---|---|---|---|
| F6 | Deliverable pipeline control flow | `report-delivery-pipeline.json`: `Until_agent_run_completes` (30 s poll, 2 h cap), `Until_verifier_completes` (10 s, 30 min) | Single pass: a verifier FAIL notifies and stops, it never re-runs the producing agent. There is no regeneration loop to bound, and polling at 30 s costs ~10–40 actions on a run that takes minutes |
| F7 | Read-only enforcement cost | `attach_integrations.py` `READ_ONLY_POST_OPS` | Non-GET operations are stripped at attach time; the five survivors are query operations (JQL, AQL, KQL hunting, Graph search, code search) that would otherwise force a far more expensive enumerate-then-filter pattern |
| F8 | Rendering path | delivery Function renderers | Already deterministic code, never token-generated: a delivered file costs zero completion tokens |
| F9 | Vector stores | one per agent | A service limit, not a choice; the combined store is reached by hand-off |
| F10 | Upload path | `_azure_helpers.UploadCache` | Already deduplicates by content hash across deploys |
| F11 | Entra tokens in the delivery Function | `azure-identity` | The credential caches and refreshes per instance; a hand-rolled cache would add a second expiry to get wrong |
| F12 | delivery vs office-tools image split | both Dockerfiles | The poppler/tesseract duplication is deliberate and documented — pulling LibreOffice into the delivery image was the reason for the split |

## 3. Open, with a decision

| # | Finding | Evidence | Decision |
|---|---|---|---|
| F13 | **Two of three tiers run Legacy/Deprecated model versions.** `gpt-4o 2024-11-20` is Legacy and `gpt-4o-mini 2024-07-18` Deprecated; both retire **2027-04-14** | `python3 ../enterprise/upgrade/check_model_lifecycle.py --dry-run` → 2 INFO rows, 213 days | Not a blind swap: report agents were validated against known-good outputs. Run the six-phase migration (policy R3: freeze golden set → candidate deployment → `run_evals.py --model-override` → comparison set → staged switch) at the next currency review, well inside the 213 days. The checker already escalates INFO → WARN → error as the date approaches |
| F14 | **`o4-mini` retirement date not captured** — a standing WARN | same run: `RETIREMENT-DATE-UNKNOWN (reasoning)` | Capture the date from the retirement schedule at the next currency review, or record a dated exception. A warning that never resolves stops being read |
| F15 | **Knowledge is per-agent vector stores; the research target state is Azure AI Search / Foundry IQ** | `KNOWLEDGE_SOURCE=vector-store` in `../setup/.env.example`; MEM-1 | Switching changes retrieval quality in both directions. Gate it on measurement: run the golden set under both settings and switch on evidence, not on the target-state label |
| F16 | **Bing Custom Search (domain allow-list) never evaluated** (research NET-3) | `ENTERPRISE_BLUEPRINT.md` NET-3 "evaluate for OSINT agents" | Worth doing for three reasons at once: fewer junk results (tokens), better sourcing (accuracy) and a narrower egress surface (the DPA gap in NET-3). Preview status — pilot in `test` per series/00 D8 before any production change |
| F17 | **Basic-logs tier for `FunctionAppLogs`; sampling of `AppTraces`** | `FINOPS.md` C6 | Both are now safe because the token queries are `ItemCount`-weighted, but neither has been measured against real ingestion volume. Tuning a tier on a guess is how evidence goes missing — decide with a month of actuals |

## 4. Control mapping

| Control | Evidence in this register |
|---|---|
| ISO/IEC 27001:2022 A.8.6 — capacity | F2 output ceilings, F4 bounded loops, F3 ingestion posture |
| ISO/IEC 27001:2022 A.8.15 — logging | F3 retention split keeps the full evidence horizon; the cap stays off |
| ISO/IEC 27001:2022 A.5.23 — cloud services | F1 reuse is bounded by approval and provenance, not by convenience |
| ISO/IEC 42001:2023 A.6.2.4 — AI system operation | F2 documented operating parameters; F13/F14 model lifecycle under a gate |
| DORA Art. 9(2) / Art. 28 | F3 resource use and ≥ 1 year ICT evidence; F1 keeps the evidence trail auditable per file |
| EU AI Act Art. 26(1) — deployer duty | F2/F13 parameters and model changes are declared, reviewed and evidenced |
