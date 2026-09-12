# Publishing the Advisors to Teams / Microsoft 365 Copilot for the Five Users

Two routes exist. The blueprint (CP-1) chooses the **native Foundry
publish** (GA) and keeps **Copilot Studio** as the fallback that
`../../integrations/copilot/README.md` Option 1 describes. Both are scoped
to `sg-infosec-foundry-users` (`{upn:francisco.gomes}`, `{upn:jose.mogollon}`,
`{upn:pedro.santos}`, `{upn:jose.meireles}`, `{upn:tania.morais}`) — never
tenant-wide. Agents published: `cyber-forum`, `dora`, `nis2`, `eu-ai-act`,
`iso27001`, `iso42001` (conversational; the file-producing pipelines stay
in Logic Apps). Human-approval Layers 1–2 apply unchanged: the published
agents hold read-only tools and the APPROVAL GATE block; Copilot adds no
write path (`../../governance/HUMAN_APPROVAL.md` scope notes).

## Route A — native publish (chosen)

Facts ([Publish to Teams and M365 Copilot](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/publish-copilot), GA, 2026-08-26):
Publish → *Teams and Microsoft 365 Copilot* compiles a Teams app manifest,
creates or reuses an **Azure Bot Service** resource (requires Azure Bot
Service Contributor), and registers the app; tenant scope needs Microsoft
365 admin approval; published agents currently lack streaming/citations and
file upload in M365 Copilot; a private-network project needs
`enable_m365_public_endpoint`. Publishing creates a **distinct Entra Agent
ID** for the agent — repeat the role assignments before traffic
([Agent identity](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/agent-identity), GA, 2026-08-25).
The SharePoint grounding tool does not work when published to Teams
([SharePoint tool limitations](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/sharepoint#limitations), preview, 2026-08-21).

| Step | Who | Action | Evidence |
|---|---|---|---|
| 1 | owner | Change record (Tier C) naming the agent, version, audience; AIMS scope note updated (second distribution channel) | PR / ticket |
| 2 | owner (Bicep) | `Microsoft.BotService/botServices` `{baseName}-bot`, EU data residency, Entra-only, `enableCopilotPublish=true` (D-EB9) | deployment output |
| 3 | owner (PIM Foundry Owner + Azure Bot Service Contributor) | Build > Agents > *agent* > Publish → Teams and Microsoft 365 Copilot; pin the promoted version (`version_selector` fixed) | screenshot |
| 4 | `{group:iam-admins}` | Repeat data-plane read roles on the new agent identity (Storage Blob Data Reader on deliverables, Search Index Data Reader on kb indexes); Conditional Access policy on the blueprint | `ACCESS_REGISTER.md` rows |
| 5 | M365 admin `{group:m365-admins}` | Approve the app in the Microsoft 365 admin center **for the group only**: Teams app setup/permission policy or "Manage apps → Available to specific users/groups" = `sg-infosec-foundry-users` | admin center screenshot |
| 6 | owner | Smoke test from Teams as one user; confirm no file upload expectation; record limitations in `USER_QUICKSTART.md` | test note |
| 7 | owner | Register in `ACCESS_REGISTER.md` (app id, agent identity id placeholder, publish date) and in the quarterly review | register diff |

Private networking note: with `publicNetworkAccess: Disabled` the Bot
Service channel is a public endpoint by design; enabling the M365 public
endpoint is a documented residual risk (NET-2) accepted by the owner.

## Route B — Copilot Studio fallback

Use when the native publish is blocked by tenant policy, or when Copilot
Studio DLP/analytics are mandatory.

| Step | Setting |
|---|---|
| Environment | `{env:infosec-foundry}` (Power Platform), EU region; owner = Environment Maker; Power Platform admins = Environment Admin |
| Agent | one Copilot Studio agent "ENX Assurance" routing by topic to the six Foundry agents through an HTTP action against the **Agents v2** data plane (conversations + responses, api-version `v1`; exact path per the [Foundry project REST reference](https://learn.microsoft.com/en-us/azure/foundry/reference/foundry-project-rest-preview) — `{responses-endpoint}`) — not the retired thread/run sequence |
| Authentication | Entra ID (delegated/OBO) so the caller identity reaches Foundry; the connector app registration gets no standing role beyond Foundry User if OBO is unavailable |
| Sharing | *Share* → security group `sg-infosec-foundry-users` only; no "everyone in the org" |
| Channels | Teams + Microsoft 365 Copilot; M365 admin approves for the same group |
| DLP | Power Platform DLP policy allowing only the Foundry HTTP connector in that environment |
| Governance | community sources note that low-code makers spread agent creation outside central control — keep maker rights to the owner ([NHI Mgmt Group](https://nhimg.org/articles/copilot-studio-vs-foundry-in-financial-services-governance/), community, 2025-11-21) |

## What users should expect

| Topic | Behaviour |
|---|---|
| Identity | you are recognised by your Entra account; answers respect the platform's read-only tools |
| Files | no upload in Copilot — send documents through the pipelines (Teams workflow → Logic Apps) |
| Citations | may be absent in Copilot; use the Foundry playground or MCP for cited answers |
| Approval | any draft ticket/finding shown in Copilot is still "awaiting your approval" — submissions of record only through the approval-gated workflows |
| Stale answers | if behaviour lags a deployment, RUNBOOK FM-30: the owner re-promotes / republishes |

## Decommission

Unpublish in Foundry (or unshare in Copilot Studio) → remove the app from
the Teams catalog → disable the agent identity in Entra → `ACCESS_REGISTER.md`
change log. Offboarding a user is group removal only (`../../team/OFFBOARDING.md`).
