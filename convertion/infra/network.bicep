// Network isolation for the InfoSec Assurance Foundry platform (requirement i).
// VNet + delegated subnets for the App Service-hosted workloads (delivery
// Function, Logic Apps Standard), the Container Apps environment (hosted MCP),
// the AGENT EGRESS subnet (snet-agents) and the private endpoints; private DNS
// zones for every private link used by main.bicep. Called as a module from
// main.bicep when enablePrivateNetworking is true. Egress FQDN allow-list:
// infra/README.md §Network (an Azure Firewall or the corporate proxy enforces
// it — NSGs cannot filter by FQDN).
//
// NET-1 / finding C12 — AGENT EGRESS: private endpoints are INBOUND only, so
// they do not cover the calls an agent's tools make (OpenAPI, MCP, A2A, Bing).
// `snet-agents` is delegated to Microsoft.App/environments and passed to the
// Foundry account as `networkInjections` BY main.bicep AT ACCOUNT/PROJECT
// CREATION — the injection cannot be added to an existing account, so the
// decision is taken before the first deployment (ENTERPRISE_BLUEPRINT NET-1;
// networking-options, GA 2026-09-09). /27 is the service minimum, /24 the
// recommendation when hosted agents run in the subnet.

@description('Base name (main.bicep baseName)')
param baseName string

@description('EU region (validated by main.bicep)')
param location string

@description('VNet address space')
param vnetAddressPrefix string = '10.60.0.0/22'

@description('Address prefix for snet-agents (BYO-VNet agent egress, NET-1/C12) — free space inside vnetAddressPrefix, RFC1918 only, /24 recommended')
param agentSubnetAddressPrefix string = '10.60.1.0/24'

var subnets = {
  privateEndpoints: '10.60.0.0/26'   // snet-pe
  apps: '10.60.0.64/26'              // snet-apps  (Function + Logic Apps VNet integration)
  agents: agentSubnetAddressPrefix   // snet-agents (agent tool egress, delegated Microsoft.App/environments)
  containerApps: '10.60.2.0/23'      // snet-aca   (Container Apps environment, /23 minimum)
}

resource nsgApps 'Microsoft.Network/networkSecurityGroups@2024-01-01' = {
  name: '${baseName}-nsg-apps'
  location: location
  properties: {
    securityRules: [
      {
        name: 'deny-inbound-internet'
        properties: { priority: 4000, direction: 'Inbound', access: 'Deny', protocol: '*', sourceAddressPrefix: 'Internet', sourcePortRange: '*', destinationAddressPrefix: '*', destinationPortRange: '*' }
      }
      {
        // Outbound to Azure platform services (Graph, Foundry, Key Vault, Storage) and the
        // corporate egress route; FQDN filtering for the third-party APIs (Jira, OneTrust,
        // SecurityScorecard, IAF, ENX gateway) is enforced by the firewall/proxy, see README.
        name: 'allow-outbound-https'
        properties: { priority: 100, direction: 'Outbound', access: 'Allow', protocol: 'Tcp', sourceAddressPrefix: '*', sourcePortRange: '*', destinationAddressPrefix: '*', destinationPortRange: '443' }
      }
      {
        name: 'deny-outbound-other'
        properties: { priority: 4000, direction: 'Outbound', access: 'Deny', protocol: '*', sourceAddressPrefix: '*', sourcePortRange: '*', destinationAddressPrefix: 'Internet', destinationPortRange: '*' }
      }
    ]
  }
}

// Agent egress NSG (FW-1): no inbound from the internet, HTTPS out only; the
// FQDN allow-list stays on the hub firewall/proxy. Same name and rules as
// enterprise/landing-zone.bicep so the two templates are idempotent together
// (set `enableAgentSubnet: false` there once this subnet is deployed here).
resource nsgAgents 'Microsoft.Network/networkSecurityGroups@2024-01-01' = {
  name: '${baseName}-nsg-agents'
  location: location
  properties: {
    securityRules: [
      {
        name: 'deny-inbound-internet'
        properties: { priority: 4000, direction: 'Inbound', access: 'Deny', protocol: '*', sourceAddressPrefix: 'Internet', sourcePortRange: '*', destinationAddressPrefix: '*', destinationPortRange: '*' }
      }
      {
        name: 'allow-outbound-https'
        properties: { priority: 100, direction: 'Outbound', access: 'Allow', protocol: 'Tcp', sourceAddressPrefix: '*', sourcePortRange: '*', destinationAddressPrefix: '*', destinationPortRange: '443' }
      }
      {
        name: 'deny-outbound-other-internet'
        properties: { priority: 4000, direction: 'Outbound', access: 'Deny', protocol: '*', sourceAddressPrefix: '*', sourcePortRange: '*', destinationAddressPrefix: 'Internet', destinationPortRange: '*' }
      }
    ]
  }
}

resource vnet 'Microsoft.Network/virtualNetworks@2024-01-01' = {
  name: '${baseName}-vnet'
  location: location
  properties: {
    addressSpace: { addressPrefixes: [vnetAddressPrefix] }
    subnets: [
      {
        name: 'snet-pe'
        properties: {
          addressPrefix: subnets.privateEndpoints
          privateEndpointNetworkPolicies: 'Disabled'
        }
      }
      {
        name: 'snet-apps'
        properties: {
          addressPrefix: subnets.apps
          networkSecurityGroup: { id: nsgApps.id }
          delegations: [{ name: 'webapps', properties: { serviceName: 'Microsoft.Web/serverFarms' } }]
        }
      }
      {
        // Agent tool egress (networkInjections target, main.bicep). Delegation
        // to Microsoft.App/environments is what the Agent Service requires.
        name: 'snet-agents'
        properties: {
          addressPrefix: subnets.agents
          networkSecurityGroup: { id: nsgAgents.id }
          delegations: [{ name: 'agents', properties: { serviceName: 'Microsoft.App/environments' } }]
        }
      }
      {
        name: 'snet-aca'
        properties: {
          addressPrefix: subnets.containerApps
          networkSecurityGroup: { id: nsgApps.id }
          delegations: [{ name: 'aca', properties: { serviceName: 'Microsoft.App/environments' } }]
        }
      }
    ]
  }
}

// Private DNS zones for every private link created by main.bicep and the modules.
var zoneNames = [
  'privatelink.cognitiveservices.azure.com'
  'privatelink.openai.azure.com'
  'privatelink.services.ai.azure.com'
  'privatelink.blob.${environment().suffixes.storage}'
  'privatelink.queue.${environment().suffixes.storage}'
  'privatelink.table.${environment().suffixes.storage}'
  'privatelink.vaultcore.azure.net'
  'privatelink.azurewebsites.net'
  'privatelink.documents.azure.com'   // Cosmos DB for NoSQL (standard agent setup, C5)
  'privatelink.search.windows.net'    // Azure AI Search (vector stores / knowledge base, C5)
]

#disable-next-line no-hardcoded-location   // private DNS zones are global resources
var dnsLocation = 'global'

resource zones 'Microsoft.Network/privateDnsZones@2024-06-01' = [for z in zoneNames: {
  name: z
  location: dnsLocation
}]

resource links 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2024-06-01' = [for (z, i) in zoneNames: {
  parent: zones[i]
  name: '${baseName}-link'
  location: dnsLocation
  properties: { virtualNetwork: { id: vnet.id }, registrationEnabled: false }
}]

output vnetId string = vnet.id
output privateEndpointSubnetId string = vnet.properties.subnets[0].id
output appsSubnetId string = vnet.properties.subnets[1].id
output agentSubnetId string = vnet.properties.subnets[2].id
output containerAppsSubnetId string = vnet.properties.subnets[3].id
output zoneIds object = {
  cognitiveservices: zones[0].id
  openai: zones[1].id
  aiservices: zones[2].id
  blob: zones[3].id
  queue: zones[4].id
  table: zones[5].id
  vault: zones[6].id
  sites: zones[7].id
  documents: zones[8].id
  search: zones[9].id
}
