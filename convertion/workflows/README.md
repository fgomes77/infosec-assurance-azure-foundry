# Workflow Layer — Logic Apps Orchestration

Claude's **Routines** (scheduled/self-triggering runs) have no equivalent
inside Azure AI Foundry agents. This folder replaces them with **Azure
Logic Apps (Standard)** workflow definitions that call the agents on
schedules and events, and move their outputs to where people work
(SharePoint, Teams, Jira, the IAF API).

Each `.json` file here is a complete Logic Apps *workflow definition*
document (`definition` + `parameters`) that you import into a Logic Apps
Standard app. Agent invocation uses plain **HTTP actions** against the
Foundry Agents data-plane REST API (create thread → post message → create
run → poll → read messages), so no premium connectors are required for the
Foundry side.

## Deployment

1. Create a Logic Apps **Standard** app (workflow runtime on App Service):
   `az logicapp create -g {rg} -n {logicapp-name} --storage-account {sa} -p {plan}`
2. Add each workflow: in the portal open the Logic App → *Workflows* →
   *Add* → paste the file's `definition` into the code view (or deploy the
   files under `{app}/wf-name/workflow.json` via `az logicapp deployment
   source config-zip` / VS Code Azure Logic Apps extension).
3. Set the workflow **parameters** (Foundry endpoint, agent ids, site ids,
   webhook URLs) as app settings or in the parameters file — every
   tenant-specific value in these definitions is a `{placeholder}`.

## Authentication

- **Foundry Agents API:** enable the Logic App's **system-assigned managed
  identity** and grant it the Foundry project data-plane role
  (`Azure AI User` on the AI Foundry project). The HTTP actions use
  `"authentication": {"type": "ManagedServiceIdentity", "audience":
  "https://ai.azure.com"}` — no keys.
- **Microsoft Graph** (SharePoint upload/list read): same managed identity,
  granted the needed Graph application permissions
  (`Sites.ReadWrite.All` or Sites.Selected) via Entra admin consent;
  audience `https://graph.microsoft.com`.
- **OneTrust / Jira / IAF API:** API tokens referenced as
  `@parameters('...')`; store the real values in **Azure Key Vault** and
  bind them through app settings (`@Microsoft.KeyVault(SecretUri=...)`).
  Never commit tokens.
- **Teams:** incoming-webhook URL of the target channel, also a parameter.

## Parameterisation

All definitions share the same convention: `foundryEndpoint` (the project
endpoint URL), `apiVersion`, one `*AgentId` per agent used, plus
integration-specific parameters (site/list ids, base URLs, tokens,
thresholds). Defaults are `{braced}` placeholders — replace per
environment; nothing here contains a real hostname or secret.

## The four workflows

| File | Trigger | Steps | Integrations |
|---|---|---|---|
| `onetrust-assessment-intake.json` | Recurrence, daily | List OneTrust assessments completed since last run → for each: run the **dpia** agent on the assessment reference → upload the report to SharePoint (Graph) → post a summary card to Teams | OneTrust API, Foundry (dpia), Graph/SharePoint, Teams webhook |
| `defender-incident-brief.json` | HTTP request (webhook from a Defender/Sentinel automation rule) | Run the **cyber-forum** agent on the incident JSON → create a Jira issue containing the brief → respond 200 to the caller | Defender/Sentinel, Foundry (cyber-forum), Jira |
| `scheduled-deepsearch.json` | Recurrence, weekly | Read the supplier watchlist from a SharePoint list (Graph) → for each supplier: run the **deepsearch-protocol** agent → store the HTML dashboard in SharePoint → if the score is below threshold, create a Jira ticket | Graph/SharePoint, Foundry (deepsearch-protocol), Jira |
| `jira-finding-sync.json` | Recurrence, hourly | JQL-search Jira for TPRM finding tickets updated in the last hour → for each: submit the finding status to the IAF API → on failure, add a Jira comment flagging the sync error | Jira, IAF API |

Notes: the Foundry run is asynchronous — each workflow polls the run with
an `Until` loop before reading messages. Long DeepSearch runs are why that
workflow (and not M365 Copilot — see
`../integrations/copilot/README.md`) is the right channel for
report-generating agents. If the ENX Gateway MCP server
(`../integrations/mcp/enx-gateway.json`) is attached to an agent, the tool
calls happen inside the Foundry run; the workflows need no extra steps.
