// Role assignments and PIM eligibilities for the InfoSec Assurance Foundry
// platform — least-privilege lens (team/least-privilege/IDENTITY_RBAC.md §2).
//
// Deploy at resource-group scope as a module from infra/main.bicep (see
// team/least-privilege/SHARED_DELTAS.md) or standalone:
//   az deployment group create -g {rg} -f rbac.bicep -p rbac.parameters.json
//
// Rules encoded here:
//   - humans are assigned through groups only, never individually
//   - every privileged human role is a PIM *eligibility* (enablePim=true;
//     requires Entra ID P2). enablePim=false falls back to permanent
//     assignments and must be recorded as an exception in the access review
//   - workload identities get the narrowest scope (container, vault, project)
//   - the deploy identity may assign only the roles listed in `assignableRoles`
//     (ABAC condition on Role Based Access Control Administrator)
//
// Built-in role GUIDs are Azure-global; verify before first deployment:
//   az role definition list --query "[?roleName=='Azure AI User'].name" -o tsv

targetScope = 'resourceGroup'

// ------------------------------------------------------------- parameters
@description('Foundry account name (infra/main.bicep output foundryAccountName)')
param foundryAccountName string

@description('Foundry project name (infra/main.bicep output projectName)')
param projectName string

@description('Log Analytics workspace name')
param logAnalyticsName string

@description('Application Insights component name')
param appInsightsName string

@description('Deliverables storage account name')
param storageAccountName string

@description('Platform Key Vault name (RBAC authorisation mode)')
param keyVaultName string

@description('Delivery Function App name (empty = skip Function roles)')
param deliveryFunctionName string = ''

@description('Logic Apps Standard app name (empty = skip Logic Apps roles)')
param logicAppName string = ''

@description('Object id of sg-infosec-foundry-users')
param usersGroupObjectId string

@description('Object id of sg-infosec-foundry-platform-admins')
param platformAdminsGroupObjectId string

@description('Object id of sg-infosec-foundry-breakglass (eligible-only; empty = skip)')
param breakglassGroupObjectId string = ''

@description('Object id of sg-infosec-foundry-auditors (empty = skip)')
param auditorsGroupObjectId string = ''

@description('Object id of the deploy service principal (GitHub OIDC federated credential)')
param deployPrincipalId string

@description('Principal id of the Logic Apps Standard system-assigned managed identity (empty = skip)')
param logicAppPrincipalId string = ''

@description('Principal id of the delivery Function system-assigned managed identity (empty = skip)')
param deliveryFunctionPrincipalId string = ''

@description('Principal id of the hosted MCP server managed identity (empty = skip)')
param mcpHostPrincipalId string = ''

@description('Create PIM eligibilities instead of permanent privileged assignments (Entra ID P2)')
param enablePim bool = true

@description('PIM eligibility validity (ISO 8601 duration); re-deploy to renew after the access review')
param pimEligibilityDuration string = 'P365D'

@description('Eligibility start (UTC, ISO 8601). Defaults to deployment time')
param pimStartDateTime string = utcNow('yyyy-MM-ddTHH:mm:ssZ')

// ------------------------------------------------------------ role GUIDs
var roles = {
  reader: 'acdd72a7-3385-48ef-bd42-f606fba81ae7'
  contributor: 'b24988ac-6180-42a0-ab88-20f7382dd24c'
  rbacAdministrator: 'f58310d9-a9f6-439a-9e8d-f62e7b41a168'
  azureAiUser: '53ca6127-db72-4b80-b1b0-d229d5fc3ae7'
  azureAiDeveloper: '64702f94-c441-49e6-a78b-ef80e0188fee'
  keyVaultSecretsUser: '4633458b-17de-408a-b874-0445c86b69e6'
  keyVaultSecretsOfficer: 'b86a8fe4-44ce-4948-aee5-eccb2c155cd7'
  storageBlobDataContributor: 'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
  storageBlobDataReader: '2a2b9908-6ea1-4ae2-8e65-a410df84e7d1'
  logAnalyticsReader: '73c42c96-874c-492b-b04d-ab87d138a893'
  monitoringContributor: '749f88d5-cbae-40b8-bcfc-e573ddc772fa'
  monitoringMetricsPublisher: '3913510d-42f4-4e42-8a64-420c390055eb'
  websiteContributor: 'de139f84-1756-47ae-9be6-808fbbe84772'
  logicAppsStandardDeveloper: '523776ba-4eb2-4600-a3c8-f2dc93da4bdb'
  logicAppsStandardOperator: 'b70c96e9-66fe-4c09-b6e7-c98e69c98555'
  logicAppsStandardReader: '4accf36b-2c05-432f-91c8-5c532dff4c73'
}

func roleId(id string) string => subscriptionResourceId('Microsoft.Authorization/roleDefinitions', id)

// Roles the deploy identity is allowed to assign/remove (ABAC condition).
var assignableRoles = [
  roles.reader
  roles.azureAiUser
  roles.azureAiDeveloper
  roles.keyVaultSecretsUser
  roles.keyVaultSecretsOfficer
  roles.storageBlobDataContributor
  roles.storageBlobDataReader
  roles.logAnalyticsReader
  roles.monitoringContributor
  roles.monitoringMetricsPublisher
  roles.websiteContributor
  roles.logicAppsStandardDeveloper
  roles.logicAppsStandardOperator
  roles.logicAppsStandardReader
]
var assignableRoleList = join(assignableRoles, ', ')
var rbacAdminCondition = '((!(ActionMatches{\'Microsoft.Authorization/roleAssignments/write\'})) OR (@Request[Microsoft.Authorization/roleAssignments:RoleDefinitionId] ForAnyOfAnyValues:GuidEquals {${assignableRoleList}})) AND ((!(ActionMatches{\'Microsoft.Authorization/roleAssignments/delete\'})) OR (@Resource[Microsoft.Authorization/roleAssignments:RoleDefinitionId] ForAnyOfAnyValues:GuidEquals {${assignableRoleList}}))'

// ---------------------------------------------------- existing resources
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
resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' existing = {
  parent: storage
  name: 'default'
}
resource deliverables 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' existing = {
  parent: blobService
  name: 'deliverables'
}
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' existing = {
  name: keyVaultName
}
resource deliveryFunction 'Microsoft.Web/sites@2023-12-01' existing = if (!empty(deliveryFunctionName)) {
  name: deliveryFunctionName
}
resource logicApp 'Microsoft.Web/sites@2023-12-01' existing = if (!empty(logicAppName)) {
  name: logicAppName
}

// ============================================================ USERS (perm)
// The only role the five assurance users hold: data-plane use of the project.
resource usersAiUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(project.id, usersGroupObjectId, roles.azureAiUser)
  scope: project
  properties: {
    principalId: usersGroupObjectId
    principalType: 'Group'
    roleDefinitionId: roleId(roles.azureAiUser)
    description: 'Assurance users: run agents/threads/files on the project (systems a-j)'
  }
}

// ================================================== PLATFORM ADMINS (owner)
// Permanent, read-only: visibility + monitoring duty (ledger A6).
resource adminsReaderRg 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, platformAdminsGroupObjectId, roles.reader)
  properties: {
    principalId: platformAdminsGroupObjectId
    principalType: 'Group'
    roleDefinitionId: roleId(roles.reader)
    description: 'Owner: read visibility of the platform resource group'
  }
}
resource adminsLogReader 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(logAnalytics.id, platformAdminsGroupObjectId, roles.logAnalyticsReader)
  scope: logAnalytics
  properties: {
    principalId: platformAdminsGroupObjectId
    principalType: 'Group'
    roleDefinitionId: roleId(roles.logAnalyticsReader)
    description: 'Owner: continuous monitoring (egress alerts, verifier rate, cost)'
  }
}

// Privileged: PIM eligibilities (ledger A1-A5, A7). Each block has a
// permanent fallback used only when enablePim=false.
resource pimAiDeveloper 'Microsoft.Authorization/roleEligibilityScheduleRequests@2022-04-01-preview' = if (enablePim) {
  name: guid('pim', foundry.id, platformAdminsGroupObjectId, roles.azureAiDeveloper)
  scope: foundry
  properties: {
    principalId: platformAdminsGroupObjectId
    roleDefinitionId: roleId(roles.azureAiDeveloper)
    requestType: 'AdminAssign'
    justification: 'A1: agent/vector-store/connection maintenance (deploy.sh steps 3-6b)'
    scheduleInfo: { startDateTime: pimStartDateTime, expiration: { type: 'AfterDuration', duration: pimEligibilityDuration } }
  }
}
resource permAiDeveloper 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!enablePim) {
  name: guid(foundry.id, platformAdminsGroupObjectId, roles.azureAiDeveloper)
  scope: foundry
  properties: { principalId: platformAdminsGroupObjectId, principalType: 'Group', roleDefinitionId: roleId(roles.azureAiDeveloper), description: 'EXCEPTION (no PIM): A1' }
}

resource pimContributorRg 'Microsoft.Authorization/roleEligibilityScheduleRequests@2022-04-01-preview' = if (enablePim) {
  name: guid('pim', resourceGroup().id, platformAdminsGroupObjectId, roles.contributor)
  properties: {
    principalId: platformAdminsGroupObjectId
    roleDefinitionId: roleId(roles.contributor)
    requestType: 'AdminAssign'
    justification: 'A2: hotfix deployments when the pipeline cannot'
    scheduleInfo: { startDateTime: pimStartDateTime, expiration: { type: 'AfterDuration', duration: pimEligibilityDuration } }
  }
}
resource permContributorRg 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!enablePim) {
  name: guid(resourceGroup().id, platformAdminsGroupObjectId, roles.contributor)
  properties: { principalId: platformAdminsGroupObjectId, principalType: 'Group', roleDefinitionId: roleId(roles.contributor), description: 'EXCEPTION (no PIM): A2' }
}

resource pimKvOfficer 'Microsoft.Authorization/roleEligibilityScheduleRequests@2022-04-01-preview' = if (enablePim) {
  name: guid('pim', keyVault.id, platformAdminsGroupObjectId, roles.keyVaultSecretsOfficer)
  scope: keyVault
  properties: {
    principalId: platformAdminsGroupObjectId
    roleDefinitionId: roleId(roles.keyVaultSecretsOfficer)
    requestType: 'AdminAssign'
    justification: 'A3: connection credential rotation'
    scheduleInfo: { startDateTime: pimStartDateTime, expiration: { type: 'AfterDuration', duration: pimEligibilityDuration } }
  }
}
resource permKvOfficer 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!enablePim) {
  name: guid(keyVault.id, platformAdminsGroupObjectId, roles.keyVaultSecretsOfficer)
  scope: keyVault
  properties: { principalId: platformAdminsGroupObjectId, principalType: 'Group', roleDefinitionId: roleId(roles.keyVaultSecretsOfficer), description: 'EXCEPTION (no PIM): A3' }
}

resource pimMonitoringContributor 'Microsoft.Authorization/roleEligibilityScheduleRequests@2022-04-01-preview' = if (enablePim) {
  name: guid('pim', logAnalytics.id, platformAdminsGroupObjectId, roles.monitoringContributor)
  scope: logAnalytics
  properties: {
    principalId: platformAdminsGroupObjectId
    roleDefinitionId: roleId(roles.monitoringContributor)
    requestType: 'AdminAssign'
    justification: 'A6: alert rules (egress, verifier fail rate, cost)'
    scheduleInfo: { startDateTime: pimStartDateTime, expiration: { type: 'AfterDuration', duration: pimEligibilityDuration } }
  }
}

resource pimBlobReader 'Microsoft.Authorization/roleEligibilityScheduleRequests@2022-04-01-preview' = if (enablePim) {
  name: guid('pim', deliverables.id, platformAdminsGroupObjectId, roles.storageBlobDataReader)
  scope: deliverables
  properties: {
    principalId: platformAdminsGroupObjectId
    roleDefinitionId: roleId(roles.storageBlobDataReader)
    requestType: 'AdminAssign'
    justification: 'A7: troubleshooting rendered artefacts'
    scheduleInfo: { startDateTime: pimStartDateTime, expiration: { type: 'AfterDuration', duration: pimEligibilityDuration } }
  }
}

resource pimWebsiteContributor 'Microsoft.Authorization/roleEligibilityScheduleRequests@2022-04-01-preview' = if (enablePim && !empty(deliveryFunctionName)) {
  name: guid('pim', resourceId('Microsoft.Web/sites', deliveryFunctionName), platformAdminsGroupObjectId, roles.websiteContributor)
  scope: deliveryFunction
  properties: {
    principalId: platformAdminsGroupObjectId
    roleDefinitionId: roleId(roles.websiteContributor)
    requestType: 'AdminAssign'
    justification: 'A5: delivery Function deployments'
    scheduleInfo: { startDateTime: pimStartDateTime, expiration: { type: 'AfterDuration', duration: pimEligibilityDuration } }
  }
}

resource pimLogicDeveloper 'Microsoft.Authorization/roleEligibilityScheduleRequests@2022-04-01-preview' = if (enablePim && !empty(logicAppName)) {
  name: guid('pim', resourceId('Microsoft.Web/sites', logicAppName), platformAdminsGroupObjectId, roles.logicAppsStandardDeveloper)
  scope: logicApp
  properties: {
    principalId: platformAdminsGroupObjectId
    roleDefinitionId: roleId(roles.logicAppsStandardDeveloper)
    requestType: 'AdminAssign'
    justification: 'A4: workflow definition deployment'
    scheduleInfo: { startDateTime: pimStartDateTime, expiration: { type: 'AfterDuration', duration: pimEligibilityDuration } }
  }
}
resource pimLogicOperator 'Microsoft.Authorization/roleEligibilityScheduleRequests@2022-04-01-preview' = if (enablePim && !empty(logicAppName)) {
  name: guid('pim', resourceId('Microsoft.Web/sites', logicAppName), platformAdminsGroupObjectId, roles.logicAppsStandardOperator)
  scope: logicApp
  properties: {
    principalId: platformAdminsGroupObjectId
    roleDefinitionId: roleId(roles.logicAppsStandardOperator)
    requestType: 'AdminAssign'
    justification: 'A4: resubmit failed runs / disable a workflow in an incident'
    scheduleInfo: { startDateTime: pimStartDateTime, expiration: { type: 'AfterDuration', duration: pimEligibilityDuration } }
  }
}

// ======================================================== BREAK-GLASS (PIM)
// Same privileged set as platform-admins, eligibility only, approval by the
// line manager configured in the PIM role setting (not expressible here).
resource pimBreakglassContributor 'Microsoft.Authorization/roleEligibilityScheduleRequests@2022-04-01-preview' = if (enablePim && !empty(breakglassGroupObjectId)) {
  name: guid('pim', resourceGroup().id, breakglassGroupObjectId, roles.contributor)
  properties: {
    principalId: breakglassGroupObjectId
    roleDefinitionId: roleId(roles.contributor)
    requestType: 'AdminAssign'
    justification: 'A9: break-glass continuity (operations/access-governance/BREAK_GLASS.md)'
    scheduleInfo: { startDateTime: pimStartDateTime, expiration: { type: 'AfterDuration', duration: pimEligibilityDuration } }
  }
}
resource pimBreakglassAiDeveloper 'Microsoft.Authorization/roleEligibilityScheduleRequests@2022-04-01-preview' = if (enablePim && !empty(breakglassGroupObjectId)) {
  name: guid('pim', foundry.id, breakglassGroupObjectId, roles.azureAiDeveloper)
  scope: foundry
  properties: {
    principalId: breakglassGroupObjectId
    roleDefinitionId: roleId(roles.azureAiDeveloper)
    requestType: 'AdminAssign'
    justification: 'A9: break-glass continuity'
    scheduleInfo: { startDateTime: pimStartDateTime, expiration: { type: 'AfterDuration', duration: pimEligibilityDuration } }
  }
}
resource pimBreakglassKvOfficer 'Microsoft.Authorization/roleEligibilityScheduleRequests@2022-04-01-preview' = if (enablePim && !empty(breakglassGroupObjectId)) {
  name: guid('pim', keyVault.id, breakglassGroupObjectId, roles.keyVaultSecretsOfficer)
  scope: keyVault
  properties: {
    principalId: breakglassGroupObjectId
    roleDefinitionId: roleId(roles.keyVaultSecretsOfficer)
    requestType: 'AdminAssign'
    justification: 'A9: break-glass credential revocation'
    scheduleInfo: { startDateTime: pimStartDateTime, expiration: { type: 'AfterDuration', duration: pimEligibilityDuration } }
  }
}

// ========================================================= DEPLOY IDENTITY
resource deployContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, deployPrincipalId, roles.contributor)
  properties: {
    principalId: deployPrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: roleId(roles.contributor)
    description: 'A10: GitHub Actions deploy (Bicep, Function, Logic Apps)'
  }
}
resource deployRbacAdmin 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, deployPrincipalId, roles.rbacAdministrator)
  properties: {
    principalId: deployPrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: roleId(roles.rbacAdministrator)
    description: 'A10: may assign/remove only the roles in assignableRoles'
    condition: rbacAdminCondition
    conditionVersion: '2.0'
  }
}
resource deployAiDeveloper 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(foundry.id, deployPrincipalId, roles.azureAiDeveloper)
  scope: foundry
  properties: {
    principalId: deployPrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: roleId(roles.azureAiDeveloper)
    description: 'A10: create/update agents, vector stores, connections from the pipeline'
  }
}
resource deployKvOfficer 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, deployPrincipalId, roles.keyVaultSecretsOfficer)
  scope: keyVault
  properties: {
    principalId: deployPrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: roleId(roles.keyVaultSecretsOfficer)
    description: 'A10: seed secret names at first deployment (values from pipeline environment)'
  }
}

// ==================================================== WORKLOAD IDENTITIES
// Foundry account MI -> Key Vault (KV-backed connections)
resource foundryKvUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, foundry.id, 'account-mi', roles.keyVaultSecretsUser) // MI principalId is runtime-only; key on the resource id
  scope: keyVault
  properties: {
    principalId: foundry.identity.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: roleId(roles.keyVaultSecretsUser)
    description: 'A13: Foundry account reads connection secrets by reference'
  }
}
// Foundry project MI -> App Insights metrics
resource projectMetricsPublisher 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(appInsights.id, project.id, 'project-mi', roles.monitoringMetricsPublisher) // MI principalId is runtime-only; key on the resource id
  scope: appInsights
  properties: {
    principalId: project.identity.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: roleId(roles.monitoringMetricsPublisher)
    description: 'A13: tracing export'
  }
}
// Logic Apps MI -> project (run agents) + Key Vault (API tokens by reference)
resource logicAppAiUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(logicAppPrincipalId)) {
  name: guid(project.id, logicAppPrincipalId, roles.azureAiUser)
  scope: project
  properties: {
    principalId: logicAppPrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: roleId(roles.azureAiUser)
    description: 'A11: pipelines run agents and the verifier'
  }
}
resource logicAppKvUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(logicAppPrincipalId)) {
  name: guid(keyVault.id, logicAppPrincipalId, roles.keyVaultSecretsUser)
  scope: keyVault
  properties: {
    principalId: logicAppPrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: roleId(roles.keyVaultSecretsUser)
    description: 'A11: @Microsoft.KeyVault app-setting references'
  }
}
// Delivery Function MI -> deliverables container only (Graph Sites.Selected is granted outside Azure RBAC)
resource functionBlobContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(deliveryFunctionPrincipalId)) {
  name: guid(deliverables.id, deliveryFunctionPrincipalId, roles.storageBlobDataContributor)
  scope: deliverables
  properties: {
    principalId: deliveryFunctionPrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: roleId(roles.storageBlobDataContributor)
    description: 'A12: staging of rendered files before SharePoint upload'
  }
}
// Hosted MCP server MI (optional)
resource mcpHostAiUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(mcpHostPrincipalId)) {
  name: guid(project.id, mcpHostPrincipalId, roles.azureAiUser)
  scope: project
  properties: {
    principalId: mcpHostPrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: roleId(roles.azureAiUser)
    description: 'Hosted MCP endpoint (Easy Auth restricts callers to sg-infosec-foundry-users)'
  }
}

// ============================================================== AUDITORS
resource auditorsReaderRg 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(auditorsGroupObjectId)) {
  name: guid(resourceGroup().id, auditorsGroupObjectId, roles.reader)
  properties: {
    principalId: auditorsGroupObjectId
    principalType: 'Group'
    roleDefinitionId: roleId(roles.reader)
    description: 'A14: audit evidence (read-only)'
  }
}
resource auditorsLogReader 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(auditorsGroupObjectId)) {
  name: guid(logAnalytics.id, auditorsGroupObjectId, roles.logAnalyticsReader)
  scope: logAnalytics
  properties: {
    principalId: auditorsGroupObjectId
    principalType: 'Group'
    roleDefinitionId: roleId(roles.logAnalyticsReader)
    description: 'A14: audit evidence (tracing, approvals export)'
  }
}
resource auditorsLogicReader 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(auditorsGroupObjectId) && !empty(logicAppName)) {
  name: guid(resourceId('Microsoft.Web/sites', logicAppName), auditorsGroupObjectId, roles.logicAppsStandardReader)
  scope: logicApp
  properties: {
    principalId: auditorsGroupObjectId
    principalType: 'Group'
    roleDefinitionId: roleId(roles.logicAppsStandardReader)
    description: 'A14: approval evidence in run history'
  }
}

// --------------------------------------------------------------- outputs
output assignableRolesForDeployIdentity array = assignableRoles
output pimEnabled bool = enablePim
