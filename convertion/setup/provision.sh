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

ENDPOINT=$(python3 -c "import json;print(json.load(open('provision-outputs.json'))['projectEndpoint']['value'])")
echo ""
echo ">> Done. Add to your .env:"
echo "PROJECT_ENDPOINT=$ENDPOINT"
echo ""
echo ">> Grant yourself data-plane access (once):"
echo "az role assignment create --assignee \$(az ad signed-in-user show --query id -o tsv) \\"
echo "  --role 'Azure AI User' --scope \$(az group show -n $AZURE_RESOURCE_GROUP --query id -o tsv)"
