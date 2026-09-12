# Workflow Layer — Logic Apps Orchestration

Claude's **Routines** (scheduled/self-triggering runs) have no equivalent
inside Azure AI Foundry agents. This folder replaces them with **Azure
Logic Apps (Standard)** workflow definitions that call the agents on
schedules and events, and move their outputs to where people work
(SharePoint, Teams, Jira, the IAF API).

Each `.json` file here is a complete Logic Apps *workflow definition*
document (`definition` + `parameters`) that you import into a Logic Apps
Standard app. Agent invocation uses plain **HTTP actions** against the
Foundry project data plane on the GA **conversations / responses** surface
(create conversation → create a background response with
`agent_reference` → poll the response → read `output_text`), so no premium
connectors are required for the Foundry side. The classic
thread/run/message sequence is gone: the Agent Service that carried it
retires **2027-03-31** and the Assistants API it was built on retired
2026-08-26 (finding C1; `../enterprise/series/07-workflows-logic-apps.md`
§2).


> Role names follow the current Foundry RBAC naming (Foundry User / Foundry Owner /
> Foundry Account Owner / Foundry Project Manager); the underlying role definition
> GUIDs in `rbac.bicep` are unchanged — `enterprise/ENTERPRISE_BLUEPRINT.md` ID-1.

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
  (`Foundry User` on the AI Foundry project). The HTTP actions use
  `"authentication": {"type": "ManagedServiceIdentity", "audience":
  "https://ai.azure.com"}` — no keys.
- **Microsoft Graph** (read only): same managed identity, granted
  **read** application permissions only (`Sites.Selected` read on the
  InfoSec Assurance site, `Mail.Read`/`Mail.ReadWrite` on the one shared
  mailbox via an Exchange application access policy, `Calendars.Read` /
  `Mail.Read` / `Chat.Read.All` scoped to the five team accounts for
  `morning-brief`); audience `https://graph.microsoft.com`. **No workflow
  writes to SharePoint through Graph** — the delivery Function's managed
  identity is the ONLY SharePoint writer (`../sharepoint/README.md`); the
  workflows call its `/render`, `/ensure_folder`, `/upload` endpoints. The
  only Graph writes left are Teams channel/chat messages
  (`teams-post-approved`, gated) and marking a mailbox message read.
- **Foundry API version:** every definition defaults `apiVersion` to
  **`v1`** (the GA agents/conversations/responses data plane); bind it to the
  `FOUNDRY_API_VERSION` app setting so scripts (`scripts/_foundry_runtime.py`)
  and workflows pin the same data-plane version. Paths are
  `{foundryEndpoint}/openai/v1/conversations` and
  `…/openai/v1/responses[/{id}]`. Response polling always uses the
  terminal-state expression `contains(createArray('completed','failed',
  'incomplete','cancelled'), status)` — never `!= 'in_progress'` (which exits
  on `queued`). `scheduled-evaluation-redteam.json` additionally carries
  `evaluationApiVersion` (`2025-11-15-preview`) because the evaluation and
  red-team surfaces are preview.
- **OneTrust / Jira / IAF API:** API tokens referenced as
  `@parameters('...')`; store the real values in **Azure Key Vault** and
  bind them through app settings (`@Microsoft.KeyVault(SecretUri=...)`).
  Never commit tokens. For Jira prefer an OAuth 2.0 (3LO) bearer for a
  service account; the Basic API-token header is the fallback only.
- **Teams:** incoming-webhook URL of the target channel, also a parameter.

## Parameterisation

All definitions share the same convention: `foundryEndpoint` (the project
endpoint URL), `apiVersion`, one `*AgentName` **and** one `*AgentVersion`
per agent used, plus integration-specific parameters (site/list ids, base
URLs, tokens, thresholds). Defaults are `{braced}` placeholders — replace
per environment; nothing here contains a real hostname or secret.

**Agent version pinning (finding C19).** The Agents v2 runtime addresses an
agent by **name** and keeps an immutable **version** per published
definition. Every workflow therefore sends
`agent_reference: {type, name, version}` and every pipeline pins
`<agent>:<version>` — the `ref` recorded in `build/agent-versions.json` by
`create_agents.py` / `create_delivery_agents.py` / `update_templates.py`.
An empty `*AgentVersion` runs the agent's *latest* version and must not be
deployed for a pipeline of record: `verify_deployment.py` flags a run whose
version is not in the ledger. Workflows that take the agent from the caller
(`agent-fanout` tasks `agentRef`, `generic-event-intake` `agentRef`,
`scheduled-followup` `agentRef`, the `advisory-file-delivery` instance)
accept the same `<agent-name>:<version>` string and split it into the
reference; a bare name is tolerated and pins nothing.

## Human approval gates

Every **submission of record** in these workflows — creating a Jira issue
or ticket, submitting a finding to the IAF API, uploading a DPIA report or
DeepSearch dashboard to SharePoint — is preceded by a
**suspend-until-approved** gate. Notification-only steps (posting a summary
card to Teams) are not gated. This implements the policy in
`../governance/HUMAN_APPROVAL.md`.

Each gate is two actions, named after the submission it guards:

1. `Wait_for_approval_<subject>` (or `Human_approval_gate` in the delivery
   pipeline) — an **HttpWebhook** action whose *subscribe* POSTs the
   **approval request** to `@parameters('approvalWebhookUrl')`. The
   workflow run **suspends** at this action — nothing is written anywhere —
   until the approval system POSTs the decision to the callback URL.
2. `Check_approval_decision_<subject>` / `If_approved` — an If condition on
   the decision: only `approved` runs the original submit action; the else
   branch records the rejection (a Compose annotation) and the submission is
   skipped.

Agent-generated content always passes the **output-verifier** before a
gate is raised (`Run_output_verifier` → `Verifier_passed`): the charter
(`../agents/verifier_instructions.md`) makes the first line exactly
`VERDICT: PASS` or `VERDICT: FAIL`; the workflows test
`startsWith(trim(first(split(text,'\n'))),'VERDICT: PASS')` (a bare `PASS`
first line is tolerated). FAIL ends the run with a Teams notice — no gate,
no write. `jira-finding-sync` carries no agent content (pure field mapping)
and uses a deterministic pre-check instead.

### Approval-callback contract (single contract for every workflow)

*Subscribe body* (workflow → approval app): `callbackUrl`, `kind` (a key of
`../team/approval-policy.json`, e.g. `REPORT_DEEPSEARCH`, `JIRA_CREATE`,
`IAF_SUBMIT`, `TEMPLATE_UPDATE`, `TEAMS_POST`, `REPORT_ADVISORY`),
`correlationId` (`@{workflow().run.name}`), `requestedBy`, `subject` /
`reportType`, `targetSystem`, `draft`, `verifierVerdict` when an agent
produced the draft.

*Decision callback* (approval app → `callbackUrl`):

```json
{ "decision": "approved" | "rejected", "approver": "{approver-upn}",
  "comment": "optional", "correlationId": "<echoed>" }
```

`decision` is compared **case-insensitively** in every workflow
(`toLower(coalesce(decision,''))` = `approved`); anything else, including a
missing field or expiry, is a rejection. The approval app must verify the
approver against the policy groups and reject approver == requestedBy (see
`../team/approval-policy.json`).

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

## The workflows

### Report delivery (requirements a–f, g/h files, briefs)

`report-delivery-pipeline.json` is a **template**: deploy one instance per
entry of `pipelines.json` (12 instances: `deepsearch-report`,
`ai-deepsearch-report`, `dpia-dpo-report`, `cyber-forum-pptx`,
`cyber-forum-brief`, `ciso-exec-summary`, `ciso-global-pptx`,
`tpa-evidence-analysis`, `soc-report-summary`, `pentest-report-summary`,
`advisory-file-delivery`, `transcript-summary`). Every key of a
`pipelines.json` entry is a workflow parameter of the same meaning
(`agent`→`agentName` plus `agentVersion` from `build/agent-versions.json`,
`libraryRoot`→`libraryRootItemId`, `approvalKind`,
`shared.sensitivityLabel`→`sensitivityLabelId`, `supplierNameFallback`,
`serviceNameFallback`, `portfolioStatusOnStore`, `appendScoreHistory`). `scripts/build_logicapps.py` (see the deployment
note below) derives `build/logicapps/<name>/workflow.json` from the two
files.

Flow: HTTP trigger → **immediate `202 {runId, status: ACCEPTED}`** (an
approval can take days, so the outcome is never returned synchronously —
poll `report-status.json` or pass `callbackUrl`) → resolve
Supplier/Service segments (fallbacks only where the manifest allows:
`_ALL-SERVICES` for d2, `General/Threat-Intel` for non-vendor briefs;
otherwise the run terminates `MISSING_SUPPLIER_OR_SERVICE`) → uploaded
file ids mapped to `{file_id, tools:[file_search, code_interpreter]}` → run
the producing agent → output-verifier → human approval gate (`kind` =
`approvalKind`) → extract the ```` ```json ```` contract (or the
`<!DOCTYPE …</html>` document for html) → `/render` → `/ensure_folder`
(`Reports/<Supplier>/<Service>/`, reuse-if-exists) → `/upload` + org share
link → `/assign_label` (Purview sensitivity label on the delivered file via
Graph `driveItem:assignSensitivityLabel`, from the delivery Function — the
only SharePoint writer; skipped when `sensitivityLabelId` is empty, the
library default label then applies — finding C16) → optional `/portfolio_update` (TPA Status `Ongoing` after DeepSearch,
`Complete` after the CISO decks) and `/history_append` (score history for
the TPSRCA Trend Analyzer; `overallScore` is read from the HTML's
`data-overall-score` attribute and never inferred) → Teams notice →
optional callback `{runId, status, webUrl, shareUrl, fileName,
overallScore}`.

| File | Trigger | Purpose |
|---|---|---|
| `report-delivery-pipeline.json` | HTTP | Template above; the only path to `Reports/…` |
| `report-status.json` | HTTP GET-by-runId | Read-only status (`GENERATING_OR_VERIFYING` / `AWAITING_APPROVAL` / `STORED` / `DECIDED_NOT_STORED`) over the Logic Apps runtime management API — no storage, no writer |
| `template-update-approval.json` | HTTP (template-manager) | Requirement j: visual preview → approval (P7D) → `update_templates.py` job |

### Routine replacements

| File | Trigger | Steps | Integrations |
|---|---|---|---|
| `onetrust-assessment-intake.json` | Recurrence, daily | List OneTrust assessments completed since last run → for each: resolve Supplier (primary inventory) / Service (assessment name) → **HttpWebhook call of the `dpia-dpo-report` pipeline** with `callbackUrl` → record outcome | OneTrust API (read), delivery pipeline |
| `scheduled-deepsearch.json` | Recurrence, weekly | Read the supplier watchlist (SharePoint list: `SupplierName`, `SupplierDomain`, `ServiceName`, `Active`; Graph read) → for each active row: **HttpWebhook call of the `deepsearch-report` pipeline** → if `STORED` and `overallScore` < threshold: **approval gate** (`JIRA_CREATE`) → create a Jira ticket | Graph (read), delivery pipeline, Jira |
| `defender-incident-brief.json` | HTTP (Defender/Sentinel automation rule) | **cyber-forum** brief → **output-verifier** → respond 200 (`brief_pending_approval` / `brief_failed_verification`) → **approval gate** → Jira issue | Defender/Sentinel, Foundry, Jira |
| `jira-finding-sync.json` | Recurrence, hourly | JQL search → deterministic pre-check (finding reference, allowed status) → **approval gate** (`IAF_SUBMIT`) → IAF submit → Jira comment on failure | Jira, IAF API |
| `morning-brief.json` | Recurrence, weekdays 07:00 (one instance per user) | Graph calendar/mail/chats (read) → `morning-brief` agent (language and sections written into the schedule; `includeActionButtons` hard-coded **false** — claude.ai deep links would send Euronext context to the web) → HTML to the user's OneDrive via the delivery Function (7-day retention) → Teams DM | Graph (read), Foundry, delivery Function |
| `mailbox-intake.json` | Recurrence, 15 min | Shared mailbox unread+attachments → file under `TPA/Inbox/<Supplier>/<Service>/` via the delivery Function → `tpa-evidence-analyzer` triage → mark read → Teams summary; **never replies** | Graph (one mailbox), Foundry, delivery Function |
| `watch-until.json` | Recurrence, N min (one instance per watch) | Read-only GET of a Jira/OneTrust/IAF item until a field equals the expected value → run an agent once → Teams → disable itself (replaces `/loop`, "monitor until") | Jira/OneTrust/IAF (read), ARM (self-disable) |
| `scheduled-evaluation-redteam.json` | Recurrence, weekly (Mon 06:00 UTC) | Golden-set **evaluation** of every pinned `<agent>:<version>` (E2 evaluator set) → **AI Red Teaming Agent** scan (preview; agentic categories) → Teams notice to the accountable owner with scores, report links and the accuracy floor. Read-only: it never promotes a candidate, changes an agent or writes anywhere (finding C18; `../enterprise/series/08-guardrails-observability-evaluation.md` §4 E2/E5) | Foundry evaluations + red-team (preview), Teams |

### Event / session patterns (Claude Code Remote & connector features)

| File | Trigger | Steps |
|---|---|---|
| `scheduled-followup.json` | HTTP `{conversationId, agentRef, fireAt, prompt, requestedBy}` | `202` → `Delay until fireAt` → one Responses call that carries the prompt into the **existing** Foundry conversation and runs the pinned agent → Teams notice (replaces `send_later` / `run_once_at`; scheduling a run is not a submission of record — see `../governance/HUMAN_APPROVAL.md`). `threadId`/`agentId` are accepted for one release |
| `agent-fanout.json` | HTTP `{tasks[{agentRef,label,prompt}], synthesisPrompt}` | parallel (5) specialist responses, one conversation each → collect → orchestrator synthesis → response (replaces sibling sessions / Explore-Plan subagents; read-only tools only) |
| `generic-event-intake.json` | HTTP, HMAC-signed `{source, payload, conversationId?, agentRef?}` | validate signature → one Responses call posting the event as DATA into the conversation → `202 {responseId, conversationId}` (replaces `watch_url` / artifact-republish wakes) |
| `teams-post-approved.json` | HTTP `{teamId, channelId, format, brief, requestedBy}` | `internal-comms` draft (ENX formats) → output-verifier → `202` → **approval gate** (`TEAMS_POST`) → Graph channel message from the automation identity |
| `speech-transcription.json` | HTTP `{audioBlobUrl, supplierName, serviceName}` | Azure AI Speech batch transcription + diarization (EU) → transcript contract → `transcript-summary` pipeline (replaces `whisperx-transcribe-diarize`) |

### Logic Apps ↔ Foundry: what we use, and what we do not (finding C20)

| Feature | Decision |
|---|---|
| **Responses API from plain HTTP actions** (what these files do) | **Used** — GA, no premium connector, managed identity, and the approval gate stays a deterministic workflow action. |
| Logic Apps Standard **Agent action / agent loop** (preview) | **Evaluated, not deployed.** When it goes GA it may orchestrate **read** steps only: **no write connector (Jira create, SharePoint upload, IAF submit, Teams post, mail) is ever exposed as an agent tool** — writes stay deterministic actions after the `HttpWebhook` approval gate. "Workflow as tool" is piloted for the read-side `/render` and `/ensure_folder` helpers only. |
| Classic "Logic Apps as an agent tool" (Consumption, same resource group) | **Not used** — it retires with the classic agent service (2027-03-31) and the new service has no native Logic Apps tool. |
| Foundry portal *workflows* (visual designer) | **Not used** — retires 2026-12-01. |

### Not converted (decision of record)

| claude.ai / Claude Code feature | Decision |
|---|---|
| PR babysitting / PR-steward, DevOps PR-activity hooks | **Excluded** — no code-repository write workflow exists at ENX for the assurance persona; `watch-until` covers "watch a ticket/assessment until it changes". |
| Session orchestration `send_message` between live sessions, Remote Control | **Excluded** — connected agents (synchronous hand-offs) + `agent-fanout` cover the need; no live-session bus is deployed. |
| Push/e-mail completion notifications | Teams-only (`teamsWebhookUrl`); e-mail sending would require an approval-gated mail action (`MAIL_SEND`), not implemented by design. |
| `morning` action buttons (`claude.ai/new` deep links) | **Removed** — would send Euronext context to the web. |
| claude.ai docs / living documents | Delivered as DOCX/XLSX through `advisory-file-delivery` and co-edited in Word/Excel Online (decision recorded in `../governance/PLATFORM_SKILLS_DECISION.md`). |

### Deployment note

Instances are derived, not hand-edited: `scripts/build_logicapps.py`
reads `pipelines.json` + `report-delivery-pipeline.json`, substitutes agent
**names and promoted versions** (`build/agent-versions.json`, finding C19)
and drive/root ids from environment variables, and emits
`build/logicapps/<name>/workflow.json`
for the 12 pipeline instances plus every standalone file here;
`ci/deploy_logicapps.sh` zips that folder and runs `az logicapp deployment
source config-zip`. Secrets stay `@Microsoft.KeyVault(...)` app settings.

Notes: the Foundry response is asynchronous (`background: true`) — each
workflow polls `GET /openai/v1/responses/{id}` with an `Until` loop
(terminal-state expression) and then reads the response object, whose
`output_text` carries the answer (fallback: the last
`output[].content[].text`). Long DeepSearch runs are why that
workflow (and not M365 Copilot — see
`../integrations/copilot/README.md`) is the right channel for
report-generating agents. If the ENX Gateway MCP server
(`../integrations/mcp/enx-gateway.json`) is attached to an agent, the tool
calls happen inside the Foundry run; the workflows need no extra steps.

### Diagnostic settings (required for the operations alerts)

Enable the diagnostic setting with category **`WorkflowRuntime`** on
`{baseName}-la` to the platform Log Analytics workspace. The operations alerts
(`../operations/MONITORING.md` §4) read `LogicAppWorkflowRuntime` and key on
the action names `Human_approval_gate`, `Wait_for_approval_*` and
`Notify_verifier_fail` — **keep those names when editing definitions**, or the
verifier-fail-rate and approval-SLA alerts go silent.
