// OPTIONAL rendered hosting for approved single-file HTML dashboards
// (DeepSearch, CISO executive summary, template review pages). Default decision
// (README §Artifacts): dashboards are stored in SharePoint as downloadable
// self-contained .html (no CDN scripts) — this module exists for teams that
// need them opened as pages. Azure Static Web Apps Standard, Entra-only access
// via the built-in auth (custom OpenID provider config lives in
// staticwebapp.config.json shipped with the published HTML), EU region.

param baseName string

@description('Static Web Apps region (EU: westeurope)')
@allowed(['westeurope'])
param location string = 'westeurope'

resource swa 'Microsoft.Web/staticSites@2023-12-01' = {
  name: '${baseName}-swa'
  location: location
  sku: { name: 'Standard', tier: 'Standard' }
  identity: { type: 'SystemAssigned' }
  properties: {
    stagingEnvironmentPolicy: 'Disabled'
    allowConfigFileUpdates: true
    publicNetworkAccess: 'Enabled' // access gated by Entra auth; private endpoint optional
  }
}

output staticSiteName string = swa.name
output defaultHostname string = swa.properties.defaultHostname
