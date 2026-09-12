# Lifecycle — Versioning, Re-sync, Pinning and Deprecation

What is versioned on the platform, how a version moves from the claude.ai
export to the live Foundry agents, how the owner re-syncs, what is pinned
(SDK, models, API versions) and how anything is retired. The change
*process* is `CHANGE_MANAGEMENT.md`; this file fixes the *objects*, their
version identifiers and the order in which they move. Nothing here alters
what agents produce: the fidelity gate (`../scripts/verify_conversion.py`)
makes every version either byte-identical to the export or visibly new.

Owner: `{upn:francisco.gomes}` (accountable for creation, maintenance,
optimisation and updates — `../team/TEAM_MODEL.md` §1–§2). Control: ISO
27001:2022 A.8.9 (configuration management), A.8.32 (change management),
A.8.19 (installation of software on operational systems), A.5.37
(documented operating procedures); ISO 42001 A.6.2.5 (deployment),
A.6.2.7 (operation and monitoring), A.6.2.3 (documentation); DORA Art.
8(2)–(3) (identification of ICT assets and dependencies), 9(4)(e); EU AI
Act Art. 9 (life-cycle risk management, deployer of a modified system).

## 1. Versioned objects and their identifiers

| # | Object | Source of truth | Version identifier | Where the live copy is | Rebuilt by |
|---|---|---|---|---|---|
| V1 | claude.ai account export (skills, `PERSONA.md`) | `../../claude-account-export/` in git | git tag `export/{yyyy-mm-dd}` set on the commit that refreshed it | — (input only) | export from claude.ai (owner) |
| V2 | Conversion kit code and docs (`scripts/`, `agents/*_instructions.md`, `governance/`, `team/`, `operations/`) | git `main` | platform release tag `platform/v{major}.{minor}.{patch}` (§2) | — | PR (`CHANGE_MANAGEMENT.md` §3) |
| V3 | Built agent definitions | `build/` (rebuilt from scratch on every run, not committed) | `build/manifest.json` — SHA-256 per instruction set, knowledge and code file; copied as the drift baseline `build/baseline-{date}.json` (`CHANGE_MANAGEMENT.md` §7) | — | `convert_skills.py` → `verify_conversion.py` |
| V4 | Live agents, per-agent vector stores `vs-<agent>`, combined store `vs-assurance-combined`, verifier, advisor, orchestrator | V3 + `../integrations/registry.json` + `../agents/advisory_addendum.md` | agent name (idempotent key) + hash recorded in `build/manifest.json`; `metadata.kit_release` = the release tag (delta D-LC-S1) | Foundry project `{baseName}-proj` | `../deploy.sh` steps 3–6b |
| V5 | Durable team memory `vs-assurance-memory` | the live store itself — **not rebuildable** | dated export folder from `backup_vector_stores.py` (`BACKUP_DR.md` §3) | Foundry project | never rebuilt; restored from the export |
| V6 | Templates (requirement j) | `../templates/registry.json` + the `source` path of each template (export or kit) | `version` + `last_approved` per template; `../templates/audit.log` line per approved change | vector stores, code_interpreter files, `functions/delivery/renderers/` | `update_templates.py` (approval-gated) |
| V7 | Integration registry, OpenAPI specs, MCP gateway allow-list | `../integrations/registry.json`, `openapi/*.yaml`, `mcp/enx-gateway.json` | git (release tag); spec `info.version` inside each yaml | attached tools on each agent | `attach_integrations.py` |
| V8 | Infrastructure | `../infra/*.bicep`, `main.parameters*.json`, `../team/rbac.bicep`, `alerts.bicep` | git + ARM deployment name `{release}-{yyyymmdd}` (`az deployment group create -n`) | RG `rg-infosec-foundry` | pipeline with the deploy SP (`infra/validate.sh` first) |
| V9 | Logic Apps workflow definitions | `../workflows/*.json` + `pipelines.json` | git; `parameters.apiVersion` inside the definitions (`2025-05-01`) | Logic Apps Standard `{baseName}-la` (run history keeps old versions) | `scripts/package_workflows.py` → `config-zip` |
| V10 | Delivery / office-tools Function images | `../functions/delivery/`, `../functions/office-tools/` | container tag `infosec-delivery:{tag}` = release tag; `deliveryImage` / `officeToolsImage` params | `{baseName}-delivery`, `{baseName}-office` | `az acr build` + Bicep param |
| V11 | Python dependencies | `../setup/requirements.txt`, `../mcp-server/requirements.txt`, `../functions/delivery/requirements.txt` | exact pins (`==`) for the SDK surface; `>=` only for renderers (§5) | runners, Function image, MCP container | pip at build time |
| V12 | Model deployments (three tiers) | `main.bicep` `modelName/modelVersion`, `reasoningModel*`, `lightModel*`, `deploymentSku` | model name + explicit `modelVersion` (§5) | Foundry account `{baseName}-aif` | Bicep |
| V13 | Foundry data-plane API version | `FOUNDRY_API_VERSION` app setting (workflows) / SDK pin (scripts) | `2025-05-01` | Logic Apps + scripts | Bicep app setting + `requirements.txt` |
| V14 | Copilot Studio agent | `../integrations/copilot/README.md` | solution export `infosec-foundry-copilot-{release}.zip` in `Governance/Releases/` | `{env:infosec-foundry}` | manual republish after instruction changes (RUNBOOK FM-30) |
| V15 | Monitoring rules and workbook | `alerts.bicep`, `kql/*.kql`, `workbook.json` | git | Azure Monitor | pipeline |
| V16 | Approval policy and identity model | `../team/approval-policy.json`, `rbac.bicep`, `least-privilege/entra/groups.json` | git; `access_snapshot.sh` before/after | Entra / RBAC | `provision_identity.sh --apply`, `rbac.bicep` |

Rule: every live object traces to one git commit through the identifiers
above; anything that cannot (a hand edit in the portal) is drift and is
reverted by re-running the rebuild in the last column (`RUNBOOK.md` H8;
alert `agent_modified_by_non_deploy_identity`). Control: A.8.9; DORA Art.
8(2).

## 2. Release numbering

One tag for the whole platform: `platform/v{major}.{minor}.{patch}`, set
by the owner on the `main` commit that the `production` environment
deployed (`CHANGE_MANAGEMENT.md` §3 step 8). The tag is recorded in
`Governance/Releases/{tag}.md` together with the export tag it was built
from, the `build/manifest.json` hash, the image tags and the ARM
deployment name.

| Bump | When | Examples | Gates beyond the standard flow |
|---|---|---|---|
| **major** | a platform invariant, an approval tier, the taxonomy, an identity model or a model *family* changes; a re-sync that changes any report-producing agent's rules or thresholds | `Azure AI User` → custom consumer role; chat tier moves to a new model family; a new Tier | comparison set on every pipeline; line-manager awareness; `HUMAN_APPROVAL.md` / `DATA_PROTECTION_GUARDRAILS.md` reviewed in the same PR |
| **minor** | new agent, pipeline, integration, template, workflow, alert; a re-sync that only adds knowledge; a model *version* bump on one tier; SDK minor bump | new read-only spec; `modelVersion` `2024-11-20` → next | comparison set on affected pipelines; staged tier rollout (`CHANGE_MANAGEMENT.md` §1 "Model tier / capacity") |
| **patch** | docs, runbooks, KQL, thresholds, watchlist rows, instruction wording that the comparison set proves neutral, dependency patch pins | typo in a runbook; alert threshold 0.30 → 0.25 | standard flow, single reviewer |

Templates keep their own `version` in `../templates/registry.json`
(semantic within the template: `17.02.11` stays the DeepSearch protocol
version because it is the export's own identifier); a template bump always
implies at least a platform **minor**.

## 3. Re-sync from a fresh claude.ai export (flow F6)

The export is the master for everything a skill defines; the kit never
edits it except through `update_templates.py` after a Tier C approval.
Trigger: the source skills changed on claude.ai, or the semi-annual
calendar item (`CHANGE_MANAGEMENT.md` §9), or a falling first-pass rate
that `RUNBOOK.md` FM-08 attributes to drift.

| # | Step | Command / evidence | Gate |
|---|---|---|---|
| 1 | Ticket `{jira:INFOSEC-PLAT}-nnn` type *re-sync* (`CHANGE_MANAGEMENT.md` §1); note which skills changed on claude.ai | ticket | — |
| 2 | Pre-deploy backup of the memory store and a snapshot of the live vector-store file lists | `python3 operations/backup_vector_stores.py --out operations/backups/{date}` (`BACKUP_DR.md` §3) | folder present, manifest written |
| 3 | Refresh the export on a branch `change/{ticket}`; tag `export/{yyyy-mm-dd}` after merge | git diff limited to `claude-account-export/` | no secrets, no personal data in the export diff (`verify_conversion.py` grep gate) |
| 4 | Local chain | `python3 scripts/convert_skills.py && python3 scripts/verify_conversion.py && ./deploy.sh --dry-run` | all exit 0; freshness markers present |
| 5 | Diff `build/manifest.json` against the stored baseline; list every agent whose instruction or knowledge hash changed | compare the `sha256` fields of both manifests (`jq` diff of `build/manifest.json` vs the baseline) pasted into the PR | reviewer confirms the changed list equals the ticket's expectation |
| 6 | Template registry: bump `version` and `last_approved` for every template whose `source` hash changed — a template change carried by a re-sync is still a Tier C item: route it through `template-update-approval` (visual before/after) before merge | `update_templates.py --dry-run` per template | approval run id in the PR |
| 7 | Comparison set for each changed report-producing agent (`CHANGE_MANAGEMENT.md` §4) and `evaluation/run_evals.py` against the golden set (`evaluation/EVALUATION.md` §5) | diff + eval report attached | PASS on first attempt; every metric floor met; structure/threshold/section identical |
| 8 | PR review (deputy when the owner authored) → merge → `production` approval by the owner → `deploy.sh` by the deploy SP | Actions log | steps 1–7 of `deploy.sh` green, smoke test answered |
| 9 | Post-checks ≤ 1 business day: `RUNBOOK.md` H8 (only expected agents differ), H9, W1–W5; new baseline `build/baseline-{date}.json`; `create_orchestrator.py` re-wired the orchestrator to every live agent | evidence links in the ticket | — |
| 10 | Copilot Studio republish if any published agent's instructions changed (V14); user guides under `Governance/UserGuides/` reviewed (`SUPPORT_MODEL.md` §8); release tag + `Governance/Releases/{tag}.md` | tag | — |

Rollback: check out the previous `platform/` tag and run `deploy.sh`
(idempotent by agent name — instructions, tools and vector stores are
recreated from that build); templates roll back with a new approval run
(`update_templates.py` keeps the previous source as backup); the memory
store is untouched by a re-sync (it is never recreated by
`create_orchestrator.py` when it already exists — if it ever were,
restore per `BACKUP_DR.md` §4 R2).

Why the memory backup comes first: `deploy.sh` recreates every vector
store *except* `vs-assurance-memory`; the backup is the insurance against
an SDK behaviour change in that path (§5) and is cheap. Control: A.8.13;
ISO 42001 A.6.2.5.

## 4. Template versioning (requirement j)

| Rule | Implementation |
|---|---|
| A template has exactly one `source` and one `version` | `../templates/registry.json`; `update_templates.py` refuses an id it cannot resolve |
| Only an approved change moves a version | `template-update-approval` (P7D) → `update_templates.py --approved-by … --approval-run …` writes the source, re-runs convert → verify → `create_*.py --only` consumers → `stage_renderers.py`, bumps `version` and `last_approved`, appends `../templates/audit.log` |
| Consumers update together | the `consumers` and `pipelines` arrays drive which agents are recreated and which renderer is re-staged — a template can never be live in one consumer and stale in another |
| Previous version is recoverable | the backup file `update_templates.py` keeps + git history of the source; the SharePoint `Templates/Reviews/` page of the approval shows before/after |
| `last_approved: null` means never approved on this platform | `ciso-global-deck`, `evidence-summary-docx`, `xlsx-generic` ship `null`: their first production use requires one approval run (rollout P1 exit criterion in `ROLLOUT_PLAN.md`) |
| Deprecation | §6 row "Template" |

Control: A.8.32, A.8.9; ISO 42001 A.6.2.4–A.6.2.5; EU AI Act Art. 14 (the
visual review is the oversight act).

## 5. Pinning — SDK, models, API versions, runtimes

| Pinned item | Where | Current pin | Bump procedure | Check after bump |
|---|---|---|---|---|
| `azure-ai-projects`, `azure-ai-agents`, `azure-identity`, `python-dotenv`, `PyYAML`, `mcp` | `../setup/requirements.txt`, `../mcp-server/requirements.txt` (`==`) | `1.0.0`, `1.1.0`, `1.19.0`, `1.0.1`, `6.0.2`, `1.12.3` | PR type *infra* (medium risk): read the migration notes for the new major, run every script `--dry-run`, then `deploy.sh` on `dev` (`main.parameters.json`) before `prod` | `RUNBOOK.md` H8–H9; `memory_store.py list`; `backup_vector_stores.py --dry-run` then live |
| Function runtime deps | `../functions/delivery/requirements.txt` (`>=` floors) | see file | floors are acceptable because the image tag (V10) freezes the resolved set; a rebuild is a *minor* | `/render` smoke on each format via the comparison set |
| Node renderers | `renderers-src/*/package.json` inside the image | see files | as above | rendered PPTX byte-compared (deterministic generators) |
| Chat / reasoning / light models | `main.bicep` `modelName` + `modelVersion` (explicit `2024-11-20` for chat; `''` = provider default for reasoning/light) | `gpt-4o` / `o3-mini` / `gpt-4o-mini`, `DataZoneStandard` | set an **explicit** `reasoningModelVersion` / `lightModelVersion` before production (delta D-LC-B1) so a provider-side default change cannot alter outputs silently; bump = *minor* with the staged rollout, the comparison set and the accuracy-floor test (`MODEL_ROUTING.md` "Accuracy floor"; `TOKEN_ECONOMY_PLAYBOOK.md` §7; `evaluation/EVALUATION.md` §5) | tokens/latency (`kql/latency-and-tokens.kql`) for one week; verifier first-pass rate |
| Model retirement | Azure announces retirement dates per model version | — | the owner tracks the notice at M2; a replacement version is deployed as a fourth deployment, compared, then the tier is switched (`attach_integrations.py --only`) — never in-place on retirement day | comparison set |
| Foundry data-plane API version | workflows `apiVersion` default `2025-05-01`; `FOUNDRY_API_VERSION` app setting | `2025-05-01` | change the app setting and the SDK pin in the same PR; re-run `package_workflows.py` | one pipeline end-to-end to the verifier (no approval) |
| Bicep API versions | `@2025-04-01-preview` (Cognitive Services), others in `main.bicep` | see file | `infra/validate.sh` (build + lint) then `what-if`; preview → GA moves are *patch* if `what-if` shows no change | `what-if` output attached |
| RAI policy | `main.bicep` `raiPolicy` `infosec-security-analysis` | see file | *high* risk change (`CHANGE_MANAGEMENT.md` §5) | content-filter block count (workbook "Data protection") |
| Python / Node runtimes | Function image base, MCP image base, CI runner | Python 3.11 (Function), 3.12 (MCP image), Node 20 | image rebuild = *minor* | image scan (ACR / Defender) |
| GitHub Actions | `.github/workflows/ci.yml` (delta D-OPS-G1) | pinned action versions | Dependabot PR = *patch* | CI green |

Rules: never two SDK majors in flight (scripts and MCP server pin the
same versions); never bump a model and an SDK in the same release
(attribution of a regression must be unambiguous); pins are bumped by PR
only — `pip install -U` on a runner is not a change. Control: A.8.19,
A.8.8 (vulnerability management drives the patch cadence: SDK and image
patches monthly at M3 unless a CVE forces earlier); DORA Art. 9(4)(f)
(patches and updates); ISO 42001 A.6.2.5.

## 6. Deprecation and retirement

Retire in the order *disable → observe → remove*, and never remove the
record. Every row is a Tier C change; rows marked † also need the
custodian (`../team/TEAM_MODEL.md` §10).

| Object | Disable | Observe | Remove | Record kept |
|---|---|---|---|---|
| Agent (a skill withdrawn from the export, or replaced) | remove it from the orchestrator's connected tools (`create_orchestrator.py` re-wires from the live list after the agent is renamed `zz-retired-<name>`) and from the Copilot publication | 30 days: no runs in `AppDependencies` for the agent | delete the agent and its `vs-<agent>` store (owner PIM `Azure AI Developer`); drop from `build/` by removing the skill from the export (`convert_skills.py` rebuilds without it); `verify_conversion.py` COVERAGE must still pass | `build/baseline-{date}.json` before removal; `Governance/Releases/{tag}.md` lists the retirement; threads that used it are kept to their normal retention (`TEAM_MODEL.md` §13) |
| Template | set `"deprecated_on": "{date}"` in `../templates/registry.json` (delta D-LC-TR1) via `template-update-approval`; pipelines referencing it fail closed at `/render` | one quarterly template inventory review (`CHANGE_MANAGEMENT.md` §9) | remove the registry entry; `update_templates.py` audit line `retired`; the source stays in git history | `../templates/audit.log`; last approved rendering kept in `Templates/Reviews/` |
| Pipeline (entry in `../workflows/pipelines.json`) | disable the Logic Apps workflow instance (owner PIM `Logic Apps Standard Operator`; no approval needed to disable) and set `approvalKind` to `RETIRED` in `pipelines.json` (a kind absent from `../team/approval-policy.json` is rejected by the approval flow, so a late callback cannot store anything) | 30 days of run history: no triggers | delete the instance; remove the `pipelines.json` entry; `report-status.json` keeps answering for historical run ids from Log Analytics | run history exported to `Governance/Operations/` before deletion (Log Analytics retains 365 d) |
| Integration / connection † | remove the connection from every agent in `../integrations/registry.json` (`attach_integrations.py` re-attaches without it); disable the Foundry connection | 30 days: no tool calls in `AppDependencies` by `gen_ai.tool.name` | delete the connection; custodian revokes the service account; Key Vault secret **disabled** (not purged — purge protection); `ACCESS_REGISTER.md` row closed | register change log; KV secret version history |
| Model deployment | move every agent off the tier (`model_tier` in the registry) — advisory agents never leave `reasoning`, so a reasoning model is replaced, never removed | 7 days of `AzureOpenAIRequests` by `ModelDeploymentName` = 0 | delete the deployment via Bicep (remove the resource; `what-if` shows exactly one delete) | ARM deployment history |
| Workflow (routine replacement) | disable the workflow | 30 days | delete the instance and the definition file | git history; run history export |
| Alert / KQL | disable the rule (`enableAlerts` or remove from `logRules`) | one review cycle | remove from `alerts.bicep` and `kql/` | git |
| Document / runbook | add a `Superseded by …` banner (as done for `../team/README.md`, delta D-T4) | next quarterly review | delete the file | git history |
| Whole platform (exit) | freeze Tier A/B approvals (approval flow rejects all kinds); export `Reports/` remains in SharePoint (it was never platform state) | — | `BACKUP_DR.md` §1 inventory walked in reverse: memory export filed under `Governance/Backups/final/`, secrets disabled by custodians, Entra groups emptied (leaver runbook ×5), RG deleted after the ISMS record schedule confirms retention of logs (export Log Analytics to storage first) | `Governance/Releases/decommission.md`; DORA Art. 28(8) exit evidence for the internal ICT service |

Control: A.5.10 (acceptable use and lifecycle of assets), A.8.10
(information deletion), A.8.32; DORA Art. 8(2)–(3), 28(8); ISO 42001
A.6.2.8 (retirement is part of the life cycle); EU AI Act Art. 26 (deployer
ceases use of a system it no longer oversees).

## 7. Environments

| Environment | Parameter set | Purpose | Data |
|---|---|---|---|
| `dev` | `main.parameters.json` (`environmentName: dev`, public access on, no VNet, placeholder images) | SDK/model bumps, new pipelines, comparison runs to the verifier | synthetic / public inputs only (`Governance/ComparisonSet/inputs/`) |
| `prod` | `main.parameters.prod.json` (private endpoints, `Disabled` public access, pinned images, budget, team RBAC, MCP hosting) | the five users | Euronext data |

Rules: same Bicep, same scripts, different parameters (A.8.31); a change
reaches `prod` only from a commit that deployed cleanly to `dev`; no
Euronext supplier data in `dev` (a `dev` project has no `Sites.Selected`
grant and no `conn-*` service accounts — its registry attaches tools with
`--dry-run` only). Where a second subscription is not available, `dev` is
a second RG in the same subscription with its own Foundry account; the
Bing connection and RAI policy are identical so egress and filtering
behave the same.

## 8. Calendar (adds to `CHANGE_MANAGEMENT.md` §9 — not a replacement)

| Cadence | Activity | Evidence |
|---|---|---|
| Before every `deploy.sh` (non-dry) | memory-store export (§3 step 2; delta D-LC-D1 automates it) | `operations/backups/{date}/manifest.json` filed under `Governance/Backups/` |
| Monthly (M3) | SDK / image patch review; model-retirement notices | ticket or "no action" note in `Governance/Operations/{yyyy}-{mm}/` |
| Quarterly | template inventory (`deprecated_on`, `last_approved` age), agent usage (retire candidates = zero runs in 90 days), pin review | `Governance/Operations/` quarterly note |
| Semi-annual | re-sync (§3) when the export changed; restore test (`BACKUP_DR.md` §6) | release tag; restore-test note |
| Annual | major-version review: invariants, environments, retirement of anything not used in 12 months; ISO 42001 AI-system impact assessment refresh | management-review input (`KPIS.md` §4) |

## 9. Shared deltas needed by this file (not applied here)

| Id | Target | Location | Literal text |
|---|---|---|---|
| D-LC-B1 | `infra/main.bicep` | params `reasoningModelVersion`, `lightModelVersion` defaults | replace `''` with an explicit catalogue version string confirmed by `az cognitiveservices model list -l {location} -o table` at first production deployment (e.g. `'2025-01-31'` for `o3-mini`, `'2024-07-18'` for `gpt-4o-mini`), and append to both `@description`s: ` — pin explicitly in prod (operations/LIFECYCLE.md §5)` |
| D-LC-S1 | `scripts/create_agents.py`, `scripts/create_delivery_agents.py`, `scripts/create_orchestrator.py` | the `metadata` dict passed on agent create/update | add `"kit_release": os.environ.get("KIT_RELEASE", "unversioned")` so every live agent carries the platform release tag (operations/LIFECYCLE.md §1 V4); `deploy.sh` exports `KIT_RELEASE="$(git describe --tags --match 'platform/*' --always 2>/dev/null)"` |
| D-LC-TR1 | `templates/registry.json` | `_comment` append | ` Optional per-template field "deprecated_on": "YYYY-MM-DD" marks a retired template (operations/LIFECYCLE.md §6): the delivery Function refuses to render it and template-manager lists it as retired; remove the entry only after the next quarterly template review.` |
| D-LC-D1 | `deploy.sh` | after `DRY=""` / `[ … ] && DRY="--dry-run"` and before step `[1/7]` | `if [ -z "$DRY" ]; then echo "==> [0/7] Pre-deploy export of vs-assurance-memory + vector-store inventory (read-only)"; python3 ../operations/backup_vector_stores.py --stores vs-assurance-memory --out "../operations/backups/$(date -u +%Y-%m-%d)" \|\| { echo "backup failed — aborting (operations/BACKUP_DR.md §3)"; exit 1; }; fi` |
| D-LC-R1 | `README.md` | folder layout tree, under `operations/` (after delta D-OPS-R1) | `│   ├── LIFECYCLE.md, BACKUP_DR.md, backup_vector_stores.py   ← versioning/re-sync/pinning/deprecation; state inventory, RPO/RTO, restore, region-failure playbook` and `│   ├── ROLLOUT_PLAN.md, KPIS.md, CONTINUOUS_IMPROVEMENT.md   ← pilot → four users → hypercare; KPI set + ISMS rhythm; feedback → backlog → quarterly cycle` |
| D-LC-T1 | `team/TEAM_MODEL.md` | §3 row F6 "Derived requirement" cell | append ` → procedure: ../operations/LIFECYCLE.md §3; pre-deploy memory export: ../operations/BACKUP_DR.md §3` |
| D-LC-C1 | `operations/CHANGE_MANAGEMENT.md` | §9 "Semi-annual" row | replace `restore test of vector stores from the export (the export *is* the backup — \`deploy.sh\` rebuilds every store)` with `restore test per \`BACKUP_DR.md\` §6 (agents and knowledge stores rebuild from the export; \`vs-assurance-memory\` restores from the \`backup_vector_stores.py\` export)` |
