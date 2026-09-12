# Update and Upgrade Review Policy — Binding Rule for Every Change to the Platform

**Rule.** Every update or upgrade of the InfoSec Assurance Foundry platform
— whatever its size, origin or urgency — is reviewed and approved by
**Francisco Gustavo Gomes** (`{upn:francisco.gomes}`, accountable owner
for creation, planning, maintenance, optimisation and updates) **before it
is implemented**. When the owner authors the change, the deputy
(`{upn:deputy-approver}`, `../team/TEAM_MODEL.md` §12.2) reviews it and
the owner still approves the production deployment. No agent, workflow,
scheduled job, optimizer, auto-upgrade setting or vendor default may
implement a change on its own. A change without this record is drift and
is reverted (`../enterprise/PORTAL_CONFIGURATION.md` §4).

This policy states *who decides and what evidence is needed per change
class*; the *how* (branch, PR, CI gates, environment approval, deploy SP)
is `../operations/CHANGE_MANAGEMENT.md`, the *objects and version ids* are
`../operations/LIFECYCLE.md`, the per-change form is `UPGRADE_CHECKLIST.md`,
the offline retirement check is `upgrade/check_model_lifecycle.py`, and
the pinned deployment shape is `upgrade/model-deployment-policy.bicep`.
Users of the platform: `{upn:francisco.gomes}`, `{upn:jose.mogollon}`,
`{upn:pedro.santos}`, `{upn:jose.meireles}`, `{upn:tania.morais}` — any of
them may propose; only the owner approves.

Control: ISO 27001:2022 A.8.32 (change management), A.8.9, A.8.19, A.8.29,
A.8.31, A.5.3; ISO 42001 A.6.2.4–A.6.2.5 (verification, validation,
deployment), A.6.2.7, cl. 8.1 (change control for the AIMS); DORA Art. 9(4)(e)
(ICT change management incl. emergency changes), Art. 10 (detection —
review must not weaken detection), Art. 8(2)–(3); EU AI Act Art. 9 (risk
management through the life cycle; deployer of a modified system), Art. 14,
Art. 26; NIS2 Art. 21(2)(e).

## 1. Scope — change classes and the evidence each one needs

Every row is approved by the owner before implementation (deputy review
when owner-authored). "Eval" = `operations/evaluation/run_evals.py` gate
G1 (control leg on the current version, candidate leg on the proposed one);
"comparison set" = `CHANGE_MANAGEMENT.md` §4; "dry-run" = the named
script's `--dry-run`; "security review" = invariants statement + read-only
proof + `access-review.sh --quick`; "cost" = `FINOPS.md` unit-cost delta.

| # | Class | Examples (kit objects) | Risk (`CHANGE_MANAGEMENT.md` §5) | Mandatory evidence before approval | Also required |
|---|---|---|---|---|---|
| C1 | **Model version / deployment** | `infra/main.bicep` `modelVersion`, `reasoningModelVersion`, `lightModelVersion`, `deploymentSku`, capacity; a fourth candidate deployment; model family change | Medium (version) / High (family, SKU) | eval baseline vs candidate (`--model-override`); comparison set on every affected pipeline; `check_model_lifecycle.py` output; tool-support row for the tier (`MODEL_ROUTING.md`, §3 R4); `infra/validate.sh` + `what-if`; cost delta | staged rollout one agent / 1 week; `versionUpgradeOption: 'NoAutoUpgrade'` stays; family change = platform **major** |
| C2 | **API / SDK / runtime versions** | `setup/requirements.txt`, `mcp-server/requirements.txt`, `functions/delivery/requirements.txt`; `FOUNDRY_API_VERSION`; Bicep api-versions; Python/Node base images; GitHub Actions pins | Medium | changelog / migration notes read and cited; every script `--dry-run`; `py_compile`; Function local run; `what-if` for api-version moves; security review (dependency CVEs) | never with a model change in the same release (`LIFECYCLE.md` §5); dev → test → prod |
| C3 | **Platform feature** (enable / disable / preview → GA) | Standard agent setup, network injection, CMK, Memory (preview), Foundry IQ, continuous evaluation, human eval, red-team schedule, A2A tool, Toolbox, Copilot/Teams publication, Logic Apps Agent action | Medium; High when it touches identity, network, write paths or data location | preview-feature register entry (§4) with exit criteria and compensating control; DPA/terms review for preview; security review; eval on affected agents; residency statement (EU Data Zone, data stored in region) | **no preview feature on the approval path** (§4); RoPA update when data flows change |
| C4 | **Instructions / persona / verifier rules** | `agents/*_instructions.md`, `agents/persona_system_prompt.md`, `advisory_addendum.md`, `verifier_instructions.md`, knowledge packs | Medium (High for verifier rules and the APPROVAL GATE block) | `verify_conversion.py` PASS; `create_agents.py` / `create_delivery_agents.py` / `create_orchestrator.py --dry-run`; eval G1; comparison set for report agents; W2/W3 checks on the built output | produces a **new immutable agent version**; Copilot republish |
| C5 | **Registry — tools, tiers, connections** | `integrations/registry.json` (`tools`, `model_tier`, `write_connections`), `openapi/*.yaml`, `mcp/enx-gateway.json` | Medium; High for any `write_connections` or new scope | `attach_integrations.py --dry-run` shows `[read-only]` on every tool; JSON/YAML parse; tool-support matrix check for the tier model; tier change = eval + comparison set; security review | advisory agents never leave `reasoning`; `write_connections` needs line manager + `HUMAN_APPROVAL.md` update |
| C6 | **Templates (requirement j)** | template sources, `templates/registry.json`, renderers | Medium | `template-update-approval` run (visual before/after, P7D); `update_templates.py --dry-run`; `verify_conversion.py`; renderer smoke via comparison set | version + `last_approved` bump; `templates/audit.log` |
| C7 | **Knowledge sources** | `agents/advisor-knowledge/*.md`, export knowledge files, Blob mirror for a knowledge base | Medium | `memory/knowledge-refresh.md` §3 intake form (provenance, IP, classification, injection scan); eval G1 on affected agents; advisor comparison set g/h/i | semi-annual re-sync = `LIFECYCLE.md` §3 |
| C8 | **Workflows / pipelines** | `workflows/*.json`, `pipelines.json`, `approval-policy.json`, `FOUNDRY_API_VERSION` | Medium; High if an approval step, expiry or `approvalKind` changes | JSON parse; `package_workflows.py`; one run to the verifier in test (never approved); approval expiry unchanged or justified; security review | `HUMAN_APPROVAL.md` Layer 3 table updated in the same PR |
| C9 | **Function code / images** | `functions/delivery/*`, `functions/office-tools/*`, MCP server, container tags | Medium | `py_compile`; `func` local run; `/render` smoke on each format via the comparison set (byte-compare deterministic renderers); image scan; security review (write path = SharePoint upload only) | image tag = release tag |
| C10 | **Infrastructure** | `infra/*.bicep`, `main.parameters*.json`, `enterprise/*.bicep`, `operations/*.bicep`, network, private endpoints, RAI policy, diagnostic settings | Medium; High for RAI policy, network egress, public access, CMK, capability host | `infra/validate.sh` (build + lint + EU policy check); `what-if` with the exact resource delta attached; security review; cost delta | immutable settings (capability host, network injection) = new project, planned as a **major** |
| C11 | **RBAC / groups / identities** | `team/rbac.bicep`, `least-privilege/entra/groups.json`, access packages, PIM, Conditional Access, agent identities / blueprints, Sites.Selected | High | `provision_identity.sh --plan`; `what-if`; `access_snapshot.sh` before/after; line-manager awareness for privileged groups; `ACCESS_REGISTER.md` row | quarterly access review picks up every change |
| C12 | **Connections / secrets** | Foundry `conn-*` targets, Key Vault secret versions, OAuth app registrations, MCP gateway allow-list | High for scope; secret rotation itself is not a PR | custodian confirms read-only scope; connection smoke test of the tool; `ACCESS_REGISTER.md` updated; `keyvault-human-secret-read` reconciled | secret values never in git; previous version kept until next rotation |
| C13 | **Documentation / runbooks only** | `operations/*.md`, `governance/*.md`, `team/*.md`, READMEs | Low | markdown renders; links resolve | still owner-approved (docs are the operating procedure of record — A.5.37) |

Anything not listed is treated as the closest higher-risk class until the
owner classifies it. A change that would **weaken an invariant** (read-only
agents, approval before any write, taxonomy, identities, EU residency,
no-egress) is not an update: it is a risk-acceptance request signed by the
CISO delegate before any PR (`CHANGE_MANAGEMENT.md` §5).

## 2. Environments and the path to production

| Stage | Where | What runs | Exit criterion |
|---|---|---|---|
| **dev** | `main.parameters.json` (`environmentName=dev`), `{baseName}-proj` dev; branch `change/{ticket}` | all `--dry-run` gates; `deploy.sh` to dev; eval G1 candidate leg; comparison set to the verifier only (nothing approved or stored) | every gate green; evidence pasted in the PR |
| **test** (staged) | prod project, **one** agent / one pipeline / one tier, or a fourth candidate deployment (`model-deployment-policy.bicep` `enableCandidateDeployment`) | 1 week of observation: `kql/latency-and-tokens.kql`, `kql/verifier-fail-rate.kql`, R1/R2/R3 checks; users informed in `{teams:infosec-assurance-platform}` | Q1 not below the previous week; no new verifier FAIL category; no alert |
| **prod** | `main.parameters.prod.json`; `production` GitHub environment | owner approves the deployment; deploy SP runs `deploy.sh`; post-checks RUNBOOK W1–W4 within 1 business day; new drift baseline `build/baseline-{date}.json` | ticket closed with evidence links; release tag `platform/v…` |

The three stages are mandatory for C1–C5, C7–C10; C6 uses the approval
workflow's visual review as its test stage; C11–C12 use `--plan` /
`what-if` as dev and the snapshot diff as test; C13 goes dev → prod.

## 3. Standing rules

| # | Rule | Why | Check |
|---|---|---|---|
| R1 | **No auto-upgrade anywhere**: every model deployment carries `versionUpgradeOption: 'NoAutoUpgrade'` and a non-empty explicit version; SDK/API pins are exact; portal "Always use latest" is not used for agents that pipelines call | a vendor default change is an unreviewed update | `check_model_lifecycle.py` (fails on empty version); `az cognitiveservices account deployment list` weekly (PORTAL_CONFIGURATION §4) |
| R2 | **Retirement watch**: the owner reads the model retirement schedule, the SDK changelog and the API lifecycle page at every quarterly platform currency review (§4) and at RUNBOOK M3; a change ticket is opened **≥ 120 days** before any retirement affecting a deployed model (Microsoft declares replacements 90–120 days before and notifies ≥ 60 days before GA retirements) | a retired version returns HTTP 410 — `NoAutoUpgrade` makes the review the compensating control | `check_model_lifecycle.py --horizon 180` in CI (warning) and monthly (blocking at 120 days) |
| R3 | **Migration method** for C1: Microsoft's six phases — Discover, Assess (freeze the golden set and success criteria first), Adapt, Validate (replay unchanged on the candidate to isolate model drift, then adapt prompts/params), Roll out (staged), Retire (delete the old deployment only after 7 days of zero requests) | attribution of regressions; evidence | eval reports control vs candidate attached |
| R4 | **Tool support rule**: a tier model must support every tool in that tier's toolset per the tool-support-by-region-and-model table on the day of the change (e.g. `o3-mini` does not support OpenAPI, MCP, Azure AI Search, SharePoint or Web Search; `gpt-4o-mini` lacks Azure AI Search) | silently non-functional enterprise integrations on advisory agents | table row pasted in the checklist; `attach_integrations.py --dry-run` and `verify_kit.py` against `integrations/registry.json` `model_tiers._tool_compatibility` (implemented 2026-09-12; both FAIL when a tier model cannot carry an agent's tools) |
| R5 | **Agent versioning**: every deploy creates a new immutable version; pipelines and the Copilot publication reference `name:version`; promotion = the owner sets the active version; rollback = switch back (no redeploy) | provable fidelity per deliverable; seconds to roll back | `build/manifest.json` records versions; alert when a run executes an unlisted version (shared delta) |
| R6 | **One kind of bump per release**: never a model change and an SDK change in the same release; never two SDK majors in flight | unambiguous regression attribution | release note |
| R7 | **Preview features** may be used only when registered (§4) with exit criteria and a compensating control, never on the approval path (verifier → human gate → delivery Function), never for data storage without a DPA/terms review | GA commitments and SLAs do not apply to preview | register reviewed quarterly |
| R8 | **EU residency**: `DataZoneStandard` (or `Standard` in an EU region) only; `GlobalStandard` refused; the Foundry resource, its VNet, Cosmos DB/Storage/AI Search of the Standard setup stay in the allowed EU regions; Bing/Web Search grounding remains the documented exception (`DATA_PROTECTION_GUARDRAILS.md` §1) | GDPR Art. 28, DORA Art. 28 evidence | `infra/validate.sh` policy check; `azure-policy-assignments.bicep` allowed locations |
| R9 | **Portal edits are not changes**: anything set in the portal outside the emergency *disable* is reverted by redeploying the authoritative template | one source of truth | `agent_modified_by_non_deploy_identity`; PORTAL_CONFIGURATION §4 |
| R10 | **Decision log**: every review produces one of adopt / defer / retire with a date and reason; deferred items carry a revisit date | auditability | `Governance/Releases/` and `Governance/Operations/{yyyy}-Qn/platform-currency.md` |

## 4. Quarterly platform currency review (owner + deputy, ~half a day)

| # | Item | Source read (status as of 2026-09-12) | Decision recorded |
|---|---|---|---|
| 1 | Model retirement schedule vs the three deployments (+ candidate) | https://learn.microsoft.com/en-us/azure/foundry/openai/concepts/model-retirement-schedule (2026-09-02, GA) — currently: `gpt-4o 2024-11-20` Legacy → retires 2027-04-14 (replacement `gpt-5.1`); `gpt-4o-mini 2024-07-18` Deprecated → 2027-04-14; `o3-mini` listed for retirement | `check_model_lifecycle.py` output attached; ticket if < 180 days |
| 2 | Model lifecycle policy (notice periods) | https://learn.microsoft.com/en-us/azure/foundry/openai/concepts/model-retirements (2026-07-24, GA) | — |
| 3 | EU Data Zone availability of candidate models and the tool-support matrix | https://learn.microsoft.com/en-us/azure/foundry/foundry-models/concepts/models-sold-directly-by-azure-region-availability (2026-09-04, GA); https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/limits-quotas-regions#tool-support-by-region-and-model (2026-09-07, GA) | candidate per tier named or "none" |
| 4 | SDK cadence and breaking changes (`azure-ai-projects` 2.x, releases every 4–6 weeks; 1.0.0 targets classic) | https://github.com/Azure/azure-sdk-for-python/blob/main/sdk/ai/azure-ai-projects/CHANGELOG.md (2026-09-04); https://learn.microsoft.com/en-us/azure/foundry/how-to/develop/sdk-overview (2026-08-26, GA) | pin bump ticket or defer |
| 5 | API lifecycle (v1 GA API needs no api-version; preview features opted-in per feature) | https://learn.microsoft.com/en-us/azure/foundry/openai/api-version-lifecycle (2026-06-05, GA) | `FOUNDRY_API_VERSION` decision |
| 6 | Portal / feature GA status and rollout pitfalls | https://learn.microsoft.com/en-us/azure/foundry/concepts/general-availability (2026-09-09); https://learn.microsoft.com/en-us/azure/foundry/whats-new-foundry (2026-09-01) | preview register updated |
| 7 | Retirements of platform components the kit still references: classic Agent Service (threads/runs) retires 2027-03-31; Assistants API retired 2026-08-26; portal workflows retire 2026-12-01; prompt flow 2027-04-20 | https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/migrate (2026-08-05, GA); https://devblogs.microsoft.com/agent-framework/microsoft-agent-framework-version-1-0/ (2026-04-03) | migration ticket state |
| 8 | Bicep api-versions for `Microsoft.CognitiveServices` (kit: `2025-04-01-preview`; stable `2025-06-01`, `2025-09-01`, `2025-12-01` exist) | https://learn.microsoft.com/en-us/azure/templates/microsoft.cognitiveservices/accounts/projects (2026-07-20) | move when `what-if` shows no diff (patch) |
| 9 | Identity and governance changes: Entra Agent ID, Foundry RBAC role names, Purview/Defender for AI | https://learn.microsoft.com/en-us/entra/agent-id/whats-new-agent-id (2026-08-13, GA); https://learn.microsoft.com/en-us/azure/foundry/concepts/rbac-foundry (2026-09-10, GA); https://learn.microsoft.com/en-us/purview/ai-azure-foundry (2026-05-01, GA) | `team/` deltas or none |
| 10 | Pricing changes (e.g. EU Data Zone uplift from 2026-09-01) vs `monthlyBudget` | https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/microsoft-foundry-model-deployment-pricing-update/4535385 (2026; date not readable — verify) | `FINOPS.md` unit costs refreshed |

**Preview-feature register** (kept in `Governance/Operations/platform-currency.md`;
one row per preview capability in use or piloted):

| Capability | Status 2026-09-12 | In use? | Compensating control while preview | Exit criterion |
|---|---|---|---|---|
| Memory (Foundry Agent Service) | Preview (https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/what-is-memory, 2026-06-02) | no | n/a — disabled | GA + VNet support + DPA review (`MEMORY_AND_LEARNING.md` §3) |
| Human evaluation templates | Preview (https://learn.microsoft.com/en-us/azure/foundry/observability/how-to/human-evaluation, 2026-07-31) | optional | feedback records also kept in `{list:PlatformFeedback}` (repo-side evidence) | GA or replacement |
| Agent Optimizer | Preview (https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/agent-optimizer-overview, 2026-08-19) | optional, input only | candidates are proposals; human Promote + `verify_conversion.py` | GA |
| AI Red Teaming Agent | Preview (https://learn.microsoft.com/en-us/azure/foundry/concepts/ai-red-teaming-agent, 2026-08-27) | optional, purple project | results exported to the repo; no production traffic | GA |
| A2A tool (replacement for connected agents) | Preview (https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/agent-to-agent, 2026-09-04) | evaluate for the orchestrator | orchestrator hand-offs stay reviewable; Agent Framework code path as alternative | GA before pipelines depend on it |
| SharePoint grounding tool / indexed SharePoint knowledge source | Preview (2026-08-21 / 2026-09-02) | no | read-only Graph tool | GA + licence decision |
| Logic Apps Standard "Agent" action | Preview (https://learn.microsoft.com/en-us/azure/logic-apps/automate-foundry-agents-with-workflows, 2026-08-13) | no | pipelines call agents through the Foundry REST/SDK path | GA |
| Foundry IQ (parts) | GA core / preview parts (2026-07-31) | planned (Blob mirror only) | file_search stores remain the fallback | preview parts unused |

## 5. Emergency changes and rollback

| Topic | Rule |
|---|---|
| Emergency | only during an open P1/P2; **prefer disable** (workflow, connection, tool, secret version, agent in the orchestrator) — disabling needs no approval; any other emergency change is applied by the owner under PIM with the ticket id, reviewed by the deputy within 2 h, and made equal to the repo by a retrospective PR within 1 business day (`CHANGE_MANAGEMENT.md` §8). An emergency change never widens a write path, never disables content filtering or the verifier, never approves a pending report |
| Rollback — agents | switch the active version back to the previous `name:version` (seconds); or check out the previous `platform/` tag and run `deploy.sh` |
| Rollback — models | the previous deployment is kept 7 days after a tier switch; `attach_integrations.py --only <agent>` re-points the tier; `NoAutoUpgrade` guarantees the old version is still what it was |
| Rollback — SDK/API | previous pins in git; runners and images rebuilt from the previous tag |
| Rollback — templates | `update_templates.py` backup + a new approval run |
| Rollback — infra / RBAC | `what-if` of the previous commit, redeploy; `access_snapshot.sh` before/after |
| Rollback — workflows | previous definition from git; Logic Apps run history survives versions |
| Rollback test | every C1 and C10 change states the rollback command in the checklist and the owner executes it once in dev before prod |

## 6. Records and evidence

| Record | Where | Retention |
|---|---|---|
| Filled `UPGRADE_CHECKLIST.md` (one per change) | PR description + `Governance/Changes/{ticket}.md` | ≥ 5 years (ISO 42001 documented information; DORA Art. 28 evidence ≥ 1 year minimum) |
| Eval reports control vs candidate; comparison-set diffs | `build/evals/{ticket}-*` attached to the PR; `Governance/Operations/` | with the change record |
| `check_model_lifecycle.py` output at each review | `Governance/Operations/{yyyy}-Qn/platform-currency.md` | 5 years |
| Preview-feature register and decision log | same file | until superseded + 5 years |
| Environment approval, Actions log, ARM deployment name, release tag | GitHub + Azure | repo history indefinitely |
| Emergency change: ticket, PIM record, retrospective PR, post-incident note | Jira + GitHub + `Governance/Incidents/` | ≥ 5 years |

Shared deltas produced by this policy (literal text, not applied here):

| Id | Target | Text |
|---|---|---|
| D-UP-1 | `infra/main.bicep` — each of `modelDeployment`, `reasoningDeployment`, `lightDeployment` `properties` | add `versionUpgradeOption: 'NoAutoUpgrade'`; change `reasoningModelVersion` and `lightModelVersion` defaults from `''` to explicit versions and add `@minLength(1)` on all three version params (or consume `enterprise/upgrade/model-deployment-policy.bicep` as a module) |
| D-UP-2 | `infra/validate.sh` policy block | append `for k in ('modelVersion','reasoningModelVersion','lightModelVersion'):` / `    if p.get(k, {}).get('value', 'x') == '': print(f"!! {k} is empty — explicit model versions are required (UPDATE_AND_UPGRADE_REVIEW_POLICY R1)"); bad = 1` and `if 'NoAutoUpgrade' not in tpl: print("!! main.bicep deployments lack versionUpgradeOption NoAutoUpgrade"); bad = 1` |
| D-UP-3 | `operations/CHANGE_MANAGEMENT.md` §9 Calendar | add row `\| Quarterly \| Platform currency review (enterprise/UPDATE_AND_UPGRADE_REVIEW_POLICY.md §4): retirement schedule, SDK changelog, API lifecycle, GA/preview page, preview-feature register; \`python3 enterprise/upgrade/check_model_lifecycle.py --dry-run\` \| owner + deputy \|` |
| D-UP-4 | `operations/RUNBOOK.md` M3 row | append "; run `python3 enterprise/upgrade/check_model_lifecycle.py --dry-run --horizon 180` and open a ticket for any deployment within 120 days of retirement" |
| D-UP-5 | `governance/MODEL_ROUTING.md` after the tier table | **Applied** — the tool-support rule and the per-model compatibility matrix are in `governance/MODEL_ROUTING.md` ("Tool compatibility (tier name ≠ tool support)"), the reasoning default is `o4-mini`, and the enforcement point is `scripts/attach_integrations.py` (`check_tool_compatibility`) plus `scripts/verify_kit.py` `check_crossrefs`. |
| D-UP-6 | `integrations/model_tool_matrix.json` (new) + `scripts/attach_integrations.py --dry-run` | static table `{ "<model>": { "openapi": bool, "mcp": bool, "azure_ai_search": bool, "sharepoint": bool, "web_search": bool, "file_search": bool, "code_interpreter": bool, "reviewed": "yyyy-mm-dd" } }`; the dry run fails when an agent's tools are unsupported by its tier model |
| D-UP-7 | `operations/CONTINUOUS_IMPROVEMENT.md` §1 row S13 | replace collector with "`enterprise/upgrade/check_model_lifecycle.py`; Azure Service Health notices to `{owner-mailbox}`; `LIFECYCLE.md` §5" |
| D-UP-8 | `.github/workflows/ci.yml` job `gates` | **Applied** — step `[7] Platform currency: pinned model versions, lifecycle, learning loop (C6/C25)`; the same step exists in `convertion/ci/azure-pipelines.yml`. `bicep build` of `enterprise/upgrade/model-deployment-policy.bicep` is covered by step `[4] Syntax gate`, which builds every `*.bicep` in the kit. The release job additionally runs `./deploy.sh --dry-run` with `STRICT_RUNTIME=1 LIFECYCLE_STRICT=1`, so a classic-runtime SDK or an open lifecycle finding fails the pipeline. |
| D-UP-9 | `infra/monitoring.bicep` / `infra/kql/agent-drift.kql` | **Applied** — the `agent_version_not_in_manifest` query is the second block of `infra/kql/agent-drift.kql` and compares `gen_ai.agent.version` from the run telemetry against **`build/agent-versions.json`** (the ledger `scripts/_foundry_runtime.py` writes), published to App Insights by `deploy.sh` as the custom event `deploy_manifest`. `build/manifest.json` holds no versions and is NOT the baseline. The release pipeline must publish and restore the ledger, or the comparison is skipped. |
| D-UP-10 | `governance/HUMAN_APPROVAL.md` Layer 3 table | add row `\| Promote agent version / switch tier model / bump SDK-API pins (enterprise/UPDATE_AND_UPGRADE_REVIEW_POLICY.md) \| owner approval in the production environment after deputy review when owner-authored; evidence = eval control vs candidate + checklist \| n/a (PR-based) \|` |

## 7. Sources (status as of 2026-09-12)

| Claim | Source | Date | Status |
|---|---|---|---|
| `versionUpgradeOption` values and pinning | https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/working-with-models | 2026-06-05 | GA |
| Lifecycle: 18-month GA lifecycle, Deprecated at 12 months, ≥ 60 days notice, replacement 90–120 days before | https://learn.microsoft.com/en-us/azure/foundry/openai/concepts/model-retirements | 2026-07-24 | GA |
| Retirement schedule (gpt-4o, gpt-4o-mini, o3-mini rows) | https://learn.microsoft.com/en-us/azure/foundry/openai/concepts/model-retirement-schedule | 2026-09-02 | GA |
| Six-phase model migration | https://learn.microsoft.com/en-us/azure/foundry/foundry-models/concepts/model-migration | 2026-08-26 | GA |
| Tool support by region and model; fixed limits; 1,000 versions per agent | https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/limits-quotas-regions | 2026-09-07 | GA |
| Deployment types and EU Data Zone semantics | https://learn.microsoft.com/en-us/azure/foundry/foundry-models/concepts/deployment-types | 2026-08-12 | GA |
| Immutable agent versions; active version; rollback by switching | https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/development-lifecycle ; https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/publish-copilot#select-an-active-agent-version | 2026-08-27 ; 2026-08-26 | GA |
| Agents v2 / classic retirement dates; tool availability differences | https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/migrate | 2026-08-05 | GA |
| v1 API lifecycle | https://learn.microsoft.com/en-us/azure/foundry/openai/api-version-lifecycle | 2026-06-05 | GA |
| Portal GA scope and rollout pitfalls | https://learn.microsoft.com/en-us/azure/foundry/concepts/general-availability | 2026-09-09 | GA |
| SDK versions and cadence | https://learn.microsoft.com/en-us/azure/foundry/how-to/develop/sdk-overview ; https://github.com/Azure/azure-sdk-for-python/blob/main/sdk/ai/azure-ai-projects/CHANGELOG.md | 2026-08-26 ; 2026-09-04 | GA |
| Bicep api-versions | https://learn.microsoft.com/en-us/azure/templates/microsoft.cognitiveservices/accounts/projects | 2026-07-20 | GA |
| Workflows retirement 2026-12-01; Agent Framework 1.0 | https://devblogs.microsoft.com/agent-framework/microsoft-agent-framework-version-1-0/ | 2026-04-03 | GA (framework) |
| Landing-zone guidance (workload-owned Foundry) | https://learn.microsoft.com/en-us/azure/architecture/ai-ml/architecture/baseline-microsoft-foundry-landing-zone | 2026-06-19 | GA |
| Azure Policy built-ins for Foundry | https://learn.microsoft.com/en-us/azure/ai-services/policy-reference | 2026-07-13 | GA |
| DORA — Microsoft's published support is generic; the kit derives its own mapping | https://www.microsoft.com/en/trust-center/compliance/dora-compliance | 2026-09-12 | n/a |
