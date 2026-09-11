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
| `sharepoint-graph` | OpenAPI (`openapi/sharepoint-graph.yaml`) | document + reporting agents | Evidence repository reads; publish generated deliverables |
| `iaf-api` | OpenAPI (`openapi/iaf-api.yaml`) — **template** | dpia, dora, deepsearch, tpsrca | Internal InfoSec Assurance Framework API; align the template to the real internal spec before use |
| `enx-gateway-mcp` | MCP (`mcp/enx-gateway.json`) — **template** | control-center, deepsearch, cyber-forum | Internal ENX gateway MCP server; fill server URL + allowed tools from the gateway's listing |
| `web-search` | Grounding with Bing Search | deepsearch, cyber-forum, regulatory advisors | Live web research with citations (provisioned by `infra/main.bicep` when `enableWebSearch=true`) |
| MS Copilot | See `copilot/README.md` | user-facing Q&A agents | Surfacing agents inside Microsoft 365 Copilot / Teams |
| Workflows | See `../workflows/` | scheduled/event pipelines | Logic Apps replacing Claude Routines (OneTrust intake, Defender briefs, scheduled DeepSearch, Jira↔IAF sync) |

## Reasoning

`registry.json` assigns each agent a model tier: `chat` (default `gpt-4o`)
for deterministic document/report pipelines, `reasoning` (default `o3-mini`,
provisioned by the Bicep) for analytic work — regulatory interpretation,
OSINT synthesis, risk scoring, exhaustive PDF analysis.
`attach_integrations.py` switches each agent to its tier; override the
deployments via `MODEL_DEPLOYMENT_NAME` / `REASONING_MODEL_DEPLOYMENT_NAME`.

## Authentication — no secrets in this repo

- Each OpenAPI connection's credentials live in an **Azure AI Foundry
  project connection** (portal: Management center → Connections → Custom
  keys / OAuth) named as in `registry.json` (`conn-*`), backed by Key Vault.
- Microsoft Graph integrations (Defender, SharePoint) need an Entra app
  registration with application permissions
  (`SecurityIncident.Read.All`, `ThreatHunting.Read.All`, `Sites.ReadWrite.All`
  as applicable) and admin consent — least privilege per agent.
- The Bing grounding key is wired into the `bing-grounding` connection by
  the Bicep; Logic Apps use managed identity + the Azure AI User role.
- The ENX gateway MCP token is injected from Key Vault at deploy time.

## Order of operations

```bash
python3 ../scripts/convert_skills.py
python3 ../scripts/create_agents.py          # agents + knowledge + code tools
# create the conn-* Foundry connections (portal or IaC), then:
python3 ../scripts/attach_integrations.py    # OpenAPI/MCP/Bing + model tiers
```

## Adding another integration

1. Drop a trimmed OpenAPI 3.0 spec in `openapi/` (only the operations agents
   need; rich per-operation descriptions — the model reads them).
2. Register it in `registry.json` under `connections`, and list it on the
   agents that should call it.
3. Create the Foundry connection holding its credentials.
4. Re-run `attach_integrations.py`.
