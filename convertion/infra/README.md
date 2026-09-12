# Infrastructure — Bicep for the InfoSec Assurance Foundry platform

Everything the converted skills, workflows and functions depend on is
provisioned here, EU-resident, Entra-only, with managed identities and no
secret values in the repository. Validate before every deploy:
`./validate.sh` (build + lint + policy) and `./validate.sh --what-if {rg}`.

## Modules

| File | Provisions | Switch (main.bicep param) |
|---|---|---|
| `main.bicep` | Foundry account + project, three model tiers (`light`/`chat`/`reasoning`) on the EU Data Zone SKU with **pinned versions + `NoAutoUpgrade`**, custom RAI policy, **agent-egress VNet injection**, **CMK**, Bing grounding, Log Analytics + App Insights (365-day retention) with account *and project* diagnostics, Key Vault (RBAC, purge protection), hardened deliverables storage, Document Intelligence (OCR), optional Speech | always |
| `agent-stores.bicep` | **Standard agent setup**: Cosmos DB (conversations + agent definitions), Azure AI Search (vector stores / knowledge base), the three AAD project connections and the **immutable capability host** that binds them | `enableStandardAgentSetup` |
| `defender-ai.bicep` | Defender for Cloud **AI threat-protection plan** (subscription scope, deployed separately with `az deployment sub create`) | `enableAiPlan` |
| `../enterprise/azure-policy-assignments.bicep` | Preventive Azure Policy: EU locations, no local auth, network restriction, Key Vault protection, CMK audit, `Deny` on Global\* deployment SKUs | `enablePolicyAssignments` + `policyEffectMode` |
| `delivery.bicep` | Elastic Premium plan + Linux **container** Function Apps: `{baseName}-delivery` (functions/delivery, the only SharePoint writer) and `{baseName}-office` (functions/office-tools: LibreOffice, pandoc, poppler, qpdf, tesseract, ImageMagick, Node 20 renderers), private container registry (managed-identity pull), identity-based runtime storage | `enableDelivery`, `deliveryImage`, `officeToolsImage` |
| `logicapp.bicep` | Logic Apps Standard (WS1) hosting `workflows/*.json`; app settings carry the workflow parameters and `@Microsoft.KeyVault(...)` references for every secret | `enableLogicApps` |
| `mcp-server.bicep` | Container Apps environment + app for `mcp-server/` (streamable HTTP), Easy Auth restricted to `sg-infosec-foundry-users`, internal ingress when the VNet is on | `enableMcpHosting` |
| `static-web-app.bicep` | Optional rendered hosting for approved HTML dashboards (see *Artifacts decision*) | `enableStaticWebApp` |
| `monitoring.bicep` + `kql/` | Action group and scheduled-query alerts: internal-marker egress, verifier FAIL rate, pipeline failures, approval expiry, agent drift | `enableMonitoring` |
| `cost.bicep` | Resource-group budget with 50/80/100 % alerts | `enableBudget` |
| `network.bicep`, `private-endpoint.bicep` | VNet (PE / apps / **agents** / Container Apps subnets), NSGs, private DNS zones, private endpoints for Foundry, Key Vault, storage, Cosmos DB, AI Search, Function and Logic App | `enablePrivateNetworking` (+ `publicNetworkAccess: Disabled`) |
| `workload-rbac.bicep` | Data-plane roles for the workload managed identities (same guid seeds as `../team/rbac.bicep`, so both are idempotent together) | always |
| `../team/rbac.bicep` | Human groups, PIM eligibilities, deploy identity (team model of record) | `deployTeamRbac` + group object ids |
| `guard.bicep` | Deployment-time assertions (public access without private networking; VNet injection without a subnet; CMK URI without a key name — each fails what-if before any change) | always |

Parameter sets: `main.parameters.json` (dev: public access on, no VNet,
placeholder images, `basic` Search SKU, policies off) and
`main.parameters.prod.json` (private endpoints, public access disabled, images
pinned, MCP hosting, budget, team RBAC, standard agent setup, agent VNet
injection, `Deny` policies, Defender alert routing).

## Decisions that CANNOT be changed after the first agent exists

Three switches bind at account/project creation; changing them later means
rebuilding the project and re-uploading every vector store. `validate.sh`
fails the prod profile if any of them is off.

| Switch | What it decides | Why it is irreversible |
|---|---|---|
| `enableStandardAgentSetup` | Conversations, uploaded files and vector stores live in `{baseName}-cosmos` / `{baseName}-search` / `{baseName}sa` (this subscription) instead of Microsoft-managed multitenant storage | The capability host that binds the project to those stores is immutable once an agent exists |
| `enableAgentVnetInjection` | Agent **tool egress** (OpenAPI, MCP, A2A, web search) leaves through `snet-agents` and is seen by the hub firewall | `networkInjections` cannot be added to an existing Foundry account; private endpoints are inbound only |
| `cmkKeyUri` | Encryption at rest with the key in `{baseName}-kv` | The account can adopt CMK later, but the Cosmos DB store must be created with it |

Prod order: (1) `main.bicep` with standard agent setup + VNet injection and
`cmkKeyUri` empty; (2) `enterprise/landing-zone.bicep` creates the CMK key and
grants `Key Vault Crypto Service Encryption User` to the Foundry, storage,
Cosmos DB and AI Search identities; (3) `main.bicep` again with `cmkKeyUri`
set; (4) `az deployment sub create -f defender-ai.bicep`; (5) `deploy.sh`
(agents) — never before step 1 has succeeded.

## Residency (requirement i) — per-component processing location

| Component | Where data is processed | Control |
|---|---|---|
| Foundry account, project, agent **conversations**, uploaded files, vector stores (`vs-*`, `vs-assurance-memory`) | `location` — with `enableStandardAgentSetup` (prod default) in **this subscription**: `{baseName}-cosmos` (conversations, 90-day TTL), `{baseName}-search` (vector stores / knowledge base), `{baseName}sa` (files) | `agent-stores.bicep` capability host, Entra-only, private endpoints, CMK. `false` falls back to Microsoft-managed in-region storage — allowed in dev only |
| Model inference (all three tiers) | EU Data Zone (`deploymentSku = DataZoneStandard`); `GlobalStandard` is not allowed | `validate.sh` policy check |
| Bing grounding / Web Search | **Global** service — only the sanitised public query leaves the EU, and the data **leaves the Azure compliance boundary so the DPA does not apply** (DATA_PROTECTION_GUARDRAILS §1) | Instruction + `egress-internal-markers` alert; **accepted residual risk, owner: platform owner**, recorded in the RoPA; domain-restricted search is the alternative under review |
| Key Vault, storage, Cosmos DB, AI Search, Log Analytics, App Insights, Function/Logic Apps, Container Apps, Document Intelligence, Speech, registry | `location` | Bicep + `allowed-locations` policy assignment (`enablePolicyAssignments`) |
| Agent **tool egress** (OpenAPI, MCP, A2A) | leaves through `snet-agents` → hub firewall FQDN allow-list | `enableAgentVnetInjection`; private endpoints cover inbound only |
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

With `enablePrivateNetworking`: Foundry, Key Vault, storage, Cosmos DB, AI
Search, the delivery Function and the Logic App are reached only through
private endpoints; the apps integrate with `snet-apps` and route all traffic
through the VNet; the Function accepts calls only from the Logic App subnet.
Subnets: `snet-pe` (10.60.0.0/26), `snet-apps` (10.60.0.64/26), `snet-agents`
(10.60.1.0/24, delegated `Microsoft.App/environments` — **agent tool egress**,
`enableAgentVnetInjection`) and `snet-aca` (10.60.2.0/23). Outbound FQDN
allow-list to enforce on the firewall/proxy (NSGs cannot filter FQDNs):
`*.services.ai.azure.com`, `*.openai.azure.com`, `*.cognitiveservices.azure.com`,
`graph.microsoft.com`, `login.microsoftonline.com`, `*.vault.azure.net`,
`*.blob/queue/table.core.windows.net`, `*.azurecr.io`, `*.atlassian.net`
(Jira/Confluence), `*.onetrust.com`, `api.securityscorecard.io`, `{iaf-host}`,
`{enx-gateway-host}`, `api.bing.microsoft.com` (platform side only).

## Preventive policy, Defender and Purview

`validate.sh` is a client-side gate: it cannot stop a portal or CLI change.
`enablePolicyAssignments` deploys `../enterprise/azure-policy-assignments.bicep`
at resource-group scope (`Audit` in dev, `Deny` in prod) for EU locations,
no local auth, network restriction, Key Vault protection, CMK audit and the
custom "no Global\* deployment SKU" definition — the platform team creates
that definition once at subscription scope and its id goes into
`denyGlobalSkuDefinitionId`. Verify a built-in GUID before the first run
(`az policy definition show --name <guid> --query displayName -o tsv`).

Defender for Cloud AI threat protection is enabled by `defender-ai.bicep`
(subscription scope, `AIPromptEvidence` off by default — prompt bodies can
carry Euronext-derived content). `monitoring.bicep` routes the resulting
security alerts: `Error`-level to `{baseName}-ag-soc` (`socEmail`), the rest
to the owner action group.

Purview governs the Foundry interactions themselves (DSPM for AI, audit,
retention, eDiscovery, Insider Risk). The platform side is the account *and
project* diagnostic settings created here plus user context on every call;
`purviewAccountId` records the governing account in the deployment outputs as
the evidence pointer. Per-report sensitivity labels are applied by the
delivery Function, not here.

## CI

`validate.sh` is the gate: pinned Bicep `0.47.16` (the `!` non-null
assertion needs ≥ 0.36), build + lint of every module, parameter-file
coherence, EU location / Data Zone / retention / placeholder policy, and
`--what-if {rg}` on PRs with a Reader OIDC identity; `create` runs on main
after environment approval.
