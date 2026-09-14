// One private endpoint + DNS zone group. Reused by main.bicep for the Foundry
// account, Key Vault, storage accounts and the App Service-hosted workloads.

@description('Name of the private endpoint')
param name string

param location string

@description('Resource id of the private-link target')
param targetResourceId string

@description('Private-link group id (account | blob | queue | table | vault | sites)')
param groupId string

param subnetId string

@description('Private DNS zone ids to register the endpoint in')
param privateDnsZoneIds array

resource pe 'Microsoft.Network/privateEndpoints@2024-01-01' = {
  name: name
  location: location
  properties: {
    subnet: { id: subnetId }
    privateLinkServiceConnections: [
      { name: name, properties: { privateLinkServiceId: targetResourceId, groupIds: [groupId] } }
    ]
  }
}

resource zoneGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2024-01-01' = {
  parent: pe
  name: 'default'
  properties: {
    privateDnsZoneConfigs: [for (z, i) in privateDnsZoneIds: { name: 'zone${i}', properties: { privateDnsZoneId: z } }]
  }
}

output id string = pe.id
