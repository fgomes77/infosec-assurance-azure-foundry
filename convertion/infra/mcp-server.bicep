// Shared hosting for mcp-server/server.py (streamable HTTP) on Azure Container
// Apps: internal-only ingress inside the platform VNet (or external when no VNet
// is used), system-assigned managed identity granted Azure AI User on the
// Foundry project (main.bicep), and Entra Easy Auth restricted to the
// sg-infosec-foundry-users group. Optional (main.bicep enableMcpHosting).

param baseName string
param location string
param logAnalyticsId string
param projectEndpoint string

@description('Container image built from convertion/ with mcp-server/Dockerfile (the build context includes scripts/ — the server shares _foundry_runtime.py and memory_store.py with the deploy scripts, finding C1). Placeholder until pushed')
param image string = '{registry}.azurecr.io/infosec-mcp:{tag}'

@description('Registry login server (delivery.bicep output); AcrPull granted to the app identity')
param registryLoginServer string = ''

@description('Container Apps subnet id (network.bicep); empty = Microsoft-managed network with external ingress')
param containerAppsSubnetId string = ''

@description('Entra app registration (client id) protecting the endpoint via Easy Auth')
param easyAuthClientId string = '{app-registration-client-id}'

@description('Object id of sg-infosec-foundry-users — the only principals allowed through Easy Auth')
param allowedGroupObjectId string = '{objectId:sg-infosec-foundry-users}'

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' existing = {
  name: last(split(logAnalyticsId, '/'))
}

resource env 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: '${baseName}-cae'
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
    vnetConfiguration: empty(containerAppsSubnetId) ? null : { infrastructureSubnetId: containerAppsSubnetId, internal: true }
    zoneRedundant: false
  }
}

resource app 'Microsoft.App/containerApps@2024-03-01' = {
  name: '${baseName}-mcp'
  location: location
  identity: { type: 'SystemAssigned' }
  properties: {
    managedEnvironmentId: env.id
    configuration: {
      ingress: { external: empty(containerAppsSubnetId), targetPort: 8000, transport: 'http', allowInsecure: false }
      registries: empty(registryLoginServer) ? [] : [{ server: registryLoginServer, identity: 'system' }]
    }
    template: {
      containers: [
        {
          name: 'mcp'
          image: image
          resources: { cpu: json('0.5'), memory: '1Gi' }
          env: [
            { name: 'PROJECT_ENDPOINT', value: projectEndpoint }
            { name: 'MCP_TRANSPORT', value: 'streamable-http' }
          ]
        }
      ]
      scale: { minReplicas: 0, maxReplicas: 2 }
    }
  }
}

// Easy Auth: Entra ID only, group-restricted; unauthenticated → 401 (API clients).
resource auth 'Microsoft.App/containerApps/authConfigs@2024-03-01' = {
  parent: app
  name: 'current'
  properties: {
    platform: { enabled: true }
    globalValidation: { unauthenticatedClientAction: 'Return401' }
    identityProviders: {
      azureActiveDirectory: {
        enabled: true
        registration: {
          clientId: easyAuthClientId
          openIdIssuer: '${environment().authentication.loginEndpoint}${subscription().tenantId}/v2.0'
        }
        validation: {
          allowedAudiences: ['api://${easyAuthClientId}']
          defaultAuthorizationPolicy: { allowedPrincipals: { groups: [allowedGroupObjectId] } }
        }
      }
    }
  }
}

// AcrPull + Azure AI User for the app identity: workload-rbac.bicep.

output mcpPrincipalId string = app.identity.principalId
output mcpFqdn string = app.properties.configuration.ingress.fqdn
