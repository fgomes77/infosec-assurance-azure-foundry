#!/usr/bin/env bash
# Fallback / CI helper: create or verify the Foundry project connections named
# in ../registry.json via `az rest`, reading every secret from Key Vault by
# secret NAME (no secret ever appears in the repo or in CI variables).
# Usage:
#   ./create_connections.sh --verify            # list missing conn-* and exit 1 if any
#   ./create_connections.sh                     # create the missing ones
# Env (setup/.env): AZURE_SUBSCRIPTION_ID AZURE_RESOURCE_GROUP FOUNDRY_ACCOUNT_NAME
#   FOUNDRY_PROJECT_NAME KEY_VAULT_NAME, plus per-connection target URLs below.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
API="2025-06-01"
BASE="https://management.azure.com/subscriptions/${AZURE_SUBSCRIPTION_ID:?}/resourceGroups/${AZURE_RESOURCE_GROUP:?}/providers/Microsoft.CognitiveServices/accounts/${FOUNDRY_ACCOUNT_NAME:?}/projects/${FOUNDRY_PROJECT_NAME:?}/connections"
VERIFY=0; [ "${1:-}" = "--verify" ] && VERIFY=1

# Connections carrying "enabled": false in the registry are provisioned later
# (today: conn-sharepoint-grounding - preview tool, finding C9) and are skipped
# here so --verify does not fail on a connection nothing is attached to.
wanted=$(python3 -c "import json,sys;r=json.load(open('$HERE/../registry.json'));print(' '.join(sorted({c['foundry_connection'] for c in r['connections'].values() if 'foundry_connection' in c and c.get('enabled', True)})))")
existing=$(az rest --method GET --url "${BASE}?api-version=${API}" --query "value[].name" -o tsv 2>/dev/null | tr '\n' ' ')
missing=""
for c in $wanted; do case " $existing " in *" $c "*) ;; *) missing="$missing $c";; esac; done
if [ -z "$missing" ]; then echo "connections: all present ($wanted)"; exit 0; fi
echo "connections missing:$missing"
[ "$VERIFY" = 1 ] && exit 1

kv() { az keyvault secret show --vault-name "${KEY_VAULT_NAME:?}" --name "$1" --query value -o tsv; }
mk_keyed() { # name target header secret-name
  az rest --method PUT --url "${BASE}/$1?api-version=${API}" --body "$(python3 -c "
import json,sys;print(json.dumps({'properties':{'category':'CustomKeys','target':sys.argv[1],'authType':'CustomKeys','isSharedToAll':False,'credentials':{'keys':{sys.argv[2]:sys.argv[3]}},'metadata':{'managedBy':'create_connections.sh'}}}))" "$2" "$3" "$(kv "$4")")" >/dev/null && echo "created $1"; }
mk_mi() { # name (Graph on the account managed identity)
  az rest --method PUT --url "${BASE}/$1?api-version=${API}" --body '{"properties":{"category":"CustomKeys","target":"https://graph.microsoft.com/v1.0","authType":"ManagedIdentity","isSharedToAll":false,"metadata":{"audience":"https://graph.microsoft.com","managedBy":"create_connections.sh"}}}' >/dev/null && echo "created $1"; }

for c in $missing; do
  case "$c" in
    conn-jira-cloud)         mk_keyed "$c" "${JIRA_BASE_URL:?}" Authorization "${KV_SECRET_JIRA:-jira-basic-auth}" ;;
    conn-jira-assets)        mk_keyed "$c" "${JIRA_ASSETS_BASE_URL:?}" Authorization "${KV_SECRET_JIRA_ASSETS:-jira-assets-bearer}" ;;
    conn-confluence)         mk_keyed "$c" "${CONFLUENCE_BASE_URL:?}" Authorization "${KV_SECRET_CONFLUENCE:-confluence-basic-auth}" ;;
    conn-onetrust)           mk_keyed "$c" "${ONETRUST_BASE_URL:?}" Authorization "${KV_SECRET_ONETRUST:-onetrust-bearer}" ;;
    conn-securityscorecard)  mk_keyed "$c" "https://api.securityscorecard.io" Authorization "${KV_SECRET_SSC:-securityscorecard-token}" ;;
    conn-iaf-api)            mk_keyed "$c" "${IAF_BASE_URL:?}" X-API-Key "${KV_SECRET_IAF:-iaf-api-key}" ;;
    conn-osint-proxy)        mk_keyed "$c" "${DELIVERY_FUNCTION_BASE_URL:?}" x-functions-key "${KV_SECRET_OSINT_PROXY:-delivery-function-key}" ;;
    conn-azure-devops)       mk_keyed "$c" "${AZURE_DEVOPS_ORG_URL:?}" Authorization "${KV_SECRET_ADO:-azure-devops-reader-token}" ;;
    # finding C10: the ENX gateway MCP bearer lives in this connection, not in
    # run-time tool_resources.mcp[].headers (../mcp/enx-gateway.json)
    conn-enx-gateway)        mk_keyed "$c" "${ENX_GATEWAY_MCP_URL:?}" Authorization "${KV_SECRET_ENX_GATEWAY:-enx-gateway-token}" ;;
    conn-defender-graph|conn-sharepoint-graph|conn-entra-iam|conn-exchange-graph) mk_mi "$c" ;;
    conn-teams-graph|conn-m365-personal) echo "skip $c: delegated OAuth2 connection - create in the portal with the delegated app registration (README §Connections)";;
    conn-sharepoint-grounding) echo "skip $c: SharePoint grounding tool is preview and OBO-only (finding C9) - registry entry has enabled=false; create in the portal only after GA + the licence decision";;
    bing-grounding)          echo "skip $c: provisioned by infra/main.bicep (enableWebSearch=true)";;
    *)                       echo "unknown connection $c - add a case here";;
  esac
done
