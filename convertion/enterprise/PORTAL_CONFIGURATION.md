# Portal Configuration — What Is Set in the Foundry Portal, What Is Set in Code, and How Drift Is Caught

Companion to `ENTERPRISE_BLUEPRINT.md`. The rule of the kit is "no hand
edits in the portal" (`../operations/CHANGE_MANAGEMENT.md`): the portal is a
**read, test and approve** surface for the five users and a **bootstrap /
break-glass** surface for the owner. This page fixes, per object, which
side is authoritative, the naming that lets a reviewer spot a stray
object, and the procedure that detects portal changes not made by
`deploy.sh` / Bicep.

Portal facts as of 2026-09-12: the new Microsoft Foundry portal is GA for
Foundry projects and is organised in six top-level sections, each with its
own left pane — among them Home (project overview), Discover (model
catalog, benchmarks), **Build** (Agents, Models, Services…) and
**Operate** (Compliance, Evaluations, Tracing…) — per
[Navigate from classic](https://learn.microsoft.com/en-us/azure/foundry/how-to/navigate-from-classic)
(GA, 2026-09-11) and [GA scope](https://learn.microsoft.com/en-us/azure/foundry/concepts/general-availability)
(2026-09-09; Operate/Control Plane experiences partly preview). Agents,
evaluations, datasets and workflows require Entra ID authentication (same
page); the platform already runs Entra-only (`disableLocalAuth: true`).

## 1. Portal map for this platform

| Portal section (new portal) | What the team sees there | Who uses it |
|---|---|---|
| Home | project overview, endpoint, recent agents | all |
| Discover > Model catalog | model cards, region/Data Zone availability, retirement dates | owner (MDL-2 quarterly check) |
| Build > Agents | the 40 prompt agents, versions, playground, Publish | users (run/test), owner (approve version) |
| Build > Models | the three deployments, capacity, guardrail assignment | owner (read; changes via Bicep) |
| Build > Services / Connections (Management center) | `conn-*`, `bing-grounding`, `app-insights` | owner (bootstrap + rotation), custodians (target side) |
| Operate > Tracing | per-run spans, tool calls, tokens (App Insights) | owner; `sg-infosec-foundry-readers` for audits |
| Operate > Evaluations | continuous evaluation results, human evaluation templates, red-teaming runs | owner + assurance lead |
| Operate > Compliance | guardrail policies, Defender/Purview enablement, compliance view | owner (read), platform team (policy) |

## 2. Authoritative side per object

| Object | Set in code (authoritative) | Allowed in the portal | Never in the portal |
|---|---|---|---|
| Foundry account, project, capability host, network injection, CMK | `../infra/main.bicep` (+ D-EB3/4/8), `landing-zone.bicep` | read | create/change (immutable settings — STO-1, NET-1) |
| Model deployments (name, version, SKU, capacity, `versionUpgradeOption`) | `main.bicep` | read; compare retirement dates | capacity or version changes (Tier C PR) |
| RAI / guardrail policies (deployment + agent level) | `main.bicep` raiPolicies; registry field `guardrail_policy` | read; **pilot** a category in annotate mode on dev only | prod change |
| Agents (instructions, tools, model, version) | `../deploy.sh` → `create_agents.py`, `attach_integrations.py`, `create_delivery_agents.py`, `create_orchestrator.py`, `apply_advisory_profile.py` | run, playground, read versions; **Promote a version** after the owner's review (approval act) | edit instructions/tools (drift alert fires) |
| Connections `conn-*` | Bicep for Bing/App Insights; `az rest`/portal **bootstrap** for `conn-*` (secrets from Key Vault by name) | create at bootstrap in a PIM window; rotate secret reference | changing target/scope without the custodian (Tier C) |
| Vector stores, files | scripts (per agent, `vs-<agent>`, `vs-assurance-memory`) | inspect | upload into an agent's store |
| Evaluations, human-evaluation templates | definitions checked into `../operations/evaluation/` | run, review, submit reviewer feedback | — |
| Copilot / Teams publish | runbook `portal/copilot-studio-publishing.md`; Bot Service via Bicep (D-EB9) | click Publish (owner) after the change record exists | tenant-wide scope |
| Policies, Defender, Purview | `azure-policy-assignments.bicep`; Control Plane toggles recorded in the change log | read compliance; enable Defender/Purview once (recorded) | exemptions without a ticket |

## 3. Naming

| Object | Pattern | Example |
|---|---|---|
| Azure resources | `{baseName}-<role>` (`main.bicep`) | `infosecfoundry-aif`, `-proj`, `-kv`, `-la`, `-delivery`, `-cosmos`, `-search`, `-bot` |
| Agents | skill name from the export, unchanged; delivery agents as listed in `../integrations/registry.json` | `dora`, `deepsearch-protocol`, `tpa-evidence-analyzer`, `infosec-assurance-orchestrator` |
| Agent versions | immutable; code references `<agent>:<version>`; the promoted version is recorded in `build/manifest.json` | `dora:7` |
| Connections | `conn-<system>` (project-scoped, `isSharedToAll: false`); platform-wide only `bing-grounding`, `app-insights` | `conn-jira-cloud`, `conn-onetrust` |
| Agent-identity connections | `conn-<system>-agentid` (category RemoteTool / RemoteA2A, auth AgenticIdentityToken) | `conn-enx-gateway-agentid`, `conn-a2a-dora` |
| Vector stores | `vs-<agent>`, `vs-assurance-combined`, `vs-assurance-memory` | — |
| Key Vault secrets | `kv-<system>-<purpose>` (names only in the repo) | `kv-jira-ro-token`, `kv-enx-gateway-token` |
| RAI policies | `infosec-<scope>` | `infosec-security-analysis`, `infosec-web-facing` |
| Evaluation runs | `eval-<agent>-<yyyymmdd>-<purpose>` | `eval-dpia-20260912-golden` |
| Published Copilot agents | display name `ENX <Agent>`; app id recorded in `ACCESS_REGISTER.md` | `ENX Cyber Forum` |

Anything in the project that does not match a pattern is a finding of the
quarterly access review (`../operations/access-governance/QUARTERLY_ACCESS_REVIEW.md`).

## 4. Drift detection

Existing detective control: `deploy.sh` records the SHA-256 of every
deployed agent's instructions and tool set in `build/manifest.json`; the
`agent-drift` alert (`../infra/monitoring.bicep`, `kql/agent-drift.kql`)
fires on any agent write by an identity other than the deploy service
principal. This page extends it to the objects the alert does not see.

| Object | Baseline | Live read | Compare | Cadence / trigger |
|---|---|---|---|---|
| Agents (instructions, tools, model, version) | `build/manifest.json` | `python3 scripts/create_agents.py --dry-run` + list live agents via SDK (`azure-ai-projects` 2.x) | hash mismatch → `agent_modified_by_non_deploy_identity`; fix = re-run `deploy.sh` (idempotent by name) | hourly alert; quarterly full compare (access review item 10) |
| Deployments | `main.parameters.prod.json` | `az cognitiveservices account deployment list -g {rg} -n {baseName}-aif -o json` | name/version/sku/capacity/raiPolicyName/versionUpgradeOption diff | weekly (RUNBOOK W-checks); after every retirement notice |
| RAI policies | `main.bicep` | `az rest --method GET --url ".../accounts/{baseName}-aif/raiPolicies?api-version={stable}"` | content filter list diff | monthly |
| Connections | `ACCESS_REGISTER.md` + `portal/connections-checklist.md` | `az rest --method GET --url ".../accounts/{baseName}-aif/projects/{baseName}-proj/connections?api-version={stable}"` | unexpected connection, `isSharedToAll: true`, changed target, auth type | monthly + `keyvault-human-secret-read` alert |
| Capability host / network injection / CMK | `main.bicep` outputs | `az rest` GET on the project and account JSON | any difference = incident (immutable settings) | after every deployment |
| Policy compliance | `azure-policy-assignments.bicep` outputs | `az policy state list -g {rg} --filter "complianceState eq 'NonCompliant'"` | non-compliant resources listed | daily summary; quarterly export as evidence |
| Published agents / Bot Service | change log | Teams admin center app list; `az bot show` | publication without a change record | monthly |
| Agent identities | `ACCESS_REGISTER.md` | project JSON `agentIdentityId`; Entra admin center > Agent ID | new blueprint/identity not in the register | quarterly access review |

Procedure when drift is found: (1) capture the live JSON into the ticket
(`{jira:INFOSEC-PLAT}-nnn`); (2) if it weakens an invariant (write tool,
Global SKU, public access, guardrail removed) treat as P1 and revert by
redeploying the authoritative template; (3) otherwise revert at the next
deploy window; (4) record in `../operations/CHANGE_MANAGEMENT.md` §7 and,
if a human made it, in the access review. No fix is applied in the portal
except the emergency **disable** of a connection or agent.
