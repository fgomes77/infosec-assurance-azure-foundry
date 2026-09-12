# Least-Privilege-First Team, Identity & Approval Model

One of the lenses on the team/ownership model for the InfoSec Assurance
Foundry platform (the operations-first lens is `../README.md`). This lens
starts from the **minimum each role needs per system a–j and per Azure
resource**, then records every addition with its justification in a
ledger — so an auditor can trace any grant to a reason.

| File | Content |
|---|---|
| `TEAM_MODEL.md` | Three roles (assurance user, platform owner, deputy approver), ownership register, minimum-access matrix per system a–j, **additions ledger** A1–A14 |
| `IDENTITY_RBAC.md` | Entra ID groups (6), Azure RBAC per resource incl. `Azure AI User` vs `Azure AI Developer`, Graph permissions (identity-scoped, `Sites.Selected` read/write), SharePoint site roles, Foundry connection ownership register, Copilot/MCP/GitHub access |
| `APPROVAL_ROUTING.md` | Three approval tiers (peer four-eyes / author sign-off / owner-only), routing matrix, segregation of duties for the owner, break-glass rules, approval evidence |
| `THREADS_MEMORY.md` | Per-user thread conventions, shared team memory rules, no personal store (and why), GDPR minimisation |
| `RACI.md` | RACI for creation, planning, maintenance, optimisation, updates/re-sync, template changes, credential rotation, incident response, evaluation review, cost review, user support, access review, on/offboarding, AIMS records |
| `entra/groups.json` | Group definitions (names, purpose, owners, initial members, review cadence) |
| `approvals/routing.json` | Routing rules consumed by the approval flow behind `approvalWebhookUrl` |
| `infra/rbac.bicep`, `infra/rbac.parameters.json` | Role assignments + PIM eligibilities as code (module for `../../infra/main.bicep`) |
| `scripts/provision_identity.sh` | Creates the groups, sets owners, verifies live role assignments against the model |
| `SHARED_DELTAS.md` | Literal edits for shared kit files (not applied here) |

Operational runbooks for this lens: `../../operations/access-governance/`
(joiner/mover/leaver, quarterly access review, break-glass, evidence
snapshot script).

## Where this lens differs from the operations-first lens (`../README.md`)

| Topic | Operations-first (`../README.md`) | Least-privilege-first (this folder) | Reconciliation hint |
|---|---|---|---|
| Groups | 7 (`users`, `report-approvers`, `senior-approvers`, `owner`, `admin-pim`, `breakglass`, `readers`) | 6 (`users`, `report-approvers`, `platform-approvers`, `platform-admins`, `breakglass`, `auditors`) — no standing `owner` group: the owner's privileged roles are all PIM-eligible through `platform-admins` | `senior-approvers` ≈ `platform-approvers`; `owner`+`admin-pim` ≈ `platform-admins` (this lens has no standing `Azure AI Developer`) |
| Stakeholder-facing reports (b, c, d) | Tier B: owner or deputy approves | Tier 1: any peer ≠ requester approves | Least privilege prefers the wider peer set (no bottleneck on two people); the operations lens prefers the accountable signature. Pick per ISMS policy |
| Internal reports (a, d2, e, f) | Tier A: peer four-eyes | Tier 2: author sign-off + 10 % quarterly peer sampling, escalating to peer four-eyes when stakeholder-facing | Both satisfy "human before write"; this lens removes one approval per internal run |
| Users' monitoring access | `Monitoring Reader` for users | none for users | Least privilege: users get results in-thread; add `Monitoring Reader` only if the cost review needs self-service |
| Custom "agent-consumer" role | Proposed (Azure AI User minus agent-authoring data actions) | Not proposed; compensating detective + re-sync controls | Adopt the custom role if the tenant permits custom roles — it is the stricter option |
| Owner's own platform change | Owner approves with deputy code review | Deputy approves (owner cannot approve his own tier-3 change) | Stricter SoD in this lens |
