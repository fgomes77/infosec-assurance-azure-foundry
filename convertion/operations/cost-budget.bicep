// Component budgets and weekly cost digest for the InfoSec Assurance Foundry
// platform (operations/FINOPS.md §4). Complements infra/cost.bicep (the whole-RG
// budget deployed by main.bicep) with two filtered budgets — model/token spend
// on the Foundry account and observability ingestion — and an optional weekly
// Cost Management e-mail digest to the owner group.
//
// Deploy at resource-group scope AFTER infra/main.bicep (needs the action group
// from monitoring.bicep and the resource names), as a module (delta D-FIN-B1 in
// FINOPS.md §8) or standalone:
//   az deployment group what-if -g {rg} -f cost-budget.bicep \
//       -p baseName=infosecfoundry foundryAccountName=infosecfoundry-aif \
//          logAnalyticsName=infosecfoundry-logs appInsightsName=infosecfoundry-appi \
//          startDate={yyyy-MM-01} actionGroupId={actionGroupResourceId}
//
// Rules encoded here (controls in brackets):
//   - budgets notify only; nothing here holds or grants a write permission and
//     no automation stops a resource — the response is a human decision
//     (RUNBOOK.md FM-06/FM-07) [ISO 27001:2022 A.8.6, A.8.16; DORA Art. 9(2)]
//   - contacts are the owner GROUP mailbox placeholder, never a personal
//     address; the same action group as every other alert [A.5.9, A.5.24]
//   - filters are by ResourceId so a budget cannot be silently widened by
//     tagging; amounts are parameters reviewed at the monthly M2 review
//     (FINOPS.md §6) and changed through a PR [A.8.32]
//   - the ML cost-anomaly alert is subscription-scoped and therefore NOT here
//     (FINOPS.md delta D-FIN-S1) — least privilege keeps this module inside the RG
//
// Placeholders in {braces}; no real e-mail addresses, hostnames or object ids.

targetScope = 'resourceGroup'

@description('Base name used by infra/main.bicep (budget names derive from it)')
@minLength(3)
@maxLength(15)
param baseName string

@description('Foundry account name created by infra/main.bicep ({baseName}-aif) — token/model spend scope')
param foundryAccountName string

@description('Log Analytics workspace name ({baseName}-logs) — observability spend scope')
param logAnalyticsName string

@description('Application Insights component name ({baseName}-appi) — observability spend scope')
param appInsightsName string

@description('Monthly budget for model/token spend on the Foundry account, in the billing currency (FINOPS.md §2 planning total × headroom)')
@minValue(1)
param modelBudgetAmount int = 300

@description('Monthly budget for Log Analytics + App Insights ingestion/retention (FINOPS.md §1 C6)')
@minValue(1)
param observabilityBudgetAmount int = 300

@description('First day of the month the budgets start (yyyy-MM-01)')
param startDate string

@description('Budget end date (yyyy-MM-dd); Azure requires one — default ten years out, reviewed annually')
param endDate string = '2036-12-31'

@description('Action group resource id from infra/monitoring.bicep (infosec-foundry-ag-owner); empty = e-mail only')
param actionGroupId string = ''

@description('Owner GROUP distribution addresses — placeholders, never personal mailboxes')
param contactEmails array = ['{email:sg-infosec-foundry-owner}']

@description('Also create the weekly Cost Management e-mail digest (scheduled action, Monday 07:00 UTC)')
param enableWeeklyReport bool = false

@description('Cost Management view id used by the weekly digest; default = the built-in daily-costs view scoped to this resource group. Verify the id in Cost analysis > Views before enabling')
param weeklyReportViewId string = '${resourceGroup().id}/providers/Microsoft.CostManagement/views/ms:DailyCosts'

@description('First Monday (yyyy-MM-dd) the weekly digest is sent')
param weeklyReportStartDate string = '{yyyy-MM-dd}'

// ---------------------------------------------------------------- existing resources
resource foundry 'Microsoft.CognitiveServices/accounts@2025-06-01' existing = {
  name: foundryAccountName
}

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' existing = {
  name: logAnalyticsName
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' existing = {
  name: appInsightsName
}

var contactGroups = empty(actionGroupId) ? [] : [actionGroupId]

// Notification set shared by both budgets: 80 % actual (warn), 100 % actual
// (breach), 100 % forecast (early warning ~mid-month).
var notificationSet = {
  actual80: {
    enabled: true
    operator: 'GreaterThanOrEqualTo'
    threshold: 80
    thresholdType: 'Actual'
    contactEmails: contactEmails
    contactGroups: contactGroups
  }
  actual100: {
    enabled: true
    operator: 'GreaterThanOrEqualTo'
    threshold: 100
    thresholdType: 'Actual'
    contactEmails: contactEmails
    contactGroups: contactGroups
  }
  forecast100: {
    enabled: true
    operator: 'GreaterThanOrEqualTo'
    threshold: 100
    thresholdType: 'Forecasted'
    contactEmails: contactEmails
    contactGroups: contactGroups
  }
}

// ---------------------------------------------------------------- budgets
// Model / token spend: everything billed against the Foundry account
// (model deployments of the three tiers, Bing grounding transactions, vector
// store storage, code_interpreter sessions) — FINOPS.md §1 C1–C4.
resource modelBudget 'Microsoft.Consumption/budgets@2023-05-01' = {
  name: '${baseName}-budget-models'
  properties: {
    category: 'Cost'
    amount: modelBudgetAmount
    timeGrain: 'Monthly'
    timePeriod: {
      startDate: startDate
      endDate: endDate
    }
    filter: {
      dimensions: {
        name: 'ResourceId'
        operator: 'In'
        values: [
          foundry.id
        ]
      }
    }
    notifications: notificationSet
  }
}

// Observability spend: Log Analytics ingestion + 365-day retention and the
// workspace-based App Insights component — FINOPS.md §1 C6. Retention is
// never the lever (DORA Art. 28 evidence); sampling of non-evidence tables is.
resource observabilityBudget 'Microsoft.Consumption/budgets@2023-05-01' = {
  name: '${baseName}-budget-observability'
  properties: {
    category: 'Cost'
    amount: observabilityBudgetAmount
    timeGrain: 'Monthly'
    timePeriod: {
      startDate: startDate
      endDate: endDate
    }
    filter: {
      dimensions: {
        name: 'ResourceId'
        operator: 'In'
        values: [
          logAnalytics.id
          appInsights.id
        ]
      }
    }
    notifications: notificationSet
  }
}

// ---------------------------------------------------------------- weekly digest
// Read-only scheduled e-mail of the resource group's daily costs to the owner
// group — the W7 weekly cost check input (RUNBOOK.md). Optional: the built-in
// view id must be confirmed in the tenant before enabling.
resource weeklyDigest 'Microsoft.CostManagement/scheduledActions@2023-11-01' = if (enableWeeklyReport) {
  name: '${baseName}-cost-weekly'
  kind: 'Email'
  properties: {
    displayName: 'InfoSec Foundry — weekly cost digest (RUNBOOK W7)'
    status: 'Enabled'
    viewId: weeklyReportViewId
    schedule: {
      frequency: 'Weekly'
      daysOfWeek: [
        'Monday'
      ]
      hourOfDay: 7
      startDate: '${weeklyReportStartDate}T07:00:00Z'
      endDate: '${endDate}T07:00:00Z'
    }
    notification: {
      to: contactEmails
      subject: 'InfoSec Foundry — weekly cost digest (rg-infosec-foundry)'
      message: 'Week-over-week cost of the InfoSec Assurance Foundry platform. Compare with the monthly forecast (operations/FINOPS.md §4, RUNBOOK W7). Evidence: file under Governance/Operations/{yyyy}-{mm}/.'
    }
  }
}

// ---------------------------------------------------------------- outputs
output modelBudgetName string = modelBudget.name
output observabilityBudgetName string = observabilityBudget.name
output weeklyDigestName string = enableWeeklyReport ? '${baseName}-cost-weekly' : ''
