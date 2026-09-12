# Step 10 — Go-live, hypercare, hand-over to operations

**Objective.** Confirm every gate, provision the five users, cut over
from claude.ai to the Foundry platform with a four-week hypercare period,
and hand the service to the operating model already written in `team/`
and `operations/` — with the dates the platform imposes (classic runtime
retirement, model retirements) on the calendar.

**Owner / effort.** `{upn:francisco.gomes}` with the four users; 2 days
+ 20 days hypercare. Countersign: `{upn:line-manager}`. **Depends on** 01–09
(all gates in `prod`).

## 1. Go-live readiness (all must be true)

| # | Condition | Evidence |
|---|---|---|
| R1 | Gates 00–09 signed in `prod` (index §4) | `Governance/Implementation/prod/NN/sign-off.md` ×10 |
| R2 | Comparison set passes in `prod` on the pinned model versions (step 06 V5) and the evaluation baseline is filed (step 08 E2) | tables |
| R3 | UAT sign-offs from the four users (`test`) and the owner's release note `Governance/Releases/{tag}.md` (`operations/LIFECYCLE.md` §2) | files |
| R4 | Access provisioned: each user through `team/ONBOARDING.md` §1–§3 (access package → `sg-infosec-foundry-users`, Teams channels `{teams:infosec-assurance-platform}` / `{teams:infosec-assurance-approvals}`, MCP client registered); `access_snapshot.sh --tag golive` | snapshot folder |
| R5 | Support model live: L1 peer / L2 owner / L3 landing zone–Microsoft–custodians (`operations/SUPPORT_MODEL.md` §1–§3); known-issue list initialised | Teams channel pinned post |
| R6 | Monitoring: alert catalogue enabled, workbook published, budgets on (`operations/MONITORING.md` §4–§5, `FINOPS.md` §4) | H1–H7 checks green for 5 consecutive days in `prod` |
| R7 | Backup / DR: `operations/BACKUP_DR.md` §3 backups scheduled (memory/knowledge export to `deliverables`, Logic Apps definitions in git, Bicep in git; Cosmos DB continuous backup if standard setup); one restore test done in `test` (§6) | test record |
| R8 | ISMS records: RoPA updated (step 08), AIMS scope + SoA updated for the Foundry and Copilot channels, EU AI Act deployer assessment filed, DORA register-of-information entry for the internal ICT service (`{cmdb:infosec-foundry}`) | documents |
| R9 | Claude.ai environment set to **read-only reference** for four weeks (no new deliverables produced there); export tag recorded | decision in the release note |
| R10 | Line-manager countersign | sign-off |

## 2. Cut-over (one day)

| Time | Action | Who |
|---|---|---|
| T-1 d | Freeze: no platform change PRs merged during cut-over week except emergency (`operations/CHANGE_MANAGEMENT.md` §8) | owner |
| T0 09:00 | `deploy.sh` from the release tag under the deploy SP; H8 drift check (`build/manifest.json` vs baseline) | pipeline / owner |
| T0 10:00 | Enable the routine workflows one by one: `onetrust-assessment-intake`, `scheduled-deepsearch`, `jira-finding-sync`, `mailbox-intake`, `morning-brief` ×5 (`operations/LIFECYCLE.md` §6 order in reverse: enable → observe) | owner (PIM Logic Apps Operator) |
| T0 11:00 | Teams announcement in `{teams:infosec-assurance-platform}`: quickstart link (`team/USER_QUICKSTART.md`), the three invariants, how to ask for help | owner |
| T0 14:00 | First production runs: one advisory question per user; one report pipeline (a or e) approved by a peer; results checked against the comparison set where applicable | users + owner |
| T0 17:00 | Day-1 review: H1–H7, `egress-detection.kql`, cost snapshot; go / no-go for day 2 | owner |

## 3. Hypercare (4 weeks)

| Cadence | Activity | Source |
|---|---|---|
| Daily | H1–H7 health checks (~10 min); triage of every Sev-1/2 alert the same day; user questions answered in the Teams channel within the L1/L2 SLOs | `operations/RUNBOOK.md` §2, `SUPPORT_MODEL.md` §2 |
| Daily | Human-evaluation feedback (step 08 E4) reviewed; verifier FAIL reasons clustered | App Insights |
| Weekly | W1–W7 (smoke test, read-only surface, gate presence, connections, memory store, credential ages, cost); hypercare note `Governance/Operations/{yyyy}-{mm}/hypercare-w{n}.md` with KPIs: verifier first-pass rate, approval turnaround, tokens per deliverable per tier, p95 latency, cost vs budget, egress alerts (0), incidents | `operations/RUNBOOK.md`, `MONITORING.md`, `FINOPS.md` §2 |
| Week 2 | Token-economy review: any agent moving tiers goes through `operations/TOKEN_ECONOMY_PLAYBOOK.md` (advisory agents never below `reasoning`) | `governance/MODEL_ROUTING.md` rule 7 |
| Week 3 | DR drill (region-failure playbook table-top; restore of the memory store from the last export) | `operations/BACKUP_DR.md` §5–§6 |
| Week 4 | Exit review with the four users and the line manager; hypercare exit criteria: 10 consecutive business days without Sev-1, verifier first-pass ≥ 70 %, every pipeline a–f run at least once to `STORED`, cost within budget, no open Sev-2 | minutes in `Governance/Reviews/` |

Fallback during hypercare: a deliverable that cannot be produced on the
platform is produced on claude.ai from the same export version (R9) and
filed to SharePoint by the owner **manually with the same folder rule**;
the incident is logged (`RUNBOOK.md` §6) and drives a Tier C fix.

## 4. Hand-over to operations (the operating model that already exists)

| Area | Document of record | First scheduled occurrence |
|---|---|---|
| Day-2 health, failure modes, escalation | `operations/RUNBOOK.md` | daily from T0 |
| Signals, alerts, workbook | `operations/MONITORING.md`, `operations/alerts.bicep`, `operations/kql/`, `infra/kql/` | continuous |
| Support tiers, SLOs, feedback loop | `operations/SUPPORT_MODEL.md` | T0 |
| Change process (PR-based, comparison set, emergency change, calendar) | `operations/CHANGE_MANAGEMENT.md` | first monthly review |
| Versioning, re-sync, pinning, deprecation | `operations/LIFECYCLE.md` | first re-sync from a fresh export (quarterly) |
| Cost, capacity, budgets | `operations/FINOPS.md`, `operations/cost-budget.bicep`, `TOKEN_ECONOMY_PLAYBOOK.md` | month-end M2 |
| Backup / DR | `operations/BACKUP_DR.md` | week 3 drill, then semi-annual |
| Access lifecycle, quarterly review, break-glass | `operations/access-governance/ACCESS_LIFECYCLE.md`, `QUARTERLY_ACCESS_REVIEW.md`, `BREAK_GLASS.md`, `team/access-review.sh`, `access_snapshot.sh` | first quarter end |
| Team model, RACI, approvals, threads/memory, on/offboarding | `team/README.md` / `team/least-privilege/*`, `team/RACI.md`, `team/approval-policy.json`, `team/ONBOARDING.md`, `team/OFFBOARDING.md`, `team/ACCESS_REGISTER.md` | as events occur |
| User guides | `team/USER_QUICKSTART.md` (systems a–j) | T0 |

## 5. Platform calendar (dates the operating model must carry)

| Date | Event | Action | Source |
|---|---|---|---|
| 2026-12-01 | Foundry portal *workflows* retire | none (not used) — verify nothing was created in the portal | index D12 |
| 2027-01-14 (≈ 90 days before) | replacement declared for `gpt-4o` / `gpt-4o-mini` (Microsoft declares 90–120 days before retirement) | start the D4 replacement project: fourth deployment, comparison set, staged tier switch | https://learn.microsoft.com/en-us/azure/foundry/openai/concepts/model-retirements (2026-07-24) |
| 2027-03-31 | classic Foundry Agent Service retires | the platform is already on the new runtime (step 06); confirm no classic SDK remains (`pip list \| grep azure-ai-agents` empty) | https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/migrate (2026-08-05) |
| 2027-04-14 | `gpt-4o 2024-11-20`, `gpt-4o-mini 2024-07-18` retire | tiers switched before this date | https://learn.microsoft.com/en-us/azure/foundry/openai/concepts/model-retirement-schedule (2026-09-02) |
| monthly | `azure-ai-projects` minor releases (≈ every 4–6 weeks) | M3 patch review; never a model and an SDK bump in the same release (`LIFECYCLE.md` §5) | https://github.com/Azure/azure-sdk-for-python/blob/main/sdk/ai/azure-ai-projects/CHANGELOG.md (2026-09-04) |
| quarterly | access review; template inventory; re-sync from export; memory prune | `QUARTERLY_ACCESS_REVIEW.md`; `CHANGE_MANAGEMENT.md` §9 | kit |
| when GA | A2A tool, Logic Apps Agent action, Foundry IQ SharePoint indexed source, Memory | re-evaluate D2, step 07 §3 rule, D5 (`enterprise/memory-learning/`) | index §5 |

## 6. Values captured into `setup/.env`

None new. The release note records the `.env` variable inventory (names
only) so a rebuild from git + Key Vault + this series is reproducible.

## 7. Verification (hypercare exit)

| # | Check | Pass when |
|---|---|---|
| V1 | R1–R10 true at T0 | checklist signed |
| V2 | Hypercare KPIs at week 4 | exit criteria of §3 met |
| V3 | `operations/kql/egress-detection.kql` over the four weeks | 0 rows |
| V4 | Every pipeline a–f, g/h `advisory-file-delivery` and `template-update-approval` executed at least once in `prod` with a real approval | run ids in the exit note |
| V5 | `provision_identity.sh --verify`, `access-review.sh --quick` | no drift |
| V6 | Cost month 1 vs `operations/FINOPS.md` §1 model (re-based for the EU Data Zone price change) | within ±25 % or explained |
| V7 | Line manager countersign of the exit review | sign-off |

**Rollback.** Fallback per §3 (claude.ai reference environment for the
duration of hypercare); platform rollback = previous release tag via
`deploy.sh` and Bicep, Logic Apps instances disabled, Copilot publication
withdrawn (step 09). **ISMS evidence.** readiness checklist, cut-over
log, weekly hypercare notes, exit review — ISO 27001:2022 A.5.37 (operating
procedures), A.8.32, A.5.30 (ICT readiness); DORA Art. 9, 11, 28(8);
ISO 42001 A.6.2.6–A.6.2.8, A.10.4; EU AI Act Art. 26(5) (monitoring by
deployers).

## Sources
- [GA] Model lifecycle and retirement schedule — https://learn.microsoft.com/en-us/azure/foundry/openai/concepts/model-retirements (2026-07-24); https://learn.microsoft.com/en-us/azure/foundry/openai/concepts/model-retirement-schedule (2026-09-02)
- [GA] Classic runtime retirement — https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/migrate (2026-08-05)
- [GA] SDK cadence — https://github.com/Azure/azure-sdk-for-python/blob/main/sdk/ai/azure-ai-projects/CHANGELOG.md (2026-09-04)
- [GA] Model migration process — https://learn.microsoft.com/en-us/azure/foundry/foundry-models/concepts/model-migration (2026-08-26)
- [announced] Euronext strategic-plan AI statement (public) — https://www.euronext.com/en/about/media/euronext-press-releases/euronext-announces-its-new-strategic-plan-innovate-for-growth (2024-11-07)
- Kit: `team/*`, `operations/*` as listed in §4
