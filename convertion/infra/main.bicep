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
// deployments use the EU Data Zone SKU, so prompts/completions, threads, files
// and vector stores are processed inside the EU. The only components outside
// the EU boundary are Bing grounding (sanitised public queries only) and, by
// design, nothing else — see README.md §Residency for the per-component table.

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

@description('Environment profile: prod enforces private networking and Disabled public access (main.parameters.prod.json)')
@allowed(['dev', 'prod'])
param environmentName string = 'dev'

// ------------------------------------------------------------ model tiers
@description('Chat-tier model (registry model_tier "chat")')
param modelName string = 'gpt-4o'
@description('Chat model version (empty = provider default)')
param modelVersion string = '2024-11-20'
@description('Chat-tier capacity (thousands of tokens-per-minute)')
param modelCapacity int = 50

@description('Reasoning-tier model for analytic agents (regulatory interpretation, OSINT synthesis)')
param reasoningModelName string = 'o3-mini'
@description('Reasoning model version (empty = provider default)')
param reasoningModelVersion string = ''
@description('Reasoning-tier capacity (thousands of tokens-per-minute)')
param reasoningModelCapacity int = 30

@description('Light-tier model (deterministic template/schema transformations: docx, pdf, pptx, xlsx agents)')
param lightModelName string = 'gpt-4o-mini'
@description('Light model version (empty = provider default)')
param lightModelVersion string = ''
@description('Light-tier capacity (thousands of tokens-per-minute)')
param lightModelCapacity int = 100

@description('Model publisher format per tier. OpenAI = Azure OpenAI models; Anthropic = Claude models from the Foundry catalog (Haiku→light, Sonnet→chat, Opus→reasoning) where offered in the EU Data Zone — verify with `az cognitiveservices model list -l <location>` before switching (README §Claude tiers)')
@allowed(['OpenAI', 'Anthropic'])
param chatModelFormat string = 'OpenAI'
@allowed(['OpenAI', 'Anthropic'])
param reasoningModelFormat string = 'OpenAI'
@allowed(['OpenAI', 'Anthropic'])
param lightModelFormat string = 'OpenAI'

@description('Deployment SKU: DataZoneStandard keeps inference inside the EU data zone (residency); Standard = single-region; GlobalStandard is NOT allowed (routes worldwide)')
@allowed(['DataZoneStandard', 'Standard'])
param deploymentSku string = 'DataZoneStandard'

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
module guard 'guard.bicep' = {
  name: 'guard'
  params: { publicAccessCheck: any(publicAccessCheck) }
}

var roles = {
  keyVaultSecretsUser: '4633458b-17de-408a-b874-0445c86b69e6'
  monitoringMetricsPublisher: '3913510d-42f4-4e42-8a64-420c390055eb'
}
func roleId(id string) string => subscriptionResourceId('Microsoft.Authorization/roleDefinitions', id)

// ---------------------------------------------------------------- network
module network 'network.bicep' = if (enablePrivateNetworking) {
  name: 'network'
  params: { baseName: baseName, location: location }
}
var peSubnetId = enablePrivateNetworking ? network!.outputs.privateEndpointSubnetId : ''
var appsSubnetId = enablePrivateNetworking ? network!.outputs.appsSubnetId : ''

// ---------------------------------------------------------------- Foundry
resource foundry 'Microsoft.CognitiveServices/accounts@2025-04-01-preview' = {
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
  }
}

resource project 'Microsoft.CognitiveServices/accounts/projects@2025-04-01-preview' = {
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
resource raiPolicy 'Microsoft.CognitiveServices/accounts/raiPolicies@2025-04-01-preview' = {
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

resource modelDeployment 'Microsoft.CognitiveServices/accounts/deployments@2025-04-01-preview' = {
  parent: foundry
  name: modelName
  sku: { name: deploymentSku, capacity: modelCapacity }
  properties: {
    model: {
      format: chatModelFormat
      name: modelName
      version: empty(modelVersion) ? null : modelVersion
    }
    raiPolicyName: raiPolicy.name
  }
}

resource reasoningDeployment 'Microsoft.CognitiveServices/accounts/deployments@2025-04-01-preview' = {
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
    raiPolicyName: raiPolicy.name
  }
}

resource lightDeployment 'Microsoft.CognitiveServices/accounts/deployments@2025-04-01-preview' = {
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

resource bingConnection 'Microsoft.CognitiveServices/accounts/connections@2025-04-01-preview' = if (enableWebSearch) {
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

resource appInsightsConnection 'Microsoft.CognitiveServices/accounts/connections@2025-04-01-preview' = {
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
  properties: {
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
    allowSharedKeyAccess: false // identity-based access only
    supportsHttpsTrafficOnly: true
    publicNetworkAccess: publicNetworkAccess
    networkAcls: { defaultAction: publicNetworkAccess == 'Disabled' ? 'Deny' : 'Allow', bypass: 'AzureServices' }
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
resource docIntel 'Microsoft.CognitiveServices/accounts@2025-04-01-preview' = if (enableDocumentIntelligence) {
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

resource speech 'Microsoft.CognitiveServices/accounts@2025-04-01-preview' = if (enableSpeech) {
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
output dataResidency object = {
  region: location
  modelDeploymentSku: deploymentSku
  publicNetworkAccess: publicNetworkAccess
  privateNetworking: enablePrivateNetworking
  outsideEuBoundary: enableWebSearch ? ['bing-grounding (sanitised public queries only)'] : []
}
