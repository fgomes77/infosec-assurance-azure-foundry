// Delivery layer hosting: the delivery Function App (functions/delivery —
// ensure_folder / upload / render, the ONLY SharePoint writer) and the optional
// office-tools Function App (functions/office-tools — LibreOffice, pandoc,
// poppler, qpdf, tesseract, ImageMagick, Node 20 renderers) that replaces the
// claude.ai sandbox toolchain the docx/pdf/pptx/xlsx skills assume.
//
// Both run as Linux CUSTOM CONTAINERS on one Elastic Premium plan: a Flex
// Consumption Python app has no Node runtime, so pptxgenjs/docx renderers and
// the LibreOffice conversions cannot run there (fidelity requirement). Images
// are built from functions/<app>/Dockerfile into the private registry below
// (see README §Delivery). System-assigned managed identities everywhere; no keys.

param baseName string
param location string
param logAnalyticsId string
param appInsightsConnectionString string

@description('Foundry project endpoint (app setting PROJECT_ENDPOINT)')
param projectEndpoint string

@description('Key Vault name (app settings reference secrets by name only)')
param keyVaultName string

@description('Document Intelligence data-plane API version used by /api/extract_pdf (v4.0 GA).')
param docIntelApiVersion string = '2024-11-30'

@description('Per-call timeout, in seconds, for Document Intelligence reads from the delivery Function.')
param docIntelTimeoutSeconds int = 120

@description('Document Intelligence endpoint (empty = OCR disabled)')
param documentIntelligenceEndpoint string = ''

@description('Container image for functions/delivery, e.g. {registry}.azurecr.io/infosec-delivery:{tag}. Empty = deploy the app with the placeholder image and push later')
param deliveryImage string = ''

@description('Container image for functions/office-tools. Empty = office-tools app not deployed')
param officeToolsImage string = ''

@description('Elastic Premium plan SKU (EP1 is enough for the five-user team)')
@allowed(['EP1', 'EP2', 'EP3'])
param planSku string = 'EP1'

@description('Subnet id for VNet integration (empty = no VNet integration)')
param appsSubnetId string = ''

@description('Public network access on the function apps (Disabled = private endpoints only)')
@allowed(['Enabled', 'Disabled'])
param publicNetworkAccess string = 'Enabled'

@description('CIDR/subnet allowed to call the endpoints when public access is Enabled (Logic Apps outbound); empty = no restriction')
param callerSubnetId string = ''

@description('SharePoint site id / drive id placeholders (setup/.env)')
param sharepointSiteId string = '{sharepoint-site-id}'
param sharepointReportsDriveId string = '{sharepoint-reports-drive-id}'

var placeholderImage = 'mcr.microsoft.com/azure-functions/python:4-python3.11'
var apps = concat(
  [{ name: '${baseName}-delivery', image: empty(deliveryImage) ? placeholderImage : deliveryImage, kind: 'delivery' }],
  empty(officeToolsImage) ? [] : [{ name: '${baseName}-office', image: officeToolsImage, kind: 'office' }]
)

// ------------------------------------------------------------ registry
resource acr 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: toLower(replace('${baseName}acr', '-', ''))
  location: location
  sku: { name: 'Basic' } // Premium if the registry itself must sit behind a private endpoint
  properties: {
    adminUserEnabled: false // managed-identity pull only
    publicNetworkAccess: 'Enabled'
  }
}

// ---------------------------------------------- runtime storage (identity-based)
resource runtimeStorage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: toLower(replace('${baseName}fnsa', '-', ''))
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

// ------------------------------------------------------------- plan
resource plan 'Microsoft.Web/serverfarms@2023-12-01' = {
  name: '${baseName}-fn-plan'
  location: location
  kind: 'elastic'
  sku: { name: planSku, tier: 'ElasticPremium' }
  properties: { reserved: true, maximumElasticWorkerCount: 3 }
}

// ------------------------------------------------------------- apps
resource functionApps 'Microsoft.Web/sites@2023-12-01' = [for a in apps: {
  name: a.name
  location: location
  kind: 'functionapp,linux,container'
  identity: { type: 'SystemAssigned' }
  properties: {
    serverFarmId: plan.id
    httpsOnly: true
    publicNetworkAccess: publicNetworkAccess
    virtualNetworkSubnetId: empty(appsSubnetId) ? null : appsSubnetId
    vnetRouteAllEnabled: !empty(appsSubnetId)
    siteConfig: {
      linuxFxVersion: 'DOCKER|${a.image}'
      acrUseManagedIdentityCreds: true
      minTlsVersion: '1.2'
      ftpsState: 'Disabled'
      http20Enabled: true
      alwaysOn: false
      ipSecurityRestrictionsDefaultAction: empty(callerSubnetId) ? 'Allow' : 'Deny'
      ipSecurityRestrictions: empty(callerSubnetId) ? [] : [
        { name: 'logic-apps-subnet', action: 'Allow', priority: 100, vnetSubnetResourceId: callerSubnetId }
      ]
      appSettings: concat([
        { name: 'FUNCTIONS_EXTENSION_VERSION', value: '~4' }
        { name: 'FUNCTIONS_WORKER_RUNTIME', value: 'python' }
        { name: 'AzureWebJobsStorage__accountName', value: runtimeStorage.name }
        { name: 'AzureWebJobsStorage__credential', value: 'managedidentity' }
        { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: appInsightsConnectionString }
        { name: 'WEBSITE_CONTENTOVERVNET', value: empty(appsSubnetId) ? '0' : '1' }
        { name: 'DOCKER_REGISTRY_SERVER_URL', value: 'https://${acr.properties.loginServer}' }
        { name: 'PROJECT_ENDPOINT', value: projectEndpoint }
        { name: 'KEY_VAULT_NAME', value: keyVaultName }
        { name: 'SHAREPOINT_SITE_ID', value: sharepointSiteId }
        { name: 'SHAREPOINT_REPORTS_DRIVE_ID', value: sharepointReportsDriveId }
        { name: 'DOCINTEL_ENDPOINT', value: documentIntelligenceEndpoint }
        { name: 'DOCINTEL_API_VERSION', value: docIntelApiVersion }
        { name: 'DOCINTEL_TIMEOUT_SECONDS', value: string(docIntelTimeoutSeconds) }
        { name: 'ENX_DATA_BOUNDARY', value: 'EU' } // asserted by main.bicep @allowed location
      ],
      // OFFICE_TOOLS_BASE_URL + OFFICE_TOOLS_KEY are the ONLY link between the
      // two apps, and they sit on the CALLER (delivery) alone. The office-tools
      // app is the callee: it holds no credential of any kind, makes no
      // outbound call, and is granted nothing in workload-rbac.bicep beyond
      // AcrPull — no Graph, no Foundry, no Document Intelligence. Giving it its
      // own function key here would be giving the callee a key to itself.
      a.kind == 'delivery' ? [
        { name: 'OFFICE_TOOLS_BASE_URL', value: empty(officeToolsImage) ? '' : 'https://${baseName}-office.azurewebsites.net/api' }
        // /api/render's xlsx recalc gate sends this as the x-functions-key
        // header to the office-tools app.
        { name: 'OFFICE_TOOLS_KEY', value: '@Microsoft.KeyVault(VaultName=${keyVaultName};SecretName=office-tools-function-key)' }
      ] : []
      )
    }
  }
}]

// Role assignments for the app identities live in workload-rbac.bicep
// (principal ids must be deployment-time constants for assignment names).

resource diagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = [for (a, i) in apps: {
  name: 'to-log-analytics'
  scope: functionApps[i]
  properties: {
    workspaceId: logAnalyticsId
    logs: [{ category: 'FunctionAppLogs', enabled: true }]
    metrics: [{ category: 'AllMetrics', enabled: true }]
  }
}]

output deliveryFunctionName string = functionApps[0].name
output deliveryFunctionPrincipalId string = functionApps[0].identity.principalId
output deliveryFunctionId string = functionApps[0].id
output deliveryFunctionBaseUrl string = 'https://${functionApps[0].properties.defaultHostName}/api'
output officeToolsFunctionName string = empty(officeToolsImage) ? '' : functionApps[1].name
output registryLoginServer string = acr.properties.loginServer
output runtimeStorageAccountName string = runtimeStorage.name
output officeToolsPrincipalId string = empty(officeToolsImage) ? '' : functionApps[1].identity.principalId
output registryId string = acr.id
output planId string = plan.id
