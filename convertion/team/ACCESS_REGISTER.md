# Access Register — InfoSec Assurance Foundry Platform

Single record of who and what holds access (ISO/IEC 27001:2022 A.5.16,
A.5.18; DORA Art. 9(4)(c)). Maintained by the owner; reviewed quarterly
(`team/README.md` §11). Placeholders only — no real object ids, hostnames
or secrets are ever written here; secret *names* are fine.

## People

| Person | UPN | Groups | Since | Last review | Notes |
|---|---|---|---|---|---|
| Francisco Gustavo Gomes | `{upn:francisco.gomes}` | users, report-approvers, senior-approvers, owner, admin-pim (eligible) | {date} | {date} | Accountable owner |
| José Mogollon | `{upn:jose.mogollon}` | users, report-approvers | {date} | {date} | |
| Pedro Santos | `{upn:pedro.santos}` | users, report-approvers | {date} | {date} | |
| José Meireles | `{upn:jose.meireles}` | users, report-approvers | {date} | {date} | |
| Tânia Morais | `{upn:tania.morais}` | users, report-approvers | {date} | {date} | |
| Deputy owner (nominated) | `{upn:deputy}` | + senior-approvers, breakglass (eligible) | {date} | {date} | Nomination recorded by the owner; CODEOWNERS reviewer for owner-authored PRs |
| Line manager | `{upn:line-manager}` | — (group owner of owner/senior/pim/breakglass; PIM approver) | {date} | {date} | Reviews privileged groups |

## Groups

| Group | Object id | Owner | Purpose | Access package | Review cadence |
|---|---|---|---|---|---|
| `sg-infosec-foundry-users` | `{objectId:sg-infosec-foundry-users}` | `{upn:francisco.gomes}` | data-plane use, SharePoint member, Copilot, MCP | `AP-InfoSec-Foundry-User` (12 months) | quarterly |
| `sg-infosec-foundry-report-approvers` | `{objectId:…}` | owner | Tier A approvals | — | quarterly |
| `sg-infosec-foundry-senior-approvers` | `{objectId:…}` | line manager | Tier B approvals | — | quarterly |
| `sg-infosec-foundry-owner` | `{objectId:…}` | line manager | standing owner roles | — | quarterly (line manager) |
| `sg-infosec-foundry-admin-pim` | `{objectId:…}` | line manager | PIM-eligible privileged roles | PIM policy 8 h | quarterly (line manager) |
| `sg-infosec-foundry-breakglass` | `{objectId:…}` | line manager | deputy emergency access | PIM policy 8 h, approver required | every activation |
| `sg-infosec-foundry-readers` | `{objectId:…}` | owner | audit/DPO read | — | quarterly |

## Non-human identities

| Identity | Type | Where used | Roles / permissions | Custodian | Rotation | Next due |
|---|---|---|---|---|---|---|
| `{mi:infosecfoundry-proj}` | Foundry project MI | Graph OpenAPI tools (SharePoint, Defender, Entra IAM) | Sites.Selected read; SecurityIncident/Alert/ThreatHunting read; User/Group/RoleManagement read | IAM admins | n/a | — |
| `{mi:infosecfoundry-la}` | Logic Apps MI | pipelines | Azure AI User (project); Sites.Selected read; KV Secrets User | owner | n/a | — |
| `{mi:infosec-delivery-fn}` | Function MI | render/store | Sites.Selected write; Blob Data Contributor; KV Secrets User | owner | n/a | — |
| `{app:infosec-foundry-deployer}` | SP, federated (GitHub OIDC) | `deploy.sh` from the `production` environment | Contributor (RG); Azure AI Developer (account) | owner | n/a (no secret) | — |
| `{app:infosec-foundry-agents-read}` | app registration (only if the project MI cannot be used) | agents' SharePoint read | Sites.Selected read | IAM admins | federated / 180 d | {date} |
| `svc-infosec-foundry-ro-jira` | service account token | `conn-jira-cloud`, `conn-jira-assets` | browse / Assets viewer | Jira admins | 180 d | {date} |
| `svc-infosec-foundry-ro-confluence` | service account token | `conn-confluence` | space read | Confluence admin | 180 d | {date} |
| `svc-infosec-foundry-ro-onetrust` | service account token | `conn-onetrust` | viewer | OneTrust admins | 180 d | {date} |
| `svc-infosec-foundry-ro-ssc` | API token | `conn-securityscorecard` | read-only | SSC admin | 365 d | {date} |
| `{app:infosec-foundry-iaf-ro}` | app / token | `conn-iaf-api` | IAF read scope | IAF owner | 180 d | {date} |
| `svc-infosec-foundry-ro-enxgw` | bearer token | `enx-gateway-mcp` | gateway read toolset | ENX gateway team | 90 d | {date} |
| Bing Grounding key | resource key | `bing-grounding` connection | web search | owner | 180 d | {date} |

## Approved AI / MCP clients (team/README.md §12)

| Client | Model provider / data path | Agreement reference | Approved by | Until |
|---|---|---|---|---|
| Foundry portal playground | Azure OpenAI in `{eu-region}` | tenant | owner | standing |
| Microsoft 365 Copilot (Copilot Studio agent) | Microsoft 365 boundary | tenant | owner + M365 admin | standing |
| ENX gateway (remote MCP) | internal | internal | owner | standing |
| `{client}` | `{provider}` | `{dpa-reference}` | `{approver}` | `{date}` |

## Change log

| Date | Change | By | Evidence |
|---|---|---|---|
| {date} | Register created | `{upn:francisco.gomes}` | — |
