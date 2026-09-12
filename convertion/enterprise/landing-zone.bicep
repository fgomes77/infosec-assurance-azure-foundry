// Enterprise hardening layer for the InfoSec Assurance Foundry platform —
// the pieces infra/main.bicep does NOT provision, composed as a SECOND
// resource-group deployment that runs AFTER main.bicep (same RG, same
// {baseName}). Nothing here re-declares a resource main.bicep owns; every
// existing resource is referenced by name (`existing`) so both templates
// stay independently idempotent.
//
// What it adds (ENTERPRISE_BLUEPRINT.md decision table):
//   NET-1  agents subnet `snet-agents` (/24, delegated Microsoft.App/environments)
//          for BYO-VNet agent egress — network injection is set on the project
//          at creation and cannot be changed later (shared delta D-EB3 passes the
//          subnet id to main.bicep). Source: networking-options (GA, 2026-09-09).
//   NET-2  private DNS zones + private endpoints for the BYO agent stores
//          (Cosmos DB, AI Search) and the container registry that main.bicep
//          leaves public; the zones are linked to the existing VNet.
//   LOG-1  diagnostic settings for the resources main.bicep leaves without
//          one (Document Intelligence, NSG, Cosmos DB, AI Search, registry) —
//          Foundry itself already streams audit + allLogs (main.bicep).
//   CMK-1  RSA key in the existing Key Vault + `Key Vault Crypto Service
//          Encryption User` for the Foundry account and storage identities;
//          the encryption block itself lives on the resources main.bicep
//          owns (shared delta D-EB4 adds `cmkKeyVaultUri/cmkKeyName`).
//          Source: encryption-keys-portal (GA, 2026-08-25).
//   FW-1   NSG for the agents subnet: HTTPS-only egress; FQDN filtering is
//          still the firewall/proxy's job (infra/README.md §Network).
//
// Deploy:  az deployment group create -g rg-infosec-foundry \
//            -f enterprise/landing-zone.bicep -p enterprise/landing-zone.parameters.example.json
// Validate first: bicep build + `az deployment group what-if` (never apply
// blind — the Foundry resource must sit in the same region as the VNet for
// network-secured agents; general-availability#common-rollout-pitfalls).
// Every tenant value is a {placeholder}; no secrets are accepted as params.

targetScope = 'resourceGroup'

// ------------------------------------------------------------ identity of the
// resources main.bicep created (names, not ids — the RG is shared)
@description('main.bicep baseName')
@minLength(3)
@maxLength(15)
param baseName string = 'infosecfoundry'

@description('EU region of the platform (must equal main.bicep location; validated by validate.sh)')
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

@description('Log Analytics workspace created by main.bicep')
param logAnalyticsName string = '${baseName}-logs'

@description('VNet created by infra/network.bicep (enablePrivateNetworking = true)')
param vnetName string = '${baseName}-vnet'

@description('Name of the private-endpoint subnet in that VNet')
param privateEndpointSubnetName string = 'snet-pe'

@description('Key Vault created by main.bicep (RBAC, soft delete, purge protection)')
param keyVaultName string = '${baseName}-kv'

@description('Foundry account created by main.bicep')
param foundryAccountName string = '${baseName}-aif'

@description('Deliverables storage account created by main.bicep')
param storageAccountName string = toLower(replace('${baseName}sa', '-', ''))

@description('Document Intelligence account created by main.bicep (empty = not deployed)')
param docIntelName string = '${baseName}-docintel'

// ------------------------------------------------------------ NET-1 agents subnet
@description('Create the delegated agents subnet for BYO-VNet agent egress (networking-options: /27 minimum, /24 recommended with hosted agents, RFC1918 only)')
param enableAgentSubnet bool = true

@description('Address prefix for snet-agents — must be free inside the VNet space (network.bicep uses 10.60.0.0/26, 10.60.0.64/26, 10.60.2.0/23 of 10.60.0.0/22)')
param agentSubnetAddressPrefix string = '10.60.1.0/24'

// ------------------------------------------------------------ NET-2 / LOG-1 BYO agent stores
@description('Cosmos DB for NoSQL account holding conversations + agent definitions (standard agent setup). Empty = not deployed yet')
param cosmosAccountName string = ''

@description('Azure AI Search service holding vector stores / knowledge bases (standard agent setup). Empty = not deployed yet')
param searchServiceName string = ''

@description('Container registry created by infra/delivery.bicep (empty = skip its private endpoint)')
param registryName string = ''

@description('Create private endpoints + DNS zones for the stores above (requires the VNet)')
param enablePrivateEndpoints bool = true

// ------------------------------------------------------------ CMK-1
@description('Create the customer-managed key and grant the encryption-user role to the platform identities')
param enableCmk bool = true

@description('Name of the RSA key used for CMK (versionless reference recommended for rotation without redeploy)')
param cmkKeyName string = 'infosec-foundry-cmk'

@description('Principal ids that must be able to wrap/unwrap with the CMK: Foundry account MI, storage MI, Cosmos DB / AI Search MIs once created. main.bicep outputs are not exposed for these — read them with `az resource show ... --query identity.principalId`')
param cmkPrincipalIds array = []

@description('Diagnostic categories for the Foundry account are set by main.bicep (audit + allLogs); set true only to ALSO export AzureOpenAIRequestUsage to a second, cost-attribution workspace')
param enableUsageExportWorkspace bool = false
param usageExportWorkspaceId string = ''

// --------------------------------------------------------------- existing
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' existing = {
  name: logAnalyticsName
}

resource vnet 'Microsoft.Network/virtualNetworks@2024-01-01' existing = {
  name: vnetName
}

resource peSubnet 'Microsoft.Network/virtualNetworks/subnets@2024-01-01' existing = {
  parent: vnet
  name: privateEndpointSubnetName
}

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' existing = {
  name: keyVaultName
}

resource foundry 'Microsoft.CognitiveServices/accounts@2025-06-01' existing = {
  name: foundryAccountName
}

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' existing = {
  name: storageAccountName
}

resource docIntel 'Microsoft.CognitiveServices/accounts@2025-06-01' existing = if (!empty(docIntelName)) {
  name: docIntelName
}

resource cosmos 'Microsoft.DocumentDB/databaseAccounts@2024-11-15' existing = if (!empty(cosmosAccountName)) {
  name: cosmosAccountName
}

resource search 'Microsoft.Search/searchServices@2024-06-01-preview' existing = if (!empty(searchServiceName)) {
  name: searchServiceName
}

resource registry 'Microsoft.ContainerRegistry/registries@2023-11-01-preview' existing = if (!empty(registryName)) {
  name: registryName
}

var roles = {
  // Key Vault Crypto Service Encryption User — required on the vault for every
  // identity that encrypts with the CMK (encryption-keys-portal, GA 2026-08-25).
  keyVaultCryptoServiceEncryptionUser: 'e147488a-f6f5-4113-8e2d-b22465e65bf6'
}
func roleId(id string) string => subscriptionResourceId('Microsoft.Authorization/roleDefinitions', id)

// ------------------------------------------------------------ NET-1 / FW-1
// Egress from agent tools (OpenAPI, MCP, A2A) traverses this subnet when the
// project is created with networkInjections pointing at it. Inbound from the
// internet is denied; HTTPS egress only; FQDN allow-list = firewall/proxy.
resource nsgAgents 'Microsoft.Network/networkSecurityGroups@2024-01-01' = if (enableAgentSubnet) {
  name: '${baseName}-nsg-agents'
  location: location
  properties: {
    securityRules: [
      {
        name: 'deny-inbound-internet'
        properties: { priority: 4000, direction: 'Inbound', access: 'Deny', protocol: '*', sourceAddressPrefix: 'Internet', sourcePortRange: '*', destinationAddressPrefix: '*', destinationPortRange: '*' }
      }
      {
        name: 'allow-outbound-https'
        properties: { priority: 100, direction: 'Outbound', access: 'Allow', protocol: 'Tcp', sourceAddressPrefix: '*', sourcePortRange: '*', destinationAddressPrefix: '*', destinationPortRange: '443' }
      }
      {
        name: 'deny-outbound-other-internet'
        properties: { priority: 4000, direction: 'Outbound', access: 'Deny', protocol: '*', sourceAddressPrefix: '*', sourcePortRange: '*', destinationAddressPrefix: 'Internet', destinationPortRange: '*' }
      }
    ]
  }
}

// Child-resource subnet on the VNet network.bicep owns. NOTE: a later
// redeploy of network.bicep that enumerates `subnets` would drop this subnet —
// shared delta D-EB3 adds snet-agents to network.bicep natively; until then
// re-run this template after any network.bicep change.
resource agentSubnet 'Microsoft.Network/virtualNetworks/subnets@2024-01-01' = if (enableAgentSubnet) {
  parent: vnet
  name: 'snet-agents'
  properties: {
    addressPrefix: agentSubnetAddressPrefix
    networkSecurityGroup: { id: nsgAgents.id }
    delegations: [{ name: 'agents', properties: { serviceName: 'Microsoft.App/environments' } }]
  }
}

resource nsgAgentsDiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = if (enableAgentSubnet) {
  name: 'to-log-analytics'
  scope: nsgAgents
  properties: {
    workspaceId: logAnalytics.id
    logs: [{ categoryGroup: 'allLogs', enabled: true }]
  }
}

// ------------------------------------------------------------ NET-2 zones + PEs
// Zones network.bicep does not create (it covers cognitiveservices, openai,
// services.ai, blob/queue/table, vaultcore, azurewebsites).
var extraZoneNames = [
  'privatelink.documents.azure.com'      // Cosmos DB for NoSQL
  'privatelink.search.windows.net'       // Azure AI Search
  'privatelink.azurecr.io'               // Container registry
]

#disable-next-line no-hardcoded-location   // private DNS zones are global resources
var dnsLocation = 'global'

resource extraZones 'Microsoft.Network/privateDnsZones@2024-06-01' = [for z in extraZoneNames: if (enablePrivateEndpoints) {
  name: z
  location: dnsLocation
}]

resource extraLinks 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2024-06-01' = [for (z, i) in extraZoneNames: if (enablePrivateEndpoints) {
  parent: extraZones[i]
  name: '${baseName}-link'
  location: dnsLocation
  properties: { virtualNetwork: { id: vnet.id }, registrationEnabled: false }
}]

module peCosmos '../infra/private-endpoint.bicep' = if (enablePrivateEndpoints && !empty(cosmosAccountName)) {
  name: 'pe-cosmos'
  params: {
    name: '${baseName}-pe-cosmos'
    location: location
    targetResourceId: cosmos!.id
    groupId: 'Sql'
    subnetId: peSubnet.id
    privateDnsZoneIds: [extraZones[0].id]
  }
}

module peSearch '../infra/private-endpoint.bicep' = if (enablePrivateEndpoints && !empty(searchServiceName)) {
  name: 'pe-search'
  params: {
    name: '${baseName}-pe-search'
    location: location
    targetResourceId: search!.id
    groupId: 'searchService'
    subnetId: peSubnet.id
    privateDnsZoneIds: [extraZones[1].id]
  }
}

module peRegistry '../infra/private-endpoint.bicep' = if (enablePrivateEndpoints && !empty(registryName)) {
  name: 'pe-acr'
  params: {
    name: '${baseName}-pe-acr'
    location: location
    targetResourceId: registry!.id
    groupId: 'registry'
    subnetId: peSubnet.id
    privateDnsZoneIds: [extraZones[2].id]
  }
}

// ------------------------------------------------------------ LOG-1 diagnostics
// Categories per diagnostic-logging (GA, 2026-07-13): Cognitive Services
// accounts expose Audit, RequestResponse, Trace, AzureOpenAIRequestUsage.
resource docIntelDiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = if (!empty(docIntelName)) {
  name: 'to-log-analytics'
  scope: docIntel
  properties: {
    workspaceId: logAnalytics.id
    logs: [{ categoryGroup: 'audit', enabled: true }, { categoryGroup: 'allLogs', enabled: true }]
    metrics: [{ category: 'AllMetrics', enabled: true }]
  }
}

resource cosmosDiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = if (!empty(cosmosAccountName)) {
  name: 'to-log-analytics'
  scope: cosmos
  properties: {
    workspaceId: logAnalytics.id
    logs: [{ categoryGroup: 'audit', enabled: true }]
    metrics: [{ category: 'Requests', enabled: true }]
  }
}

resource searchDiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = if (!empty(searchServiceName)) {
  name: 'to-log-analytics'
  scope: search
  properties: {
    workspaceId: logAnalytics.id
    logs: [{ categoryGroup: 'allLogs', enabled: true }]
    metrics: [{ category: 'AllMetrics', enabled: true }]
  }
}

resource registryDiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = if (!empty(registryName)) {
  name: 'to-log-analytics'
  scope: registry
  properties: {
    workspaceId: logAnalytics.id
    logs: [{ categoryGroup: 'audit', enabled: true }]
  }
}

// Optional second sink for cost attribution only (usage category, no content).
// A second diagnostic setting may not reuse the workspace main.bicep already
// targets — point it at a separate FinOps workspace.
resource foundryUsageExport 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = if (enableUsageExportWorkspace && !empty(usageExportWorkspaceId)) {
  name: 'usage-to-finops'
  scope: foundry
  properties: {
    workspaceId: usageExportWorkspaceId
    logs: [{ category: 'AzureOpenAIRequestUsage', enabled: true }]
  }
}

// ------------------------------------------------------------ CMK-1
// Same-region vault with soft delete + purge protection is already what
// main.bicep creates. RSA 2048+ key; versionless URI lets Key Vault rotation
// policies rotate without a redeploy (encryption-keys-portal).
resource cmkKey 'Microsoft.KeyVault/vaults/keys@2023-07-01' = if (enableCmk) {
  parent: keyVault
  name: cmkKeyName
  properties: {
    kty: 'RSA'
    keySize: 3072
    keyOps: ['wrapKey', 'unwrapKey']
    rotationPolicy: {
      lifetimeActions: [
        { trigger: { timeBeforeExpiry: 'P30D' }, action: { type: 'rotate' } }
        { trigger: { timeBeforeExpiry: 'P15D' }, action: { type: 'notify' } }
      ]
      attributes: { expiryTime: 'P1Y' }
    }
  }
}

// Foundry account + storage identities are known from main.bicep; extra
// principals (Cosmos DB, AI Search once created) come through cmkPrincipalIds
// (a for-loop cannot read runtime identity properties, so the two known
// principals get explicit assignments and the list covers the rest).
resource cmkFoundry 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (enableCmk) {
  name: guid(keyVault.id, foundry.id, 'cmk', roles.keyVaultCryptoServiceEncryptionUser)
  scope: keyVault
  properties: { principalId: foundry.identity.principalId, principalType: 'ServicePrincipal', roleDefinitionId: roleId(roles.keyVaultCryptoServiceEncryptionUser) }
}

resource cmkStorage 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (enableCmk) {
  name: guid(keyVault.id, storage.id, 'cmk', roles.keyVaultCryptoServiceEncryptionUser)
  scope: keyVault
  properties: { principalId: storage.identity.principalId, principalType: 'ServicePrincipal', roleDefinitionId: roleId(roles.keyVaultCryptoServiceEncryptionUser) }
}

resource cmkExtra 'Microsoft.Authorization/roleAssignments@2022-04-01' = [for p in cmkPrincipalIds: if (enableCmk) {
  name: guid(keyVault.id, p, 'cmk', roles.keyVaultCryptoServiceEncryptionUser)
  scope: keyVault
  properties: { principalId: p, principalType: 'ServicePrincipal', roleDefinitionId: roleId(roles.keyVaultCryptoServiceEncryptionUser) }
}]

// ---------------------------------------------------------------- outputs
// Feed these to main.bicep (shared deltas D-EB3 / D-EB4) — the encryption
// block and networkInjections belong on the resources main.bicep owns.
output agentSubnetId string = enableAgentSubnet ? agentSubnet.id : ''
output cmkKeyVaultUri string = enableCmk ? keyVault.properties.vaultUri : ''
output cmkKeyName string = enableCmk ? cmkKeyName : ''
output cmkKeyUriVersionless string = enableCmk ? cmkKey!.properties.keyUri : ''
output extraPrivateDnsZoneIds object = {
  documents: enablePrivateEndpoints ? extraZones[0].id : ''
  search: enablePrivateEndpoints ? extraZones[1].id : ''
  azurecr: enablePrivateEndpoints ? extraZones[2].id : ''
}
