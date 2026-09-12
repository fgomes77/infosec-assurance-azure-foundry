# Step 04 — Connections and integrations (every `conn-*`, consents, service accounts)

**Objective.** Provision every connection named in
`integrations/registry.json` so that `scripts/attach_integrations.py` can
attach the tools **read-only**: the Graph-backed OpenAPI specs on the
**project managed identity** (no secrets), the token/Basic specs as
**custom-keys** project connections backed by Key Vault, the ENX gateway
MCP as a project connection with an allow-list of read-only tools, and
Bing grounding as created by `infra/main.bicep`. Obtain the admin
consents and read-only service accounts with their custodians, and record
everything in `team/ACCESS_REGISTER.md`.

**Owner / effort.** `{upn:francisco.gomes}` with each custodian; 5 days
plus waiting. Countersign: each custodian on their row. **Depends on** 02, 03.

## 1. Platform facts

| Fact | Status / source |
|---|---|
| OpenAPI tool GA: OpenAPI 3.0/3.1; every operation needs an `operationId` of letters, `-`, `_`; auth = **anonymous**, **API key / bearer via a project connection** (Custom keys, e.g. header `Authorization: Bearer <token>`), or **project managed identity with an audience**; one security scheme per tool | [GA] https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/openapi (2026-08-21) |
| MCP tool GA: auth via project connection — types `none`, `custom-keys` (headers), `oauth2` (Foundry-managed connector or own app registration), `user-entra`, project managed identity; `require_approval` default `always`; `allowed_tools`; Toolbox (preview) can front several tools with one endpoint | [GA] https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/model-context-protocol (2026-08-26) |
| Azure Functions tool is **not** available in the new service (MCP-on-Functions or OpenAPI are the routes) — the kit already calls the delivery Function through OpenAPI (`osint-proxy`) | [GA] https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/migrate#agent-tool-availability (2026-08-05) |
| Grounding with Bing Search (GA) / Web Search tool (GA): data flows outside the Azure compliance boundary; the Data Protection Addendum does not apply; Bing Custom Search (preview) can domain-restrict | [GA] https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/bing-tools (2026-08-27) |
| SharePoint *tool* (preview) is delegated-only, needs M365 Copilot licences or the pay-as-you-go Retrieval API, one per agent, text-only — not used; the kit's Graph OpenAPI read surface stays | [preview] https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/sharepoint (2026-08-21) |
| Tools under network isolation: MCP/OpenAPI/A2A traverse the agents subnet; AI Search / file search via private endpoint; Code Interpreter and function calling via Microsoft-managed paths | [GA] https://learn.microsoft.com/en-us/azure/foundry/how-to/configure-private-link (2026-08-26) |
| Fixed limit: 128 tools per agent | [GA] https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/limits-quotas-regions (2026-09-07) |

Consequence for the kit (shared delta **S-05**, `integrations/registry.json`):
each `connections.*` entry gains `"auth": "managed_identity" | "custom_keys" | "none"` and
Graph-backed entries set `"foundry_connection": null`; `attach_integrations.py`
maps `managed_identity` to the OpenAPI tool's managed-identity auth with
audience `https://graph.microsoft.com`, and `custom_keys` to the named
project connection. The registry `_comment` gains: `Auth model: Graph
specs = project managed identity (Entra app roles, no secret); token/Basic
specs = custom-keys connections whose header value is a Key Vault secret;
MCP = custom-keys connection; delegated (OBO) specs are not attached to
agents in v1.`

## 2. Connection register (one row per `registry.json` connection)

| Connection (`registry.json`) | Foundry connection | Auth model | Identity / secret (Key Vault name) | Custodian | Read-only scope to confirm in writing |
|---|---|---|---|---|---|
| `jira-cloud` | `conn-jira-cloud` (custom keys) | header `Authorization: Basic {base64(email:token)}` **or** OAuth 2.0 (3LO) bearer for a service account — prefer bearer | `svc-infosec-foundry-ro-jira`; `kv-jira-api-token` (the full header value) | `{group:jira-admins}` | project role *browse* only; no create/transition; API token rotated 180 d |
| `jira-assets-cmdb` | `conn-jira-assets` (custom keys) | same service account; header as above | `svc-infosec-foundry-ro-jira`; `kv-jira-assets-token` | `{group:jira-admins}` | Assets *viewer* on the workspace `{workspaceId}` |
| `onetrust` | `conn-onetrust` (custom keys) | client-credentials token obtained **outside** the agent (Logic App / Key Vault rotation job) and stored as `Authorization: Bearer …` — the OpenAPI tool holds a static header, not an OAuth flow | `svc-infosec-foundry-ro-onetrust`; `kv-onetrust-api-token` | `{group:onetrust-admins}` | credential scoped to Assessments + Inventory **read** |
| `securityscorecard` | `conn-securityscorecard` (custom keys) | header `Authorization: Token {key}` | `svc-infosec-foundry-ro-ssc`; `kv-ssc-api-key` | SSC admin | read-only key; 365 d |
| `defender-graph` | — (managed identity) | project MI, audience `https://graph.microsoft.com` | `{mi:infosecfoundry-proj}` | `{group:m365-admins}` / SecOps | app roles `SecurityIncident.Read.All`, `SecurityAlert.Read.All`, `ThreatHunting.Read.All`, `SecurityEvents.Read.All` |
| `sharepoint-graph` | — (managed identity) | project MI | `{mi:infosecfoundry-proj}` | `{group:spo-admins}` | `Sites.Selected` + **read** grant on the one site (step 05 §3) |
| `entra-iam-graph` | — (managed identity) | project MI | `{mi:infosecfoundry-proj}` | `{group:iam-admins}` | `User.Read.All`, `Group.Read.All`, `RoleManagement.Read.Directory`, `Application.Read.All`, `AccessReview.Read.All` |
| `exchange-graph` | — (managed identity) | project MI | `{mi:infosecfoundry-proj}` | Exchange admins | `Mail.Read` **plus** an Exchange *application access policy* restricting it to the one shared mailbox `{mailbox:assurance-shared}` |
| `iaf-api` | `conn-iaf-api` (custom keys) | `Authorization: Bearer …` (token from the internal IdP, rotated by a Logic App) or `X-API-Key` | `{app:infosec-foundry-iaf-ro}`; `kv-iaf-client-secret` / `kv-iaf-api-key` | `{upn:iaf-owner}` | scope `iaf.read` only — never `iaf.write` (writes happen only in `workflows/jira-finding-sync.json` after approval) |
| `confluence-cloud` | `conn-confluence` (custom keys) | `Authorization: Basic …` or 3LO bearer with `read:confluence-content.all`, `read:confluence-space.summary` | `svc-infosec-foundry-ro-confluence`; `kv-confluence-api-token` | Confluence admin | space *view* only |
| `enx-gateway-mcp` | `conn-enx-gateway` (custom keys **or** `user-entra` if the gateway accepts Entra tokens) | MCP tool: `server_url` `https://{enx-gateway-host}/mcp`, `allowed_tools` = the read tools, `require_approval: never` (justified by `readOnlyHint=true` on every allow-listed tool — `integrations/mcp/enx-gateway.json`) | `svc-infosec-foundry-ro-enxgw`; `kv-enx-gateway-token` | `{group:enx-gateway}` | gateway policy exposes the read toolset only to this project; token 90 d |
| `web-search` | `bing-grounding` (created by `main.bicep`, category `GroundingWithBingSearch`, ApiKey) | resource key wired by Bicep | `{baseName}-bing` | owner | outside the EU boundary — risk acceptance recorded in step 08 §5; sanitised queries only |
| `osint-proxy` | `conn-osint-proxy` (custom keys) | header `x-functions-key` | Function key `kv-delivery-function-key` | owner | GET `/api/fetch_public_page` only; allow-list of public hosts in the Function |
| `azure-devops` | `conn-azure-devops` (custom keys) | `Authorization: Bearer {PAT or Entra token}` for a Reader SP | `svc-infosec-foundry-ro-ado`; `kv-ado-token` | ADO admin | *Reader* on the project(s); no PR write |
| `teams-graph`, `m365-personal-graph` | **not attached in v1** | delegated (OBO) only — the OpenAPI tool has no delegated auth; these example-agent surfaces are served by Logic Apps (`workflows/morning-brief.json`) or the Copilot wrapper's OBO exchange (step 09) | — | — | `Chat.Read`, `ChannelMessage.Read.All`, `Team.ReadBasic.All`, `Calendars.Read`, `Mail.Read` (delegated) — consent only if step 09 enables the wrapper |
| `app-insights` | created by `main.bicep` (category `AppInsights`) | connection string | — | owner | tracing sink (step 08) |

Every custom-keys connection stores the **whole header value** as one Key
Vault secret so rotation is a secret-version change plus a connection
re-point (`operations/CHANGE_MANAGEMENT.md` §1 "Integration credential").

## 3. Admin consents — app roles for the project managed identity

Application permissions on a managed identity are granted as app-role
assignments on the Graph service principal (there is no consent button
for MIs). Run as a Privileged Role / Global Administrator
(`{group:m365-admins}`), once per environment and again for each
**published** agent identity (step 09):

```bash
MI_OBJECT_ID={objectId:infosecfoundry-proj-mi}            # az cognitiveservices account show … projects → identity.principalId
GRAPH_SP=$(az ad sp list --filter "appId eq '00000003-0000-0000-c000-000000000000'" --query "[0].id" -o tsv)
for ROLE in Sites.Selected SecurityIncident.Read.All SecurityAlert.Read.All ThreatHunting.Read.All SecurityEvents.Read.All \
            User.Read.All Group.Read.All RoleManagement.Read.Directory Application.Read.All AccessReview.Read.All Mail.Read; do
  ROLE_ID=$(az ad sp show --id "$GRAPH_SP" --query "appRoles[?value=='$ROLE' && contains(allowedMemberTypes,'Application')].id | [0]" -o tsv)
  az rest --method POST --url "https://graph.microsoft.com/v1.0/servicePrincipals/$MI_OBJECT_ID/appRoleAssignments" \
    --body "{\"principalId\":\"$MI_OBJECT_ID\",\"resourceId\":\"$GRAPH_SP\",\"appRoleId\":\"$ROLE_ID\"}"
done
# Exchange: restrict Mail.Read to the one shared mailbox (Exchange Online PowerShell)
# New-ApplicationAccessPolicy -AppId {appId:infosecfoundry-proj-mi} -PolicyScopeGroupId {mailbox:assurance-shared} -AccessRight RestrictAccess
```

No `Sites.Read.All`, `Sites.ReadWrite.All`, `Mail.ReadWrite` or any
`*.ReadWrite.*` role is ever granted to an agent identity. Delegated
scopes (`teams-graph`, `m365-personal-graph`) are consented only for the
Copilot wrapper app registration in step 09, never for the project MI.

## 4. Click-path

**Foundry portal.** *Home* → project → **Connections** (Management
center) → *+ New connection* → **Custom keys** → name `conn-jira-cloud`,
target `https://{your-domain}.atlassian.net`, key `Authorization`, value
= the Key Vault secret (paste at creation; the portal stores it in the
connection, not in Key Vault — prefer the Bicep module below so the value
comes from Key Vault) → *Is shared to all projects* = off. Repeat per row.
For MCP: *Build* → *Agents* → (after step 06) agent → *Tools* → *Add* →
**MCP** → server URL, connection `conn-enx-gateway`, allowed tools,
approval *never*. **Azure portal.** Key Vault `{baseName}-kv` → *Secrets*
→ generate/import each `kv-*` secret (owner under PIM `Key Vault Secrets
Officer`; values typed from the custodian's secure hand-over, never from a
file in the repo). **Entra admin center.** Enterprise applications →
`{mi:infosecfoundry-proj}` → *Permissions* → verify the app roles of §3.

## 5. CLI / Bicep / kit scripts

Reusable module for a custom-keys connection whose header value is read
from Key Vault (validated with Bicep 0.47.16):

```bicep
// series-04-connection-customkeys.bicep — one custom-keys Foundry connection, value from Key Vault
param foundryAccountName string
param connectionName string
param target string
param headerName string = 'Authorization'
@secure()
param headerValue string

resource foundry 'Microsoft.CognitiveServices/accounts@2025-04-01-preview' existing = { name: foundryAccountName }

resource connection 'Microsoft.CognitiveServices/accounts/connections@2025-04-01-preview' = {
  parent: foundry
  name: connectionName
  properties: {
    category: 'CustomKeys'
    authType: 'CustomKeys'
    target: target
    isSharedToAll: false
    credentials: { keys: toObject([headerName], k => k, k => headerValue) }
    metadata: { ApiType: 'Azure' }
  }
}
output connectionId string = connection.id
```

Caller (in a `connections.bicep` at RG scope, one module per row):

```bicep
resource kv 'Microsoft.KeyVault/vaults@2023-07-01' existing = { name: '{baseName}-kv' }
module jira 'series-04-connection-customkeys.bicep' = {
  name: 'conn-jira-cloud'
  params: { foundryAccountName: '{baseName}-aif', connectionName: 'conn-jira-cloud', target: 'https://{your-domain}.atlassian.net', headerValue: kv.getSecret('kv-jira-api-token') }
}
```

Gap **G-04** (shared delta S-15): `integrations/mcp/enx-gateway.json` documents `attach_integrations.py --dry-run --list-mcp-tools` and a readOnlyHint check at attach time, but `scripts/attach_integrations.py` contains neither (no `tools/list` call, no `readOnlyHint` test). Until the integration pass adds them, V3 below is performed manually against the gateway's `tools/list` and the output is filed as evidence.

Kit scripts, after the connections exist:

```bash
python3 scripts/attach_integrations.py --dry-run                 # every OpenAPI tool shows [read-only]; unknown connections fail
python3 scripts/attach_integrations.py --dry-run --list-mcp-tools   # gap G-04: flag documented in integrations/mcp/enx-gateway.json, not yet implemented (see below)
python3 scripts/attach_integrations.py --only cyber-forum          # first live attach (dev/test), then the rest
```

## 6. Values captured into `setup/.env`

| Variable | Value |
|---|---|
| `KEY_VAULT_NAME` | `{baseName}-kv` |
| `ENX_GATEWAY_MCP_URL` | `https://{enx-gateway-host}/mcp` (not a secret) |
| `FOUNDRY_PROJECT_MI_OBJECT_ID` | `{objectId:infosecfoundry-proj-mi}` (new, S-04 — used by step 05 grants and step 09 re-grants) |

## 7. Verification

| # | Check | Pass when |
|---|---|---|
| V1 | Foundry portal → Connections | every row of §2 present (except the two deferred), no auth error |
| V2 | `attach_integrations.py --dry-run` | `[read-only]` on every OpenAPI tool; `write_connections` absent for every agent |
| V3 | ENX gateway `tools/list` (curl with the connection's token, or `attach_integrations.py --dry-run --list-mcp-tools` once G-04 is closed) | every allow-listed tool carries `readOnlyHint=true`; any that does not is removed from `allowed_tools` before attach |
| V4 | Per connection, one read call through an agent in `test` (`smoke_test.py --agent cyber-forum --prompt "List the five most recent Defender incidents (titles only)"`) | tool call visible in tracing; data returned; **no** non-GET call possible (attempt `create an issue` → agent reports it cannot) |
| V5 | Graph app roles: `az rest GET …/servicePrincipals/{MI}/appRoleAssignments` | exactly the roles of §3; none `ReadWrite` |
| V6 | Custodian confirmations filed (`Governance/Implementation/{env}/04/custodian-{system}.md`) | one per row |
| V7 | Egress: tracing shows Bing queries contain public terms only (sample of 20) | `operations/kql/egress-detection.kql` returns 0 rows |
| V8 | `team/ACCESS_REGISTER.md` "Non-human identities" rows updated with rotation dates | all rows dated |

**Rollback.** Delete the connection (`az rest DELETE` on the connection
resource or portal), disable the Key Vault secret (never purge — purge
protection), custodian revokes the account; `attach_integrations.py`
re-attaches without it. **ISMS evidence.** V1–V8 outputs, custodian
confirmations, register rows — ISO 27001:2022 A.5.19–A.5.21 (supplier
relationships / ICT supply chain), A.5.17 (authentication information),
A.8.3; DORA Art. 9(4)(c), Art. 28; ISO 42001 A.10.3 (suppliers); GDPR
Art. 28 (processors, for Bing — DPO informed).

## Sources
- [GA] OpenAPI tool — https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/openapi (2026-08-21)
- [GA] MCP tool — https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/model-context-protocol (2026-08-26)
- [GA] Tool availability classic vs new — https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/migrate#agent-tool-availability (2026-08-05)
- [GA] Azure Functions tool page — https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/azure-functions (2026-08-21)
- [GA] Bing tools / boundary — https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/bing-tools (2026-08-27)
- [preview] SharePoint tool — https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/sharepoint (2026-08-21)
- [GA] Tools under private link — https://learn.microsoft.com/en-us/azure/foundry/how-to/configure-private-link (2026-08-26)
- [GA] Limits — https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/limits-quotas-regions (2026-09-07)
