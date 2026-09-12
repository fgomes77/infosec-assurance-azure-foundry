# Token Economy Playbook — Operating MODEL_ROUTING Rule 7 Without Losing Accuracy

The procedure behind `../governance/MODEL_ROUTING.md` rule 7 ("monitor and
tune") and its accuracy floor. It tells the owner how to move an agent
between the `light` / `chat` / `reasoning` tiers, size retrieval, keep
outputs single-pass, cache what can be cached and batch what can wait —
and which test must pass **before** any downgrade. Cost figures are in
`FINOPS.md` §2; the test harness is `evaluation/run_evals.py` against
`evaluation/golden-set.*.json` (`evaluation/EVALUATION.md`).

Invariants the playbook can never touch: the advisory pin (g/h/i agents
stay on `reasoning`), the verifier pass, the human approval gate, content
recording in tracing, EU Data Zone SKUs, read-only tools. Every lever below
is a Tier C platform change (`../team/TEAM_MODEL.md` §12.1; deputy reviews
what the owner authored) executed through `CHANGE_MANAGEMENT.md` §3 — the
portal is never edited by hand. Control: ISO 42001 A.6.2.4 (verification
and validation before deployment), A.6.2.6; ISO 27001:2022 A.8.32, A.8.29;
EU AI Act Art. 9(6)–(8), 26(5); DORA Art. 9(4)(e).

## 1. The tier-tuning loop (monthly, owner)

| Step | What | Evidence / tool | Exit criterion |
|---|---|---|---|
| 1 Observe | Per-agent tokens, € per deliverable, p95 latency, verifier first-pass PASS rate, 429s | `kql/latency-and-tokens.kql` (full table), `kql/verifier-fail-rate.kql`, `../infra/kql/tokens-per-agent.kql`, `FINOPS.md` §6 steps 2–4 | table filed in `Governance/Operations/{yyyy}-{mm}/finops.md` |
| 2 Classify | Each agent → *hold*, *down-candidate*, *up-candidate*, *fix-first* (§2) | this playbook §2 rules | list in `finops.md` |
| 3 Fix-first | Before any tier move: RAG sizing (§3), single-pass contract (§4), chunking, tool-loop guard, caching (§5) | PR with the change; `deploy.sh --dry-run` | tokens per run drop ≥ 20 % **or** the cause is confirmed to be model capability |
| 4 Accuracy-floor test | Run the golden set for the agent on the candidate tier (§7; `EVALUATION.md` gate G1) | `run_evals.py --only <cases> --report …` JSON + md attached to the PR | every metric ≥ its floor; verifier PASS on first attempt for every case |
| 5 Stage | Change `model_tier` for **one** agent; `attach_integrations.py --only <agent>`; observe one week | `CHANGE_MANAGEMENT.md` §1 "Model tier / capacity" (staged rollout) | PASS rate and rework unchanged vs the prior 4 weeks; no new FM-08 |
| 6 Commit or roll back | Keep (registry stays), or revert the tier (same PR path) | ticket closed with the two observation windows | `MODEL_ROUTING.md` table updated if the tier changed for a named agent |

Time box: one agent per month per direction, so an accuracy regression is
attributable. Emergency direction (up-tier after an FM-08 verifier FAIL
spike) skips step 4 but not step 5's observation.

## 2. Classification rules per agent

| Class | Rule | Action |
|---|---|---|
| **Pinned** | agent ∈ `advisory_read_only_toolset.agents` (`../integrations/registry.json`): `iso27001`, `iso42001`, `dora`, `nis2`, `eu-ai-act`, `cyber-forum`, `tpsrca-assessment-engine`, `enx-tprm-control-center`, `infosec-assurance-advisor`; plus `infosec-assurance-orchestrator` and `output-verifier` | never down; economy from §3–§5 only |
| **Down-candidate** | non-pinned; first-pass PASS ≥ 95 % over 8 weeks; ≥ 20 runs; token share ≥ 5 % of the month **or** € per deliverable ≥ 2× its `FINOPS.md` §2 row; output is template-bound (fixed schema, renderer does the layout) | §7 test on the next tier down; then loop steps 5–6 |
| **Up-candidate** | first-pass PASS < 85 % or rework (approver edits) > 20 % over 4 weeks, after fix-first; or loops (> 3 tool rounds median) on `chat` | move up one tier; observe; add golden cases for the failure pattern |
| **Fix-first** | tokens per run > 2× the row in `FINOPS.md` §2 with PASS rate fine | §3/§4/§5 before any tier decision |
| **Hold** | everything else | nothing |

Today's registry has one `light` agent (`xlsx`), eleven `chat` and the rest
`reasoning`. Realistic down-candidates after fix-first are `docx`, `pdf`,
`pptx` (document agents, chat → light: their instructions are deterministic
transformation) and, only with a full G1 pass, `ciso-executive-summary`
(chat → light is **not** expected to pass — the extraction rules need
judgement; keep on chat). `dpia`, `ciso-reporting`, `onetrust-form-b`,
`template-manager` stay on chat: their known-good outputs were validated
there (`MODEL_ROUTING.md` accuracy floor).

## 3. RAG sizing (file_search)

Retrieval, not the model, is the first lever for reasoning-tier cost.

| Parameter | Where | Default | Rule |
|---|---|---|---|
| Chunk size / overlap | vector store creation (`../scripts/create_agents.py`, `create_orchestrator.py`) | platform default (≈ 800 tokens / 400 overlap) | keep; regulatory texts need whole-article chunks — smaller chunks raise citation errors (EVALUATION metric *citation validity*) |
| `max_num_results` | `file_search` tool options per agent | platform default (up to 20 on gpt-4o-class) | set **8** for advisors, **5** for report agents; re-run G1; raise only if *grounding rate* falls |
| Ranking threshold | `file_search` ranking options | none | set a score threshold (≈ 0.5) so off-topic chunks are dropped instead of padded |
| Knowledge pack size | `../agents/advisor-knowledge/*.md`, per-skill `references/` | as converted | one store per agent (already); no catalogue duplicated across stores — the upload cache dedupes byte-identical files (`_azure_helpers.UploadCache`), not semantic duplicates |
| Memory recall | `vs-assurance-memory` via `search_memory` / advisor `MEMORY:` block | all notes | retention per `TEAM_MODEL.md` §13 (W5 check); stale notes are tokens on every turn |
| Combined advisor store | `infosec-assurance-advisor` | all 18 TPRM skills' knowledge | keep, but route framework-specific questions to the framework advisor (orchestrator restraint, rule 5) |

Measure before/after with `kql/latency-and-tokens.kql`: input tokens per
run is the RAG signal; output tokens are the contract signal (§4).

## 4. Single-pass output contracts

| Rule | Implementation | Check |
|---|---|---|
| One structured block per deliverable, sized to the renderer schema | agent instructions (`../agents/*_instructions.md`, addenda from `convert_skills.py`) | `run_evals.py` metric *format* (JSON parses / required sections) |
| No conversational padding in pipeline runs | pipelines pass the trigger payload only; the APPROVAL GATE block asks for the draft, not a narrative | output tokens per run ≈ `FINOPS.md` §2 row |
| No self-repair loops | on verifier FAIL the pipeline returns the findings **once** to the producer (`Notify_verifier_fail`); a second FAIL goes to the requester | `kql/verifier-fail-rate.kql`; FM-08 |
| Deterministic rendering | DOCX/PPTX/XLSX/HTML bytes come from `functions/delivery` or code_interpreter scripts — zero completion tokens | `verify_conversion.py` byte checks; baseline sha256 in the golden set |
| Chunked long inputs | `pdf-full-coverage-analyzer` method: bounded chunks, per-chunk extraction, one synthesis | input tokens scale linearly with pages, not quadratically |

## 5. Caching — what is cached, what never is

| Cache | Mechanism | Saves | Constraint |
|---|---|---|---|
| Prompt prefix cache (Azure OpenAI automatic caching of repeated ≥ 1 024-token prefixes) | keep the persona preamble + instructions + APPROVAL GATE block **first and stable**; put per-request content last | discounted input tokens on every run of the same agent | changes to the preamble invalidate it for all agents — batch instruction edits into one release |
| Upload cache | `build/upload-cache.json` (`_azure_helpers.UploadCache`, sha256 → file id) | re-uploads and duplicate vector-store files at every `deploy.sh` | cleared only on a full re-sync (F6) |
| DeepSearch score history | `appendScoreHistory` on `deepsearch-report` (stored with the report) | re-running OSINT for a supplier assessed < 30 days ago — `scheduled-deepsearch` skips suppliers with a fresh report | freshness window is an instruction parameter, not a code path — record it in the ticket |
| Comparison-set baseline | `Governance/ComparisonSet/baseline/{pipeline}/` (+ sha256 in the golden set) | regenerating known-good outputs for every evaluation | refresh quarterly (`CHANGE_MANAGEMENT.md` §9) |
| Thread reuse | one thread per supplier/service topic per user (`../team/THREADS_MEMORY.md`) | re-explaining context; the thread carries the uploaded PDF | threads are per user (no sharing of uploaded Euronext files across users through threads) |
| **Never cached** | Bing results containing Euronext-side context (none exist by design — queries are sanitised), verifier verdicts (each draft is verified), approval decisions | — | `DATA_PROTECTION_GUARDRAILS.md`; `HUMAN_APPROVAL.md` |

## 6. Off-peak batching

| Workload | Today | Rule |
|---|---|---|
| `scheduled-deepsearch` (watchlist re-assessment) | weekly, Monday recurrence (`../workflows/scheduled-deepsearch.json`) | keep at 02:00–06:00 CET (`schedule.hours`) so it never competes with the five users for the 30 k TPM reasoning cap (`FINOPS.md` §3); cap the batch at the watchlist slice that fits the window |
| Portfolio campaigns (bulk OT PDFs, bulk TPA trees) | manual | run through the pipeline trigger in sequence, not fan-out; use `agent-fanout.json` only with a concurrency limit ≤ 2 |
| Evaluation runs (`run_evals.py` against live agents) | manual | off-peak; they consume the same reasoning quota; never approve their gates (EVALUATION §3) |
| Azure OpenAI Batch (50 % discount, 24 h turnaround) | not used | admissible only through a **Data Zone Batch** deployment in the EU (residency invariant); candidate for `scheduled-deepsearch` and quarterly baseline refresh once the SDK path is verified — Tier C, High risk (new deployment kind) |
| Re-sync `deploy.sh` (uploads, agent updates) | on change | run from the pipeline off-peak; the upload cache keeps repeated runs cheap |

## 7. Accuracy-floor test before a downgrade (mandatory)

Runs before step 5 of §1; the artefacts go in the PR (`CHANGE_MANAGEMENT.md`
§4, §6 "Comparison set: attached").

| # | Step | Command / evidence |
|---|---|---|
| 1 | Select the golden cases of the agent (all `pipeline`/`agent` matches; ≥ 3 cases, including one adversarial: placeholder-laden input, long input) | `evaluation/golden-set.*.json` filtered by `agent` |
| 2 | Run on the **current** tier (control) — or reuse last month's M1 report if < 30 days old | `python3 evaluation/run_evals.py --golden evaluation/golden-set.example.json --only <ids> --out build/evals/<agent>-control` |
| 3 | Never touch the production agent: `run_evals.py --model-override <candidate-deployment>` clones it as `<agent>-eval` (same instructions, tools and stores; model swapped), runs the cases and deletes the clone at the end. Creating the clone needs `Azure AI Developer` — the owner's PIM window L1 (`TEAM_MODEL.md` §5); the control run in step 2 needs only `Azure AI User` | PIM activation id + clone name in the ticket |
| 4 | Run on the candidate tier | `python3 evaluation/run_evals.py --golden … --only <ids> --model-override <deployment> --out build/evals/<agent>-candidate` |
| 5 | Compare: every metric in `EVALUATION.md` §4 ≥ floor; verifier first-pass PASS = 100 % of cases; no structure/threshold/section drift vs baseline sha256 where the case is deterministic; wording delta reviewed by the owner **and** one peer (deputy when the owner proposes) | `report.md` diff attached |
| 6 | Cost evidence: tokens and € per case, control vs candidate | from the report's `usage` block (live runs) |
| 7 | Decision | PASS → §1 step 5 staged rollout; FAIL → agent stays; add the failing case to the golden set |

Never approve an approval gate created by an evaluation run; nothing from
an evaluation is stored under `Reports/` (the run is stopped at the
verifier — `EVALUATION.md` §3).

## 8. Anti-patterns (found at M2, fix-first)

| Symptom in KQL | Likely cause | Fix |
|---|---|---|
| input tokens ≫ output, flat across cases | RAG returning too many chunks; memory bloat | §3 `max_num_results`, memory retention |
| output ≫ contract size | narrative padding; agent "explaining" before the JSON block | instruction tightening (§4) |
| runs with > 5 tool calls | search loops (DeepSearch re-querying), missing stop rule | instruction: max queries per section; watchlist dedupe |
| p95 latency ≫ p50 | 429 back-off (see `model-throttling-429`) | capacity or off-peak (§6), not a tier change |
| `(unattributed)` agent rows | tracing attributes missing on a caller (MCP server, Copilot) | fix the caller's instrumentation before drawing cost conclusions |

## 9. Controls implemented here

| Control | Where |
|---|---|
| ISO 42001 A.6.2.4 verification/validation; A.6.2.6 operation; A.8.4 performance | §1 loop, §7 test, `EVALUATION.md` |
| ISO 27001:2022 A.8.32 change management; A.8.29 security testing; A.8.6 capacity | Tier C path; §7; §6 |
| DORA Art. 9(4)(e) change control; Art. 9(2) capacity | §1; §6 |
| EU AI Act Art. 9(6)–(8) testing against metrics; Art. 26(5) monitoring | §7; §1 step 1 |
| ISO 27001:2022 A.5.3 segregation of duties | deputy reviews owner-authored tier changes (`TEAM_MODEL.md` §12) |
