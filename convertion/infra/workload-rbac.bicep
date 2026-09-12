// Data-plane role assignments for the WORKLOAD managed identities (delivery
// Function, office-tools Function, Logic Apps Standard, hosted MCP). Humans and
// the deploy identity are assigned in team/rbac.bicep; the guid seeds here are
// identical to that module's so deploying both is idempotent (ARM treats the
// same name + same properties as no-op). Narrowest scope everywhere.

param foundryAccountName string
param projectName string
param keyVaultName string
param storageAccountName string
param docIntelName string = ''
param registryName string = ''
param functionRuntimeStorageAccountName string = ''
param logicAppRuntimeStorageAccountName string = ''
param deliveryFunctionPrincipalId string = ''
param officeToolsPrincipalId string = ''
param logicAppPrincipalId string = ''
param mcpPrincipalId string = ''

@description('Entra Agent ID principals (finding C7 / ID-2): the project shared agent identity and each PUBLISHED agent. They receive READ-ONLY data-plane roles only — the read/verify/approve chain of governance/HUMAN_APPROVAL.md is unchanged, and no agent identity may write to SharePoint or the deliverables archive. Re-run after every publish: a republished agent is a NEW principal (team/ACCESS_REGISTER.md records them)')
param agentIdentityPrincipalIds array = []

var roles = {
  azureAiUser: '53ca6127-db72-4b80-b1b0-d229d5fc3ae7'
  keyVaultSecretsUser: '4633458b-17de-408a-b874-0445c86b69e6'
  cognitiveServicesUser: 'a97b65f3-24c7-4388-baec-2e87135dc908'
  storageBlobDataContributor: 'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
  storageQueueDataContributor: '974c5e8b-45b9-4653-ba55-5f855dd0fb88'
  storageTableDataContributor: '0a9a7e1f-b9d0-4cc4-a60d-0319b160aebd'
  acrPull: '7f951dda-4ed3-4680-a7ca-43fe172d538d'
  storageBlobDataReader: '2a2b9908-6ea1-4ae2-8e65-a410df84e7d1'
}
func roleId(id string) string => subscriptionResourceId('Microsoft.Authorization/roleDefinitions', id)

var hasFn = !empty(deliveryFunctionPrincipalId)
var hasOffice = !empty(officeToolsPrincipalId)
var hasLa = !empty(logicAppPrincipalId)
var hasMcp = !empty(mcpPrincipalId)
var hasDocIntel = !empty(docIntelName)
var hasAcr = !empty(registryName)

resource foundry 'Microsoft.CognitiveServices/accounts@2025-04-01-preview' existing = { name: foundryAccountName }
resource project 'Microsoft.CognitiveServices/accounts/projects@2025-04-01-preview' existing = { parent: foundry, name: projectName }
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' existing = { name: keyVaultName }
resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' existing = { name: storageAccountName }
resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' existing = { parent: storage, name: 'default' }
resource deliverables 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' existing = { parent: blobService, name: 'deliverables' }
resource docIntel 'Microsoft.CognitiveServices/accounts@2025-04-01-preview' existing = if (hasDocIntel) { name: docIntelName }
resource acr 'Microsoft.ContainerRegistry/registries@2023-07-01' existing = if (hasAcr) { name: registryName }
resource fnStorage 'Microsoft.Storage/storageAccounts@2023-05-01' existing = if (hasFn) { name: functionRuntimeStorageAccountName }
resource laStorage 'Microsoft.Storage/storageAccounts@2023-05-01' existing = if (hasLa) { name: logicAppRuntimeStorageAccountName }

// ---- runtime storage (identity-based AzureWebJobsStorage) for the Function apps
var fnPrincipals = concat(hasFn ? [deliveryFunctionPrincipalId] : [], hasOffice ? [officeToolsPrincipalId] : [])
var storageDataRoles = [roles.storageBlobDataContributor, roles.storageQueueDataContributor, roles.storageTableDataContributor]

var fnRolePairs = flatten(map(fnPrincipals, p => map(storageDataRoles, r => { p: p, r: r })))

resource fnRuntimeRoles 'Microsoft.Authorization/roleAssignments@2022-04-01' = [for pair in fnRolePairs: {
  name: guid(fnStorage.id, pair.p, pair.r)
  scope: fnStorage
  properties: { principalId: pair.p, principalType: 'ServicePrincipal', roleDefinitionId: roleId(pair.r) }
}]

resource fnAcrPull 'Microsoft.Authorization/roleAssignments@2022-04-01' = [for p in fnPrincipals: if (hasAcr) {
  name: guid(acr.id, p, roles.acrPull)
  scope: acr
  properties: { principalId: p, principalType: 'ServicePrincipal', roleDefinitionId: roleId(roles.acrPull) }
}]

// The office-tools app's grants END HERE, deliberately: AcrPull (to pull its
// own image) and the identity-based AzureWebJobsStorage roles every Function
// app needs on the shared runtime storage account. It gets NO Graph, NO
// Foundry, NO Document Intelligence and no access to the deliverables
// container — it holds no credential and makes no outbound call. It converts
// bytes it is handed and returns bytes. The only link to it is
// OFFICE_TOOLS_BASE_URL + OFFICE_TOOLS_KEY on the DELIVERY app
// (infra/delivery.bicep). Do not add a role for it here without first
// changing that design statement in MAPPING.md and infra/README.md.

// ---- delivery Function: deliverables container (archive/evidence) + OCR
resource functionBlobContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (hasFn) {
  name: guid(deliverables.id, deliveryFunctionPrincipalId, roles.storageBlobDataContributor)
  scope: deliverables
  properties: { principalId: deliveryFunctionPrincipalId, principalType: 'ServicePrincipal', roleDefinitionId: roleId(roles.storageBlobDataContributor) }
}
resource functionDocIntelUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (hasFn && hasDocIntel) {
  name: guid(docIntel.id, deliveryFunctionPrincipalId, roles.cognitiveServicesUser)
  scope: docIntel
  properties: { principalId: deliveryFunctionPrincipalId, principalType: 'ServicePrincipal', roleDefinitionId: roleId(roles.cognitiveServicesUser) }
}

// ---- Logic Apps Standard: runtime storage, Foundry project, Key Vault (references)
resource laRuntimeRoles 'Microsoft.Authorization/roleAssignments@2022-04-01' = [for r in storageDataRoles: if (hasLa) {
  name: guid(laStorage.id, logicAppPrincipalId, r)
  scope: laStorage
  properties: { principalId: logicAppPrincipalId, principalType: 'ServicePrincipal', roleDefinitionId: roleId(r) }
}]
resource logicAppAiUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (hasLa) {
  name: guid(project.id, logicAppPrincipalId, roles.azureAiUser)
  scope: project
  properties: { principalId: logicAppPrincipalId, principalType: 'ServicePrincipal', roleDefinitionId: roleId(roles.azureAiUser) }
}
resource logicAppKvUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (hasLa) {
  name: guid(keyVault.id, logicAppPrincipalId, roles.keyVaultSecretsUser)
  scope: keyVault
  properties: { principalId: logicAppPrincipalId, principalType: 'ServicePrincipal', roleDefinitionId: roleId(roles.keyVaultSecretsUser) }
}

// ---- hosted MCP server
resource mcpAiUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (hasMcp) {
  name: guid(project.id, mcpPrincipalId, roles.azureAiUser)
  scope: project
  properties: { principalId: mcpPrincipalId, principalType: 'ServicePrincipal', roleDefinitionId: roleId(roles.azureAiUser) }
}
resource mcpAcrPull 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (hasMcp && hasAcr) {
  name: guid(acr.id, mcpPrincipalId, roles.acrPull)
  scope: acr
  properties: { principalId: mcpPrincipalId, principalType: 'ServicePrincipal', roleDefinitionId: roleId(roles.acrPull) }
}

// ---- C7 / ID-2: Entra Agent ID identities (project agent identity + one per
// published agent). Read-only by construction: Azure AI User on the project to
// run, and Storage Blob Data READER on the deliverables container so an agent
// can cite an archived report without ever writing one.
resource agentIdentityAiUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = [for p in agentIdentityPrincipalIds: {
  name: guid(project.id, p, roles.azureAiUser)
  scope: project
  properties: { principalId: p, principalType: 'ServicePrincipal', roleDefinitionId: roleId(roles.azureAiUser) }
}]

resource agentIdentityBlobReader 'Microsoft.Authorization/roleAssignments@2022-04-01' = [for p in agentIdentityPrincipalIds: {
  name: guid(deliverables.id, p, roles.storageBlobDataReader)
  scope: deliverables
  properties: { principalId: p, principalType: 'ServicePrincipal', roleDefinitionId: roleId(roles.storageBlobDataReader) }
}]
