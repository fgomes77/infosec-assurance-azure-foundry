#!/usr/bin/env bash
# Quarterly access-review evidence collector (team/TEAM_MODEL.md §15).
# READ-ONLY: lists group memberships, role assignments, PIM-relevant
# assignments, Foundry connections and Key Vault secret ages. Writes nothing
# to Azure. Output goes to a dated folder you then file under
# SharePoint Governance/AccessReviews/<yyyy>-Q<n>/ .
#
#   ./access-review.sh            full run (needs az login; Reader on the RG,
#                                 Directory read for group membership)
#   ./access-review.sh --quick    role assignments only (used by deploy.sh)
#
# Standards: ISO/IEC 27001:2022 A.5.18 (review of access rights), A.8.2
# (privileged access); DORA Art. 9(4)(c); NIS2 Art. 21(2)(i).
set -euo pipefail
cd "$(dirname "$0")"

[ -f ../setup/.env ] && set -a && . ../setup/.env && set +a
RG="${AZURE_RESOURCE_GROUP:?Set AZURE_RESOURCE_GROUP (setup/.env)}"
OUT="${ACCESS_REVIEW_OUT:-../build/access-review/$(date -u +%Y-%m-%d)}"
mkdir -p "$OUT"
QUICK=""; [ "${1:-}" = "--quick" ] && QUICK=1

GROUPS=(
  sg-infosec-foundry-users
  sg-infosec-foundry-report-approvers
  sg-infosec-foundry-senior-approvers
  sg-infosec-foundry-owner
  sg-infosec-foundry-admin-pim
  sg-infosec-foundry-breakglass
  sg-infosec-foundry-readers
)

echo ">> [1] Azure role assignments in $RG (expected set: team/rbac.bicep)"
az role assignment list --resource-group "$RG" --include-inherited \
  --query "[].{principal:principalName,type:principalType,role:roleDefinitionName,scope:scope}" \
  -o table | tee "$OUT/role-assignments.txt"

echo ">> [1b] Standing privileged roles on HUMANS (must be empty)"
az role assignment list --resource-group "$RG" --include-inherited \
  --query "[?principalType=='User' && (roleDefinitionName=='Owner' || roleDefinitionName=='Contributor' || roleDefinitionName=='User Access Administrator' || roleDefinitionName=='Key Vault Secrets Officer' || roleDefinitionName=='Logic App Contributor' || roleDefinitionName=='Website Contributor')].{principal:principalName,role:roleDefinitionName}" \
  -o table | tee "$OUT/standing-privileged-humans.txt"

if [ -n "$QUICK" ]; then
  echo ">> quick mode done -> $OUT"; exit 0
fi

echo ">> [2] Entra group memberships"
for g in "${GROUPS[@]}"; do
  echo "--- $g" | tee -a "$OUT/group-members.txt"
  gid=$(az ad group show --group "$g" --query id -o tsv 2>/dev/null || true)
  if [ -z "$gid" ]; then echo "  (group not found)" | tee -a "$OUT/group-members.txt"; continue; fi
  az ad group owner list --group "$gid" --query "[].userPrincipalName" -o tsv \
    | sed 's/^/  owner: /' | tee -a "$OUT/group-members.txt"
  az ad group member list --group "$gid" --query "[].{upn:userPrincipalName,type:'@odata.type'}" -o tsv \
    | sed 's/^/  member: /' | tee -a "$OUT/group-members.txt"
done

echo ">> [3] Foundry connections (names + auth type; never values)"
ACCOUNT=$(az cognitiveservices account list -g "$RG" --query "[?kind=='AIServices'].name | [0]" -o tsv)
if [ -n "$ACCOUNT" ]; then
  az rest --method get \
    --url "https://management.azure.com/subscriptions/${AZURE_SUBSCRIPTION_ID}/resourceGroups/${RG}/providers/Microsoft.CognitiveServices/accounts/${ACCOUNT}/connections?api-version=2025-04-01-preview" \
    --query "value[].{name:name,category:properties.category,auth:properties.authType}" -o table \
    | tee "$OUT/foundry-connections.txt"
fi

echo ">> [4] Key Vault secret ages (rotation table: team/TEAM_MODEL.md §10)"
KV=$(az keyvault list -g "$RG" --query "[0].name" -o tsv 2>/dev/null || true)
if [ -n "$KV" ]; then
  az keyvault secret list --vault-name "$KV" \
    --query "[].{name:name,updated:attributes.updated,expires:attributes.expires,enabled:attributes.enabled}" -o table \
    | tee "$OUT/keyvault-secret-ages.txt"
else
  echo "  (no Key Vault in $RG)" | tee "$OUT/keyvault-secret-ages.txt"
fi

echo ">> [5] Managed identities and app registrations of the platform"
az identity list -g "$RG" --query "[].{name:name,principalId:principalId}" -o table | tee "$OUT/identities.txt" || true
az functionapp list -g "$RG" --query "[].{name:name,principalId:identity.principalId}" -o table | tee -a "$OUT/identities.txt" || true
az logicapp list -g "$RG" --query "[].{name:name,principalId:identity.principalId}" -o table | tee -a "$OUT/identities.txt" || true

echo ">> [6] Registry write_connections (must be none)"
python3 - <<'PY' | tee "$OUT/write-connections.txt"
import json, pathlib
reg = json.loads(pathlib.Path("../integrations/registry.json").read_text(encoding="utf-8"))
grants = {a: v.get("write_connections") for a, v in reg["agents"].items() if v.get("write_connections")}
print("write_connections grants:", grants or "none")
PY

echo ""
echo ">> Evidence written to $OUT — attach to Governance/AccessReviews/$(date -u +%Y)-Q$((($(date -u +%-m)-1)/3+1))/"
echo ">> Reviewers: users/approvers groups = owner; owner/senior/pim/breakglass groups = line manager (team/TEAM_MODEL.md §15)."
