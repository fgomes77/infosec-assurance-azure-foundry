# Integration Layer — Euronext Technology Stack

Connects the converted Foundry agents to the surrounding Euronext toolchain.
Every integration is declared in `registry.json` (which agent gets which
tool, and which model tier) and attached by
`../scripts/attach_integrations.py` after the agents exist.

## Integrations

| Connection | Type | Used by (default) | Purpose in the TPRM workflow |
|---|---|---|---|
| `jira-cloud` | OpenAPI (`openapi/jira-cloud.yaml`) | cyber-forum, ciso-reporting | Raise/track remediation and finding tickets; JQL queries |
| `jira-assets-cmdb` | OpenAPI (`openapi/jira-assets-cmdb.yaml`) | dora, tpsrca-assessment-engine | CMDB (JSM Assets) lookups: CIs, suppliers, service mapping for the DORA Register of Information and concentration risk |
| `onetrust` | OpenAPI (`openapi/onetrust.yaml`) | dpia, onetrust-form-b, ciso-reporting, ciso-executive-summary | Pull assessments/vendor inventory instead of manual PDF upload |
| `securityscorecard` | OpenAPI (`openapi/securityscorecard.yaml`) | deepsearch agents, tpsrca | External security ratings as OSINT evidence |
| `defender-graph` | OpenAPI (`openapi/defender-graph.yaml`) | cyber-forum | Defender XDR incidents, alerts, KQL hunting, Secure Score |
| `sharepoint-graph` | OpenAPI (`openapi/sharepoint-graph.yaml`) | document + reporting agents, tpa-evidence-analyzer | Evidence repository READS only: sites/drives, folder walk by id or path (TPA/Active tree), drive-scoped search, small-file download. Deliverables are written only by `functions/delivery` |
| `iaf-api` | OpenAPI (`openapi/iaf-api.yaml`) — **template** | dpia, dora, deepsearch, tpsrca | Internal InfoSec Assurance Framework API; align the template to the real internal spec before use |
| `enx-gateway-mcp` | MCP (`mcp/enx-gateway.json`) — **template** | control-center, deepsearch, cyber-forum | Internal ENX gateway MCP server; fill server URL + allowed tools from the gateway's listing |
| `osint-proxy` | OpenAPI (`openapi/osint-proxy.yaml`) → delivery Function `GET /api/fetch_public_page` | deepsearch agents, tpsrca, cyber-forum, advisor | Sanitised public-page fetch (allow-listed hosts, DLP on URL, size cap, HTML→text) replacing claude.ai `web_fetch`/Firecrawl page reads; the only fetch beside Bing |
| `exchange-graph` | OpenAPI (`openapi/exchange-graph.yaml`) | tpa-evidence-analyzer, advisor | Gmail replacement: read-only shared assurance mailbox (supplier evidence by mail); sending only via gated workflow |
| `teams-graph` / `m365-personal-graph` | OpenAPI (delegated OBO) | example agents (internal-comms, morning, doc-coauthoring) | Slack / personal Gmail+Calendar replacement: the user's own Teams chats, channels, calendar and mail, read-only, on-behalf-of the user |
| `azure-devops` | OpenAPI (`openapi/azure-devops.yaml`) | advisor, cyber-forum, template-manager | GitHub replacement: read-only repos, items, PRs, threads, pipeline runs, code search — no PR/push/merge tools by design |
| `web-search` | Grounding with Bing Search | deepsearch, cyber-forum, regulatory advisors | Live web research with citations (provisioned by `infra/main.bicep` when `enableWebSearch=true`) |
| MS Copilot | See `copilot/README.md` | user-facing Q&A agents | Surfacing agents inside Microsoft 365 Copilot / Teams |
| Workflows | See `../workflows/` | scheduled/event pipelines | Logic Apps replacing Claude Routines (OneTrust intake, Defender briefs, scheduled DeepSearch, Jira↔IAF sync) |

## Read-only rule of record

`attach_integrations.py` keeps **GET** operations plus operations flagged
`x-enx-read-only: true` (idempotent query POSTs: `searchIssuesJql`,
`aqlSearchObjects`, `runHuntingQuery`, SharePoint `searchContent`, Azure
DevOps `codeSearch`); every other verb is stripped unless the connection is
in the agent's `write_connections` (no agent has any). MCP tools: the
`allowed_tools` list of `mcp/enx-gateway.json` is checked against the
gateway's `tools/list` annotations — a tool without `readOnlyHint=true` is
refused. The verify step prints the retained operations per agent
(`attach_integrations.py --dry-run` lists kept POSTs; `verify_conversion.py`
audits them).

## Model tiers

`registry.json` assigns each agent one of three tiers (governance/
MODEL_ROUTING.md): `light` (`LIGHT_MODEL_DEPLOYMENT_NAME`, default
`gpt-4o-mini`: docx/pdf/pptx/xlsx document agents, the
enx-tprm-control-center router, morning), `chat` (`MODEL_DEPLOYMENT_NAME`,
`gpt-4o`: template-driven report generation) and `reasoning`
(`REASONING_MODEL_DEPLOYMENT_NAME`, `o3-mini`: OSINT synthesis, risk
scoring, evidence/SOC/pentest analysis, advisors). All three deployments
are created by `infra/main.bicep`; `attach_integrations.py` maps
`TIER_MAP = {light, chat, reasoning}` and fails for any live agent absent
from the registry (except `example_agents.unmanaged_ok`). Example skills
converted with `--include-examples` have explicit entries (`example: true`).

## Authentication — no secrets in this repo

- Each OpenAPI connection's credentials live in an **Azure AI Foundry
  project connection** (portal: Management center → Connections → Custom
  keys / OAuth) named as in `registry.json` (`conn-*`), backed by Key Vault.
- Microsoft Graph integrations ride on the Foundry project **managed
  identity** (`authType: ManagedIdentity`): Defender
  `SecurityIncident.Read.All`, `SecurityAlert.Read.All`,
  `ThreatHunting.Read.All`; SharePoint `Sites.Selected` (read grant on the
  one InfoSec Assurance site — no `Sites.Read.All`/`ReadWrite`); Entra IAM
  `User/Group/Application.Read.All`, `AccessReview.Read.All`; Exchange
  `Mail.Read` restricted by an application access policy to the shared
  mailbox. Teams and personal calendar/mail are **delegated (OBO)** only
  — never app-only — through the Copilot wrapper (`copilot/README.md`).
- **Provisioning (reproducible):** `connections/connections.bicep` (module
  called from `infra/main.bicep` with Key-Vault-sourced secure params) or
  `connections/create_connections.sh` (`az rest`, secrets read from Key
  Vault by name). `create_connections.sh --verify` is the pre-flight run in
  CI before `attach_integrations.py --check-connections`; both fail fast
  naming the missing `conn-*`. `attach_integrations.py` resolves each name
  to the connection resource id (`client.connections.get(name).id`) — the
  SDK does not accept bare names.
- The Bing grounding key is wired into the `bing-grounding` connection by
  the Bicep; Logic Apps use managed identity + the Azure AI User role.
- The ENX gateway MCP token is NOT part of the tool definition: it is read
  from Key Vault at run time and passed as `tool_resources.mcp[].headers`
  by the caller (`_azure_helpers.mcp_run_headers()`); see `mcp/enx-gateway.json`.
- Consumer connectors of the previous environment (Gmail, Google Drive,
  GitHub, Firecrawl, Slack, Google Calendar, Adobe/Canva/Gamma…) and their
  ENX replacement or exclusion: `CONNECTOR_DECISIONS.md`.

## Order of operations

```bash
python3 ../scripts/convert_skills.py
python3 ../scripts/create_agents.py          # agents + knowledge + code tools
./connections/create_connections.sh --verify  # or deploy connections.bicep via infra/main.bicep
python3 ../scripts/attach_integrations.py --check-connections
python3 ../scripts/attach_integrations.py    # OpenAPI/MCP/Bing + model tiers
```

## Adding another integration

1. Drop a trimmed OpenAPI 3.0 spec in `openapi/` (only the operations agents
   need; rich per-operation descriptions — the model reads them).
2. Register it in `registry.json` under `connections`, and list it on the
   agents that should call it.
3. Create the Foundry connection holding its credentials.
4. Re-run `attach_integrations.py`.
