# Step 00 — Prerequisites, decisions of record, request queue

**Objective.** Everything that must exist or be decided before any Azure
resource is created: subscriptions and tooling, the eight decisions of
record the research forces (index §5), the request queue for the parties
whose lead time dominates the plan (custodians, IAM, M365 admins), and the
evidence folder structure.

**Owner / effort.** Francisco Gustavo Gomes `{upn:francisco.gomes}`; 2 days. No countersign.

## 1. Prerequisites

| # | Item | Detail | Evidence |
|---|---|---|---|
| P1 | Azure subscription(s) in the ENX landing zone with **Microsoft Foundry** (`Microsoft.CognitiveServices`) allowed, EU regions allowed, quota tier ≥ 1 | Quota tiers replaced Default/Enterprise levels (seven tiers, auto-upgrade by usage/agreement) — [GA] https://learn.microsoft.com/en-us/azure/foundry/openai/quotas-limits (2026-08-20) | `az account show`; quota tier page screenshot |
| P2 | Three resource groups (dev, test, prod) or at least dev + prod (`operations/LIFECYCLE.md` §7) | naming in index §2 | RG ids in the sign-off |
| P3 | Tooling on the owner's workstation / CI runner: `az` CLI (current), Bicep CLI **0.47.16** (pinned by `infra/validate.sh`), Python **3.10+** (`azure-ai-projects` 2.x requires 3.10+), `jq`, Node 20 (renderers), `func` core tools, PnP PowerShell (SharePoint) | [GA] https://learn.microsoft.com/en-us/azure/foundry/how-to/develop/sdk-overview (2026-08-26) | `infra/validate.sh` runs clean offline |
| P4 | The claude.ai export present at `../claude-account-export/` (input of `scripts/convert_skills.py`) and `scripts/verify_conversion.py` passing on the current commit | fidelity gate of `REQUIREMENTS.md` | `python3 scripts/convert_skills.py && python3 scripts/verify_conversion.py` exit 0 |
| P5 | GitHub (or Azure DevOps) repository with branch protection, CODEOWNERS = deputy for owner PRs, `production` environment approval (`operations/CHANGE_MANAGEMENT.md` §2) and two OIDC federated identities — `{app:infosec-foundry-deployer}` (deploy, bound to the `production` environment) and `{app:infosec-foundry-readonly}` (nightly drift and access review: `Reader` + `Azure AI User` + Graph `Directory.Read.All`, bound to the `main` branch, read-only by design; `team/least-privilege/IDENTITY_RBAC.md` §2a). Set `vars.AZURE_READONLY_CLIENT_ID` — until it is set, the nightly job falls back to the deploy identity | no client secrets | repo settings screenshot; both federated-credential subjects |
| P6 | Entra ID: the owner can request groups through `{group:iam-admins}`; PIM for Groups licensed (Entra ID P2 / Governance) | `team/least-privilege/IDENTITY_RBAC.md` §1 | IAM ticket id |
| P7 | Microsoft 365: InfoSec Assurance SharePoint site exists (prod) and a test site is created; the five users hold Microsoft 365 licences (M365 Copilot licence only needed if the SharePoint *tool* is ever used — it is not in v1) | `sharepoint/README.md` | site URLs (placeholders in docs) |
| P8 | Evidence folders on the prod site: `Governance/Implementation/{dev,test,prod}/NN/`, `Governance/ComparisonSet/inputs/`, `Governance/Releases/` | index §4 | folder listing |

## 2. Decisions of record (fill the table, file it as `Governance/Implementation/decisions.md`)

| Id | Decision | Options | Recommended | Decided by |
|---|---|---|---|---|
| D1 | Agent runtime | classic (retires 2027-03-31) / **new Responses-API service** | new service; scripts migrated in step 06 §A before any agent is created | owner |
| D2 | Multi-agent routing without connected agents | Logic Apps `agent-fanout.json` + explicit agent choice / A2A tool (preview) / Agent Framework hosted agent (GA) | v1: Logic Apps + explicit choice; A2A pilot in `test`; Agent Framework hosted orchestrator as the Q1-2027 candidate | owner |
| D3 | Reasoning-tier model | one of the EU-Data-Zone models marked supported for OpenAPI + MCP + Web Search | **decided: `o4-mini`** (alternate `gpt-5-mini`, then `gpt-4.1`); re-read the tool-support table in step 02 §C on the day and record the row in the sign-off; `o3-mini` is excluded (finding C4) | owner |
| D4 | Model version policy | auto-upgrade / **`NoAutoUpgrade` + explicit versions** | pinned; replacement project scheduled 90 days before 2027-04-14 | owner |
| D5 | Advisor stores | single merged vector store / AI Search index (Foundry IQ) | single store `vs-assurance-advisor` in v1 (memory notes prefixed `MEMORY-`), Foundry IQ evaluated in `test` (`enterprise/memory-learning/`) | owner |
| D6 | Agent setup | basic (Microsoft-managed storage) / **standard (BYO Cosmos DB + Storage + AI Search)** | basic in `dev`; standard in `test`/`prod` — residency evidence and export/delete control for DORA Art. 28 / GDPR; note the extra cost (Cosmos DB ≥ 3000 RU/s, AI Search) | owner + landing zone |
| D7 | Agent egress | public / **BYO VNet subnet** / managed VNet | BYO subnet in `test`/`prod` (hub firewall + DNS supplied by the landing zone); managed VNet only if the landing zone cannot provide a /24 | owner + landing zone |
| D8 | Web search | keep Bing grounding (risk accepted) / disable | keep, sanitised queries, alert; Bing Custom Search domain allow-list piloted | owner (risk owner) + DPO informed |
| D9 | Copilot surface | native Foundry publish to Teams/M365 Copilot (GA) / Copilot Studio wrapper / declarative agent package | native publish for the advisors; Logic Apps for reports | owner + M365 admins |
| D10 | Anthropic models on Foundry | not for v1 | the retirement schedule lists Claude models as GA on Foundry, but a community source (InfoQ, 2026-07-05) reports no European data zone for them — [community-claim] https://www.infoq.com/news/2026/07/claude-foundry-ga-europe/ ; without EU residency they fail the `DataZoneStandard` rule. **Record of decision, the `anthropicModelFormat` parameters and the tier-switch procedure: `../../governance/CLAUDE_ON_FOUNDRY.md`** — that file carries the quarterly re-check step, so the reviewer has one place to update rather than three | owner |

## 3. Request queue — start now, they gate later steps

| Request to | For step | What | Lead time |
|---|---|---|---|
| `{group:azure-platform}` | 01 | three RGs, VNet address space (a /22 as `infra/network.bicep` defaults to `10.60.0.0/22`, plus a /24 for the agents subnet), hub firewall rules, private DNS zone delegation, Azure Policy exemptions if the hub policy blocks `Microsoft.CognitiveServices` or `Microsoft.Bing` | 2–3 weeks |
| `{group:iam-admins}` | 03 | the six/seven `sg-infosec-foundry-*` groups (`team/least-privilege/entra/groups.json`), PIM policies, Conditional Access policy, app registration(s) for MCP Easy Auth and the Copilot wrapper | 2 weeks |
| `{group:jira-admins}`, Confluence admin, `{group:onetrust-admins}`, SecurityScorecard admin, `{upn:iaf-owner}`, `{group:enx-gateway}`, Azure DevOps admin | 04 | read-only service accounts / tokens named as in `team/ACCESS_REGISTER.md` ("Non-human identities"), scope confirmation in writing | 1–4 weeks |
| `{group:m365-admins}` | 04, 05, 09 | admin consent for the Graph application permissions (step 04 §3), `Sites.Selected` grants (step 05), Teams app approval (step 09) | 1–2 weeks |
| `{group:dpo}` | 04, 08 | RoPA entry `{ropa:infosec-foundry}` update (conversations, memory store, Bing egress, continuous evaluation sampling) | 2 weeks |
| `{upn:line-manager}` | 03, 10 | group ownership of the privileged groups, gate countersigns | — |

## 4. Portal orientation (Foundry portal, for everyone executing later steps)

The current Foundry portal is GA for Foundry projects and is organised in
top-level sections — **Home**, **Discover** (model catalog, benchmarks),
**Build** (Agents, Models, Services, Evaluations, Tracing), **Operate**
(Control Plane: assets, policies, guardrails, Defender/Purview) — each with
its own left pane; the classic portal remains for hub-based projects —
[GA] https://learn.microsoft.com/en-us/azure/foundry/how-to/navigate-from-classic
(2026-09-11); feature readiness (agents GA, tracing GA for prompt/hosted
agents, evaluations GA with some evaluators preview) —
[GA] https://learn.microsoft.com/en-us/azure/foundry/concepts/general-availability
(2026-09-09). The steps write click-paths as *Foundry portal → section →
left-pane item*.

## 5. Values captured into `setup/.env`

| Variable | Source | Note |
|---|---|---|
| `AZURE_SUBSCRIPTION_ID`, `AZURE_LOCATION` (`swedencentral`), `AZURE_RESOURCE_GROUP` | P1/P2 | already in `setup/.env.example` |
| `FOUNDRY_API_VERSION=v1` | D1 | **new** (shared delta S-04); replaces the `2025-05-01` default used by `workflows/*.json` |
| `AGENT_SETUP=basic|standard` | D6 | new (S-04); read by step 02 |

## 6. Verification

| # | Check | Pass when |
|---|---|---|
| V1 | `infra/validate.sh` (offline) | `build + lint OK`, `policy OK` |
| V2 | `python3 scripts/convert_skills.py && python3 scripts/verify_conversion.py` | exit 0 |
| V3 | `decisions.md` filed with D1–D10 decided | all rows have a decider and date |
| V4 | Request queue tickets opened | ticket ids in the sign-off |
| V5 | `deploy.sh --dry-run` on the current commit | completes (it will still target the classic SDK until step 06 §A — the check proves the build, not the runtime) |

**Rollback.** None (no Azure state). **ISMS evidence.** `decisions.md`,
ticket ids, `validate.sh` output — ISO 27001:2022 A.5.8 (project security),
A.8.32 (change management); ISO 42001 A.6.2.2 (AI system requirements);
DORA Art. 8 (identification).

## Sources
- [GA] Portal structure — https://learn.microsoft.com/en-us/azure/foundry/how-to/navigate-from-classic (2026-09-11)
- [GA] GA scope and readiness — https://learn.microsoft.com/en-us/azure/foundry/concepts/general-availability (2026-09-09)
- [GA] SDK versions, Python 3.10+ — https://learn.microsoft.com/en-us/azure/foundry/how-to/develop/sdk-overview (2026-08-26); https://pypi.org/project/azure-ai-projects/ (2.6.0, 2026-09-04)
- [GA] Quota tiers — https://learn.microsoft.com/en-us/azure/foundry/openai/quotas-limits (2026-08-20)
- [GA] Runtime retirement — https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/migrate (2026-08-05)
- [community-claim] Claude models / EU data zone — https://www.infoq.com/news/2026/07/claude-foundry-ga-europe/ (2026-07-05)
