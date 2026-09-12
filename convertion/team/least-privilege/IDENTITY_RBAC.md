# Identity & RBAC — Entra ID Groups, Azure Roles per Resource, SharePoint, Connections

> **HISTORICAL DESIGN VARIANT — not the model of record.** This file is the
> least-privilege lens kept as a design record; it uses a superseded
> vocabulary (six groups, approval tiers 1/2/3). The authoritative model is
> `../TEAM_MODEL.md` (decisions in §21) with `../RACI.md`,
> `../approval-policy.json` and `../rbac.bicep`. See `README.md` in this
> folder for the name mapping. Do not implement from this file.

Principles: Entra ID identities everywhere (the Foundry account already
sets `disableLocalAuth: true`); managed identities for every workload;
groups, never individual role assignments, for humans; privileged roles
**eligible** (PIM), not permanent; one writer to SharePoint; no keys in
the repo. Controls cited: ISO 27001 A.5.15/A.5.16/A.5.18/A.8.2/A.8.5,
DORA Art. 9(4)(c)–(d), NIS2 Art. 21(2)(i)–(j).

## 1. Entra ID security groups

| Group | Purpose | Members (initial) | Group owner (can add/remove) | Who may request additions | Review |
|---|---|---|---|---|---|
| `sg-infosec-foundry-users` | Assurance users: `Azure AI User` on the Foundry project; audience for the Copilot Studio agent; allowed group for hosted-MCP Easy Auth; SharePoint site membership | `{upn:francisco.gomes}`, `{upn:jose.mogollon}`, `{upn:pedro.santos}`, `{upn:jose.meireles}`, `{upn:tania.morais}` | `{upn:francisco.gomes}` | Line manager of the joiner, via Entra access package `ap-infosec-foundry-user` | Quarterly Entra access review, reviewer = group owner |
| `sg-infosec-foundry-report-approvers` | Four-eyes approvers of tier-1 reports and Jira/IAF submissions (approval flow resolves this group minus the requester) | same five | `{upn:francisco.gomes}` | Owner | Quarterly |
| `sg-infosec-foundry-platform-approvers` | Approvers of template, platform, prompt, registry changes | `{upn:francisco.gomes}`; `{upn:deputy-approver}` (used only when requester = owner) | **Entra IAM team**, not the owner (the owner cannot widen who approves his changes) | Owner, with `{upn:line-manager}` confirmation | Quarterly, reviewer = line manager |
| `sg-infosec-foundry-platform-admins` | Azure privileged roles (all PIM-eligible) listed in §2 | `{upn:francisco.gomes}` | Entra IAM team | Line manager | Quarterly, reviewer = line manager; PIM activations reviewed monthly |
| `sg-infosec-foundry-breakglass` | Eligible (never active by default) membership that grants the platform-admin role set for a bounded window | none active; eligible: `{upn:deputy-approver}` | Entra IAM team | Deputy, on incident/unavailability trigger (`../../operations/access-governance/BREAK_GLASS.md`) | Each activation reviewed by owner within 5 business days |
| `sg-infosec-foundry-auditors` | Read-only evidence access for internal audit / certification bodies | none | `{upn:francisco.gomes}` | Head of internal audit | Populated per engagement, emptied after |

Design notes:

- Groups are **role-assignable = no** (they carry Azure RBAC, not Entra
  directory roles) and **dynamic = no** (membership is a deliberate act).
- The owner owns the groups he uses to run the team, but **not** the
  groups that grant him privilege or approve his changes — that is the
  segregation-of-duties line (A.5.3).
- Conditional Access policy `ca-infosec-foundry`: MFA + compliant device
  for the Azure Management and Azure AI/Cognitive Services cloud apps,
  scoped to these groups (A.8.5, DORA Art. 9(4)(d), NIS2 Art. 21(2)(j)).
- Machine-readable definition: `entra/groups.json`; creation script:
  `scripts/provision_identity.sh`.

## 2. Azure RBAC per resource

Scope column is the narrowest scope that works. **P** = PIM-eligible
(activation with MFA + justification, max duration shown); **perm** =
permanent. Role GUIDs are in `infra/rbac.bicep`.

| Resource | `sg-infosec-foundry-users` | `sg-infosec-foundry-platform-admins` (owner) | `sp-infosec-foundry-deploy` (GitHub OIDC) | Workload managed identities | Auditors |
|---|---|---|---|---|---|
| Resource group `rg-infosec-foundry` | — | `Reader` perm; `Contributor` P 8 h | `Contributor`; `Role Based Access Control Administrator` with condition: may assign only the roles listed in `infra/rbac.bicep` | — | `Reader` |
| Foundry account `{baseName}-aif` | — | `Azure AI Developer` P 8 h (agents, vector stores, connections, deployments via portal when the pipeline cannot) | `Azure AI Developer` | Foundry account MI: `Key Vault Secrets User` on the platform Key Vault (connection secrets by reference) | — |
| Foundry project `{baseName}-proj` | `Azure AI User` perm | `Azure AI User` perm (as a user) | inherits | Logic Apps MI: `Azure AI User`; hosted MCP (Container Apps) MI: `Azure AI User`; Copilot Studio connector: delegated (user token) preferred, else its app registration `Azure AI User` | — |
| Model deployments (`gpt-4o`, `o3-mini`, `gpt-4o-mini`) | via `Azure AI User` data actions | via `Azure AI Developer` (capacity, RAI policy) | Bicep-managed | — | — |
| Key Vault `{baseName}-kv` (RBAC authorisation mode, purge protection on) | — | `Key Vault Secrets Officer` P 2 h | `Key Vault Secrets Officer` (seeding only; secrets values come from the pipeline's environment, never the repo) | Logic Apps MI: `Key Vault Secrets User`; Foundry account MI: `Key Vault Secrets User`; delivery Function MI: none (uses MI to Graph, needs no secret) | — |
| Delivery Function App `{delivery-function}` | — | `Website Contributor` P 4 h | `Website Contributor` | Function MI: `Storage Blob Data Contributor` on its runtime storage; Graph `Sites.Selected` write on the one site (not an Azure role) | — |
| Logic Apps Standard `{logicapp-name}` | — | `Logic Apps Standard Developer` P 8 h; `Logic Apps Standard Operator` P 8 h | `Logic Apps Standard Contributor` | Logic Apps MI: `Storage Blob Data Contributor` + `Storage Queue/Table Data Contributor` on its runtime storage; `Azure AI User` on project; `Key Vault Secrets User` | `Logic Apps Standard Reader` (approval evidence in run history) |
| Storage `{baseName}sa` / `deliverables` container | — | `Storage Blob Data Reader` P 4 h | `Storage Account Contributor` | Function MI: `Storage Blob Data Contributor` scoped to the `deliverables` container | — |
| Log Analytics `{baseName}-logs` / App Insights `{baseName}-appi` | — | `Log Analytics Reader` perm; `Monitoring Contributor` P 4 h (alert rules) | `Monitoring Contributor` | Foundry project MI: `Monitoring Metrics Publisher` | `Log Analytics Reader` |
| Bing Grounding account `{baseName}-bing` | via the project connection only | `Reader` (usage), keys read only by Bicep at deploy | Bicep-managed | — | — |
| Container Apps (hosted MCP, optional) | Easy Auth allowed group `sg-infosec-foundry-users` | `Contributor` on the Container App P 4 h | `Contributor` | Container App MI: `Azure AI User` on project | — |

Why no `Owner`/`User Access Administrator` for any human: role
assignments are code (`infra/rbac.bicep`) applied by the deploy identity
under a constrained RBAC-Administrator condition; changing who can do
what therefore always leaves a PR, a review and a deployment record
(A.5.18, DORA Art. 9(4)(e)).

### `Azure AI User` vs `Azure AI Developer`

| Capability | Azure AI User (five users) | Azure AI Developer (owner, PIM) |
|---|---|---|
| Open the project in the Foundry portal, playground | yes | yes |
| Run any agent, create threads/runs, upload files to a thread, download generated files | yes | yes |
| Create/update/delete **agents**, vector stores, knowledge files | should be no — see note | yes |
| Create/modify **connections** (`conn-*`), model deployments, RAI policies | no | yes |
| Manage role assignments | no | no (deploy identity only) |

Note on agent-definition drift: Foundry role definitions evolve; verify the
effective data actions at deployment (`az role definition list --name
"Azure AI User" --query "[].permissions[].dataActions"`). If the tenant's
version of `Azure AI User` includes agent-write data actions, the
compensating controls are (1) `deploy.sh` is idempotent by agent name and
overwrites drift on every re-sync, (2) the Activity/diagnostic-log alert
`agent_modified_by_non_deploy_identity` in the operations layer, and
(3) the quarterly review compares live agent instructions to
`build/agents/*/instructions.md` (`scripts/verify_conversion.py`).

## 3. Microsoft Graph application permissions (identity-scoped, all read except one)

| Identity | Permission | Grant scope | Used by | Why not broader |
|---|---|---|---|---|
| Delivery Function MI (`infosec-delivery-fn`) | `Sites.Selected` — site permission **write** | the InfoSec Assurance site only | `ensure_folder`, `upload`, `createLink` | The only writer; `Sites.ReadWrite.All` would reach every site in the tenant |
| Foundry project MI (OpenAPI tools with managed-identity auth) | `Sites.Selected` — site permission **read** | same site (`Reports/`, `Templates/`, `Infosec Assurance/GRC/TPA/Active`) | `sharepoint-graph` (agents) | Replaces `Sites.Read.All`. The spec's tenant-wide `/search/query` operation needs `Sites.Read.All`; the least-privilege path is drive-scoped search (`/drives/{driveId}/root/search(q=)`) — recorded as a shared delta. Keeping `/search/query` = a ledger addition the owner must justify |
| Foundry project MI | `SecurityIncident.Read.All`, `SecurityAlert.Read.All`, `ThreatHunting.Read.All`, `SecurityEvents.Read.All` | tenant | `defender-graph` | Matches the five GET operations in the spec; no `ReadWrite` |
| Foundry project MI | `User.Read.All`, `Group.Read.All`, `Application.Read.All`, `RoleManagement.Read.Directory`, `AccessReview.Read.All` | tenant | `entra-iam-graph` | Matches `/users`, `/groups`, `/directoryRoles`, `/servicePrincipals`, `/identityGovernance/accessReviews` reads |
| Logic Apps MI | none on Graph | — | pipelines call the delivery Function for every SharePoint action | Keeps a single Graph writer |

Admin consent is recorded by the Entra IAM team with the ticket id in
`../../operations/access-governance/` evidence. Consent for a new permission is a
platform change (owner approval, `APPROVAL_ROUTING.md`).

## 4. SharePoint site roles (InfoSec Assurance site)

| Principal | Site role | `Reports/` | `Reports/DPO/` | `Templates/` | `Templates/Reviews/` | `Governance/` (access reviews, evidence) | `Infosec Assurance/GRC/TPA/Active` |
|---|---|---|---|---|---|---|---|
| `sg-infosec-foundry-users` | Members (Edit on the site) | **Read** (unique permissions) | Read | Read | Read | Read | Edit (pre-existing evidence-management duty, outside this platform's scope) |
| `{upn:francisco.gomes}` | Site Owner | Contribute (no delete — versioning keeps history) | Contribute | Edit | Edit | Edit | Edit |
| Delivery Function MI | `Sites.Selected` write (Graph, not a SharePoint group) | write | write | — | write (review pages) | — | — |
| Foundry project MI | `Sites.Selected` read | read | read | read | read | — | read |
| DPO team group `{sg:dpo-team}` | Visitors | — | Read | — | — | — | — |
| `sg-infosec-foundry-auditors` | Visitors | — | — | — | — | Read | — |
| Site-collection admin | M365 SharePoint admin team | — | — | — | — | — | — |

Rules: no anonymous links (org-scoped view links only, `../../sharepoint/README.md`);
library versioning on with ≥ 50 major versions; `Reports/` and
`Templates/` break permission inheritance; the site is excluded from
tenant-wide "Everyone except external users" defaults; sensitivity label
`{label:confidential-internal}` applied at library level.

## 5. Foundry project connections — ownership register

All connections are **project-scoped** (`isSharedToAll: false`) except
`bing-grounding` and `app-insights`, which the Bicep shares. Auth material
lives in Key Vault or is a managed identity; the registry references
names only.

| Connection | Auth | Identity behind it | Scope granted (read-only) | Secret (Key Vault name) | Owner | Rotation | System owner consulted |
|---|---|---|---|---|---|---|---|
| `conn-jira-cloud` | Custom key (API token) | Service account `{svc:jira-infosec-ro}` | Browse projects, read issues (JQL) | `kv-jira-api-token` | `{upn:francisco.gomes}` | 90 days | Jira admin |
| `conn-jira-assets` | Custom key | same service account | Assets/CMDB read | `kv-jira-api-token` | owner | 90 days | Jira admin |
| `conn-confluence` | Custom key | `{svc:confluence-infosec-ro}` | Space read on assurance spaces | `kv-confluence-api-token` | owner | 90 days | Confluence admin |
| `conn-onetrust` | Custom key | `{svc:onetrust-infosec-viewer}` (Viewer role) | Assessments/vendors read | `kv-onetrust-api-token` | owner | 90 days | OneTrust admin |
| `conn-securityscorecard` | Custom key | SSC read-only API key | Ratings read | `kv-ssc-api-key` | owner | 90 days | SSC account owner |
| `conn-iaf-api` | Custom key or Entra client credentials (preferred) | `{app:iaf-infosec-ro}` | Findings read | `kv-iaf-client-secret` (only if no federated credential) | owner | 90 days | IAF platform team |
| `conn-defender-graph` | Managed identity (project MI) | project MI | Graph security read (§3) | none | owner | n/a | Security operations |
| `conn-sharepoint-graph` | Managed identity | project MI | `Sites.Selected` read (§3) | none | owner | n/a | M365 admin |
| `conn-entra-iam` | Managed identity | project MI | Graph directory read (§3) | none | owner | n/a | Entra IAM team |
| `enx-gateway-mcp` | Bearer token from Key Vault (Entra if the gateway supports it) | `{app:enx-gateway-infosec-ro}` | Gateway read-only toolset for this project | `kv-enx-gateway-token` | owner | 90 days | ENX gateway team |
| `bing-grounding` | API key wired by Bicep | Bing resource | Web grounding (sanitised queries only) | Bicep-managed, regenerated on redeploy | owner | With each redeploy / 180 days | — |
| `app-insights` | Connection string wired by Bicep | — | Tracing | Bicep-managed | owner | n/a | — |

Rotation evidence: Key Vault secret versions (immutable, timestamped) +
the rotation ticket. Any change to a connection's scope is a platform
change (owner approval + deputy review).

## 6. Copilot Studio, MCP, GitHub

| Surface | Users | Owner | Notes |
|---|---|---|---|
| **Copilot Studio** (`../../integrations/copilot/README.md` option 1) | Consume the published agent in M365 Copilot/Teams; the app is published to `sg-infosec-foundry-users` only | Environment Maker in a dedicated Power Platform environment `{env:infosec-foundry}`; Power Platform admin team holds Environment Admin | Connector auth: delegated (user token, OBO) so answers respect the user's own permissions; DLP policy blocks any connector other than the Foundry HTTP connector |
| **MCP server, local** (`../../mcp-server/README.md`) | Run `server.py` under their own `az login`; access = their `Azure AI User` role; tracing records the caller identity | — | No shared credentials; `PROJECT_ENDPOINT` is not a secret; revocation = group removal |
| **MCP server, hosted** (Container Apps) | Easy Auth, allowed group `sg-infosec-foundry-users`, MFA via CA | Container App MI `Azure AI User` | Deploy only if a shared endpoint is needed; adds an identity to review |
| **GitHub repo** | `Read` (docs) | `Maintain` + CODEOWNERS on `convertion/**`; branch protection: 1 review from CODEOWNERS, owner's own PRs reviewed by `{upn:deputy-approver}` (`Write`) | Org admin holds `Admin`; Actions deploy via OIDC federated credential to `sp-infosec-foundry-deploy`; `prod` environment requires owner approval; secret scanning + push protection on |

## 7. Verification commands

```bash
# Role assignments at RG scope, grouped by principal (evidence for A.5.18)
az role assignment list --resource-group {rg} --include-inherited -o table

# Group membership
az ad group member list --group sg-infosec-foundry-users --query "[].userPrincipalName" -o tsv

# PIM eligibilities on the RG (requires Entra ID P2)
az rest --method get --url "https://management.azure.com/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.Authorization/roleEligibilityScheduleInstances?api-version=2020-10-01"

# Sites.Selected grants on the InfoSec Assurance site (Graph)
az rest --method get --url "https://graph.microsoft.com/v1.0/sites/{siteId}/permissions"

# Key Vault secret ages
az keyvault secret list --vault-name {baseName}-kv --query "[].{n:name,updated:attributes.updated}" -o table
```

`../../operations/access-governance/scripts/access_snapshot.sh` runs all of these and stores the
output as quarterly evidence.
