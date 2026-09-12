#!/usr/bin/env bash
# Provision / verify the Entra ID groups and role assignments of the
# least-privilege team model (team/least-privilege/IDENTITY_RBAC.md).
#
#   ./provision_identity.sh --plan      print what would be created (default)
#   ./provision_identity.sh --apply     create missing groups, set owners,
#                                       write object ids into ../infra/rbac.parameters.json
#   ./provision_identity.sh --verify    compare live role assignments in the RG
#                                       with the model; exit 1 on drift
#
# Requires: az CLI (az login as a Groups Administrator for --apply; any
# reader of the RG for --verify), jq. Reads ../entra/groups.json and
# ../../../setup/.env (AZURE_RESOURCE_GROUP). No secrets are read or written.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
GROUPS_JSON="$HERE/../entra/groups.json"
PARAMS_JSON="$HERE/../infra/rbac.parameters.json"
ENV_FILE="$HERE/../../../setup/.env"
MODE="${1:---plan}"

[ -f "$ENV_FILE" ] && set -a && . "$ENV_FILE" && set +a
RG="${AZURE_RESOURCE_GROUP:-rg-infosec-foundry}"

need() { command -v "$1" >/dev/null || { echo "missing: $1" >&2; exit 2; }; }
need az; need jq

groups() { jq -r '.groups[].name' "$GROUPS_JSON"; }

case "$MODE" in
  --plan)
    echo "Groups (from $GROUPS_JSON):"
    jq -r '.groups[] | "  \(.name)\t owners=\(.owners|join(","))\t members=\(.members|length)\t eligible=\((.eligibleMembers//[])|length)"' "$GROUPS_JSON"
    echo "Service principals:"
    jq -r '.servicePrincipals[] | "  \(.name)\t \(.type)"' "$GROUPS_JSON"
    echo
    echo "Apply order: --apply (groups + owners) -> fill placeholders in $PARAMS_JSON"
    echo "  -> az deployment group create -g $RG -f ../infra/rbac.bicep -p ../infra/rbac.parameters.json"
    echo "  -> grant Sites.Selected (IDENTITY_RBAC.md §3) -> --verify"
    ;;

  --apply)
    for g in $(groups); do
      existing=$(az ad group list --display-name "$g" --query "[0].id" -o tsv)
      if [ -z "$existing" ]; then
        echo "creating $g"
        existing=$(az ad group create --display-name "$g" --mail-nickname "$g" \
                    --description "$(jq -r --arg g "$g" '.groups[]|select(.name==$g)|.purpose' "$GROUPS_JSON")" \
                    --query id -o tsv)
      else
        echo "exists   $g ($existing)"
      fi
      # Owners are UPN placeholders until the operator replaces them in groups.json
      for owner in $(jq -r --arg g "$g" '.groups[]|select(.name==$g)|.owners[]' "$GROUPS_JSON"); do
        case "$owner" in
          \{*\}) echo "  owner placeholder $owner - replace in groups.json before apply" ;;
          *) oid=$(az ad user show --id "$owner" --query id -o tsv 2>/dev/null || az ad group show --group "$owner" --query id -o tsv)
             az ad group owner add --group "$existing" --owner-object-id "$oid" >/dev/null 2>&1 || true ;;
        esac
      done
      # Members (placeholders skipped the same way); eligible members are PIM-for-Groups, not direct members
      for m in $(jq -r --arg g "$g" '.groups[]|select(.name==$g)|.members[]' "$GROUPS_JSON"); do
        case "$m" in
          \{*\}) echo "  member placeholder $m - replace in groups.json before apply" ;;
          *) mid=$(az ad user show --id "$m" --query id -o tsv)
             az ad group member add --group "$existing" --member-id "$mid" >/dev/null 2>&1 || true ;;
        esac
      done
      # Write the object id into the parameters file placeholder
      key="{objectId:$g}"
      tmp=$(mktemp); jq --arg k "$key" --arg v "$existing" 'walk(if . == $k then $v else . end)' "$PARAMS_JSON" > "$tmp" && mv "$tmp" "$PARAMS_JSON"
    done
    echo "done - review $PARAMS_JSON, then deploy ../infra/rbac.bicep"
    ;;

  --verify)
    drift=0
    echo "Live role assignments in $RG (humans must appear only via sg-infosec-foundry-* groups):"
    az role assignment list --resource-group "$RG" --include-inherited \
      --query "[].{principal:principalName,type:principalType,role:roleDefinitionName,scope:scope}" -o table
    humans=$(az role assignment list --resource-group "$RG" --include-inherited \
      --query "[?principalType=='User'].principalName" -o tsv)
    if [ -n "$humans" ]; then
      echo "DRIFT: direct user assignments found (model requires groups only):"; echo "$humans"; drift=1
    fi
    # Privileged roles must not be permanent on humans/groups when PIM is enabled
    priv=$(az role assignment list --resource-group "$RG" --include-inherited \
      --query "[?principalType=='Group' && (roleDefinitionName=='Contributor' || roleDefinitionName=='Owner' || roleDefinitionName=='User Access Administrator' || roleDefinitionName=='Azure AI Developer' || roleDefinitionName=='Key Vault Secrets Officer')].[principalName,roleDefinitionName]" -o tsv)
    if [ -n "$priv" ]; then
      echo "CHECK: permanent privileged group assignments (allowed only when enablePim=false, record as exception):"; echo "$priv"; drift=1
    fi
    for g in $(groups); do
      az ad group show --group "$g" --query displayName -o tsv >/dev/null 2>&1 || { echo "MISSING group $g"; drift=1; }
    done
    [ $drift -eq 0 ] && echo "OK: no drift against the least-privilege model" || { echo "drift detected"; exit 1; }
    ;;
  *) echo "usage: $0 [--plan|--apply|--verify]" >&2; exit 2 ;;
esac
