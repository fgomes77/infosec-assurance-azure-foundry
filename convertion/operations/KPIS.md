# KPIs and the ISMS Operating Rhythm

The measures by which the owner, the team and the ISMS judge the platform:
adoption, quality, efficiency and risk/compliance, each with a formula, a
source that already exists in the kit, a target and amber/red thresholds.
`SUPPORT_MODEL.md` §2 fixes the service-level objectives; this file adds
the outcome and control indicators around them and says when each is
measured, by whom, and where it is reported. Nothing here needs a new
permission: every source is readable with the owner's standing
`Log Analytics Reader` + `Reader` (`../team/TEAM_MODEL.md` §5 L6) or with
site Read.

Control: ISO 27001:2022 cl. 9.1 (monitoring, measurement, analysis,
evaluation), cl. 9.3 (management review), cl. 10.2 (nonconformity and
corrective action), A.5.36 (compliance with policies), A.8.16; ISO 42001
cl. 9.1, cl. 9.3, A.6.2.6 (AI system operation and monitoring), A.8.4
(performance of the AI system communicated), A.9.4; EU AI Act Art. 26(5)
(deployer monitoring), Art. 72 (post-market monitoring — as input to the
provider where applicable); DORA Art. 6(5) (review of the ICT risk
framework), Art. 13(6).

## 1. KPI set

Columns: **Target** = green; **Amber** = review at the next monthly cycle;
**Red** = corrective action opened (`CONTINUOUS_IMPROVEMENT.md` §3) and,
for R-ids, an incident where the definition says so.

### Adoption

| Id | KPI | Formula | Source | Target | Amber | Red | Cadence |
|---|---|---|---|---|---|---|---|
| A1 | Weekly active users | distinct `owner_upn` with ≥ 1 run in the week ÷ 5 | `AppDependencies` custom dimension `owner_upn` (`TEAM_MODEL.md` §13) | ≥ 4/5 | 3/5 | ≤ 2/5 for 2 weeks | weekly |
| A2 | Reports delivered per pipeline | count of runs reaching `STORED` per pipeline per month | `LogicAppWorkflowRuntime` (`Upload_and_share` succeeded) | trend ≥ the monthly plan agreed at M1 (per supplier portfolio) | −25 % | −50 % for 2 months | monthly |
| A3 | Channel mix | share of runs by entry point: pipeline / portal / MCP / Copilot | `gen_ai.*` attributes + thread metadata `system` | report-producing agents ≥ 90 % via pipelines (KI-01) | 80 % | < 70 % | monthly |
| A4 | Memory contribution | notes added per month; authors ≥ 3 distinct | `memory_store.py list` count delta; author tag in note | ≥ 5 notes, ≥ 3 authors | 2 authors | 1 author for 2 months | monthly |
| A5 | Competence | users with a valid onboarding attestation and quiz ÷ users | `Governance/Onboarding/` | 100 % | — | < 100 % (Art. 26(2)) | quarterly |

### Quality

| Id | KPI | Formula | Source | Target | Amber | Red | Cadence |
|---|---|---|---|---|---|---|---|
| Q1 | Verifier first-pass rate | PASS on first verifier call ÷ verifier calls, per pipeline | `kql/verifier-fail-rate.kql` | ≥ 70 % | 60–70 % | < 60 % (alert `verifier-fail-rate` at FAIL > 30 %) → FM-08 | weekly |
| Q2 | Approval without rework | approved with no edit/rejection cycle ÷ decisions | `{list:ApprovalDecisions}` (`reviewedBy`, decision comments) | ≥ 80 % | 70–80 % | < 70 % | monthly |
| Q3 | Rejection rate by tier | rejected ÷ decisions, per tier A/B/C | same | ≤ 10 % | 10–20 % | > 20 % | monthly |
| Q4 | Fidelity to known-good outputs | golden-set / comparison-set runs meeting every metric floor ÷ runs | `evaluation/run_evals.py` report (`evaluation/EVALUATION.md` §4–§5); `CHANGE_MANAGEMENT.md` §4 diffs | 100 % | — | < 100 % (a change is refused or a re-sync is opened) | per change + quarterly refresh |
| Q5 | Grounding rate | sampled advisory answers (g/h/i) citing a knowledge source or enterprise record ÷ sample of 10 | M1 sample (`ARCHITECTURE.md` "Evaluation") | ≥ 90 % | 80–90 % | < 80 % | monthly |
| Q6 | User satisfaction | mean of the monthly 1–5 question (weekly in hypercare) | `SUPPORT_MODEL.md` §7 | ≥ 4.0 | 3.5–4.0 | < 3.5 | monthly |
| Q7 | Quality sampling findings | Tier A 10 % sample + 100 % Tier B fallbacks with a finding that should have escalated ÷ sampled | `QUARTERLY_ACCESS_REVIEW.md` item 13 / `TEAM_MODEL.md` §12.1 | 0 | 1 | ≥ 2 (routing change) | quarterly |

### Efficiency

| Id | KPI | Formula | Source | Target | Amber | Red | Cadence |
|---|---|---|---|---|---|---|---|
| E1a | Request → decision | median hours from gate start to human decision | `kql/approval-sla.kql` | ≤ 2 business days (SLO) | 2–3 days | > 3 days or any P3D expiry > 5 % (E1c) | weekly |
| E1b | Approval → stored | median minutes from `If_approved` to `Upload_and_share` | run history | ≤ 15 min | 15–30 | > 30 | weekly |
| E1c | Expired gates | expired ÷ gates raised | `kql/approval-sla.kql` | ≤ 5 % | 5–10 % | > 10 % | monthly |
| E2 | Tokens per deliverable | tokens per stored report, per pipeline, 30-day median vs the previous 30 days | `kql/latency-and-tokens.kql`; unit costs in `FINOPS.md` §2 | ≤ previous period +10 % | +10–25 % | > +25 % (FM-07, M2) | monthly |
| E3 | Cost per report | (model + Function + Logic Apps cost attributed by tags) ÷ stored reports | Cost Management (`FINOPS.md` §1, §5 tagging) + E2 | trend ↓ or flat quarter-on-quarter | +10 % | +25 % | monthly |
| E4 | Budget adherence | month-to-date spend ÷ (`monthlyBudget` × elapsed share) | `cost.bicep` RG budget + `cost-budget.bicep` component budgets (`FINOPS.md` §4) | ≤ 100 % | 100–110 % | > 110 % or 100 % alert before day 25 | weekly (W7) |
| E5 | Throttling share | 429 ÷ requests | `model-throttling-429` metric | < 1 % | 1–3 % | > 3 % (FM-05 capacity change) | weekly (H5) |
| E6 | Support responsiveness | posts answered ≤ 4 business h ÷ posts | Teams thread timestamps | ≥ 90 % | 80–90 % | < 80 % | monthly |
| E7 | Change lead time | median business days PR → production | GitHub | ≤ 5 | 5–10 | > 10 | monthly |
| E8 | Reasoning-tier share of tokens | reasoning tokens ÷ all tokens | `kql/latency-and-tokens.kql` by tier | ≤ 60 % (advisory pin makes the floor ~40 %) | 60–75 % | > 75 % without an advisory workload increase (M2 tier review for non-advisory agents) | monthly |

### Risk and compliance

| Id | KPI | Formula | Source | Target | Amber | Red | Cadence |
|---|---|---|---|---|---|---|---|
| R1 | Egress hits | rows of the internal-marker detector | `kql/egress-detection.kql`; alert `egress-internal-marker` | 0 | — | ≥ 1 = P1 (FM-03) | daily (H4) |
| R2 | Read-only tool surface | OpenAPI tools attached `[read-only]` ÷ tools; `write_connections` entries | `attach_integrations.py --dry-run`; registry | 100 %; 0 | — | any non-read-only tool or any `write_connections` entry not backed by a Tier C PR + `HUMAN_APPROVAL.md` update | weekly (W2) |
| R3 | Approval-gate presence | agents whose built instructions carry `APPROVAL GATE` ÷ agents | W3 grep | 100 % | — | < 100 % | weekly |
| R4 | Approver = requester | decision rows where approver = requestedBy | `{list:ApprovalDecisions}`; workbook "Oversight" | 0 | — | ≥ 1 = P1 (flow defect) | daily |
| R5 | Human oversight coverage | stored deliverables with a decision record ÷ stored deliverables | run history × decisions list | 100 % | — | < 100 % = P1 (a write without a gate) | monthly |
| R6 | Privileged writes outside PIM | `breakglass_window_write` / `agent_modified_by_non_deploy_identity` rows without a matching PIM activation + ticket | H7 reconciliation | 0 | — | ≥ 1 = P1 | daily |
| R7 | Secrets past rotation | KV secrets older than the register's rotation period | `access-review.sh --quick` (W6) | 0 | — | ≥ 1 (connection disabled until rotated) | weekly |
| R8 | Access review timeliness | quarterly review signed within the first two weeks; ledger rows re-confirmed | `Governance/AccessReviews/{yyyy}-Q{n}/sign-off.md` | 100 % on time | 1 week late | > 2 weeks late | quarterly |
| R9 | Unexplained drift | drift alerts not explained by a deployment in the same window | H8, `agent-drift.kql` | 0 | — | ≥ 1 | per deploy / weekly |
| R10 | Incidents | P1 count; P2 closed within target ÷ P2 | Jira `{jira:INFOSEC-PLAT}` | P1 = 0; P2 ≥ 90 % on time | P2 80–90 % | any P1; P2 < 80 % | monthly |
| R11 | Backup age | days since the last successful memory export | `manifest.json` `exported_at` (W8) | ≤ 1 (automated) / ≤ 7 (manual) | +2 days | > 2× target (`BACKUP_DR.md` RPO breached) | weekly |
| R12 | Content-filter false blocks | legitimate runs blocked by the RAI policy (user-reported, FM-04) | tickets | ≤ 1 / month | 2–3 | > 3 (RAI severity tuning, high-risk change) | monthly |
| R13 | Memory hygiene | notes failing the `TEAM_MODEL.md` §13 format or containing banned content, found at W5/quarterly review | `memory_store.py list` review | 0 | 1–2 (deleted) | ≥ 3 or any personal data beyond role/company (DPO informed) | monthly |
| R14 | Retention compliance | threads older than the retention rule still present; notes past review date | quarterly review items 11–12 | 0 | ≤ 5 | > 5 | quarterly |

## 2. Measurement rules

| Rule | Detail |
|---|---|
| One source per KPI | the query or list named above is the only source; if the telemetry schema changes (RUNBOOK H9), the KPI is marked *not measurable* until the query is fixed — never estimated |
| No individual performance measurement | `owner_upn` is aggregated to counts (A1, A4); per-person report counts are never reported (`TEAM_MODEL.md` §13 "Attribution in telemetry"); the works-council-relevant line is drawn at the team level |
| Two consecutive misses | a KPI red (or amber twice) in two consecutive periods opens a corrective action (cl. 10.2) in the backlog with an owner and a due date |
| Targets are reviewed, not chased | targets change only at the quarterly cycle with the evidence of the previous quarter (`CONTINUOUS_IMPROVEMENT.md` §4), by the owner with the line manager |
| Evidence retention | monthly KPI note ≥ 3 years (management-review input); underlying queries reproducible from Log Analytics for 365 days (delta D-OPS-B3) and from exports thereafter (`BACKUP_DR.md` B6) |

## 3. Reporting formats

| Artefact | Content | Produced by | Filed under |
|---|---|---|---|
| Weekly snapshot (hypercare: daily) | A1, Q1, E1a–c, E4, E5, R1, R4, R6, R7, R11 as one table from the workbook `{baseName}-ops` | owner (W-checks) | `Governance/Operations/{yyyy}-{mm}/kpis-week-{n}.md` |
| Monthly KPI note (M1/M2 output) | full set; trend arrows; amber/red list with the action for each; tier-tuning proposals; known-issue changes | owner, users consulted | `Governance/Operations/{yyyy}-{mm}/kpis.md` |
| Quarterly review pack | quarter view of every KPI; access review sign-off; template inventory; comparison-set refresh; DR test results; improvement cycle results | owner + deputy; line manager for R6–R8 | `Governance/Operations/{yyyy}-Q{n}/review.md` |
| Annual management-review input | year trends; incidents; risk acceptances (Bing egress, Microsoft-managed agent storage — `../infra/README.md`); AI impact assessment refresh; proposed targets | owner → ISMS `{group:isms-audit}` | ISMS management review record |

Reports carry counts, rates and run/ticket ids only — never report
content, supplier findings or personal data.

## 4. ISMS operating rhythm

| Cadence | Activity | KPIs | Who | Output → where | Kit reference |
|---|---|---|---|---|---|
| Daily | H1–H7 health checks | R1, R4, R6 | owner | check log | `RUNBOOK.md` §2 |
| Weekly | W1–W8; snapshot | A1, Q1, E1, E4, E5, R2, R3, R7, R9, R11 | owner | weekly snapshot | `RUNBOOK.md` §2, `BACKUP_DR.md` §6 |
| Monthly | M1 evaluation, M2 cost/tier, M3 known issues, M4 PIM report; satisfaction question | all A, Q, E; R10, R12, R13 | owner; users consulted; line manager receives M4 | monthly KPI note; tier-change PRs; KI list | `RUNBOOK.md` §2; `evaluation/EVALUATION.md` §6 (M1); `FINOPS.md` §6 + `TOKEN_ECONOMY_PLAYBOOK.md` §1 (M2) |
| Quarterly | access review; template inventory; comparison-set refresh; alert-threshold review; improvement cycle close-out; target review | A5, Q7, R8, R14 + quarter view | owner, deputy, line manager | quarterly review pack; `sign-off.md` | `QUARTERLY_ACCESS_REVIEW.md`; `CHANGE_MANAGEMENT.md` §9; `CONTINUOUS_IMPROVEMENT.md` §4 |
| Semi-annual | re-sync; restore test; DR tabletop | Q4, R11 | owner | release tag; DR note | `LIFECYCLE.md` §3; `BACKUP_DR.md` §6 |
| Annual | management review input; policy review (`HUMAN_APPROVAL.md`, `DATA_PROTECTION_GUARDRAILS.md`); ISO 42001 AI impact assessment; training refresh; risk-acceptance re-confirmation | year view | owner → ISMS, CISO delegate, DPO | management review record | `CHANGE_MANAGEMENT.md` §9; `ROLLOUT_PLAN.md` §5 |

## 5. Hypercare view (`ROLLOUT_PLAN.md` P3)

Daily during hypercare: A1, Q1, E1a, E1b, R1, R4, R6, R7 plus open KIs
and pending gates > 24 h; targets as in §1 except Q2 ≥ 75 % and P2
severity handled as P1 for the first two weeks. The hypercare exit review
uses P3-1 … P3-8 of the rollout plan, which are these KPIs over the four
weeks.

## 6. Shared deltas needed by this file (not applied here)

| Id | Target | Location | Literal text |
|---|---|---|---|
| D-KP-A1 | `ARCHITECTURE.md` | "Evaluation and success metrics", end | ` The full indicator set (adoption, quality, efficiency, risk/compliance) with formulas, sources, targets and the ISMS operating rhythm is operations/KPIS.md; the review cadence is RUNBOOK.md §2 and CONTINUOUS_IMPROVEMENT.md.` |
| D-KP-S1 | `operations/SUPPORT_MODEL.md` | §2 intro paragraph, end | ` Outcome and control indicators beyond these SLOs (adoption, quality, cost, egress, oversight coverage): KPIS.md.` |
| D-KP-M1 | `operations/MONITORING.md` | §5 Dashboard table, new last row | `\| KPIs \| the weekly snapshot tiles of \`KPIS.md\` §3 (A1, Q1, E1a–c, E4, E5, R1, R4, R6, R7, R11) with green/amber/red thresholds \| the queries named per KPI in \`KPIS.md\` §1 \|` |
| D-KP-T1 | `team/TEAM_MODEL.md` | §3 row F9 "Derived requirement" cell | append ` → indicators and reporting: ../operations/KPIS.md` |
