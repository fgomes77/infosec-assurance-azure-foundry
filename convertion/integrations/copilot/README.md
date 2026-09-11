# Surfacing the Foundry Agents in Microsoft 365 Copilot

The converted agents live in Azure AI Foundry and are invoked over the
Foundry Agents (data-plane) REST API. This page describes how to expose a
subset of them inside **Microsoft 365 Copilot** (and Teams), so users can ask
DORA/NIS2/ISO questions or the cyber-forum agent without leaving their chat.

## Option 1 — Copilot Studio agent calling the Foundry endpoint (recommended)

1. In **Copilot Studio**, create a new agent (one per Foundry agent you want
   to surface, or one "ENX Assurance" agent that routes by topic).
2. Add a **custom connector** (or an HTTP action inside a topic/agent flow)
   that calls the Foundry Agents REST API on your project endpoint:
   `https://{foundry-account}.services.ai.azure.com/api/projects/{project}` —
   create thread → add user message → create run (with the target
   `agent_id`) → poll run status → read the assistant message.
3. Configure the connector's authentication as **Entra ID (OAuth)** against
   the Azure Cognitive Services audience, or use a Copilot Studio connection
   with a service-principal secret held in Azure Key Vault.
4. In the Copilot Studio agent, wire the user's utterance into the thread
   message and return the run's final message text as the agent reply.
5. **Publish** the Copilot Studio agent to the **Microsoft 365 Copilot**
   channel (and optionally the Teams channel). After admin approval in the
   Microsoft 365 admin center, users invoke it from Copilot chat / Teams via
   `@{agent-name}`.

This path needs no extra hosting, gives you Copilot Studio's built-in
analytics and DLP integration, and is the fastest to govern centrally.

## Option 2 — Declarative agent + API plugin via Teams Toolkit

For teams that prefer a code-first package:

1. Deploy a **thin Azure Function** wrapper over the Foundry Agents API:
   one HTTP-triggered function per operation you want to expose, e.g.
   `POST /ask` (body: `{ "agent": "dora", "question": "..." }`) that
   internally performs the thread/message/run dance and returns the answer
   synchronously. The Function authenticates to Foundry with its
   **managed identity** (role: `Azure AI User` on the project).
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
- **Application permissions (app-only)** — simpler when the agents only
  reason over their own vector-store knowledge (the DORA/NIS2/ISO advisors):
  the wrapper's managed identity calls Foundry; every user gets the same
  capability. Do NOT use app-only if the agent can reach user-scoped data.
- Secrets (if any client secret is unavoidable) live in **Azure Key Vault**;
  prefer managed identity / federated credentials everywhere else.

## Which agents belong in Copilot — and which don't

**Good fits (conversational, seconds-scale answers):**

- `cyber-forum` — security/GRC Q&A and regulatory interpretation
- `dora`, `nis2`, `eu-ai-act`, `iso27001`, `iso42001` — compliance advisors

**Poor fits (long-running, file-producing pipelines):** `ciso-reporting`,
`deepsearch-protocol` / `ai-deepsearch-osint`, `dpia`,
`tprm-slide-generator` / `pptx-executive-summary-ciso`. These run for
minutes and emit HTML/DOCX/PPTX artifacts — Copilot plugin calls will time
out and chat is the wrong delivery vehicle. Route these through the
**workflow layer** instead (see `../../workflows/README.md`): trigger via a
Teams workflow / Logic Apps HTTP endpoint, run asynchronously, then email
the artifact or drop it in SharePoint and post the link back to Teams.

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
