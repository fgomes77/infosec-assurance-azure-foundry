# Support Model — L1 Self-Service · L2 Owner · L3 Microsoft / Landing Zone / Custodians

How the five assurance users get help with the platform, what response
they can expect, and how their feedback changes the platform. The team
model (`../team/TEAM_MODEL.md` §3 flow F12) fixes the chain *requester →
peer (L1) → owner (L2) → landing-zone / Microsoft (L3)*; this file makes
it operable. Procedures for actual failures are in `RUNBOOK.md`; changes
that result from support go through `CHANGE_MANAGEMENT.md`.

## 1. Tiers

| Tier | Who | Handles | Does not handle | Access used |
|---|---|---|---|---|
| **L0 — self-help** | the requester | known-issue list (§6), user guides per system a–j, re-running a run, re-triggering an expired approval, re-authenticating (`az login`), saving/searching memory | anything touching configuration | own Entra user only |
| **L1 — peer** | any other member of `sg-infosec-foundry-users` | "how do I" questions, prompt shaping, checking an approval is pending on the right person, reproducing an issue, confirming a P-level | RBAC, connections, secrets, redeploys | own Entra user; peer approver role (Tier A) |
| **L2 — owner** | `{upn:francisco.gomes}` (deputy `{upn:deputy-approver}` when the owner is unavailable, disable-only) | diagnosis with `Log Analytics Reader`; fixes needing PIM; all Tier C changes; tier tuning; re-sync; template propagation; incident lead | target-system faults; subscription/network/policy issues; Microsoft service incidents | standing `Reader` + `Log Analytics Reader`; PIM roles per `../team/TEAM_MODEL.md` §5 |
| **L3 — external** | landing zone `{group:azure-platform}` / IAM `{group:iam-admins}`; custodians (`{group:jira-admins}`, `{group:onetrust-admins}`, `{group:enx-gateway}`, `{upn:iaf-owner}`, `{group:spo-admins}`); Microsoft support (via the landing-zone support plan) | subscription, VNet, policy, CA/PIM, Graph consents; service-account tokens and target-system outages; Foundry / Logic Apps / Functions service issues | anything inside the platform's own configuration | their own |

Control: ISO 27001:2022 A.5.2 (roles), A.5.24 (incident planning),
A.6.3 (users know where to get help); DORA Art. 5(2); ISO 42001 A.3.2.

## 2. Service-level objectives

Measured monthly by the owner (RUNBOOK §2 M1) from `{list:ApprovalDecisions}`,
`LogicAppWorkflowRuntime` and the ticket queue; reported in the ISMS
operating rhythm.

| SLO | Target | Source of measurement |
|---|---|---|
| First response to a support post | ≤ 4 business hours (L1), per `RUNBOOK.md` §3 for incidents | Teams thread timestamps / ticket |
| Conversational systems (g, h, i) availability, business hours | ≥ 99 % of calendar business hours | `AppRequests` success rate on `{baseName}-proj`; `model-throttling-429` |
| Report pipeline success (a–f, d2) | ≥ 95 % of runs reach the approval gate without a technical failure | `pipeline-run-failed`, `kql/verifier-fail-rate.kql` |
| Verifier first-pass PASS rate | ≥ 70 % per pipeline (alert at < 70 %) | `kql/verifier-fail-rate.kql` |
| Approval decision (human) | ≤ 2 business days from gate start; never past the P3D expiry | `kql/approval-sla.kql` |
| Time from approval to stored report | ≤ 15 min | run history `If_approved` → `Upload_and_share` |
| Template change (j) end-to-end | ≤ 5 business days from proposal to propagation | `template-update-approval` run history + `../templates/registry.json` `last_approved` |
| Joiner access | same day (`access-governance/ACCESS_LIFECYCLE.md`) | access package record |
| Security alert acknowledgement (severity 1) | ≤ 1 h | Azure Monitor alert state |

SLOs are objectives of an internal service run by one owner; they are not
contractual. A missed SLO in two consecutive months is a finding for the
monthly review with a corrective action (ISO 27001:2022 cl. 10.2; ISO
42001 cl. 10.2).

## 3. Intake

| Channel | Use | Record |
|---|---|---|
| Teams channel `{teams:infosec-assurance-platform}` | every question, issue and idea; L1 happens here | thread |
| Jira `{jira:INFOSEC-PLAT}` | opened by the owner for every P1–P3 and every change request; users may open P4 directly | ticket = record of record |
| Teams Approvals | approvals only — never support | `{list:ApprovalDecisions}` |
| Ticket to the custodian's own queue | L3 target-system items, opened by the owner with the platform ticket referenced | their record |

Intake template (paste into the Teams post; no report content, secrets or
personal data — thread ids and run ids only):

```
System (a–j) / agent:        e.g. d2 tpa-evidence-analyzer
What I did:                  trigger / prompt shape (no internal text)
What happened:               error text, or "no answer after N min"
Ids:                         thread_id / run id / Logic Apps run name / correlationId
Impact:                      me only | several users | a due report (supplier, due date)
Severity I think:            P1–P4 (RUNBOOK §3)
Already tried:               re-run | re-login | peer check
```

Triage rules: the first peer to respond confirms L0/L1 or hands to L2 by
tagging the owner; the owner sets the severity and opens the ticket for
P1–P3; requests that would change configuration become change requests
(`CHANGE_MANAGEMENT.md` §3) whatever the channel they arrived in.

## 4. What L1 may and may not do

| May | May not |
|---|---|
| Read the requester's thread to reproduce (threads are team-visible working papers — `../team/TEAM_MODEL.md` §13) and re-run in a **new** thread of their own | Post into, upload to, or delete files from another user's thread (attribution stays with its `owner_upn`) |
| Check who the pending approval sits with (`{list:ApprovalDecisions}`, Teams Approvals) and nudge them | Approve their own request, or an item outside their tier |
| Reproduce with a synthetic supplier (no real assessment data) | Paste assessment content, findings or scores into the channel |
| Read the known-issue list and the user guides | Change any setting, tool, template or instruction (no access exists to do so) |
| Propose a template change via `template-manager` (F4) | Approve it (Tier C is owner-only; deputy if the owner proposed it) |

## 5. What L2 does with a ticket

1. Classify: incident (RUNBOOK §3) or change request (CHANGE_MANAGEMENT §3).
2. Diagnose read-only first (`Log Analytics Reader`, run history, `--dry-run` scripts); activate PIM only when a fix needs it, with the ticket id as justification.
3. Prefer *disable* over *change* while a P1 is open; changes go through a PR even when urgent (§8 emergency change).
4. Close with the evidence links and, for P1/P2, the post-incident note (RUNBOOK §6).
5. Feed the feedback loop (§7).

## 6. Known-issue list (maintained monthly, RUNBOOK M3)

| Id | Issue | Workaround | Permanent fix (ticket) |
|---|---|---|---|
| KI-01 | Reasoning-tier runs (deepsearch, evidence analysis) can take several minutes; Copilot times out | use the pipeline (Teams form / MCP), not Copilot, for report-producing agents (`../integrations/copilot/README.md`) | by design |
| KI-02 | PPTX renders only in the delivery Function (Node runtime); code_interpreter cannot run the JS generators | request the pipeline; the agent's in-thread output is the verified JSON, not the deck | by design (`../README.md` limitation 3) |
| KI-03 | Approval expired after 3 days | requester re-triggers; nothing was stored | by design (`../governance/HUMAN_APPROVAL.md`) |
| KI-04 | `serviceName` omitted on d2 | the pipeline asks for it before storage; supply both names at trigger time | — |
| KI-05 | Web results missing on an advisory answer | the query was sanitised or Bing is unavailable; the agent reasons from internal sources — ask it to state which sources it used | — |
| KI-06 | Content filter blocks a legitimate exploit description | rephrase; report the run id so the RAI severity can be tuned (RUNBOOK FM-04) | `{ticket}` |
| `{KI-nn}` | `{issue}` | `{workaround}` | `{ticket}` |

## 7. Feedback loop

| Signal | Collected how | Goes to |
|---|---|---|
| Rework on approved reports (approver edits before approving) | `reviewedBy` / decision comments in `{list:ApprovalDecisions}`; quarterly 10 % Tier A sample (`../team/TEAM_MODEL.md` §12.1) | M1 evaluation → instruction/knowledge change (Tier C) or template proposal (j) |
| Verifier FAIL reasons | `kql/verifier-fail-rate.kql`; the FAIL findings in the run output | same |
| Template wishes | `template-manager` proposals (F4) | `../workflows/template-update-approval.json` |
| Tier/cost | `kql/latency-and-tokens.kql` | M2 tier tuning (`../governance/MODEL_ROUTING.md` rule 7) |
| Memory quality | `memory_store.py list` review at W5 | delete/curate per §13 of the team model |
| User satisfaction | one question per month in the channel (1–5, free text) | M1 note; trend reported quarterly |
| Onboarding friction | joiner attestation (`access-governance/ACCESS_LIFECYCLE.md` §1) | user-guide update |

Control: ISO 27001:2022 cl. 9.1, 10.1; ISO 42001 cl. 9.1, A.6.2.6
(monitoring), A.8.2 (documentation for users), A.8.3 (external reporting of
AI concerns — users can report any concern with an AI output through this
model); EU AI Act Art. 26(5), 26(7) (deployer monitoring and informing
workers); DORA Art. 13(6) (lessons learned feed staff awareness).

## 8. User guides

One page per system a–j, kept under `Governance/UserGuides/` on the site
(owner-maintained, reviewed after every re-sync). Each guide states: how
to start (portal / Copilot / MCP / Teams form), the inputs the pipeline
requires (`supplierName`, `serviceName`, the PDF), who approves (tier),
where the output lands (`Reports/<Supplier>/<Service>/` or
`Reports/DPO/…`), what the agent will not do (write anywhere, search the
web with internal text), and the KI-ids that apply. The persona is the
same for every user, so the guides carry no per-user variants.
