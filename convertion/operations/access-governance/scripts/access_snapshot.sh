#!/usr/bin/env bash
# Read-only evidence collector for the quarterly access review
# (operations/access-governance/QUARTERLY_ACCESS_REVIEW.md) and for
# joiner/leaver snapshots. Writes JSON + tables into an evidence folder;
# never writes to Azure, never prints secret values (Key Vault: names and
# dates only).
#
#   ./access_snapshot.sh                      -> evidence/<yyyy>-Q<n>/snapshot/
#   ./access_snapshot.sh --tag leaver-{upn}   -> evidence/<yyyy>-Q<n>/snapshot-leaver-{upn}/
#
# Requires: az CLI logged in as a reader of the RG (Reader + Log Analytics
# Reader are enough; group listing needs Directory read), jq.
# Env (setup/.env): AZURE_SUBSCRIPTION_ID, AZURE_RESOURCE_GROUP, KEY_VAULT_NAME,
# SHAREPOINT_SITE_ID, PROJECT_ENDPOINT (optional, for thread listing via SDK).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="$HERE/../../../setup/.env"
[ -f "$ENV_FILE" ] && set -a && . "$ENV_FILE" && set +a

RG="${AZURE_RESOURCE_GROUP:-rg-infosec-foundry}"
SUB="${AZURE_SUBSCRIPTION_ID:-}"
KV="${KEY_VAULT_NAME:-}"
SITE="${SHAREPOINT_SITE_ID:-}"
TAG=""
[ "${1:-}" = "--tag" ] && TAG="-${2:-untagged}"

q=$(( ( $(date -u +%-m) - 1 ) / 3 + 1 ))
OUT="$HERE/../evidence/$(date -u +%Y)-Q${q}/snapshot${TAG}"
mkdir -p "$OUT"
echo "evidence -> $OUT"

command -v az >/dev/null && command -v jq >/dev/null || { echo "need az + jq" >&2; exit 2; }

# 1. Groups and members
for g in sg-infosec-foundry-users sg-infosec-foundry-report-approvers \
         sg-infosec-foundry-senior-approvers sg-infosec-foundry-owner \
         sg-infosec-foundry-admin-pim sg-infosec-foundry-breakglass \
         sg-infosec-foundry-readers; do
  az ad group member list --group "$g" --query "[].{upn:userPrincipalName,type:'@odata.type',id:id}" -o json \
    > "$OUT/groups-$g.json" 2>/dev/null || echo "[]" > "$OUT/groups-$g.json"
  az ad group owner list --group "$g" --query "[].userPrincipalName" -o json \
    > "$OUT/groups-$g.owners.json" 2>/dev/null || echo "[]" > "$OUT/groups-$g.owners.json"
done

# 2. Azure role assignments (RG + inherited)
az role assignment list --resource-group "$RG" --include-inherited \
  --query "[].{principal:principalName,type:principalType,role:roleDefinitionName,scope:scope,condition:condition}" \
  -o json > "$OUT/role-assignments.json"
az role assignment list --resource-group "$RG" --include-inherited -o table > "$OUT/role-assignments.txt"

# 3. PIM eligibilities + activations (best effort; needs Entra ID P2)
if [ -n "$SUB" ]; then
  az rest --method get \
    --url "https://management.azure.com/subscriptions/$SUB/resourceGroups/$RG/providers/Microsoft.Authorization/roleEligibilityScheduleInstances?api-version=2020-10-01" \
    -o json > "$OUT/pim-eligibilities.json" 2>/dev/null || echo '{"note":"PIM query failed or not licensed"}' > "$OUT/pim-eligibilities.json"
  az rest --method get \
    --url "https://management.azure.com/subscriptions/$SUB/resourceGroups/$RG/providers/Microsoft.Authorization/roleAssignmentScheduleInstances?api-version=2020-10-01" \
    -o json > "$OUT/pim-active.json" 2>/dev/null || true
fi

# 4. Key Vault secret inventory: names + dates only
if [ -n "$KV" ]; then
  az keyvault secret list --vault-name "$KV" \
    --query "[].{name:name,updated:attributes.updated,expires:attributes.expires,enabled:attributes.enabled}" \
    -o json > "$OUT/kv-secrets.json" 2>/dev/null || echo '[]' > "$OUT/kv-secrets.json"
fi

# 5. SharePoint Sites.Selected grants (Graph)
if [ -n "$SITE" ]; then
  az rest --method get --url "https://graph.microsoft.com/v1.0/sites/$SITE/permissions" \
    -o json > "$OUT/site-permissions.json" 2>/dev/null || echo '{"note":"Graph query needs Sites.FullControl.All or site admin"}' > "$OUT/site-permissions.json"
fi

# 6. Foundry connections (names + auth type only)
AIF=$(az cognitiveservices account list -g "$RG" --query "[?kind=='AIServices'].name | [0]" -o tsv 2>/dev/null || true)
if [ -n "$AIF" ]; then
  az rest --method get \
    --url "https://management.azure.com/subscriptions/$SUB/resourceGroups/$RG/providers/Microsoft.CognitiveServices/accounts/$AIF/connections?api-version=2025-04-01-preview" \
    --query "value[].{name:name,category:properties.category,authType:properties.authType,shared:properties.isSharedToAll}" \
    -o json > "$OUT/foundry-connections.json" 2>/dev/null || true
fi

# 7. GitHub collaborators (if gh is available and GITHUB_REPO is set)
if command -v gh >/dev/null && [ -n "${GITHUB_REPO:-}" ]; then
  gh api "repos/$GITHUB_REPO/collaborators" --jq '[.[]|{login,permissions}]' > "$OUT/github-collaborators.json" 2>/dev/null || true
  gh api "repos/$GITHUB_REPO/branches/main/protection" > "$OUT/github-branch-protection.json" 2>/dev/null || true
fi

# 8. Summary table for the reviewer
{
  echo "# Access snapshot $(date -u +%Y-%m-%dT%H:%MZ) ${TAG#-}"
  echo
  echo "| Group | Members | Owners |"; echo "|---|---|---|"
  for f in "$OUT"/groups-*.json; do
    case "$f" in *.owners.json) continue;; esac
    g=$(basename "$f" .json); g=${g#groups-}
    echo "| $g | $(jq -r '[.[].upn]|join(", ")' "$f") | $(jq -r 'join(", ")' "$OUT/groups-$g.owners.json") |"
  done
  echo
  echo "Direct USER role assignments (must be empty): $(jq -r '[.[]|select(.type=="User")|.principal]|join(", ")' "$OUT/role-assignments.json")"
  echo "Permanent privileged GROUP assignments (exception only): $(jq -r '[.[]|select(.type=="Group" and (.role|test("Contributor|Owner|User Access Administrator|Azure AI Developer|Secrets Officer")))|"\(.principal):\(.role)"]|join(", ")' "$OUT/role-assignments.json")"
  [ -f "$OUT/kv-secrets.json" ] && echo "Key Vault secrets older than 90 days: $(jq -r --arg d "$(date -u -d '-90 days' +%Y-%m-%dT%H:%M:%S 2>/dev/null || date -u -v-90d +%Y-%m-%dT%H:%M:%S)" '[.[]|select(.updated < $d)|.name]|join(", ")' "$OUT/kv-secrets.json")"
} > "$OUT/SUMMARY.md"

echo "done: $(ls "$OUT" | wc -l) files; open $OUT/SUMMARY.md"
