// Defender for Cloud — AI threat protection plan (finding C17 / SEC-1).
// SUBSCRIPTION scope: the plan that produces the model-aware alerts
// (jailbreak / prompt-injection attempts, sensitive-data exposure in prompts
// and completions, wallet abuse and credential theft) is a subscription
// setting, so it cannot live in the resource-group deployment of main.bicep.
// The ROUTING of those alerts is in monitoring.bicep (activity-log alerts on
// category `Security` → SOC action group for High, owner action group for the
// rest); this template only turns the detection on.
//
// Deploy once, with the platform owner under a PIM window:
//   az deployment sub create -l {location} -f infra/defender-ai.bicep \
//     -p enableAiPlan=true enableAiUserPromptEvidence=false
// Verify:
//   az security pricing show -n AI --query "{tier:pricingTier,sub:subPlan}"
//
// Sources: Defender for Cloud AI workload alerts (GA, 2026-07-06);
// Foundry Control Plane compliance & security (2026-08-04).
// ISMS: ISO 27001:2022 A.8.16 (monitoring activities), DORA Art. 10
// (detection), and the SOC runbook entry in operations/RUNBOOK.md.

targetScope = 'subscription'

@description('Enable the Defender for Cloud AI Services threat-protection plan on this subscription. Standard is billed per 10k prompts — start on the 30-day trial to size the cost before the FinOps review (enterprise FinOps rule COST-1)')
param enableAiPlan bool = true

@description('Include the user prompt/response evidence in alerts. FALSE by default: prompt bodies can carry Euronext-derived assessment content and the alert payload leaves the workspace boundary. Turn it on only with a DPO decision recorded in the RoPA (governance/DATA_PROTECTION_GUARDRAILS.md §1)')
param enableAiUserPromptEvidence bool = false

resource aiPlan 'Microsoft.Security/pricings@2024-01-01' = if (enableAiPlan) {
  name: 'AI'
  properties: {
    pricingTier: 'Standard'
    extensions: [
      {
        name: 'AIPromptEvidence'
        isEnabled: enableAiUserPromptEvidence ? 'True' : 'False'
      }
    ]
  }
}

output aiPlanEnabled bool = enableAiPlan
output aiPromptEvidenceEnabled bool = enableAiPlan && enableAiUserPromptEvidence
