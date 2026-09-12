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

//
// ===========================================================================
// TWO ALERT CATALOGUES — WHICH ONE IS DEPLOYED (reconciliation 2026-09-12)
// ===========================================================================
// `infra/monitoring.bicep` is the SET OF RECORD: it is a module of
// infra/main.bicep (`enableMonitoring`), owns the action groups
// `{baseName}-ag` and `{baseName}-ag-soc`, the five platform rules
// (egress-internal-markers, verifier-fail-rate, pipeline-failures,
// approval-expiry, agent-drift + agent_version_not_in_manifest) and the
// Defender-for-AI activity-log routing (finding C17).
//
// `operations/alerts.bicep` is the EXTENDED OPERATIONS CATALOGUE: the same
// five signals PLUS latency-and-token-budget, delivery-function-5xx,
// breakglass_window_write, keyvault-human-secret-read, model-throttling-429
// and daily-token-budget, on its own action groups `{alertPrefix}-ag-owner`
// / `-ag-soc`.
//
// **Deploy exactly one of the two.** They cover overlapping signals under
// different rule names, so deploying both double-pages the owner:
//   * default            -> main.bicep with `enableMonitoring: true`, and
//                           operations/alerts.bicep NOT deployed;
//   * extended operations -> main.bicep with `enableMonitoring: false`, then
//                           operations/alerts.bicep standalone.
// Name mapping between the two: egress-internal-markers ~
// egress-internal-marker; pipeline-failures ~ pipeline-run-failed;
// approval-expiry ~ approval-sla; agent-drift ~
// agent_modified_by_non_deploy_identity. `operations/MONITORING.md` §4 is the
// catalogue of record for thresholds either way.
// ===========================================================================

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
