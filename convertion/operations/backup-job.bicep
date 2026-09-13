// Nightly, EU-resident export of the shared memory store and the vector-store
// inventory (operations/BACKUP_DR.md §3 B1) as an Azure Container Apps Job.
//
// Why a job in the resource group and not a CI runner: the export carries
// team memory notes (internal), so it must never transit a runner outside
// the EU tenant boundary. The job runs the kit image (mcp-server/ or any
// python:3.12 image with setup/requirements.txt + azure-storage-blob) with a
// system-assigned managed identity that holds exactly two rights:
//   - Azure AI User on the Foundry project (data-plane read of vector stores)
//   - Storage Blob Data Contributor on the ONE 'backups' container
// No Key Vault access, no Azure AI Developer, no write to SharePoint.
// [ISO 27001:2022 A.8.13, A.8.2; DORA Art. 12(1)–(2); residency: requirement i]
//
// Deploy after infra/main.bicep (needs the Foundry project, the storage account
// and the 'backups' container from delta D-BDR-B1), as a module (delta D-BDR-B3)
// or standalone:
//   az deployment group what-if -g {rg} -f backup-job.bicep \
//       -p baseName=infosecfoundry projectEndpoint={project-endpoint} \
//          jobImage={registry}.azurecr.io/infosec-mcp:{tag}
// Placeholders in {braces}; no real hostnames, ids or secrets.

targetScope = 'resourceGroup'

@description('Base name used by infra/main.bicep (Foundry account {baseName}-aif, storage {baseName}sa)')
@minLength(3)
@maxLength(15)
param baseName string = 'infosecfoundry'

@description('EU region (same as the platform)')
param location string = resourceGroup().location

@description('Foundry project data-plane endpoint (PROJECT_ENDPOINT in setup/.env) — not a secret')
param projectEndpoint string = '{project-endpoint}'

@description('Name of the Foundry project resource ({baseName}-proj)')
param projectName string = '${baseName}-proj'

@description('Container image carrying the kit scripts + azure-storage-blob (private registry, identity pull)')
param jobImage string = '{registry}.azurecr.io/infosec-mcp:{tag}'

@description('Registry login server for managed-identity pull (empty = public image)')
param registryServer string = ''

@description('Existing Container Apps environment id (e.g. the one from infra/mcp-server.bicep); empty = create a minimal one')
param containerAppsEnvironmentId string = ''

@description('Log Analytics workspace name for the created environment ({baseName}-logs); ignored when reusing an environment')
param logAnalyticsName string = '${baseName}-logs'

@description('Cron (UTC) — nightly 02:00 keeps the memory-store RPO at 24 h (BACKUP_DR.md §2)')
param cronExpression string = '0 2 * * *'

@description('Blob container that receives the dated export folders (created by infra delta D-BDR-B1)')
param backupContainerName string = 'backups'

@description('Platform release tag stamped into manifest.json (LIFECYCLE.md §1)')
param kitRelease string = 'unversioned'

var roles = {
  azureAiUser: '53ca6127-db72-4b80-b1b0-d745d6d5456d'          // Azure AI User (data plane)
  storageBlobDataContributor: 'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
  acrPull: '7f951dda-4ed3-4680-a7ca-43fe172d538d'
}
var storageAccountName = toLower(replace('${baseName}sa', '-', ''))
var createEnvironment = empty(containerAppsEnvironmentId)

// ------------------------------------------------------------ existing resources
resource foundry 'Microsoft.CognitiveServices/accounts@2025-06-01' existing = {
  name: '${baseName}-aif'
}

resource project 'Microsoft.CognitiveServices/accounts/projects@2025-06-01' existing = {
  parent: foundry
  name: projectName
}

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' existing = {
  name: storageAccountName
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' existing = {
  parent: storage
  name: 'default'
}

resource backupsContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' existing = {
  parent: blobService
  name: backupContainerName
}

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' existing = {
  name: logAnalyticsName
}

// ------------------------------------------------------------ environment (optional)
resource environment 'Microsoft.App/managedEnvironments@2024-03-01' = if (createEnvironment) {
  name: '${baseName}-cae-ops'
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
    zoneRedundant: false
  }
}

// ------------------------------------------------------------ the job
resource backupJob 'Microsoft.App/jobs@2024-03-01' = {
  name: '${baseName}-job-backup'
  location: location
  identity: { type: 'SystemAssigned' }
  properties: {
    environmentId: createEnvironment ? environment.id : containerAppsEnvironmentId
    configuration: {
      triggerType: 'Schedule'
      scheduleTriggerConfig: {
        cronExpression: cronExpression
        parallelism: 1
        replicaCompletionCount: 1
      }
      replicaTimeout: 1800
      replicaRetryLimit: 1
      registries: empty(registryServer) ? [] : [
        {
          server: registryServer
          identity: 'system'
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'backup'
          image: jobImage
          command: [ 'python3' ]
          args: [
            '/app/operations/backup_vector_stores.py'
            '--out'
            '/tmp/backup/run'
            '--upload-account'
            storageAccountName
            '--upload-container'
            backupContainerName
          ]
          env: [
            { name: 'PROJECT_ENDPOINT', value: projectEndpoint }
            { name: 'KIT_RELEASE', value: kitRelease }
            { name: 'ENX_DATA_BOUNDARY', value: 'EU' }
          ]
          resources: { cpu: json('0.25'), memory: '0.5Gi' }
        }
      ]
    }
  }
}

// ------------------------------------------------------------ least-privilege grants
resource jobAiUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(project.id, backupJob.id, 'backup-job', roles.azureAiUser)
  scope: project
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roles.azureAiUser)
    principalId: backupJob.identity.principalId
    principalType: 'ServicePrincipal'
    description: 'Nightly memory-store export: data-plane read only (operations/BACKUP_DR.md B1)'
  }
}

resource jobBlobWriter 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(backupsContainer.id, backupJob.id, 'backup-job', roles.storageBlobDataContributor)
  scope: backupsContainer
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roles.storageBlobDataContributor)
    principalId: backupJob.identity.principalId
    principalType: 'ServicePrincipal'
    description: 'Write dated export folders into the backups container only'
  }
}

output backupJobName string = backupJob.name
output backupJobPrincipalId string = backupJob.identity.principalId
output backupPath string = '${storageAccountName}/${backupContainerName}/<yyyy-mm-dd>/'
