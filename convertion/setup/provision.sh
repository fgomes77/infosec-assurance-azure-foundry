#!/usr/bin/env bash
# Provision the Azure AI Foundry environment (infra/main.bicep).
# Prereqs: az CLI logged in (az login), .env filled in from .env.example.
set -euo pipefail
cd "$(dirname "$0")"

[ -f .env ] && set -a && . ./.env && set +a
: "${AZURE_SUBSCRIPTION_ID:?Set AZURE_SUBSCRIPTION_ID in .env}"
: "${AZURE_LOCATION:?Set AZURE_LOCATION in .env (e.g. swedencentral, eastus2)}"
: "${AZURE_RESOURCE_GROUP:?Set AZURE_RESOURCE_GROUP in .env}"

az account set --subscription "$AZURE_SUBSCRIPTION_ID"

echo ">> Creating resource group $AZURE_RESOURCE_GROUP in $AZURE_LOCATION"
az group create --name "$AZURE_RESOURCE_GROUP" --location "$AZURE_LOCATION" --output none

echo ">> Deploying infra/main.bicep"
az deployment group create \
  --resource-group "$AZURE_RESOURCE_GROUP" \
  --template-file ../infra/main.bicep \
  --parameters ../infra/main.parameters.json \
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

ENDPOINT=$(python3 -c "import json;print(json.load(open('provision-outputs.json'))['projectEndpoint']['value'])")
echo ""
echo ">> Done. Add to your .env:"
echo "PROJECT_ENDPOINT=$ENDPOINT"
echo ""
echo ">> Assign roles by group, not by user: deploy ../team/rbac.bicep with the group object ids (team/TEAM_MODEL.md §7)"
echo ">> Then bootstrap SharePoint ids + the Function's Sites.Selected grant:"
echo "python3 ../scripts/sharepoint_bootstrap.py --site-url https://{tenant}.sharepoint.com/sites/{site} --function-app-id {function-mi-appId}"
