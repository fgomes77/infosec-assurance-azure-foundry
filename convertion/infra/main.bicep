// Azure AI Foundry environment for the InfoSec Assurance agent toolset.
// Provisions: Foundry account (AIServices) + project + model deployment
// + storage account for generated deliverables.
// Deploy at resource-group scope (see setup/provision.sh).

@description('Base name for all resources (letters/digits, 3-15 chars)')
@minLength(3)
@maxLength(15)
param baseName string = 'infosecfoundry'

@description('Azure region (must offer Azure AI Foundry and the chosen model)')
param location string = resourceGroup().location

@description('Chat model to deploy from the Foundry catalog')
param modelName string = 'gpt-4o'

@description('Model version (empty = provider default)')
param modelVersion string = '2024-11-20'

@description('Model deployment capacity (thousands of tokens-per-minute)')
param modelCapacity int = 50

@description('Reasoning model for analytic agents (regulatory interpretation, OSINT synthesis)')
param reasoningModelName string = 'o3-mini'

@description('Reasoning model version (empty = provider default)')
param reasoningModelVersion string = ''

@description('Provision Grounding with Bing Search for agent web research')
param enableWebSearch bool = true

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
    publicNetworkAccess: 'Enabled' // harden to 'Disabled' + private endpoints for production
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

resource modelDeployment 'Microsoft.CognitiveServices/accounts/deployments@2025-04-01-preview' = {
  parent: foundry
  name: modelName
  sku: { name: 'GlobalStandard', capacity: modelCapacity }
  properties: {
    model: {
      format: 'OpenAI'
      name: modelName
      version: empty(modelVersion) ? null : modelVersion
    }
  }
}

resource reasoningDeployment 'Microsoft.CognitiveServices/accounts/deployments@2025-04-01-preview' = {
  parent: foundry
  name: reasoningModelName
  dependsOn: [modelDeployment] // deployments must be created serially
  sku: { name: 'GlobalStandard', capacity: modelCapacity }
  properties: {
    model: {
      format: 'OpenAI'
      name: reasoningModelName
      version: empty(reasoningModelVersion) ? null : reasoningModelVersion
    }
  }
}

// ------------------------------------------ web search (Bing grounding)
resource bing 'Microsoft.Bing/accounts@2020-06-10' = if (enableWebSearch) {
  name: '${baseName}-bing'
  location: 'global'
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
    retentionInDays: 90 // align to ISMS log-retention policy
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: '${baseName}-appi'
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
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

// ------------------------------------------------- deliverables storage
resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: toLower(replace('${baseName}sa', '-', ''))
  location: location
  kind: 'StorageV2'
  sku: { name: 'Standard_LRS' }
  properties: {
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
    supportsHttpsTrafficOnly: true
  }
}

resource deliverables 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  name: '${storage.name}/default/deliverables'
}

// ---------------------------------------------------------------- outputs
output projectEndpoint string = 'https://${foundry.properties.customSubDomainName}.services.ai.azure.com/api/projects/${project.name}'
output foundryAccountName string = foundry.name
output projectName string = project.name
output modelDeploymentName string = modelDeployment.name
output reasoningModelDeploymentName string = reasoningDeployment.name
output bingConnectionName string = enableWebSearch ? 'bing-grounding' : ''
output storageAccountName string = storage.name
