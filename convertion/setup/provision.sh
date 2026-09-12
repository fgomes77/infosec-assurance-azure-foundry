#!/usr/bin/env bash
# Provision the Azure AI Foundry environment (infra/main.bicep).
# Prereqs: az CLI logged in (az login), .env filled in from .env.example.
set -euo pipefail
cd "$(dirname "$0")"

[ -f .env ] && set -a && . ./.env && set +a
: "${AZURE_SUBSCRIPTION_ID:?Set AZURE_SUBSCRIPTION_ID in .env}"
: "${AZURE_LOCATION:?Set AZURE_LOCATION in .env to an EU region (e.g. swedencentral, westeurope) — infra/main.bicep restricts location to the EU @allowed list}"
: "${AZURE_RESOURCE_GROUP:?Set AZURE_RESOURCE_GROUP in .env}"

az account set --subscription "$AZURE_SUBSCRIPTION_ID"

# Refuse a non-EU AZURE_LOCATION here, the same way CI gate [4b] does, so a
# hand-run provision cannot put the platform outside the EU/EEA and then be
# caught only at the next pull request.
echo ">> Checking EU residency of AZURE_LOCATION=$AZURE_LOCATION"
python3 ../ci/tests/test_residency.py

# `[ … ] && PARAMS=…` would return 1 in the dev case and kill the script under
# `set -e`, so this is written as a plain if.
if [ "${ENVIRONMENT_NAME:-dev}" = "prod" ]; then
  PARAMS="../infra/main.parameters.prod.json"
else
  PARAMS="../infra/main.parameters.json"
fi

echo ">> Validating infra (build + lint + EU residency policy + what-if)"
PARAMS="$(basename "$PARAMS")" ../infra/validate.sh --what-if "$AZURE_RESOURCE_GROUP"

echo ">> Creating resource group $AZURE_RESOURCE_GROUP in $AZURE_LOCATION"
az group create --name "$AZURE_RESOURCE_GROUP" --location "$AZURE_LOCATION" --output none

echo ">> Deploying infra/main.bicep"
az deployment group create \
  --resource-group "$AZURE_RESOURCE_GROUP" \
  --template-file ../infra/main.bicep \
  --parameters "$PARAMS" --parameters location="$AZURE_LOCATION" \
  --query "properties.outputs" --output json | tee provision-outputs.json

# ---------------------------------------------------------------------------
# Pass 2 (prod, finding C22): after enterprise/landing-zone.bicep has created
# the CMK key and granted `Key Vault Crypto Service Encryption User` to the
# Foundry, storage, Cosmos DB and AI Search identities, re-run this deployment
# with the key URI so the account and the BYO stores adopt CMK:
#   az deployment group create -g "$AZURE_RESOURCE_GROUP" \
#     --template-file ../infra/main.bicep \
#     --parameters ../infra/main.parameters.prod.json \
#     cmkKeyUri="https://{baseName}-kv.{vaultSuffix}/keys/infosec-foundry-cmk"
#
# Defender for Cloud AI threat protection (finding C17) is a SUBSCRIPTION
# setting, not a resource-group one:
#   az deployment sub create -l "$AZURE_LOCATION" \
#     --template-file ../infra/defender-ai.bicep \
#     -p enableAiPlan=true enableAiUserPromptEvidence=false
#
# Standard agent setup (finding C5) is bound by an IMMUTABLE capability host:
# NEVER run ../deploy.sh (agents) before this deployment has succeeded with
# enableStandardAgentSetup=true — the host cannot be added once the first
# agent exists, and deploy.sh's pre-flight refuses to continue without it.
# ---------------------------------------------------------------------------

# Write the Bicep outputs straight back into .env, so nobody copies an
# endpoint by hand (setup/.env.example marks these keys as provision-written).
python3 - <<'ENVBACK'
import json, re, pathlib
o = {k: v['value'] for k, v in json.load(open('provision-outputs.json')).items()}
wanted = {
    'PROJECT_ENDPOINT': 'projectEndpoint',
    'MODEL_DEPLOYMENT_NAME': 'modelDeploymentName',
    'REASONING_MODEL_DEPLOYMENT_NAME': 'reasoningModelDeploymentName',
    'LIGHT_MODEL_DEPLOYMENT_NAME': 'lightModelDeploymentName',
    'BING_CONNECTION_NAME': 'bingConnectionName',
    'KEY_VAULT_NAME': 'keyVaultName',
    'DELIVERY_FUNCTION_APP': 'deliveryFunctionApp',
    'DELIVERY_FUNCTION_BASE_URL': 'deliveryFunctionBaseUrl',
    'LOGIC_APP_NAME': 'logicAppName',
    'CONTAINER_REGISTRY': 'registryLoginServer',
    'DOCINTEL_ENDPOINT': 'docIntelEndpoint',
}
m = {k: o[v] for k, v in wanted.items() if v in o}
missing = sorted(k for k, v in wanted.items() if v not in o)
p = pathlib.Path('.env')
s = p.read_text() if p.exists() else ''
for k, v in m.items():
    if re.search(rf'^{k}=', s, re.M):
        s = re.sub(rf'^{k}=.*$', f'{k}={v}', s, flags=re.M)
    else:
        s = s.rstrip('\n') + f'\n{k}={v}\n'
p.write_text(s)
print('>> .env updated:', ', '.join(sorted(m)))
if missing:
    print('>> not in the deployment outputs, fill by hand:', ', '.join(missing))
ENVBACK

echo ""
echo ">> Assign roles by group, not by user: deploy ../team/rbac.bicep with the group object ids (team/TEAM_MODEL.md §7)"
echo ">> Then bootstrap SharePoint ids + the Function's Sites.Selected grant:"
echo "python3 ../scripts/sharepoint_bootstrap.py --site-url https://{tenant}.sharepoint.com/sites/{site} --function-app-id {function-mi-appId}"
