# Entra ID Groups — Creation, PIM Settings, Conditional Access, Quarterly Review

Executable companion to `TEAM_MODEL.md` §6 (the seven groups), §7 (roles
they carry, deployed by `rbac.bicep`) and §15 (quarterly review). Run by
the Entra IAM team `{group:iam-admins}` for the privileged groups and by
the owner for the user-facing groups (§18 bootstrap step 1). Every UPN,
object id and tenant value is a placeholder — replace before running;
never paste real ids back into this folder. Commands are `az` CLI and
Microsoft Graph via `az rest`; all are idempotent or safe to re-run.

Prerequisites: `az login` as a member of `{group:iam-admins}` (Groups
Administrator for §1, Privileged Role Administrator for §3–§4, Identity
Governance Administrator for §5–§6); `jq`. Nothing here needs a client
secret.

## 1. The seven groups

Attributes common to all: `securityEnabled=true`, `mailEnabled=false`,
`isAssignableToRole=false`, **assigned** membership (no dynamic rules),
`visibility=Private`. Membership of `-admin-pim` and `-breakglass` is
standing but grants nothing by itself: every Azure role these two groups
carry is a **PIM eligibility** created by `rbac.bicep` (`enablePim=true`),
activated per role under the settings of §4.

| Group | Purpose (description field) | Owner | Members (assigned) |
|---|---|---|---|
| `sg-infosec-foundry-users` | Assurance users: Azure AI User on the Foundry project; SharePoint site members; Copilot audience; hosted-MCP Easy Auth | `{upn:francisco.gomes}` (backup `{group:iam-admins}`) | `{upn:francisco.gomes}`, `{upn:jose.mogollon}`, `{upn:pedro.santos}`, `{upn:jose.meireles}`, `{upn:tania.morais}` |
| `sg-infosec-foundry-report-approvers` | Tier A approvers (peer four-eyes); joiners added after the onboarding attestation (`ONBOARDING.md` §5) | `{upn:francisco.gomes}` | the five |
| `sg-infosec-foundry-senior-approvers` | Tier B approvers; deputy approves the owner's Tier C items | `{upn:line-manager}` | `{upn:francisco.gomes}`, `{upn:deputy-approver}` |
| `sg-infosec-foundry-owner` | Standing low-privilege owner roles (Reader RG, Log Analytics Reader, KV Reader, site owner, Copilot maker, GitHub Maintain) | `{upn:line-manager}` | `{upn:francisco.gomes}` |
| `sg-infosec-foundry-admin-pim` | Carrier of the PIM-eligible privileged Azure roles (ledger L1–L5, L7, L8) | `{upn:line-manager}` | `{upn:francisco.gomes}` |
| `sg-infosec-foundry-breakglass` | Deputy continuity: same eligible role set, activation approved by a third party (`../operations/access-governance/BREAK_GLASS.md`) | `{upn:line-manager}` | `{upn:deputy-approver}` |
| `sg-infosec-foundry-readers` | Audit / DPO evidence read; empty outside engagements | `{upn:francisco.gomes}` | none by default |

Rule encoded above: the owner owns the groups he uses to run the team and
never a group that grants him privilege or approves his changes (ISO
27001:2022 A.5.3, A.8.2).

## 2. Create the groups (az CLI, then Graph for owners)

```bash
# 2a. Create (skip if it exists) — run once per row of §1
create_group() {  # name, description
  local id
  id=$(az ad group list --display-name "$1" --query "[0].id" -o tsv)
  if [ -z "$id" ]; then
    id=$(az ad group create --display-name "$1" --mail-nickname "$1" \
          --description "$2" --query id -o tsv)
  fi
  echo "$1 $id"
}
create_group sg-infosec-foundry-users            "InfoSec Assurance Foundry: assurance users (TEAM_MODEL.md §6)"
create_group sg-infosec-foundry-report-approvers "InfoSec Assurance Foundry: Tier A report approvers"
create_group sg-infosec-foundry-senior-approvers "InfoSec Assurance Foundry: Tier B senior approvers"
create_group sg-infosec-foundry-owner            "InfoSec Assurance Foundry: owner standing low-privilege roles"
create_group sg-infosec-foundry-admin-pim        "InfoSec Assurance Foundry: PIM-eligible privileged roles"
create_group sg-infosec-foundry-breakglass       "InfoSec Assurance Foundry: deputy break-glass (PIM only)"
create_group sg-infosec-foundry-readers          "InfoSec Assurance Foundry: audit/DPO evidence read"

# 2b. Owners — Graph accepts a UPN in the users/ segment
set_owner() {  # group, ownerUpn
  local gid; gid=$(az ad group show --group "$1" --query id -o tsv)
  az rest --method POST --url "https://graph.microsoft.com/v1.0/groups/$gid/owners/\$ref" \
    --body "{\"@odata.id\":\"https://graph.microsoft.com/v1.0/users/$2\"}" || true   # 400 = already owner
}
set_owner sg-infosec-foundry-users            "{upn:francisco.gomes}"
set_owner sg-infosec-foundry-report-approvers "{upn:francisco.gomes}"
set_owner sg-infosec-foundry-readers          "{upn:francisco.gomes}"
for g in senior-approvers owner admin-pim breakglass; do
  set_owner "sg-infosec-foundry-$g" "{upn:line-manager}"
done
# Backup owner of -users is the IAM team group (a group can own a group)
gid=$(az ad group show --group sg-infosec-foundry-users --query id -o tsv)
iam=$(az ad group show --group "{group:iam-admins}" --query id -o tsv)
az rest --method POST --url "https://graph.microsoft.com/v1.0/groups/$gid/owners/\$ref" \
  --body "{\"@odata.id\":\"https://graph.microsoft.com/v1.0/groups/$iam\"}" || true

# 2c. Members — assigned membership, one act per person
add_member() {  # group, upn
  az ad group member add --group "$1" \
     --member-id "$(az ad user show --id "$2" --query id -o tsv)" 2>/dev/null || true
}
for u in "{upn:francisco.gomes}" "{upn:jose.mogollon}" "{upn:pedro.santos}" "{upn:jose.meireles}" "{upn:tania.morais}"; do
  add_member sg-infosec-foundry-users "$u"
  add_member sg-infosec-foundry-report-approvers "$u"     # joiners: only after attestation
done
add_member sg-infosec-foundry-senior-approvers "{upn:francisco.gomes}"
add_member sg-infosec-foundry-senior-approvers "{upn:deputy-approver}"
add_member sg-infosec-foundry-owner            "{upn:francisco.gomes}"
add_member sg-infosec-foundry-admin-pim        "{upn:francisco.gomes}"
add_member sg-infosec-foundry-breakglass       "{upn:deputy-approver}"

# 2d. Object ids → rbac.parameters.example.json placeholders {objectId:sg-infosec-foundry-*}
for g in users owner admin-pim breakglass readers; do
  printf '{objectId:sg-infosec-foundry-%s} = %s\n' "$g" "$(az ad group show --group sg-infosec-foundry-$g --query id -o tsv)"
done
```

`least-privilege/scripts/provision_identity.sh --apply` automates 2a–2d
from `least-privilege/entra/groups.json` once delta D-T3 (`TEAM_MODEL.md`
§20) has re-keyed that file to the seven names above; until then use the
commands here. Evidence: Entra audit log entries "Add group", "Add owner
to group", "Add member to group"; file the `az ad group show` output as
`Governance/AccessReviews/{yyyy}-Q0/groups-baseline.json`.

## 3. Azure role eligibilities (PIM for Azure resources)

Created by `rbac.bicep` (`roleEligibilityScheduleRequests`, `P365D`,
`requestType: AdminAssign`) — not by hand. Deploy after the groups exist:

```bash
az deployment group what-if -g rg-infosec-foundry -f rbac.bicep -p rbac.parameters.example.json
az deployment group create  -g rg-infosec-foundry -f rbac.bicep -p rbac.parameters.example.json
# verify: every eligibility sits on a GROUP, none on a user
az rest --method GET --url "https://management.azure.com/subscriptions/{subscriptionId}/resourceGroups/rg-infosec-foundry/providers/Microsoft.Authorization/roleEligibilitySchedules?api-version=2020-10-01&\$filter=atScope()" \
  --query "value[].{principal:properties.principalId,type:properties.principalType,role:properties.expandedProperties.roleDefinition.displayName,scope:properties.scope,end:properties.endDateTime}" -o table
```

Renewal: eligibilities expire after 365 days; redeploy `rbac.bicep` after
the Q4 access review (item 2 of §6). Without Entra ID P2, deploy with
`enablePim=false` and record the exception (`ACCESS_REGISTER.md`, "PIM
fallback exception").

## 4. PIM role settings (activation policy per role)

Role settings are properties of the role at its scope
(`Microsoft.Authorization/roleManagementPolicies`), not of the group, and
cannot be expressed in `rbac.bicep`; the IAM team sets them once per
(scope, role) and exports them as evidence. Values from `TEAM_MODEL.md` §5.

| Scope | Role | Max activation | MFA | Justification | Ticket | Activation approver | Ledger |
|---|---|---|---|---|---|---|---|
| RG `rg-infosec-foundry` | Contributor | 8 h | yes | yes | yes | `{upn:line-manager}` (for `-admin-pim`); `{upn:line-manager}` or `{group:soc-oncall}` (for `-breakglass`) | L2, L10 |
| Foundry account `infosecfoundry-aif` | Azure AI Developer | 8 h | yes | yes | yes | none (self-activation) / third party for `-breakglass` | L1 |
| Key Vault `infosecfoundry-kv` | Key Vault Secrets Officer | 2 h | yes | yes | yes | none / third party for `-breakglass` | L3 |
| Logic Apps `infosecfoundry-la` | Logic Apps Standard Developer, Operator | 8 h | yes | yes | yes | none / third party | L4 |
| Function `infosecfoundry-fn-delivery` | Website Contributor | 4 h | yes | yes | yes | none / third party | L5 |
| Container `deliverables` | Storage Blob Data Reader | 4 h | yes | yes | yes | none / third party | L7 |
| Log Analytics `infosecfoundry-logs` | Monitoring Contributor | 4 h | yes | yes | yes | none / third party | L8 |
| Bing `infosecfoundry-bing` | Contributor | 2 h | yes | yes | yes | none | §7 |

Because a role setting applies to every eligible principal at that scope,
the stricter `-breakglass` approval is achieved by the **approval rule
listing the third-party approvers** and by PIM notifications to the owner
on every activation; the owner self-activates the same roles without
approval only where the table says "none". Where the tenant needs the two
groups to differ in approval, split the scope (breakglass eligibilities
at RG scope only, `enablePim` per group) — record the decision in
`ACCESS_REGISTER.md`.

Read, then patch, the policy of one (scope, role):

```bash
SCOPE="/subscriptions/{subscriptionId}/resourceGroups/rg-infosec-foundry"
ROLE="b24988ac-6180-42a0-ab88-20f7382dd24c"   # Contributor (rbac.bicep var roles)
POLICY=$(az rest --method GET --url "https://management.azure.com${SCOPE}/providers/Microsoft.Authorization/roleManagementPolicyAssignments?api-version=2020-10-01" \
  --query "value[?ends_with(properties.roleDefinitionId, '${ROLE}')].properties.policyId | [0]" -o tsv)
# Export current rules as evidence before changing anything
az rest --method GET --url "https://management.azure.com${POLICY}?api-version=2020-10-01" > "policy-contributor-before.json"
# Patch: 8 h max, MFA + justification + ticket, approval by the line manager
az rest --method PATCH --url "https://management.azure.com${POLICY}?api-version=2020-10-01" --body '{
  "properties": { "rules": [
    { "id": "Expiration_EndUser_Assignment", "ruleType": "RoleManagementPolicyExpirationRule",
      "isExpirationRequired": true, "maximumDuration": "PT8H",
      "target": { "caller": "EndUser", "operations": ["All"], "level": "Assignment" } },
    { "id": "Enablement_EndUser_Assignment", "ruleType": "RoleManagementPolicyEnablementRule",
      "enabledRules": ["MultiFactorAuthentication", "Justification", "Ticketing"],
      "target": { "caller": "EndUser", "operations": ["All"], "level": "Assignment" } },
    { "id": "Approval_EndUser_Assignment", "ruleType": "RoleManagementPolicyApprovalRule",
      "setting": { "isApprovalRequired": true, "isApprovalRequiredForExtension": false,
        "approvalMode": "SingleStage",
        "approvalStages": [ { "approvalStageTimeOutInDays": 1, "isApproverJustificationRequired": true,
          "escalationTimeInMinutes": 0, "isEscalationEnabled": false,
          "primaryApprovers": [ { "id": "{objectId:line-manager}", "description": "{upn:line-manager}", "isBackup": false, "userType": "User" },
                                { "id": "{objectId:soc-oncall}", "description": "{group:soc-oncall}", "isBackup": true, "userType": "Group" } ] } ] },
      "target": { "caller": "EndUser", "operations": ["All"], "level": "Assignment" } },
    { "id": "Notification_Admin_EndUser_Assignment", "ruleType": "RoleManagementPolicyNotificationRule",
      "notificationType": "Email", "recipientType": "Admin", "notificationLevel": "All", "isDefaultRecipientsEnabled": true,
      "notificationRecipients": ["{upn:francisco.gomes}", "{upn:line-manager}"],
      "target": { "caller": "EndUser", "operations": ["All"], "level": "Assignment" } }
  ] } }'
```

Repeat per row with the durations above, dropping the approval rule (or
setting `isApprovalRequired:false`) where the approver column says
"none". Rule ids and shapes are the documented `2020-10-01` contract —
confirm with the exported `*-before.json` before patching. Evidence:
before/after exports under `Governance/AccessReviews/{yyyy}-Q0/pim-settings/`.

## 5. Conditional Access and the access package

**`CA-InfoSec-Foundry`** (ISO 27001:2022 A.8.5; DORA Art. 9(4)(d); NIS2
Art. 21(2)(j)): MFA + compliant device, sign-in frequency 12 h, legacy
auth blocked, scoped to the seven groups. Resolve the first-party app ids
in the tenant rather than hard-coding them:

```bash
for app in "Windows Azure Service Management API" "Office 365 SharePoint Online" "Azure AI Foundry" "Azure Cognitive Services"; do
  az ad sp list --filter "displayName eq '$app'" --query "[].{name:displayName,appId:appId}" -o tsv
done
az rest --method POST --url https://graph.microsoft.com/v1.0/identity/conditionalAccess/policies --body '{
  "displayName": "CA-InfoSec-Foundry",
  "state": "enabledForReportingButNotEnforced",
  "conditions": {
    "users": { "includeGroups": ["{objectId:sg-infosec-foundry-users}", "{objectId:sg-infosec-foundry-report-approvers}", "{objectId:sg-infosec-foundry-senior-approvers}", "{objectId:sg-infosec-foundry-owner}", "{objectId:sg-infosec-foundry-admin-pim}", "{objectId:sg-infosec-foundry-breakglass}", "{objectId:sg-infosec-foundry-readers}"] },
    "applications": { "includeApplications": ["{appId:azure-management}", "{appId:sharepoint-online}", "{appId:azure-ai-services}"] },
    "clientAppTypes": ["browser", "mobileAppsAndDesktopClients"]
  },
  "grantControls": { "operator": "AND", "builtInControls": ["mfa", "compliantDevice"] },
  "sessionControls": { "signInFrequency": { "value": 12, "type": "hours", "isEnabled": true } }
}'
```

Switch `state` to `enabled` after one week of report-only sign-in log
review; legacy authentication is blocked by the tenant baseline policy
(confirm it covers `exchangeActiveSync` and `other` client app types).

**Access package `AP-InfoSec-Foundry-User`** (entitlement management;
ISO 27001:2022 A.5.18): resource = `sg-infosec-foundry-users` (member);
policy = requestable by `{group:infosec-assurance-team}` on the line
manager's behalf, approver `{upn:francisco.gomes}`, single stage, 14-day
approval timeout, **expiry 12 months**, quarterly access review of
assignments by the group owner. Create it in the Identity Governance
portal (catalog `InfoSec Assurance Foundry`) or via
`POST /identityGovernance/entitlementManagement/accessPackages` and
`…/accessPackages/{id}/assignmentPolicies`; record the package id in
`ACCESS_REGISTER.md`. Where entitlement management is not licensed, the
owner adds directly (2c) and records the request ticket.

## 6. Quarterly access review (Entra access reviews)

Two recurring review definitions, both quarterly, 14-day window, decisions
auto-applied, "no response" = **Deny** (a right nobody confirms is removed
— ISO 27001:2022 A.5.18; DORA Art. 9(4)(c); NIS2 Art. 21(2)(i)):

| Definition | Groups | Reviewer | Fallback reviewer |
|---|---|---|---|
| `AR-InfoSec-Foundry-Users` | `-users`, `-report-approvers`, `-readers` | group owner (`{upn:francisco.gomes}`) | `{upn:line-manager}` |
| `AR-InfoSec-Foundry-Privileged` | `-owner`, `-senior-approvers`, `-admin-pim`, `-breakglass` | `{upn:line-manager}` | `{group:iam-admins}` |

```bash
az rest --method POST --url https://graph.microsoft.com/v1.0/identityGovernance/accessReviews/definitions --body '{
  "displayName": "AR-InfoSec-Foundry-Privileged",
  "descriptionForAdmins": "TEAM_MODEL.md §15 items 1-3: privileged groups reviewed by the line manager, never by the owner",
  "scope": { "@odata.type": "#microsoft.graph.principalResourceMembershipsScope",
    "principalScopes": [ { "@odata.type": "#microsoft.graph.accessReviewQueryScope", "query": "/users", "queryType": "MicrosoftGraph" } ],
    "resourceScopes": [
      { "@odata.type": "#microsoft.graph.accessReviewQueryScope", "query": "/groups/{objectId:sg-infosec-foundry-owner}/transitiveMembers", "queryType": "MicrosoftGraph" },
      { "@odata.type": "#microsoft.graph.accessReviewQueryScope", "query": "/groups/{objectId:sg-infosec-foundry-senior-approvers}/transitiveMembers", "queryType": "MicrosoftGraph" },
      { "@odata.type": "#microsoft.graph.accessReviewQueryScope", "query": "/groups/{objectId:sg-infosec-foundry-admin-pim}/transitiveMembers", "queryType": "MicrosoftGraph" },
      { "@odata.type": "#microsoft.graph.accessReviewQueryScope", "query": "/groups/{objectId:sg-infosec-foundry-breakglass}/transitiveMembers", "queryType": "MicrosoftGraph" } ] },
  "reviewers": [ { "query": "/users/{objectId:line-manager}", "queryType": "MicrosoftGraph" } ],
  "fallbackReviewers": [ { "query": "/groups/{objectId:iam-admins}/transitiveMembers", "queryType": "MicrosoftGraph" } ],
  "settings": { "mailNotificationsEnabled": true, "reminderNotificationsEnabled": true, "justificationRequiredOnApproval": true,
    "defaultDecisionEnabled": true, "defaultDecision": "Deny", "instanceDurationInDays": 14, "autoApplyDecisionsEnabled": true,
    "recommendationsEnabled": true,
    "recurrence": { "pattern": { "type": "absoluteMonthly", "interval": 3, "dayOfMonth": 1 },
                    "range": { "type": "noEnd", "startDate": "{yyyy}-01-01" } } }
}'
# Same body for AR-InfoSec-Foundry-Users with the three user-facing groups and reviewers = group owners:
#   "reviewers": [ { "query": "./owners", "queryType": "MicrosoftGraph", "queryRoot": "group" } ]
```

Collect results and file them (review item 1 of
`../operations/access-governance/QUARTERLY_ACCESS_REVIEW.md`):

```bash
DEF=$(az rest --method GET --url "https://graph.microsoft.com/v1.0/identityGovernance/accessReviews/definitions?\$filter=startswith(displayName,'AR-InfoSec-Foundry')" --query "value[].id" -o tsv)
for d in $DEF; do
  az rest --method GET --url "https://graph.microsoft.com/v1.0/identityGovernance/accessReviews/definitions/$d/instances?\$top=1&\$orderby=startDateTime desc" \
    --query "value[0].{id:id,status:status,start:startDateTime,end:endDateTime}"
done
# decisions of the latest instance -> Governance/AccessReviews/{yyyy}-Q{n}/entra-access-review-{groups}.json
az rest --method GET --url "https://graph.microsoft.com/v1.0/identityGovernance/accessReviews/definitions/{definitionId}/instances/{instanceId}/decisions" \
  --query "value[].{principal:principal.displayName,resource:resource.displayName,decision:decision,reviewer:reviewedBy.userPrincipalName,justification:justification,applied:applyResult}" -o json
# read-only collectors for the rest of the checklist
./access-review.sh                                       # role assignments, groups, connections, KV ages
../operations/access-governance/scripts/access_snapshot.sh   # json snapshot for the evidence folder
```

Additional quarterly checks that the access review does not cover:
PIM activation log for the quarter
(`GET /auditLogs/directoryAudits?$filter=category eq 'RoleManagement'`
plus the Azure Activity Log for `roleAssignmentScheduleRequests`), the
`-breakglass` group has **no active** Azure role assignment outside a
ticketed window, the CA policy is still `enabled` and unchanged, and the
eligibility end dates (§3) are more than 90 days away.

## 7. Verification (bootstrap and after every change)

```bash
for g in users report-approvers senior-approvers owner admin-pim breakglass readers; do
  echo "== sg-infosec-foundry-$g"
  az ad group show --group sg-infosec-foundry-$g --query "{security:securityEnabled,mail:mailEnabled,roleAssignable:isAssignableToRole,rules:membershipRule}" -o tsv
  az ad group owner list  --group sg-infosec-foundry-$g --query "[].userPrincipalName" -o tsv | sed 's/^/  owner:  /'
  az ad group member list --group sg-infosec-foundry-$g --query "[].userPrincipalName" -o tsv | sed 's/^/  member: /'
done
# no human holds a direct role in the RG (groups only)
az role assignment list -g rg-infosec-foundry --include-inherited --query "[?principalType=='User']" -o table
```

Pass criteria: `mailEnabled=false`, `isAssignableToRole=false`, no
membership rule; owners exactly as §1; `-breakglass` and `-readers`
members as designed; the last command prints nothing.

## 8. Controls implemented here

| Control | Where |
|---|---|
| ISO 27001:2022 A.5.15, A.5.16, A.5.18 | groups §1–§2, access package §5, access reviews §6 |
| ISO 27001:2022 A.5.3, A.8.2 | privileged groups owned by the line manager §1; PIM settings §4; independent review of the owner's privilege §6 |
| ISO 27001:2022 A.8.5 | Conditional Access §5 |
| DORA Art. 9(4)(c)–(d) | access management and review §3–§6; strong authentication §5 |
| NIS2 Art. 21(2)(i)–(j) | access-control policy §1–§6; MFA §5 |
| ISO 42001 A.3.2; EU AI Act Art. 26(2) | approver groups as the named natural persons exercising oversight §1 |
