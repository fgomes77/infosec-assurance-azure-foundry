# Secrets — Key Vault names, binding and population

Every credential this platform uses lives in the Key Vault created by
`../infra/main.bicep` (`{baseName}-kv`, name in `.env` as `KEY_VAULT_NAME`).
Nothing is stored in the repository, in `.env`, in a workflow definition or in
an app setting value. App settings hold **Key Vault references**
(`@Microsoft.KeyVault(VaultName=…;SecretName=…)`) resolved at runtime by the
app's managed identity; Foundry connections hold the secret by reference the
same way. This file is the operator's copy of the naming table in
`../infra/README.md` §Secrets — change both together.

## Names of record

| Secret name | Bound as | Used by |
|---|---|---|
| `kv-delivery-function-key` | `DELIVERY_FUNCTION_KEY` | Logic Apps → delivery Function |
| `kv-approval-webhook-url` | `APPROVAL_WEBHOOK_URL` | the approval gates in every pipeline |
| `kv-teams-webhook-url` | `TEAMS_WEBHOOK_URL` | Teams notifications |
| `kv-jira-api-token` | `JIRA_API_TOKEN` | `jira-finding-sync`, the Jira Foundry connection |
| `kv-onetrust-api-token` | `ONETRUST_API_TOKEN` | `onetrust-assessment-intake`, the OneTrust connection |
| `kv-iaf-client-secret` | `IAF_CLIENT_SECRET` | the IAF API Foundry connection |
| `kv-confluence-api-token` | Foundry connection (by reference) | agents (read-only Confluence) |
| `kv-ssc-api-key` | Foundry connection (by reference) | agents (SecurityScorecard, read-only) |
| `kv-enx-gateway-token` | Foundry connection (by reference) | agents (ENX gateway MCP) |
| `office-tools-function-key` | `OFFICE_TOOLS_KEY` (delivery app only) | delivery Function → office-tools Function |

The office-tools app itself never receives this setting: it is the callee, and
`OFFICE_TOOLS_BASE_URL` + `OFFICE_TOOLS_KEY` on the delivery app are the only
link between the two apps (`../infra/delivery.bicep`).

## Populating

Feed the value from the deployment pipeline's own environment or from an
operator's terminal — never from a file in the repository, never as a command
argument (it lands in shell history and in process listings):

```bash
az keyvault secret set --vault-name "$KEY_VAULT_NAME" -n kv-jira-api-token --value @-
# then paste the value and press Ctrl-D
```

Rotation is a Tier-B change (`../operations/CHANGE_MANAGEMENT.md` §1): rotate
at the source system first, `az keyvault secret set` the new version, then
restart the consuming app so the reference re-resolves. Key Vault keeps the
previous version for rollback; do not disable it until the new one is proven.

## What must never become a secret here

Placeholder UPNs, group names, site ids, drive ids and item ids are **not**
secrets — they belong in `.env` and in the parameter files. Conversely, no
hostname, e-mail address or real UPN belongs in this file or in any committed
artefact; `../scripts/scan_secrets.py` (and `verify_kit.py`) fail the build on
either mistake.

Controls: ISO 27001:2022 A.5.17, A.8.24; DORA Art. 9(4)(c).
