# Offboarding — Leaver, Deputy Step-Down, Owner Hand-Over

Same-day revocation checklist with the commands that produce the
**evidence of revocation**. Companion to
`../operations/access-governance/ACCESS_LIFECYCLE.md` §2–§3 (runbook) and
`TEAM_MODEL.md` §14 (model). Target: every platform right gone the same
day as the HR / line-manager trigger, never later than the next business
day (ISO 27001:2022 A.5.18, A.6.5; DORA Art. 9(4)(c); NIS2 Art.
21(2)(i)). Placeholders in `{braces}`; `{upn:leaver}` is the person
leaving.

## 1. Trigger and roles

| Trigger | Executes | Verifies |
|---|---|---|
| HR leaver record / access-package expiry / line-manager instruction | `{group:iam-admins}` (groups, sessions), owner (platform artefacts) | owner files the evidence; `{upn:line-manager}` reviews at the quarterly review (item 1) |
| Mover out of the team (keeps a Euronext account) | same steps — membership of `sg-infosec-foundry-users` is for team members only; a read need is served by report links, not platform access | owner |

## 2. Same-day revocation (T0)

| # | Step | Command / action | Evidence | Control |
|---|---|---|---|---|
| 1 | Remove from **every** `sg-infosec-foundry-*` group — one act revokes Foundry, SharePoint, Copilot, MCP and CA scope | see block below (`remove_all`) | Entra audit log "Remove member from group" | A.5.18 |
| 2 | Revoke refresh tokens so cached data-plane tokens die (access tokens expire ≤ 1 h; sign-in frequency 12 h) | `az rest --method POST --url "https://graph.microsoft.com/v1.0/users/{upn:leaver}/revokeSignInSessions"` | response `{"value": true}` | A.5.17 |
| 3 | End the access-package assignment (if not already expired) so the review does not show a dangling assignment | Identity Governance → `AP-InfoSec-Foundry-User` → remove assignment | assignment state | A.5.18 |
| 4 | GitHub: remove from team `infosec-assurance-users` (and `Write` / CODEOWNERS if deputy); Teams: remove from `{teams:infosec-assurance-platform}` and `{teams:infosec-assurance-approvals}` | owner | GitHub audit log | A.5.18 |
| 5 | Copilot Studio agent: nothing to do — audience is `sg-infosec-foundry-users` (step 1) | — | — | — |
| 6 | MCP: nothing server-side — local MCP used the leaver's own `az login` (dead after steps 1–2); hosted MCP Easy Auth allows the group only. Ask IT to remove the client configuration in the device wipe | IT / Intune | device retirement record | A.5.17 |
| 7 | Pending approvals: any Tier A/B item awaiting the leaver expires or is re-routed to another approver; items **requested** by the leaver are re-run by the new engagement owner if still needed | owner | approval decision records | A.5.3 |

```bash
LEAVER="{upn:leaver}"
LID=$(az ad user show --id "$LEAVER" --query id -o tsv)
remove_all() {
  for g in users report-approvers senior-approvers owner admin-pim breakglass readers; do
    az ad group member remove --group "sg-infosec-foundry-$g" --member-id "$LID" 2>/dev/null && echo "removed from sg-infosec-foundry-$g"
  done
}
remove_all
az rest --method POST --url "https://graph.microsoft.com/v1.0/users/$LID/revokeSignInSessions"
```

## 3. Deputy step-down (in addition to §2, or alone if the person stays a user)

| # | Step | Who |
|---|---|---|
| 1 | IAM removes `{upn:leaver}` from `sg-infosec-foundry-senior-approvers` and `-breakglass` the same day; PIM shows no remaining eligibility for the person | `{group:iam-admins}` |
| 2 | Owner nominates a replacement within 5 business days; `{upn:line-manager}` confirms; PR updates `least-privilege/entra/groups.json`, `approval-policy.json` (`principals.deputy`) and CODEOWNERS; `ACCESS_REGISTER.md` Deputy row updated | owner, line manager |
| 3 | Until a new deputy exists, Tier B requests by the owner fall back to any Tier A approver with the exception logged (`ruleId` `tierB-fallback-peer-after-2bd`); owner-authored PRs wait — no self-approval | approval flow |

## 4. Threads, files and memory — GDPR handling on exit

The platform holds no personal store (`TEAM_MODEL.md` §13: no per-user
vector store, no personal memory), so there is nothing to purge by
design; what remains is attribution of business acts, retained as ISMS /
DORA evidence (GDPR Art. 6(1)(c), (f); Art. 17(3)(b)).

| Object | Action | Basis |
|---|---|---|
| Active engagement threads (`metadata.owner_upn = {upn:leaver}`) | re-tag `owner_upn` to the new engagement owner **or** delete when the deliverable is stored; delete thread files first (the source lives in SharePoint) | GDPR Art. 5(1)(c), (e); A.5.12 |
| `personal-working` threads | delete (they were the leaver's scratch space; nothing in them is a record) | minimisation |
| Threads referenced by an open audit finding or incident | export to `Governance/Evidence/` first, then handle as above | A.5.33 |
| Shared memory notes `… \| by {upn:leaver} \| …` | **stay** — team facts and decisions; the `by` field is the audit attribution. Do not rewrite history. A data-subject request is handled by the DPO under the RoPA entry `{ropa:infosec-foundry-memory}` | Art. 17(3)(b); A.5.34 |
| App Insights traces with `owner_upn` | stay for the retention period (≥ 1 year, DORA Art. 28); purpose limited to cost / audit | Art. 5(1)(b) |
| Approval decision records naming the leaver as requester / approver | stay ≥ 1 year (`Governance/Approvals/`) | DORA Art. 28; EU AI Act Art. 12, 26(6) |
| Stored reports the leaver produced | stay — reports of record belong to the team | A.5.33 |

Thread inventory (read-only listing, then re-tag / delete through the
same SDK; run by the owner with `Azure AI User`):

```python
# python3 - <<'PY'   (azure-ai-projects, DefaultAzureCredential = owner's az login)
import os
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
client = AIProjectClient(endpoint=os.environ["PROJECT_ENDPOINT"], credential=DefaultAzureCredential())
leaver = "{upn:leaver}"
for t in client.agents.threads.list():
    md = t.metadata or {}
    if md.get("owner_upn") == leaver:
        print(t.id, md.get("supplier"), md.get("service"), md.get("classification"), t.created_at)
        # decision per row: client.agents.threads.update(t.id, metadata={**md, "owner_upn": "{upn:new-owner}"})
        #                or: client.agents.threads.delete(t.id)
PY
```

Save the before/after listing as `threads-{upn:leaver}-before.json` /
`-after.json` in the leaver's evidence folder (`Governance/AccessLifecycle/{yyyy}/`).

## 5. Credentials

No human ever holds a platform key or token (`TEAM_MODEL.md` §10), so the
default is **no rotation**. Rotate only if the leaver activated
`-admin-pim` or `-breakglass` in the last 90 days: list the activations,
then every Key Vault secret that had a `SecretGet` during a window is
re-issued by its custodian and re-pointed by the owner (`RACI.md` R22).

```bash
# PIM activations of the leaver (Azure resource roles) in the last 90 days
az rest --method GET --url "https://management.azure.com/subscriptions/{subscriptionId}/resourceGroups/rg-infosec-foundry/providers/Microsoft.Authorization/roleAssignmentScheduleInstances?api-version=2020-10-01&\$filter=assignedTo('$LID')" \
  --query "value[].{role:properties.expandedProperties.roleDefinition.displayName,start:properties.startDateTime,end:properties.endDateTime}" -o table
# SecretGet during a window (Key Vault diagnostics -> Log Analytics)
az monitor log-analytics query -w {logAnalyticsWorkspaceId} --analytics-query \
  "AzureDiagnostics | where ResourceProvider == 'MICROSOFT.KEYVAULT' and OperationName == 'SecretGet' and identity_claim_upn_s == '$LEAVER' and TimeGenerated > ago(90d) | project TimeGenerated, id_s" -o table
```

## 6. Evidence of revocation (file the same day)

```bash
OUT="offboarding-$LEAVER-$(date -u +%Y-%m-%d)"; mkdir -p "$OUT"
for g in users report-approvers senior-approvers owner admin-pim breakglass readers; do
  printf 'sg-infosec-foundry-%s: ' "$g"; az ad group member check --group "sg-infosec-foundry-$g" --member-id "$LID" --query value -o tsv
done | tee "$OUT/group-membership.txt"                       # every line: false
az role assignment list --assignee "$LID" --all --include-groups -o json | tee "$OUT/role-assignments.json"   # []
az rest --method GET --url "https://management.azure.com/subscriptions/{subscriptionId}/providers/Microsoft.Authorization/roleEligibilitySchedules?api-version=2020-10-01&\$filter=assignedTo('$LID')" \
  --query "value" -o json | tee "$OUT/pim-eligibilities.json"   # []
az ad user show --id "$LEAVER" --query "{accountEnabled:accountEnabled}" -o json | tee "$OUT/account.json"
../operations/access-governance/scripts/access_snapshot.sh --tag "leaver-$LEAVER"
```

| Check | Pass |
|---|---|
| `group-membership.txt` | seven lines, all `false` |
| `role-assignments.json`, `pim-eligibilities.json` | empty arrays |
| SharePoint | `sharepoint-permissions.md` §5 export shows no individual entry for the leaver (rights were group-based) |
| GitHub | `gh api orgs/{org}/teams/infosec-assurance-users/members` does not list the leaver |
| Threads | `-after.json` has no `owner_upn = {upn:leaver}` rows |
| Register | `ACCESS_REGISTER.md` People row closed with the date; change-log line; Deputy row updated if applicable |

Retention of the evidence folder: 5 years (ISMS record schedule).

## 7. Owner hand-over (only when `{upn:francisco.gomes}` leaves the role)

Run `TEAM_MODEL.md` §14 "Owner succession" before §2 of this file:
`{upn:line-manager}` appoints the successor (normally the deputy); IAM
transfers ownership of `-users`, `-report-approvers`, `-readers`, moves
`-owner` / `-admin-pim` / `-senior-approvers` membership; owner transfers
SharePoint site ownership (`sharepoint-permissions.md` §2a), Copilot
Studio maker, GitHub Maintain + CODEOWNERS, connection custodianship rows
and the RoPA entry; the successor runs `../deploy.sh --dry-run`,
`least-privilege/scripts/provision_identity.sh --verify` and
`access-review.sh` as the hand-over check and files them as the new Q0
baseline. Only then do steps §2–§6 apply to the outgoing owner.

## 8. Controls implemented here

| Control | Step |
|---|---|
| ISO 27001:2022 A.5.18, A.6.5 | §2 same-day removal, §6 evidence |
| ISO 27001:2022 A.5.17 | §2 session revocation; §5 conditional rotation |
| ISO 27001:2022 A.5.3 | §3 deputy continuity without self-approval |
| ISO 27001:2022 A.5.12, A.5.33, A.5.34; GDPR Art. 5(1)(c), (e), 17(3)(b) | §4 thread minimisation, records retained |
| DORA Art. 9(4)(c), 11, 28 | §2 access management; §3 continuity; §4–§6 evidence ≥ 1 year |
| NIS2 Art. 21(2)(i) | §2, §6 |
| ISO 42001 A.4.6, A.9.2; EU AI Act Art. 26(6) | §2 step 7 approvals re-routed; §4 logs kept |
