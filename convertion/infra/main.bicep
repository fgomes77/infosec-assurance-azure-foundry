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
output storageAccountName string = storage.name
