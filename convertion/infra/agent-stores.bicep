// BYO agent state stores for the Foundry Agent Service — "standard agent
// setup" (finding C5, ENTERPRISE_BLUEPRINT.md decision STO-1).
//
// DECISION, AND WHEN IT IS TAKEN
// ------------------------------------------------------------------------
// The capability host that binds a project to customer-owned stores is
// IMMUTABLE: it is created with the project and cannot be added, removed or
// repointed once the FIRST AGENT EXISTS. The choice between
//   * basic setup   — conversations, uploaded files and vector stores live in
//                     Microsoft-managed multitenant storage, in-region; and
//   * standard setup — the same data lives in THIS subscription, in
//                     {baseName}-cosmos (conversations + agent definitions),
//                     {baseName}-search (vector stores / knowledge base) and
//                     {baseName}sa (files),
// must therefore be made BEFORE `deploy.sh` creates the first agent. The ENX
// ISMS requires customer custody of Euronext-derived assessment content, so
// `enableStandardAgentSetup = true` is the prod default; flipping it later
// means recreating the project and re-uploading every vector store.
// Sources: standard agent setup (GA, 2026-07-09), capability hosts
// (2026-08-21), foundry-samples 43-standard-agent-setup-with-customization.
//
// Residency: all three stores are created in `location` (EU allow-list of
// main.bicep), Entra-only (no keys/local auth), and — with CMK params — are
// encrypted with the key in the existing {baseName}-kv (finding C22).
// Retention: conversation/run state is kept for `conversationRetentionDays`
// (THREADS_MEMORY.md 90 d) through the Cosmos default TTL; the Agent Service
// creates the databases/containers itself at capability-host creation, so the
// TTL is applied to `run-state-v1` afterwards (see the CLI note at the end).

@description('main.bicep baseName')
@minLength(3)
@maxLength(15)
param baseName string

@description('EU region (validated by main.bicep @allowed + validate.sh)')
param location string

@description('Foundry account created by main.bicep (parent of the project)')
param foundryAccountName string

@description('Foundry project created by main.bicep')
param projectName string

@description('System-assigned principal id of the project — receives the data-plane roles on the three stores')
param projectPrincipalId string

@description('Deliverables storage account created by main.bicep — reused as the agent file store (blob)')
param storageAccountName string

@description('Log Analytics workspace id for diagnostics (LOG-1 / finding C15)')
param logAnalyticsId string

@description('Public network access on the BYO stores; mirrors main.bicep publicNetworkAccess')
@allowed(['Enabled', 'Disabled'])
param publicNetworkAccess string = 'Enabled'

@description('Cosmos DB total throughput limit in RU/s. Standard agent setup needs >= 3000 RU/s for the three system containers; -1 = uncapped')
@minValue(3000)
param cosmosThroughputLimitRuPerSecond int = 4000

@description('Conversation / run-state retention in days (THREADS_MEMORY.md). Applied as the Cosmos default TTL on run-state-v1 after the capability host is created')
@minValue(1)
param conversationRetentionDays int = 90

@description('Azure AI Search SKU for vector stores / Foundry IQ knowledge base')
@allowed(['basic', 'standard'])
param searchSku string = 'standard'

@description('Customer-managed key URI (versionless, e.g. https://{baseName}-kv.vault.azure.net/keys/infosec-foundry-cmk) — empty = Microsoft-managed keys (finding C22)')
param cmkKeyUri string = ''

@description('Enforce CMK on every AI Search index. Enable only after the agent-created indexes are provisioned with a key, otherwise index creation fails')
@allowed(['Unspecified', 'Enabled'])
param searchCmkEnforcement string = 'Unspecified'

var hasCmk = !empty(cmkKeyUri)

var roles = {
  // ARM (control-plane) roles the project identity needs on the BYO stores.
  cosmosDbOperator: '230815da-be43-4aae-9cb4-875f7bd000aa'
  searchIndexDataContributor: '8ebe5a00-799e-43f5-93ac-243d3dce84a7'
  searchServiceContributor: '7ca78c08-252a-4471-8644-bb5ff32d4ba0'
  storageBlobDataContributor: 'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
}
func roleId(id string) string => subscriptionResourceId('Microsoft.Authorization/roleDefinitions', id)

resource foundry 'Microsoft.CognitiveServices/accounts@2025-06-01' existing = {
  name: foundryAccountName
}

resource project 'Microsoft.CognitiveServices/accounts/projects@2025-06-01' existing = {
  parent: foundry
  name: projectName
}

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' existing = {
  name: storageAccountName
}

// ------------------------------------------------------- conversations store
// Cosmos DB for NoSQL holds conversations (formerly threads), messages and the
// agent definitions. disableLocalAuth = Entra-only, matching the Foundry
// account. CMK note: the key must already be wrappable by the Cosmos first-
// party identity — grant `Key Vault Crypto Service Encryption User` on
// {baseName}-kv (enterprise/landing-zone.bicep CMK-1) BEFORE enabling it here.
resource cosmos 'Microsoft.DocumentDB/databaseAccounts@2024-11-15' = {
  name: '${baseName}-cosmos'
  location: location
  kind: 'GlobalDocumentDB'
  identity: { type: 'SystemAssigned' }
  properties: {
    databaseAccountOfferType: 'Standard'
    locations: [{ locationName: location, failoverPriority: 0, isZoneRedundant: false }]
    consistencyPolicy: { defaultConsistencyLevel: 'Session' }
    disableLocalAuth: true
    minimalTlsVersion: 'Tls12'
    publicNetworkAccess: publicNetworkAccess
    networkAclBypass: 'AzureServices'
    capacity: { totalThroughputLimit: cosmosThroughputLimitRuPerSecond }
    backupPolicy: { type: 'Continuous', continuousModeProperties: { tier: 'Continuous7Days' } }
    keyVaultKeyUri: hasCmk ? cmkKeyUri : null
  }
}

// Data-plane (SQL) role for the project identity — the ARM `Cosmos DB
// Operator` role does not grant document access. Scoped to the account here;
// the Agent Service narrows nothing further (it owns the system containers).
resource cosmosDataContributor 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2024-11-15' = if (!empty(projectPrincipalId)) {
  parent: cosmos
  name: guid(cosmos.id, projectPrincipalId, 'sql-data-contributor')
  properties: {
    principalId: projectPrincipalId
    roleDefinitionId: '${cosmos.id}/sqlRoleDefinitions/00000000-0000-0000-0000-000000000002'
    scope: cosmos.id
  }
}

resource cosmosOperator 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(projectPrincipalId)) {
  name: guid(cosmos.id, projectPrincipalId, roles.cosmosDbOperator)
  scope: cosmos
  properties: { principalId: projectPrincipalId, principalType: 'ServicePrincipal', roleDefinitionId: roleId(roles.cosmosDbOperator) }
}

// --------------------------------------------------- vector / knowledge store
// One vector store per agent is the Agent Service limit (finding C3), so the
// durable memory and the combined knowledge base live in this search service
// as a Foundry IQ knowledge base rather than in a second agent vector store.
resource search 'Microsoft.Search/searchServices@2024-06-01-preview' = {
  name: '${baseName}-search'
  location: location
  sku: { name: searchSku }
  identity: { type: 'SystemAssigned' }
  properties: {
    replicaCount: 1
    partitionCount: 1
    hostingMode: 'default'
    publicNetworkAccess: publicNetworkAccess == 'Disabled' ? 'disabled' : 'enabled'
    disableLocalAuth: true
    semanticSearch: 'standard'
    encryptionWithCmk: { enforcement: searchCmkEnforcement }
  }
}

resource searchIndexData 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(projectPrincipalId)) {
  name: guid(search.id, projectPrincipalId, roles.searchIndexDataContributor)
  scope: search
  properties: { principalId: projectPrincipalId, principalType: 'ServicePrincipal', roleDefinitionId: roleId(roles.searchIndexDataContributor) }
}

resource searchService 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(projectPrincipalId)) {
  name: guid(search.id, projectPrincipalId, roles.searchServiceContributor)
  scope: search
  properties: { principalId: projectPrincipalId, principalType: 'ServicePrincipal', roleDefinitionId: roleId(roles.searchServiceContributor) }
}

// ------------------------------------------------------------- file store
// Agent-uploaded files land in {baseName}sa (already hardened in main.bicep:
// no shared keys, no public blobs, versioning, 90-day soft delete).
resource storageBlobData 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(projectPrincipalId)) {
  name: guid(storage.id, projectPrincipalId, roles.storageBlobDataContributor)
  scope: storage
  properties: { principalId: projectPrincipalId, principalType: 'ServicePrincipal', roleDefinitionId: roleId(roles.storageBlobDataContributor) }
}

// ------------------------------------------------- project connections (AAD)
// The capability host references these connections BY NAME. All three use
// Entra authentication — no keys are read, stored or rotated.
resource cosmosConnection 'Microsoft.CognitiveServices/accounts/projects/connections@2025-06-01' = {
  parent: project
  name: 'agent-cosmos'
  properties: {
    category: 'CosmosDB'
    target: cosmos.properties.documentEndpoint
    authType: 'AAD'
    isSharedToAll: false
    metadata: { ApiType: 'Azure', ResourceId: cosmos.id, location: location }
  }
}

resource searchConnection 'Microsoft.CognitiveServices/accounts/projects/connections@2025-06-01' = {
  parent: project
  name: 'agent-search'
  properties: {
    category: 'CognitiveSearch'
    target: 'https://${search.name}.search.windows.net'
    authType: 'AAD'
    isSharedToAll: false
    metadata: { ApiType: 'Azure', ResourceId: search.id, location: location }
  }
}

resource storageConnection 'Microsoft.CognitiveServices/accounts/projects/connections@2025-06-01' = {
  parent: project
  name: 'agent-storage'
  properties: {
    category: 'AzureStorageAccount'
    target: storage.properties.primaryEndpoints.blob
    authType: 'AAD'
    isSharedToAll: false
    metadata: { ApiType: 'Azure', ResourceId: storage.id, location: location }
  }
}

// ---------------------------------------------------------- capability hosts
// Account host first, then the project host that names the three connections.
// IMMUTABLE after the first agent — see the decision note at the top.
resource accountCapabilityHost 'Microsoft.CognitiveServices/accounts/capabilityHosts@2025-06-01' = {
  parent: foundry
  name: '${baseName}-account-caphost'
  properties: {
    capabilityHostKind: 'Agents'
  }
}

resource projectCapabilityHost 'Microsoft.CognitiveServices/accounts/projects/capabilityHosts@2025-06-01' = {
  parent: project
  name: '${baseName}-proj-caphost'
  dependsOn: [accountCapabilityHost, cosmosDataContributor, cosmosOperator, searchIndexData, searchService, storageBlobData]
  properties: {
    // capabilityHostKind is required by the REST API; the published Bicep
    // types for the project child lag behind it.
    #disable-next-line BCP037
    capabilityHostKind: 'Agents'
    threadStorageConnections: [cosmosConnection.name]
    vectorStoreConnections: [searchConnection.name]
    storageConnections: [storageConnection.name]
  }
}

// ------------------------------------------------------------- diagnostics
// Same setting name and categories as enterprise/landing-zone.bicep LOG-1, so
// the two templates stay idempotent if both are deployed (finding C15).
resource cosmosDiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: 'to-log-analytics'
  scope: cosmos
  properties: {
    workspaceId: logAnalyticsId
    logs: [{ categoryGroup: 'audit', enabled: true }]
    metrics: [{ category: 'Requests', enabled: true }]
  }
}

resource searchDiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: 'to-log-analytics'
  scope: search
  properties: {
    workspaceId: logAnalyticsId
    logs: [{ categoryGroup: 'allLogs', enabled: true }]
    metrics: [{ category: 'AllMetrics', enabled: true }]
  }
}

output cosmosAccountName string = cosmos.name
output cosmosEndpoint string = cosmos.properties.documentEndpoint
output cosmosAccountId string = cosmos.id
output searchServiceName string = search.name
output searchServiceId string = search.id
output projectCapabilityHostName string = projectCapabilityHost.name
output connectionNames object = {
  conversations: cosmosConnection.name
  vectorStore: searchConnection.name
  files: storageConnection.name
}
output conversationRetentionDays int = conversationRetentionDays

// Post-deployment (once, after the capability host has created its containers;
// run by the owner under the change record — operations/CHANGE_MANAGEMENT.md):
//   az cosmosdb sql container update -g {rg} -a {baseName}-cosmos \
//     -d {project-workspace-id}-thread-message-store -n run-state-v1 \
//     --ttl <conversationRetentionDays * 86400>
// Verify the binding:
//   az rest --method get --url "https://management.azure.com{projectId}/capabilityHosts/{baseName}-proj-caphost?api-version=2025-06-01"
