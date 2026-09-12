// Deployment-time assertion helper: main.bicep passes 'ok' or an error text;
// anything but 'ok' fails validation / what-if before any resource changes.
// Each param guards one decision that cannot be corrected after deployment.
@description('publicNetworkAccess=Disabled without private endpoints would make the platform unreachable')
@allowed(['ok'])
param publicAccessCheck string

@description('C12 — agent VNet injection needs a delegated subnet; the account cannot be injected later')
@allowed(['ok'])
param agentEgressCheck string = 'ok'

@description('C22 — a CMK key URI without a key name silently falls back to platform-managed keys')
@allowed(['ok'])
param cmkCheck string = 'ok'

output check string = '${publicAccessCheck}/${agentEgressCheck}/${cmkCheck}'
