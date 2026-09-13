# Step 02 — Foundry account, project, model deployments

**Objective.** Deploy `infra/main.bicep` per environment: the Foundry
resource (`Microsoft.CognitiveServices/accounts`, kind `AIServices`,
`allowProjectManagement: true`) with its project, the three model tiers
on `DataZoneStandard` with pinned versions and `NoAutoUpgrade`, the custom
RAI policy, Key Vault, deliverables storage, observability, Document
Intelligence, and — decision D6 — the standard agent setup (customer-owned
Cosmos DB, Storage, AI Search) in `test`/`prod`, with the agents subnet
of step 01 injected at creation.

**Owner / effort.** `{upn:francisco.gomes}`; 2 days. **Depends on** 01.

## 1. Platform facts that shape this step

| Fact | Status / source |
|---|---|
| Resource model: one Foundry resource + child projects (`accounts/projects`); Agent Service GA and the Foundry API exist only for Foundry projects (not hub-based) | [GA] https://learn.microsoft.com/en-us/azure/foundry/what-is-foundry (2026-08-27); https://learn.microsoft.com/en-us/azure/foundry-classic/how-to/migrate-project (2026-09-11) |
| Bicep api-versions for `accounts`, `projects`, `deployments`, `connections`: **`2025-06-01` (stable) everywhere in the kit**; later stable versions `2025-09-01`, `2025-12-01`, … | [GA] https://learn.microsoft.com/en-us/azure/templates/microsoft.cognitiveservices/accounts/projects (2026-07-20) — the preview→stable move was made after `bicep build` showed the compiled ARM identical apart from the api-version string in every affected file; confirm with `what-if` before the first deployment, and treat any later bump the same way (Tier C change) |
| Deployment SKUs: `DataZoneStandard` keeps processing inside the EU Data Zone (follows the EU Data Boundary, may include EFTA); `GlobalStandard` processes anywhere; data at rest stays in the resource region for all types | [GA] https://learn.microsoft.com/en-us/azure/foundry/foundry-models/concepts/deployment-types (2026-08-12) |
| EU Data Zone availability in `swedencentral` (and FR/DE/IT/PL/ES/…): `gpt-4o 2024-11-20`, `gpt-4o-mini`, `o3-mini`, `o4-mini`, `gpt-4.1`, `gpt-5`, `gpt-5-mini` | [GA] https://learn.microsoft.com/en-us/azure/foundry/foundry-models/concepts/models-sold-directly-by-azure-region-availability (2026-09-04) |
| Tool support by model: `o3-mini` — OpenAPI **No**, MCP **No**, Azure AI Search **No**, SharePoint **No**, Web Search **No**; `gpt-4o-mini` lacks Azure AI Search | [GA] https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/limits-quotas-regions#tool-support-by-region-and-model (2026-09-07) |
| Retirements: `gpt-4o 2024-11-20` Legacy → 2027-04-14 (`gpt-5.1`); `gpt-4o-mini 2024-07-18` Deprecated → 2027-04-14; GA models get an 18-month lifecycle, ≥ 60 days notice, replacement declared 90–120 days before | [GA] https://learn.microsoft.com/en-us/azure/foundry/openai/concepts/model-retirement-schedule (2026-09-02); …/model-retirements (2026-07-24) |
| `versionUpgradeOption`: `OnceNewDefaultVersionAvailable` / `OnceCurrentVersionExpired` / `NoAutoUpgrade` | [GA] https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/working-with-models (2026-06-05) |
| Standard agent setup: Cosmos DB for NoSQL (≥ 3000 RU/s; containers `agent-definitions-v1`, `run-state-v1` for the new runtime), Storage (files), AI Search (vector stores); capability host fixed at creation | [GA] https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/standard-agent-setup (2026-07-09); …/capability-hosts (2026-08-21) |
| EU Data Zone price ≈ 9 % above Global from 2026-09-01 (Tech Community post; date not readable) | [unknown] https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/microsoft-foundry-model-deployment-pricing-update/4535385 — budget line in `operations/FINOPS.md` §1 to be re-based |
| Agents, evaluations, workflows require Entra ID auth (no API keys) — the kit already sets `disableLocalAuth: true` | [GA] https://learn.microsoft.com/en-us/azure/foundry/concepts/general-availability (2026-09-09) |

## 2. Click-path

**Azure portal (what the Bicep does, for verification).** Create a
resource → *Microsoft Foundry* → Basics: subscription, RG, region `Sweden
Central`, name `{baseName}-aif`, *Default project* `{baseName}-proj` →
Networking: *Disabled* + the private endpoint on `snet-pe`; *Agent
networking*: BYO subnet `snet-agents` (step 01) → Encryption: Microsoft-
managed (CMK is optional; requires same-region Key Vault with purge
protection — [GA] https://learn.microsoft.com/en-us/azure/foundry/concepts/encryption-keys-portal (2026-08-25)) → Identity: system-assigned → Review + create.
**Foundry portal.** *Home* → project `{baseName}-proj` → *Build* →
**Models** → *Deploy model* → `gpt-4o` (version `2024-11-20`), deployment
type **Data Zone Standard**, capacity 50 K TPM, guardrail
`infosec-security-analysis`, *Version upgrade policy* = **No auto-upgrade**;
repeat for the light and reasoning tiers. *Operate* → *Assets* shows the
resource, project and capability host after the first agent is created.

## 3. CLI / Bicep / kit scripts

```bash
cd convertion/setup && cp .env.example .env         # fill subscription, region, RG
./provision.sh                                      # RG + infra/main.bicep with infra/main.parameters.json
#   prod: az deployment group create -g rg-infosec-foundry --template-file ../infra/main.bicep \
#         --parameters ../infra/main.parameters.prod.json
az cognitiveservices model list -l swedencentral --query "[?model.name=='gpt-4o' || model.name=='gpt-4o-mini' || model.name=='o4-mini'].{n:model.name,v:model.version,sku:model.skus[].name}" -o table
```

### A. Model tiers (`main.parameters.*.json`)

| Tier (`integrations/registry.json` `model_tiers`) | Deployment (`main.bicep` param) | Version | SKU | Capacity | Note |
|---|---|---|---|---|---|
| `chat` | `modelName=gpt-4o` | `2024-11-20` (explicit) | `DataZoneStandard` | 50 K TPM | retires 2027-04-14 → D4 replacement project |
| `light` | `lightModelName=gpt-4o-mini` | set explicitly (kit default `''` = provider default — set `2024-07-18`, `operations/LIFECYCLE.md` §5) | `DataZoneStandard` | 100 K | lacks Azure AI Search (not used by light agents) |
| `reasoning` | `reasoningModelName` = `o4-mini` — **not `o3-mini`** (D3) | `2025-04-16`, re-confirmed on the day | `DataZoneStandard` | 30 K | must show OpenAPI + MCP + Web Search = Yes in the tool-support table on the day; record the row in the sign-off |
| candidate (D4) | fourth deployment `{replacement}` | explicit | `DataZoneStandard` | 10 K | created only during a migration window, compared with the comparison set, then tiers switched (`attach_integrations.py --only`) — six-phase process: https://learn.microsoft.com/en-us/azure/foundry/foundry-models/concepts/model-migration (2026-08-26) |

Every deployment in `main.bicep` already carries `raiPolicyName:
raiPolicy.name` (custom policy `infosec-security-analysis`, step 08 §1).
Add the pin (literal, part of shared delta S-02 to `main.bicep`, in each
of the three `deployments` resources' `properties`):

```bicep
    versionUpgradeOption: 'NoAutoUpgrade'
```

Self-contained reference shape of one pinned deployment (validated with
Bicep 0.47.16; `BCP081` warning expected for the Bing type only):

```bicep
// series-02-deployment-example.bicep — one pinned, RAI-governed EU deployment
param foundryAccountName string
param deploymentName string = 'gpt-4o'
param modelVersion string = '2024-11-20'
param capacity int = 50
param raiPolicyName string = 'infosec-security-analysis'

resource foundry 'Microsoft.CognitiveServices/accounts@2025-06-01' existing = { name: foundryAccountName }

resource deployment 'Microsoft.CognitiveServices/accounts/deployments@2025-06-01' = {
  parent: foundry
  name: deploymentName
  sku: { name: 'DataZoneStandard', capacity: capacity }
  properties: {
    model: { format: 'OpenAI', name: deploymentName, version: modelVersion }
    versionUpgradeOption: 'NoAutoUpgrade'
    raiPolicyName: raiPolicyName
  }
}
output deploymentId string = deployment.id
```

### B. Agent setup and network injection (D6, D7) — shared delta S-02 for `main.bicep`

`main.bicep` today creates a *basic* setup (no capability host → Microsoft-
managed agent storage). For `test`/`prod` add, behind
`param enableStandardAgentSetup bool = false` and `param agentsSubnetId string = ''`:

- `Microsoft.DocumentDB/databaseAccounts` (NoSQL, ≥ 3000 RU/s, private endpoint, zone `privatelink.documents.azure.com`),
- `Microsoft.Search/searchServices` (basic or standard, `disableLocalAuth: true`, private endpoint, zone `privatelink.search.windows.net`),
- the existing `storage` account reused for agent files,
- project connections to the three (categories `CosmosDB`, `CognitiveSearch`, `AzureStorageAccount`, auth = project managed identity),
- `accounts/projects/capabilityHosts` `agents` referencing the three connections, created **after** the RBAC of step 03 (the project MI needs data-plane roles on Cosmos DB, Search and Storage),
- `networkInjections` on the account pointing at `agentsSubnetId` (`useMicrosoftManagedNetwork: false`).

Exact property names come from the standard-setup Bicep samples referenced
by the doc above; the integration pass validates them with
`infra/validate.sh` before the kit adopts them. Do not create any agent in
`test`/`prod` until the capability host exists (it cannot be added later).

### C. Reasoning-tier decision procedure (D3)

1. Open the tool-support table (source above) on the execution day; list
   the EU-DZ models whose OpenAPI, MCP, Web Search, File Search and Code
   Interpreter columns are all *Yes* for `swedencentral`.
2. Deploy the candidate as `reasoningModelName` in `dev`; run
   `scripts/smoke_test.py --agent infosec-assurance-advisor` and the
   comparison set (`operations/CHANGE_MANAGEMENT.md` §4).
3. Record the model, version and the table row in the sign-off; the
   `MODEL_ROUTING.md` "reasoning" default changes accordingly (shared
   delta, listed in step 06).

## 4. Values captured into `setup/.env`

| Variable | From |
|---|---|
| `PROJECT_ENDPOINT` | `provision-outputs.json` → `projectEndpoint` (printed by `provision.sh`) |
| `MODEL_DEPLOYMENT_NAME`, `REASONING_MODEL_DEPLOYMENT_NAME`, `LIGHT_MODEL_DEPLOYMENT_NAME` | deployment names of §A |
| `AGENT_SETUP=standard|basic` | D6 (new, S-04) |
| `KEY_VAULT_NAME`, `STORAGE_ACCOUNT_NAME`, `LOG_ANALYTICS_NAME` | Bicep outputs `keyVaultName`, `storageAccountName`, `logAnalyticsName` |

## 5. Verification

| # | Check | Pass when |
|---|---|---|
| V1 | `az cognitiveservices account show -n {baseName}-aif --query "{kind:kind,pm:properties.allowProjectManagement,la:properties.disableLocalAuth,pna:properties.publicNetworkAccess}"` | `AIServices`, `true`, `true`, `Disabled` (test/prod) |
| V2 | `az cognitiveservices account deployment list -n {baseName}-aif --query "[].{n:name,sku:sku.name,v:properties.model.version,up:properties.versionUpgradeOption,rai:properties.raiPolicyName}" -o table` | three rows, all `DataZoneStandard`, explicit versions, `NoAutoUpgrade`, `infosec-security-analysis` |
| V3 | Reasoning model row in the tool-support table | OpenAPI/MCP/Web Search = Yes (screenshot filed) |
| V4 | Bicep output `dataResidency` | `region` EU, `modelDeploymentSku` `DataZoneStandard`, `outsideEuBoundary` = `bing-grounding (…)` only |
| V5 | Capability host (`test`/`prod`): Foundry portal → *Operate* → *Assets* → project → agent storage | shows the customer Cosmos DB / Search / Storage; `AGENT_SETUP=standard` |
| V6 | Quota: Foundry portal → *Build* → *Models* → quota view | requested TPM granted for all three deployments; no `429` on `smoke_test.py` |
| V7 | `az resource list -g … --query "[?location!='swedencentral' && location!='global'].name"` | empty |

**Rollback.** Bicep is declarative — redeploy the previous commit's
template/parameters (`what-if` first). Model deployments can be deleted
and recreated (agents referencing them fail until recreated). The
capability host **cannot** be rolled back to basic: delete and recreate
the project (before any agent exists). **ISMS evidence.** deployment
outputs, V1–V7 outputs — ISO 27001:2022 A.5.23, A.8.9 (configuration
management); ISO 42001 A.6.2.4 (AI system deployment); DORA Art. 9(2),
Art. 12 (backup — standard setup); EU AI Act Art. 12 (logging).

## Sources
- [GA] Resource model — https://learn.microsoft.com/en-us/azure/foundry/what-is-foundry (2026-08-27)
- [GA] Project types — https://learn.microsoft.com/en-us/azure/foundry-classic/how-to/migrate-project (2026-09-11)
- [GA] Bicep api-versions — https://learn.microsoft.com/en-us/azure/templates/microsoft.cognitiveservices/accounts/projects (2026-07-20)
- [GA] Deployment types — https://learn.microsoft.com/en-us/azure/foundry/foundry-models/concepts/deployment-types (2026-08-12)
- [GA] EU region availability — https://learn.microsoft.com/en-us/azure/foundry/foundry-models/concepts/models-sold-directly-by-azure-region-availability (2026-09-04)
- [GA] Tool support by model — https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/limits-quotas-regions#tool-support-by-region-and-model (2026-09-07)
- [GA] Retirement schedule / lifecycle — https://learn.microsoft.com/en-us/azure/foundry/openai/concepts/model-retirement-schedule (2026-09-02); https://learn.microsoft.com/en-us/azure/foundry/openai/concepts/model-retirements (2026-07-24)
- [GA] versionUpgradeOption — https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/working-with-models (2026-06-05)
- [GA] Standard agent setup / capability hosts — https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/standard-agent-setup (2026-07-09); https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/capability-hosts (2026-08-21)
- [GA] Model migration process — https://learn.microsoft.com/en-us/azure/foundry/foundry-models/concepts/model-migration (2026-08-26)
- [GA] CMK — https://learn.microsoft.com/en-us/azure/foundry/concepts/encryption-keys-portal (2026-08-25)
- [unknown] EU Data Zone pricing — https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/microsoft-foundry-model-deployment-pricing-update/4535385
