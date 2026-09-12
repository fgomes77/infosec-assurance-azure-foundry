# Surfacing the Foundry Agents in Microsoft 365 Copilot

The converted agents live in Azure AI Foundry and are invoked over the
Foundry Agents (data-plane) REST API. This page describes how to expose a
subset of them inside **Microsoft 365 Copilot** (and Teams), so users can ask
DORA/NIS2/ISO questions or the cyber-forum agent without leaving their chat.


> Role names follow the current Foundry RBAC naming (Foundry User / Foundry Owner /
> Foundry Account Owner / Foundry Project Manager); the underlying role definition
> GUIDs in `rbac.bicep` are unchanged — `enterprise/ENTERPRISE_BLUEPRINT.md` ID-1.

## Option 0 — Native publish from Foundry (recommended, GA)

**Decision 2026-09** (`../../enterprise/series/09-copilot-mcp-user-surfaces.md`):
conversational advisors are published with the native Foundry
**Publish → Teams and Microsoft 365 Copilot** flow. An Azure Bot Service
resource `{baseName}-bot` is created by `../../infra/main.bicep` when
`enableCopilotPublish = true`; tenant scope needs Microsoft 365 admin
approval; the audience is restricted to `sg-infosec-foundry-users` through a
Teams app policy.

**Limitations to accept before choosing it:** no streaming and no citations in
Microsoft 365 Copilot, no file upload there (use the pipelines), the SharePoint
grounding tool does **not** work when published to Teams, and a private-network
project needs the M365 public endpoint enabled.

**Identity:** publishing creates a **distinct Entra Agent ID** per published
agent — repeat its role assignments before traffic and record it in
`../../team/ACCESS_REGISTER.md` ("Entra Agent ID principals", finding C7).

Runbook: `../../enterprise/portal/copilot-studio-publishing.md`.
Source: https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/publish-copilot (GA, 2026-08-26).

Option 1 (Copilot Studio) and Option 2 (declarative agent) below remain
documented as the fallback for report requests and delegated (OBO) reads.

## Option 1 — Copilot Studio agent calling the Foundry endpoint (fallback)

1. In **Copilot Studio**, create a new agent (one per Foundry agent you want
   to surface, or one "ENX Assurance" agent that routes by topic).
2. Add a **custom connector** (or an HTTP action inside a topic/agent flow)
   that calls the Foundry Agents REST API on your project endpoint:
   `https://{foundry-account}.services.ai.azure.com/api/projects/{project}` —
   **Agents v2: create conversation → create response with `agent_reference`
   (`{type:'agent_reference', name, version}`) → read `output_text`**
   (`api-version=v1`). The thread/run sequence retired with the Assistants API
   on 2026-08-26 and the classic agents surface retires 2027-03-31.
3. Configure the connector's authentication as **Entra ID (OAuth)** against
   the Azure Cognitive Services audience, or use a Copilot Studio connection
   with a service-principal secret held in Azure Key Vault.
4. In the Copilot Studio agent, wire the user's utterance into the response
   `input` and return `output_text` as the agent reply; pass the returned
   `conversationId` back on follow-ups to keep context.
5. **Publish** the Copilot Studio agent to the **Microsoft 365 Copilot**
   channel (and optionally the Teams channel). After admin approval in the
   Microsoft 365 admin center, users invoke it from Copilot chat / Teams via
   `@{agent-name}`.

This path needs no extra hosting, gives you Copilot Studio's built-in
analytics and DLP integration, and is the fastest to govern centrally.

## Option 2 — Declarative agent + API plugin via Teams Toolkit (shipped here)

Deployable artefacts in this folder:

| File | Role |
|---|---|
| `openapi/ask.yaml` | API plugin spec: `POST /ask` (advisory Q&A), `POST /request_report` (starts a `workflows/pipelines.json` pipeline, returns `runId`), `GET /report_status/{runId}` |
| `appPackage/declarativeAgent.json`, `ai-plugin.json`, `manifest.json` | Teams Toolkit app package (placeholders in `{braces}`; add icons) — publish to `sg-infosec-foundry-users` only |
| `function/function_app.py` (+ `host.json`, `requirements.txt`) | Thin wrapper Function: Easy Auth (Entra) → group check → Foundry thread/run with **managed identity** → OBO for user-scoped Graph reads; input limits (8 000 chars), 110 s run budget (504 → use `request_report`), App Insights logging. Also implements the **approval gate UI** the workflows' `approvalWebhookUrl` points at: `POST /approval/subscribe` (stores the draft, posts the link to Teams), `GET /approval/{id}` (draft + Approve/Reject), `POST /approval/{id}/decide` (verifies approver against `team/approval-policy.json` groups via `checkMemberGroups`, rejects self-approval, records `{kind, correlationId, requestedBy, approver, decision, timestamp}`, then POSTs `{decision, approver}` to the workflow's `callbackUrl`). Deploy it as `{copilot-wrapper-function}` (or copy to `functions/ask/`). |

App settings (Key Vault references, no secrets in code): `PROJECT_ENDPOINT`,
`FOUNDRY_API_VERSION`, `ADVISORY_AGENT_IDS_JSON`, `PIPELINE_TRIGGER_URLS_JSON`,
`ENTRA_GROUP_USERS_OBJECT_ID`, `APPROVAL_POLICY_JSON`, `STATE_TABLE_ENDPOINT`,
`TEAMS_APPROVAL_WEBHOOK_URL`, `TENANT_ID`, `WRAPPER_CLIENT_ID`,
`WRAPPER_FEDERATED_ASSERTION`, `WRAPPER_BASE_URL`.

Original step list:

1. Deploy a **thin Azure Function** wrapper over the Foundry Agents API:
   one HTTP-triggered function per operation you want to expose, e.g.
   `POST /ask` (body: `{ "agent": "dora", "question": "..." }`) that
   internally performs the thread/message/run dance and returns the answer
   synchronously. The Function authenticates to Foundry with its
   **managed identity** (role: `Foundry User` on the project).
2. Describe the Function with an **OpenAPI 3.0 spec** (keep it small — one
   or two operations, good descriptions: Copilot picks operations from the
   descriptions).
3. Use **Teams Toolkit** ("Declarative agent" + "API plugin" templates) to
   build the app package: `declarativeAgent.json` (name, instructions,
   conversation starters), the API plugin manifest referencing your OpenAPI
   spec, and the Teams app `manifest.json`.
4. Sideload for testing, then publish through your org's Teams app catalog.

Choose this option when you need tighter control of the payload,
response-shaping, or want the wrapper to also enforce input limits/logging.

## Authentication

- **Entra app registrations:** one for the wrapper/connector (exposing an
  API scope), and — for Option 2 — the API plugin registered for OAuth
  against it (Teams Toolkit's `microsoftEntra` auth scheme).
- **On-behalf-of (delegated)** — preferred when responses must respect the
  *user's* permissions (e.g. the agent reads SharePoint content): Copilot
  passes the user token; the wrapper exchanges it (OBO flow) for a
  downstream token. More setup (consent, `api://` scopes) but a clean audit
  trail per user.
- **Decision for this platform:** the wrapper ALWAYS calls Foundry with its
  managed identity, and ALWAYS exchanges the caller's token (OBO) for the
  user-scoped Graph reads (`teams-graph`, `m365-personal-graph`, and the
  SharePoint-scoped advisors, whose answers must respect the user's site
  permissions). App-only is used for nothing user-scoped — the advisors
  carry SharePoint tools, so the earlier "app-only is simpler" option does
  not apply here.
- Secrets (if any client secret is unavoidable) live in **Azure Key Vault**;
  prefer managed identity / federated credentials everywhere else.

## Which agents belong in Copilot — and which don't

**Good fits (conversational, seconds-scale answers):**

- `cyber-forum` — security/GRC Q&A and regulatory interpretation
- `dora`, `nis2`, `eu-ai-act`, `iso27001`, `iso42001` — compliance advisors

- `infosec-assurance-advisor` — routing front door (default for `/ask`)

**Poor fits as synchronous chat, good fits as `request_report`:** every
delivery pipeline of `../../workflows/pipelines.json` — `deepsearch-report`,
`ai-deepsearch-report` (a), `dpia-dpo-report` (b), `cyber-forum-pptx` (c),
`ciso-global-pptx` (d), `tpa-evidence-analysis` (d2), `soc-report-summary`
(e), `pentest-report-summary` (f), `ciso-exec-summary`, `cyber-forum-brief`,
`advisory-file-delivery`, `transcript-summary`. They run for minutes and
emit HTML/DOCX/PPTX/XLSX; Copilot starts them through `POST /request_report`
(returns `runId`), the pipeline runs verifier → human approval → SharePoint
`Reports/<Supplier>/<Service>/`, and the requester gets the link in Teams.
`enx-tprm-control-center` is not surfaced: the declarative agent's own
instructions ARE the menu.

## Governance note (ISO 42001 / EU AI Act)

Surfacing these agents in M365 Copilot creates a **second AI distribution
channel** with its own user population and data paths. Before go-live:
record the Copilot channel in the **ISO 42001 AIMS scope** (and the
Statement of Applicability where it changes control applicability), and
update the **EU AI Act deployer assessment** — the deployment context,
transparency measures (users must know they are talking to an AI system),
and human-oversight arrangements differ from the Foundry-portal channel.
Log usage via Copilot Studio analytics / Azure Monitor and review both
channels together in the AIMS management review.
