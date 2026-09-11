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

## Human approval gates

Every **submission of record** in these workflows — creating a Jira issue
or ticket, submitting a finding to the IAF API, uploading a DPIA report or
DeepSearch dashboard to SharePoint — is preceded by a
**suspend-until-approved** gate. Notification-only steps (posting a summary
card to Teams) are not gated. This implements the policy in
`../governance/HUMAN_APPROVAL.md`.

Each gate is three actions, named after the submission it guards:

1. `Send_approval_request_<subject>` — HTTP POST to
   `@parameters('approvalWebhookUrl')` (securestring, default empty) with
   the draft payload (or a description/link), the target system, the
   correlation id (`@{workflow().run.name}`), and a callback instruction.
2. `Wait_for_approval_<subject>` — an **HttpWebhook** action whose
   *subscribe* posts the run's callback URL (`@{listCallbackUrl()}`) to the
   same approval webhook. The workflow run **suspends** at this action —
   nothing is written anywhere — until the approval system POSTs the
   decision to the callback URL.
3. `Check_approval_decision_<subject>` — an If condition on
   `@body('Wait_for_approval_<subject>')?['decision']`: only `approved`
   runs the original submit action; the else branch records the rejection
   (a Compose annotation) and the submission is skipped.

**Wiring the approval side.** Point `approvalWebhookUrl` at either:

- a **Power Automate** flow ("When an HTTP request is received"): render
  the draft as a Teams **Approval** to the reviewer, then have the flow
  POST `{"decision": "approved" | "rejected", "approver": "<upn>"}` to
  the `callbackUrl` it received in the subscribe body; or
- an **Azure Function** that renders the draft (e.g. as an adaptive card
  or review page), collects the human decision, and posts the same JSON
  to the `callbackUrl`.

The `correlationId` in both the notification and the subscribe body ties
the approval back to the suspended run. Any decision value other than
`approved` (including `rejected`) skips the submission.

**Expiry.** Each `Wait_for_approval_*` action has
`"limit": {"timeout": "P3D"}`: an item not approved within **3 days**
times out, the gate fails, and the submission never happens — unapproved
drafts expire rather than submit late. Note for
`defender-incident-brief.json`: the HTTP 200 response to the Defender
webhook caller is returned *before* the gate (status
`brief_pending_approval`), so the caller is not held while a human
reviews.

## The four workflows

| File | Trigger | Steps | Integrations |
|---|---|---|---|
| `onetrust-assessment-intake.json` | Recurrence, daily | List OneTrust assessments completed since last run → for each: run the **dpia** agent on the assessment reference → **approval gate** → upload the report to SharePoint (Graph) → post a summary card to Teams | OneTrust API, Foundry (dpia), Graph/SharePoint, Teams webhook |
| `defender-incident-brief.json` | HTTP request (webhook from a Defender/Sentinel automation rule) | Run the **cyber-forum** agent on the incident JSON → respond 200 to the caller (`brief_pending_approval`) → **approval gate** → create a Jira issue containing the brief | Defender/Sentinel, Foundry (cyber-forum), Jira |
| `scheduled-deepsearch.json` | Recurrence, weekly | Read the supplier watchlist from a SharePoint list (Graph) → for each supplier: run the **deepsearch-protocol** agent → **approval gate** → store the HTML dashboard in SharePoint → if the score is below threshold, **approval gate** → create a Jira ticket | Graph/SharePoint, Foundry (deepsearch-protocol), Jira |
| `jira-finding-sync.json` | Recurrence, hourly | JQL-search Jira for TPRM finding tickets updated in the last hour → for each: **approval gate** → submit the finding status to the IAF API → on failure, add a Jira comment flagging the sync error | Jira, IAF API |

Notes: the Foundry run is asynchronous — each workflow polls the run with
an `Until` loop before reading messages. Long DeepSearch runs are why that
workflow (and not M365 Copilot — see
`../integrations/copilot/README.md`) is the right channel for
report-generating agents. If the ENX Gateway MCP server
(`../integrations/mcp/enx-gateway.json`) is attached to an agent, the tool
calls happen inside the Foundry run; the workflows need no extra steps.
