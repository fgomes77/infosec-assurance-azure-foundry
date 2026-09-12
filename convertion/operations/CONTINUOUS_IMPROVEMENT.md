# Continuous Improvement — Feedback → Owner Backlog → Quarterly Cycle

How everything the platform and its users learn turns into a controlled
change: the signals already collected by the support model, the monthly
evaluation, FinOps/tier tuning, monitoring and template governance feed
one owner-maintained backlog, which is triaged weekly and delivered in a
quarterly improvement cycle through `CHANGE_MANAGEMENT.md`. The cycle
never bypasses a tier: an improvement is still a Tier C change (or a
template approval, or a memory deletion) with the same gates; what this
file adds is *where ideas go, how they are prioritised and when they are
done*. Owner: `{upn:francisco.gomes}` (optimisation of the whole solution
— `../team/TEAM_MODEL.md` §1).

Control: ISO 27001:2022 cl. 10.1 (continual improvement), cl. 10.2
(nonconformity and corrective action), cl. 9.1, cl. 9.3, A.5.27 (learning
from incidents), A.5.35 (independent review), A.5.36; ISO 42001 cl. 10.1,
cl. 10.2, A.6.2.6 (operation and monitoring), A.8.3 (external reporting —
concerns about AI outputs), A.8.4; EU AI Act Art. 26(5), 26(7); DORA Art.
6(5) (annual review of the ICT risk framework and after incidents), Art.
13 (learning and evolving), Art. 13(6).

## 1. Signals → backlog

| # | Signal | Collected by (existing) | Frequency | Becomes a backlog item when | Type (§2) |
|---|---|---|---|---|---|
| S1 | Rework before approval, rejection comments | `{list:ApprovalDecisions}`; quarterly 10 % Tier A sample (`TEAM_MODEL.md` §12.1) | monthly M1 | the same cause appears twice, or any Tier B rejection | quality |
| S2 | Verifier FAIL reasons | `kql/verifier-fail-rate.kql`; FAIL findings in run output | weekly H3 | Q1 amber/red for a pipeline, or a new finding category | quality |
| S3 | Golden-set / comparison-set drift | `evaluation/run_evals.py` (`evaluation/EVALUATION.md` §4–§5); `CHANGE_MANAGEMENT.md` §4 diffs | per change + quarterly | any structural diff (Q4 < 100 %) | fidelity (re-sync or refuse) |
| S4 | Tokens, latency, cost per deliverable | `kql/latency-and-tokens.kql`; Cost Management; budget alerts | monthly M2, weekly W7 | E2/E3/E4/E8 amber | FinOps |
| S5 | Throttling, capacity | `model-throttling-429`; H5 | weekly | E5 amber | capacity |
| S6 | Alerts: noise, misses, threshold fit | alert history; H7 reconciliations | monthly | an alert fired without a finding twice, or a finding had no alert | monitoring |
| S7 | Template wishes and defects | `template-manager` proposals (F4); `Templates/Reviews/` | as raised | every proposal (the approval workflow is the delivery path; the backlog tracks it) | template (j) |
| S8 | Support posts, known issues | Teams intake template; `SUPPORT_MODEL.md` §6 KI list | continuous; M3 | a KI older than 60 days, or ≥ 3 posts on one cause | usability / fix |
| S9 | Incident post-incident notes (prevention items) | `RUNBOOK.md` §6 | per P1/P2 | always | corrective action (cl. 10.2) |
| S10 | Access-review findings, ledger rows removed, drift | `QUARTERLY_ACCESS_REVIEW.md`; H8 | quarterly | always | access / control |
| S11 | Memory quality (W5), retention breaches | `memory_store.py list` review | weekly / quarterly | R13/R14 amber | data hygiene |
| S12 | DR / restore test findings | `BACKUP_DR.md` §6 | semi-annual | always | resilience |
| S13 | Model, SDK, API retirement notices; new EU-region models (incl. Claude tiers) | `../enterprise/upgrade/check_model_lifecycle.py`; Azure Service Health notices to `{owner-mailbox}`; `LIFECYCLE.md` §5 | monthly M3 | always (plan the bump) | lifecycle |
| S14 | User satisfaction and free text | monthly question (`SUPPORT_MODEL.md` §7) | monthly | Q6 amber or any concrete suggestion | usability |
| S15 | Concern about an AI output (bias, wrong regulatory claim, hallucinated citation, injection suspected) | any user, any channel; DPO/ISMS | as raised | always — logged the same day, acknowledged in the channel | AI concern (ISO 42001 A.8.3; EU AI Act Art. 26(7)) |
| S16 | Regulatory or framework change (DORA RTS, NIS2 transposition, ISO amendments) | advisors' web grounding + the team's own watch | as raised | affects knowledge packs, verifier rules or thresholds | knowledge |
| S17 | Feedback records (`../enterprise/memory/feedback-schema.json`) and the monthly learning proposal (`python3 ../enterprise/memory/learning_loop.py --dry-run --month {yyyy-mm}`) | `build/learning/{yyyy-mm}/proposal.md`; `{list:PlatformFeedback}` | monthly M1 | every accepted item; AI concerns mandatory | per proposal |

Everything enters the same place: Jira project `{jira:INFOSEC-PLAT}`,
issue type *Improvement* (or *Corrective action* for S9/S10 and any
two-period KPI miss), label `ci-cycle-{yyyy}-Q{n}` once scheduled. A Teams
post is not a record — the owner (or the first peer, L1) creates the
ticket. No report content, findings, scores or personal data go into a
ticket; run ids and thread ids only.

## 2. Backlog item

```
Title:            <verb> <object> — e.g. "Raise verifier rule 3 precision on SOC summaries"
Signal:           S1–S16 + evidence link (run id, KPI note, ticket)
Requirement:      a–j affected
Type:             quality | fidelity | FinOps | capacity | monitoring | template | usability | fix |
                  corrective action | access | data hygiene | resilience | lifecycle | knowledge | AI concern
Change path:      CHANGE_MANAGEMENT §1 type (prompt / registry / template / infra / tier / re-sync / access / docs)
Invariant check:  read-only agents / approval before write / taxonomy / identities / EU / no egress — unchanged (must be "unchanged"; otherwise it is not an improvement but a risk-acceptance request)
Value (1–5):      effect on Q1/Q2/E2/E3/R-ids or user time saved
Risk (1–5):       CHANGE_MANAGEMENT §5 class (low 1, medium 3, high 5)
Effort (1–5):     owner days, custodian involvement
Score:            value × (6 − risk) ÷ effort   (corrective actions and AI concerns bypass scoring: mandatory)
Proposed by:      {upn} (any of the five)
Decision:         scheduled Q{n} | deferred (reason, revisit date) | declined (reason)
```

Scoring keeps the owner honest about a one-person capacity: a quarter
takes at most **6 scheduled improvements** plus every mandatory item;
anything else is deferred with a revisit date, never silently dropped.
Users see the backlog (Jira project read for `sg-infosec-foundry-users`)
so proposals are visible and duplicates are avoided.

## 3. Weekly triage (owner, 30 min, after W1–W8)

| Step | Action |
|---|---|
| 1 | New tickets: complete the template; classify the type; set the change path |
| 2 | Mandatory items (corrective actions, AI concerns, S9/S10/S12): acknowledge to the proposer; open the change or incident now — they do not wait for the quarter |
| 3 | Fixes for a red KPI or a KI with a known workaround: schedule in the current cycle if effort ≤ 1 day, else next cycle |
| 4 | Everything else: score; add to the candidate list for the next quarterly planning |
| 5 | Close items delivered this week with the evidence links (PR, approval run, KPI moved) |

Corrective action discipline (cl. 10.2): the ticket states the
nonconformity, the cause analysis (why the control did not prevent it),
the action, the owner, the due date and — after delivery — the
effectiveness check (the KPI that must move, and by when).

## 4. Quarterly improvement cycle

One cycle per quarter, aligned to the quarterly items already in the kit
(access review, template inventory, comparison-set refresh, alert
thresholds — `CHANGE_MANAGEMENT.md` §9; `QUARTERLY_ACCESS_REVIEW.md`).

| Week | Step | Inputs | Output | Who |
|---|---|---|---|---|
| 1–2 | **Review** the previous quarter: KPI quarter view (`KPIS.md` §3 pack), delivered items and their effectiveness checks, deferred list, access-review findings | monthly KPI notes; Jira | `Governance/Operations/{yyyy}-Q{n}/review.md` §"Improvement" | owner + deputy; line manager for control items |
| 2 | **Plan**: pick ≤ 6 scored items + mandatory ones; assign each its change path and a target KPI; check custodian / IAM lead times; confirm no item weakens an invariant | backlog | plan section of `review.md`; tickets labelled `ci-cycle-{yyyy}-Q{n}` | owner (users consulted in the channel; deputy reviews) |
| 3–11 | **Deliver** through the normal gates: PR flow for prompt/registry/infra/tier items; `template-update-approval` for j; `MEMORY_DELETE` for data hygiene; staged rollout for tier changes (one agent, one week); comparison set where required | `CHANGE_MANAGEMENT.md` §3–§5 | merged PRs, approval runs, release tags (`LIFECYCLE.md` §2) | owner; deputy reviews owner-authored PRs; approvers per tier |
| 12 | **Verify**: effectiveness check per item (did the target KPI move? did the KI close? did the alert stop misfiring?); items without evidence stay open | KPIs, alert history, KI list | `review.md` §"Verification" | owner + deputy (independent) |
| 13 | **Report**: results, targets proposed for next quarter (`KPIS.md` §2 rule), items rolled over, risk acceptances re-confirmed; posted to the channel and filed for the management review | — | `review.md` final; Teams post; ISMS input at year end | owner → line manager, ISMS |

### 4.1 What each stream contributes to the cycle

| Stream | Monthly (feeds) | Quarterly (decides) | Typical improvement | Gate |
|---|---|---|---|---|
| **Evaluation** (`evaluation/EVALUATION.md`; `ARCHITECTURE.md` metrics; RUNBOOK M1) | Q1, Q2, Q4, Q5 per pipeline; verifier FAIL categories; grounding sample; `run_evals.py` metric trends | instruction / knowledge / verifier-rule changes; re-sync when drift is the cause; golden-set / comparison-set refresh with the quarter's best approved outputs (`evaluation/EVALUATION.md` §2; `CHANGE_MANAGEMENT.md` §9) | tighten a verifier rule; add a knowledge pack; fix a section template | Tier C PR + comparison set (medium risk) |
| **FinOps / token economy** (`FINOPS.md` §6; `TOKEN_ECONOMY_PLAYBOOK.md` §1; `MODEL_ROUTING.md` rule 7; RUNBOOK M2, W7) | E2, E3, E4, E8 per agent and tier; 429 share; upload-cache hit rate (`_azure_helpers.py`) | tier moves (never advisory agents down, never below the accuracy floor — `TOKEN_ECONOMY_PLAYBOOK.md` §7 test mandatory); `modelCapacity` changes (`FINOPS.md` §3); budget review (`cost-budget.bicep`); retire unused agents (`LIFECYCLE.md` §6); RAG sizing and single-pass contracts (`TOKEN_ECONOMY_PLAYBOOK.md` §3–§4) | move a rendering-heavy agent to `light`; raise reasoning capacity before a campaign; drop an agent with zero runs in 90 days | Tier C; staged rollout; comparison set for report agents |
| **Monitoring** (`MONITORING.md`; RUNBOOK H1–H9) | alert noise / miss review; H9 schema drift; workbook gaps | threshold changes (`alerts.bicep` params such as `verifierFailRateThreshold`, `dailyTokenBudget`); new KQL for a miss; egress marker list refresh from the current supplier/employee lists (`DATA_PROTECTION_GUARDRAILS.md` §1) | add an internal-marker pattern; split an alert per pipeline; export the workbook JSON | low-risk PR (thresholds) / high-risk if egress rules change |
| **Template governance** (requirement j; `template-update-approval`) | proposals raised; `last_approved` ages; renderer defects | template inventory review: consumers still correct, `deprecated_on` set for unused templates, versions bumped by re-sync reconciled | wording/branding change to a deck; a new section in the evidence-summary DOCX | template approval (owner; deputy if the owner proposed) + `update_templates.py` |
| **Support / usability** (`SUPPORT_MODEL.md` §6–§8) | KI list; post volume by cause; satisfaction | user-guide updates; onboarding changes; Copilot vs pipeline guidance | a Teams form field that pre-fills `serviceName`; clearer verifier findings | docs (low) or prompt (medium) |
| **Resilience / lifecycle** (`BACKUP_DR.md`, `LIFECYCLE.md`) | backup age; retirement notices | restore-test findings; pin bumps; deprecations; environment hygiene | automate the nightly backup; pin an explicit model version | infra PR (medium) |
| **Access / controls** (`QUARTERLY_ACCESS_REVIEW.md`) | H7 reconciliations; PIM report | ledger rows removed; routing changes when Q7 shows an escalation gap; MCP-client register | escalate a report type from Tier A to Tier B | Tier C; line manager for privileged rows |

## 5. Rules that never change inside a cycle

- An improvement that needs a write path, a new Graph permission, a
  `write_connections` entry, a wider `Sites.Selected`, a relaxed RAI
  policy or a change to the egress rules is not an improvement item: it
  is a **risk-acceptance request** to the CISO delegate first
  (`CHANGE_MANAGEMENT.md` §5 "High"), then — if accepted — a high-risk
  change. The backlog template's "Invariant check" line enforces this.
- Advisory agents (g/h/i) stay on the `reasoning` tier whatever the
  FinOps numbers say (`MODEL_ROUTING.md` advisory pin).
- Report agents' outputs are compared before and after (Q4 = 100 %) or
  the change is a *major* release with a new baseline — never a silent
  quality change.
- The owner does not approve the effectiveness of his own change: the
  deputy signs the verification step (week 12) for items the owner
  delivered (A.5.3, A.5.35).
- Users propose freely; only the owner schedules; nobody's proposal is
  closed without a written reason.

## 6. Measures of the improvement process itself

| Measure | Target | Source |
|---|---|---|
| Backlog age (median days open, non-deferred) | ≤ 90 | Jira |
| Mandatory items acknowledged ≤ 1 business day | 100 % | Jira |
| Scheduled items delivered in the quarter | ≥ 80 % | `review.md` |
| Items with a passed effectiveness check | ≥ 80 % of delivered | `review.md` |
| Corrective actions closed within their due date | 100 % (cl. 10.2) | Jira |
| Proposals per quarter from users other than the owner | ≥ 4 | Jira |

Reported in the quarterly pack (`KPIS.md` §3) and, yearly, to the
management review with the KPI trends, the risk acceptances and the
ISO 42001 impact-assessment refresh.

## 7. Annual close

| Item | Action |
|---|---|
| Management review input (ISO 27001 cl. 9.3; ISO 42001 cl. 9.3) | year KPI trends, incidents, corrective actions and their effectiveness, cycle results, deferred backlog, resource needs (owner capacity, licences such as PIM/P2) |
| Policy and control review | `HUMAN_APPROVAL.md`, `DATA_PROTECTION_GUARDRAILS.md`, `MODEL_ROUTING.md`, `TEAM_MODEL.md` ledger re-confirmation |
| AI system impact assessment refresh (ISO 42001 A.5; EU AI Act deployer duties) | with the DPO and ISMS; outcome recorded in the ISMS risk register |
| Targets for next year | proposed by the owner, confirmed by the line manager |
| Re-sync and major-version review | `LIFECYCLE.md` §8 |

## 8. Shared deltas needed by this file (not applied here)

| Id | Target | Location | Literal text |
|---|---|---|---|
| D-CI-S1 | `operations/SUPPORT_MODEL.md` | §7 Feedback loop, end of table intro / after the table | `Every signal above lands in the owner's improvement backlog and is delivered in the quarterly cycle described in CONTINUOUS_IMPROVEMENT.md (signals §1, backlog template §2, weekly triage §3, cycle §4).` |
| D-CI-C1 | `operations/CHANGE_MANAGEMENT.md` | §9 Quarterly row, end | append `; improvement cycle review/plan/verify/report (\`CONTINUOUS_IMPROVEMENT.md\` §4)` |
| D-CI-M1 | `governance/MODEL_ROUTING.md` | rule 7, end | ` Tier proposals from the monthly review are backlog items delivered in the quarterly improvement cycle (operations/CONTINUOUS_IMPROVEMENT.md §4.1 "FinOps").` |
| D-CI-R1 | `operations/RUNBOOK.md` | §6 last sentence | append ` The prevention item is a mandatory backlog entry (CONTINUOUS_IMPROVEMENT.md §1 S9) with an effectiveness check.` |
| D-CI-J1 | Jira project `{jira:INFOSEC-PLAT}` (configuration, not a repo file) | issue types / permissions | add issue types *Improvement* and *Corrective action*, label scheme `ci-cycle-{yyyy}-Q{n}`, browse permission for `sg-infosec-foundry-users`, create permission for the five, edit/close for the owner |
