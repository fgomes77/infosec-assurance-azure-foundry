# Infrastructure — Bicep for the InfoSec Assurance Foundry platform

Everything the converted skills, workflows and functions depend on is
provisioned here, EU-resident, Entra-only, with managed identities and no
secret values in the repository. Validate before every deploy:
`./validate.sh` (build + lint + policy) and `./validate.sh --what-if {rg}`.

## Modules

| File | Provisions | Switch (main.bicep param) |
|---|---|---|
| `main.bicep` | Foundry account + project, three model tiers (`light`/`chat`/`reasoning`) on the EU Data Zone SKU, custom RAI policy, Bing grounding, Log Analytics + App Insights (365-day retention) with diagnostic settings, Key Vault (RBAC, purge protection), hardened deliverables storage, Document Intelligence (OCR), optional Speech | always |
| `delivery.bicep` | Elastic Premium plan + Linux **container** Function Apps: `{baseName}-delivery` (functions/delivery, the only SharePoint writer) and `{baseName}-office` (functions/office-tools: LibreOffice, pandoc, poppler, qpdf, tesseract, ImageMagick, Node 20 renderers), private container registry (managed-identity pull), identity-based runtime storage | `enableDelivery`, `deliveryImage`, `officeToolsImage` |
| `logicapp.bicep` | Logic Apps Standard (WS1) hosting `workflows/*.json`; app settings carry the workflow parameters and `@Microsoft.KeyVault(...)` references for every secret | `enableLogicApps` |
| `mcp-server.bicep` | Container Apps environment + app for `mcp-server/` (streamable HTTP), Easy Auth restricted to `sg-infosec-foundry-users`, internal ingress when the VNet is on | `enableMcpHosting` |
| `static-web-app.bicep` | Optional rendered hosting for approved HTML dashboards (see *Artifacts decision*) | `enableStaticWebApp` |
| `monitoring.bicep` + `kql/` | Action group and scheduled-query alerts: internal-marker egress, verifier FAIL rate, pipeline failures, approval expiry, agent drift | `enableMonitoring` |
| `cost.bicep` | Resource-group budget with 50/80/100 % alerts | `enableBudget` |
| `network.bicep`, `private-endpoint.bicep` | VNet (PE / apps / Container Apps subnets), NSG, private DNS zones, private endpoints for Foundry, Key Vault, storage, Function and Logic App | `enablePrivateNetworking` (+ `publicNetworkAccess: Disabled`) |
| `workload-rbac.bicep` | Data-plane roles for the workload managed identities (same guid seeds as `../team/rbac.bicep`, so both are idempotent together) | always |
| `../team/rbac.bicep` | Human groups, PIM eligibilities, deploy identity (team model of record) | `deployTeamRbac` + group object ids |
| `guard.bicep` | Deployment-time assertion (`Disabled` public access without private networking fails what-if) | always |

Parameter sets: `main.parameters.json` (dev: public access on, no VNet,
placeholder images) and `main.parameters.prod.json` (private endpoints,
public access disabled, images pinned, MCP hosting, budget, team RBAC).

## Residency (requirement i) — per-component processing location

| Component | Where data is processed | Control |
|---|---|---|
| Foundry account, project, agent threads, uploaded files, vector stores (`vs-*`, `vs-assurance-memory`) | `location` (EU allow-list enforced by `@allowed` + `validate.sh`) — Microsoft-managed storage in that region | Basic agent setup keeps data in-region; BYO storage/Cosmos/AI Search ("standard agent setup") is the option if the ISMS requires customer-subscription custody — **accepted risk, owner: platform owner**, revisit at the annual review |
| Model inference (all three tiers) | EU Data Zone (`deploymentSku = DataZoneStandard`); `GlobalStandard` is not allowed | `validate.sh` policy check |
| Bing grounding | **Global** service — only the sanitised public query leaves the EU (DATA_PROTECTION_GUARDRAILS §1) | Instruction + `egress-internal-markers` alert; **accepted residual risk, owner: platform owner** |
| Key Vault, storage, Log Analytics, App Insights, Function/Logic Apps, Container Apps, Document Intelligence, Speech, registry | `location` | Bicep |
| Microsoft Graph (SharePoint, Defender, Entra) | EU tenant | Managed identity, `Sites.Selected` |
| Static Web App (optional) | `westeurope` | Entra auth |

Model availability per EU region changes; run
`az cognitiveservices model list -l {location} -o table` before changing
`modelName`/`*ModelFormat`.

## Claude tiers on Foundry (fidelity option)

Anthropic Claude models are offered in the Foundry model catalog; where a
Claude deployment is available in the EU Data Zone, set
`lightModelFormat/chatModelFormat/reasoningModelFormat = 'Anthropic'` with
`lightModelName` = Haiku, `modelName` = Sonnet, `reasoningModelName` = Opus
(current catalog names). Reproducibility procedure before switching a tier:
run `scripts/smoke_test.py` prompts plus one known assessment on both
deployments, diff the rendered deliverables (renderers are deterministic, so
only the verified JSON should differ) and file the comparison with the
template-manager approval. Tool-use/MCP behaviour is provided by the Foundry
Agents runtime, not the model SDK — no Anthropic SDK is needed in the kit.

## Artifacts decision (HTML dashboards)

Default: approved dashboards (DeepSearch, CISO executive summary, template
review pages) are stored in SharePoint as **self-contained single-file HTML**
(no CDN scripts — the templates must vendor Chart.js) and opened as
downloads. `enableStaticWebApp = true` adds rendered hosting behind Entra
for teams that need a link that opens as a page; the delivery Function then
publishes the approved file there after the approval gate. The
`web-artifacts-builder` skill (React/Vite bundling) is **not deployed** —
no need it serves exists once dashboards are self-contained HTML.

## Delivery and office toolchain

`functions/delivery` and `functions/office-tools` run as custom containers
(a Flex Consumption Python app has no Node runtime, so pptxgenjs/docx
renderers and LibreOffice conversions would be dead code). Build and push:

```bash
az acr build -r {registryLoginServer%%.*} -t infosec-delivery:{tag} ../functions/delivery
az acr build -r {registryLoginServer%%.*} -t infosec-office-tools:{tag} ../functions/office-tools
az deployment group create -g {rg} -f main.bicep -p main.parameters.prod.json \
  -p deliveryImage={registry}.azurecr.io/infosec-delivery:{tag} officeToolsImage={registry}.azurecr.io/infosec-office-tools:{tag}
```

App settings injected (both apps): `PROJECT_ENDPOINT`, `KEY_VAULT_NAME`,
`SHAREPOINT_SITE_ID`, `SHAREPOINT_REPORTS_DRIVE_ID`, `DOCINTEL_ENDPOINT`,
`OFFICE_TOOLS_BASE_URL`, `ENX_DATA_BOUNDARY=EU`. Document Intelligence is
reached only from the delivery Function (`/api/extract_pdf`) with its managed
identity — never attached to agents, so the "strip every non-GET" rule of
`attach_integrations.py` needs no exception.

## Workflows packaging (Logic Apps Standard)

Expected zip layout for `az logicapp deployment source config-zip -g {rg}
-n {baseName}-la --src workflows.zip`: one folder per workflow containing
`workflow.json` (the `definition` from `workflows/*.json`), with the seven
report-delivery pipelines expanded from `workflows/pipelines.json` as
`report-delivery-<pipeline>/workflow.json` and a root `parameters.json`
whose values read `@appsetting('FOUNDRY_ENDPOINT')`, `@appsetting('DELIVERY_FUNCTION_BASE_URL')`
and the secret settings below. (`scripts/package_workflows.py` builds it.)

## Secrets (Key Vault `{baseName}-kv`) — names only

| Secret name | Bound as | Used by |
|---|---|---|
| `kv-delivery-function-key` | `DELIVERY_FUNCTION_KEY` | Logic Apps → delivery Function |
| `kv-approval-webhook-url` | `APPROVAL_WEBHOOK_URL` | approval gates |
| `kv-teams-webhook-url` | `TEAMS_WEBHOOK_URL` | notifications |
| `kv-jira-api-token`, `kv-onetrust-api-token`, `kv-iaf-client-secret` | same-named settings | intake / finding-sync workflows and Foundry connections |
| `kv-confluence-api-token`, `kv-ssc-api-key`, `kv-enx-gateway-token` | Foundry connections (by reference) | agents (read-only) |

Populate with `az keyvault secret set --vault-name {baseName}-kv -n <name>
--value @-` from the pipeline's environment; never from files in the repo.

## Network

With `enablePrivateNetworking`: Foundry, Key Vault, storage, the delivery
Function and the Logic App are reached only through private endpoints;
the apps integrate with `snet-apps` and route all traffic through the VNet;
the Function accepts calls only from the Logic App subnet. Outbound FQDN
allow-list to enforce on the firewall/proxy (NSGs cannot filter FQDNs):
`*.services.ai.azure.com`, `*.openai.azure.com`, `*.cognitiveservices.azure.com`,
`graph.microsoft.com`, `login.microsoftonline.com`, `*.vault.azure.net`,
`*.blob/queue/table.core.windows.net`, `*.azurecr.io`, `*.atlassian.net`
(Jira/Confluence), `*.onetrust.com`, `api.securityscorecard.io`, `{iaf-host}`,
`{enx-gateway-host}`, `api.bing.microsoft.com` (platform side only).

## CI

`validate.sh` is the gate: pinned Bicep `0.47.16` (the `!` non-null
assertion needs ≥ 0.36), build + lint of every module, parameter-file
coherence, EU location / Data Zone / retention / placeholder policy, and
`--what-if {rg}` on PRs with a Reader OIDC identity; `create` runs on main
after environment approval.
