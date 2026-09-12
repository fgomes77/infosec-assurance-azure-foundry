# Step 03 — Identity, groups, RBAC, agent identities

**Objective.** Create the `sg-infosec-foundry-*` groups with the ownership
lines of the team model, PIM eligibilities, the Conditional Access policy,
the deploy identity, and deploy the role assignments as code
(`team/rbac.bicep` from `infra/main.bicep` with `deployTeamRbac=true`, or
`team/least-privilege/infra/rbac.bicep`) — then account for the **agent
identities** the new service creates automatically.

**Owner / effort.** `{group:iam-admins}` with `{upn:francisco.gomes}`;
3 days. Countersign: `{upn:line-manager}`. **Depends on** 02.

## 1. Platform facts

| Fact | Status / source |
|---|---|
| Built-in roles renamed: `Azure AI User` → **Foundry User** (`53ca6127-db72-4b80-b1b0-d745d6d5456d`), `Azure AI Owner` → Foundry Owner, `Azure AI Account Owner` → Foundry Account Owner, project-manager role likewise; GUIDs unchanged | [GA] https://learn.microsoft.com/en-us/azure/foundry/concepts/rbac-foundry (2026-09-10) |
| Agents / evaluations / workflows need Entra ID auth; API keys give no RBAC granularity | [GA] https://learn.microsoft.com/en-us/azure/foundry/concepts/general-availability (2026-09-09) |
| **Microsoft Entra Agent ID is GA.** Foundry provisions an *agent identity blueprint* and a shared *project agent identity* (service principal) at first agent creation; publishing an agent creates a distinct blueprint + identity; RBAC on tools must be reassigned to that identity on publish | [GA] https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/agent-identity (2026-08-25); https://learn.microsoft.com/en-us/entra/agent-id/whats-new-agent-id (2026-08-13) |
| Conditional Access for data-plane access is supported but not on by default; CAF governance guidance for Foundry | [GA] https://learn.microsoft.com/en-us/azure/cloud-adoption-framework/ai/platform/governance (2026-06-25) |
| Microsoft Agent 365 GA (2026-05-01, per-user licence) extends Entra controls to agents — optional, not required for v1 | [GA] https://www.microsoft.com/en-us/security/blog/2026/05/01/microsoft-agent-365-now-generally-available-expands-capabilities-and-integrations/ (2026-05-01) |

## 2. Groups and roles (from `team/`)

The kit carries two lenses; pick one before executing (index D-decisions
file) — `team/README.md` §3 (seven groups incl. a standing `-owner`) or
`team/least-privilege/IDENTITY_RBAC.md` §1 (six groups, all privilege
PIM-eligible). The steps below use the least-privilege names; map to the
other lens with `team/least-privilege/README.md` "Where this lens differs".

| Group | Members | Owner | Azure role (scope) | PIM |
|---|---|---|---|---|
| `sg-infosec-foundry-users` | the five | `{upn:francisco.gomes}` | **Foundry User** (project) — or the custom `InfoSec Foundry Agent Consumer` role (`team/custom-role.agent-consumer.json`) if the tenant allows custom roles | permanent |
| `sg-infosec-foundry-report-approvers` | the five | owner | none (approval flow only) | — |
| `sg-infosec-foundry-platform-approvers` | owner + deputy | `{group:iam-admins}` | none | — |
| `sg-infosec-foundry-platform-admins` | owner | IAM | Contributor (RG), Foundry account developer role, Key Vault Secrets Officer, Logic Apps Standard Developer/Operator, Website Contributor, Monitoring Contributor, Storage Blob Data Reader | eligible, 2–8 h |
| `sg-infosec-foundry-breakglass` | deputy (eligible) | IAM | same set | eligible, approver = line manager / `{group:soc-oncall}` |
| `sg-infosec-foundry-auditors` | per engagement | owner | Reader, Log Analytics Reader, Logic Apps Standard Reader | — |
| `{app:infosec-foundry-deployer}` (OIDC SP) | — | owner | Contributor + Foundry account developer role (RG), RBAC Administrator with a condition limited to the roles in `rbac.bicep` | — |

Workload identities (all system-assigned MIs, assigned by
`infra/workload-rbac.bicep` and `team/rbac.bicep`): Logic Apps MI →
Foundry User (project) + Key Vault Secrets User + runtime storage; delivery
Function MI → Storage Blob Data Contributor (`deliverables`) + Document
Intelligence user + Key Vault Secrets User; MCP host MI → Foundry User;
Foundry **account** MI → Key Vault Secrets User (connection secrets);
Foundry **project** MI → Graph app roles (step 04) and, with standard
setup, Cosmos DB Built-in Data Contributor, Search Index Data Contributor
+ Search Service Contributor, Storage Blob Data Contributor.

## 3. Click-path

**Entra admin center.** Groups → *New group* (Security, assigned, not
role-assignable) ×6 with owners per table → Identity Governance → PIM →
*Groups* → `sg-infosec-foundry-platform-admins` → eligible assignment
(owner; MFA + justification + ticket; max 8 h) → Access packages →
`ap-infosec-foundry-user` (12 months, approver owner) → Protection →
Conditional Access → `ca-infosec-foundry`: users = the six groups; cloud
apps = *Azure Management*, *Azure AI / Cognitive Services*, *Office 365
SharePoint Online*; grant = MFA + compliant device; sign-in frequency 12 h;
block legacy auth → Enterprise applications → filter *Agent identities* →
after step 06, the project agent identity appears here (owner = the
owner; no directory roles).
**Azure portal.** RG → *Access control (IAM)* → verify assignments after
the Bicep run; *Foundry User* on the project for the users group.
**Foundry portal.** *Home* → project → *Users* (Manage access) shows the
same assignments; `Operate` → *Assets* lists agent identities once agents
exist.

## 4. CLI / Bicep / kit scripts

```bash
cd convertion/team/least-privilege/scripts
./provision_identity.sh --plan                       # from entra/groups.json
./provision_identity.sh --apply                      # groups + owners; writes object ids into ../infra/rbac.parameters.json
# role assignments as code (either module; main.bicep uses team/rbac.bicep when deployTeamRbac=true)
az deployment group create -g rg-infosec-foundry --template-file ../../../infra/main.bicep \
  --parameters ../../../infra/main.parameters.prod.json deployTeamRbac=true \
  usersGroupObjectId={objectId:sg-infosec-foundry-users} ownerGroupObjectId={objectId:sg-infosec-foundry-owner} \
  pimGroupObjectId={objectId:sg-infosec-foundry-admin-pim} breakglassGroupObjectId={objectId:sg-infosec-foundry-breakglass} \
  deployerPrincipalId={principalId:app-infosec-foundry-deployer}
./provision_identity.sh --verify                     # drift check, exit 1 on drift
../../access-review.sh --quick                       # role-assignment evidence
```

Shared delta **S-03** (`setup/provision.sh`, last `echo` lines): replace
`--role 'Azure AI User'` with `--role 'Foundry User'` and add the comment
`# Foundry User = former Azure AI User (same role id 53ca6127-db72-4b80-b1b0-d745d6d5456d)`.
`team/rbac.bicep` assigns by GUID — no change needed; the display names in
`team/*.md` are updated by the integration pass (docs-only change).

Agent identities (after step 06 creates the first agent): record the
project agent identity's object id in `team/ACCESS_REGISTER.md`
("Non-human identities"), set its owner to `{upn:francisco.gomes}`, and
include the *Agent identities* app type in `ca-infosec-foundry` if the
tenant's Conditional Access supports agent principals (Entra Agent ID
what's-new, above). When an agent is **published** (step 09), the new
per-agent identity needs the same Graph app roles as the project MI for
the tools it carries — step 04 §3 is re-run for that identity.

## 5. Values captured into `setup/.env`

| Variable | Value |
|---|---|
| `ENTRA_GROUP_USERS_OBJECT_ID`, `ENTRA_GROUP_REPORT_APPROVERS_OBJECT_ID`, `ENTRA_GROUP_PLATFORM_APPROVERS_OBJECT_ID`, `ENTRA_GROUP_PLATFORM_ADMINS_OBJECT_ID` | `{objectId:…}` from `provision_identity.sh --apply` (shared delta S-04, already proposed by `team/least-privilege/SHARED_DELTAS.md`) |
| `PLATFORM_OWNER_UPN`, `DEPUTY_APPROVER_UPN` | `{upn:francisco.gomes}`, `{upn:deputy-approver}` |
| `APPROVAL_ROUTING_PATH` | `../team/least-privilege/approvals/routing.json` (or `../team/approval-policy.json`) |

## 6. Verification

| # | Check | Pass when |
|---|---|---|
| V1 | `provision_identity.sh --verify` | exit 0 (no drift) |
| V2 | `az role assignment list --scope {project id} --query "[].{p:principalName,r:roleDefinitionName}" -o table` | users group = Foundry User; no human holds Owner / User Access Administrator anywhere in the RG |
| V3 | A user from the group: `az login` → `smoke_test.py --agent dora --prompt "…"` (dev) | answer returned; the same user cannot create an agent (portal *Build → Agents → New* is denied, or the custom role test) |
| V4 | PIM: activation of `platform-admins` requires MFA + justification; deactivation returns the RG to read-only for the owner | activation log entry |
| V5 | Conditional Access *What If* for a user on a non-compliant device against *Azure AI / Cognitive Services* | blocked |
| V6 | `access-review.sh --quick` output filed | matches `team/ACCESS_REGISTER.md` |
| V7 | After step 06: project agent identity listed under Entra *Agent identities* with owner set | screenshot |

**Rollback.** Groups are left in place (empty); role assignments are
redeployed from the previous `rbac.parameters`; `access_snapshot.sh
--tag rollback-{date}` before and after (`operations/access-governance/`).
**ISMS evidence.** snapshot folders, PIM policy export, CA policy JSON —
ISO 27001:2022 A.5.15–A.5.18, A.8.2, A.8.5; DORA Art. 9(4)(c)–(d); NIS2
Art. 21(2)(i)–(j); ISO 42001 A.9.2 (responsible use), A.10.2.

## Sources
- [GA] Foundry RBAC / role rename — https://learn.microsoft.com/en-us/azure/foundry/concepts/rbac-foundry (2026-09-10)
- [GA] Entra-only auth — https://learn.microsoft.com/en-us/azure/foundry/concepts/general-availability (2026-09-09)
- [GA] Agent identity — https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/agent-identity (2026-08-25); https://learn.microsoft.com/en-us/entra/agent-id/whats-new-agent-id (2026-08-13)
- [GA] CAF governance / security baseline — https://learn.microsoft.com/en-us/azure/cloud-adoption-framework/ai/platform/governance (2026-06-25)
- [GA] Agent 365 GA — https://www.microsoft.com/en-us/security/blog/2026/05/01/microsoft-agent-365-now-generally-available-expands-capabilities-and-integrations/ (2026-05-01)
- [community-claim] Agents receive Entra Agent IDs automatically; label inheritance — https://www.engineerup.com/post/microsoft-foundry-agents (2026-08)
