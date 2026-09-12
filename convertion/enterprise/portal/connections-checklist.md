# Connections Checklist (`conn-*`) — Auth, Key Vault Secret, Owner, Rotation

Checked at bootstrap, at every rotation and in the quarterly access review.
Model of record: `../../team/TEAM_MODEL.md` §10 and
`../../team/ACCESS_REGISTER.md`; this page adds the portal-side fields to
verify and the agent-identity connections the blueprint introduces (ID-2).
Portal path: Management center / Build > Services > Connections (new
portal) — connections are project-scoped unless `isSharedToAll` is true.

Platform facts: OpenAPI tools authenticate anonymous, API key/bearer via a
project connection (custom keys), or project managed identity with an
audience — one security scheme per tool
([OpenAPI tool](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/openapi), GA, 2026-08-21).
MCP tools take a project connection with auth `none`, `custom-keys`,
`oauth2`, `user-entra`, project managed identity or **agent identity**
([MCP tool](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/model-context-protocol), GA, 2026-08-26).
Bing grounding data leaves the Azure compliance boundary and the DPA does
not apply ([Bing tools](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/bing-tools), GA, 2026-08-27).

## Per-connection checks (all rows)

| # | Check | Expected |
|---|---|---|
| 1 | Name follows `conn-<system>` / `conn-<system>-agentid`; `isSharedToAll: false` (except `bing-grounding`, `app-insights`) | yes |
| 2 | Auth type is the one in the table below; no API key where a managed/agent identity is possible | yes |
| 3 | Secret material exists only as a Key Vault secret **name** in the repo; value set by the custodian in a PIM window | `kv-*` |
| 4 | Target-side principal is read-only (browse/viewer/read scope) — custodian confirmation attached | yes |
| 5 | Rotation date ≤ period; past-due = connection disabled until rotated | `ACCESS_REGISTER.md` |
| 6 | Attached only to the agents listed for it in `../../integrations/registry.json` | `attach_integrations.py --dry-run` |
| 7 | Change of target/scope has a Tier C PR + custodian sign-off (two people) | change record |

## Register

| Connection | Category (portal) | Auth | Identity | KV secret (name) | Foundry owner | Custodian | Rotation |
|---|---|---|---|---|---|---|---|
| `conn-sharepoint-graph` | Custom / OpenAPI | project managed identity, audience `https://graph.microsoft.com` | `{mi:infosecfoundry-proj}` (`Sites.Selected` read) | none | owner | `{group:iam-admins}` | n/a |
| `conn-defender-graph` | Custom / OpenAPI | project MI | same (Security*.Read.All, ThreatHunting.Read.All) | none | owner | `{group:iam-admins}` | n/a |
| `conn-entra-iam` | Custom / OpenAPI | project MI | same (directory read scopes) | none | owner | `{group:iam-admins}` | n/a |
| `conn-exchange-graph`, `conn-teams-graph`, `conn-m365-personal` | Custom / OpenAPI | delegated (OBO) where the spec says so; app-only never for personal scopes | user token / `{mi:infosecfoundry-proj}` | none | owner | `{group:iam-admins}` | n/a |
| `conn-jira-cloud`, `conn-jira-assets` | Custom keys | bearer/API token header | `{svc:infosec-foundry-ro-jira}` | `kv-jira-ro-token` | owner | `{group:jira-admins}` | 180 d |
| `conn-confluence` | Custom keys | API token | `{svc:infosec-foundry-ro-confluence}` | `kv-confluence-ro-token` | owner | Confluence admin | 180 d |
| `conn-onetrust` | Custom keys | API token | `{svc:infosec-foundry-ro-onetrust}` | `kv-onetrust-ro-token` | owner | `{group:onetrust-admins}` | 180 d |
| `conn-securityscorecard` | Custom keys | API token | `{svc:infosec-foundry-ro-ssc}` | `kv-ssc-ro-token` | owner | SSC admin | 180 d |
| `conn-iaf-api` | Custom keys or project MI (federated, preferred) | bearer / MI audience `{iaf-audience}` | `{app:infosec-foundry-iaf-ro}` | `kv-iaf-ro-token` (token path only) | owner | `{upn:iaf-owner}` | 180 d |
| `conn-osint-proxy` | Custom keys | function key header to the delivery Function `/api/fetch_public_page` | — | `kv-delivery-function-key` | owner | owner | 180 d |
| `conn-azure-devops` | Custom keys | PAT (read) or MI where supported | `{svc:infosec-foundry-ro-ado}` | `kv-ado-ro-token` | owner | ADO admins | 180 d |
| `conn-enx-gateway-agentid` (replaces header-token injection) | RemoteTool | **AgenticIdentityToken** (agent identity), audience `{enx-gateway-audience}`; fallback custom-keys `kv-enx-gateway-token` (90 d) | project agent identity / per-published-agent identity | none (identity) or `kv-enx-gateway-token` | owner | `{group:enx-gateway}` | n/a / 90 d |
| `conn-a2a-<specialist>` | RemoteA2A | AgenticIdentityToken | orchestrator agent identity → published specialist | none | owner | owner | n/a |
| `conn-kb-assurance` (optional, Foundry IQ) | RemoteTool | ProjectManagedIdentity → `{search}/knowledgebases/kb-assurance/mcp` | `{mi:infosecfoundry-proj}` (Search Index Data Reader) | none | owner | owner | n/a ([Foundry IQ connect](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/foundry-iq-connect), preview, 2026-09-11) |
| `sharepoint-grounding` (optional, SP-1) | SharePoint (preview) | delegated user identity only | each user's token (Copilot licence / PAYG) | none | owner | `{group:spo-admins}` | n/a |
| `bing-grounding` | GroundingWithBingSearch | ApiKey (resource key, Bicep-wired) | — | Bicep `listKeys` | owner | owner | 180 d (PIM `Contributor` on `{baseName}-bing`) |
| `app-insights` | AppInsights | connection string (Bicep-wired) | — | — | owner | owner | workspace rebuild |
| `conn-cosmos`, `conn-storage`, `conn-search` (standard agent setup, STO-1) | CosmosDB / AzureStorageAccount / CognitiveSearch | project managed identity | `{mi:infosecfoundry-proj}` (Cosmos DB Built-in Data Contributor, Storage Blob Data Contributor, Search Index Data Contributor) | none | owner | owner | n/a ([Standard setup](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/standard-agent-setup), GA, 2026-07-09) |

## Bootstrap and rotation commands (names only)

```bash
# 1. secret value from the custodian's environment, never from a file in the repo
az keyvault secret set --vault-name {baseName}-kv -n kv-jira-ro-token --value @-
# 2. create/refresh the connection (custom keys) — the header value is a Key Vault reference
az rest --method PUT \
  --url "https://management.azure.com/subscriptions/{subscriptionId}/resourceGroups/rg-infosec-foundry/providers/Microsoft.CognitiveServices/accounts/{baseName}-aif/projects/{baseName}-proj/connections/conn-jira-cloud?api-version={stable-api-version}" \
  --body '{"properties":{"category":"CustomKeys","target":"https://{jira-host}","authType":"CustomKeys","isSharedToAll":false,"credentials":{"keys":{"Authorization":"Bearer {value-read-from-key-vault-in-the-pipeline}"}}}}'
# 3. re-attach so agents pick up the refreshed connection
python3 ../../scripts/attach_integrations.py --only cyber-forum
# 4. register: ACCESS_REGISTER.md row (rotation date) + change log
```

Evidence per rotation: Key Vault `SecretSet` audit event (caller = owner in
PIM window), custodian confirmation, `ACCESS_REGISTER.md` diff.
