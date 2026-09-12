// Logic Apps Standard app hosting workflows/*.json (Routine replacements, the
// report-delivery pipelines instantiated from workflows/pipelines.json, and the
// template-update approval flow). System-assigned managed identity: Azure AI
// User on the Foundry project (main.bicep), Key Vault Secrets User (secrets are
// bound through @Microsoft.KeyVault app-setting references — never stored here),
// identity-based runtime storage. Workflow packaging/zip deploy: README §Workflows.

param baseName string
param location string
param logAnalyticsId string
param appInsightsConnectionString string
param projectEndpoint string
param keyVaultName string

@description('Delivery Function base URL (workflow parameter deliveryFunctionBaseUrl)')
param deliveryFunctionBaseUrl string

@description('Key Vault secret names bound as app settings (setup/SECRETS.md). Values NEVER appear in the template')
param secretNames object = {
  DELIVERY_FUNCTION_KEY: 'kv-delivery-function-key'
  APPROVAL_WEBHOOK_URL: 'kv-approval-webhook-url'
  TEAMS_WEBHOOK_URL: 'kv-teams-webhook-url'
  JIRA_API_TOKEN: 'kv-jira-api-token'
  ONETRUST_API_TOKEN: 'kv-onetrust-api-token'
  IAF_CLIENT_SECRET: 'kv-iaf-client-secret'
}

@description('Foundry Agents REST api-version used by the HTTP actions')
param foundryApiVersion string = '2025-05-01'

param appsSubnetId string = ''
@allowed(['Enabled', 'Disabled'])
param publicNetworkAccess string = 'Enabled'

func kvRef(vault string, secret string) string => '@Microsoft.KeyVault(VaultName=${vault};SecretName=${secret})'

resource runtimeStorage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: toLower(replace('${baseName}lasa', '-', ''))
  location: location
  kind: 'StorageV2'
  sku: { name: 'Standard_ZRS' }
  properties: {
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
    allowSharedKeyAccess: false
    supportsHttpsTrafficOnly: true
    publicNetworkAccess: publicNetworkAccess
    networkAcls: { defaultAction: publicNetworkAccess == 'Disabled' ? 'Deny' : 'Allow', bypass: 'AzureServices' }
  }
}

resource plan 'Microsoft.Web/serverfarms@2023-12-01' = {
  name: '${baseName}-la-plan'
  location: location
  kind: 'elastic'
  sku: { name: 'WS1', tier: 'WorkflowStandard' }
  properties: { reserved: false, maximumElasticWorkerCount: 3 }
}

var secretSettings = [for k in objectKeys(secretNames): { name: k, value: kvRef(keyVaultName, secretNames[k]) }]

resource logicApp 'Microsoft.Web/sites@2023-12-01' = {
  name: '${baseName}-la'
  location: location
  kind: 'functionapp,workflowapp'
  identity: { type: 'SystemAssigned' }
  properties: {
    serverFarmId: plan.id
    httpsOnly: true
    publicNetworkAccess: publicNetworkAccess
    virtualNetworkSubnetId: empty(appsSubnetId) ? null : appsSubnetId
    vnetRouteAllEnabled: !empty(appsSubnetId)
    siteConfig: {
      minTlsVersion: '1.2'
      ftpsState: 'Disabled'
      netFrameworkVersion: 'v8.0'
      appSettings: concat([
        { name: 'APP_KIND', value: 'workflowApp' }
        { name: 'FUNCTIONS_EXTENSION_VERSION', value: '~4' }
        { name: 'FUNCTIONS_WORKER_RUNTIME', value: 'dotnet' }
        { name: 'AzureFunctionsJobHost__extensionBundle__id', value: 'Microsoft.Azure.Functions.ExtensionBundle.Workflows' }
        { name: 'AzureFunctionsJobHost__extensionBundle__version', value: '[1.*, 2.0.0)' }
        { name: 'AzureWebJobsStorage__accountName', value: runtimeStorage.name }
        { name: 'AzureWebJobsStorage__credential', value: 'managedidentity' }
        { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: appInsightsConnectionString }
        { name: 'WEBSITE_CONTENTOVERVNET', value: empty(appsSubnetId) ? '0' : '1' }
        // Workflow parameters (workflows/README.md "Parameterisation") read via appsetting():
        { name: 'FOUNDRY_ENDPOINT', value: projectEndpoint }
        { name: 'FOUNDRY_API_VERSION', value: foundryApiVersion }
        { name: 'DELIVERY_FUNCTION_BASE_URL', value: deliveryFunctionBaseUrl }
        { name: 'KEY_VAULT_NAME', value: keyVaultName }
      ], secretSettings)
    }
  }
}

// Runtime-storage, Key Vault and Foundry roles: workload-rbac.bicep.

resource diagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: 'to-log-analytics'
  scope: logicApp
  properties: {
    workspaceId: logAnalyticsId
    logs: [{ category: 'WorkflowRuntime', enabled: true }, { category: 'FunctionAppLogs', enabled: true }]
    metrics: [{ category: 'AllMetrics', enabled: true }]
  }
}

output logicAppName string = logicApp.name
output logicAppId string = logicApp.id
output logicAppPrincipalId string = logicApp.identity.principalId
output runtimeStorageAccountName string = runtimeStorage.name
