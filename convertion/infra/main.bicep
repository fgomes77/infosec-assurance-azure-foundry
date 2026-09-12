// Azure AI Foundry environment for the InfoSec Assurance agent toolset.
// Provisions the Foundry account (AIServices) + project + the three model
// deployment tiers (light / chat / reasoning, governance/MODEL_ROUTING.md),
// Bing grounding, observability, Key Vault, deliverables storage, Document
// Intelligence (OCR), and — through modules — the delivery Function App,
// Logic Apps Standard, hosted MCP server, alerts, budget, private networking
// and the team RBAC model. Deploy at resource-group scope (setup/provision.sh,
// validate first with infra/validate.sh). Every tenant value is a {placeholder}.
//
// Residency (requirement i): `location` is restricted to EU regions and model
// deployments use the EU Data Zone SKU, so prompts/completions, conversations,
// files and vector stores are processed inside the EU. The only components
// outside the EU boundary are Bing grounding (sanitised public queries only)
// and, by design, nothing else — see README.md §Residency for the
// per-component table.
//
// DECISIONS TAKEN HERE THAT CANNOT BE TAKEN LATER — all three bind at
// account/project creation and require a rebuild afterwards; deploy prod with
// them set from the first run (ENTERPRISE_BLUEPRINT.md §5 rollout order):
//   1. Standard agent setup (`enableStandardAgentSetup`, finding C5) — the
//      capability host that puts conversations, files and vector stores in the
//      customer subscription ({baseName}-cosmos / -search / sa) is IMMUTABLE
//      once the FIRST AGENT exists. See agent-stores.bicep.
//   2. Agent egress VNet injection (`enableAgentVnetInjection`, finding C12) —
//      `networkInjections` on the Foundry account cannot be added to an
//      existing account. Private endpoints are INBOUND only and never cover
//      the calls an agent's tools make (OpenAPI, MCP, A2A, web search).
//   3. Customer-managed keys (`cmkKeyUri`, finding C22) — CMK can be enabled
//      later on the account, but the Cosmos DB store must be created with it.
// Preventive enforcement of the residency/SKU/private-link rules lives in
// enterprise/azure-policy-assignments.bicep (finding C11, `enablePolicyAssignments`);
// validate.sh remains the client-side gate, not the control.

@description('Base name for all resources (letters/digits, 3-15 chars)')
@minLength(3)
@maxLength(15)
param baseName string = 'infosecfoundry'

@description('Azure region — EU only (Euronext data residency). Must offer Azure AI Foundry, the chosen models and the EU Data Zone')
@allowed([
  'swedencentral'
  'westeurope'
  'northeurope'
  'francecentral'
  'germanywestcentral'
  'italynorth'
  'spaincentral'
  'polandcentral'
  'norwayeast'
  'switzerlandnorth'
])
param location string = 'swedencentral'

@description('Environment profile: test and prod enforce private networking and Disabled public access (main.parameters.test.json / main.parameters.prod.json)')
@allowed(['dev', 'test', 'prod'])
param environmentName string = 'dev'

// ------------------------------------------------------------ model tiers
@description('Chat-tier model (registry model_tier "chat")')
param modelName string = 'gpt-4o'
@description('Chat model version — PINNED (finding C6). gpt-4o 2024-11-20 is Legacy and retires 2027-04-14; the six-phase migration to its replacement runs on dev with the comparison set before Q1 2027 (enterprise/UPDATE_AND_UPGRADE_REVIEW_POLICY.md, MDL-2)')
param modelVersion string = '2024-11-20'
@description('Chat-tier capacity (thousands of tokens-per-minute)')
param modelCapacity int = 50

@description('Reasoning-tier model for analytic agents (regulatory interpretation, OSINT synthesis). Finding C4 RESOLVED: o3-mini supports NO OpenAPI, MCP, AI Search, SharePoint or Web Search tools and every reasoning agent carries that read surface, so the tier of record is a tool-capable reasoning model. Matrix of record: integrations/registry.json model_tiers._tool_compatibility (alternate gpt-5-mini, then gpt-4.1). Confirm the OpenAPI + MCP + Web Search columns for the chosen model on the day of deployment and record the row in the step-02 sign-off.')
param reasoningModelName string = 'o4-mini'
@description('Reasoning model version — PINNED (finding C6): never leave empty in prod, an unpinned deployment follows the provider default and silently changes validated deliverables. Re-confirm with `az cognitiveservices model list -l <location> -o table` before the first deployment — this value must be a version of reasoningModelName, not of the rejected o3-mini')
param reasoningModelVersion string = '2025-04-16'
@description('Reasoning-tier capacity (thousands of tokens-per-minute)')
param reasoningModelCapacity int = 30

@description('Light-tier model (deterministic template/schema transformations: docx, pdf, pptx, xlsx agents). gpt-4o-mini is DEPRECATED — plan the replacement with the comparison set (finding C6 / MDL-2)')
param lightModelName string = 'gpt-4o-mini'
@description('Light model version — PINNED (finding C6)')
param lightModelVersion string = '2024-07-18'
@description('Light-tier capacity (thousands of tokens-per-minute)')
param lightModelCapacity int = 100

@description('Model publisher format per tier. OpenAI = Azure OpenAI models; Anthropic = Claude models from the Foundry catalog (Haiku→light, Sonnet→chat, Opus→reasoning) where offered in the EU Data Zone — verify with `az cognitiveservices model list -l <location>` before switching (README §Claude tiers)')
@allowed(['OpenAI', 'Anthropic'])
param chatModelFormat string = 'OpenAI'
@allowed(['OpenAI', 'Anthropic'])
param reasoningModelFormat string = 'OpenAI'
@allowed(['OpenAI', 'Anthropic'])
param lightModelFormat string = 'OpenAI'

@description('Deployment SKU: DataZoneStandard keeps inference inside the EU data zone (residency); Standard = single-region; GlobalStandard is NOT allowed (routes worldwide) and is denied by Azure Policy, not only by this @allowed list (finding C11)')
@allowed(['DataZoneStandard', 'Standard'])
param deploymentSku string = 'DataZoneStandard'

@description('Model auto-upgrade behaviour on all three deployments (finding C6). NoAutoUpgrade is mandatory in prod: report agents are validated against known-good outputs, so an upgrade would change deliverables without a change record. OnceCurrentVersionExpired is the dev convenience')
@allowed(['NoAutoUpgrade', 'OnceNewDefaultVersionAvailable', 'OnceCurrentVersionExpired'])
param modelVersionUpgradeOption string = 'NoAutoUpgrade'

@description('Provision Grounding with Bing Search for agent web research (global service — sanitised queries only, README §Residency)')
param enableWebSearch bool = true

// ------------------------------------------------------------ platform
@description('Public network access on Foundry, Key Vault and storage. Disabled requires enablePrivateNetworking = true')
@allowed(['Enabled', 'Disabled'])
param publicNetworkAccess string = 'Enabled'

@description('Deploy the VNet, private DNS zones and private endpoints (network.bicep)')
param enablePrivateNetworking bool = false

@description('Log Analytics / App Insights retention in days (≥ 365 for DORA Art. 28 evidence)')
@minValue(365)
param logRetentionDays int = 365

@description('Deliverables storage redundancy (ZRS or GRS within the EU pair)')
@allowed(['Standard_ZRS', 'Standard_GRS', 'Standard_LRS'])
param storageSku string = 'Standard_ZRS'

@description('Provision Azure AI Document Intelligence for OCR of scanned evidence (reached ONLY through the delivery Function)')
param enableDocumentIntelligence bool = true

@description('Provision Azure AI Speech (transcription skills) in the same EU region')
param enableSpeech bool = false

// ------------------------------------------- standard agent setup (C5, STO-1)
@description('ENX internal gateway MCP endpoint (finding C10: the MCP tool authenticates through the conn-enx-gateway project connection instead of run-time bearer headers — integrations/mcp/enx-gateway.json)')
param enxGatewayMcpUrl string = 'https://{enx-gateway-host}/mcp'

@description('Deploy the Foundry project connections (integrations/connections/connections.bicep). SECOND PASS ONLY: the keyed connections read their credentials from {baseName}-kv with keyVault.getSecret(), so the vault and the secrets of setup/SECRETS.md must already exist (bootstrap step 4). Pass 1 creates the vault with this false; the owner then loads the secrets and redeploys with it true — the same two-pass shape as cmkKeyUri (finding C22)')
param deployConnections bool = false

@description('Name of the project connection of category CognitiveSearch created with enableKnowledgeSearch. MUST equal SEARCH_CONNECTION_NAME in setup/.env — scripts/apply_advisory_profile.py and scripts/create_orchestrator.py resolve it by name')
param searchConnectionName string = 'ai-search'

@description('Provision Azure AI Search for the durable memory index MEMORY_INDEX_NAME and a future Foundry IQ knowledge base when the standard agent setup is NOT used (delta D-ML-4 / finding C3). With enableStandardAgentSetup = true the search service comes from agent-stores.bicep instead and this flag must stay false')
param enableKnowledgeSearch bool = false

@description('Standard agent setup: provision BYO Cosmos DB (conversations) + Azure AI Search (vector stores / knowledge base) and reuse {baseName}sa for files, bound to the project by an IMMUTABLE capability host (agent-stores.bicep). DECIDE BEFORE THE FIRST AGENT IS CREATED — changing it afterwards means recreating the project. false = basic setup (Microsoft-managed multitenant stores, still in-region)')
param enableStandardAgentSetup bool = false

@description('Cosmos DB total throughput limit in RU/s for the conversation store (>= 3000 for the three system containers)')
@minValue(3000)
param cosmosThroughputLimitRuPerSecond int = 4000

@description('Conversation / run-state retention in days, applied as the Cosmos default TTL after the capability host creates its containers (governance/THREADS_MEMORY.md)')
@minValue(1)
param conversationRetentionDays int = 90

@description('Azure AI Search SKU for the BYO vector store / knowledge base')
@allowed(['basic', 'standard'])
param searchSku string = 'standard'

// ------------------------------------------------ agent egress (C12, NET-1)
@description('Inject the Foundry account into snet-agents so AGENT TOOL EGRESS (OpenAPI, MCP, A2A, web search) leaves through the VNet the hub firewall sees. Private endpoints are inbound only. Set at ACCOUNT CREATION — it cannot be added later. Requires enablePrivateNetworking, or an explicit agentSubnetId')
param enableAgentVnetInjection bool = false

@description('Subnet id for agent egress. Empty = the snet-agents subnet created by network.bicep (requires enablePrivateNetworking). Provide an id to inject into a platform-team-owned VNet instead')
param agentSubnetId string = ''

// ----------------------------------------------------------- CMK (C22, CMK-1)
@description('Customer-managed key URI in the existing {baseName}-kv, versionless so Key Vault rotation needs no redeploy (https://{baseName}-kv.{vaultSuffix}/keys/infosec-foundry-cmk). Empty = Microsoft-managed keys. Grant `Key Vault Crypto Service Encryption User` to the Foundry, storage, Cosmos DB and AI Search identities FIRST (enterprise/landing-zone.bicep CMK-1), then redeploy this template with the value set')
param cmkKeyUri string = ''

@description('Name of the CMK key inside {baseName}-kv (must match cmkKeyUri)')
param cmkKeyName string = 'infosec-foundry-cmk'

@description('Enforce CMK on every AI Search index. Enable only after the agent-created indexes carry a key, otherwise index creation fails')
@allowed(['Unspecified', 'Enabled'])
param searchCmkEnforcement string = 'Unspecified'

// ------------------------------------------------- preventive policy (C11)
@description('Deploy the resource-group Azure Policy assignments that ENFORCE EU residency, no-local-auth, network restriction, Key Vault protection and the Global* SKU denial (enterprise/azure-policy-assignments.bicep). validate.sh is a client-side check only and cannot stop a portal change')
param enablePolicyAssignments bool = false

@description('Policy effect: Deny in prod, Audit in dev (so what-if and dev experiments are not blocked)')
@allowed(['Audit', 'Deny'])
param policyEffectMode string = 'Audit'

@description('Resource id of the custom subscription-scope definition "Foundry model deployments must not use Global SKUs" (created once by the platform team — see the CLI block in enterprise/azure-policy-assignments.bicep). Empty = that one assignment is skipped')
param denyGlobalSkuDefinitionId string = ''

// -------------------------------------------- Purview / audit wiring (C15)
@description('Resource id of the tenant Purview account that governs Foundry interactions (DSPM for AI, audit, retention, eDiscovery). Recorded in the outputs as the evidence pointer; DSPM itself is enabled in the Purview portal by {group:purview-admins}, and every caller must pass user context (x-ms-user-*) so interactions are attributable')
param purviewAccountId string = ''

// --------------------------------------- Defender for Cloud AI alerts (C17)
@description('Route Defender for Cloud AI threat-protection alerts (jailbreak, sensitive-data exposure, wallet abuse) to the SOC through an activity-log alert on the action group. The subscription-level Defender for AI plan itself is enabled by defender-ai.bicep')
param enableDefenderAiAlerts bool = true

@description('SOC mailbox for High-severity Defender for AI alerts ({placeholder}); owner takes Medium and below')
param socEmail string = '{soc-mailbox}'

// -------------------------------------------------- Entra Agent ID (C7, ID-2)
@description('Object (principal) ids of the Entra Agent ID identities — the project shared agent identity and each PUBLISHED agent, which gets its OWN identity. They are inventoried in team/ACCESS_REGISTER.md and receive read-only data-plane roles here (workload-rbac.bicep). REPEAT this assignment after every publish: a republished agent is a new principal. Conditional Access on the agent blueprint is owned by {group:iam-admins}')
param agentIdentityPrincipalIds array = []

// ------------------------------------------------------------ workloads
@description('Deploy the delivery Function App plan/apps (delivery.bicep)')
param enableDelivery bool = true
@description('Container image for functions/delivery (empty = placeholder image until first push)')
param deliveryImage string = ''
@description('Container image for functions/office-tools (empty = office-tools app not deployed)')
param officeToolsImage string = ''

@description('Deploy Logic Apps Standard for workflows/ (logicapp.bicep)')
param enableLogicApps bool = true

@description('Deploy the shared MCP server on Container Apps (mcp-server.bicep)')
param enableMcpHosting bool = false
param mcpImage string = '{registry}.azurecr.io/infosec-mcp:{tag}'
param mcpEasyAuthClientId string = '{app-registration-client-id}'

@description('Deploy the optional Static Web App for rendered HTML dashboards (static-web-app.bicep). Default: SharePoint download-only HTML')
param enableStaticWebApp bool = false

@description('Deploy alert rules + action group (monitoring.bicep)')
param enableMonitoring bool = true
param ownerEmail string = '{owner-mailbox}'
param alertWebhookUrl string = ''

@description('Deploy the resource-group budget (cost.bicep)')
param enableBudget bool = true
param monthlyBudget int = 1500
@description('Budget start date, first day of a month (yyyy-MM-01)')
param budgetStartDate string = '{yyyy-MM-01}'

// ------------------------------------------------------------ team RBAC
@description('Deploy the team RBAC module (team/rbac.bicep) — requires the group object ids below')
param deployTeamRbac bool = false
param usersGroupObjectId string = '{objectId:sg-infosec-foundry-users}'
param ownerGroupObjectId string = '{objectId:sg-infosec-foundry-owner}'
param readersGroupObjectId string = ''
param pimGroupObjectId string = ''
param breakglassGroupObjectId string = ''
param deployerPrincipalId string = ''
param deployServicePrincipalAppId string = '{deploy-service-principal-appid}'

// SharePoint identifiers passed to the delivery Function (setup/.env)
param sharepointSiteId string = '{sharepoint-site-id}'
param sharepointReportsDriveId string = '{sharepoint-reports-drive-id}'

// --------------------------------------------------------------- guards
// Fails validation/what-if (not only the build) when public access is
// disabled without private endpoints — the platform would be unreachable.
var publicAccessCheck = (publicNetworkAccess == 'Enabled' || enablePrivateNetworking) ? 'ok' : 'ERROR publicNetworkAccess=Disabled requires enablePrivateNetworking=true'
// C12: injection needs a subnet — either the one network.bicep creates or an explicit id.
var agentEgressCheck = (!enableAgentVnetInjection || enablePrivateNetworking || !empty(agentSubnetId)) ? 'ok' : 'ERROR enableAgentVnetInjection=true requires enablePrivateNetworking=true or an explicit agentSubnetId'
// C22: a key URI without a key name (or the reverse) silently falls back to platform keys.
var cmkCheck = (empty(cmkKeyUri) || !empty(cmkKeyName)) ? 'ok' : 'ERROR cmkKeyUri set without cmkKeyName'
module guard 'guard.bicep' = {
  name: 'guard'
  params: {
    publicAccessCheck: any(publicAccessCheck)
    agentEgressCheck: any(agentEgressCheck)
    cmkCheck: any(cmkCheck)
  }
}

var roles = {
  keyVaultSecretsUser: '4633458b-17de-408a-b874-0445c86b69e6'
  monitoringMetricsPublisher: '3913510d-42f4-4e42-8a64-420c390055eb'
  // Search Index Data Contributor — the project MI writes/reads the durable
  // memory and knowledge indexes (delta D-ML-4 / finding C3)
  searchIndexDataContributor: '8ebe5a00-799e-43f5-93ac-243d3dce84a7'
}
func roleId(id string) string => subscriptionResourceId('Microsoft.Authorization/roleDefinitions', id)

// ---------------------------------------------------------------- network
module network 'network.bicep' = if (enablePrivateNetworking) {
  name: 'network'
  params: { baseName: baseName, location: location }
}
var peSubnetId = enablePrivateNetworking ? network!.outputs.privateEndpointSubnetId : ''
var appsSubnetId = enablePrivateNetworking ? network!.outputs.appsSubnetId : ''
// C12 — agent tool egress subnet (delegated Microsoft.App/environments).
var effectiveAgentSubnetId = !empty(agentSubnetId) ? agentSubnetId : (enablePrivateNetworking ? network!.outputs.agentSubnetId : '')
var injectAgentVnet = enableAgentVnetInjection && !empty(effectiveAgentSubnetId)

// ---------------------------------------------------------------- Foundry
resource foundry 'Microsoft.CognitiveServices/accounts@2025-06-01' = {
  name: '${baseName}-aif'
  location: location
  kind: 'AIServices'
  sku: { name: 'S0' }
  identity: { type: 'SystemAssigned' }
  properties: {
    // Foundry account: project management enabled distinguishes it from a
    // plain multi-service Cognitive Services account.
    allowProjectManagement: true
    customSubDomainName: toLower('${baseName}-aif')
    publicNetworkAccess: publicNetworkAccess
    networkAcls: { defaultAction: publicNetworkAccess == 'Disabled' ? 'Deny' : 'Allow' }
    disableLocalAuth: true          // Entra ID only; scripts use DefaultAzureCredential
    // C12 / NET-1 — BYO VNet injection for AGENT TOOL EGRESS. Set at creation
    // only: an existing account cannot be injected, and the account and the
    // VNet must share the region. `useMicrosoftManagedNetwork: false` is what
    // makes the egress traverse snet-agents instead of the platform network.
    networkInjections: injectAgentVnet ? [
      { scenario: 'agent', subnetArmId: effectiveAgentSubnetId, useMicrosoftManagedNetwork: false }
    ] : null
    // C22 / CMK-1 — customer-managed key from the existing {baseName}-kv. The
    // account identity needs `Key Vault Crypto Service Encryption User` on the
    // vault BEFORE this is set (enterprise/landing-zone.bicep grants it), so
    // prod runs main.bicep once without cmkKeyUri, then again with it.
    encryption: empty(cmkKeyUri) ? null : {
      keySource: 'Microsoft.KeyVault'
      keyVaultProperties: {
        keyName: cmkKeyName
        keyVaultUri: substring(cmkKeyUri, 0, indexOf(cmkKeyUri, '/keys/') + 1)
      }
    }
  }
}

resource project 'Microsoft.CognitiveServices/accounts/projects@2025-06-01' = {
  parent: foundry
  name: '${baseName}-proj'
  location: location
  identity: { type: 'SystemAssigned' }
  properties: {
    displayName: 'InfoSec Assurance GRC-TPRM'
    description: 'Agents converted from the Claude account export (claude-account-export/)'
  }
}

// Custom content-filter policy (DATA_PROTECTION §3 "Content safety"): the
// security vocabulary of GRC work (vulnerabilities, exploits, attack paths) is
// ANNOTATED, not blocked, on both prompt and completion; jailbreak and
// protected-material filters stay blocking.
var annotateOnly = [for c in ['Hate', 'Sexual', 'Violence', 'Selfharm']: [
  { name: c, severityThreshold: 'High', blocking: false, enabled: true, source: 'Prompt' }
  { name: c, severityThreshold: 'High', blocking: false, enabled: true, source: 'Completion' }
]]
resource raiPolicy 'Microsoft.CognitiveServices/accounts/raiPolicies@2025-06-01' = {
  parent: foundry
  name: 'infosec-security-analysis'
  properties: {
    mode: 'Default'
    basePolicyName: 'Microsoft.DefaultV2'
    contentFilters: concat(flatten(annotateOnly), [
      { name: 'Jailbreak', blocking: true, enabled: true, source: 'Prompt' }
      { name: 'Protected Material Text', blocking: true, enabled: true, source: 'Completion' }
      { name: 'Protected Material Code', blocking: false, enabled: true, source: 'Completion' }
    ])
  }
}

resource modelDeployment 'Microsoft.CognitiveServices/accounts/deployments@2025-06-01' = {
  parent: foundry
  name: modelName
  sku: { name: deploymentSku, capacity: modelCapacity }
  properties: {
    model: {
      format: chatModelFormat
      name: modelName
      version: empty(modelVersion) ? null : modelVersion
    }
    versionUpgradeOption: modelVersionUpgradeOption   // C6: pin, never drift
    raiPolicyName: raiPolicy.name
  }
}

resource reasoningDeployment 'Microsoft.CognitiveServices/accounts/deployments@2025-06-01' = {
  parent: foundry
  name: reasoningModelName
  dependsOn: [modelDeployment] // deployments must be created serially
  sku: { name: deploymentSku, capacity: reasoningModelCapacity }
  properties: {
    model: {
      format: reasoningModelFormat
      name: reasoningModelName
      version: empty(reasoningModelVersion) ? null : reasoningModelVersion
    }
    versionUpgradeOption: modelVersionUpgradeOption   // C6
    raiPolicyName: raiPolicy.name
  }
}

resource lightDeployment 'Microsoft.CognitiveServices/accounts/deployments@2025-06-01' = {
  parent: foundry
  name: lightModelName
  dependsOn: [reasoningDeployment]
  sku: { name: deploymentSku, capacity: lightModelCapacity }
  properties: {
    model: {
      format: lightModelFormat
      name: lightModelName
      version: empty(lightModelVersion) ? null : lightModelVersion
    }
    versionUpgradeOption: modelVersionUpgradeOption   // C6
    raiPolicyName: raiPolicy.name
  }
}

// ------------------------------------------ web search (Bing grounding)
// Bing Grounding is a GLOBAL service: the sanitised public query (never
// Euronext data — DATA_PROTECTION §1) leaves the EU boundary. Accepted
// residual risk, owner: platform owner (README §Residency).
#disable-next-line no-hardcoded-location
var bingLocation = 'global'
resource bing 'Microsoft.Bing/accounts@2020-06-10' = if (enableWebSearch) {
  name: '${baseName}-bing'
  location: bingLocation
  kind: 'Bing.Grounding'
  sku: { name: 'G1' }
}

resource bingConnection 'Microsoft.CognitiveServices/accounts/connections@2025-06-01' = if (enableWebSearch) {
  parent: foundry
  name: 'bing-grounding'
  properties: {
    category: 'GroundingWithBingSearch'
    target: 'https://api.bing.microsoft.com/'
    authType: 'ApiKey'
    isSharedToAll: true
    credentials: { key: enableWebSearch ? bing!.listKeys().key1 : '' }
    metadata: { ApiType: 'Azure', ResourceId: enableWebSearch ? bing!.id : '' }
  }
}

// ---------------------------------------- observability (traces/metrics)
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: '${baseName}-logs'
  location: location
  properties: {
    sku: { name: 'PerGB2018' }
    retentionInDays: logRetentionDays // DORA Art. 28 evidence: ≥ 1 year
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: '${baseName}-appi'
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
    RetentionInDays: logRetentionDays
  }
}

resource appInsightsConnection 'Microsoft.CognitiveServices/accounts/connections@2025-06-01' = {
  parent: foundry
  name: 'app-insights'
  properties: {
    category: 'AppInsights'
    target: appInsights.id
    authType: 'ApiKey'
    isSharedToAll: true
    credentials: { key: appInsights.properties.ConnectionString }
    metadata: { ApiType: 'Azure', ResourceId: appInsights.id }
  }
}

// Foundry audit + request/response + trace logs → Log Analytics (DATA_PROTECTION §4)
resource foundryDiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: 'to-log-analytics'
  scope: foundry
  properties: {
    workspaceId: logAnalytics.id
    logs: [{ categoryGroup: 'audit', enabled: true }, { categoryGroup: 'allLogs', enabled: true }]
    metrics: [{ category: 'AllMetrics', enabled: true }]
  }
}

// C15 / PUR-1 + LOG-1 — project-scope diagnostics. Foundry interactions are
// also governed in Purview (DSPM for AI, audit, retention, eDiscovery, Insider
// Risk "Risky AI usage"): Purview is enabled tenant-side by
// {group:purview-admins}; the platform side of the contract is (a) these logs
// and (b) every caller passing user context so an interaction is attributable
// to one of the five named users (see governance/DATA_PROTECTION_GUARDRAILS.md).
resource projectDiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: 'to-log-analytics'
  scope: project
  properties: {
    workspaceId: logAnalytics.id
    logs: [{ categoryGroup: 'audit', enabled: true }, { categoryGroup: 'allLogs', enabled: true }]
    metrics: [{ category: 'AllMetrics', enabled: true }]
  }
}

resource projectMetricsPublisher 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(appInsights.id, project.id, 'project-mi', roles.monitoringMetricsPublisher)
  scope: appInsights
  properties: { principalId: project.identity.principalId, principalType: 'ServicePrincipal', roleDefinitionId: roleId(roles.monitoringMetricsPublisher) }
}

// ------------------------------------------------------------- Key Vault
// Secrets live here only (setup/SECRETS.md names them); workflows and apps
// bind them by reference; RBAC authorisation; purge protection for evidence.
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: '${baseName}-kv'
  location: location
  properties: {
    tenantId: subscription().tenantId
    sku: { family: 'A', name: 'standard' }
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 90
    enablePurgeProtection: true
    publicNetworkAccess: publicNetworkAccess
    networkAcls: { defaultAction: publicNetworkAccess == 'Disabled' ? 'Deny' : 'Allow', bypass: 'AzureServices' }
  }
}

resource foundryKvUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, foundry.id, 'account-mi', roles.keyVaultSecretsUser)
  scope: keyVault
  properties: { principalId: foundry.identity.principalId, principalType: 'ServicePrincipal', roleDefinitionId: roleId(roles.keyVaultSecretsUser) }
}

resource keyVaultDiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: 'to-log-analytics'
  scope: keyVault
  properties: {
    workspaceId: logAnalytics.id
    logs: [{ categoryGroup: 'audit', enabled: true }]
    metrics: [{ category: 'AllMetrics', enabled: true }]
  }
}

// ------------------------------------------------- deliverables storage
// Role of the `deliverables` container: approval evidence + report archive
// (the byte-identical copy of every report uploaded to SharePoint) and
// vector-store backups written by scripts/memory_store.py — README §Storage.
resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: toLower(replace('${baseName}sa', '-', ''))
  location: location
  kind: 'StorageV2'
  sku: { name: storageSku }
  // System-assigned identity: required to wrap with the CMK (C22) and read by
  // enterprise/landing-zone.bicep when it grants the encryption-user role.
  identity: { type: 'SystemAssigned' }
  properties: {
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
    allowSharedKeyAccess: false // identity-based access only
    supportsHttpsTrafficOnly: true
    publicNetworkAccess: publicNetworkAccess
    networkAcls: { defaultAction: publicNetworkAccess == 'Disabled' ? 'Deny' : 'Allow', bypass: 'AzureServices' }
    // C22 — CMK for the deliverables/evidence archive and the agent file store.
    // The storage system-assigned identity (declared above) is the one that
    // wraps with the key; no `identity` block is needed for that case.
    encryption: empty(cmkKeyUri) ? null : {
      keySource: 'Microsoft.Keyvault'
      keyvaultproperties: {
        keyname: cmkKeyName
        keyvaulturi: substring(cmkKeyUri, 0, indexOf(cmkKeyUri, '/keys/') + 1)
      }
      services: {
        blob: { enabled: true, keyType: 'Account' }
        file: { enabled: true, keyType: 'Account' }
      }
    }
  }
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  parent: storage
  name: 'default'
  properties: {
    deleteRetentionPolicy: { enabled: true, days: 90 }
    containerDeleteRetentionPolicy: { enabled: true, days: 90 }
    isVersioningEnabled: true
    changeFeed: { enabled: true }
  }
}

resource deliverables 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  parent: blobService
  name: 'deliverables'
}

resource storageDiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: 'to-log-analytics'
  scope: blobService
  properties: {
    workspaceId: logAnalytics.id
    logs: [{ category: 'StorageWrite', enabled: true }, { category: 'StorageDelete', enabled: true }]
  }
}

// ------------------------------------------ Document Intelligence (OCR)
// Replaces the pytesseract OCR of the claude.ai sandbox for scanned evidence.
// Reached ONLY by the delivery Function (/api/extract_pdf) with managed
// identity — never attached to agents as an OpenAPI tool, so the
// "strip every non-GET" rule of attach_integrations.py needs no exception.
resource docIntel 'Microsoft.CognitiveServices/accounts@2025-06-01' = if (enableDocumentIntelligence) {
  name: '${baseName}-docintel'
  location: location
  kind: 'FormRecognizer'
  sku: { name: 'S0' }
  identity: { type: 'SystemAssigned' }
  properties: {
    customSubDomainName: toLower('${baseName}-docintel')
    publicNetworkAccess: publicNetworkAccess
    networkAcls: { defaultAction: publicNetworkAccess == 'Disabled' ? 'Deny' : 'Allow' }
    disableLocalAuth: true
  }
}

resource speech 'Microsoft.CognitiveServices/accounts@2025-06-01' = if (enableSpeech) {
  name: '${baseName}-speech'
  location: location
  kind: 'SpeechServices'
  sku: { name: 'S0' }
  identity: { type: 'SystemAssigned' }
  properties: {
    customSubDomainName: toLower('${baseName}-speech')
    publicNetworkAccess: publicNetworkAccess
    networkAcls: { defaultAction: publicNetworkAccess == 'Disabled' ? 'Deny' : 'Allow' }
    disableLocalAuth: true
  }
}

// ------------------------------------------------------------ workloads
var projectEndpoint = 'https://${foundry.properties.customSubDomainName}.services.ai.azure.com/api/projects/${project.name}'

// ------------------------------------------- standard agent setup (C5, STO-1)
// Conversations, uploaded files and vector stores in the customer subscription
// instead of Microsoft-managed multitenant storage. The capability host this
// module creates is IMMUTABLE once the first agent exists — deploy it in the
// SAME run that creates the project, before scripts/deploy.sh.
module agentStores 'agent-stores.bicep' = if (enableStandardAgentSetup) {
  name: 'agent-stores'
  params: {
    baseName: baseName
    location: location
    foundryAccountName: foundry.name
    projectName: project.name
    projectPrincipalId: project.identity.principalId
    storageAccountName: storage.name
    logAnalyticsId: logAnalytics.id
    publicNetworkAccess: publicNetworkAccess
    cosmosThroughputLimitRuPerSecond: cosmosThroughputLimitRuPerSecond
    conversationRetentionDays: conversationRetentionDays
    searchSku: searchSku
    cmkKeyUri: cmkKeyUri
    searchCmkEnforcement: searchCmkEnforcement
  }
}

// ------------------------- knowledge search without standard agent setup
// Delta D-ML-4 / finding C3: one vector store per agent is a fixed service
// limit, so combined knowledge and durable memory move to an Azure AI Search
// index reached through the GA AI Search tool. With enableStandardAgentSetup
// the service already exists (agent-stores.bicep) and this block stays off.
resource knowledgeSearch 'Microsoft.Search/searchServices@2024-06-01-preview' = if (enableKnowledgeSearch && !enableStandardAgentSetup) {
  name: '${baseName}-search'
  location: location
  sku: { name: 'basic' }
  identity: { type: 'SystemAssigned' }
  properties: {
    replicaCount: 1
    partitionCount: 1
    disableLocalAuth: true
    publicNetworkAccess: publicNetworkAccess == 'Disabled' ? 'disabled' : 'enabled'
  }
}

resource knowledgeSearchConnection 'Microsoft.CognitiveServices/accounts/projects/connections@2025-06-01' = if (enableKnowledgeSearch && !enableStandardAgentSetup) {
  parent: project
  // Name matches SEARCH_CONNECTION_NAME (setup/.env, default 'ai-search');
  // scripts/apply_advisory_profile.py and scripts/create_orchestrator.py
  // resolve the connection BY NAME, never by id.
  name: searchConnectionName
  properties: {
    category: 'CognitiveSearch'
    authType: 'AAD'
    isSharedToAll: true
    target: 'https://${baseName}-search.search.windows.net'
    metadata: {
      ApiType: 'Azure'
      ResourceId: enableKnowledgeSearch && !enableStandardAgentSetup ? knowledgeSearch.id : ''
      location: location
    }
  }
}

resource knowledgeSearchIndexReader 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (enableKnowledgeSearch && !enableStandardAgentSetup) {
  name: guid(resourceGroup().id, '${baseName}-search', project.id, roles.searchIndexDataContributor)
  scope: knowledgeSearch
  properties: {
    principalId: project.identity.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: roleId(roles.searchIndexDataContributor)
  }
}

// --------------------------------- Foundry project connections (conn-*, C10)
// SECOND PASS: the keyed connections read their credentials from the vault
// created above, so the secrets must exist before this module is enabled.
resource kvForConnections 'Microsoft.KeyVault/vaults@2023-07-01' existing = {
  name: '${baseName}-kv'
  dependsOn: [keyVault]
}

module projectConnections '../integrations/connections/connections.bicep' = if (deployConnections) {
  name: 'project-connections'
  params: {
    foundryAccountName: foundry.name
    projectName: last(split(project.name, '/'))
    enxGatewayMcpUrl: enxGatewayMcpUrl
    deliveryFunctionBaseUrl: 'https://${baseName}-fn-delivery.azurewebsites.net/api'
    enxGatewayToken: kvForConnections.getSecret('enx-gateway-token')
  }
}

module delivery 'delivery.bicep' = if (enableDelivery) {
  name: 'delivery'
  params: {
    baseName: baseName
    location: location
    logAnalyticsId: logAnalytics.id
    appInsightsConnectionString: appInsights.properties.ConnectionString
    projectEndpoint: projectEndpoint
    keyVaultName: keyVault.name
    documentIntelligenceEndpoint: enableDocumentIntelligence ? docIntel!.properties.endpoint : ''
    deliveryImage: deliveryImage
    officeToolsImage: officeToolsImage
    appsSubnetId: appsSubnetId
    publicNetworkAccess: publicNetworkAccess
    callerSubnetId: appsSubnetId
    sharepointSiteId: sharepointSiteId
    sharepointReportsDriveId: sharepointReportsDriveId
  }
}

module logicApps 'logicapp.bicep' = if (enableLogicApps) {
  name: 'logic-apps'
  params: {
    baseName: baseName
    location: location
    logAnalyticsId: logAnalytics.id
    appInsightsConnectionString: appInsights.properties.ConnectionString
    projectEndpoint: projectEndpoint
    keyVaultName: keyVault.name
    deliveryFunctionBaseUrl: enableDelivery ? delivery!.outputs.deliveryFunctionBaseUrl : '{delivery-function-base-url}'
    appsSubnetId: appsSubnetId
    publicNetworkAccess: publicNetworkAccess
  }
}

module mcp 'mcp-server.bicep' = if (enableMcpHosting) {
  name: 'mcp-server'
  params: {
    baseName: baseName
    location: location
    logAnalyticsId: logAnalytics.id
    projectEndpoint: projectEndpoint
    image: mcpImage
    registryLoginServer: enableDelivery ? delivery!.outputs.registryLoginServer : ''
    containerAppsSubnetId: enablePrivateNetworking ? network!.outputs.containerAppsSubnetId : ''
    easyAuthClientId: mcpEasyAuthClientId
    allowedGroupObjectId: usersGroupObjectId
  }
}

module staticWebApp 'static-web-app.bicep' = if (enableStaticWebApp) {
  name: 'static-web-app'
  params: { baseName: baseName }
}

module monitoring 'monitoring.bicep' = if (enableMonitoring) {
  name: 'monitoring'
  params: {
    baseName: baseName
    location: location
    logAnalyticsId: logAnalytics.id
    ownerEmail: ownerEmail
    webhookUrl: alertWebhookUrl
    deployServicePrincipalAppId: deployServicePrincipalAppId
    socEmail: socEmail
    enableDefenderAiAlerts: enableDefenderAiAlerts
  }
}

module budget 'cost.bicep' = if (enableBudget && enableMonitoring) {
  name: 'budget'
  params: {
    baseName: baseName
    monthlyAmount: monthlyBudget
    startDate: budgetStartDate
    actionGroupId: monitoring!.outputs.actionGroupId
    contactEmails: [ownerEmail]
  }
}

// Workload identities → data-plane roles (same guid seeds as team/rbac.bicep,
// so both modules are idempotent against each other).
module workloadRbac 'workload-rbac.bicep' = {
  name: 'workload-rbac'
  params: {
    foundryAccountName: foundry.name
    projectName: project.name
    keyVaultName: keyVault.name
    storageAccountName: storage.name
    docIntelName: enableDocumentIntelligence ? docIntel!.name : ''
    registryName: enableDelivery ? last(split(delivery!.outputs.registryId, '/')) : ''
    functionRuntimeStorageAccountName: enableDelivery ? delivery!.outputs.runtimeStorageAccountName : ''
    logicAppRuntimeStorageAccountName: enableLogicApps ? logicApps!.outputs.runtimeStorageAccountName : ''
    deliveryFunctionPrincipalId: enableDelivery ? delivery!.outputs.deliveryFunctionPrincipalId : ''
    officeToolsPrincipalId: enableDelivery ? delivery!.outputs.officeToolsPrincipalId : ''
    logicAppPrincipalId: enableLogicApps ? logicApps!.outputs.logicAppPrincipalId : ''
    mcpPrincipalId: enableMcpHosting ? mcp!.outputs.mcpPrincipalId : ''
    agentIdentityPrincipalIds: agentIdentityPrincipalIds
  }
}

// ----------------------------------------------- preventive policy (C11, POL-1)
// Deny/Audit assignments at resource-group scope: a portal or CLI change can no
// longer create a non-EU resource, a key-authenticated account or a Global* SKU
// deployment. Deployed by the workload owner; the platform team may lift the
// same assignments to the subscription or management group.
module policyAssignments '../enterprise/azure-policy-assignments.bicep' = if (enablePolicyAssignments) {
  name: 'policy-assignments'
  params: {
    effectMode: policyEffectMode
    denyGlobalSkuDefinitionId: denyGlobalSkuDefinitionId
    auditCmk: empty(cmkKeyUri)
  }
}

// ------------------------------------------------------ private endpoints
var peTargets = [
  { name: 'aif', id: foundry.id, group: 'account', zones: ['cognitiveservices', 'openai', 'aiservices'] }
  { name: 'kv', id: keyVault.id, group: 'vault', zones: ['vault'] }
  { name: 'sa-blob', id: storage.id, group: 'blob', zones: ['blob'] }
]
module privateEndpoints 'private-endpoint.bicep' = [for t in peTargets: if (enablePrivateNetworking) {
  name: 'pe-${t.name}'
  params: {
    name: '${baseName}-pe-${t.name}'
    location: location
    targetResourceId: t.id
    groupId: t.group
    subnetId: peSubnetId
    privateDnsZoneIds: [for z in t.zones: network!.outputs.zoneIds[z]]
  }
}]
// C5 / NET-2 — the BYO conversation and vector stores hold Euronext-derived
// content and must not stay reachable from the internet when public access is
// off. (enterprise/landing-zone.bicep covers the same two stores when they are
// created outside this template — set its cosmosAccountName/searchServiceName
// to empty while enableStandardAgentSetup is true here.)
module peCosmos 'private-endpoint.bicep' = if (enablePrivateNetworking && enableStandardAgentSetup) {
  name: 'pe-cosmos'
  params: {
    name: '${baseName}-pe-cosmos'
    location: location
    targetResourceId: enableStandardAgentSetup ? agentStores!.outputs.cosmosAccountId : ''
    groupId: 'Sql'
    subnetId: peSubnetId
    privateDnsZoneIds: [network!.outputs.zoneIds.documents]
  }
}
module peSearch 'private-endpoint.bicep' = if (enablePrivateNetworking && enableStandardAgentSetup) {
  name: 'pe-search'
  params: {
    name: '${baseName}-pe-search'
    location: location
    targetResourceId: enableStandardAgentSetup ? agentStores!.outputs.searchServiceId : ''
    groupId: 'searchService'
    subnetId: peSubnetId
    privateDnsZoneIds: [network!.outputs.zoneIds.search]
  }
}
module peDelivery 'private-endpoint.bicep' = if (enablePrivateNetworking && enableDelivery) {
  name: 'pe-delivery'
  params: {
    name: '${baseName}-pe-delivery'
    location: location
    targetResourceId: delivery!.outputs.deliveryFunctionId
    groupId: 'sites'
    subnetId: peSubnetId
    privateDnsZoneIds: [network!.outputs.zoneIds.sites]
  }
}
module peLogicApp 'private-endpoint.bicep' = if (enablePrivateNetworking && enableLogicApps) {
  name: 'pe-logicapp'
  params: {
    name: '${baseName}-pe-la'
    location: location
    targetResourceId: logicApps!.outputs.logicAppId
    groupId: 'sites'
    subnetId: peSubnetId
    privateDnsZoneIds: [network!.outputs.zoneIds.sites]
  }
}

// ------------------------------------------------------------ team RBAC
module teamRbac '../team/rbac.bicep' = if (deployTeamRbac) {
  name: 'team-rbac'
  params: {
    foundryAccountName: foundry.name
    projectName: project.name
    logAnalyticsName: logAnalytics.name
    appInsightsName: appInsights.name
    storageAccountName: storage.name
    keyVaultName: keyVault.name
    deliveryFunctionName: enableDelivery ? delivery!.outputs.deliveryFunctionName : ''
    logicAppName: enableLogicApps ? logicApps!.outputs.logicAppName : ''
    logicAppRuntimeStorageAccountName: enableLogicApps ? logicApps!.outputs.runtimeStorageAccountName : ''
    bingAccountName: enableWebSearch ? '${baseName}-bing' : ''
    usersGroupObjectId: usersGroupObjectId
    ownerGroupObjectId: ownerGroupObjectId
    readersGroupObjectId: readersGroupObjectId
    pimGroupObjectId: pimGroupObjectId
    breakglassGroupObjectId: breakglassGroupObjectId
    deployerPrincipalId: deployerPrincipalId
    logicAppPrincipalId: enableLogicApps ? logicApps!.outputs.logicAppPrincipalId : ''
    deliveryFunctionPrincipalId: enableDelivery ? delivery!.outputs.deliveryFunctionPrincipalId : ''
    mcpHostPrincipalId: enableMcpHosting ? mcp!.outputs.mcpPrincipalId : ''
  }
}

// ---------------------------------------------------------------- outputs
output projectEndpoint string = projectEndpoint
output foundryAccountName string = foundry.name
output projectName string = project.name
output modelDeploymentName string = modelDeployment.name
output reasoningModelDeploymentName string = reasoningDeployment.name
output lightModelDeploymentName string = lightDeployment.name
output bingConnectionName string = enableWebSearch ? 'bing-grounding' : ''
output storageAccountName string = storage.name
output keyVaultName string = keyVault.name
output logAnalyticsName string = logAnalytics.name
output appInsightsName string = appInsights.name
output docIntelEndpoint string = enableDocumentIntelligence ? docIntel!.properties.endpoint : ''
output deliveryFunctionApp string = enableDelivery ? delivery!.outputs.deliveryFunctionName : ''
output deliveryFunctionBaseUrl string = enableDelivery ? delivery!.outputs.deliveryFunctionBaseUrl : ''
output registryLoginServer string = enableDelivery ? delivery!.outputs.registryLoginServer : ''
output logicAppName string = enableLogicApps ? logicApps!.outputs.logicAppName : ''
output mcpFqdn string = enableMcpHosting ? mcp!.outputs.mcpFqdn : ''
output staticWebAppHostname string = enableStaticWebApp ? staticWebApp!.outputs.defaultHostname : ''
output environmentName string = environmentName
output cosmosAccountName string = enableStandardAgentSetup ? agentStores!.outputs.cosmosAccountName : ''
output searchServiceName string = enableStandardAgentSetup ? agentStores!.outputs.searchServiceName : ''
output agentStoreConnections object = enableStandardAgentSetup ? agentStores!.outputs.connectionNames : {}
output agentEgressSubnetId string = injectAgentVnet ? effectiveAgentSubnetId : ''
output socActionGroupId string = enableMonitoring ? monitoring!.outputs.socActionGroupId : ''
output policyAssignmentNames array = enablePolicyAssignments ? policyAssignments!.outputs.assignmentNames : []
output dataResidency object = {
  region: location
  modelDeploymentSku: deploymentSku
  modelVersionUpgradeOption: modelVersionUpgradeOption
  publicNetworkAccess: publicNetworkAccess
  privateNetworking: enablePrivateNetworking
  // C5 — where conversations, uploaded files and vector stores actually live.
  agentStateCustody: enableStandardAgentSetup ? 'standard agent setup — customer subscription (cosmos/search/storage, ${location})' : 'basic agent setup — Microsoft-managed, in-region'
  // C12 — agent tool egress path.
  agentEgress: injectAgentVnet ? 'VNet-injected (snet-agents → hub firewall)' : 'platform-managed egress (dev only)'
  // C22 — encryption at rest.
  customerManagedKey: empty(cmkKeyUri) ? 'Microsoft-managed keys' : 'CMK ${cmkKeyName} in ${baseName}-kv'
  // C11 — preventive enforcement, not only the validate.sh client-side check.
  preventivePolicy: enablePolicyAssignments ? policyEffectMode : 'none (validate.sh only)'
  // C15 — Purview governance pointer (DSPM for AI, audit, retention, eDiscovery).
  purviewAccountId: purviewAccountId
  outsideEuBoundary: enableWebSearch ? ['bing-grounding / web search — leaves the Azure compliance boundary, the DPA does not apply; sanitised public queries only, accepted residual risk (owner: platform owner)'] : []
}
