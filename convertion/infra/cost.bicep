// Cost controls (requirement j — token economy): resource-group budget with
// 50/80/100 % alerts to the platform owner's action group (monitoring.bicep).

param baseName string
@description('Monthly budget in the subscription currency')
param monthlyAmount int = 1500
@description('First day of the month the budget starts (yyyy-MM-01)')
param startDate string
param actionGroupId string
param contactEmails array = ['{owner-mailbox}']

resource budget 'Microsoft.Consumption/budgets@2023-05-01' = {
  name: '${baseName}-budget'
  properties: {
    category: 'Cost'
    amount: monthlyAmount
    timeGrain: 'Monthly'
    timePeriod: { startDate: startDate }
    notifications: {
      at50: { enabled: true, operator: 'GreaterThan', threshold: 50, thresholdType: 'Actual', contactEmails: contactEmails, contactGroups: [actionGroupId] }
      at80: { enabled: true, operator: 'GreaterThan', threshold: 80, thresholdType: 'Actual', contactEmails: contactEmails, contactGroups: [actionGroupId] }
      at100: { enabled: true, operator: 'GreaterThan', threshold: 100, thresholdType: 'Forecasted', contactEmails: contactEmails, contactGroups: [actionGroupId] }
    }
  }
}
