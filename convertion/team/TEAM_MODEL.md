# Team Model — Ownership, Identity/RBAC and Approval Model (authoritative)

Single model of record for **who may run, approve, release and change**
the InfoSec Assurance platform on Euronext's Azure AI Foundry. It merges
the operations-first lens (`README.md`) and the least-privilege lens
(`least-privilege/`) into one design; where the two disagreed the
stricter control wins unless it contradicts the kit as shipped or leaves
five people unable to run the platform (every trade-off is in §21).
Nothing here changes what agents produce; `RACI.md` carries the
responsibility matrix per lifecycle activity.

Platform invariants respected throughout: agents read-only
(`../governance/DATA_PROTECTION_GUARDRAILS.md` §2 — non-GET stripped);
verifier + human approval before any write (`../governance/HUMAN_APPROVAL.md`
Layers 1–3); `Reports/<Supplier>/<Service>/` taxonomy
(`../sharepoint/README.md`); Entra ID users and managed identities
everywhere, no keys; EU region; no Euronext data to the web; light / chat /
reasoning tiers (`../governance/MODEL_ROUTING.md`). Placeholders in
`{braces}`; no real UPNs, object ids, hostnames or secrets anywhere in
this folder.

Files this model governs (companions in this folder and in
`../operations/access-governance/`):

| File | Role in the model |
|---|---|
| `TEAM_MODEL.md` (this file) | model of record; every other file below implements a section of it |
| `RACI.md` | responsibility matrix per lifecycle activity (§16) |
| `rbac.bicep` + `rbac.parameters.example.json` | Azure role assignments per §7 and PIM eligibilities per §6 (delta D-T1 applied); `provision_identity.sh --apply` fills a git-ignored `rbac.parameters.json` copy |
| `approval-policy.json` | machine-readable §12 for the approval flow behind `approvalWebhookUrl` (delta D-T2 applied: `REPORT_DELIVERY` + `reportType`, `MEMORY_DELETE`, owner SoD rule) |
| `custom-role.agent-consumer.json` | preventive control of §7.1 |
| `least-privilege/entra/groups.json` | group definitions, owners, review cadence (§6; delta D-T3 applied — the seven groups of record) |
| `least-privilege/scripts/provision_identity.sh` (`--plan/--apply/--verify`), `access-review.sh` (`--quick`) | provisioning and the read-only drift checks called from `deploy.sh` |
| `ACCESS_REGISTER.md` | living register: people, groups, non-human identities, approved MCP clients, change log (§5, §10, §11) |
| `entra-groups.md` | `az` / Graph commands that create the seven groups, PIM role settings, the CA policy, the access package and the quarterly Entra access reviews (§6, §15) |
| `sharepoint-permissions.md` | site roles for the five + the three `Sites.Selected` grants with grant / list / revoke commands (§8, §9) |
| `ONBOARDING.md`, `OFFBOARDING.md` | person-centric joiner / leaver checklists with evidence commands (§14); the admin runbook stays in `../operations/access-governance/ACCESS_LIFECYCLE.md` |
| `USER_QUICKSTART.md` | one section per system a–j: invocation, inputs (Supplier + Service), output path, approval tier, portal map (§4, §12) |
| `../operations/{RUNBOOK,SUPPORT_MODEL,CHANGE_MANAGEMENT,MONITORING}.md`, `kql/`, `alerts.bicep` | day-2 operation, support, change control (Tier C process), alert catalogue |
| `least-privilege/` (`.md` files) | **historical design variant** — a different vocabulary (six groups, approval tiers 1/2/3); see its `README.md` for the name mapping and §21 for every decision. Only `least-privilege/entra/groups.json` and `least-privilege/scripts/provision_identity.sh` are live. |
| `../operations/access-governance/ACCESS_LIFECYCLE.md`, `QUARTERLY_ACCESS_REVIEW.md`, `BREAK_GLASS.md`, `scripts/access_snapshot.sh` | runbooks for §14, §15 and §12.3 |

Consolidation note for the maintainer: `README.md` §1–§15 and
`least-privilege/{TEAM_MODEL,IDENTITY_RBAC,APPROVAL_ROUTING,THREADS_MEMORY,RACI}.md`
are superseded by this file and `RACI.md`; keep them until the deltas of
§20 are applied, then retire them (git history is the record).


> Role names follow the current Foundry RBAC naming (Foundry User / Foundry Owner /
> Foundry Account Owner / Foundry Project Manager); the underlying role definition
> GUIDs in `rbac.bicep` are unchanged — `enterprise/ENTERPRISE_BLUEPRINT.md` ID-1.

## 1. Team and roles

| Person | UPN | Standing role | Additional privileges |
|---|---|---|---|
| Francisco Gustavo Gomes | `{upn:francisco.gomes}` | **Accountable owner** — creation, planning, maintenance, optimisation, updates / re-sync of the whole solution; assurance user | Platform admin (PIM-eligible only), approver of template / platform / prompt / registry changes, owner of the user-facing groups, SharePoint site owner, Copilot Studio maker, GitHub maintainer |
| José Mogollon | `{upn:jose.mogollon}` | Assurance user | Report approver |
| Pedro Santos | `{upn:pedro.santos}` | Assurance user | Report approver |
| José Meireles | `{upn:jose.meireles}` | Assurance user | Report approver |
| Tânia Morais | `{upn:tania.morais}` | Assurance user | Report approver |
| Deputy | `{upn:deputy-approver}` — one of the four, nominated by the owner, confirmed by `{upn:line-manager}`, recorded in `ACCESS_REGISTER.md` | Assurance user | Senior approver (Tier B); approves the **owner's own** Tier C items; code-owner reviewer of owner-authored PRs; break-glass eligible |

All five have the **identical persona experience**: the preamble in
`../agents/persona_system_prompt.md` is agent-side and the same for every
caller — no per-user persona, prompt, knowledge pack or model tier. What
differs per person is only *what they may change* (§7) and *what they may
approve* (§12). The deputy is the only role beyond "owner + users"; it
exists because ISO 27001:2022 A.5.3 and DORA Art. 5(2) / 9(4)(e) do not
allow the person who changes a control to be the only person able to
approve it, and because DORA Art. 9 / 11 continuity needs a second pair of
hands.

## 2. Ownership register

| Object | Accountable | Custodian / executes | Consulted |
|---|---|---|---|
| Foundry account / project, agents, vector stores, model deployments, RAI policies (`../infra/main.bicep`, `../scripts/`) | owner | owner (PIM window) or deploy SP `{app:infosec-foundry-deployer}` via GitHub OIDC | landing-zone team `{group:azure-platform}` |
| Foundry connections (`conn-*`, `bing-grounding`, `enx-gateway-mcp`, `app-insights`) — `../integrations/registry.json` | owner | owner (Foundry side); target-system custodians issue / revoke identities (§10) | system owners |
| Logic Apps Standard (`../workflows/`), delivery Function (`../functions/delivery/`), Key Vault, storage, Log Analytics / App Insights | owner | owner (PIM) / deploy SP | landing-zone team |
| SharePoint site `{sharepoint:infosec-assurance}` (`GRC/TPA/Active`, `Reports/`, `Templates/`, `Governance/`) | owner (site owner) | SharePoint admins `{group:spo-admins}` (site-collection backup) | DPO `{group:dpo}` for `Reports/DPO/` |
| Shared memory `vs-assurance-memory` (`../scripts/memory_store.py`) | owner (RoPA entry `{ropa:infosec-foundry-memory}`) | every user adds; author or owner deletes (§13) | DPO |
| `../templates/registry.json` and the template library | owner | `template-manager` agent + `../scripts/update_templates.py` after Tier C approval | users (proposers) |
| GitHub repo `{github:org/repo}` | owner (CODEOWNERS) | owner; deputy reviews owner-authored PRs | GitHub org admins |
| Copilot Studio agent in `{env:infosec-foundry}` (`../integrations/copilot/README.md`) | owner (Environment Maker) | owner | Power Platform admins |
| Entra groups that grant the owner privilege (`-owner`, `-senior-approvers`, `-admin-pim`, `-breakglass`) | `{upn:line-manager}` | Entra IAM team `{group:iam-admins}` | owner |

Control: ISO 27001:2022 A.5.2 (roles and responsibilities), A.5.9 (asset
ownership); DORA Art. 5(2); ISO 42001 A.3.2.

## 3. Operating flows → derived access

| # | Flow | Actor | Identity in use | Derived requirement |
|---|---|---|---|---|
| F1 | Converse with advisors / orchestrator (g, h, i) via playground, Copilot, MCP | any of the five | own Entra user | `Foundry User` (or the agent-consumer custom role) on the project; Copilot agent shared to the users group; local MCP = own `az login` |
| F2 | Request a report (a–f, d2): upload PDF or trigger a pipeline with Supplier / Service | any of the five | own user → Logic App MI → Function MI | trigger accepts only authenticated team callers; `requestedBy` taken from the token claim |
| F3 | Approve a report before render / store | a different member (four-eyes) | own user in Teams Approvals | approver ∈ tier group, approver ≠ requester, decision recorded |
| F4 | Propose a template change (j) | any of the five via `template-manager` | own user | proposal open to all; approval owner-only |
| F5 | Change the platform (Bicep, registry, instructions, scripts, tiers, Copilot publication) | owner (peers propose via PR) | owner + PIM; deploy SP via OIDC | code-owner review; `production` environment approval |
| F6 | Re-sync from a fresh claude.ai export | owner | as F5 | `../deploy.sh` runs from the pipeline; drift baseline refreshed |
| F7 | Incident (egress alert, verifier FAIL spike, injection, credential exposure, outage) | any user reports / stops own runs; owner leads; deputy if owner absent | owner PIM / deputy break-glass | disable connection, workflow, agent tool or secret without approval; change only with approval → `../operations/RUNBOOK.md` |
| F8 | Rotate an integration credential | owner + custodian | owner PIM `Key Vault Secrets Officer` | new KV secret version; connection re-pointed |
| F9 | Monthly evaluation + cost review (`../ARCHITECTURE.md` metrics) | owner; users consulted | owner standing `Log Analytics Reader` | users need no monitoring role (§5) → `../operations/MONITORING.md` §5, `RUNBOOK.md` M1–M2 |
| F10 | Quarterly access review | owner (user groups); line manager (privileged groups) | Entra access reviews + `access-review.sh` | evidence in `Governance/AccessReviews/{yyyy}-Q{n}/` |
| F11 | Save / search team memory | any of the five | own user via MCP `save_memory` / advisor `MEMORY:` block | add = own identity; delete = author or owner |
| F12 | Support | requester → peer (L1) → owner (L2) → landing-zone / Microsoft (L3) | — | Teams channel `{teams:infosec-assurance-platform}` → `../operations/SUPPORT_MODEL.md` |

Consequences: four people need data-plane use only; one needs
control-plane change for bounded windows → two human access levels
(standing use, PIM change). `requestedBy` must come from the caller's
token, never from free text, or F3 is not enforceable (delta D-W1/D-W2).
F4/F5 are the only owner-only decisions, so the owner is never a
bottleneck for daily reports. The owner also produces reports, so a peer
approves the owner's reports (§12.2).

## 4. Minimum access per system a–j

Agent-side credentials (Foundry connections) are never user permissions:
the agent holds the read-only enterprise surface; the user holds only the
right to run it. Requirement ids per `../REQUIREMENTS.md`; pipeline names
per `../workflows/pipelines.json`.

| Req | System | User action | Minimum user grant | Identity doing the work | Tier (§12) |
|---|---|---|---|---|---|
| a | DeepSearch HTML (`deepsearch-report`) | ask agent / Teams form with Supplier + Service | `Foundry User`; SharePoint `Reports/` Read | project MI (Bing, SSC, IAF, CMDB, ENX gateway — read); Logic App MI; Function MI (writer) | **A** peer four-eyes |
| b | OneTrust PDF → DPO DOCX (`dpia-dpo-report`) | upload to own thread; trigger | `Foundry User`; `Reports/DPO/` Read | `conn-onetrust` (viewer); Function MI | **B** senior four-eyes |
| c | OneTrust PDF → Cyber Forum PPTX (`cyber-forum-pptx`) | as b | as b + `Reports/` Read | `conn-onetrust`, `conn-sharepoint-graph` read; Function MI | **B** |
| d | OneTrust PDF → Global CISO PPTX (`ciso-global-pptx`) | as c | as c | + `conn-jira-assets` CMDB read | **B** |
| d2 | TPA evidence tree analysis (`tpa-evidence-analysis`) | trigger with Supplier (+ Service) | `Foundry User`; `Reports/` Read; Edit on `GRC/TPA/Active` is a pre-existing job duty | project MI `Sites.Selected` read | **A** |
| e / f | SOC / pentest upload → summary (`soc-report-summary`, `pentest-report-summary`) | upload to own thread; trigger | `Foundry User`; `Reports/` Read | Function MI | **A** |
| g / h | Framework advisory, TPRM knowledge (+ file generation) | converse; download from thread | `Foundry User` | project MI advisory read surface (`advisory_read_only_toolset`) | none (stays in-thread) |
| i | Persona + read-only enterprise + sanitised web | converse (portal, MCP, Copilot) | `Foundry User`; membership of `sg-infosec-foundry-users` for Copilot audience / hosted-MCP Easy Auth | project MI (all `conn-*` read) | none |
| j | Template management (`template-update-approval`) | select / analyse / edit / preview; propose | `Foundry User`; `Templates/` Read | Function MI writes `Templates/Reviews/` | **C** owner-only (deputy if proposer = owner) |

Not granted to users, and why: any Azure role beyond `Foundry User`
(outputs arrive in-thread, Teams or SharePoint); SharePoint write on
`Reports/` or `Templates/` (Function MI is the only writer); Key Vault or
connection secrets; GitHub write (changes flow through `template-manager`
and PRs); monitoring roles (owner runs F9; incidents are reported, not
triaged in logs by users). Control: ISO 27001:2022 A.5.15, A.8.3 (need to
know); DORA Art. 9(4)(c).

## 5. Additions ledger (every grant above the §4 minimum)

| # | Principal | Addition | Justification | Control |
|---|---|---|---|---|
| L1 | owner | `Foundry Owner` on Foundry account — **PIM 8 h** | agent / vector-store / connection maintenance (`deploy.sh` steps 3–6b) | PIM: MFA + justification + ticket; Activity Log; A.8.2 |
| L2 | owner | `Contributor` on RG — PIM 8 h, line-manager approval | hotfix Bicep / config when the pipeline cannot | PIM approval; activations reviewed quarterly; A.8.2 |
| L3 | owner | `Key Vault Secrets Officer` — PIM 2 h | credential rotation | immutable secret versions = A.5.17 evidence |
| L4 | owner | `Logic Apps Standard Developer` + `Operator` — PIM 8 h | deploy workflows; resubmit / disable in incident | run history; A.8.2 |
| L5 | owner | `Website Contributor` on delivery Function — PIM 4 h | `func azure functionapp publish` | PIM |
| L6 | owner | `Reader` on RG + `Log Analytics Reader` — **permanent** | daily monitoring; read-only, low blast radius | quarterly review; A.8.15 / A.8.16 |
| L7 | owner | `Storage Blob Data Reader` on `deliverables` — PIM 4 h | troubleshooting rendered artefacts | PIM |
| L8 | owner | `Monitoring Contributor` — PIM 4 h | alert rules, KQL detections | PIM |
| L9 | owner | SharePoint Site Owner; `Templates/`, `Governance/` Edit; `Reports/` Contribute (no delete) | site admin; `Sites.Selected` grants need site ownership; versioned corrections | versioning + SharePoint audit log; A.8.3 |
| L10 | deputy | `sg-infosec-foundry-senior-approvers`; PIM-eligible `-breakglass` | SoD (A.5.3) + continuity (DORA Art. 9) | routing rule; PIM approval by line manager / SOC on-call |
| L11 | deploy SP `{app:infosec-foundry-deployer}` (OIDC, no secret) | `Contributor` RG; `RBAC Administrator` ABAC-constrained to the role set in `rbac.bicep`; `Foundry Owner` (account); `Key Vault Secrets Officer` (seeding) | reproducible deployments; removes the owner's standing write | GitHub `production` environment approval by owner; no interactive sign-in; A.5.17, A.8.32 |
| L11b | read-only SP `{app:infosec-foundry-readonly}` (OIDC, no secret) | `Reader` (RG); `Azure AI User` (Foundry account/project); Graph `Directory.Read.All` | the nightly drift and access-review job must be able to *see* everything and change nothing — reusing the deploy identity for a detective control would give a nightly unattended job Contributor | federated subject is the `main` branch with no environment and therefore no approval gate, which is only safe because the identity is read-only; A.5.15, A.5.18, A.8.32 |
| L12 | Logic App MI | `Foundry User` (project); `Key Vault Secrets User` (named secrets); runtime storage data roles; Graph `Sites.Selected` **read** on the one site | runs agents / verifier; KV references; `scheduled-deepsearch` watchlist list read | managed identity |
| L12x | Logic App MI | Graph `Sites.Selected` **write** — **time-boxed exception** until delta D-W3 routes the two direct `PUT …/content` uploads in `onetrust-assessment-intake` and `scheduled-deepsearch` through the delivery Function | kit as shipped uploads directly from these two workflows | expiry date in `ACCESS_REGISTER.md`; removed in the same PR as the delta |
| L13 | Delivery Function MI | Graph `Sites.Selected` **write** on the one site; `Storage Blob Data Contributor` on `deliverables`; `Key Vault Secrets User` (if the Function reads any secret) | the single SharePoint write path after verifier PASS + human approval | `../functions/delivery/README.md` |
| L14 | Foundry project MI | Graph app permissions (all read, §8); account MI `Key Vault Secrets User` for KV-backed connections | OpenAPI tools authenticate with managed identity, not secrets | non-GET stripped; admin consent recorded |
| L15 | `sg-infosec-foundry-readers` (empty by default) | `Reader` RG, `Log Analytics Reader`, `Logic Apps Standard Reader` / Operator (run history), SharePoint Visitor on `Governance/` | audit evidence without touching the owner's account | populated per engagement; A.5.35 |
| L16 | hosted MCP MI (only if deployed) | `Foundry User` (project) | shared endpoint for the ENX gateway | Easy Auth allowed group |

A new ledger row is a platform change (Tier C). A row nobody can justify
at the quarterly review is removed, not renewed (ISO 27001:2022 A.5.18).

## 6. Entra ID security groups

Naming `sg-infosec-foundry-<purpose>`; security groups, mail-disabled,
**assigned** membership (no dynamic rules), not role-assignable, covered by
Entra access reviews. Membership changes go through entitlement-management
access packages where available, otherwise the group owner adds directly
and records the change in `ACCESS_REGISTER.md`.

The group definitions of record (names, purpose, owners, initial members,
review cadence, the Conditional Access policy and the service principals) live
in `least-privilege/entra/groups.json` and are created by
`least-privilege/scripts/provision_identity.sh`, which deploys **this** model's
`rbac.bicep`. Those two files are the only live artefacts in that folder;
every `.md` there is a historical design variant with a different vocabulary
(six groups, approval tiers 1/2/3) — the mapping to the names below is in
`least-privilege/README.md`, and each decision is recorded in §21.

| Group | Members | Group owner (adds / removes) | Approval to add | Review | Grants |
|---|---|---|---|---|---|
| `sg-infosec-foundry-users` | all five | owner (backup owner `{group:iam-admins}`) | owner, on line-manager request via access package `AP-InfoSec-Foundry-User` (12 months) | quarterly, owner | Foundry data plane, SharePoint site member, Copilot audience, hosted-MCP Easy Auth, GitHub read, CA policy scope |
| `sg-infosec-foundry-report-approvers` | all five (joiners after onboarding attestation, §14) | owner | owner | quarterly, owner | Tier A approvals |
| `sg-infosec-foundry-senior-approvers` | owner + deputy | `{upn:line-manager}` (via IAM team) | line manager | quarterly, line manager | Tier B approvals; Tier C for the owner's own items (deputy) |
| `sg-infosec-foundry-owner` | owner only | line manager | line manager | quarterly, line manager | **standing low-privilege only**: `Reader` RG, `Log Analytics Reader`, SharePoint site owner, Copilot Studio maker, GitHub Maintain, KV `Reader` (names, not values) |
| `sg-infosec-foundry-admin-pim` | eligible: owner; active: nobody by default | line manager (PIM for Groups policy) | PIM activation: MFA + justification + ticket; max 8 h; line-manager approval for `Contributor`; self-activation for AI Developer / KV / Logic App / Function / Monitoring / Blob roles | activations monthly; membership quarterly, line manager | the PIM set of §5 L1–L5, L7, L8 |
| `sg-infosec-foundry-breakglass` | eligible: deputy; active: nobody | line manager | PIM activation approved by line manager or SOC on-call `{group:soc-oncall}`; max 8 h; only when the owner is unavailable | every activation reviewed by the owner ≤ 5 business days | same role set as `-admin-pim` (no RBAC Administrator) |
| `sg-infosec-foundry-readers` | none by default; ISMS / internal audit `{group:isms-audit}`, DPO `{group:dpo}` per engagement | owner | head of internal audit / DPO | emptied after engagement | §5 L15 |

Rules: the owner owns the groups he uses to run the team, never the
groups that grant him privilege or approve his changes (ISO 27001:2022
A.5.3 / A.8.2 — no privileged self-grant). If Entra ID P2 / PIM is not
licensed, `rbac.bicep enablePim=false` assigns the `-admin-pim` roles
permanently to `sg-infosec-foundry-owner` and the exception is recorded in
`ACCESS_REGISTER.md` with a review date. Conditional Access
`CA-InfoSec-Foundry` targets all groups for *Azure Management*, *Azure AI /
Cognitive Services* and *Office 365 SharePoint Online*: MFA + compliant
device, sign-in frequency 12 h, legacy auth blocked (A.8.5; DORA Art.
9(4)(d); NIS2 Art. 21(2)(j)).

## 7. Azure RBAC per resource

Resource names per `../infra/main.bicep` (`{baseName}` = `infosecfoundry`;
Key Vault `{baseName}-kv` is declared by delta D-B2). Standing = permanent;
PIM = eligible via `-admin-pim` / `-breakglass`. All assignments are
deployed by `rbac.bicep`; nothing is assigned by hand after bootstrap
(§18). Verify role GUIDs with `az role definition list` before first
deployment (§19).

| Resource | `-users` | `-owner` (standing) | `-admin-pim` / `-breakglass` (PIM) | Deploy SP | Workload identities | `-readers` |
|---|---|---|---|---|---|---|
| RG `rg-infosec-foundry` | — | `Reader` | `Contributor` 8 h (line-manager approval) | `Contributor`; `RBAC Administrator` with ABAC condition restricting grantable roles to the set in `rbac.bicep` | — | `Reader` |
| Foundry account `{baseName}-aif` | — | — | `Foundry Owner` 8 h | `Foundry Owner` | account MI: `Key Vault Secrets User` | `Reader` |
| Foundry project `{baseName}-proj` | `Foundry User` **or** custom `InfoSec Foundry Agent Consumer` (§7.1) | as user | — | inherits | Logic App MI, hosted-MCP MI: `Foundry User`; Function MI: **none**; Copilot connector: delegated (OBO) | `Reader` |
| Model deployments (`gpt-4o`, `o3-mini`, `gpt-4o-mini`) | via AI User data actions | — | via AI Developer | Bicep-managed | — | — |
| Key Vault `{baseName}-kv` (RBAC model, soft-delete + purge protection) | — | `Reader` (names only) | `Key Vault Secrets Officer` 2 h | `Secrets Officer` (seeding) | Logic App MI, account MI, Function MI: `Key Vault Secrets User` scoped to the named secrets | — |
| Delivery Function `{baseName}-fn-delivery` | — | `Reader` | `Website Contributor` 4 h | `Website Contributor` | Function MI: `Storage Blob Data Contributor` (runtime + `deliverables`); Graph `Sites.Selected` write | `Reader` |
| Logic Apps Standard `{baseName}-la` | — | `Reader` | `Logic Apps Standard Developer` + `Operator` 8 h | `Logic Apps Standard Contributor` | Logic App MI: runtime storage Blob / Queue / Table Data Contributor; `Foundry User`; `Secrets User`; Graph `Sites.Selected` read (+ write under L12x) | `Logic Apps Standard Reader` / Operator (run history) |
| Storage `{baseName}sa` (`deliverables`) + Logic Apps runtime SA | — | — | `Storage Blob Data Reader` 4 h | `Storage Account Contributor` | Function MI: `Blob Data Contributor` (container scope); `allowSharedKeyAccess: false` where the runtime supports identity-based connections (D-B4) | — |
| Log Analytics `{baseName}-logs` + App Insights `{baseName}-appi` | — | `Log Analytics Reader` | `Monitoring Contributor` 4 h | `Monitoring Contributor` | project MI: `Monitoring Metrics Publisher` | `Log Analytics Reader` |
| Bing Grounding `{baseName}-bing` | via connection only | `Reader` | `Contributor` 2 h (key rotation — the single API key on the platform, imposed by the resource) | Bicep-managed | — | — |
| Container Apps (hosted MCP, optional) | Easy Auth allowed group | `Reader` | `Contributor` 4 h | `Contributor` | MI: `Foundry User` | — |

Roles deliberately not used: `Owner` / `User Access Administrator` on the
RG; `Foundry Account Owner` (bundles role assignment with data plane);
`Foundry Project Manager` for humans (role grants go through code);
`Cognitive Services Contributor` for humans (keys); storage account keys.
No human holds `RBAC Administrator`: every access change is a PR + review
+ deployment record (ISO 27001:2022 A.5.18, A.8.32; DORA Art. 9(4)(e)).

### 7.1 Foundry User vs Foundry Owner, and the agent-authoring gap

| Capability | Foundry User (five users) | Foundry Owner (owner, PIM) |
|---|---|---|
| Playground, run agents, threads, files, vector-store retrieval | yes | yes |
| Create / update / delete agents, vector stores | **built-in role currently includes these data actions** | yes |
| Connections, model deployments, RAI policies | no | yes |
| Role assignments | no | no (deploy SP only) |
| Sees other users' threads via SDK | yes (project-wide data plane) → §13 conventions | yes |

Because the built-in `Foundry User` allows agent authoring, "prompt /
registry changes are owner-only" needs both controls:

- **Preventive (preferred where tenant policy allows custom roles):**
  `custom-role.agent-consumer.json` — a copy of `Foundry User` with the
  agent create / update / delete data actions removed; operation strings
  confirmed from `az provider operation show --namespace
  Microsoft.CognitiveServices` at deployment (`{to-confirm}` markers).
  Assigned to `sg-infosec-foundry-users` via
  `agentConsumerRoleDefinitionId`; otherwise fall back to `Foundry User`.
- **Detective (always on):** `../deploy.sh` records the SHA-256 of each
  deployed agent's instructions and tool set in `build/manifest.json`; a
  daily Logic App (`../operations/` layer) re-reads live agents and raises
  `agent_modified_by_non_deploy_identity` on any hash mismatch;
  `deploy.sh` is idempotent by name and re-running it reverts drift (F6);
  quarterly hash compare is item 10 of the access review (§15).

Control: ISO 27001:2022 A.8.9 (configuration management), A.8.32 (change
management); ISO 42001 A.6.2.6; DORA Art. 9(4)(e).

## 8. Microsoft Graph application permissions (identity-scoped)

| Identity | Permission | Scope | Used by | Why not broader |
|---|---|---|---|---|
| Delivery Function MI `{mi:infosec-delivery-fn}` | `Sites.Selected` **write** | the one InfoSec Assurance site | `ensure_folder`, `upload`, `createLink` | `Sites.ReadWrite.All` reaches every site |
| Foundry project MI `{mi:infosecfoundry-proj}` | `Sites.Selected` **read** | same site | `sharepoint-graph` tools; TPA evidence tree | replaces `Sites.Read.All`; the spec's tenant-wide `/search/query` needs `Sites.Read.All` → prefer `/drives/{driveId}/root/search(q=)` scoped to the reports drive (delta D-I2); keeping `/search/query` = ledger row |
| Foundry project MI | `SecurityIncident.Read.All`, `SecurityAlert.Read.All`, `ThreatHunting.Read.All`, `SecurityEvents.Read.All` | tenant | `defender-graph` (GET only) | no ReadWrite |
| Foundry project MI | `User.Read.All`, `Group.Read.All`, `Application.Read.All`, `RoleManagement.Read.Directory`, `AccessReview.Read.All` | tenant | `entra-iam-graph` | matches the spec's read paths only |
| Logic App MI | `Sites.Selected` **read** (write only under L12x) | same site | `scheduled-deepsearch` watchlist list read | all writes go through the Function |
| Copilot connector | delegated (OBO) | — | Copilot Studio → Foundry | caller identity preserved |

Admin consent is granted by `{group:iam-admins}` and recorded in
`ACCESS_REGISTER.md`. `Sites.Selected` is granted to exactly three
application identities (Function write, project MI read, Logic App read).
No identity holds `Sites.Read.All` / `Sites.ReadWrite.All`. Control: ISO
27001:2022 A.8.3; DORA Art. 9(4)(c).

## 9. SharePoint site roles

Site `{sharepoint:infosec-assurance}` (`SHAREPOINT_SITE_ID` in
`../setup/.env`). Inheritance is broken only where report-of-record
integrity requires it; taxonomy per `../sharepoint/README.md`.

| Scope | Site Owners (Full Control) | `sg-…-users` (Members) | `sg-…-owner` | Visitors | App-only (`Sites.Selected`) |
|---|---|---|---|---|---|
| Site root | `sg-infosec-foundry-owner`, `{group:spo-admins}` (backup) | Edit | Site owner | `sg-…-readers` Read | — |
| `GRC/TPA/Active/<Supplier>[/<Service>]/` (evidence library, uploaded by hand) | inherit | **Edit** (pre-existing duty) | Edit | — | project MI read |
| `Reports/<Supplier>/<Service>/` (reports of record) | inherit | **unique: Read** — a correction is a new pipeline run; versioning keeps history | Contribute (no delete) | — | Function MI **write**; project MI read; Logic App MI read |
| `Reports/DPO/<Supplier>/<Service>/` | inherit | unique: Read | Contribute | `{group:dpo}` Read | Function MI write |
| `Templates/` and `Templates/Reviews/` (req. j) | inherit | unique: Read (proposals via `template-manager`) | Edit | — | Function MI write (`Reviews/`); project MI read |
| `Governance/` (access reviews, evaluation / cost minutes, onboarding attestations, approval decisions) | inherit | unique: Read | Edit | `sg-…-readers` Read | — |

Sharing links: organisation-scoped **view** links for `Reports/`; for
`Reports/DPO/` use `{"type":"view","scope":"users"}` with the DPO group as
recipient (delta D-F1), because that deliverable leaves the team.
Versioning on (≥ 50 major versions); sensitivity label
`{label:confidential-internal}`; SharePoint audit log retained ≥ 1 year.
Control: ISO 27001:2022 A.5.12, A.8.3; DORA Art. 28 (evidence).

## 10. Foundry project connections — ownership and custody

Preference order: managed identity → app registration with federated
credential → service-account token in Key Vault (only where the SaaS
offers nothing else). All project-scoped (`isSharedToAll: false`) except
`bing-grounding` and `app-insights`. Every connection has a Foundry-side
owner and a target-side custodian; **two people are needed to change what
an agent can reach** (ISO 27001:2022 A.5.3).

| Connection | Identity type | Identity | Target-side role (read-only) | Custodian | KV secret | Rotation |
|---|---|---|---|---|---|---|
| `conn-sharepoint-graph`, `conn-defender-graph`, `conn-entra-iam-graph` | project **managed identity** (audience `https://graph.microsoft.com`) | `{mi:infosecfoundry-proj}` | §8 | `{group:iam-admins}` (consent) | none | n/a |
| `conn-jira-cloud`, `conn-jira-assets` | service-account API token | `{svc:infosec-foundry-ro-jira}` | browse / JQL; Assets schema viewer | `{group:jira-admins}` | `kv-jira-ro-token` | 180 d |
| `conn-confluence` | service-account API token | `{svc:infosec-foundry-ro-confluence}` | space read | Confluence admin | `kv-confluence-ro-token` | 180 d |
| `conn-onetrust` | service-account API token | `{svc:infosec-foundry-ro-onetrust}` | Viewer, assessment read | `{group:onetrust-admins}` | `kv-onetrust-ro-token` | 180 d |
| `conn-securityscorecard` | API token | `{svc:infosec-foundry-ro-ssc}` | portfolio read | SSC admin | `kv-ssc-ro-token` | 180 d |
| `conn-iaf-api` | app registration with federated credential to the project MI (preferred) else token | `{app:infosec-foundry-iaf-ro}` | findings read | `{upn:iaf-owner}` | `kv-iaf-ro-token` only if token | 180 d if token |
| `enx-gateway-mcp` (`../integrations/mcp/enx-gateway.json`) | bearer token from KV (Entra if the gateway supports it) | `{svc:infosec-foundry-ro-enxgw}` | read-only toolset (allowlist in the json) | `{group:enx-gateway}` | `kv-enx-gateway-token` | **90 d** (gateway policy) |
| `bing-grounding` | Bing resource key (platform constraint) | — | public web only, after query sanitisation | owner | Bicep-wired | 180 d |
| `app-insights` | connection string (Bicep-wired) | — | telemetry write | owner | — | workspace rebuild |
| `write_connections` (registry) | **none for every agent** | — | — | — | — | any grant = Tier C PR |

Rules: tokens are written to Key Vault by the custodian or the owner during
a PIM window and referenced by name; a secret past its rotation date fails
the quarterly review and the connection is disabled until rotated; migrate
to federated identity at the next rotation wherever the SaaS supports it;
Euronext's credential policy prevails where stricter than the periods
above. Scope changes are Tier C. Control: ISO 27001:2022 A.5.17, A.5.19 /
A.5.20; DORA Art. 28–30 (ICT third-party register); ISO 42001 A.10.3.

## 11. Copilot Studio, MCP, GitHub

| Surface | Users | Owner | Controls |
|---|---|---|---|
| Copilot Studio (`../integrations/copilot/README.md`) | consume the agent published to `sg-infosec-foundry-users` only | Environment Maker in `{env:infosec-foundry}`; Power Platform admins hold Environment Admin | delegated (OBO) auth; DLP allows only the Foundry HTTP connector |
| MCP local (`../mcp-server/server.py`) — default for the five | own `az login` (`DefaultAzureCredential`); access = own project role; CA applies to the token | — | server stamps `owner_upn` into thread metadata; group removal revokes; `PROJECT_ENDPOINT` is not a secret |
| MCP hosted (Container Apps, EU) — only if the ENX gateway or shared tooling needs it | Easy Auth allowed group `sg-infosec-foundry-users` | MI `Foundry User` | `X-MS-CLIENT-PRINCIPAL-NAME` copied into thread metadata; `save_memory` records the caller |
| MCP **clients** | only clients on the approved AI-tooling register `{register:approved-ai-clients}` in `ACCESS_REGISTER.md` (internal tooling and the ENX gateway by default; third-party desktop clients only under a Euronext-approved agreement — DPA, EU processing) | owner maintains the register | a client's model provider receives Euronext data: A.5.19 / A.5.20, GDPR Art. 28 |
| GitHub `{github:org/repo}` | `Read` (team `infosec-assurance-users`) | `Maintain` + CODEOWNERS; deputy `Write` for reviews | branch protection: 1 CODEOWNERS review, no self-approval; OIDC federated credential bound to environment `production`; environment approval by owner; secret scanning + push protection |

## 12. Approval routing

Every submission of record already passes verifier → `HttpWebhook` gate
(`../governance/HUMAN_APPROVAL.md` Layer 3; mechanics in
`../workflows/README.md`). `approval-policy.json` fixes **who** may answer
the gate; the approval flow behind `approvalWebhookUrl` (Power Automate or
Function) must enforce: approver's token UPN ∈ the tier's group (Graph
`checkMemberGroups`); approver ≠ `requestedBy` (token claim); decision
stored before the callback.

### 12.1 Tiers

| Tier | Kind (subscribe body) → pipelines | Who may approve | Rationale |
|---|---|---|---|
| **A — peer four-eyes** | `REPORT_DELIVERY` with `reportType` ∈ {`DeepSearch` (a), `EvidenceAnalysis` (d2), `SOCSummary` (e), `PentestSummary` (f)} → `deepsearch-report`, `scheduled-deepsearch`, `tpa-evidence-analysis`, `soc-report-summary`, `pentest-report-summary`; `JIRA_CREATE` → `defender-incident-brief`, `scheduled-deepsearch`; `IAF_SUBMIT` → `jira-finding-sync` | any `sg-…-report-approvers` member ≠ requester; scheduled runs (no human requester) → any report approver | anything written to `Reports/` or a register of record is a record; peer review is the quality control (EU AI Act Art. 14; A.5.3) |
| **B — senior four-eyes** | `REPORT_DELIVERY` with `reportType` ∈ {`InfoSecTPA-DPO` (b), `CyberForum` (c), `CISOGlobal` (d)} → `dpia-dpo-report`, `onetrust-assessment-intake`, `cyber-forum-pptx`, `ciso-global-pptx` | `sg-…-senior-approvers` (owner or deputy) ≠ requester; owner's request → deputy, deputy's → owner; if both unavailable > 2 business days → any Tier A approver with the owner notified (logged exception, `ruleId` recorded) | these leave the team (DPO, CISOs, contract owners): the accountable owner or deputy signs what carries the team's name |
| **C — owner-only** | `TEMPLATE_UPDATE` (j) → `template-update-approval`; `PLATFORM_CHANGE` → GitHub PR + `production` environment; `MEMORY_DELETE` (note not authored by the requester) | owner; **if the requester / author is the owner → deputy approves** (template: after visual diff review; PR: required CODEOWNERS review, owner merges and approves deployment as accountable); privileged-group membership → line manager | configuration of record; SoD (A.5.3; DORA Art. 9(4)(e)) |
| never auto-approved | all of the above | — | break-glass grants access, never approval; an expired gate (P3D reports, P7D templates / memory) is a rejection — the requester re-runs |

Platform change scope: Bicep, `../integrations/registry.json` (tools,
tiers, `write_connections`), `../templates/registry.json`, OpenAPI specs,
workflows, agent instructions / persona / knowledge packs, `../scripts/`,
Graph consents, KV scope, connection scope, Copilot publication, CA / PIM
settings, ledger rows (§5). A model-tier change is a platform change
(`../governance/MODEL_ROUTING.md` rule 7).

Decision record (kept ≥ 1 year, DORA Art. 28; filed under
`Governance/Approvals/`): `kind, reportType, tier, ruleId, correlationId,
requestedBy, approver, approverObjectId, reviewedBy, decision, timestamp,
reportPath`.

Quality sampling: each quarter the owner samples 10 % of Tier A approvals
and 100 % of Tier B fallbacks against the stored deliverable (review item
12). Control: EU AI Act Art. 14, 26(2); ISO 42001 A.9.2; ISO 27001:2022
A.8.15.

### 12.2 Segregation of duties for the owner

| Situation | Approver / control |
|---|---|
| Owner requests a Tier A report | any peer (requester exclusion) |
| Owner requests a Tier B report | deputy |
| Owner proposes a template change | deputy |
| Owner opens a platform PR | deputy reviews (required, no self-approval); owner merges and approves `production` as accountable |
| Owner rotates a credential | owner executes; deputy verifies ticket ↔ KV secret version at the quarterly sample |
| Owner deletes another's memory note | note author; else deputy via `MEMORY_DELETE` |
| Owner activates PIM | self, with justification; `Contributor` needs line-manager approval; monthly PIM report to line manager |
| Owner adds himself to a privileged group | impossible — `-owner`, `-senior-approvers`, `-admin-pim`, `-breakglass` are owned by the line manager |
| One person controls both sides of an integration | Foundry side = owner; target credential = custodian |
| Human bypasses the gate and writes directly | only the Function MI (and, until L12x expires, the Logic App MI) can write to `Reports/`; humans hold Read; agents hold GET-only tools |
| Deployer identity used interactively | federated credential only, bound to the `production` environment |

Control: ISO 27001:2022 A.5.3; DORA Art. 5(2), 9(4)(e); NIS2 Art. 20.

### 12.3 Break-glass

Runbook: `../operations/access-governance/BREAK_GLASS.md`. Trigger: owner
unavailable > 2 business days with a pending Tier C item, or a P1 / P2
platform incident. The deputy activates `sg-infosec-foundry-breakglass`
(PIM, 8 h, MFA, ticket) with approval from `{upn:line-manager}` or
`{group:soc-oncall}`; may *disable* (workflow, connection, agent tool,
secret) freely; may *change* only with the owner's retrospective approval;
**never approves anything**. Detective alerts on ARM writes, agent edits
and KV `SecretGet` during the window; owner post-review ≤ 5 business days;
every activation is an entry in `ACCESS_REGISTER.md`. Control: ISO
27001:2022 A.8.2, A.5.24–A.5.26; DORA Art. 9(4)(c), 11, 17.

## 13. Conversations and memory

(The runtime object is a Foundry **conversation**; classic threads/runs retire
2027-03-31 — finding C1. "Thread" below is kept only where a tool still spells it
that way.)

| Topic | Convention |
|---|---|
| Conversation ownership | one conversation per (person, supplier, service, engagement / month); metadata `{owner_upn, supplier, service, system, engagement, classification:"internal", created}` set by the MCP server / Copilot connector / pipeline; playground threads named `<initials>/<Supplier>/<Service>/<yyyy-mm>` |
| Visibility | conversations are **team-visible** (project data plane); treat every thread as a shared working paper; a colleague may read a thread to take over an engagement |
| Personal data | none beyond business role names already in the source; supplier contacts as role + company |
| Uploads / retention | only the file the run needs; conversation files deleted after approval when the source lives in SharePoint; conversations deleted 90 days after their deliverable is approved and stored, and at 180 days of inactivity otherwise; the report, its Logic Apps run and the App Insights trace (≥ 1 year) are the record |
| **How the 90 days is enforced (finding C5)** | With the standard agent setup (`../infra/agent-stores.bicep`) conversations and run state live in `{baseName}-cosmos` **in this subscription**, not in Microsoft-managed storage. Retention is therefore a **database policy, not a script**: the default TTL on the `run-state-v1` container of the `{project-workspace-id}-thread-message-store` database is set once, after the capability host has created its containers — `az cosmosdb sql container update … --ttl 7776000` (= `conversationRetentionDays × 86400`) — and the value is evidenced at the quarterly access review (item 12). Deleting a single conversation through the API remains the per-user path. |
| Shared memory (`vs-assurance-memory`) | note = `YYYY-MM-DD \| <Supplier> \| <Service or -> \| decision/fact/position/follow-up \| <text> \| by {upn} \| review <YYYY-Qn>`; any user adds under own identity (the human act is the approval — `HUMAN_APPROVAL.md` scope notes); author deletes own; owner deletes any via recorded `MEMORY_DELETE`; quarterly prune by the owner; retention: supplier facts until exit + 1 year, decisions 5 years or 24 months where no decision is attached; RoPA entry owned by the owner, DPO informed (GDPR Art. 5(1)(c)) |
| Never in memory | special-category data; personal data beyond role / company; credentials; hostnames / IPs; verbatim contract or supplier-document text; personal reminders |
| Personal notes | **no personal store** on the platform (no per-user vector store, no personal memory — nothing to purge at offboarding, no per-user profiling); use OneNote / OneDrive or a `personal-working` thread deleted by its owner |
| Attribution in telemetry | `owner_upn` flows to App Insights as a custom dimension for cost / capacity tuning only, not individual performance |

Control: ISO 27001:2022 A.5.12, A.5.34, A.8.10; GDPR Art. 5(1)(c), (e);
ISO 42001 A.7.2–A.7.4 (data for AI systems), A.9.2.

## 14. Joiner / mover / leaver

Runbook: `../operations/access-governance/ACCESS_LIFECYCLE.md`.

| Event | Steps (who) | Evidence |
|---|---|---|
| Joiner | line manager requests `AP-InfoSec-Foundry-User` → owner approves → `sg-…-users` (one act grants Foundry, SharePoint, Copilot, MCP, CA scope) → owner adds GitHub team + Teams channels `{teams:infosec-assurance-platform}`, `{teams:infosec-assurance-approvals}` → joiner reads `../governance/*.md`, `../sharepoint/README.md`, this file, runs local MCP with `az login`, completes one Tier A report end-to-end with a peer approving → **onboarding attestation** (EU AI Act Art. 26(2) competence) → owner adds to `-report-approvers` → register row + snapshot | `Governance/Onboarding/` |
| Mover (deputy change) | owner nominates, line manager confirms; IAM team updates `-senior-approvers` and `-breakglass` eligibility; PR updates `least-privilege/entra/groups.json`, `approval-policy.json`, CODEOWNERS | PR + register |
| Leaver | same-day removal from every `sg-infosec-foundry-*` group (HR / IAM trigger or line manager) → revoke sessions → owner removes GitHub / Teams → re-tag (`owner_upn` → new engagement owner) or delete active threads → shared memory notes stay (team facts) → rotate KV secrets only if the leaver held a break-glass / PIM window in the last 90 days → snapshot | register + snapshot |
| Owner succession | line manager appoints the successor (normally the deputy): transfer group ownership of the user-facing groups, `-owner` / `-admin-pim` membership, SharePoint site ownership, Copilot maker, GitHub maintain, custodianship rows and the RoPA entry; successor runs `deploy.sh --dry-run`, `provision_identity.sh --verify` and `access-review.sh` as the hand-over check | hand-over checklist |

Control: ISO 27001:2022 A.5.16, A.5.18, A.6.1, A.6.5; DORA Art. 9(4)(c);
NIS2 Art. 21(2)(i).

## 15. Quarterly access review

Runbook: `../operations/access-governance/QUARTERLY_ACCESS_REVIEW.md`.
First week of each quarter; owner reviews `-users`, `-report-approvers`,
`-readers`; **line manager reviews `-owner`, `-senior-approvers`,
`-admin-pim`, `-breakglass`**; evidence
`Governance/AccessReviews/{yyyy}-Q{n}/` (5 years); collectors
`access-review.sh` / `../operations/access-governance/scripts/access_snapshot.sh`
(read-only).

| # | Item | Source | Pass criterion |
|---|---|---|---|
| 1 | Group memberships | Entra access review + snapshot | each member still in the team; no unexpected identity |
| 2 | Azure role assignments in the RG | `az role assignment list` | matches `rbac.bicep` exactly; no standing privileged role on a human |
| 3 | PIM / break-glass activations | PIM audit log | ticket + justification on every activation; break-glass ones reviewed by the owner |
| 4 | SharePoint permissions + `Sites.Selected` grants | site permissions report; Graph `/sites/{id}/permissions` | only §9 groups; exactly three app grants with the roles in §8 |
| 5 | Graph app permissions on the project MI and Logic App MI | enterprise apps | read-only set of §8 only |
| 6 | Connections and secret ages | Management center + KV versions + register | all within rotation date; `write_connections` empty |
| 7 | Conditional Access policy | Entra | unchanged, enabled |
| 8 | GitHub | settings | owner Maintain, users Read, CODEOWNERS = owner + deputy, protections on |
| 9 | Copilot Studio sharing | Copilot Studio | shared with `-users` only; delegated auth |
| 10 | Agent drift | drift alert history + hash compare | no unexplained drift |
| 11 | Memory store and old threads | `memory_store.py list`; thread listing | notes conform to §13; retention applied |
| 12 | Approval sampling | decision records | 10 % Tier A + all Tier B fallbacks match the stored deliverable |
| 13 | Ledger re-confirmation | §5 | every row re-justified or removed |
| 14 | Approved MCP clients | register | list current; no unapproved client in traces |
| 15 | Sign-off | template in runbook | owner + line manager signatures filed |

Control: ISO 27001:2022 A.5.18, A.5.35, A.8.2; DORA Art. 9(4)(c); NIS2
Art. 21(2)(i); EU AI Act Art. 26(6).

## 16. RACI

The full matrix is `RACI.md`: §2 names the five people individually
(FGG, JMo, PSa, JMe, TMo) with the deputy as an overlay column and the
line manager; §3 adds the external parties (LZ, CUST, M365, DPO, AUD,
SOC) per activity id R1–R38 across create / plan / run / maintain /
optimise / govern; §4 maps each activity group to ISO 27001:2022, DORA
and ISO 42001 / EU AI Act. One Accountable per row; the owner is A for
every lifecycle activity except the review of his own privileged access
(R32) and break-glass approval (R26) — line manager —, deputy nomination /
owner succession (R34) — line manager — and the GDPR Art. 33 notification
path (R36) — DPO. Changes to the matrix are Tier C.

## 17. Compliance mapping

| Control / article | Implemented by |
|---|---|
| ISO 27001:2022 A.5.2, A.5.3 | roles §1; owner SoD §12.2; privileged groups owned by the line manager §6; two-person integration custody §10 |
| A.5.15, A.5.16, A.5.18, A.6.5 | group-only assignments, access packages, JML §14, quarterly review §15 |
| A.5.17 | KV secret versions as rotation evidence; no human-held keys; OIDC for the deployer |
| A.5.19 / A.5.20 | approved MCP-client register §11; connection custodians §10 |
| A.5.35 | readers group; line-manager review of the owner's access |
| A.8.2, A.8.5 | PIM eligibilities §6–§7; CA MFA + compliant device |
| A.8.3 | SharePoint unique permissions §9; `Sites.Selected` §8 |
| A.8.9, A.8.32 | RBAC-as-code, drift detection §7.1, Tier C change control §12 |
| A.8.15, A.8.16 | approval decision records, PIM logs, drift alerts, access snapshots |
| DORA Art. 5(2), 9(4)(c)–(e), 11, 17, 28 | accountable owner; access management, strong auth, change control; deputy continuity and break-glass; evidence ≥ 1 year |
| NIS2 Art. 20, 21(2)(i)–(j) | management accountability; access-control policy; MFA |
| ISO 42001 A.3.2, A.6.2.6, A.7.2–A.7.4, A.9.2, A.10.3 | RACI; monitoring / evaluation duties; data conventions §13; responsible use; supplier / custodian register §10 |
| EU AI Act Art. 12, 14, 26(2), 26(6) | approval tiers §12; onboarding attestation of approver competence §14; logs retained |
| GDPR Art. 5(1)(c), 28, 33 | memory minimisation §13; approved-client agreements §11; DPO breach path (`RACI.md`) |

## 18. Bootstrap order (first deployment)

1. LZ / IAM team creates the seven groups (§6), CA policy, PIM policies,
   deploy SP `{app:infosec-foundry-deployer}` with a federated credential
   for `{github:org/repo}` environment `production`, and grants admin
   consent for the Graph permissions in §8.
2. Owner (PIM `Contributor`) runs `../setup/provision.sh`;
   `least-privilege/scripts/provision_identity.sh --plan` then `--apply`;
   deploys `rbac.bicep` with the group object ids
   (`rbac.parameters.example.json`, `enablePim` per licence).
3. Owner grants `Sites.Selected` to the three app identities (§8) and
   configures the site permissions of §9.
4. Custodians place service-account tokens in Key Vault; owner creates the
   `conn-*` connections referencing them by name.
5. Owner runs `../deploy.sh`; the agent drift baseline
   (`build/manifest.json`) is recorded.
6. Owner runs `access-review.sh` / `access_snapshot.sh` and files the
   output as the Q0 baseline in `Governance/AccessReviews/`.

## 19. Verify before first deployment

| Check | Command / source |
|---|---|
| Built-in role GUIDs in `rbac.bicep` | `az role definition list --query "[].{n:roleName,id:name}"` — `rbac.bicep` and `least-privilege/infra/rbac.bicep` both carry `Foundry User` = `53ca6127-db72-4b80-b1b0-d229d5fc3ae7` (the published built-in id); confirm every GUID of `var roles` with the command before the first `what-if`, as built-in ids are tenant-independent but preview roles (`Foundry User`, `Foundry Owner`) have been re-published |
| `Foundry User` data actions include agent authoring? | `az role definition list --name "Foundry User" --query "[].permissions[].dataActions"` → decide custom role vs detective-only |
| Custom-role operation strings | `az provider operation show --namespace Microsoft.CognitiveServices` |
| PIM API availability (`roleEligibilityScheduleRequests`) and Entra ID P2 licence | tenant admin; else `enablePim=false` |
| `Sites.Selected` support for the `sharepoint-graph` spec's `/search/query` | test with the project MI; apply delta D-I2 |
| Logic Apps Standard OAuth authorization policy on Request triggers (token claim for `requestedBy`) | delta D-W1 |
| Bicep compile | `bicep build rbac.bicep` passes (Bicep CLI 0.47; only BCP081 for `Microsoft.Bing/accounts`, whose types are not published — not blocking); still run `az deployment group what-if` on `rbac.bicep` before the first deployment |

## 20. Shared deltas (literal text — applied by the kit maintainer, not here)

Deltas to files outside `team/` and `operations/`. Ids are stable so
`ACCESS_REGISTER.md` and PRs can cite them. Rows marked **applied** target
files inside `team/` or `operations/` and are already in force in this
folder set (kept for traceability; the literal text now lives in the
target file).

| Id | Target | Location | Literal text |
|---|---|---|---|
| D-R1 | `README.md` | folder layout tree | `├── team/                      ← team model (TEAM_MODEL.md, RACI.md), Entra groups, RBAC-as-code (rbac.bicep), approval routing, access register` and `├── operations/                ← runbooks: access lifecycle, quarterly access review, break-glass (access-governance/)` |
| D-R2 | `README.md` | "What gets created in Azure" | `- Role assignments and PIM eligibilities for the sg-infosec-foundry-* groups and the workload managed identities (team/rbac.bicep; model: team/TEAM_MODEL.md)` |
| D-Q1 | `REQUIREMENTS.md` | after the "Invocation summary" table | `Who may run, approve and change each system (five assurance users with the identical persona, one accountable owner, approval tiers A/B/C): team/TEAM_MODEL.md §4 and §12; responsibilities per lifecycle activity: team/RACI.md.` |
| D-B1 | `infra/main.bicep` | params after `enableWebSearch` | `@description('Object id of sg-infosec-foundry-users') param usersGroupObjectId string = ''` / `@description('Object id of sg-infosec-foundry-owner') param ownerGroupObjectId string = ''` / `@description('Object id of sg-infosec-foundry-admin-pim') param pimGroupObjectId string = ''` / `@description('Object id of sg-infosec-foundry-breakglass') param breakglassGroupObjectId string = ''` / `@description('Object id of sg-infosec-foundry-readers') param readersGroupObjectId string = ''` / `@description('Object id of the deploy service principal') param deployerPrincipalId string = ''` / `@description('Principal id of the Logic Apps managed identity') param logicAppPrincipalId string = ''` / `@description('Principal id of the delivery Function managed identity') param deliveryFunctionPrincipalId string = ''` / `@description('Optional custom role definition id for assurance users (agent consumer)') param agentConsumerRoleDefinitionId string = ''` / `@description('Use PIM eligibilities for privileged human roles (requires Entra ID P2)') param enablePim bool = true` / `@description('Deploy the team RBAC module') param deployTeamRbac bool = false` |
| D-B2 | `infra/main.bicep` | before outputs | `resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = { name: '${baseName}-kv' location: location properties: { tenantId: subscription().tenantId sku: { family: 'A', name: 'standard' } enableRbacAuthorization: true enableSoftDelete: true enablePurgeProtection: true publicNetworkAccess: 'Enabled' // harden with a private endpoint for production } }` |
| D-B3 | `infra/main.bicep` | after Key Vault | `module teamRbac '../team/rbac.bicep' = if (deployTeamRbac) { name: 'team-rbac' params: { foundryAccountName: foundry.name projectName: project.name logAnalyticsName: logAnalytics.name appInsightsName: appInsights.name storageAccountName: storage.name keyVaultName: keyVault.name usersGroupObjectId: usersGroupObjectId ownerGroupObjectId: ownerGroupObjectId pimGroupObjectId: pimGroupObjectId breakglassGroupObjectId: breakglassGroupObjectId readersGroupObjectId: readersGroupObjectId deployerPrincipalId: deployerPrincipalId logicAppPrincipalId: logicAppPrincipalId deliveryFunctionPrincipalId: deliveryFunctionPrincipalId agentConsumerRoleDefinitionId: agentConsumerRoleDefinitionId enablePim: enablePim } }` |
| D-B4 | `infra/main.bicep` | storage `properties` | `allowSharedKeyAccess: false` |
| D-B5 | `infra/main.bicep` | outputs | `output keyVaultName string = keyVault.name` |
| D-B6 | `infra/main.parameters.json` | parameters | `"deployTeamRbac": { "value": false }, "enablePim": { "value": true }, "usersGroupObjectId": { "value": "{objectId:sg-infosec-foundry-users}" }, "ownerGroupObjectId": { "value": "{objectId:sg-infosec-foundry-owner}" }, "pimGroupObjectId": { "value": "{objectId:sg-infosec-foundry-admin-pim}" }, "breakglassGroupObjectId": { "value": "{objectId:sg-infosec-foundry-breakglass}" }, "readersGroupObjectId": { "value": "{objectId:sg-infosec-foundry-readers}" }, "deployerPrincipalId": { "value": "{objectId:infosec-foundry-deployer}" }` |
| D-T1 | `team/rbac.bicep` | `var roles` + owner block + new params | **applied** — `rbac.bicep` carries `azureAiUser: '53ca6127-db72-4b80-b1b0-d229d5fc3ae7'` (same as `least-privilege/infra/rbac.bicep`), the role set below, `breakglassGroupObjectId`, `enablePim`, `keyVaultSecretNames` (Secrets User scoped to named secrets), no standing `Foundry Owner` / `Foundry Project Manager` on `-owner`, `pim*` / `perm*` / `bg*` resource pairs. Original text: add `keyVaultSecretsOfficer: 'b86a8fe4-44ce-4948-aee5-eccb2c155cd7'`, `storageBlobDataReader: '2a2b9908-6ea1-4ae2-8e65-a410df84e7d1'`, `monitoringContributor: '749f88d5-cbae-40b8-bcfc-e573ddc772fa'`, `websiteContributor: 'de139f84-1756-47ae-9be6-808fbbe84772'`, `logicAppsStandardDeveloper: '523776ba-4eb2-4600-a3c8-f2dc93da4bdb'`, `logicAppsStandardOperator: 'b70c96e9-66fe-4c09-b6e7-c98e69c98555'`; add `@description('Object id of sg-infosec-foundry-breakglass') param breakglassGroupObjectId string = ''` and `@description('PIM eligibilities for privileged human roles (Entra ID P2); false = permanent assignment to ownerGroupObjectId, recorded as an exception in ACCESS_REGISTER.md') param enablePim bool = true`; **remove** `ownerAccount` (Foundry Owner) and `ownerProject` (Foundry Project Manager) standing assignments; add, per role in {contributor (RG), azureAiDeveloper (account), keyVaultSecretsOfficer (KV), monitoringContributor (workspace), storageBlobDataReader (deliverables), websiteContributor (Function), logicAppsStandardDeveloper + Operator (Logic App)}, the pair from `team/least-privilege/infra/rbac.bicep` lines 194–300: `resource pim<Role> 'Microsoft.Authorization/roleEligibilityScheduleRequests@2022-04-01-preview' = if (enablePim) { name: guid(<scope>.id, pimGroupObjectId, roles.<role>, 'pim') scope: <scope> properties: { principalId: pimGroupObjectId roleDefinitionId: roleId(roles.<role>) requestType: 'AdminAssign' justification: 'TEAM_MODEL.md §5 ledger row' scheduleInfo: { startDateTime: pimStartDateTime, expiration: { type: 'AfterDuration', duration: pimEligibilityDuration } } } }` and `resource perm<Role> 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!enablePim) { … principalId: ownerGroupObjectId … }`, plus the same `pim<Role>` set for `breakglassGroupObjectId` when non-empty (no RBAC Administrator); add `param pimEligibilityDuration string = 'P365D'` and `param pimStartDateTime string = utcNow('yyyy-MM-ddTHH:mm:ssZ')` |
| D-T2 | `team/approval-policy.json` | `kinds`, tier C, `record.fields` | **applied** (extended to every `reportType` in `../workflows/pipelines.json`: `AIDeepSearch`, `ThreatIntelBrief`, `Transcript`, `Advisory` → A; `CISOExecSummary` → B; `TEAMS_POST` → A; `principals` block for the flow). Original text: replace the seven `REPORT_*` kinds with `"REPORT_DELIVERY": { "tier_by_reportType": { "DeepSearch": "A", "EvidenceAnalysis": "A", "SOCSummary": "A", "PentestSummary": "A", "InfoSecTPA-DPO": "B", "CyberForum": "B", "CISOGlobal": "B" }, "pipelines": ["deepsearch-report", "scheduled-deepsearch", "tpa-evidence-analysis", "soc-report-summary", "pentest-report-summary", "dpia-dpo-report", "onetrust-assessment-intake", "cyber-forum-pptx", "ciso-global-pptx"] }`; add `"MEMORY_DELETE": { "tier": "C", "requirement": "-", "pipelines": ["scripts/memory_store.py delete"] }`; in tier C set `"self_approval": false, "requester_is_owner_fallback": { "approver_groups": ["senior_approvers"], "exclude": ["requestedBy"], "ruleId": "tierC-owner-item-deputy-approves" }` and drop `self_approval_compensating_control`; in tier B fallback add `"ruleId": "tierB-fallback-peer-after-2bd"`; `record.fields` → `["kind", "reportType", "tier", "ruleId", "correlationId", "requestedBy", "approver", "approverObjectId", "reviewedBy", "decision", "timestamp", "reportPath"]`; `_comment` → reference `team/TEAM_MODEL.md §12` |
| D-T3 | `team/least-privilege/entra/groups.json` | `groups[]` | **applied** (also: deployer renamed `{app:infosec-foundry-deployer}`, IAM team `{group:iam-admins}`, CA policy `CA-InfoSec-Foundry`, `-admin-pim` uses `eligibleMembers`). Original text: rename `sg-infosec-foundry-platform-approvers` → `sg-infosec-foundry-senior-approvers`, `sg-infosec-foundry-platform-admins` → `sg-infosec-foundry-admin-pim` (members → `eligibleMembers`), `sg-infosec-foundry-auditors` → `sg-infosec-foundry-readers`; add `{ "name": "sg-infosec-foundry-owner", "purpose": "standing low-privilege owner roles (Reader RG, Log Analytics Reader, SharePoint site owner, Copilot maker, GitHub Maintain)", "owners": ["{upn:line-manager}"], "members": ["{upn:francisco.gomes}"], "accessReview": { "cadence": "quarterly", "reviewer": "{upn:line-manager}" } }`; set `owners` of `-senior-approvers`, `-admin-pim`, `-breakglass` to `["{upn:line-manager}"]` (executed by `{group:iam-admins}`); `_comment` → `team/TEAM_MODEL.md §6` |
| D-T4 | `team/README.md` | top of file | **applied**. Original text: replace the intro with `Superseded: the authoritative model is TEAM_MODEL.md (identity, RBAC, approvals, threads/memory, access review) and RACI.md; this file is retained for its companion-file table until the §20 deltas of TEAM_MODEL.md are applied.` |
| D-T5 | `team/ACCESS_REGISTER.md` | header + Groups/People | **applied** (plus deployer roles per L11, SSC rotation 180 d, `-agents-read` marked not granted by default). Original text: replace `(\`team/README.md\` §11)` with `(\`team/TEAM_MODEL.md\` §15)`; Deputy row UPN `{upn:deputy}` → `{upn:deputy-approver}`; add row under Non-human identities: `| Logic Apps MI Sites.Selected write (L12x) | time-boxed exception | onetrust-assessment-intake, scheduled-deepsearch direct uploads | Sites.Selected write | owner | expires on delta D-W3 | {date} |`; add section `## PIM fallback exception` with `| enablePim=false in force? | {yes/no} | review date {date} | approved by {upn:line-manager} |` |
| D-E1 | `setup/.env.example` | end | `# --- Team / identity (team/TEAM_MODEL.md) ---` / `KEY_VAULT_NAME=<baseName>-kv` / `ENTRA_GROUP_USERS_OBJECT_ID={objectId:sg-infosec-foundry-users}` / `ENTRA_GROUP_REPORT_APPROVERS_OBJECT_ID={objectId:sg-infosec-foundry-report-approvers}` / `ENTRA_GROUP_SENIOR_APPROVERS_OBJECT_ID={objectId:sg-infosec-foundry-senior-approvers}` / `ENTRA_GROUP_OWNER_OBJECT_ID={objectId:sg-infosec-foundry-owner}` / `ENTRA_GROUP_ADMIN_PIM_OBJECT_ID={objectId:sg-infosec-foundry-admin-pim}` / `PLATFORM_OWNER_UPN={upn:francisco.gomes}` / `DEPUTY_APPROVER_UPN={upn:deputy-approver}` / `APPROVAL_POLICY_PATH=../team/approval-policy.json` |
| D-S1 | `setup/provision.sh` | final echo block | replace the self-grant hint with `echo ">> Assign roles by group, not by user: deploy ../team/rbac.bicep with the group object ids (team/TEAM_MODEL.md §7)"` |
| D-D1 | `deploy.sh` | before `if [ -z "$DRY" ]; then` | `echo "==> [6d/7] Identity model check (read-only)"` / `../team/least-privilege/scripts/provision_identity.sh --verify && ../team/access-review.sh --quick \|\| echo "note: identity drift detected - see team/TEAM_MODEL.md §15"` |
| D-G1 | `integrations/registry.json` | `_comment` append | ` Connection ownership, identity type, custodians and rotation: team/TEAM_MODEL.md §10 and team/ACCESS_REGISTER.md. Graph-backed connections (defender-graph, sharepoint-graph, entra-iam-graph) authenticate with the Foundry project managed identity; sharepoint-graph uses Sites.Selected (read) on the InfoSec Assurance site.` |
| D-I1 | `integrations/README.md` | Authentication | replace `(\`SecurityIncident.Read.All\`, \`ThreatHunting.Read.All\`, \`Sites.ReadWrite.All\` as applicable)` with `granted to the Foundry project managed identity: \`SecurityIncident.Read.All\`, \`SecurityAlert.Read.All\`, \`ThreatHunting.Read.All\`, \`SecurityEvents.Read.All\`, \`User.Read.All\`, \`Group.Read.All\`, \`Application.Read.All\`, \`RoleManagement.Read.Directory\`, \`AccessReview.Read.All\`, \`Sites.Selected\` (read) — no client secrets (team/TEAM_MODEL.md §8)` |
| D-I2 | `integrations/openapi/sharepoint-graph.yaml` | header line 9 | replace `Sites.Read.All (read)` with `Sites.Selected (read grant on the InfoSec Assurance site; tenant-wide /search/query would require Sites.Read.All - prefer /drives/{driveId}/root/search(q='...') scoped to the reports drive)` |
| D-H1 | `governance/HUMAN_APPROVAL.md` | end of Layer 3 | `Who may answer each gate is defined in ../team/TEAM_MODEL.md §12 and enforced from ../team/approval-policy.json: Tier A peer four-eyes (approver ≠ requester) for internal reports and records of record, Tier B senior four-eyes (owner or deputy) for reports that leave the team, Tier C owner-only for template/platform changes with the deputy approving the owner's own items.` |
| D-P1 | `governance/DATA_PROTECTION_GUARDRAILS.md` | §2 service-accounts bullet | replace `Graph \`Sites.Read.All\`` with `Graph \`Sites.Selected\` (read grant on the one InfoSec Assurance site, held by the Foundry project managed identity)`; append bullet `- Identity, RBAC and approval model: ../team/TEAM_MODEL.md; responsibilities: ../team/RACI.md; runbooks in ../operations/access-governance/.` |
| D-M1 | `governance/MODEL_ROUTING.md` | rule 7 append | `A tier change is a platform change: owner approval, deputy review when the owner proposes it (team/TEAM_MODEL.md §12, Tier C).` |
| D-W1 | `workflows/README.md` | Authentication, Graph bullet | replace `(\`Sites.ReadWrite.All\` or Sites.Selected)` with `(\`Sites.Selected\` read on the InfoSec Assurance site for list reads; all uploads go through the delivery Function, which holds the only write grant — team/TEAM_MODEL.md §8)`; add under Human approval gates: `The approval side enforces team/approval-policy.json: approver ∈ tier group (Graph checkMemberGroups), approver ≠ requestedBy, decision recorded with UPN/timestamp/correlationId/ruleId before the callback. Enable the Logic Apps Standard OAuth authorization policy on Request triggers (issuer = tenant, audience = the trigger app id) so requestedBy is a token claim.` |
| D-W2 | `workflows/report-delivery-pipeline.json` | trigger schema + `Wait_for_approval_*` subscribe body | schema: `"requestedBy": { "type": "string", "description": "populated from the caller token claim x-ms-client-principal-name, not from the body" }`; subscribe body: `"kind": "REPORT_DELIVERY", "reportType": "@{parameters('reportType')}", "requestedBy": "@{coalesce(triggerOutputs()?['headers']?['x-ms-client-principal-name'], triggerBody()?['requestedBy'])}"`; same `kind` / `requestedBy` fields in the subscribe bodies of `defender-incident-brief` (`JIRA_CREATE`), `jira-finding-sync` (`IAF_SUBMIT`), `scheduled-deepsearch` (`REPORT_DELIVERY` / `DeepSearch` and `JIRA_CREATE`), `onetrust-assessment-intake` (`REPORT_DELIVERY` / `InfoSecTPA-DPO`), `template-update-approval` (`TEMPLATE_UPDATE`) |
| D-W3 | `workflows/onetrust-assessment-intake.json`, `workflows/scheduled-deepsearch.json` | the `PUT https://graph.microsoft.com/v1.0/sites/…:/content` upload actions | replace with `"method": "POST", "uri": "@{parameters('deliveryFunctionUrl')}/api/upload", "authentication": { "type": "ManagedServiceIdentity", "audience": "@{parameters('deliveryFunctionAudience')}" }, "body": { "supplierName": "…", "serviceName": "…", "fileName": "…", "contentBase64": "…", "share": "org-view" }` (fields per `functions/delivery/README.md`); then remove the Logic App MI's `Sites.Selected` write grant (ledger row L12x) |
| D-F1 | `functions/delivery/README.md` | after the Graph JSON | `The Foundry project managed identity and the Logic App managed identity each receive a separate \`Sites.Selected\` grant with \`"roles": ["read"]\` on the same site; no identity on the platform holds Sites.Read.All or Sites.ReadWrite.All. Share links for \`Reports/DPO/\` use \`{"type":"view","scope":"users"}\` with the DPO group as recipient (team/TEAM_MODEL.md §9). Prefer App Service authentication (Easy Auth, allowed identity = the Logic App MI) over the function key.` |
| D-SP1 | `sharepoint/README.md` | Permissions | `Human roles on the site (Members with unique Read on Reports/, Templates/ and Governance/; owner Contribute/Edit; DPO Visitors on Reports/DPO/; readers on Governance/): ../team/TEAM_MODEL.md §9.` |
| D-MCP1 | `mcp-server/README.md` | Security notes | `- Access model: each user's own \`az login\` identity (local) or Easy Auth allowed group \`sg-infosec-foundry-users\` (hosted); thread metadata carries the caller UPN. Clients: only MCP clients on the approved AI-tooling register may connect — a client's model provider receives Euronext data (team/TEAM_MODEL.md §11, §13).` |
| D-O1 | `orchestrator/README.md` | Governance | `Thread and shared-memory conventions (owner metadata, retention, note format, who adds/deletes, no personal store): ../team/TEAM_MODEL.md §13.` |
| D-C1 | `integrations/copilot/README.md` | Option 1 step 5 | `Publish to the security group \`sg-infosec-foundry-users\` only (not org-wide); connector auth delegated (OBO) — team/TEAM_MODEL.md §11.` |
| D-OP1 | `operations/access-governance/{ACCESS_LIFECYCLE,QUARTERLY_ACCESS_REVIEW,BREAK_GLASS}.md`, `scripts/access_snapshot.sh` | every `team/least-privilege/…` reference | **applied** (snapshot script lists the seven groups). Original text: point to `team/TEAM_MODEL.md` (§14, §15, §12.3) and rename `-platform-approvers` → `-senior-approvers`, `-platform-admins` → `-admin-pim`, `-auditors` → `-readers`, `tier-1/2/3` → `Tier B/A/C`; QUARTERLY item 5: `exactly three Sites.Selected grants (Function MI write, project MI read, Logic App MI read)`; QUARTERLY item 13: `10 % of Tier A approvals + 100 % of Tier B fallbacks` |

## 21. Resolution log — contradictions between the two lenses and the decision taken

| Topic | Least-privilege lens | Operations lens | Decision and reason |
|---|---|---|---|
| Group count / standing privilege | 6 groups; no standing privileged role | 7 groups; `-owner` holds standing `Foundry Owner` + `Foundry Project Manager` | **7 groups, no standing privilege**: keep `-owner` but strip it to Reader / Log Analytics Reader / site owner / maker / GitHub; `Foundry Owner` is PIM via `-admin-pim`; `Foundry Project Manager` dropped (role grants are code). `enablePim=false` fallback recorded as an exception |
| Tier A (a, d2, e, f) | author sign-off + 10 % sampling + escalation flag | peer four-eyes | **Peer four-eyes** — everything written to `Reports/` is a record and the kit's Layer 3 expects a human other than the producer; five people give four candidate approvers. Sampling kept as a quality check on approvals |
| Tier B (b, c, d) | any peer ≠ requester | owner or deputy ≠ requester | **Owner / deputy** — deliverables leaving the team carry the accountable signature; 2-business-day fallback to any peer with owner notification avoids the bottleneck |
| Owner's own platform change | deputy approves | owner approves, deputy reviews | **Both**: required deputy review (no self-approval) and the owner merges / approves deployment as accountable; templates proposed by the owner are approved by the deputy |
| Users' `Monitoring Reader` | none | granted | **None** — F9 is the owner's; users report incidents; add via ledger if self-service cost review is wanted |
| Custom agent-consumer role | compensating controls only | preventive custom role | **Custom role where allowed + detective drift control always on** |
| Logic App MI Graph permission | none (all via Function) | `Sites.Selected` read | **Read** — `scheduled-deepsearch` reads the watchlist list directly; the two direct uploads in the shipped workflows are routed through the Function (D-W3) with a time-boxed write exception (L12x) until then |
| Approval kinds | `REPORT_DELIVERY` + `reportType` (values from `pipelines.json`) | one kind per report type | **`REPORT_DELIVERY` + `reportType`** (no new vocabulary in the workflows) plus `JIRA_CREATE`, `IAF_SUBMIT`, `TEMPLATE_UPDATE`, `PLATFORM_CHANGE`, `MEMORY_DELETE`; tier labels A/B/C from `approval-policy.json` (D-T2) |
| `requestedBy` | token UPN | token claim via Logic Apps OAuth policy | **Token claim** (D-W1 / D-W2); body value only as a fallback until the policy is enabled |
| Token rotation | 90 d all | 180 d (SSC 365 d) | **180 d default, 90 d for the ENX gateway, Bing 180 d** — all tokens are read-only and live only in Key Vault; Euronext policy prevails if stricter |
| Thread retention | 90 d after approved deliverable | 180 d inactive | **Both**: 90 d after the deliverable is stored, 180 d inactivity cap |
| Memory deletion | author, or owner via `MEMORY_DELETE` (deputy if owner is author) | owner | **Author or owner via recorded `MEMORY_DELETE`**; deputy only when the owner is the author |
| DPO share links | org view links | `scope: users` to DPO group | **`scope: users`** for `Reports/DPO/` (D-F1) |
| Approved MCP clients | not covered | register | **Adopted** (§11) |
| Group ownership | Entra IAM team owns privileged groups | line manager owns them | **Line manager as accountable owner, IAM team executes** |
| Deputy nomination | owner nominates, line manager confirms | owner nominates | **Owner nominates, line manager confirms**, recorded in the register |
