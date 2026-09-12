// Role assignments for the InfoSec Assurance Foundry platform (team/README.md §4).
// Deploy at resource-group scope, after infra/main.bicep (or as a module from it —
// see the shared delta in team/README.md §15). Assigns roles to Entra ID GROUPS and
// MANAGED IDENTITIES only — never to individual users; standing human access is the
// minimum (Azure AI User for the team, Azure AI Developer / Project Manager for the
// owner); every privileged role is PIM-eligible via the admin-pim group and is NOT
// assigned here as a standing assignment.
//
// Built-in role definition ids: verify before first use with
//   az role definition list --query "[].{name:roleName,id:name}" -o table

@description('Foundry account name (infra/main.bicep: ${baseName}-aif)')
param foundryAccountName string

@description('Foundry project name (infra/main.bicep: ${baseName}-proj)')
param projectName string

@description('Log Analytics workspace name')
param logAnalyticsName string

@description('Application Insights component name')
param appInsightsName string

@description('Deliverables storage account name')
param storageAccountName string

@description('Key Vault name (empty = skip Key Vault assignments)')
param keyVaultName string = ''

@description('Object id of sg-infosec-foundry-users')
param usersGroupObjectId string

@description('Object id of sg-infosec-foundry-owner')
param ownerGroupObjectId string

@description('Object id of sg-infosec-foundry-readers (empty = skip)')
param readersGroupObjectId string = ''

@description('Object id of sg-infosec-foundry-admin-pim (used only for the conditioned RBAC Administrator eligibility note; PIM eligibility itself is configured in Entra PIM, not here)')
param pimGroupObjectId string = ''

@description('Principal id of the GitHub OIDC deployer service principal (empty = skip)')
param deployerPrincipalId string = ''

@description('Principal id of the Logic Apps Standard system-assigned managed identity (empty = skip)')
param logicAppPrincipalId string = ''

@description('Principal id of the delivery Function App system-assigned managed identity (empty = skip)')
param deliveryFunctionPrincipalId string = ''

@description('Optional custom role definition id for assurance users (team/custom-role.agent-consumer.json). Empty = built-in Azure AI User.')
param agentConsumerRoleDefinitionId string = ''

// ------------------------------------------------------------ built-in roles
var roles = {
  reader: 'acdd72a7-3385-48ef-bd42-f606fba81ae7'
  contributor: 'b24988ac-6180-42a0-ab88-20f7382dd24c'
  azureAiUser: '53ca6127-db72-4b80-b1b0-d745d6d5456d'
  azureAiDeveloper: '64702f94-c441-49e6-a78b-ef80e0188fee'
  azureAiProjectManager: 'eadc314b-1a2d-4efa-be10-5d325db5065e'
  monitoringReader: '43d0d8ad-25c7-4714-9337-8ba259a9fe05'
  logAnalyticsReader: '73c42c96-874c-492b-b04d-ab87d138a893'
  keyVaultSecretsUser: '4633458b-17de-408a-b874-0445c86b69e6'
  storageBlobDataContributor: 'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
}

func roleId(id string) string => subscriptionResourceId('Microsoft.Authorization/roleDefinitions', id)

// ------------------------------------------------------------ existing resources
resource foundry 'Microsoft.CognitiveServices/accounts@2025-04-01-preview' existing = {
  name: foundryAccountName
}

resource project 'Microsoft.CognitiveServices/accounts/projects@2025-04-01-preview' existing = {
  parent: foundry
  name: projectName
}

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' existing = {
  name: logAnalyticsName
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' existing = {
  name: appInsightsName
}

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' existing = {
  name: storageAccountName
}

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' existing = if (!empty(keyVaultName)) {
  name: keyVaultName
}

// ------------------------------------------------------------ users group
// Data-plane use of the project: run agents, threads, files, vector-store reads.
resource usersProject 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(project.id, usersGroupObjectId, 'agent-consumer')
  scope: project
  properties: {
    principalId: usersGroupObjectId
    principalType: 'Group'
    roleDefinitionId: empty(agentConsumerRoleDefinitionId) ? roleId(roles.azureAiUser) : agentConsumerRoleDefinitionId
    description: 'sg-infosec-foundry-users: persona experience (team/README.md §4.1)'
  }
}

resource usersAppInsights 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(appInsights.id, usersGroupObjectId, roles.monitoringReader)
  scope: appInsights
  properties: {
    principalId: usersGroupObjectId
    principalType: 'Group'
    roleDefinitionId: roleId(roles.monitoringReader)
    description: 'sg-infosec-foundry-users: view traces of own runs'
  }
}

resource usersLogs 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(logAnalytics.id, usersGroupObjectId, roles.monitoringReader)
  scope: logAnalytics
  properties: {
    principalId: usersGroupObjectId
    principalType: 'Group'
    roleDefinitionId: roleId(roles.monitoringReader)
  }
}

// ------------------------------------------------------------ owner group (standing)
resource ownerRg 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, ownerGroupObjectId, roles.reader)
  properties: {
    principalId: ownerGroupObjectId
    principalType: 'Group'
    roleDefinitionId: roleId(roles.reader)
    description: 'sg-infosec-foundry-owner: standing read on the RG; Contributor is PIM-eligible only'
  }
}

resource ownerAccount 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(foundry.id, ownerGroupObjectId, roles.azureAiDeveloper)
  scope: foundry
  properties: {
    principalId: ownerGroupObjectId
    principalType: 'Group'
    roleDefinitionId: roleId(roles.azureAiDeveloper)
    description: 'sg-infosec-foundry-owner: create/update agents, connections, deployments (scripts/)'
  }
}

resource ownerProject 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(project.id, ownerGroupObjectId, roles.azureAiProjectManager)
  scope: project
  properties: {
    principalId: ownerGroupObjectId
    principalType: 'Group'
    roleDefinitionId: roleId(roles.azureAiProjectManager)
    description: 'sg-infosec-foundry-owner: manage the project and grant Azure AI User'
  }
}

// ------------------------------------------------------------ readers group (optional)
resource readersRg 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(readersGroupObjectId)) {
  name: guid(resourceGroup().id, readersGroupObjectId, roles.reader)
  properties: {
    principalId: readersGroupObjectId
    principalType: 'Group'
    roleDefinitionId: roleId(roles.reader)
    description: 'sg-infosec-foundry-readers: ISMS/audit/DPO read'
  }
}

resource readersLogs 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(readersGroupObjectId)) {
  name: guid(logAnalytics.id, readersGroupObjectId, roles.logAnalyticsReader)
  scope: logAnalytics
  properties: {
    principalId: readersGroupObjectId
    principalType: 'Group'
    roleDefinitionId: roleId(roles.logAnalyticsReader)
  }
}

// ------------------------------------------------------------ deployer SP (GitHub OIDC)
resource deployerRg 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(deployerPrincipalId)) {
  name: guid(resourceGroup().id, deployerPrincipalId, roles.contributor)
  properties: {
    principalId: deployerPrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: roleId(roles.contributor)
    description: 'GitHub OIDC deployer: Bicep redeploys from the production environment only'
  }
}

resource deployerAccount 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(deployerPrincipalId)) {
  name: guid(foundry.id, deployerPrincipalId, roles.azureAiDeveloper)
  scope: foundry
  properties: {
    principalId: deployerPrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: roleId(roles.azureAiDeveloper)
    description: 'GitHub OIDC deployer: deploy.sh (agents, integrations, orchestrator)'
  }
}

// ------------------------------------------------------------ Logic Apps MI
resource logicAppProject 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(logicAppPrincipalId)) {
  name: guid(project.id, logicAppPrincipalId, roles.azureAiUser)
  scope: project
  properties: {
    principalId: logicAppPrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: roleId(roles.azureAiUser)
    description: 'Logic Apps Standard MI: run agents from the pipelines'
  }
}

resource logicAppKv 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(logicAppPrincipalId) && !empty(keyVaultName)) {
  name: guid(keyVault.id, logicAppPrincipalId, roles.keyVaultSecretsUser)
  scope: keyVault
  properties: {
    principalId: logicAppPrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: roleId(roles.keyVaultSecretsUser)
    description: 'Logic Apps MI: read integration tokens by name (narrow further to per-secret scope where the tenant allows)'
  }
}

// ------------------------------------------------------------ delivery Function MI
resource functionBlob 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(deliveryFunctionPrincipalId)) {
  name: guid(storage.id, deliveryFunctionPrincipalId, roles.storageBlobDataContributor)
  scope: storage
  properties: {
    principalId: deliveryFunctionPrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: roleId(roles.storageBlobDataContributor)
    description: 'Delivery Function MI: deliverables container (the only SharePoint writer holds Sites.Selected write, granted via Graph, not ARM)'
  }
}

resource functionKv 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(deliveryFunctionPrincipalId) && !empty(keyVaultName)) {
  name: guid(keyVault.id, deliveryFunctionPrincipalId, roles.keyVaultSecretsUser)
  scope: keyVault
  properties: {
    principalId: deliveryFunctionPrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: roleId(roles.keyVaultSecretsUser)
  }
}

// ------------------------------------------------------------ outputs (for the access register)
output assignedUsersRole string = empty(agentConsumerRoleDefinitionId) ? 'Azure AI User (built-in)' : 'custom agent-consumer role'
output pimNote string = 'Privileged roles (Contributor, Key Vault Secrets Officer, Logic App Contributor, Website Contributor, Monitoring Contributor, Storage Blob Data Reader, conditioned RBAC Administrator) are PIM-eligible for group ${pimGroupObjectId}; configure in Entra PIM, never as standing assignments.'
