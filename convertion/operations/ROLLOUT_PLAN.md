# Rollout Plan — Pilot (Owner) → Four Users → Hypercare → Steady State

How the platform goes live for the InfoSec Assurance team without lowering
any control: the owner pilots every system a–j with the deputy as the
second pair of eyes, the four users join in one wave once the pilot exit
criteria are evidenced, four weeks of hypercare follow, and the ISMS
operating rhythm (`KPIS.md` §4) takes over. The claude.ai account stays
available in parallel until hypercare exit, so nothing is lost if a phase
fails its criteria. Access is granted phase by phase through the joiner
runbook (`access-governance/ACCESS_LIFECYCLE.md` §1) — never earlier than
the phase needs it.

Control: ISO 27001:2022 A.5.8 (information security in project
management), A.8.31 (dev/test/prod separation), A.8.29 (security testing
in development and acceptance), A.6.3 (awareness and training), A.5.37;
ISO 42001 A.6.2.5 (deployment), A.4.4 (resources — competence),
A.8.2 (documentation for users); EU AI Act Art. 4 (AI literacy), Art.
26(2) (competent natural persons for oversight), Art. 14; DORA Art. 13(6)
(awareness and training), Art. 9(4)(e).

## 1. Phases at a glance

| Phase | Weeks | Who is on the platform | Scope | Exit criteria (§3) | Decision |
|---|---|---|---|---|---|
| **P0 Readiness** | W-2 → W0 | nobody (owner in `dev`) | bootstrap, verification, comparison-set baselines, training material | P0-1 … P0-8 | owner + line manager: go to P1 |
| **P1 Pilot** | W1 → W2 | owner `{upn:francisco.gomes}` + deputy `{upn:deputy-approver}` (users group; deputy also senior approver) | every system a–j run for real on 2 suppliers each; approvals exercised in both directions (owner requests → deputy approves; deputy requests → owner approves) | P1-1 … P1-9 | owner + deputy + line manager: go to P2 |
| **P2 Team wave** | W3 | + `{upn:jose.mogollon}`, `{upn:pedro.santos}`, `{upn:jose.meireles}`, `{upn:tania.morais}` (the deputy is one of them and is already on) | joiner runbook ×3 (the deputy joined in P1), training, first Tier A report each with a peer approver | P2-1 … P2-6 | owner: hypercare starts |
| **P3 Hypercare** | W4 → W7 (4 weeks) | all five | daily stand-up, owner on-call, freeze on Tier C changes except fixes, KPI tracking daily, claude.ai parallel run for comparison | P3-1 … P3-8 | owner + line manager: steady state; claude.ai demoted to upstream-only |
| **P4 Steady state** | W8 → | all five | `RUNBOOK.md` rhythm, `KPIS.md` targets, `CONTINUOUS_IMPROVEMENT.md` quarterly cycle | — | first quarterly cycle at Q+1 |

No-go at any gate = stay in the current phase, fix through
`CHANGE_MANAGEMENT.md`, re-test the failed criterion; no phase is skipped
and no criterion is waived without a written risk acceptance by the CISO
delegate (ISO 27001 cl. 6.1.3; DORA Art. 6(8)).

## 2. Phase content

### P0 — Readiness (owner, `dev` then `prod` infrastructure)

| # | Activity | Reference | Evidence |
|---|---|---|---|
| P0-a | Bootstrap in order: groups / PIM / CA / deploy SP; `provision.sh`; `rbac.bicep`; `Sites.Selected` ×3; custodian tokens; `conn-*`; `deploy.sh`; access baseline | `../team/TEAM_MODEL.md` §18–§19 | Q0 access review folder |
| P0-b | Verification: `verify_conversion.py` PASS; `attach_integrations.py --dry-run` shows `[read-only]` on every tool; `APPROVAL GATE` count = agent count; `access-review.sh`; `provision_identity.sh --verify`; `infra/validate.sh` | `RUNBOOK.md` W1–W4 | pasted outputs in the P0 ticket |
| P0-c | Approval flow wired (`approvalWebhookUrl`): approver ∈ tier group, approver ≠ requester, decision stored — tested with a synthetic request from the owner rejected when the owner tries to approve it | `../team/approval-policy.json`, `../workflows/README.md` | flow run showing the rejection |
| P0-d | Comparison set built: inputs (synthetic/public) + known-good claude.ai outputs per pipeline, hashed | `CHANGE_MANAGEMENT.md` §4 | `Governance/ComparisonSet/` |
| P0-e | Monitoring live: alerts deployed, H9 telemetry schema validated, workbook `{baseName}-ops` built, egress detector proven with a test marker in `dev` | `MONITORING.md` §4–§5 | alert list; H9 note |
| P0-f | Backup live: first `backup_vector_stores.py` export filed; nightly `backup-job.bicep` deployed (delta D-BDR-B3) or W8 manual agreed | `BACKUP_DR.md` §3 | `Governance/Backups/{date}/` |
| P0-g | Training material ready: `../team/USER_QUICKSTART.md`, `../team/ONBOARDING.md`, user guides a–j under `Governance/UserGuides/`, the intake template (`SUPPORT_MODEL.md` §3), this plan | §5 | files present |
| P0-h | Templates with `last_approved: null` (`ciso-global-deck`, `evidence-summary-docx`, `xlsx-generic`) approved once through `template-update-approval` so requirement j's audit line exists before first use | `LIFECYCLE.md` §4 | `templates/audit.log` |

### P1 — Pilot (owner + deputy, 2 weeks, production)

| # | Activity | Detail |
|---|---|---|
| P1-a | Deputy joins via the joiner runbook (steps 1–6); nominated deputy confirmed by `{upn:line-manager}`; `-senior-approvers` membership set by IAM | `ACCESS_LIFECYCLE.md` §1–§2 |
| P1-b | Run every pipeline for two real suppliers each: a (DeepSearch), b (DPO DOCX), c (Cyber Forum PPTX), d (Global CISO PPTX), d2 (evidence tree), e (SOC), f (pentest); g/h/i conversationally via portal, MCP and Copilot; j one template proposal end-to-end | outputs stored under `Reports/<Supplier>/<Service>/` by the Function MI only |
| P1-c | Approvals in both directions per tier: Tier A owner → deputy and deputy → owner; Tier B (b, c, d) owner-requested → deputy approves; Tier C (j) deputy-proposed → owner approves and owner-proposed → deputy approves | `{list:ApprovalDecisions}` rows |
| P1-d | Negative tests: self-approval attempt rejected; expired gate (let one P3D gate expire) stores nothing; a prompt containing an internal identifier in a web-search request is sanitised (trace shows public terms only) and the detector stays at zero; a deliberate instruction to "create a Jira ticket" yields a draft with the approval marker and no write | `HUMAN_APPROVAL.md`; `DATA_PROTECTION_GUARDRAILS.md` |
| P1-e | Fidelity: every P1 output diffed against the comparison baseline (structure, scores, thresholds, sections); `evaluation/run_evals.py` against the golden set | `CHANGE_MANAGEMENT.md` §4; `evaluation/EVALUATION.md` §5 |
| P1-f | Operations rehearsal: one simulated P2 (disable a connection, observe agent degradation and recovery), one break-glass tabletop with the deputy, one memory restore in `dev` | `RUNBOOK.md`, `BREAK_GLASS.md`, `BACKUP_DR.md` §6 |
| P1-g | Known-issue list seeded (KI-01 … KI-06 confirmed or closed) | `SUPPORT_MODEL.md` §6 |

### P2 — Team wave (1 week)

| # | Activity | Detail |
|---|---|---|
| P2-a | Joiner runbook for the three remaining users on the same day (access package `AP-InfoSec-Foundry-User`); `-report-approvers` only after attestation (step 4) | `ACCESS_LIFECYCLE.md` §1; `access_snapshot.sh --tag joiner-{upn}` ×3 |
| P2-b | Training sessions (§5) — 2 × 90 min + self-paced | attendance list |
| P2-c | Each user: own thread naming, one memory note, one Tier A report end-to-end with a peer approver ≠ self, one approval given, MCP registered with own `az login` | onboarding attestation `Governance/Onboarding/{upn}.md` |
| P2-d | Copilot agent shared to `sg-infosec-foundry-users` only; each user confirms the same persona answer as in the portal | `../integrations/copilot/README.md` |

### P3 — Hypercare (4 weeks)

| Practice | Detail |
|---|---|
| Daily stand-up, 15 min, `{teams:infosec-assurance-platform}` | yesterday's runs, pending approvals older than 24 h, new KIs, one KPI snapshot (`KPIS.md` §5 hypercare view) |
| Owner on-call | business hours; response per `RUNBOOK.md` §3 with P2 treated as P1 for the first two weeks; deputy covers the owner's absence (break-glass rules unchanged) |
| Change freeze | Tier C changes limited to fixes for hypercare findings and Low-risk docs; no tier changes, no re-sync, no new integrations; the freeze is lifted at P3 exit |
| Parallel run | for the first 10 real reports, the requester also runs the claude.ai skill on the same input and files the diff with the approval comment — the third consecutive week with zero structural diffs ends the parallel run early |
| Feedback capture | every stand-up item → backlog (`CONTINUOUS_IMPROVEMENT.md` §2); the monthly satisfaction question asked weekly during hypercare |
| Exit review | week 7: KPI table vs targets, open findings, claude.ai demotion decision, hand-over of the daily rhythm to `RUNBOOK.md` §2 |

### P4 — Steady state

`RUNBOOK.md` §2 (daily/weekly/monthly), `KPIS.md` §4 rhythm,
`CONTINUOUS_IMPROVEMENT.md` quarterly cycle; the first quarterly access
review (`QUARTERLY_ACCESS_REVIEW.md`) falls in the first full quarter
after go-live and re-confirms every grant made during rollout.

## 3. Exit criteria

Every criterion names its evidence; the KPI ids are defined in `KPIS.md`.

| Id | Criterion | Target | Evidence |
|---|---|---|---|
| P0-1 | Bootstrap verified: no direct user role assignments; every assignment maps to a ledger row | `access-review.sh` clean | Q0 review folder |
| P0-2 | Read-only surface and gates | R2 = 100 %, R3 = 100 % | W2/W3 outputs |
| P0-3 | Approval flow rejects self-approval and out-of-tier approvers | 2/2 negative tests rejected | flow runs |
| P0-4 | Comparison set complete for the 7 report pipelines + g/h/i prompts | 7 baselines hashed | `Governance/ComparisonSet/baseline/` |
| P0-5 | Alerts live, H9 passed, egress detector fires on a test marker in `dev` | 11 rules enabled | alert list |
| P0-6 | First backup filed; restore test in `dev` passed | R11 ≤ 7 days | `Governance/Backups/` |
| P0-7 | Training material and user guides a–j published | 11 guides (a, b, c, d, d2, e, f, g, h, i, j) | `Governance/UserGuides/` |
| P0-8 | Templates with `last_approved: null` approved once | 3 audit lines | `templates/audit.log` |
| P1-1 | Every system a–j produced at least two stored deliverables (g/h/i: two answers each with cited sources) | 14 reports + 6 answers | run ids, SharePoint paths |
| P1-2 | Verifier first-pass rate over the pilot | Q1 ≥ 70 % per pipeline | `kql/verifier-fail-rate.kql` |
| P1-3 | Fidelity vs comparison baselines | Q4 = 100 % structural match | diffs in the ticket |
| P1-4 | Approvals exercised in both directions per tier; zero approver = requester rows | R4 = 0; ≥ 2 decisions per tier | `{list:ApprovalDecisions}` |
| P1-5 | Egress detector | R1 = 0 rows over the pilot | `kql/egress-detection.kql` weekly export |
| P1-6 | Time approval → stored | E1b ≤ 15 min for every run | run history |
| P1-7 | Negative tests P1-d all pass | 4/4 | ticket |
| P1-8 | Operations rehearsal P1-f done; post-rehearsal note filed | 3/3 | `Governance/Operations/` |
| P1-9 | No open P1/P2 | 0 | Jira |
| P2-1 | All five in `-users`; all five attested and in `-report-approvers` | 5/5 | snapshots + attestations |
| P2-2 | Each user completed one Tier A report and one approval | A1 = 5/5 | decisions list |
| P2-3 | MCP registered with own identity for each user; Copilot answers for each | 5/5 | attestation |
| P2-4 | Training delivered; quiz (§5) passed | 5/5 ≥ 80 % | attendance + quiz |
| P2-5 | Access snapshots filed for the three joiners | 3 | `Governance/AccessLifecycle/` |
| P2-6 | No direct role assignment or extra group appeared during P2 | `access-review.sh --quick` clean | output |
| P3-1 | Weekly active users | A1 ≥ 4/5 for the last 3 weeks | workbook |
| P3-2 | Verifier first-pass rate | Q1 ≥ 70 % per pipeline over 4 weeks | KQL |
| P3-3 | Approval without rework | Q2 ≥ 75 % (steady-state target 80 %) | decisions list |
| P3-4 | Parallel-run diffs | Q4 = 100 % structural; wording deltas reviewed | approval comments |
| P3-5 | Egress hits, privileged writes outside PIM, secrets past rotation | R1 = R6 = R7 = 0 | H4, H7, W6 |
| P3-6 | Cost | E4 ≤ 100 % of the month's budget share; forecast within budget | Cost Management |
| P3-7 | Support | E6: first response ≤ 4 business h on ≥ 90 % of posts; no P1; P2s closed within target | Teams / Jira |
| P3-8 | Satisfaction | Q6 ≥ 4/5 average in the last two weekly questions | channel poll |

## 4. Roles during rollout

| Role | Who | Responsibilities |
|---|---|---|
| Rollout owner (A/R) | `{upn:francisco.gomes}` | plan, P0 build, pilot, training delivery, gate decisions, hypercare on-call, evidence |
| Deputy (R) | `{upn:deputy-approver}` | second user in P1; approver of the owner's items; independent check of P1-4/P1-5 evidence; break-glass tabletop |
| Users (R for their own onboarding) | the four | attend training, complete attestation tasks, report every friction as a backlog item |
| Line manager (A for gates P0→P1, P3→P4; C otherwise) | `{upn:line-manager}` | confirms the deputy; approves go decisions; reviews privileged access granted during rollout at the first quarterly review |
| IAM / landing zone / custodians (R for their steps) | `{group:iam-admins}`, `{group:azure-platform}`, custodians | P0 bootstrap steps; joiner group changes; tokens |
| DPO (I) | `{group:dpo}` | informed of go-live and of the memory store RoPA entry; receives the first `Reports/DPO/` deliverable during P1 |
| ISMS (I) | `{group:isms-audit}` | receives the P3 exit review as input to the management review |

RACI ids: `../team/RACI.md` R1–R38 apply unchanged; rollout adds no
Accountable other than the owner and the line manager for the gates.

## 5. Training

Same curriculum for all five (identical persona, identical user rights);
the owner and the deputy take the two overlays. Delivery: two 90-minute
sessions in P2 (recorded, filed under `Governance/UserGuides/training/`),
self-paced reading, and a 10-question quiz (pass ≥ 80 %) that is part of
the onboarding attestation (EU AI Act Art. 4 literacy, Art. 26(2)).

| Module | Content | Material | Assessment |
|---|---|---|---|
| T1 What the platform is and is not | agents are read-only; every write is verifier + human; taxonomy `Reports/<Supplier>/<Service>/`; EU residency; what the persona will refuse (web egress of internal terms) | `../README.md`, `../governance/*.md`, `USER_QUICKSTART.md` §1 | quiz Q1–Q3 |
| T2 Systems a–j hands-on | trigger each pipeline with Supplier + Service; upload a PDF to your thread; read the verifier verdict; where the file lands; KIs | `USER_QUICKSTART.md` §2, user guides | one Tier A report (P2-c) |
| T3 Approving | tiers A/B/C; approver ≠ requester; what to check before approving (the verifier findings, scores vs thresholds, personal-data minimisation); rejection comments; expiry | `../team/TEAM_MODEL.md` §12, `HUMAN_APPROVAL.md` | one approval given; quiz Q4–Q6 |
| T4 Threads, memory, data protection | thread naming, team visibility, retention; memory note format; what never goes into memory; injection defence; how to report an AI concern | `TEAM_MODEL.md` §13, `THREADS_MEMORY.md` | one memory note; quiz Q7–Q8 |
| T5 Getting help | intake template, severities, what L1 may do, known-issue list | `SUPPORT_MODEL.md` §3–§6, `RUNBOOK.md` §3 | quiz Q9–Q10 |
| O1 Deputy overlay | senior approvals, reviewing owner-authored PRs, break-glass procedure and its limits (never approves), DR steps 5.4–5.6 | `BREAK_GLASS.md`, `CHANGE_MANAGEMENT.md` §2, `BACKUP_DR.md` §5 | tabletop in P1-f |
| O2 Owner overlay | full runbook, PIM discipline, change flow, re-sync, backups, KPI reporting | `RUNBOOK.md`, `CHANGE_MANAGEMENT.md`, `LIFECYCLE.md`, `BACKUP_DR.md`, `KPIS.md` | self-attested; reviewed by the line manager at the first quarterly review |

Refresher: T1/T3/T4 annually and after any *major* release
(`LIFECYCLE.md` §2); new joiners follow `../team/ONBOARDING.md`.

## 6. Parallel run and cut-over of the claude.ai account

| Period | claude.ai role | Rule |
|---|---|---|
| P0–P3 | production fallback + comparison source | the five may still deliver from claude.ai if the platform fails a report; every such case is a backlog item |
| P3 exit | demoted to **upstream only** (`LIFECYCLE.md` V1/V2: source of the export for re-sync) | no Euronext deliverable is produced on claude.ai after this date; the account's skills are edited only through the template-manager path so the export stays the master |
| Steady state | export source | re-sync semi-annually or on change (`LIFECYCLE.md` §3) |

## 7. Risks to the rollout

| Risk | Mitigation | Owner |
|---|---|---|
| Fidelity gap between `gpt-4o`/`o3-mini` and the claude.ai outputs on `chat`/`reasoning` tiers (`../README.md` limitation 1) | comparison set; parallel run; Claude tiers on Foundry where available in the EU Data Zone (`../infra/README.md` "Claude tiers") as a *minor* release after P3 | owner |
| Copilot timeouts on long runs (KI-01) | pipelines for a–f; Copilot for g/h/i only; stated in T2 | owner |
| Approval fatigue (five people, Tier A on every report) | `approval-sla` alert; hypercare stand-up reviews pending gates; SLO ≤ 2 business days | all |
| PIM / custom-role not available at bootstrap | `enablePim=false` fallback recorded with a review date; detective drift alert compensates (`TEAM_MODEL.md` §7.1) | owner + IAM |
| Custodian lead time for tokens / consents | requested in W-2 with the P0 ticket | owner |
| Owner single point of failure during hypercare | deputy trained (O1) in P1; break-glass tested | line manager |

## 8. Shared deltas needed by this file (not applied here)

| Id | Target | Location | Literal text |
|---|---|---|---|
| D-RO-Q1 | `REQUIREMENTS.md` | after delta D-OPS-Q1 | `Go-live sequencing (readiness → owner pilot → four users → four-week hypercare, with exit criteria and training per role): operations/ROLLOUT_PLAN.md; targets: operations/KPIS.md.` |
| D-RO-ON1 | `team/ONBOARDING.md` | §5 attestation table, last row | `\| Training quiz (operations/ROLLOUT_PLAN.md §5, modules T1–T5) \| ≥ 80 % \| joiner + owner \|` |
| D-RO-S1 | `operations/SUPPORT_MODEL.md` | §6 known-issue list intro | append ` Seeded during the pilot and hypercare (operations/ROLLOUT_PLAN.md P1-g, P3).` |
