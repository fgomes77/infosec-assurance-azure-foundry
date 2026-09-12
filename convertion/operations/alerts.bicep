// Monitoring alerts for the InfoSec Assurance Foundry platform
// (operations/MONITORING.md §4 alert catalogue; runbook: operations/RUNBOOK.md).
//
// Defender for Cloud AI threat-protection alerts (finding C17) are routed by
// infra/monitoring.bicep to the SOC action group `{baseName}-ag-soc` (rules
// `{baseName}-defender-ai-high` / `-other` on activity-log category Security);
// this file covers the LOG-QUERY alerts only. Do NOT add a second Defender
// rule here - two alert catalogues on one signal means duplicate pages.
//
// Deploy at resource-group scope AFTER infra/main.bicep (needs the Log Analytics
// workspace and the Foundry account it created), as a module (delta D-OPS-B1 in
// MONITORING.md §7) or standalone:
//   az deployment group what-if -g {rg} -f alerts.bicep \
//       -p logAnalyticsName={baseName}-logs foundryAccountName={baseName}-aif \
//          ownerAlertEmail={email:sg-infosec-foundry-owner}
//
// Rules encoded here (controls in brackets):
//   - every alert notifies ONE action group owned by the platform owner group
//     (sg-infosec-foundry-owner); severity 1 also pages the SOC on-call webhook
//     [ISO 27001:2022 A.5.24, A.8.16; DORA Art. 10(1), 17; NIS2 Art. 21(2)(b)]
//   - log-query alerts are read-only over the workspace; nothing here grants
//     write access anywhere [A.8.2 — monitoring needs no privilege]
//   - queries live next to this file (kql/*.kql) so the same text is used by the
//     alert rule, the workbook and the runbook — one source [A.8.9]
//   - break-glass detective controls named in operations/access-governance/BREAK_GLASS.md §4
//     (`breakglass_window_write`, `agent_modified_by_non_deploy_identity`) are
//     implemented here [A.8.2, A.8.15; DORA Art. 9(4)(c)]
//   - skipQueryValidation is on: tables such as LogicAppWorkflowRuntime only exist
//     once diagnostic settings have shipped data (MONITORING.md §2 delta D-OPS-B2)
//
// Placeholders in {braces}; no real e-mail addresses, hostnames or object ids.

targetScope = 'resourceGroup'

@description('Log Analytics workspace created by infra/main.bicep ({baseName}-logs)')
param logAnalyticsName string

@description('Foundry account created by infra/main.bicep ({baseName}-aif) — metric alerts scope')
param foundryAccountName string

@description('Region of the workspace (scheduled query rules must be co-located)')
param location string = resourceGroup().location

@description('Distribution address of the owner group — placeholder, never a personal mailbox')
param ownerAlertEmail string = '{email:sg-infosec-foundry-owner}'

@description('Optional Teams incoming-webhook for {teams:infosec-assurance-platform}; empty = e-mail only')
@secure()
param teamsWebhookUrl string = ''

@description('Optional SOC on-call webhook for severity-1 alerts ({group:soc-oncall}); empty = none')
@secure()
param socWebhookUrl string = ''

@description('Principal id (object id) of the deploy service principal {app:infosec-foundry-deployer}; ARM writes by any other caller raise breakglass_window_write')
param deployerPrincipalId string = '{objectId:infosec-foundry-deployer}'

@description('Name prefix for alert resources')
param alertPrefix string = 'infosec-foundry'

@description('Verifier FAIL-rate threshold used in the runbook text (the query carries its own copy)')
param verifierFailRateThreshold string = '0.30'

@description('Daily Azure OpenAI token budget for the whole account (metric alert)')
param dailyTokenBudget int = 20000000

@description('Enable every rule (set false to deploy the action group only)')
param enableAlerts bool = true

// ------------------------------------------------------------- existing scopes
resource workspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' existing = {
  name: logAnalyticsName
}

resource foundry 'Microsoft.CognitiveServices/accounts@2025-04-01-preview' existing = {
  name: foundryAccountName
}

// ---------------------------------------------------------------- action groups
resource ownerActionGroup 'Microsoft.Insights/actionGroups@2023-01-01' = {
  name: '${alertPrefix}-ag-owner'
  location: 'global'
  properties: {
    groupShortName: 'isf-owner'
    enabled: true
    emailReceivers: [
      {
        name: 'platform-owner-group'
        emailAddress: ownerAlertEmail
        useCommonAlertSchema: true
      }
    ]
    webhookReceivers: empty(teamsWebhookUrl) ? [] : [
      {
        name: 'teams-platform-channel'
        serviceUri: teamsWebhookUrl
        useCommonAlertSchema: true
      }
    ]
  }
}

resource socActionGroup 'Microsoft.Insights/actionGroups@2023-01-01' = if (!empty(socWebhookUrl)) {
  name: '${alertPrefix}-ag-soc'
  location: 'global'
  properties: {
    groupShortName: 'isf-soc'
    enabled: true
    webhookReceivers: [
      {
        name: 'soc-oncall'
        serviceUri: socWebhookUrl
        useCommonAlertSchema: true
      }
    ]
  }
}

var sev1Actions = empty(socWebhookUrl) ? [ownerActionGroup.id] : [ownerActionGroup.id, socActionGroup!.id]
var ownerActions = [ownerActionGroup.id]

// ------------------------------------------------ inline detective queries
// Human-caller ARM writes in this resource group. Expected only inside a PIM or
// break-glass window; the owner reconciles hits against PIM activations
// (BREAK_GLASS.md §2 step 6).
var kqlBreakglassWriteRaw = '''
AzureActivity
| where TimeGenerated > ago(1h)
| where CategoryValue == "Administrative" and ActivityStatusValue in ("Success", "Succeeded")
| where OperationNameValue endswith "/write" or OperationNameValue endswith "/delete" or OperationNameValue endswith "/action"
| where ResourceGroup =~ "__RG__"
| where Caller !~ "__DEPLOYER__" and CallerIpAddress != ""
| project TimeGenerated, Caller, OperationNameValue, ResourceId = _ResourceId, CorrelationId
'''

// Agent / connection definition changes on the Foundry data plane by a caller other
// than the deploy identity (agents are created only by deploy.sh via OIDC).
// Column names verified at first deployment (RUNBOOK.md §2 check H9).
var kqlAgentModifiedRaw = '''
AzureDiagnostics
| where TimeGenerated > ago(1h)
| where ResourceProvider =~ "MICROSOFT.COGNITIVESERVICES"
| where Category in ("Audit", "RequestResponse")
| where OperationName has_any ("assistants", "agents", "connections", "vector_stores")
| where properties_s has_any ("POST", "PUT", "PATCH", "DELETE")
| where isempty(column_ifexists("identity_claim_appid_g", "")) or column_ifexists("identity_claim_appid_g", "") !~ "__DEPLOYER__"
| project TimeGenerated, OperationName, CallerIPAddress, identity = column_ifexists("identity_claim_appid_g", ""), Resource
'''

// Multi-line strings do not interpolate in Bicep: tokens are substituted here.
var kqlBreakglassWrite = replace(replace(kqlBreakglassWriteRaw, '__RG__', resourceGroup().name), '__DEPLOYER__', deployerPrincipalId)
var kqlAgentModified = replace(kqlAgentModifiedRaw, '__DEPLOYER__', deployerPrincipalId)

// Key Vault secret VALUE reads by a human (UPN claim present). Workload identities
// read secrets routinely; a human read means a PIM window and triggers rotation
// (BREAK_GLASS.md §2 step 7; TEAM_MODEL.md §5 L3).
var kqlKvHumanSecretGet = '''
AzureDiagnostics
| where TimeGenerated > ago(1h)
| where ResourceType == "VAULTS" and Category == "AuditEvent"
| where OperationName in ("SecretGet", "SecretList", "SecretPurge")
| extend upn = column_ifexists("identity_claim_http_schemas_xmlsoap_org_ws_2005_05_identity_claims_upn_s", "")
| where isnotempty(upn)
| project TimeGenerated, OperationName, upn, ResultSignature, Resource, CallerIPAddress
'''

// Delivery-pipeline runs that failed or timed out (any workflow in workflows/).
var kqlPipelineFailed = '''
LogicAppWorkflowRuntime
| where TimeGenerated > ago(1h)
| where OperationName =~ "Microsoft.Logic/workflows/workflowRunCompleted"
| where Status in ("Failed", "TimedOut", "Cancelled")
| project TimeGenerated, WorkflowName, RunId, Status, Error = column_ifexists("Error", "")
'''

// Delivery Function 5xx (render / ensure_folder / upload) — the only writer to
// SharePoint; failures here block every pipeline after approval.
var kqlFunction5xx = '''
AppRequests
| where TimeGenerated > ago(1h)
| where AppRoleName has "fn-delivery" or Name has_any ("render", "ensure_folder", "upload")
| where Success == false and toint(ResultCode) >= 500
| project TimeGenerated, AppRoleName, Name, ResultCode, DurationMs, OperationId
'''

// ----------------------------------------------------------- log-query rules
var logRules = [
  {
    name: 'egress-internal-marker'
    displayName: 'Egress: Bing grounding query carries an internal marker'
    description: 'governance/DATA_PROTECTION_GUARDRAILS.md §1 detective layer. RUNBOOK FM-03. Open a review ticket; fix the pattern forward.'
    severity: 1
    frequency: 'PT15M'
    window: 'PT1H'
    query: loadTextContent('kql/egress-detection.kql')
    actions: sev1Actions
  }
  {
    name: 'verifier-fail-rate'
    displayName: 'Quality: output-verifier FAIL rate above ${verifierFailRateThreshold} on a pipeline'
    description: 'ARCHITECTURE.md metrics; MODEL_ROUTING.md rule 7. RUNBOOK FM-08: knowledge/instruction drift or tier too low.'
    severity: 2
    frequency: 'PT1H'
    window: 'P1D'
    query: loadTextContent('kql/verifier-fail-rate.kql')
    actions: ownerActions
  }
  {
    name: 'latency-and-token-budget'
    displayName: 'Capacity: agent p95 latency or daily token budget exceeded'
    description: 'MODEL_ROUTING.md rule 7 tuning input. RUNBOOK FM-06 / FM-07.'
    severity: 3
    frequency: 'PT1H'
    window: 'P1D'
    query: loadTextContent('kql/latency-and-tokens.kql')
    actions: ownerActions
  }
  {
    name: 'approval-sla'
    displayName: 'Oversight: approval gate pending > 48 h or expired'
    description: 'HUMAN_APPROVAL.md Layer 3; TEAM_MODEL.md §12 Tier B fallback. RUNBOOK FM-10.'
    severity: 3
    frequency: 'PT1H'
    window: 'P7D'
    query: loadTextContent('kql/approval-sla.kql')
    actions: ownerActions
  }
  {
    name: 'pipeline-run-failed'
    displayName: 'Delivery: Logic Apps pipeline run failed or timed out'
    description: 'workflows/README.md. RUNBOOK FM-09 (agent run), FM-11 (Function), FM-12 (SharePoint).'
    severity: 2
    frequency: 'PT15M'
    window: 'PT1H'
    query: kqlPipelineFailed
    actions: ownerActions
  }
  {
    name: 'delivery-function-5xx'
    displayName: 'Delivery: render/ensure_folder/upload returned 5xx'
    description: 'functions/delivery/README.md. RUNBOOK FM-11.'
    severity: 2
    frequency: 'PT15M'
    window: 'PT1H'
    query: kqlFunction5xx
    actions: ownerActions
  }
  {
    name: 'breakglass_window_write'
    displayName: 'Privileged access: ARM write by a human caller in the platform RG'
    description: 'BREAK_GLASS.md §4; TEAM_MODEL.md §12.3. Reconcile against PIM activations within 5 business days.'
    severity: 1
    frequency: 'PT15M'
    window: 'PT1H'
    query: kqlBreakglassWrite
    actions: sev1Actions
  }
  {
    name: 'agent_modified_by_non_deploy_identity'
    displayName: 'Privileged access: agent/connection changed outside deploy.sh'
    description: 'BREAK_GLASS.md §4; CHANGE_MANAGEMENT.md §6 (every agent change is a PR + deploy.sh run).'
    severity: 1
    frequency: 'PT15M'
    window: 'PT1H'
    query: kqlAgentModified
    actions: sev1Actions
  }
  {
    name: 'keyvault-human-secret-read'
    displayName: 'Privileged access: Key Vault secret value read by a human identity'
    description: 'TEAM_MODEL.md §5 L3; BREAK_GLASS.md §2 step 7 — rotate the secret after the window.'
    severity: 2
    frequency: 'PT15M'
    window: 'PT1H'
    query: kqlKvHumanSecretGet
    actions: ownerActions
  }
]

resource logAlerts 'Microsoft.Insights/scheduledQueryRules@2023-12-01' = [for rule in logRules: {
  name: '${alertPrefix}-${rule.name}'
  location: location
  kind: 'LogAlert'
  properties: {
    displayName: rule.displayName
    description: rule.description
    severity: rule.severity
    enabled: enableAlerts
    evaluationFrequency: rule.frequency
    windowSize: rule.window
    scopes: [workspace.id]
    targetResourceTypes: ['Microsoft.OperationalInsights/workspaces']
    skipQueryValidation: true
    autoMitigate: false
    checkWorkspaceAlertsStorageConfigured: false
    criteria: {
      allOf: [
        {
          query: rule.query
          timeAggregation: 'Count'
          operator: 'GreaterThan'
          threshold: 0
          failingPeriods: {
            numberOfEvaluationPeriods: 1
            minFailingPeriodsToAlert: 1
          }
        }
      ]
    }
    actions: {
      actionGroups: rule.actions
      customProperties: {
        runbook: 'convertion/operations/RUNBOOK.md'
        owner: '{upn:francisco.gomes}'
      }
    }
  }
}]

// ---------------------------------------------------------------- metric rules
// Model throttling (HTTP 429) on any deployment — capacity, not a fault.
resource throttlingAlert 'Microsoft.Insights/metricAlerts@2018-03-01' = {
  name: '${alertPrefix}-model-throttling-429'
  location: 'global'
  properties: {
    description: 'Azure OpenAI 429 responses on the Foundry account. RUNBOOK FM-05: raise modelCapacity in infra/main.parameters.json via a Tier C change.'
    severity: 3
    enabled: enableAlerts
    scopes: [foundry.id]
    evaluationFrequency: 'PT15M'
    windowSize: 'PT1H'
    targetResourceType: 'Microsoft.CognitiveServices/accounts'
    criteria: {
      'odata.type': 'Microsoft.Azure.Monitor.SingleResourceMultipleMetricCriteria'
      allOf: [
        {
          name: 'throttled-requests'
          metricNamespace: 'Microsoft.CognitiveServices/accounts'
          metricName: 'AzureOpenAIRequests'
          dimensions: [
            {
              name: 'StatusCode'
              operator: 'Include'
              values: ['429']
            }
          ]
          operator: 'GreaterThan'
          threshold: 20
          timeAggregation: 'Total'
          criterionType: 'StaticThresholdCriterion'
        }
      ]
    }
    autoMitigate: true
    actions: [
      {
        actionGroupId: ownerActionGroup.id
      }
    ]
  }
}

// Daily token budget for the whole account (FinOps guard; MODEL_ROUTING.md rule 7).
resource tokenBudgetAlert 'Microsoft.Insights/metricAlerts@2018-03-01' = {
  name: '${alertPrefix}-daily-token-budget'
  location: 'global'
  properties: {
    description: 'Processed tokens over 24 h above dailyTokenBudget. RUNBOOK FM-07 / monthly cost review (RUNBOOK §2 M2).'
    severity: 3
    enabled: enableAlerts
    scopes: [foundry.id]
    evaluationFrequency: 'PT1H'
    windowSize: 'P1D'
    targetResourceType: 'Microsoft.CognitiveServices/accounts'
    criteria: {
      'odata.type': 'Microsoft.Azure.Monitor.SingleResourceMultipleMetricCriteria'
      allOf: [
        {
          name: 'tokens-24h'
          metricNamespace: 'Microsoft.CognitiveServices/accounts'
          metricName: 'TokenTransaction'
          operator: 'GreaterThan'
          threshold: dailyTokenBudget
          timeAggregation: 'Total'
          criterionType: 'StaticThresholdCriterion'
        }
      ]
    }
    autoMitigate: true
    actions: [
      {
        actionGroupId: ownerActionGroup.id
      }
    ]
  }
}

// ---------------------------------------------------------------------- outputs
output ownerActionGroupId string = ownerActionGroup.id
output logAlertNames array = [for (rule, i) in logRules: logAlerts[i].name]
output metricAlertNames array = [throttlingAlert.name, tokenBudgetAlert.name]
