// Azure Policy assignments for the InfoSec Assurance Foundry resource group —
// PREVENTIVE enforcement of the residency / identity / network rules that
// infra/validate.sh only checks client-side (ENTERPRISE_BLUEPRINT.md decision
// POL-1). Resource-group scope so the workload owner can deploy it without
// subscription rights; the landing-zone team may lift the same assignments to
// the subscription or management group (baseline-microsoft-foundry-landing-zone,
// GA guidance 2026-06-19).
//
// Sources: Azure Policy built-ins for Azure AI services
//   https://learn.microsoft.com/en-us/azure/ai-services/policy-reference (2026-07-13, GA)
//   Control Plane compliance policies: control-plane/how-to-manage-compliance-security (2026-08-04)
//   Deployment types / EU Data Zone: foundry-models/concepts/deployment-types (2026-08-12)
//
// Policy definition GUIDs: the two marked CONFIRMED were read from the
// policy-reference page during the 2026-09-12 research pass; every other GUID
// is a well-known built-in recalled from memory and MUST be verified before
// the first deployment with
//   az policy definition list --query "[?displayName=='<name>'].{n:name,d:displayName}" -o table
// The custom "deny global SKU" definition is created once at subscription
// scope (policy definitions cannot live in a resource group) — see the
// az CLI block at the end of this file — and its id is passed as a parameter.
//
// Effects: `Deny` in prod, `Audit` in dev (parameter `effectMode`) so what-if
// runs and dev experiments are not blocked. Deny policies evaluate ARM
// requests only: existing non-compliant resources show as non-compliant and
// are fixed by redeploying main.bicep, never by hand.

targetScope = 'resourceGroup'

@description('Deny in prod; Audit in dev')
@allowed(['Audit', 'Deny'])
param effectMode string = 'Deny'

@description('EU regions allowed for every resource in the RG (mirrors the @allowed list of main.bicep location)')
param allowedLocations array = [
  'swedencentral'
  'westeurope'
  'northeurope'
  'francecentral'
  'germanywestcentral'
  'italynorth'
  'spaincentral'
  'polandcentral'
  'norwayeast'
  'switzerlandnorth'
  'global' // Bing grounding + private DNS zones are global resources (accepted, README §Residency)
]

@description('Resource id of the custom definition "Foundry deployments must not use Global SKUs" (created at subscription scope with the CLI block below). Empty = skip that assignment')
param denyGlobalSkuDefinitionId string = ''

@description('Assign the CMK audit policy (Audit only — CMK is rolled out by landing-zone.bicep + main.bicep delta D-EB4)')
param auditCmk bool = true

// ---------------------------------------------------------------- built-ins
// name = displayName as of the policy-reference page; guid = definition name.
var builtins = {
  // CONFIRMED (policy-reference, 2026-07-13): "Azure AI Services resources should restrict network access" — Audit/Deny
  aiRestrictNetworkAccess: '037eea7a-bd0a-46c5-9a66-03aea78705d3'
  // CONFIRMED (policy-reference, 2026-07-13): "Azure AI Services resources should use Azure Private Link" — Audit
  aiPrivateLink: 'd6759c02-b87f-42b7-892e-71b3f471d782'
  // VERIFY: "Azure AI Services resources should have key access disabled (disable local authentication)" — Audit/Deny
  aiDisableLocalAuth: '71ef260a-8f18-47b7-abcb-62d0673d94dc'
  // VERIFY: "Azure AI Services resources should encrypt data at rest with a customer-managed key (CMK)" — Audit
  aiCmk: '67121cc7-ff39-4ab8-b7e3-95b84dab487d'
  // VERIFY: "Allowed locations" — Deny
  allowedLocations: 'e56962a6-4747-49cd-b67b-bf8b01975c4c'
  // VERIFY: "Key vaults should have deletion protection enabled" (purge protection) — Audit/Deny
  kvPurgeProtection: '0b60c0b2-2dc2-4e1c-b5c9-abbed971de53'
  // VERIFY: "Key vaults should have soft delete enabled" — Audit/Deny
  kvSoftDelete: '1e66c121-a66a-4b1f-9b83-0fd99bf0fc2d'
  // VERIFY: "Azure Key Vault should use private link" — Audit
  kvPrivateLink: 'a6abeaec-4d90-4a02-805f-6b26c4d3fbe9'
  // VERIFY: "Storage accounts should restrict network access" — Audit/Deny
  storageRestrictNetwork: '34c877ad-507e-4c82-993e-3452a6e0ad3c'
  // VERIFY: "Storage accounts should prevent shared key access" — Audit/Deny
  storageNoSharedKey: '8c6a50c6-9ffd-4ae7-986f-5fa6111f9a54'
  // VERIFY: "Storage accounts should use private link" — Audit
  storagePrivateLink: '6edd7eda-6dd8-40f7-810d-67160c639cd9'
}
func defId(name string) string => tenantResourceId('Microsoft.Authorization/policyDefinitions', name)

// Assignments that take an `effect` parameter (Audit | Deny)
var effectAssignments = [
  { key: 'ai-restrict-network', def: builtins.aiRestrictNetworkAccess, name: 'Foundry/Azure AI resources must restrict network access (publicNetworkAccess Disabled or networkAcls Deny)' }
  { key: 'ai-no-local-auth', def: builtins.aiDisableLocalAuth, name: 'Foundry/Azure AI resources must have local (key) authentication disabled — Entra ID only (disableLocalAuth=true, main.bicep)' }
  { key: 'kv-purge-protection', def: builtins.kvPurgeProtection, name: 'Key Vault purge protection required (CMK + evidence custody)' }
  { key: 'kv-soft-delete', def: builtins.kvSoftDelete, name: 'Key Vault soft delete required' }
  { key: 'sa-restrict-network', def: builtins.storageRestrictNetwork, name: 'Storage accounts must restrict network access' }
  { key: 'sa-no-shared-key', def: builtins.storageNoSharedKey, name: 'Storage accounts must prevent shared-key access (identity-based only)' }
]

resource effectPolicies 'Microsoft.Authorization/policyAssignments@2024-04-01' = [for a in effectAssignments: {
  name: 'infosec-foundry-${a.key}'
  properties: {
    displayName: a.name
    policyDefinitionId: defId(a.def)
    parameters: { effect: { value: effectMode } }
    enforcementMode: 'Default'
    nonComplianceMessages: [{ message: 'InfoSec Assurance Foundry platform policy (enterprise/azure-policy-assignments.bicep): ${a.name}. Fix by redeploying infra/main.bicep, not by hand.' }]
  }
}]

// Audit-only assignments (built-ins that offer Audit/Disabled only)
var auditAssignments = concat([
  { key: 'ai-private-link', def: builtins.aiPrivateLink, name: 'Foundry/Azure AI resources should use Private Link (audit; inbound only — agent egress is a separate control, NET-1)' }
  { key: 'kv-private-link', def: builtins.kvPrivateLink, name: 'Key Vault should use Private Link (audit)' }
  { key: 'sa-private-link', def: builtins.storagePrivateLink, name: 'Storage accounts should use Private Link (audit)' }
], auditCmk ? [
  { key: 'ai-cmk', def: builtins.aiCmk, name: 'Foundry/Azure AI resources should encrypt data at rest with a customer-managed key (audit until D-EB4 is applied)' }
] : [])

resource auditPolicies 'Microsoft.Authorization/policyAssignments@2024-04-01' = [for a in auditAssignments: {
  name: 'infosec-foundry-${a.key}'
  properties: {
    displayName: a.name
    policyDefinitionId: defId(a.def)
    enforcementMode: 'Default'
  }
}]

// EU residency: every resource in the RG must sit in an allowed region.
resource allowedLocationsPolicy 'Microsoft.Authorization/policyAssignments@2024-04-01' = {
  name: 'infosec-foundry-allowed-locations'
  properties: {
    displayName: 'EU residency — allowed locations for rg-infosec-foundry (README §Residency; DORA Art. 28 / GDPR Art. 28 evidence)'
    policyDefinitionId: defId(builtins.allowedLocations)
    parameters: { listOfAllowedLocations: { value: allowedLocations } }
    enforcementMode: 'Default'
    nonComplianceMessages: [{ message: 'Resource location is outside the EU allow-list of infra/main.bicep. Only Bing grounding and private DNS zones may be global.' }]
  }
}

// Model-deployment SKU: DataZoneStandard (EU Data Zone) or Standard only.
// GlobalStandard / GlobalProvisionedManaged / GlobalBatch route inference
// worldwide (deployment-types, 2026-08-12) and are denied. Custom definition
// created once at subscription scope (CLI block below).
resource denyGlobalSku 'Microsoft.Authorization/policyAssignments@2024-04-01' = if (!empty(denyGlobalSkuDefinitionId)) {
  name: 'infosec-foundry-deny-global-sku'
  properties: {
    displayName: 'Foundry model deployments must use DataZoneStandard/Standard SKUs (no Global*)'
    policyDefinitionId: denyGlobalSkuDefinitionId
    parameters: { effect: { value: effectMode } }
    enforcementMode: 'Default'
    nonComplianceMessages: [{ message: 'Global* deployment SKUs process prompts outside the EU Data Zone and are not allowed (main.bicep deploymentSku).' }]
  }
}

var effectNames = [for a in effectAssignments: 'infosec-foundry-${a.key}']
var auditNames = [for a in auditAssignments: 'infosec-foundry-${a.key}']
output assignmentNames array = concat(
  effectNames,
  auditNames,
  ['infosec-foundry-allowed-locations'],
  empty(denyGlobalSkuDefinitionId) ? [] : ['infosec-foundry-deny-global-sku']
)

/*
One-time custom definition (subscription scope, run by the landing-zone team
or the owner under a PIM `Resource Policy Contributor` window), then pass the
printed id as `denyGlobalSkuDefinitionId`:

az policy definition create --name infosec-foundry-deny-global-sku \
  --display-name "Foundry model deployments must not use Global SKUs" \
  --mode All --subscription {subscriptionId} \
  --params '{"effect":{"type":"String","allowedValues":["Audit","Deny","Disabled"],"defaultValue":"Deny"}}' \
  --rules '{
    "if": { "allOf": [
      { "field": "type", "equals": "Microsoft.CognitiveServices/accounts/deployments" },
      { "field": "Microsoft.CognitiveServices/accounts/deployments/sku.name",
        "in": ["GlobalStandard", "GlobalProvisionedManaged", "GlobalBatch"] }
    ] },
    "then": { "effect": "[parameters(\'effect\')]" }
  }'
az policy definition show --name infosec-foundry-deny-global-sku --query id -o tsv

Verify a built-in GUID before first use:
az policy definition show --name 037eea7a-bd0a-46c5-9a66-03aea78705d3 --query displayName -o tsv
*/
