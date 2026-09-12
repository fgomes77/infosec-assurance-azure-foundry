// Role assignments and PIM eligibilities for the InfoSec Assurance Foundry
// platform — team model of record (team/TEAM_MODEL.md §5–§7, §18).
//
// Deploy at resource-group scope, after infra/main.bicep, either as a module
// (delta D-B3 in team/TEAM_MODEL.md §20) or standalone:
//   az deployment group what-if -g {rg} -f rbac.bicep -p rbac.parameters.json
//   az deployment group create  -g {rg} -f rbac.bicep -p rbac.parameters.json
//
// Rules encoded here (controls in brackets):
//   - humans are assigned through Entra ID GROUPS only, never individually
//     [ISO 27001:2022 A.5.15, A.5.18; DORA Art. 9(4)(c)]
//   - the five assurance users hold ONE role: Azure AI User (or the custom
//     agent-consumer role) on the project — nothing else [A.5.15 least privilege]
//   - sg-infosec-foundry-owner holds standing LOW privilege only (Reader,
//     Log Analytics Reader, Key Vault Reader = names, not values) [A.8.2]
//   - every privileged human role is a PIM *eligibility* on
//     sg-infosec-foundry-admin-pim / -breakglass (enablePim=true, Entra ID P2).
//     enablePim=false assigns the same roles PERMANENTLY to -owner and must be
//     recorded as an exception in team/ACCESS_REGISTER.md [A.8.2; DORA 9(4)(c)]
//   - PIM activation policy (max 8 h / 4 h / 2 h, MFA, justification, ticket,
//     line-manager approval for Contributor) is a PIM role SETTING configured
//     by the IAM team (team/entra-groups.md §4) — not expressible in ARM
//   - the deploy identity may assign/remove ONLY the roles listed in
//     assignableRoles (ABAC condition on Role Based Access Control
//     Administrator) — no human holds RBAC Administrator [A.5.18; DORA 9(4)(e)]
//   - workload identities get the narrowest scope (container, vault, project)
//     [ISO 42001 A.9.2; DORA Art. 9(4)(d)]
//   - assignment names are guid() of (scope, principal, role) → idempotent
//     redeploys and a stable drift baseline for access-review.sh [A.8.15]
//
// Built-in role GUIDs are Azure-global; verify before first deployment:
//   az role definition list --query "[].{n:roleName,id:name}" -o table

targetScope = 'resourceGroup'

// ------------------------------------------------------------- parameters
@description('Foundry account name (infra/main.bicep: <baseName>-aif)')
param foundryAccountName string

@description('Foundry project name (infra/main.bicep: <baseName>-proj)')
param projectName string

@description('Log Analytics workspace name (<baseName>-logs)')
param logAnalyticsName string

@description('Application Insights component name (<baseName>-appi)')
param appInsightsName string

@description('Deliverables storage account name (<baseName>sa)')
param storageAccountName string

@description('Platform Key Vault name (<baseName>-kv, RBAC authorisation mode). Empty = skip every Key Vault assignment')
param keyVaultName string = ''

@description('Delivery Function App name (functions/delivery). Empty = skip Function-scoped roles')
param deliveryFunctionName string = ''

@description('Logic Apps Standard app name (workflows/). Empty = skip Logic-App-scoped roles')
param logicAppName string = ''

@description('Logic Apps Standard runtime storage account (empty = same as storageAccountName)')
param logicAppRuntimeStorageAccountName string = ''

@description('Bing Grounding resource name (<baseName>-bing). Empty = skip')
param bingAccountName string = ''

@description('Object id of sg-infosec-foundry-users (all five assurance users)')
param usersGroupObjectId string

@description('Object id of sg-infosec-foundry-owner (standing low-privilege roles of the accountable owner)')
param ownerGroupObjectId string

@description('Object id of sg-infosec-foundry-admin-pim (PIM-eligible privileged roles; empty = skip)')
param pimGroupObjectId string = ''

@description('Object id of sg-infosec-foundry-breakglass (deputy, PIM-eligible only; empty = skip)')
param breakglassGroupObjectId string = ''

@description('Object id of sg-infosec-foundry-readers (ISMS audit / DPO evidence read; empty = skip)')
param readersGroupObjectId string = ''

@description('Object id of the deploy service principal (GitHub OIDC federated credential, no secret; empty = skip)')
param deployerPrincipalId string = ''

@description('Principal id of the Logic Apps Standard system-assigned managed identity (empty = skip)')
param logicAppPrincipalId string = ''

@description('Principal id of the delivery Function system-assigned managed identity (empty = skip)')
param deliveryFunctionPrincipalId string = ''

@description('Principal id of the hosted MCP server managed identity (Container Apps; empty = not deployed)')
param mcpHostPrincipalId string = ''

@description('Optional custom role definition resource id for assurance users (team/custom-role.agent-consumer.json). Empty = built-in Azure AI User')
param agentConsumerRoleDefinitionId string = ''

@description('Key Vault secret NAMES the workload identities may read (TEAM_MODEL.md §7: Secrets User scoped to the named secrets, e.g. kv-jira-ro-token). Empty = vault-scoped Secrets User until the secrets exist (bootstrap step 4); redeploy with the names afterwards')
param keyVaultSecretNames array = []

@description('Grant the delivery Function MI Key Vault Secrets User (only if the Function reads a secret; ledger row L13)')
param deliveryFunctionReadsSecrets bool = false

@description('Grant sg-infosec-foundry-users Monitoring Reader on App Insights (NOT in the model — requires a new ledger row, team/TEAM_MODEL.md §5)')
param grantUsersMonitoringReader bool = false

@description('Create PIM eligibilities for privileged human roles (Entra ID P2). false = permanent assignments to -owner (recorded exception)')
param enablePim bool = true

@description('PIM eligibility validity (ISO 8601 duration); redeploy to renew after the quarterly access review')
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
  keyVaultReader: '21090545-7ca7-4776-b22c-e363652d74d2'
  keyVaultSecretsUser: '4633458b-17de-408a-b874-0445c86b69e6'
  keyVaultSecretsOfficer: 'b86a8fe4-44ce-4948-aee5-eccb2c155cd7'
  storageBlobDataContributor: 'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
  storageBlobDataReader: '2a2b9908-6ea1-4ae2-8e65-a410df84e7d1'
  storageQueueDataContributor: '974c5e8b-45b9-4653-ba55-5f855dd0fb88'
  storageTableDataContributor: '0a9a7e1f-b9d0-4cc4-a60d-0319b160aebd'
  logAnalyticsReader: '73c42c96-874c-492b-b04d-ab87d138a893'
  monitoringReader: '43d0d8ad-25c7-4714-9337-8ba259a9fe05'
  monitoringContributor: '749f88d5-cbae-40b8-bcfc-e573ddc772fa'
  monitoringMetricsPublisher: '3913510d-42f4-4e42-8a64-420c390055eb'
  websiteContributor: 'de139f84-1756-47ae-9be6-808fbbe84772'
  logicAppContributor: '87a39d53-fc1b-424a-814c-f7e04687dc9e'
  logicAppsStandardDeveloper: '523776ba-4eb2-4600-a3c8-f2dc93da4bdb'
  logicAppsStandardOperator: 'b70c96e9-66fe-4c09-b6e7-c98e69c98555'
  logicAppsStandardReader: '4accf36b-2c05-432f-91c8-5c532dff4c73'
}

func roleId(id string) string => subscriptionResourceId('Microsoft.Authorization/roleDefinitions', id)

// Roles the deploy identity may assign or remove (ABAC condition on its
// RBAC Administrator assignment). Owner / UAA / RBAC Administrator itself are
// deliberately absent: the deployer cannot escalate anyone, including itself.
var assignableRoles = [
  roles.reader
  roles.azureAiUser
  roles.azureAiDeveloper
  roles.keyVaultReader
  roles.keyVaultSecretsUser
  roles.keyVaultSecretsOfficer
  roles.storageBlobDataContributor
  roles.storageBlobDataReader
  roles.storageQueueDataContributor
  roles.storageTableDataContributor
  roles.logAnalyticsReader
  roles.monitoringReader
  roles.monitoringContributor
  roles.monitoringMetricsPublisher
  roles.websiteContributor
  roles.logicAppContributor
  roles.logicAppsStandardDeveloper
  roles.logicAppsStandardOperator
  roles.logicAppsStandardReader
]
var assignableRoleList = join(assignableRoles, ', ')
var rbacAdminCondition = '((!(ActionMatches{\'Microsoft.Authorization/roleAssignments/write\'})) OR (@Request[Microsoft.Authorization/roleAssignments:RoleDefinitionId] ForAnyOfAnyValues:GuidEquals {${assignableRoleList}})) AND ((!(ActionMatches{\'Microsoft.Authorization/roleAssignments/delete\'})) OR (@Resource[Microsoft.Authorization/roleAssignments:RoleDefinitionId] ForAnyOfAnyValues:GuidEquals {${assignableRoleList}}))'

var hasKv = !empty(keyVaultName)
var secretScoped = hasKv && !empty(keyVaultSecretNames)
var usersRoleDefinitionId = empty(agentConsumerRoleDefinitionId) ? roleId(roles.azureAiUser) : agentConsumerRoleDefinitionId
var hasFn = !empty(deliveryFunctionName)
var hasLa = !empty(logicAppName)
var hasPimGroup = !empty(pimGroupObjectId)
var hasBreakglass = !empty(breakglassGroupObjectId)
var laRuntimeStorageName = empty(logicAppRuntimeStorageAccountName) ? storageAccountName : logicAppRuntimeStorageAccountName

// Principal that receives the privileged set when PIM is NOT available
// (permanent fallback → -owner, recorded exception).
var permPrivilegedPrincipal = ownerGroupObjectId
var pimSchedule = {
  startDateTime: pimStartDateTime
  expiration: { type: 'AfterDuration', duration: pimEligibilityDuration }
}

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
resource laRuntimeStorage 'Microsoft.Storage/storageAccounts@2023-05-01' existing = {
  name: laRuntimeStorageName
}
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' existing = if (hasKv) {
  name: keyVaultName
}
resource kvSecrets 'Microsoft.KeyVault/vaults/secrets@2023-07-01' existing = [for n in keyVaultSecretNames: {
  parent: keyVault
  name: n
}]
resource deliveryFunction 'Microsoft.Web/sites@2023-12-01' existing = if (hasFn) {
  name: deliveryFunctionName
}
resource logicApp 'Microsoft.Web/sites@2023-12-01' existing = if (hasLa) {
  name: logicAppName
}
resource bing 'Microsoft.Bing/accounts@2020-06-10' existing = if (!empty(bingAccountName)) {
  name: bingAccountName
}

// =========================================================== USERS (§4, §7)
// The only Azure role the five assurance users hold: data-plane use of the
// project (systems a–j). Everything else reaches them in-thread, in Teams or
// in SharePoint. [A.5.15; EU AI Act Art. 26(2) — same persona for everyone]
resource usersProject 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  // name keyed on the effective role: switching between the built-in role and
  // the custom role creates a new assignment instead of failing an immutable update
  name: guid(project.id, usersGroupObjectId, usersRoleDefinitionId)
  scope: project
  properties: {
    principalId: usersGroupObjectId
    principalType: 'Group'
    roleDefinitionId: usersRoleDefinitionId
    description: 'sg-infosec-foundry-users: run agents, threads, files, vector-store retrieval (team/TEAM_MODEL.md §4, §7.1)'
  }
}

// Off by default — the model gives users no monitoring role (§21). Turning it
// on is a ledger addition (§5) approved as a Tier C platform change.
resource usersMonitoringReader 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (grantUsersMonitoringReader) {
  name: guid(appInsights.id, usersGroupObjectId, roles.monitoringReader)
  scope: appInsights
  properties: {
    principalId: usersGroupObjectId
    principalType: 'Group'
    roleDefinitionId: roleId(roles.monitoringReader)
    description: 'LEDGER ADDITION: sg-infosec-foundry-users self-service trace/cost view'
  }
}

// ==================================================== OWNER — standing (§5 L6, L9)
// Permanent, read-only: daily monitoring and visibility. No standing write.
resource ownerReaderRg 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, ownerGroupObjectId, roles.reader)
  properties: {
    principalId: ownerGroupObjectId
    principalType: 'Group'
    roleDefinitionId: roleId(roles.reader)
    description: 'L6: owner standing read on the platform RG (Contributor is PIM-eligible only)'
  }
}
resource ownerLogReader 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(logAnalytics.id, ownerGroupObjectId, roles.logAnalyticsReader)
  scope: logAnalytics
  properties: {
    principalId: ownerGroupObjectId
    principalType: 'Group'
    roleDefinitionId: roleId(roles.logAnalyticsReader)
    description: 'L6: owner continuous monitoring — egress alerts, verifier rate, tokens/cost (A.8.15/A.8.16)'
  }
}
resource ownerKvReader 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (hasKv) {
  name: guid(keyVault.id, ownerGroupObjectId, roles.keyVaultReader)
  scope: keyVault
  properties: {
    principalId: ownerGroupObjectId
    principalType: 'Group'
    roleDefinitionId: roleId(roles.keyVaultReader)
    description: 'L6: owner sees secret NAMES and rotation dates, never values (A.5.17 evidence)'
  }
}

// ============================================ PRIVILEGED SET — PIM (§5 L1–L5, L7, L8)
// Eligibilities on sg-infosec-foundry-admin-pim when enablePim=true; the same
// roles land PERMANENTLY on sg-infosec-foundry-owner when enablePim=false
// (record the exception with a review date in team/ACCESS_REGISTER.md).

// L1 — Azure AI Developer on the Foundry account (8 h, self-activation)
resource pimAiDeveloper 'Microsoft.Authorization/roleEligibilityScheduleRequests@2020-10-01' = if (enablePim && hasPimGroup) {
  name: guid('pim', foundry.id, pimGroupObjectId, roles.azureAiDeveloper)
  scope: foundry
  properties: {
    principalId: pimGroupObjectId
    roleDefinitionId: roleId(roles.azureAiDeveloper)
    requestType: 'AdminAssign'
    justification: 'L1: agent / vector-store / connection maintenance (deploy.sh steps 3-6b)'
    scheduleInfo: pimSchedule
  }
}
resource permAiDeveloper 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!enablePim) {
  name: guid(foundry.id, permPrivilegedPrincipal, roles.azureAiDeveloper)
  scope: foundry
  properties: {
    principalId: permPrivilegedPrincipal
    principalType: 'Group'
    roleDefinitionId: roleId(roles.azureAiDeveloper)
    description: 'EXCEPTION (enablePim=false): L1 permanent on -owner — record in ACCESS_REGISTER.md'
  }
}

// L2 — Contributor on the RG (8 h, line-manager approval in the PIM setting)
resource pimContributorRg 'Microsoft.Authorization/roleEligibilityScheduleRequests@2020-10-01' = if (enablePim && hasPimGroup) {
  name: guid('pim', resourceGroup().id, pimGroupObjectId, roles.contributor)
  properties: {
    principalId: pimGroupObjectId
    roleDefinitionId: roleId(roles.contributor)
    requestType: 'AdminAssign'
    justification: 'L2: hotfix Bicep/config when the pipeline cannot (line-manager approval)'
    scheduleInfo: pimSchedule
  }
}
resource permContributorRg 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!enablePim) {
  name: guid(resourceGroup().id, permPrivilegedPrincipal, roles.contributor)
  properties: {
    principalId: permPrivilegedPrincipal
    principalType: 'Group'
    roleDefinitionId: roleId(roles.contributor)
    description: 'EXCEPTION (enablePim=false): L2 permanent on -owner — record in ACCESS_REGISTER.md'
  }
}

// L3 — Key Vault Secrets Officer (2 h) — credential rotation
resource pimKvOfficer 'Microsoft.Authorization/roleEligibilityScheduleRequests@2020-10-01' = if (enablePim && hasPimGroup && hasKv) {
  name: guid('pim', keyVault.id, pimGroupObjectId, roles.keyVaultSecretsOfficer)
  scope: keyVault
  properties: {
    principalId: pimGroupObjectId
    roleDefinitionId: roleId(roles.keyVaultSecretsOfficer)
    requestType: 'AdminAssign'
    justification: 'L3: connection credential rotation (new secret version = A.5.17 evidence)'
    scheduleInfo: pimSchedule
  }
}
resource permKvOfficer 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!enablePim && hasKv) {
  name: guid(keyVault.id, permPrivilegedPrincipal, roles.keyVaultSecretsOfficer)
  scope: keyVault
  properties: {
    principalId: permPrivilegedPrincipal
    principalType: 'Group'
    roleDefinitionId: roleId(roles.keyVaultSecretsOfficer)
    description: 'EXCEPTION (enablePim=false): L3 permanent on -owner'
  }
}

// L4 — Logic Apps Standard Developer + Operator (8 h)
resource pimLogicDeveloper 'Microsoft.Authorization/roleEligibilityScheduleRequests@2020-10-01' = if (enablePim && hasPimGroup && hasLa) {
  name: guid('pim', logicApp.id, pimGroupObjectId, roles.logicAppsStandardDeveloper)
  scope: logicApp
  properties: {
    principalId: pimGroupObjectId
    roleDefinitionId: roleId(roles.logicAppsStandardDeveloper)
    requestType: 'AdminAssign'
    justification: 'L4: deploy workflow definitions (workflows/)'
    scheduleInfo: pimSchedule
  }
}
resource pimLogicOperator 'Microsoft.Authorization/roleEligibilityScheduleRequests@2020-10-01' = if (enablePim && hasPimGroup && hasLa) {
  name: guid('pim', logicApp.id, pimGroupObjectId, roles.logicAppsStandardOperator)
  scope: logicApp
  properties: {
    principalId: pimGroupObjectId
    roleDefinitionId: roleId(roles.logicAppsStandardOperator)
    requestType: 'AdminAssign'
    justification: 'L4: resubmit failed runs / disable a workflow during an incident'
    scheduleInfo: pimSchedule
  }
}
resource permLogicDeveloper 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!enablePim && hasLa) {
  name: guid(logicApp.id, permPrivilegedPrincipal, roles.logicAppsStandardDeveloper)
  scope: logicApp
  properties: {
    principalId: permPrivilegedPrincipal
    principalType: 'Group'
    roleDefinitionId: roleId(roles.logicAppsStandardDeveloper)
    description: 'EXCEPTION (enablePim=false): L4 permanent on -owner'
  }
}
resource permLogicOperator 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!enablePim && hasLa) {
  name: guid(logicApp.id, permPrivilegedPrincipal, roles.logicAppsStandardOperator)
  scope: logicApp
  properties: {
    principalId: permPrivilegedPrincipal
    principalType: 'Group'
    roleDefinitionId: roleId(roles.logicAppsStandardOperator)
    description: 'EXCEPTION (enablePim=false): L4 permanent on -owner'
  }
}

// L5 — Website Contributor on the delivery Function (4 h)
resource pimWebsiteContributor 'Microsoft.Authorization/roleEligibilityScheduleRequests@2020-10-01' = if (enablePim && hasPimGroup && hasFn) {
  name: guid('pim', deliveryFunction.id, pimGroupObjectId, roles.websiteContributor)
  scope: deliveryFunction
  properties: {
    principalId: pimGroupObjectId
    roleDefinitionId: roleId(roles.websiteContributor)
    requestType: 'AdminAssign'
    justification: 'L5: func azure functionapp publish (functions/delivery)'
    scheduleInfo: pimSchedule
  }
}
resource permWebsiteContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!enablePim && hasFn) {
  name: guid(deliveryFunction.id, permPrivilegedPrincipal, roles.websiteContributor)
  scope: deliveryFunction
  properties: {
    principalId: permPrivilegedPrincipal
    principalType: 'Group'
    roleDefinitionId: roleId(roles.websiteContributor)
    description: 'EXCEPTION (enablePim=false): L5 permanent on -owner'
  }
}

// L7 — Storage Blob Data Reader on the deliverables container (4 h)
resource pimBlobReader 'Microsoft.Authorization/roleEligibilityScheduleRequests@2020-10-01' = if (enablePim && hasPimGroup) {
  name: guid('pim', deliverables.id, pimGroupObjectId, roles.storageBlobDataReader)
  scope: deliverables
  properties: {
    principalId: pimGroupObjectId
    roleDefinitionId: roleId(roles.storageBlobDataReader)
    requestType: 'AdminAssign'
    justification: 'L7: troubleshooting rendered artefacts'
    scheduleInfo: pimSchedule
  }
}
resource permBlobReader 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!enablePim) {
  name: guid(deliverables.id, permPrivilegedPrincipal, roles.storageBlobDataReader)
  scope: deliverables
  properties: {
    principalId: permPrivilegedPrincipal
    principalType: 'Group'
    roleDefinitionId: roleId(roles.storageBlobDataReader)
    description: 'EXCEPTION (enablePim=false): L7 permanent on -owner'
  }
}

// L8 — Monitoring Contributor on Log Analytics (4 h) — alert rules, KQL detections
resource pimMonitoringContributor 'Microsoft.Authorization/roleEligibilityScheduleRequests@2020-10-01' = if (enablePim && hasPimGroup) {
  name: guid('pim', logAnalytics.id, pimGroupObjectId, roles.monitoringContributor)
  scope: logAnalytics
  properties: {
    principalId: pimGroupObjectId
    roleDefinitionId: roleId(roles.monitoringContributor)
    requestType: 'AdminAssign'
    justification: 'L8: alert rules (egress, verifier fail rate, latency, cost)'
    scheduleInfo: pimSchedule
  }
}
resource permMonitoringContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!enablePim) {
  name: guid(logAnalytics.id, permPrivilegedPrincipal, roles.monitoringContributor)
  scope: logAnalytics
  properties: {
    principalId: permPrivilegedPrincipal
    principalType: 'Group'
    roleDefinitionId: roleId(roles.monitoringContributor)
    description: 'EXCEPTION (enablePim=false): L8 permanent on -owner'
  }
}

// Bing Grounding — Contributor (2 h) for key rotation of the one API key the
// platform cannot avoid (§7). No permanent fallback: without PIM the owner
// rotates it in a Contributor (L2) window.
resource pimBingContributor 'Microsoft.Authorization/roleEligibilityScheduleRequests@2020-10-01' = if (enablePim && hasPimGroup && !empty(bingAccountName)) {
  name: guid('pim', bing.id, pimGroupObjectId, roles.contributor)
  scope: bing
  properties: {
    principalId: pimGroupObjectId
    roleDefinitionId: roleId(roles.contributor)
    requestType: 'AdminAssign'
    justification: 'Bing Grounding key rotation (180 d) — the single API key on the platform'
    scheduleInfo: pimSchedule
  }
}

// ================================================= BREAK-GLASS — PIM only (§5 L10, §12.3)
// Deputy continuity: same role set as -admin-pim, eligibility only, activation
// approved by the line manager / SOC on-call (PIM setting). No RBAC
// Administrator, no permanent fallback — without PIM there is no break-glass
// and the runbook (operations/access-governance/BREAK_GLASS.md) says so.
resource bgContributorRg 'Microsoft.Authorization/roleEligibilityScheduleRequests@2020-10-01' = if (enablePim && hasBreakglass) {
  name: guid('pim', resourceGroup().id, breakglassGroupObjectId, roles.contributor)
  properties: {
    principalId: breakglassGroupObjectId
    roleDefinitionId: roleId(roles.contributor)
    requestType: 'AdminAssign'
    justification: 'L10: break-glass continuity — disable freely, change only with retrospective owner approval (DORA Art. 9/11)'
    scheduleInfo: pimSchedule
  }
}
resource bgAiDeveloper 'Microsoft.Authorization/roleEligibilityScheduleRequests@2020-10-01' = if (enablePim && hasBreakglass) {
  name: guid('pim', foundry.id, breakglassGroupObjectId, roles.azureAiDeveloper)
  scope: foundry
  properties: {
    principalId: breakglassGroupObjectId
    roleDefinitionId: roleId(roles.azureAiDeveloper)
    requestType: 'AdminAssign'
    justification: 'L10: break-glass — disable a connection or an agent tool'
    scheduleInfo: pimSchedule
  }
}
resource bgKvOfficer 'Microsoft.Authorization/roleEligibilityScheduleRequests@2020-10-01' = if (enablePim && hasBreakglass && hasKv) {
  name: guid('pim', keyVault.id, breakglassGroupObjectId, roles.keyVaultSecretsOfficer)
  scope: keyVault
  properties: {
    principalId: breakglassGroupObjectId
    roleDefinitionId: roleId(roles.keyVaultSecretsOfficer)
    requestType: 'AdminAssign'
    justification: 'L10: break-glass — disable / rotate an exposed secret'
    scheduleInfo: pimSchedule
  }
}
resource bgLogicOperator 'Microsoft.Authorization/roleEligibilityScheduleRequests@2020-10-01' = if (enablePim && hasBreakglass && hasLa) {
  name: guid('pim', logicApp.id, breakglassGroupObjectId, roles.logicAppsStandardOperator)
  scope: logicApp
  properties: {
    principalId: breakglassGroupObjectId
    roleDefinitionId: roleId(roles.logicAppsStandardOperator)
    requestType: 'AdminAssign'
    justification: 'L10: break-glass — disable a workflow'
    scheduleInfo: pimSchedule
  }
}
resource bgLogicDeveloper 'Microsoft.Authorization/roleEligibilityScheduleRequests@2020-10-01' = if (enablePim && hasBreakglass && hasLa) {
  name: guid('pim', logicApp.id, breakglassGroupObjectId, roles.logicAppsStandardDeveloper)
  scope: logicApp
  properties: {
    principalId: breakglassGroupObjectId
    roleDefinitionId: roleId(roles.logicAppsStandardDeveloper)
    requestType: 'AdminAssign'
    justification: 'L10: break-glass — redeploy a workflow definition (change only with retrospective owner approval)'
    scheduleInfo: pimSchedule
  }
}
resource bgBlobReader 'Microsoft.Authorization/roleEligibilityScheduleRequests@2020-10-01' = if (enablePim && hasBreakglass) {
  name: guid('pim', deliverables.id, breakglassGroupObjectId, roles.storageBlobDataReader)
  scope: deliverables
  properties: {
    principalId: breakglassGroupObjectId
    roleDefinitionId: roleId(roles.storageBlobDataReader)
    requestType: 'AdminAssign'
    justification: 'L10: break-glass — inspect a rendered artefact during an incident'
    scheduleInfo: pimSchedule
  }
}
resource bgMonitoringContributor 'Microsoft.Authorization/roleEligibilityScheduleRequests@2020-10-01' = if (enablePim && hasBreakglass) {
  name: guid('pim', logAnalytics.id, breakglassGroupObjectId, roles.monitoringContributor)
  scope: logAnalytics
  properties: {
    principalId: breakglassGroupObjectId
    roleDefinitionId: roleId(roles.monitoringContributor)
    requestType: 'AdminAssign'
    justification: 'L10: break-glass — silence / adjust an alert rule during an incident'
    scheduleInfo: pimSchedule
  }
}
resource bgWebsiteContributor 'Microsoft.Authorization/roleEligibilityScheduleRequests@2020-10-01' = if (enablePim && hasBreakglass && hasFn) {
  name: guid('pim', deliveryFunction.id, breakglassGroupObjectId, roles.websiteContributor)
  scope: deliveryFunction
  properties: {
    principalId: breakglassGroupObjectId
    roleDefinitionId: roleId(roles.websiteContributor)
    requestType: 'AdminAssign'
    justification: 'L10: break-glass — stop the delivery Function'
    scheduleInfo: pimSchedule
  }
}

// ======================================================= DEPLOY IDENTITY (§5 L11)
// GitHub OIDC federated credential bound to environment `production`; no
// secret, no interactive sign-in. Contributor on the RG already covers the
// Function, Logic App, storage and monitoring control planes; the two extra
// rows are data-plane (agents) and secret seeding.
resource deployContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(deployerPrincipalId)) {
  name: guid(resourceGroup().id, deployerPrincipalId, roles.contributor)
  properties: {
    principalId: deployerPrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: roleId(roles.contributor)
    description: 'L11: Bicep / Function / Logic Apps deployments from the production environment only'
  }
}
resource deployRbacAdmin 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(deployerPrincipalId)) {
  name: guid(resourceGroup().id, deployerPrincipalId, roles.rbacAdministrator)
  properties: {
    principalId: deployerPrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: roleId(roles.rbacAdministrator)
    description: 'L11: may assign/remove ONLY the roles in assignableRoles (this file) — every access change is a PR + deployment record (A.5.18; DORA 9(4)(e))'
    condition: rbacAdminCondition
    conditionVersion: '2.0'
  }
}
resource deployAiDeveloper 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(deployerPrincipalId)) {
  name: guid(foundry.id, deployerPrincipalId, roles.azureAiDeveloper)
  scope: foundry
  properties: {
    principalId: deployerPrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: roleId(roles.azureAiDeveloper)
    description: 'L11: deploy.sh — agents, vector stores, connections, orchestrator'
  }
}
resource deployKvOfficer 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(deployerPrincipalId) && hasKv) {
  name: guid(keyVault.id, deployerPrincipalId, roles.keyVaultSecretsOfficer)
  scope: keyVault
  properties: {
    principalId: deployerPrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: roleId(roles.keyVaultSecretsOfficer)
    description: 'L11: seed secret NAMES at first deployment (values come from the pipeline environment, never the repo)'
  }
}

// ==================================================== WORKLOAD IDENTITIES (§5 L12–L14, L16)
// Foundry account MI → Key Vault (KV-backed conn-* connections)          [L14]
resource foundryKvUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (hasKv && !secretScoped) {
  name: guid(keyVault.id, foundry.id, 'account-mi', roles.keyVaultSecretsUser) // MI principalId is runtime-only; key on the resource id
  scope: keyVault
  properties: {
    principalId: foundry.identity.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: roleId(roles.keyVaultSecretsUser)
    description: 'L14: Foundry account reads connection secrets by reference (kv-*-ro-token) — vault scope until keyVaultSecretNames is set'
  }
}
resource foundryKvUserSecret 'Microsoft.Authorization/roleAssignments@2022-04-01' = [for (n, i) in keyVaultSecretNames: if (secretScoped) {
  name: guid(keyVault.id, n, foundry.id, 'account-mi', roles.keyVaultSecretsUser)
  scope: kvSecrets[i]
  properties: {
    principalId: foundry.identity.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: roleId(roles.keyVaultSecretsUser)
    description: 'L14: Foundry account MI — Secrets User on this named secret only (TEAM_MODEL.md §7)'
  }
}]
// Foundry project MI → App Insights metrics (tracing export)              [L14]
resource projectMetricsPublisher 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(appInsights.id, project.id, 'project-mi', roles.monitoringMetricsPublisher) // MI principalId is runtime-only; key on the resource id
  scope: appInsights
  properties: {
    principalId: project.identity.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: roleId(roles.monitoringMetricsPublisher)
    description: 'L14: tracing / token metrics export (ARCHITECTURE.md metrics)'
  }
}
// Graph app permissions of the project MI (Sites.Selected read, Defender and
// Entra read sets) are granted in Entra, not ARM — team/sharepoint-permissions.md
// and team/TEAM_MODEL.md §8.

// Logic Apps MI → project (run agents + verifier), Key Vault, runtime storage  [L12]
resource logicAppAiUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(logicAppPrincipalId)) {
  name: guid(project.id, logicAppPrincipalId, roles.azureAiUser)
  scope: project
  properties: {
    principalId: logicAppPrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: roleId(roles.azureAiUser)
    description: 'L12: pipelines run the producing agent and output-verifier (workflows/README.md)'
  }
}
resource logicAppKvUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(logicAppPrincipalId) && hasKv && !secretScoped) {
  name: guid(keyVault.id, logicAppPrincipalId, roles.keyVaultSecretsUser)
  scope: keyVault
  properties: {
    principalId: logicAppPrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: roleId(roles.keyVaultSecretsUser)
    description: 'L12: @Microsoft.KeyVault app-setting references — vault scope until keyVaultSecretNames is set'
  }
}
resource logicAppKvUserSecret 'Microsoft.Authorization/roleAssignments@2022-04-01' = [for (n, i) in keyVaultSecretNames: if (!empty(logicAppPrincipalId) && secretScoped) {
  name: guid(keyVault.id, n, logicAppPrincipalId, roles.keyVaultSecretsUser)
  scope: kvSecrets[i]
  properties: {
    principalId: logicAppPrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: roleId(roles.keyVaultSecretsUser)
    description: 'L12: Logic Apps MI — Secrets User on this named secret only (TEAM_MODEL.md §7)'
  }
}]
resource logicAppBlob 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(logicAppPrincipalId)) {
  name: guid(laRuntimeStorage.id, logicAppPrincipalId, roles.storageBlobDataContributor)
  scope: laRuntimeStorage
  properties: {
    principalId: logicAppPrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: roleId(roles.storageBlobDataContributor)
    description: 'L12: Logic Apps Standard runtime storage (identity-based connection, no shared key)'
  }
}
resource logicAppQueue 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(logicAppPrincipalId)) {
  name: guid(laRuntimeStorage.id, logicAppPrincipalId, roles.storageQueueDataContributor)
  scope: laRuntimeStorage
  properties: {
    principalId: logicAppPrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: roleId(roles.storageQueueDataContributor)
    description: 'L12: Logic Apps Standard runtime storage (queues)'
  }
}
resource logicAppTable 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(logicAppPrincipalId)) {
  name: guid(laRuntimeStorage.id, logicAppPrincipalId, roles.storageTableDataContributor)
  scope: laRuntimeStorage
  properties: {
    principalId: logicAppPrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: roleId(roles.storageTableDataContributor)
    description: 'L12: Logic Apps Standard runtime storage (tables)'
  }
}

// Delivery Function MI → deliverables container only; NO project role         [L13]
// (Graph Sites.Selected WRITE is granted in Entra — team/sharepoint-permissions.md)
resource functionBlobContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(deliveryFunctionPrincipalId)) {
  name: guid(deliverables.id, deliveryFunctionPrincipalId, roles.storageBlobDataContributor)
  scope: deliverables
  properties: {
    principalId: deliveryFunctionPrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: roleId(roles.storageBlobDataContributor)
    description: 'L13: staging of rendered files before the SharePoint upload (the single write path after verifier PASS + approval)'
  }
}
resource functionKvUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(deliveryFunctionPrincipalId) && hasKv && deliveryFunctionReadsSecrets && !secretScoped) {
  name: guid(keyVault.id, deliveryFunctionPrincipalId, roles.keyVaultSecretsUser)
  scope: keyVault
  properties: {
    principalId: deliveryFunctionPrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: roleId(roles.keyVaultSecretsUser)
    description: 'L13 (optional): only if the Function reads a secret — default off, MI-to-Graph needs none'
  }
}
resource functionKvUserSecret 'Microsoft.Authorization/roleAssignments@2022-04-01' = [for (n, i) in keyVaultSecretNames: if (!empty(deliveryFunctionPrincipalId) && deliveryFunctionReadsSecrets && secretScoped) {
  name: guid(keyVault.id, n, deliveryFunctionPrincipalId, roles.keyVaultSecretsUser)
  scope: kvSecrets[i]
  properties: {
    principalId: deliveryFunctionPrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: roleId(roles.keyVaultSecretsUser)
    description: 'L13 (optional): delivery Function MI — Secrets User on this named secret only'
  }
}]

// Hosted MCP server MI (optional; Easy Auth allowed group = -users)            [L16]
resource mcpHostAiUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(mcpHostPrincipalId)) {
  name: guid(project.id, mcpHostPrincipalId, roles.azureAiUser)
  scope: project
  properties: {
    principalId: mcpHostPrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: roleId(roles.azureAiUser)
    description: 'L16: shared MCP endpoint for the ENX gateway (caller UPN carried in thread metadata, team/TEAM_MODEL.md §11)'
  }
}

// ============================================================ READERS (§5 L15)
// Empty by default; ISMS audit / DPO per engagement. Read-only evidence access
// without touching the owner's account (A.5.35).
resource readersReaderRg 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(readersGroupObjectId)) {
  name: guid(resourceGroup().id, readersGroupObjectId, roles.reader)
  properties: {
    principalId: readersGroupObjectId
    principalType: 'Group'
    roleDefinitionId: roleId(roles.reader)
    description: 'L15: audit evidence — control plane read'
  }
}
resource readersLogReader 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(readersGroupObjectId)) {
  name: guid(logAnalytics.id, readersGroupObjectId, roles.logAnalyticsReader)
  scope: logAnalytics
  properties: {
    principalId: readersGroupObjectId
    principalType: 'Group'
    roleDefinitionId: roleId(roles.logAnalyticsReader)
    description: 'L15: audit evidence — tracing, approval exports'
  }
}
resource readersLogicReader 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(readersGroupObjectId) && hasLa) {
  name: guid(logicApp.id, readersGroupObjectId, roles.logicAppsStandardReader)
  scope: logicApp
  properties: {
    principalId: readersGroupObjectId
    principalType: 'Group'
    roleDefinitionId: roleId(roles.logicAppsStandardReader)
    description: 'L15: approval evidence in workflow run history'
  }
}

// --------------------------------------------------------------- outputs
output usersRole string = empty(agentConsumerRoleDefinitionId) ? 'Azure AI User (built-in) — pair with the drift alert (team/TEAM_MODEL.md §7.1)' : 'custom InfoSec Foundry Agent Consumer role'
output pimEnabled bool = enablePim
output keyVaultSecretsUserScope string = secretScoped ? 'per named secret (${length(keyVaultSecretNames)} secrets)' : 'vault scope — set keyVaultSecretNames after bootstrap step 4 (TEAM_MODEL.md §18)'
output privilegedPrincipalMode string = enablePim ? 'PIM eligibilities on sg-infosec-foundry-admin-pim / -breakglass' : 'EXCEPTION: permanent assignments on sg-infosec-foundry-owner — record in team/ACCESS_REGISTER.md with a review date'
output assignableRolesForDeployIdentity array = assignableRoles
output graphGrantsOutsideArm array = [
  'delivery Function MI: Sites.Selected write on the InfoSec Assurance site (team/sharepoint-permissions.md §3)'
  'Foundry project MI: Sites.Selected read + Defender/Entra read sets (team/TEAM_MODEL.md §8)'
  'Logic Apps MI: Sites.Selected read (write only under ledger row L12x until delta D-W3)'
]
