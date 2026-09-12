# Break-Glass Runbook — Emergency Platform Access

Purpose: keep the platform maintainable when the owner is unavailable or
during an incident, **without** creating a second standing administrator.
Break-glass grants *access*, never *approval* — every Tier A / B / C
approval in `../../team/TEAM_MODEL.md` §12 (enforced from
`../../team/approval-policy.json`) still requires the designated human.
Model: `TEAM_MODEL.md` §12.3. Controls: ISO/IEC 27001:2022 A.8.2, A.5.3, A.5.24–A.5.26 (incident
management); DORA Art. 9(4)(c), Art. 17 (ICT incident process).

## 1. Triggers

| Trigger | Example | Allowed actions during the window |
|---|---|---|
| Owner unavailable > 2 business days with a pending Tier C item | Template update waiting, PIM-only fix needed | Deputy approves the owner's Tier C item (`approval-policy.json` `tiers.C.requester_is_owner_fallback` — no break-glass needed for the *approval*); Tier B requests by the owner fall back to a peer after 2 business days; break-glass only if an Azure change is needed |
| P1/P2 platform incident | Egress alert with confirmed internal identifier leak, credential exposure, runaway cost, pipeline writing wrong files | **Disable**: a Logic Apps workflow, a Foundry connection, an agent's tool; rotate/disable a Key Vault secret; stop the Function. **Change** (edit instructions, redeploy) only with the owner's retrospective approval recorded in the ticket |
| Regulatory/audit deadline requiring evidence extraction | Auditor needs Log Analytics export today | Read-only actions (already covered by `sg-infosec-foundry-readers`, ledger row L15 — prefer that path) |

## 2. Procedure

| # | Step | Who | Evidence |
|---|---|---|---|
| 1 | Open incident/ticket `{jira:INFOSEC-PLAT}-nnn` stating trigger, intended actions, expected duration | `{upn:deputy-approver}` | Ticket |
| 2 | Activate PIM eligibility on `sg-infosec-foundry-breakglass` (max 8 h, MFA, justification = ticket id) | deputy | PIM request |
| 3 | Approve activation | `{upn:line-manager}` or `{group:soc-oncall}` | PIM approval record; alert to the owner group address `{email:sg-infosec-foundry-owner}` |
| 4 | Perform only the actions listed in the ticket; prefer disable over change; log each action in the ticket as it happens | deputy | Activity Log, Foundry tracing, ticket comments |
| 5 | Deactivate the role as soon as done (do not wait for expiry) | deputy | PIM deactivation |
| 6 | Post-review within 5 business days: owner compares the Activity Log / diagnostic logs of the window with the ticket; any unlisted action becomes a finding | `{upn:francisco.gomes}` | `Governance/AccessReviews/breakglass-{ticket}.md` |
| 7 | If any Key Vault secret value was read, rotate it (custodian issues a new token) | owner + custodian | Key Vault version id |
| 8 | Quarterly review item 4 lists every activation | line manager | Sign-off |

## 3. What break-glass can never do

- Approve a report, template or platform change on its own authority.
- Add members to `sg-infosec-foundry-owner`, `-senior-approvers`, `-admin-pim` or `-breakglass` (group owner = `{upn:line-manager}`, executed by `{group:iam-admins}`); the break-glass role set carries no `RBAC Administrator`.
- Grant `write_connections` to any agent, change `Sites.Selected` grants, or consent Graph permissions — these are Tier C changes with a PR.
- Exceed 8 hours or be activated twice for the same incident without a new line-manager approval.

## 4. Detective controls around the window

| Signal | Where |
|---|---|
| PIM activation / deactivation | Entra PIM audit → alert to owner and line manager |
| Every ARM write during the window | Activity Log alert `breakglass_window_write` (`operations/alerts.bicep`; `operations/MONITORING.md` §4) |
| Agent definition change during the window | `agent_modified_by_non_deploy_identity` alert (`operations/alerts.bicep`) |
| Key Vault `SecretGet` during the window | Key Vault diagnostic logs → Log Analytics |
