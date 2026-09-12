// enterprise/upgrade/model-deployment-policy.bicep
// Pinned, no-auto-upgrade, EU-resident model deployments for the three tiers
// (light / chat / reasoning — governance/MODEL_ROUTING.md) plus an optional
// candidate deployment used only during a reviewed model migration
// (enterprise/UPDATE_AND_UPGRADE_REVIEW_POLICY.md §1 C1, §3 R1–R3).
//
// Why a separate module: infra/main.bicep creates the same three deployments
// with `version: empty(x) ? null : x` and no versionUpgradeOption, so a
// provider-side default change could alter outputs without a review. This
// module is the target shape (shared delta D-UP-1); consume it from main.bicep
// as `module tiers 'enterprise/upgrade/model-deployment-policy.bicep' = {...}`
// (delete the three inline deployments in the same PR) or deploy it alone
// against an existing account for a migration window.
//
// Sources (status as of 2026-09-12):
//   versionUpgradeOption semantics — https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/working-with-models (2026-06-05, GA)
//   deployment types / EU Data Zone — https://learn.microsoft.com/en-us/azure/foundry/foundry-models/concepts/deployment-types (2026-08-12, GA)
//   api-versions for deployments      — https://learn.microsoft.com/en-us/azure/templates/microsoft.cognitiveservices/accounts/projects (2026-07-20, GA)
//   retirement schedule               — https://learn.microsoft.com/en-us/azure/foundry/openai/concepts/model-retirement-schedule (2026-09-02, GA)
//
// Rules enforced here: explicit non-empty version per tier (@minLength(1)),
// versionUpgradeOption = NoAutoUpgrade on every deployment, SKU restricted to
// DataZoneStandard / Standard (GlobalStandard refused — routes outside the EU),
// RAI policy attached, deployments created serially (service requirement).
// A retired version returns HTTP 410 — the compensating control is the
// quarterly platform currency review and enterprise/upgrade/check_model_lifecycle.py.
//
// Validate: bicep build enterprise/upgrade/model-deployment-policy.bicep
// (Bicep 0.47.x; no BCP081 expected — all types are published).

targetScope = 'resourceGroup'

@description('Existing Foundry account (Microsoft.CognitiveServices/accounts, kind AIServices) — {baseName}-aif')
param foundryAccountName string

@description('RAI policy attached to every deployment (created by infra/main.bicep)')
param raiPolicyName string = 'infosec-security-analysis'

@description('Deployment SKU. DataZoneStandard keeps inference inside the EU Data Zone; Standard = single EU region. GlobalStandard is not allowed (UPDATE_AND_UPGRADE_REVIEW_POLICY R8).')
@allowed(['DataZoneStandard', 'Standard'])
param deploymentSku string = 'DataZoneStandard'

// ------------------------------------------------------------ chat tier
@description('Chat-tier model name (registry model_tier "chat"); deployment name = model name (setup/.env MODEL_DEPLOYMENT_NAME)')
param chatModelName string = 'gpt-4o'
@minLength(1)
@description('Chat-tier model version — explicit, never empty. gpt-4o 2024-11-20 is Legacy and retires 2027-04-14 (replacement gpt-5.1) — see check_model_lifecycle.py')
param chatModelVersion string = '2024-11-20'
@allowed(['OpenAI', 'Anthropic'])
param chatModelFormat string = 'OpenAI'
@minValue(1)
param chatCapacity int = 50

// ------------------------------------------------------------ reasoning tier
@description('Reasoning-tier model name (registry model_tier "reasoning"). Must support every tool of the advisory toolset in the tool-support table (policy R4): o3-mini does NOT (no OpenAPI/MCP/Azure AI Search/SharePoint/Web Search) — re-select before production')
param reasoningModelName string = 'o3-mini'
@minLength(1)
@description('Reasoning-tier model version — explicit, never empty (kit default was empty = provider default)')
param reasoningModelVersion string = '{reasoning-model-version}'
@allowed(['OpenAI', 'Anthropic'])
param reasoningModelFormat string = 'OpenAI'
@minValue(1)
param reasoningCapacity int = 30

// ------------------------------------------------------------ light tier
@description('Light-tier model name (registry model_tier "light")')
param lightModelName string = 'gpt-4o-mini'
@minLength(1)
@description('Light-tier model version — explicit, never empty. gpt-4o-mini 2024-07-18 is Deprecated and retires 2027-04-14')
param lightModelVersion string = '2024-07-18'
@allowed(['OpenAI', 'Anthropic'])
param lightModelFormat string = 'OpenAI'
@minValue(1)
param lightCapacity int = 100

// ------------------------------------------------------------ candidate (migration window only)
@description('Create a fourth, candidate deployment for a reviewed migration (policy §2 "test" stage). Compared with run_evals.py --model-override, then the tier is switched with attach_integrations.py --only; deleted 7 days after zero requests.')
param enableCandidateDeployment bool = false
@description('Candidate deployment name — distinct from the tier deployments, e.g. {model}-candidate')
param candidateDeploymentName string = 'candidate'
param candidateModelName string = ''
param candidateModelVersion string = ''
@allowed(['OpenAI', 'Anthropic'])
param candidateModelFormat string = 'OpenAI'
@minValue(1)
param candidateCapacity int = 10

// The three tiers stay pinned: no vendor-driven upgrade ever changes what an
// agent runs on. The only way a version moves is a reviewed change to these
// parameters (UPGRADE_CHECKLIST.md) followed by a deployment under the deploy SP.
var upgradeOption = 'NoAutoUpgrade'

resource foundry 'Microsoft.CognitiveServices/accounts@2025-04-01-preview' existing = {
  name: foundryAccountName
}

resource chatDeployment 'Microsoft.CognitiveServices/accounts/deployments@2025-04-01-preview' = {
  parent: foundry
  name: chatModelName
  sku: { name: deploymentSku, capacity: chatCapacity }
  properties: {
    model: { format: chatModelFormat, name: chatModelName, version: chatModelVersion }
    versionUpgradeOption: upgradeOption
    raiPolicyName: raiPolicyName
  }
}

resource reasoningDeployment 'Microsoft.CognitiveServices/accounts/deployments@2025-04-01-preview' = {
  parent: foundry
  name: reasoningModelName
  dependsOn: [chatDeployment] // deployments must be created serially
  sku: { name: deploymentSku, capacity: reasoningCapacity }
  properties: {
    model: { format: reasoningModelFormat, name: reasoningModelName, version: reasoningModelVersion }
    versionUpgradeOption: upgradeOption
    raiPolicyName: raiPolicyName
  }
}

resource lightDeployment 'Microsoft.CognitiveServices/accounts/deployments@2025-04-01-preview' = {
  parent: foundry
  name: lightModelName
  dependsOn: [reasoningDeployment]
  sku: { name: deploymentSku, capacity: lightCapacity }
  properties: {
    model: { format: lightModelFormat, name: lightModelName, version: lightModelVersion }
    versionUpgradeOption: upgradeOption
    raiPolicyName: raiPolicyName
  }
}

resource candidateDeployment 'Microsoft.CognitiveServices/accounts/deployments@2025-04-01-preview' = if (enableCandidateDeployment && !empty(candidateModelName) && !empty(candidateModelVersion)) {
  parent: foundry
  name: candidateDeploymentName
  dependsOn: [lightDeployment]
  sku: { name: deploymentSku, capacity: candidateCapacity }
  properties: {
    model: { format: candidateModelFormat, name: candidateModelName, version: candidateModelVersion }
    versionUpgradeOption: upgradeOption
    raiPolicyName: raiPolicyName
  }
}

// ------------------------------------------------------------ outputs (feed setup/.env and check_model_lifecycle.py)
output chatDeploymentName string = chatDeployment.name
output reasoningDeploymentName string = reasoningDeployment.name
output lightDeploymentName string = lightDeployment.name
output candidateDeploymentName string = enableCandidateDeployment ? candidateDeploymentName : ''
output pinnedDeployments array = [
  { tier: 'chat', name: chatModelName, version: chatModelVersion, format: chatModelFormat, sku: deploymentSku, upgrade: upgradeOption }
  { tier: 'reasoning', name: reasoningModelName, version: reasoningModelVersion, format: reasoningModelFormat, sku: deploymentSku, upgrade: upgradeOption }
  { tier: 'light', name: lightModelName, version: lightModelVersion, format: lightModelFormat, sku: deploymentSku, upgrade: upgradeOption }
]
