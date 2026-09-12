// Detective controls (DATA_PROTECTION_GUARDRAILS §1 detective layer, §4
// auditability; ARCHITECTURE metrics): action group, scheduled-query alerts
// over the KQL in infra/kql/, and diagnostic settings for the platform
// resources. Queries are loaded at build time so the .kql files stay the
// single source (also usable in a workbook / Sentinel).
//
// Finding C17 / SEC-1 — Defender for Cloud AI threat protection (jailbreak,
// sensitive-data exposure, wallet abuse / credential theft) raises SECURITY
// alerts, not Log Analytics rows, so they are routed with an ACTIVITY-LOG
// alert on category `Security`: High severity to the SOC action group,
// everything else to the owner's group. The subscription plan that produces
// the alerts is enabled by infra/defender-ai.bicep (subscription scope).

param baseName string
param location string
param logAnalyticsId string

@description('Owner mailbox for alert e-mails ({placeholder})')
param ownerEmail string = '{owner-mailbox}'

@description('Optional Teams incoming-webhook / Logic App callback for alerts (leave empty to use e-mail only)')
param webhookUrl string = ''

@description('Deploy-identity app id used by the agent-drift query')
param deployServicePrincipalAppId string = '{deploy-service-principal-appid}'

@description('SOC mailbox for High-severity Defender for AI alerts ({placeholder})')
param socEmail string = '{soc-mailbox}'

@description('Create the activity-log alerts that route Defender for Cloud AI alerts to the SOC / owner (finding C17)')
param enableDefenderAiAlerts bool = true

#disable-next-line no-hardcoded-location   // action groups are global resources
var agLocation = 'global'

resource actionGroup 'Microsoft.Insights/actionGroups@2023-01-01' = {
  name: '${baseName}-ag'
  location: agLocation
  properties: {
    groupShortName: 'infosecai'
    enabled: true
    emailReceivers: [{ name: 'owner', emailAddress: ownerEmail, useCommonAlertSchema: true }]
    webhookReceivers: empty(webhookUrl) ? [] : [{ name: 'teams', serviceUri: webhookUrl, useCommonAlertSchema: true }]
  }
}

var alerts = [
  { name: 'egress-internal-markers', severity: 1, freq: 'PT1H', window: 'PT1H', threshold: 0, query: loadTextContent('kql/egress-internal-markers.kql'), desc: 'Bing grounding input carried an internal marker (DATA_PROTECTION §1) — open a review ticket, fix forward' }
  { name: 'verifier-fail-rate', severity: 3, freq: 'PT6H', window: 'P1D', threshold: 0, query: loadTextContent('kql/verifier-fail-rate.kql'), desc: 'output-verifier FAIL rate > 30 % for an agent — tier/template review (MODEL_ROUTING rule 7)' }
  { name: 'pipeline-failures', severity: 2, freq: 'PT1H', window: 'PT1H', threshold: 0, query: loadTextContent('kql/pipeline-failures.kql'), desc: 'Logic Apps pipeline failed/timed out' }
  { name: 'approval-expiry', severity: 3, freq: 'P1D', window: 'P7D', threshold: 0, query: loadTextContent('kql/approval-expiry.kql'), desc: 'Approval gate waiting > 3 days (HUMAN_APPROVAL.md)' }
  { name: 'agent-drift', severity: 2, freq: 'PT1H', window: 'PT1H', threshold: 0, query: replace(loadTextContent('kql/agent-drift.kql'), '{deploy-service-principal-appid}', deployServicePrincipalAppId), desc: 'Agent definition modified outside deploy.sh (IDENTITY_RBAC §2)' }
]

resource rules 'Microsoft.Insights/scheduledQueryRules@2023-03-15-preview' = [for a in alerts: {
  name: '${baseName}-alert-${a.name}'
  location: location
  kind: 'LogAlert'
  properties: {
    displayName: a.name
    description: a.desc
    severity: a.severity
    enabled: true
    evaluationFrequency: a.freq
    windowSize: a.window
    scopes: [logAnalyticsId]
    criteria: {
      allOf: [{ query: a.query, timeAggregation: 'Count', operator: 'GreaterThan', threshold: a.threshold }]
    }
    autoMitigate: false
    actions: { actionGroups: [actionGroup.id] }
  }
}]

// ------------------------------------------------ C17 Defender for AI routing
resource socActionGroup 'Microsoft.Insights/actionGroups@2023-01-01' = if (enableDefenderAiAlerts) {
  name: '${baseName}-ag-soc'
  location: agLocation
  properties: {
    groupShortName: 'infosecsoc'
    enabled: true
    emailReceivers: [{ name: 'soc', emailAddress: socEmail, useCommonAlertSchema: true }]
  }
}

// High: SOC on call (jailbreak attempts, sensitive-data exposure in a prompt or
// completion, wallet abuse). Medium/Low: the platform owner, triaged at the
// weekly operating rhythm (operations/RUNBOOK.md).
var defenderAlerts = [
  { key: 'high', level: 'Error', group: 'soc', desc: 'Defender for Cloud AI threat protection — High severity (jailbreak / sensitive-data exposure / wallet abuse). SOC triage, runbook: operations/RUNBOOK.md §AI threat alerts' }
  { key: 'other', level: 'Warning', group: 'owner', desc: 'Defender for Cloud AI threat protection — Medium/Low severity. Owner triage at the weekly review' }
]

resource defenderAiAlertRules 'Microsoft.Insights/activityLogAlerts@2020-10-01' = [for a in defenderAlerts: if (enableDefenderAiAlerts) {
  name: '${baseName}-defender-ai-${a.key}'
  #disable-next-line no-hardcoded-location   // activity-log alerts are global resources
  location: 'global'
  properties: {
    description: a.desc
    enabled: true
    scopes: [subscription().id]
    condition: {
      allOf: [
        { field: 'category', equals: 'Security' }
        { field: 'level', equals: a.level }
      ]
    }
    actions: {
      actionGroups: [{ actionGroupId: a.group == 'soc' ? socActionGroup.id : actionGroup.id }]
    }
  }
}]

output actionGroupId string = actionGroup.id
output socActionGroupId string = enableDefenderAiAlerts ? socActionGroup.id : ''
