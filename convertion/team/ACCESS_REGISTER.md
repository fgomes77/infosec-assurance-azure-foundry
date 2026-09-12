# Access Register — InfoSec Assurance Foundry Platform

Single record of who and what holds access (ISO/IEC 27001:2022 A.5.16,
A.5.18; DORA Art. 9(4)(c)). Maintained by the owner; reviewed quarterly
(`team/TEAM_MODEL.md` §15; runbook
`operations/access-governance/QUARTERLY_ACCESS_REVIEW.md`). Placeholders only — no real object ids, hostnames
or secrets are ever written here; secret *names* are fine.

## People

| Person | UPN | Groups | Since | Last review | Notes |
|---|---|---|---|---|---|
| Francisco Gustavo Gomes | `{upn:francisco.gomes}` | users, report-approvers, senior-approvers, owner, admin-pim (eligible) | {date} | {date} | Accountable owner (`TEAM_MODEL.md` §1); assurance user |
| José Mogollon | `{upn:jose.mogollon}` | users, report-approvers | {date} | {date} | |
| Pedro Santos | `{upn:pedro.santos}` | users, report-approvers | {date} | {date} | |
| José Meireles | `{upn:jose.meireles}` | users, report-approvers | {date} | {date} | |
| Tânia Morais | `{upn:tania.morais}` | users, report-approvers | {date} | {date} | |
| Deputy approver (nominated: one of the four above) | `{upn:deputy-approver}` | + senior-approvers, breakglass (eligible) | {date} | {date} | Nominated by the owner, confirmed by `{upn:line-manager}`; CODEOWNERS reviewer for owner-authored PRs; approves the owner's own Tier C items (`TEAM_MODEL.md` §12.2) |
| Line manager | `{upn:line-manager}` | — (group owner of owner/senior/pim/breakglass; PIM approver) | {date} | {date} | Reviews privileged groups |

## Groups

| Group | Object id | Owner | Purpose | Access package | Review cadence |
|---|---|---|---|---|---|
| `sg-infosec-foundry-users` | `{objectId:sg-infosec-foundry-users}` | `{upn:francisco.gomes}` | data-plane use, SharePoint member, Copilot, MCP | `AP-InfoSec-Foundry-User` (12 months) | quarterly |
| `sg-infosec-foundry-report-approvers` | `{objectId:sg-infosec-foundry-report-approvers}` | owner | Tier A approvals (after onboarding attestation) | — | quarterly |
| `sg-infosec-foundry-senior-approvers` | `{objectId:sg-infosec-foundry-senior-approvers}` | line manager | Tier B approvals; deputy for the owner's Tier C items | — | quarterly (line manager) |
| `sg-infosec-foundry-owner` | `{objectId:sg-infosec-foundry-owner}` | line manager | standing low-privilege owner roles (`TEAM_MODEL.md` §6) | — | quarterly (line manager) |
| `sg-infosec-foundry-admin-pim` | `{objectId:sg-infosec-foundry-admin-pim}` | line manager | PIM-eligible privileged roles (ledger L1–L5, L7, L8) | PIM policy 8 h | quarterly (line manager); activations monthly |
| `sg-infosec-foundry-breakglass` | `{objectId:sg-infosec-foundry-breakglass}` | line manager | deputy emergency access (ledger L10) | PIM policy 8 h, approver required | every activation (owner ≤ 5 business days); quarterly (line manager) |
| `sg-infosec-foundry-readers` | `{objectId:sg-infosec-foundry-readers}` | owner | audit / DPO read (ledger L15) | — | end of engagement; quarterly |

## Non-human identities

| Identity | Type | Where used | Roles / permissions | Custodian | Rotation | Next due |
|---|---|---|---|---|---|---|
| `{mi:infosecfoundry-proj}` | Foundry project MI | Graph OpenAPI tools (SharePoint, Defender, Entra IAM) | Sites.Selected read; SecurityIncident/Alert/ThreatHunting read; User/Group/RoleManagement read | IAM admins | n/a | — |
| `{mi:infosecfoundry-la}` | Logic Apps MI | pipelines | Azure AI User (project); Sites.Selected read; KV Secrets User (named secrets); runtime storage data roles (ledger L12) | owner | n/a | — |
| Logic Apps MI Sites.Selected **write** (L12x) | time-boxed exception | `onetrust-assessment-intake`, `scheduled-deepsearch` direct uploads | Sites.Selected write | owner | expires on delta D-W3 (uploads routed through the delivery Function) | {date} |
| `{mi:infosec-delivery-fn}` | Function MI | render/store | Sites.Selected write; Blob Data Contributor (`deliverables`); KV Secrets User only if `deliveryFunctionReadsSecrets` (ledger L13) | owner | n/a | — |
| `{app:infosec-foundry-deployer}` | SP, federated (GitHub OIDC) | `deploy.sh` from the `production` environment | Contributor (RG); RBAC Administrator (ABAC-constrained to the `rbac.bicep` role set); Azure AI Developer (account); KV Secrets Officer (seeding) (ledger L11) | owner | n/a (no secret) | — |
| `{app:infosec-foundry-agents-read}` | app registration — **not granted by default**; only if the project MI cannot hold `Sites.Selected` (would be a new ledger row: exactly three app grants exist today) | agents' SharePoint read | Sites.Selected read | IAM admins | federated / 180 d | {date} |
| `svc-infosec-foundry-ro-jira` | service account token | `conn-jira-cloud`, `conn-jira-assets` | browse / Assets viewer | Jira admins | 180 d | {date} |
| `svc-infosec-foundry-ro-confluence` | service account token | `conn-confluence` | space read | Confluence admin | 180 d | {date} |
| `svc-infosec-foundry-ro-onetrust` | service account token | `conn-onetrust` | viewer | OneTrust admins | 180 d | {date} |
| `svc-infosec-foundry-ro-ssc` | API token | `conn-securityscorecard` | portfolio read | SSC admin | 180 d | {date} |
| `{app:infosec-foundry-iaf-ro}` | app / token | `conn-iaf-api` | IAF read scope | IAF owner | 180 d | {date} |
| `svc-infosec-foundry-ro-enxgw` | bearer token | `enx-gateway-mcp` | gateway read toolset | ENX gateway team | 90 d | {date} |
| Bing Grounding key | resource key | `bing-grounding` connection | web search | owner | 180 d | {date} |

## Approved AI / MCP clients (`team/TEAM_MODEL.md` §11)

| Client | Model provider / data path | Agreement reference | Approved by | Until |
|---|---|---|---|---|
| Foundry portal playground | Azure OpenAI in `{eu-region}` | tenant | owner | standing |
| Microsoft 365 Copilot (Copilot Studio agent) | Microsoft 365 boundary | tenant | owner + M365 admin | standing |
| ENX gateway (remote MCP) | internal | internal | owner | standing |
| `{client}` | `{provider}` | `{dpa-reference}` | `{approver}` | `{date}` |

## PIM fallback exception (`TEAM_MODEL.md` §6)

| `enablePim=false` in force? | Review date | Approved by |
|---|---|---|
| {yes/no} | {date} | `{upn:line-manager}` |

## Change log

| Date | Change | By | Evidence |
|---|---|---|---|
| {date} | Register created | `{upn:francisco.gomes}` | — |
