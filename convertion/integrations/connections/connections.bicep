// Foundry project connections for integrations/registry.json (conn-*).
// Module: called from infra/main.bicep AFTER the account, project and Key
// Vault exist; every secret is passed as a secure parameter sourced from
// Key Vault (keyVault.getSecret('<secret-name>')) - nothing is in this file.
// Categories: CustomKeys (API key / bearer in a named header) for the SaaS
// APIs and the Function-backed proxies; the Graph specs (defender, sharepoint,
// entra-iam, exchange) ride on the project managed identity (AAD auth, no
// secret); the delegated specs (teams, m365-personal) are OAuth2
// authorization-code clients registered in the portal (client id only).
// Least-privilege scopes per connection: ../README.md §Connections.
targetScope = 'resourceGroup'

@description('Name of the Foundry (Cognitive Services) account')
param foundryAccountName string
@description('Name of the Foundry project under the account')
param projectName string
@description('Deploy the connections that need a secret (false = MI/OAuth-only connections)')
param deployKeyedConnections bool = true

@description('Jira Cloud base URL, e.g. https://{tenant}.atlassian.net')
param jiraBaseUrl string = 'https://{jira-tenant}.atlassian.net'
@description('Jira Assets (JSM) base URL')
param jiraAssetsBaseUrl string = 'https://api.atlassian.com/jsm/assets/workspace/{workspace-id}'
@description('Confluence Cloud base URL')
param confluenceBaseUrl string = 'https://{confluence-tenant}.atlassian.net/wiki'
@description('OneTrust API base URL')
param onetrustBaseUrl string = 'https://{onetrust-tenant}.onetrust.com'
@description('SecurityScorecard API base URL')
param securityScorecardBaseUrl string = 'https://api.securityscorecard.io'
@description('Internal IAF API base URL')
param iafBaseUrl string = 'https://{iaf-api-host}/api/v1'
@description('Delivery Function base URL (osint-proxy endpoints)')
param deliveryFunctionBaseUrl string = 'https://{delivery-function}.azurewebsites.net/api'
@description('Azure DevOps organisation URL')
param azureDevOpsOrgUrl string = 'https://dev.azure.com/{organization}'
@description('ENX internal gateway MCP endpoint (finding C10: the MCP tool authenticates through this project connection instead of run-time bearer headers - see ../mcp/enx-gateway.json)')
param enxGatewayMcpUrl string = 'https://{enx-gateway-host}/mcp'
@description('Entra tenant id used for the OAuth2 delegated connections')
param tenantId string = subscription().tenantId
@description('Client id of the delegated Graph app registration (teams / m365-personal)')
param delegatedGraphClientId string = '{delegated-graph-app-client-id}'

@secure()
param jiraBasicAuth string = ''           // base64(email:api-token) of the browse-only service account
@secure()
param jiraAssetsBearer string = ''        // Assets API token (read-only)
@secure()
param confluenceBasicAuth string = ''     // base64(email:api-token), read scopes
@secure()
param onetrustApiKey string = ''          // OneTrust viewer-role key
@secure()
param securityScorecardApiKey string = '' // SSC read token
@secure()
param iafApiKey string = ''               // IAF read-only key
@secure()
param osintProxyFunctionKey string = ''   // Function key of fetch_public_page
@secure()
param azureDevOpsReaderToken string = ''  // Entra token/PAT of the Reader-only SP (prefer AAD via MI if supported)
@secure()
param enxGatewayToken string = ''         // ENX gateway bearer, read-only tool scope (Key Vault secret {kv-secret-name-enx-gateway-token})

resource foundry 'Microsoft.CognitiveServices/accounts@2025-06-01' existing = {
  name: foundryAccountName
}
resource project 'Microsoft.CognitiveServices/accounts/projects@2025-06-01' existing = {
  parent: foundry
  name: projectName
}

// ---- keyed (CustomKeys) connections: header name + secret value ----------
var keyed = [
  { name: 'conn-jira-cloud', target: jiraBaseUrl, header: 'Authorization', value: 'Basic ${jiraBasicAuth}', scope: 'Jira: browse-only service account (no create/edit/transition)' }
  { name: 'conn-jira-assets', target: jiraAssetsBaseUrl, header: 'Authorization', value: 'Bearer ${jiraAssetsBearer}', scope: 'Assets: object read + AQL only' }
  { name: 'conn-confluence', target: confluenceBaseUrl, header: 'Authorization', value: 'Basic ${confluenceBasicAuth}', scope: 'Confluence: read:content, read:space' }
  { name: 'conn-onetrust', target: onetrustBaseUrl, header: 'Authorization', value: 'Bearer ${onetrustApiKey}', scope: 'OneTrust: viewer role' }
  { name: 'conn-securityscorecard', target: securityScorecardBaseUrl, header: 'Authorization', value: 'Token ${securityScorecardApiKey}', scope: 'SSC: read' }
  { name: 'conn-iaf-api', target: iafBaseUrl, header: 'X-API-Key', value: iafApiKey, scope: 'IAF: read (no /findings POST)' }
  { name: 'conn-osint-proxy', target: deliveryFunctionBaseUrl, header: 'x-functions-key', value: osintProxyFunctionKey, scope: 'delivery Function: fetch_public_page + allowlist only' }
  { name: 'conn-azure-devops', target: azureDevOpsOrgUrl, header: 'Authorization', value: 'Bearer ${azureDevOpsReaderToken}', scope: 'Azure DevOps: Project Reader, repos read' }
  { name: 'conn-enx-gateway', target: enxGatewayMcpUrl, header: 'Authorization', value: 'Bearer ${enxGatewayToken}', scope: 'ENX gateway MCP: allow-listed read tools only (readOnlyHint=true), require_approval waiver limited to that list - ../mcp/enx-gateway.json' }
]

resource keyedConnections 'Microsoft.CognitiveServices/accounts/projects/connections@2025-06-01' = [for c in keyed: if (deployKeyedConnections) {
  parent: project
  name: c.name
  properties: {
    category: 'CustomKeys'
    target: c.target
    authType: 'CustomKeys'
    isSharedToAll: false
    credentials: { keys: { '${c.header}': c.value } }
    metadata: { readOnlyScope: c.scope, managedBy: 'integrations/connections/connections.bicep' }
  }
}]

// ---- Graph connections on the project managed identity (no secret) ------
var graphMi = [
  { name: 'conn-defender-graph', scope: 'SecurityIncident.Read.All, SecurityAlert.Read.All, ThreatHunting.Read.All, SecurityEvents.Read.All' }
  { name: 'conn-sharepoint-graph', scope: 'Sites.Selected (read grant on the InfoSec Assurance site)' }
  { name: 'conn-entra-iam', scope: 'User.Read.All, Group.Read.All, Application.Read.All, AccessReview.Read.All, RoleManagement.Read.Directory' }
  { name: 'conn-exchange-graph', scope: 'Mail.Read + Exchange application access policy restricted to the assurance shared mailbox' }
]

resource graphConnections 'Microsoft.CognitiveServices/accounts/projects/connections@2025-06-01' = [for g in graphMi: {
  parent: project
  name: g.name
  properties: {
    category: 'CustomKeys'
    target: 'https://graph.microsoft.com/v1.0'
    authType: 'ManagedIdentity'
    isSharedToAll: false
    credentials: { clientId: foundry.identity.principalId, resourceId: foundry.id }
    metadata: { readOnlyScope: g.scope, audience: 'https://graph.microsoft.com', managedBy: 'integrations/connections/connections.bicep' }
  }
}]

// ---- delegated (OAuth2 authorization-code) connections -------------------
// Finding C9: 'conn-sharepoint-grounding' (native SharePoint grounding tool,
// preview, OBO-only) is deliberately NOT created here. It is registered in
// ../registry.json with enabled=false and is created in the portal only after
// the tool reaches GA and the licence decision is taken
// (enterprise/UPDATE_AND_UPGRADE_REVIEW_POLICY.md); unattended reads keep
// conn-sharepoint-graph (managed identity, Sites.Selected) in every case.
var delegated = [
  { name: 'conn-teams-graph', scope: 'Chat.Read ChannelMessage.Read.All Team.ReadBasic.All (delegated)' }
  { name: 'conn-m365-personal', scope: 'Calendars.Read Mail.Read (delegated)' }
]

resource delegatedConnections 'Microsoft.CognitiveServices/accounts/projects/connections@2025-06-01' = [for d in delegated: {
  parent: project
  name: d.name
  properties: {
    category: 'CustomKeys'
    target: 'https://graph.microsoft.com/v1.0'
    authType: 'OAuth2'
    isSharedToAll: false
    credentials: {
      clientId: delegatedGraphClientId
      tenantId: tenantId
    }
    metadata: {
      readOnlyScope: d.scope
      obo: 'true'
      authUrl: '${environment().authentication.loginEndpoint}${tenantId}/oauth2/v2.0/authorize'
      tokenUrl: '${environment().authentication.loginEndpoint}${tenantId}/oauth2/v2.0/token'
      managedBy: 'integrations/connections/connections.bicep'
    }
  }
}]

var keyedNames = ['conn-jira-cloud', 'conn-jira-assets', 'conn-confluence', 'conn-onetrust', 'conn-securityscorecard', 'conn-iaf-api', 'conn-osint-proxy', 'conn-azure-devops', 'conn-enx-gateway']
output connectionNames array = concat(keyedNames, map(graphMi, g => g.name), map(delegated, d => d.name))
