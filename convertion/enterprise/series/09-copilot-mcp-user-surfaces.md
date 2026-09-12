# Step 09 — Copilot, MCP and the user surfaces

**Objective.** Give the five users the three ways in that the kit
defines — the Foundry portal playground, Microsoft 365 Copilot / Teams,
and the MCP server — using the native GA publish flow for the
conversational advisors (D11), the Logic Apps path for report requests,
the migrated MCP server (local stdio per user; optional hosted endpoint
behind Easy Auth), and the approved-client register.

**Owner / effort.** `{upn:francisco.gomes}` with `{group:m365-admins}`;
3 days. Countersign: M365 admins (app approval). **Depends on** 06, 08.

## 1. Platform facts

| Fact | Status / source |
|---|---|
| Publish to Teams / Microsoft 365 Copilot is a native GA flow (portal or REST): compiles a Teams app manifest, creates/uses an **Azure Bot Service** resource (Azure Bot Service Contributor role needed), enables the activity protocol; tenant scope needs M365 admin approval; published agents lack streaming, citations and file upload in M365 Copilot; private-network projects need `enable_m365_public_endpoint` | [GA] https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/publish-copilot (2026-08-26) |
| Publishing creates a distinct Entra agent identity; tool RBAC must be re-assigned to it | [GA] https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/agent-identity (2026-08-25) |
| Active version pinned per published agent (`version_selector`, not "always latest" in prod) | [GA] https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/publish-copilot#select-an-active-agent-version (2026-08-26) |
| Agent 365 *autopilot* agents (Frontier preview, own agent user account, per-instance licences) — out of scope for v1 | [preview] https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/agent-365 (2026-08-26) |
| MCP tool GA (server side, step 04); Foundry Toolkit for VS Code GA; Toolboxes preview | [GA/preview] https://devblogs.microsoft.com/foundry/whats-new-in-microsoft-foundry-build-2026/ (2026-06) |
| Community view: agent creation outside central control creates identity risk — keep publication owner-only | [community-claim] https://nhimg.org/articles/copilot-studio-vs-foundry-in-financial-services-governance/ (2025-11-21) |

## 2. Surfaces

| Surface | Agents | Identity | Mechanism | Governance |
|---|---|---|---|---|
| Foundry portal playground | all | user's own Entra id (Foundry User) | *Build → Agents → Try* | default surface; threads/conversations team-visible (`team/least-privilege/THREADS_MEMORY.md`) |
| Microsoft 365 Copilot / Teams (**native publish**, replaces `integrations/copilot/README.md` Option 1) | `infosec-assurance-advisor`, `cyber-forum`, `dora`, `nis2`, `eu-ai-act`, `iso27001`, `iso42001` (conversational, seconds-scale) — **never** the report pipelines | the published agent's Entra agent identity (Graph app roles re-granted per step 04 §3); users authenticated by Teams | Foundry portal → agent → **Publish** → *Teams and Microsoft 365 Copilot* → M365 admin approval in the Teams admin center, where an app policy limits the audience to `sg-infosec-foundry-users` (not org-wide) | transparency line in the agent description (already in `integrations/copilot/appPackage/declarativeAgent.json` instructions); ISO 42001 scope + EU AI Act deployer assessment updated (step 08 §5) |
| Report requests from Teams | pipelines a–f, g/h files | Logic Apps HTTP trigger (`requestReport`/`getReportStatus` of `integrations/copilot/openapi/ask.yaml`) via a Power Automate button or the declarative-agent package (Option 2) — optional in v1 | Logic Apps MI; `requestedBy` from the caller's token | approval gates unchanged (step 07) |
| MCP server, local stdio (default) | orchestrator + `ask_agent` + memory tools | each user's `az login` | `mcp-server/server.py` migrated to conversations (step 06 §A3); client registration in `mcp-server/README.md` | only clients on the **approved register** (`team/ACCESS_REGISTER.md` "Approved AI / MCP clients") — a client's model provider receives agent answers |
| MCP server, hosted (optional) | same | Container App MI (Foundry User) + Easy Auth allowed group `sg-infosec-foundry-users` | `infra/mcp-server.bicep` (`enableMcpHosting=true`, `mcpEasyAuthClientId` app registration) | registered in the ENX gateway if required; `mcp-server/README.md` security notes |

## 3. Click-path

**Foundry portal.** *Build* → *Agents* → `dora` → *Versions* → pin the
deploy-log version as active → **Publish** → *Teams and Microsoft 365
Copilot* → name `ENX InfoSec Assurance — DORA`, description (transparency
sentence), icon →
creates/uses Azure Bot Service `{baseName}-bot` (the owner needs *Azure Bot
Service Contributor* on the RG during the PIM window) → *Submit for admin
approval*. Repeat per advisor (or publish only the
`infosec-assurance-advisor` and let its `ROUTE:` answers name the
specialist). For private-network `prod`, set `enable_m365_public_endpoint`
on the project as the doc instructs and record it as an accepted
exception (inbound from the M365 activity protocol only).
**Teams admin center.** Manage apps → pending → approve → *app permission
policy* / *setup policy* limited to `sg-infosec-foundry-users` — the
audience restriction lives here, not in the Foundry publish dialog (which
submits tenant-wide for admin approval). **Entra admin center.** Enterprise
applications → the new agent identity → owner = `{upn:francisco.gomes}`;
re-run step 04 §3 app-role assignments for it (only the roles the agent's
tools need). **Azure portal (hosted MCP).** Container App `{baseName}-mcp`
→ Authentication → Microsoft provider, allowed group → Ingress internal.

## 4. CLI / kit scripts

```bash
# local MCP per user (mcp-server/README.md)
cd convertion/mcp-server && pip install -r requirements.txt && az login && export PROJECT_ENDPOINT="https://{account}.services.ai.azure.com/api/projects/{project}" && python3 server.py
# hosted MCP image (only if enableMcpHosting=true)
az acr build -r {registry} -t infosec-mcp:{tag} -f convertion/mcp-server/Dockerfile convertion
az deployment group create -g {rg} --template-file convertion/infra/main.bicep --parameters convertion/infra/main.parameters.prod.json mcpImage={registry}.azurecr.io/infosec-mcp:{tag} mcpEasyAuthClientId={app-registration-client-id}
# publication evidence
az bot show -g {rg} -n {baseName}-bot --query "{name:name,msaAppId:properties.msaAppId}"
```

The build context is `convertion/`, not `mcp-server/`: the server shares the
Foundry runtime adapter and the memory backend with the deploy scripts
(`scripts/_foundry_runtime.py`, `scripts/memory_store.py`, finding C1).
Transport is selected by the app setting `MCP_TRANSPORT=streamable-http`
(set in `infra/mcp-server.bicep`); no code edit is needed.

Shared delta for `integrations/copilot/README.md` (docs-only, S-09 family):
add at the top — `Decision 2026-09: conversational advisors are published
with the native Foundry "Publish → Teams and Microsoft 365 Copilot" flow
(GA); Option 1 (Copilot Studio) and Option 2 (declarative agent) remain
documented for report requests and delegated (OBO) reads.`

## 5. Values captured into `setup/.env`

| Variable | Value |
|---|---|
| `MCP_EASYAUTH_CLIENT_ID` | `{app-registration-client-id}` (hosted MCP only; not a secret) |
| `COPILOT_PUBLISHED_AGENTS` | comma list of the published agent names (documentation; read by `operations/RUNBOOK.md` FM-30) |

## 6. Verification

| # | Check | Pass when |
|---|---|---|
| V1 | A user in the group opens Teams → `@ENX InfoSec Assurance — DORA` → asks an Art. 30 question | answer within 60 s; transparency sentence shown once; a user **outside** the group cannot find the app |
| V2 | Ask the published agent to "create a Jira ticket for this finding" | the agent drafts and states it awaits approval / cannot write (Layers 1–2 hold in the Copilot channel) |
| V3 | Published agent identity in Entra: app roles = the agent's tools only; owner set | listing filed |
| V4 | Active version pinned (portal *Versions*) | not "always latest" |
| V5 | Local MCP: `ask_orchestrator` returns a `conversation_id`; `save_memory` writes a `MEMORY-` note visible in `memory_store.py list`; `search_memory` finds it | as expected |
| V6 | Hosted MCP (if enabled): unauthenticated request → 401; group member → 200; non-member → 403 | as expected |
| V7 | Approved-client register updated; each user's client listed | rows in `team/ACCESS_REGISTER.md` |
| V8 | Purview DLP prompt-blocking policy scoped to the published agent app (if enabled) blocks a prompt containing a test credit-card number | blocked |

**Rollback.** Foundry portal → agent → *Publish* → unpublish (Teams app
removed at the next policy sync); delete the Bot Service; hosted MCP:
`enableMcpHosting=false`. **ISMS evidence.** publication approval record,
V1–V8 outputs — EU AI Act Art. 50 (transparency), Art. 26; ISO 42001 A.8.2
(system documentation for users), A.9.4; ISO 27001:2022 A.5.19–A.5.20
(approved clients), A.8.5.

## Sources
- [GA] Publish to Teams / M365 Copilot — https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/publish-copilot (2026-08-26)
- [GA] Agent identity — https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/agent-identity (2026-08-25)
- [preview] Agent 365 autopilot — https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/agent-365 (2026-08-26)
- [GA/preview] Build 2026 recap (Toolboxes, Toolkit) — https://devblogs.microsoft.com/foundry/whats-new-in-microsoft-foundry-build-2026/ (2026-06)
- [community-claim] Copilot Studio vs Foundry governance — https://nhimg.org/articles/copilot-studio-vs-foundry-in-financial-services-governance/ (2025-11-21)
- Kit: `integrations/copilot/README.md`, `integrations/copilot/appPackage/declarativeAgent.json`, `mcp-server/README.md`, `infra/mcp-server.bicep`
