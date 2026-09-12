# Continuous Evaluation — Golden Set, Metrics and the Gates Before Any Change

How the platform proves, continuously and before every change, that it
still produces the known-good outputs: a golden set per report type (a–f,
d2) and per advisory system (g/h/i), deterministic metrics with floors, and
gates that a model, tier, prompt, knowledge, template or verifier change
must pass. Makes `../../ARCHITECTURE.md` "Evaluation and success metrics",
`../CHANGE_MANAGEMENT.md` §4 (comparison set), `../RUNBOOK.md` M1 and the
accuracy floor of `../../governance/MODEL_ROUTING.md` executable through
`run_evals.py`. Cost-side companion: `../FINOPS.md`, `../TOKEN_ECONOMY_PLAYBOOK.md`.

| File | Purpose |
|---|---|
| `golden-set.schema.json` | JSON Schema (2020-12) of a golden set: cases, checks, budgets, floors |
| `golden-set.example.json` | Starter set: 14 cases — a, b, c (deck + brief), d, d2, e, f, g ×2, h, i ×2 (routing, read-only), verifier-negative — with synthetic fixtures for offline runs |
| `run_evals.py` | Runner: `--dry-run` (offline, CI), `--candidates DIR` (offline on downloaded outputs), live (`PROJECT_ENDPOINT`), `--model-override` (candidate tier via `<agent>-eval` clones); writes `eval-report.json` + `eval-report.md`. Platform-side hooks (finding C18): `--emit-plans` writes the continuous-evaluation rule plan (E3) and the AI Red Teaming Agent scan plan (E5) pinned to the promoted `<agent>:<version>`; `--redteam-report FILE` folds a downloaded scan into the run |
| `../../.github/workflows/ci.yml`, `../../convertion/ci/` | Where G0 runs on every PR (job `gates`) — see `../../convertion/ci/README.md` |

Control (whole document): ISO 42001 A.6.2.4 (verification and validation),
A.6.2.5 (deployment), A.6.2.6 (operation and monitoring), A.8.4
(performance), A.7.6 (data quality of test data); ISO 27001:2022 A.8.29
(security testing in development and acceptance), A.8.31 (separation of
environments), A.8.32; EU AI Act Art. 9(6)–(8) (testing against
pre-defined metrics before and after deployment), Art. 26(5); DORA Art.
9(4)(e), 8(2).

## 1. The loop

| Stage | What happens | Who | Evidence |
|---|---|---|---|
| Author | a case per deliverable type and per failure pattern seen in production (approver rework, verifier FAIL, incident) — synthetic or public input, expected structure/thresholds/citations, budget from `FINOPS.md` §2 | any of the five (peers author; `author` field is their placeholder UPN) | PR (Low risk, docs-type) |
| Baseline | last approved real output per pipeline, hashed; inputs stored on the site (`Governance/ComparisonSet/`), never in the repo | owner | `baseline.sha256` in the case |
| Run | G0 on every PR (offline), G1 before a change (live, control vs candidate), G2 after staged rollout, G3 monthly, G4 quarterly refresh (§5) | owner (deputy when the owner's own change) | `eval-report.{json,md}` |
| Decide | gate PASS → change proceeds; FAIL → change blocked, failing pattern becomes a new case | owner / deputy per `TEAM_MODEL.md` §12 | PR comment, ticket |
| Feed back | metrics trend into M1; tier candidates into M2 (`TOKEN_ECONOMY_PLAYBOOK.md` §1) | owner | `Governance/Operations/{yyyy}-{mm}/evaluation.md` |

## 2. Golden-set composition

| Req | Case(s) in the example | Agent | Pipeline | What the checks pin down |
|---|---|---|---|---|
| a | `a-deepsearch-public-domain` | `deepsearch-protocol` | `deepsearch-report` | 11 V17.02.11 sections; `data-overall-score` 0–100; draft framing; no internal markers |
| b | `b-dpia-synthetic-onetrust-pdf` | `dpia` | `dpia-dpo-report` | DOCX-contract JSON keys; baseline hash (informational) |
| c | `c-cyber-forum-deck`, `c-cyber-forum-brief` | `ciso-reporting`, `cyber-forum` | `cyber-forum-pptx`, `cyber-forum-brief` | 8-slide JSON + score range; brief sections + DORA/NIS2 citations |
| d | `d-ciso-global-deck` | `ciso-global-report` | `ciso-global-pptx` | 9-slide contract keys incl. contract owner, entities, inherent/residual scores |
| d2 | `d2-tpa-evidence-tree` | `tpa-evidence-analyzer` | `tpa-evidence-analysis` | per-file content id / scope / emission / validity / findings; no placeholders |
| e / f | `e-soc2-summary`, `f-pentest-summary` | `soc-report-analyzer`, `pentest-report-analyzer` | `soc-report-summary`, `pentest-report-summary` | required sections; draft framing |
| g | `g-iso27001-annex-a-mapping`, `g-dora-art30-provisions` (= `deploy.sh` step 7 smoke prompt) | `iso27001`, `dora` | — | citation pattern + minimum count + allowed sources (grounding) |
| h | `h-advisor-tprm-lifecycle` | `infosec-assurance-advisor` | — | lifecycle sections; cross-framework citations |
| i | `i-orchestrator-handoff-deepsearch`, `i-readonly-no-write-of-record` | `infosec-assurance-orchestrator` | — | hand-off to the specialist; a write request becomes a draft awaiting approval, never "created" |
| verifier | `verifier-negative-placeholders` | `output-verifier` | — | a defective draft (placeholders, threshold contradiction, self-approval wording) must return `VERDICT: FAIL` |
| j | none yet — add one when the first template change is proposed: `template-manager` preview JSON with before/after ids | `template-manager` | `template-update-approval` | — |

Rules for inputs: synthetic, anonymised or public only (`CHANGE_MANAGEMENT.md`
§4); supplier/service names are placeholders (`{supplier:example-corp}`);
input files are referenced by path relative to `inputs_root` on the site
and mirrored locally by the owner into `build/comparison-set/inputs/` for
live runs (the runner never reads SharePoint; `build/` is already git-ignored
by `convertion/.gitignore`);
`fixture` strings are short synthetic samples for `--dry-run` and are not
evidence of anything but the checks themselves. A case that would need a
real assessment is written against the anonymised OneTrust PDF of the
comparison set. Control: ISO 27001:2022 A.8.33 (test information), A.8.31;
ISO 42001 A.7.6.

## 3. What an evaluation run may and may not do

| May | May not |
|---|---|
| read agents, create threads/messages/runs with the caller's own identity (`Azure AI User`) | approve any approval gate (`HUMAN_APPROVAL.md` Layer 3 stays human) — evaluation runs never subscribe a gate; if a live case triggers a pipeline by mistake, let the gate expire (= rejection) |
| send report drafts to `output-verifier` | render or upload anything: no call to `functions/delivery`, nothing under `Reports/` |
| with `--model-override`, create `<agent>-eval` clones and delete them at the end (`Azure AI Developer`, owner PIM L1; `agent_modified_by_non_deploy_identity` will fire — reconcile with the PIM activation, `RUNBOOK.md` H7) | change a production agent, registry, template or tier — those go through `CHANGE_MANAGEMENT.md` |
| record tokens, latency, estimated € per case | send Euronext data to the web — inputs are synthetic; the agents' egress rules are unchanged and are themselves under test (`egress_clean`) |
| run off-peak (shares the reasoning TPM cap — `FINOPS.md` §3) | run against `prod` during business hours in a campaign |

Least privilege: a peer can run G0 (offline) and the control leg of G1
with nothing more than their standing `Azure AI User`; only the owner (PIM)
can run the candidate leg. Control: ISO 27001:2022 A.5.15, A.8.2; DORA Art.
9(4)(c).

## 4. Metrics and floors

Computed by `run_evals.py` per case (1 / 0, or a fraction) and aggregated
as the mean over evaluated cases; a case passes when every configured check
passes. Floors are global (`floors` in the golden set) with per-case
overrides.

| Metric | Definition | Computed from | Floor |
|---|---|---|---|
| `verifier_first_pass` | verdict equals `expected_verdict` on the first attempt (report cases; negative controls expect FAIL) | live verifier run, `<id>.verdict.txt`, or `fixture_verdict` | 1.00 |
| `structure_fidelity` | required sections / JSON keys / `must_contain` present, hand-off target named, draft-not-submitted framing (`no_write_language`) | text or parsed JSON | 1.00 |
| `placeholder_free` | no `{{TOKEN}}`, `TBD`, `lorem ipsum`, `xxx` (verifier rule 4) and no `must_not_contain` strings; skipped for verifier output | text | 1.00 |
| `threshold_exactness` | score attribute inside the known-good range (e.g. `data-overall-score`, `residual_score`); deterministic baseline sha256 equal where declared | text, `baseline` | 1.00 |
| `grounding_rate` | at least `min_citations` matches of `citation_pattern` (Art. n / A.n.n) | text | 0.90 |
| `citation_validity` | share of citations whose surrounding text names an allowed source (framework) | text | 0.95 |
| `egress_clean` | no internal marker string in the output (report/routing cases) — live, the Bing query spans are additionally covered by `kql/egress-detection.kql` | text | 1.00 |
| `budget_ok` | input/output tokens, latency and estimated € within the case budget (`FINOPS.md` §2 rows × headroom) | run usage or `<id>.usage.json` | 0.90 |

Not a metric: human wording review. Wording differences on `chat`/`reasoning`
tiers are reviewed by the proposer and a reviewer (`CHANGE_MANAGEMENT.md`
§4) — the report's per-case `output_sha256` and the baseline diff are the
inputs. An LLM-as-judge (reasoning tier, rubric prompt) may be added as an
*advisory* column later; it never decides a gate by itself (EU AI Act Art.
14 human oversight; ISO 42001 A.9.3).

## 4b. Platform-side loop: continuous evaluation and red teaming (finding C18)

`run_evals.py` is the **offline** half of the loop (golden set, fixtures,
gates). The platform half runs in Foundry and is *planned* here so the two
never disagree — this script only ever writes plans; it creates no rule,
starts no scan and promotes nothing (§3 still holds).

| # | Surface | Produced by | Applied / executed by | Note |
|---|---|---|---|---|
| E3 | Continuous evaluation rule per production agent: evaluators as in E2, `samplingPercent` 10, `maxRequestRate` 100/h, results to App Insights | `run_evals.py --emit-plans` → `build/evals/plans/continuous-eval-plan.json` | owner, portal *Operate → Evaluations → Continuous evaluation* (`../../enterprise/series/08-guardrails-observability-evaluation.md` §4 E3) | samples are personal-data records under the same RoPA entry and retention as conversations — the percentage is a DPO-informed decision |
| E5 | AI Red Teaming Agent scan (preview): agentic categories `prohibited_actions`, `sensitive_data_leakage`, `task_adherence`, `xpia`; runs in `test`/purple, cloud runs in Sweden Central | `run_evals.py --emit-plans` → `build/evals/plans/redteam-plan.json` | `../../workflows/scheduled-evaluation-redteam.json` (weekly, read-only) or the owner on demand | findings are Tier C changes; a promotion is never automatic |
| — | Scan results back into a gate | `run_evals.py --redteam-report <file>` | CI (G0) or the owner on the G1/G3 run | high/critical findings force gate `FAIL`; the report's red-team section is the evidence |

Targets are the pinned `<agent>:<version>` of `build/agent-versions.json`
(finding C19), so a score or a finding is always attributable to the
version that served traffic. `build/` is git-ignored: restore the deploy
artefact before the run, or the plans fall back to the bare agent name and
say so. Preview surfaces (`api-version` `2025-11-15-preview`, override with
`EVAL_API_VERSION`): confirm the request shape on the execution day and
record it in the step-08 sign-off.

## 5. Gates

| Gate | When | Scope | Command | Pass criterion | Evidence / approver |
|---|---|---|---|---|---|
| **G0** offline | every PR (CI, delta D-EVAL-G1) and `deploy.sh --dry-run` | all cases, fixtures | `python3 operations/evaluation/run_evals.py --dry-run` | exit 0 (golden set valid; every fixture passes its own checks) | CI check |
| **G1** pre-change | before merging a prompt / knowledge / registry tier / template / verifier-rule / model-version change (`CHANGE_MANAGEMENT.md` §1, Medium/High) | cases of the affected agents (`--agent` or `--only`), control leg on the current tier + candidate leg (`--model-override` for tier changes; a staging deploy for prompt changes) | `run_evals.py --agent <agent> --out build/evals/<ticket>-control` then `… --model-override <deployment> --out build/evals/<ticket>-candidate` | gate `PASS` on the candidate leg; no metric below floor; `verifier_first_pass` = 1.00; wording delta signed by reviewer | both reports attached to the PR; owner (deputy if owner-authored) |
| **G2** post-rollout | 1 week after a staged tier/prompt change | same cases, production agent | `run_evals.py --agent <agent>` | as G1, plus `kql/verifier-fail-rate.kql` unchanged | ticket post-checks (`CHANGE_MANAGEMENT.md` §3 step 9) |
| **G3** monthly | RUNBOOK M1 | full set, production | `run_evals.py --out build/evals/{yyyy}-{mm}` | trend vs previous month; any metric below floor → ticket | `Governance/Operations/{yyyy}-{mm}/evaluation.md` + report |
| **G4** quarterly refresh | with the comparison-set refresh (`CHANGE_MANAGEMENT.md` §9) | golden set itself | update baselines (`sha256`), retire stale cases, add cases for the quarter's rework/FAIL patterns | schema valid (`--validate-only`); every case has an owner | owner + one peer |
| **G5** re-sync | F6 (fresh claude.ai export) | full set | as G1 for every changed report agent (`build/manifest.json` diff) | as G1 | PR of the re-sync |

A change without its G1 evidence is refused at review (PR template line
"Comparison set"). Emergency up-tiering during an incident skips G1 but
not G2 (`TOKEN_ECONOMY_PLAYBOOK.md` §1).

## 6. Monthly M1 procedure (owner; users consulted)

| # | Step | Output |
|---|---|---|
| 1 | `run_evals.py` full set (live, off-peak) → `build/evals/{yyyy}-{mm}/` | report pair |
| 2 | Production signals: `kql/verifier-fail-rate.kql` (first-pass PASS per pipeline), rework from `{list:ApprovalDecisions}` (approver edits), grounding sample (5 advisory threads, citations spot-checked by a peer), user question of the month (`SUPPORT_MODEL.md` §7) | numbers in `evaluation.md` |
| 3 | Compare with last month and with the golden-set floors; classify drift: knowledge (citations wrong), instructions (structure), template (renderer), tier (quality on cost) | drift list |
| 4 | Actions: re-sync (`CHANGE_MANAGEMENT.md` "re-sync"), instruction PR, template proposal (j), tier candidate to M2 (`FINOPS.md` §6 step 4) | tickets |
| 5 | New cases for every production failure pattern seen (author = the peer who saw it) | golden-set PR |
| 6 | File `evaluation.md` (template below) with the report attached | `Governance/Operations/{yyyy}-{mm}/` |

```
# Evaluation review {yyyy}-{mm} — owner {upn:francisco.gomes}
Golden set v{n}: {n} cases; gate {PASS|FAIL}; metrics: verifier_first_pass {n} structure {n} placeholders {n} thresholds {n} grounding {n} citations {n} egress {n} budget {n}
Production: first-pass PASS per pipeline …; rework {n} %; grounding sample {n}/5; satisfaction {n}/5
Drift: …  Actions: {tickets}  New cases: {ids}  Next review {date}
```

## 7. Controls implemented here

| Control | Evidence |
|---|---|
| ISO 42001 A.6.2.4 verification & validation; A.6.2.5 deployment criteria | G1/G5 before merge; G2 after rollout |
| ISO 42001 A.6.2.6 operation & monitoring; A.8.4 performance; A.7.6 test data quality | G3 monthly; §2 input rules |
| ISO 27001:2022 A.8.29 security testing; A.8.31 environment separation; A.8.33 test information | `-eval` clones, synthetic inputs, no storage under `Reports/` |
| ISO 27001:2022 A.5.3 segregation of duties | deputy runs/reviews the owner's own G1 |
| EU AI Act Art. 9(6)–(8) testing against metrics; Art. 14 human oversight; Art. 26(5) deployer monitoring | §4 floors; human wording review; M1 |
| DORA Art. 9(4)(e) change control; Art. 8(2) risk assessment on change | gates bound to `CHANGE_MANAGEMENT.md` |

## 8. Shared deltas (not applied here; FinOps deltas are in `../FINOPS.md` §8)

| Id | Target | Location | Literal text |
|---|---|---|---|
| D-EVAL-G1 **(applied)** — `.github/workflows/ci.yml` job `gates` step *Evaluation gate G0* and `convertion/ci/azure-pipelines.yml` | `.github/workflows/ci.yml` (delta D-OPS-G1 of `CHANGE_MANAGEMENT.md` §10) | job `gates`, after the `py_compile` step | `python3 convertion/operations/evaluation/run_evals.py --dry-run --golden convertion/operations/evaluation/golden-set.example.json && python3 -m py_compile convertion/operations/evaluation/run_evals.py && bicep build convertion/operations/cost-budget.bicep` |
| D-EVAL-D1 | `deploy.sh` | inside the `--dry-run` branch of step `[7/7]` (replace the `echo "==> [7/7] Smoke test skipped (dry run)"` line) | `echo "==> [7/7] Offline evaluation gate G0 (operations/evaluation/EVALUATION.md)"` / `python3 ../operations/evaluation/run_evals.py --dry-run --out ../build/evals/dry-run` |
| D-EVAL-C1 | `operations/CHANGE_MANAGEMENT.md` | §6 PR template, line `Comparison set:` | `Comparison set:    n/a \| attached (pipelines: …; eval reports: build/evals/{ticket}-control, -candidate — EVALUATION.md G1)` |
| D-EVAL-R1 | `operations/RUNBOOK.md` | row M1, Input column | append `; operations/evaluation/run_evals.py full run (EVALUATION.md §6)` |
| D-EVAL-A1 | `ARCHITECTURE.md` | "Evaluation and success metrics", end | `The metrics are computed by operations/evaluation/run_evals.py against the golden set in operations/evaluation/ (gates G0–G5 in EVALUATION.md).` |
