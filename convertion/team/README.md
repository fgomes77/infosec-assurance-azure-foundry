# Team, Ownership, Identity/RBAC and Approval Model

Operations-first design for the five people who run the InfoSec Assurance
platform on Euronext's Azure AI Foundry. It starts from how the team works
day-to-day (requests, approvals, incidents, changes, reviews) and derives
the Entra ID groups, Azure/SharePoint/GitHub roles, connection ownership,
approval routing, thread/memory conventions and the RACI from those flows.
Everything here obeys the platform invariants already fixed in the kit:
agents read-only (`governance/DATA_PROTECTION_GUARDRAILS.md`), verifier +
human approval before any write (`governance/HUMAN_APPROVAL.md`),
`Reports/<Supplier>/<Service>/` (`sharepoint/README.md`), Entra identities
and managed identities everywhere, EU region, no Euronext data to the web,
three model tiers (`governance/MODEL_ROUTING.md`).

Companion files in this folder:

| File | Purpose |
|---|---|
| `rbac.bicep` + `rbac.parameters.example.json` | Role assignments for the groups and managed identities below (module referenced from `infra/main.bicep` — see shared deltas) |
| `approval-policy.json` | Machine-readable approval routing (kind → tier → approver group → self-approval rule), consumed by the approval flow behind `approvalWebhookUrl` |
| `custom-role.agent-consumer.json` | Optional custom data-plane role for assurance users (run agents, no agent authoring) |
| `access-review.sh` | Read-only evidence collector for the quarterly access review |
| `ACCESS_REGISTER.md` | Register template: people, groups, service accounts, connections, rotation dates |

## 1. The team

| Person | UPN (placeholder) | Standing role | Extra privileges |
|---|---|---|---|
| Francisco Gustavo Gomes | `{upn:francisco.gomes}` | Accountable **owner**: creation, planning, maintenance, optimisation, updates of the whole solution; assurance user | Platform admin (PIM-eligible), change approver (templates/platform/prompts/registry), group owner |
| José Mogollon | `{upn:jose.mogollon}` | Assurance user | Report approver |
| Pedro Santos | `{upn:pedro.santos}` | Assurance user | Report approver |
| José Meireles | `{upn:jose.meireles}` | Assurance user | Report approver |
| Tânia Morais | `{upn:tania.morais}` | Assurance user | Report approver |
| Deputy owner | `{upn:deputy}` — one of the four, nominated by the owner and recorded in `ACCESS_REGISTER.md` | Assurance user | Break-glass eligible; second approver for external-facing reports; code-owner reviewer of the owner's PRs |

All five have the **same persona experience**: the preamble in
`agents/persona_system_prompt.md` is agent-side and identical for every
caller; there is no per-user persona configuration, no per-user prompt,
no per-user model tier. What differs per person is only *what they may
change* (RBAC) and *what they may approve* (approval routing).

## 2. Operations first — the daily flows and what each needs

| # | Flow | Who acts | Identity in use | Must be true (derived access) | Evidence |
|---|---|---|---|---|---|
| F1 | Ask an advisor / orchestrator a question (req. g, h, i) via Foundry playground, Copilot, or local MCP | any of the five | own Entra user | `Azure AI User` on the project; Copilot agent shared with the users group; MCP = own `az login` | Foundry thread + App Insights trace |
| F2 | Request a report (req. a–f): upload PDF or trigger a pipeline with Supplier/Service | any of the five | own Entra user → Logic App MI → Function MI | pipeline trigger accepts only authenticated team callers; `requestedBy` = token UPN | Logic Apps run + SharePoint version |
| F3 | Approve a report before it is rendered/stored | a **different** team member (four-eyes) | own Entra user in Teams Approval | approver ∈ approver group, approver ≠ requester; Tier B needs owner/deputy | Approval record (UPN, timestamp, correlationId) |
| F4 | Propose a template change (req. j) | any of the five via `template-manager` | own Entra user | proposal open to all; **approval owner-only** | Review page + `templates/audit.log` |
| F5 | Change the platform (Bicep, registry, instructions, scripts, tiers, Copilot publication) | owner (peers may propose via PR) | owner user + PIM activation; deployer SP via OIDC | code-owner review; `production` environment approval by owner | PR, PIM log, deployment run |
| F6 | Re-sync from a fresh claude.ai export | owner | as F5 | `deploy.sh` runs only from the deploy pipeline | verify_conversion output |
| F7 | Incident (egress alert, verifier FAIL spike, injection, credential exposure, pipeline outage) | any user triages; owner leads | own users; owner PIM for containment | users read logs; owner can disable a connection / workflow | Incident ticket `{jira:INFOSEC-PLAT}` |
| F8 | Rotate an integration credential | owner + target-system admin | owner PIM `Key Vault Secrets Officer` | KV RBAC; connection re-pointed to new secret version | KV secret versions, register row |
| F9 | Monthly evaluation + cost review | owner, users consulted | users `Monitoring Reader` | read-only access to App Insights/Log Analytics | Review minutes in `Governance/Reviews/` |
| F10 | Quarterly access review | owner (users group), owner's line manager (owner/break-glass groups) | Entra access reviews | `access-review.sh` evidence | `Governance/AccessReviews/{yyyy}-Q{n}/` |
| F11 | Save/search team memory | any of the five | own Entra user via MCP `save_memory` or advisor `MEMORY:` block | users may add; owner deletes | `memory_store.py list` |
| F12 | Support request | requester → peer (L1) → owner (L2) → Azure landing-zone team / Microsoft (L3) | — | Teams channel `{teams:infosec-assurance-platform}` | Ticket |

Design consequences that follow directly from the flows:

1. Four of the five need **data-plane use only** (F1–F3, F11); one needs
   **control-plane change** (F5, F6, F8), and only for bounded windows.
   Hence two human groups, standing access for use, PIM-eligible access for
   change.
2. F3 requires a **technically enforced** requester ≠ approver check; the
   only way to make it enforceable is to derive `requestedBy` from the
   caller's token, never from a free-text field.
3. F4/F5 are the only owner-only decisions; keeping them owner-only keeps
   the report path (F2/F3) fast — the owner is never a bottleneck for daily
   work.
4. Because the owner also produces reports, **a peer approves the owner's
   reports** (segregation of duties, §9).

## 3. Entra ID security groups

Naming: `sg-infosec-foundry-<purpose>`. All groups are security groups,
mail-disabled, **assigned** membership (no dynamic rules — membership is a
deliberate act), owned as below, and covered by Entra access reviews
(§11). Membership changes go through an entitlement-management access
package where available, otherwise the group owner adds directly and
records the change in `ACCESS_REGISTER.md`.

| Group | Members | Group owner (can add/remove) | Approval to add | Expiry / review | Grants |
|---|---|---|---|---|---|
| `sg-infosec-foundry-users` | all five | owner `{upn:francisco.gomes}` (backup owner: IAM team `{group:iam-admins}`) | owner | access package 12 months; quarterly review | Foundry data plane, SharePoint site member, Copilot agent audience, MCP hosted endpoint, App Insights read, GitHub read/PR |
| `sg-infosec-foundry-report-approvers` | all five (new joiners after the onboarding attestation, §10) | owner | owner | quarterly review | May approve Tier A submissions (§7) |
| `sg-infosec-foundry-senior-approvers` | owner + deputy | owner's line manager `{upn:line-manager}` | line manager | quarterly review | May approve Tier B submissions (§7) |
| `sg-infosec-foundry-owner` | owner only | owner's line manager | line manager | quarterly review by line manager | Standing: `Azure AI Developer` (account), `Azure AI Project Manager` (project), Reader (RG), GitHub admin, SharePoint site owner, Copilot Studio maker |
| `sg-infosec-foundry-admin-pim` | **eligible**: owner; **active**: nobody by default | line manager (PIM for Groups policy) | PIM activation: MFA + justification + ticket; max 8 h; approver = line manager for `Contributor`, self-activation allowed for Key Vault/Logic App/Function roles | activation history reviewed quarterly | Contributor (RG), Key Vault Secrets Officer, Logic App Contributor, Website Contributor, Monitoring Contributor, Storage Blob Data Reader, RBAC Administrator (conditioned) |
| `sg-infosec-foundry-breakglass` | **eligible**: deputy (owner absent) | line manager | PIM activation approved by line manager or SecOps on-call `{group:soc-oncall}`; max 8 h; used only when the owner is unavailable | every activation reviewed by the owner within 5 business days | Same as `admin-pim` |
| `sg-infosec-foundry-readers` | ISMS/internal audit `{group:isms-audit}`, DPO `{group:dpo}` (optional) | owner | owner | quarterly review | Reader (RG), Log Analytics Reader, Logic App Operator (run history), SharePoint visitor |

Rationale: the owner cannot add himself to the privileged groups (their
owner is the line manager), which is the ISO 27001 A.5.3 / A.8.2 control on
privileged-right self-grant; the users group is owned by the person
accountable for the platform, which keeps onboarding a same-day act.

Conditional Access policy `CA-InfoSec-Foundry` targets all groups above
for the cloud apps *Azure Management*, *Azure AI / Cognitive Services* and
*Office 365 SharePoint Online*: MFA + compliant device required, sign-in
frequency 12 h, legacy auth blocked (NIS2 Art. 21(2)(j); ISO 27001 A.8.5).

## 4. Azure RBAC per resource

Resource names follow `infra/main.bicep` (`{baseName}` = `infosecfoundry`
by default). Standing = permanent assignment; PIM = eligible via
`sg-infosec-foundry-admin-pim` / `-breakglass`. Role assignments are
deployed by `team/rbac.bicep` — nothing is assigned by hand except the
first bootstrap (§10). Built-in role GUIDs are in the Bicep; verify them
against `az role definition list` before first deployment.

| Resource | `sg-…-users` | `sg-…-owner` (standing) | `sg-…-admin-pim` / `-breakglass` (PIM) | Managed identities / SPs | `sg-…-readers` |
|---|---|---|---|---|---|
| Resource group `rg-infosec-foundry` | — | Reader | **Contributor** (redeploy Bicep, create connections) | deployer SP `{app:infosec-foundry-deployer}` (GitHub OIDC): Contributor + `Azure AI Developer` on the account, scoped to this RG only | Reader |
| Foundry account `{baseName}-aif` | — | **Azure AI Developer** (create/update agents, deployments, connections via the scripts; no role assignment) | RBAC Administrator with condition `roles ∈ {Azure AI User, Reader, Monitoring Reader}` (can only grant the low-privilege roles) | Logic App MI, MCP host MI, Copilot connector SP: **none at account** | Reader |
| Foundry project `{baseName}-proj` | **Azure AI User** — run agents, threads, files, vector-store reads; the persona experience | **Azure AI Project Manager** (can grant Azure AI User to the users group; manage project) | — | Logic App MI: Azure AI User; MCP host MI (if hosted): Azure AI User; delivery Function MI: **none** (it never calls Foundry) | Reader |
| Key Vault `{baseName}-kv` (RBAC permission model, soft-delete + purge protection, no access policies) | — | Reader (list names, not values) | **Key Vault Secrets Officer** (rotate) | Logic App MI, Function MI, Foundry account MI (KV-backed connections): **Key Vault Secrets User** on the specific secrets only (secret-scoped assignments) | — |
| Delivery Function App `{baseName}-fn-delivery` | — | Reader | **Website Contributor** (deploy) + Monitoring Contributor | Function MI: Graph `Sites.Selected` **write** on the one site; Storage Blob Data Contributor on `deliverables`; Key Vault Secrets User | Reader |
| Logic Apps Standard `{baseName}-la` | — | Reader | **Logic App Contributor** (import/edit workflows, set parameters) | Logic App MI: Azure AI User (project); Graph `Sites.Selected` **read** (watchlist/list reads) — writes only through the Function; Key Vault Secrets User; Storage (runtime SA) Blob/Queue/Table Data Contributor | **Logic App Operator** (read run history = approval evidence) |
| Storage `{baseName}sa` (`deliverables`) and Logic Apps runtime SA | — | — | Storage Blob Data Reader (investigation only) | Function MI: Blob Data Contributor (`deliverables`); Logic App MI: as above; `allowSharedKeyAccess: false` where the runtime supports identity-based connections | — |
| Log Analytics `{baseName}-logs` + App Insights `{baseName}-appi` | **Monitoring Reader** (see own runs' traces; team data is shared by classification) | Monitoring Reader | **Monitoring Contributor** (alerts, KQL rules) | Foundry project MI: Monitoring Metrics Publisher (tracing export) | Log Analytics Reader |
| Bing Grounding `{baseName}-bing` + connection `bing-grounding` | — (used only through agents) | Reader | Contributor (key rotation — the single API key on the platform, imposed by the Bing resource; rotated semi-annually, §6) | — | — |
| Model deployments (`gpt-4o`, `o3-mini`, `gpt-4o-mini`) | via Azure AI User | via Azure AI Developer | Cognitive Services Contributor is unnecessary — deployments are Bicep-managed | — | — |

Roles the platform deliberately does **not** use: `Owner` and `User Access
Administrator` on the RG (role grants go through the conditioned RBAC
Administrator role or the landing-zone team), `Azure AI Account Owner`
(bundles role assignment with data plane — too broad for one person),
`Cognitive Services Contributor` for humans (keys), Storage account keys.

### 4.1 Azure AI User vs Azure AI Developer — why this split

| | Azure AI User (users group) | Azure AI Developer (owner) |
|---|---|---|
| Data plane: threads, runs, messages, files, vector-store retrieval | yes | yes |
| Create/update/delete agents, connections, model deployments | current built-in role includes agent-authoring data actions | yes (control + data plane) |
| Assign roles | no | no (that is Azure AI Project Manager, standing for the owner at project scope only) |
| Sees other users' threads via SDK | yes (project-wide data plane) — hence the thread conventions in §8 | yes |

The Azure AI User built-in role allows agent authoring in the current
Foundry role model. That conflicts with "prompt/registry changes are
owner-only" unless mitigated, so the design applies **both**:

- **Preventive (preferred when the tenant allows custom roles):**
  `custom-role.agent-consumer.json` — a copy of Azure AI User with the
  agent create/update/delete data actions removed. The exact operation
  strings must be taken from `az provider operation show --namespace
  Microsoft.CognitiveServices` at deployment time (marked `{to-confirm}`
  in the file); if the tenant forbids custom roles, assign Azure AI User
  and rely on the detective control.
- **Detective (always on):** the deployment writes the SHA-256 of every
  deployed agent's instructions and tool set into `build/manifest.json`;
  a daily Logic App (`operations/` layer) re-reads the live agents and
  raises an alert on any hash that differs from the last approved
  deployment. Live edits that were not made by the deploy pipeline are
  reverted by re-running `deploy.sh` (F6). Evidence: alert + run history.

## 5. SharePoint site roles

Site `{sharepoint:infosec-assurance}` (the `SHAREPOINT_SITE_ID` of
`setup/.env`). Groups map to the SharePoint permission levels; unique
permissions are broken **only** where the report-of-record integrity
requires it.

| SharePoint scope | Site owners (Full Control) | Site members (Edit) | Site visitors (Read) | App-only (Sites.Selected) |
|---|---|---|---|---|
| Site root | `sg-infosec-foundry-owner`, SharePoint admin `{group:spo-admins}` (backup) | `sg-infosec-foundry-users` | `sg-infosec-foundry-readers` | — |
| `Infosec Assurance/GRC/TPA/Active/<Supplier>[/<Service>]/` (evidence repository — the team uploads evidence here by hand) | inherit | inherit (**Edit**: this is the team's working library) | inherit | agents' Graph app `{app:infosec-foundry-agents-read}`: **read** |
| `Reports/<Supplier>/<Service>/` (reports of record) | inherit | **unique: Read** (humans never edit a report of record; a correction is a new pipeline run — versioning keeps history) | inherit | delivery Function MI `{mi:infosec-delivery-fn}`: **write** (the only writer); agents' app: read |
| `Reports/DPO/<Supplier>/<Service>/` | inherit | unique: Read | + DPO `{group:dpo}` Read | Function MI write |
| `Templates/` (template library, req. j) | inherit | unique: Read (proposals go through `template-manager`, not direct edits) | inherit | Function MI write (review pages under `Templates/Reviews/`); agents' app read |
| `Governance/` (access reviews, evaluation and cost minutes) | inherit | unique: Read; owner Edit | `sg-…-readers` Read | — |

`Sites.Selected` is granted to exactly three application identities, each
with the least role the flow needs: the Function MI (`write`), the Logic
App MI (`read`), the agents' Graph app registration (`read`). No identity
holds `Sites.Read.All` / `Sites.ReadWrite.All` (tightening of the
current text in `governance/DATA_PROTECTION_GUARDRAILS.md` §2 and
`workflows/README.md` — see shared deltas). Sharing links stay
organisation-scoped **view** links for `Reports/`; for `Reports/DPO/`
the design recommends `scope: users` with the DPO group as recipient
(delta to `functions/delivery`), because the DPO deliverable leaves the
team.

## 6. Foundry project connections — ownership and custody

Every connection is created by the owner in the Foundry Management
center (or Bicep), holds **no human credential**, and has a named
custodian on the target-system side who issues and revokes the identity.
Preference order: managed identity → app registration with federated
credential → service-account token in Key Vault (only where the SaaS
offers nothing else).

| Connection (`registry.json`) | Identity type | Identity name | Target-side role (read-only) | Custodian (issues/revokes) | Owner (Foundry side) | Rotation | Key Vault secret |
|---|---|---|---|---|---|---|---|
| `conn-sharepoint-graph`, `conn-defender-graph`, `conn-entra-iam-graph` | **Foundry project managed identity** (OpenAPI tool auth = managed identity, audience `https://graph.microsoft.com`) — no secret | `{mi:infosecfoundry-proj}` | Graph app permissions: `Sites.Selected` (read on the one site), `SecurityIncident.Read.All`, `SecurityAlert.Read.All`, `ThreatHunting.Read.All`, `User.Read.All`, `Group.Read.All`, `RoleManagement.Read.Directory` | Entra admin `{group:iam-admins}` (admin consent) | owner | none (identity-based) | — |
| `conn-jira-cloud`, `conn-jira-assets` | service-account API token | `svc-infosec-foundry-ro-jira` | Jira: browse projects / Assets: object schema viewer; no create/edit | Jira admin `{group:jira-admins}` | owner | 180 days | `kv-jira-ro-token` |
| `conn-confluence` | service-account API token | `svc-infosec-foundry-ro-confluence` | space read | Confluence admin | owner | 180 days | `kv-confluence-ro-token` |
| `conn-onetrust` | service-account API token | `svc-infosec-foundry-ro-onetrust` | Viewer role, assessment read | OneTrust admin `{group:onetrust-admins}` | owner | 180 days | `kv-onetrust-ro-token` |
| `conn-securityscorecard` | API token | `svc-infosec-foundry-ro-ssc` | read-only portfolio access | SSC admin | owner | 365 days | `kv-ssc-ro-token` |
| `conn-iaf-api` | app registration with federated credential to the project MI (preferred) or token | `{app:infosec-foundry-iaf-ro}` | IAF read scope | IAF product owner `{upn:iaf-owner}` | owner | 180 days if token | `kv-iaf-ro-token` |
| `enx-gateway-mcp` (`integrations/mcp/enx-gateway.json`) | bearer token from Key Vault, injected at deploy | `svc-infosec-foundry-ro-enxgw` | gateway read-only toolset (allowlist in the json) | ENX gateway team `{group:enx-gateway}` | owner | 90 days (gateway policy) | `kv-enx-gateway-token` |
| `bing-grounding` | Bing resource key (platform constraint) | — | n/a (public web) | owner | owner | 180 days | wired by Bicep, not in KV |
| `app-insights` | connection string (Bicep-wired) | — | telemetry write | owner | owner | on workspace rebuild | — |
| `write_connections` (registry) | **none, for every agent** — any grant is a PR reviewed by the owner and a deputy | — | — | — | owner | — | — |

Rules: (1) a custodian never holds the Foundry side and the owner never
holds target-system admin — two people are needed to change what an
agent can reach (ISO 27001 A.5.3); (2) tokens are written to Key Vault by
the custodian or the owner during a PIM window and referenced by name
only; (3) a connection whose secret is past rotation date fails the
quarterly review and is disabled until rotated; (4) when a SaaS supports
OAuth client credentials with a federated identity, migrate off the token
at the next rotation.

## 7. Approval routing

Every submission of record already passes verifier → `HttpWebhook` gate
(`governance/HUMAN_APPROVAL.md`). This section fixes **who** may answer
the gate. `approval-policy.json` encodes it for the approval flow (Power
Automate or Function) behind `approvalWebhookUrl`, which must enforce all
of: approver's token UPN ∈ the tier's group (Graph `checkMemberGroups`),
approver ≠ `requestedBy`, decision stored with UPN/timestamp/correlationId
before calling back.

| Kind (from the subscribe body) | Pipelines / workflows | Tier | Who may approve | Why |
|---|---|---|---|---|
| `REPORT_DEEPSEARCH` (a), `REPORT_EVIDENCE` (d2), `REPORT_SOC` (e), `REPORT_PENTEST` (f) | `deepsearch-report`, `tpa-evidence-analysis`, `soc-report-summary`, `pentest-report-summary`, `scheduled-deepsearch` store | **A — four-eyes peer** | any `sg-…-report-approvers` member ≠ requester | Internal working outputs consumed by the team itself; peer review is the quality control |
| `REPORT_DPO` (b), `REPORT_CYBERFORUM` (c), `REPORT_CISO_GLOBAL` (d) | `dpia-dpo-report`, `cyber-forum-pptx`, `ciso-global-pptx`, `onetrust-assessment-intake` upload | **B — senior four-eyes** | `sg-…-senior-approvers` (owner or deputy) ≠ requester; if the requester is the owner → deputy; if both are unavailable > 2 business days → any Tier A approver with the owner notified (logged exception) | These leave the team (DPO, CISOs, contract owners): the accountable owner or deputy signs what carries the team's name |
| `JIRA_CREATE`, `IAF_SUBMIT` | `defender-incident-brief`, `scheduled-deepsearch` ticket, `jira-finding-sync` | **A** | any report approver (scheduled runs have no human requester) | Submissions into registers of record are human-accountable acts; peer is sufficient because Jira/IAF have their own workflow |
| `TEMPLATE_UPDATE` (j) | `template-update-approval` | **C — owner-only** | owner; when the owner is the proposer → deputy reviews the visual diff first (recorded), owner approves | Templates propagate to every consumer agent and renderer (fidelity contract) |
| Platform change (Bicep, `integrations/registry.json`, `templates/registry.json`, agent instructions, `scripts/`, model tier, `write_connections`, Copilot publication, CA/PIM settings) | GitHub PR + `production` deployment environment | **C — owner-only** | owner merges + approves deployment; code-owner review by deputy when the owner authored the PR, by owner otherwise | Single accountable point for the solution; four-eyes preserved through review |
| Memory note (`save_memory`, advisor `MEMORY:` block) | MCP / `memory_store.py add` | self | the person saving (per `HUMAN_APPROVAL.md`); deletion by owner | Not a write to an external system |
| Break-glass activation | PIM | line manager / SecOps on-call | see §3 | Owner unavailable |

Gate expiry stays P3D for reports and P7D for templates (as shipped). An
expired gate is not an approval; the requester re-runs the pipeline.

## 8. Threads and memory conventions

| Topic | Convention | Rationale |
|---|---|---|
| Thread ownership | One thread per **(person, supplier, service, month)**; metadata `{owner_upn, supplier, service, classification:"internal", created}` set by the MCP server / Copilot connector / pipeline; playground users name the thread `<initials>/<Supplier>/<Service>/<yyyy-mm>` | Attribution for audit and per-user cost review; bounded context per engagement |
| Visibility | Threads are **team-visible** (project data plane); nothing personal goes into a thread; team members may read a colleague's thread to take over an engagement | Same data classification for all five; supports hand-over |
| Retention | Threads inactive > 180 days are deleted by the `operations/` cleanup job; a thread that produced a stored report may be deleted — the report and its Logic Apps run are the record | Minimisation; App Insights keeps the trace ≥ 1 year (DORA Art. 28 evidence) |
| Shared team memory (`vs-assurance-memory`) | Note format `YYYY-MM-DD | <Supplier> | <Service or "-"> | decision/fact/position/follow-up | <text> | by {upn}`; facts about suppliers, decisions taken, positions defended, follow-ups; **no** personal data of individuals beyond a role title, no special-category data, no credentials, no text pasted from a supplier document | Auditable, per-note deletable; GDPR Art. 5(1)(c) |
| Personal notes | Not on the platform: no per-user vector store, no personal memory. Personal working notes live in the person's own OneNote/OneDrive | Keeps the platform out of scope for per-user profiling; nothing to purge at offboarding |
| Memory hygiene | Users add (own identity); owner reviews the list quarterly and deletes stale/duplicate/erroneous notes; any team member may request deletion; retention 24 months or supplier exit | RoPA entry `{ropa:infosec-foundry-memory}` owned by the owner, DPO informed |
| Attribution in telemetry | `owner_upn` flows to App Insights as a custom dimension for the monthly cost review; purpose limited to capacity/cost tuning, not individual performance | Purpose limitation, transparency to the team |

## 9. Segregation of duties

| Conflict | Control |
|---|---|
| Owner authors a report and would approve it | Approval flow rejects approver = requester; Tier B for the owner's reports goes to the deputy |
| Owner approves his own platform change | Accepted by design (single accountable owner) with compensating controls: code-owner review by the deputy on every owner-authored PR, PIM activation with justification, deployment only via the pipeline, quarterly review of the owner/PIM groups by the line manager |
| Owner adds himself to a privileged group | Privileged groups are owned by the line manager; access reviews of those groups are done by the line manager |
| One person controls both sides of an integration | Foundry side = owner; target-system credential = custodian; both are needed to change what agents reach |
| Producer checks its own output | Separate `output-verifier` agent, then a human |
| Human bypasses the gate and writes directly | Only the Function MI can write to `Reports/`; humans hold Read; agents hold GET-only tools |
| Deployer identity used interactively | The deployer SP has no interactive sign-in (federated credential only, bound to the `production` environment of the repo) |
| Deputy break-glass | PIM-approved by a third party, time-boxed, reviewed by the owner afterwards |

## 10. Joiner / mover / leaver

**Joiner (new assurance user)** — target: same-day for use, approver role
after attestation.

| Step | Who | Action | Evidence |
|---|---|---|---|
| 1 | line manager | Request access package `AP-InfoSec-Foundry-User` (or Teams message to the owner) | request id |
| 2 | owner | Approve → member of `sg-infosec-foundry-users` (grants Foundry Azure AI User, SharePoint member, Copilot agent, hosted MCP, App Insights read, CA policy) | group change |
| 3 | owner | Add to GitHub team `infosec-assurance-users` (read + PR), Teams channels `{teams:infosec-assurance-platform}` and `{teams:infosec-assurance-approvals}` | — |
| 4 | joiner | Read `governance/*.md`, `sharepoint/README.md`, this file; run the MCP server locally with `az login`; complete one Tier A report end-to-end with a peer approving | attestation form in `Governance/Onboarding/` |
| 5 | owner | Add to `sg-infosec-foundry-report-approvers`; record in `ACCESS_REGISTER.md` | register row |

**Mover / leaver**

| Step | Who | Action |
|---|---|---|
| 1 | HR/IAM trigger or line manager | Access package expiry / removal from every `sg-infosec-foundry-*` group (removes Foundry, SharePoint, Copilot, MCP, App Insights, CA scope in one act) |
| 2 | owner | Remove from GitHub team and Teams channels; if the leaver was the deputy: nominate a new deputy, update `sg-…-senior-approvers`, `-breakglass` eligibility, CODEOWNERS |
| 3 | owner | Re-tag the leaver's active threads (`owner_upn` → new engagement owner) or delete them; leave shared memory notes (team facts) in place; nothing personal to purge (§8) |
| 4 | owner + custodians | Rotate any credential the leaver could have seen (break-glass window logs decide; normally none — no human ever holds a platform key) |
| 5 | owner | Register updated; evidence filed |

**Owner leaver / succession** — line manager appoints the successor
(normally the deputy): transfer Entra group ownership, Foundry Azure AI
Developer / Project Manager, PIM eligibility, GitHub admin, SharePoint site
ownership, Copilot Studio maker role, custodianship rows in the register
and the RoPA entry; the successor re-runs `deploy.sh --dry-run` and
`access-review.sh` as the hand-over check.

## 11. Quarterly access review

Cadence: first week of each quarter; reviewer of `sg-…-users` and
`-report-approvers` = owner; reviewer of `-owner`, `-senior-approvers`,
`-admin-pim`, `-breakglass` = line manager; evidence in
`Governance/AccessReviews/{yyyy}-Q{n}/`.

| Item | Source | Pass criterion |
|---|---|---|
| Group memberships | Entra access review + `access-review.sh` | Each member still in the team; no unexpected identity |
| Azure role assignments in the RG | `access-review.sh` (`az role assignment list`) | Matches `rbac.bicep` exactly; no standing privileged role on a human |
| PIM / break-glass activations | PIM audit log | Every activation has ticket + justification; break-glass ones reviewed by the owner |
| SharePoint site permissions | Site permissions report | Only the groups in §5; three Sites.Selected grants |
| Foundry connections and service accounts | Management center + register | All within rotation date; `write_connections` still empty |
| Graph app permissions on the project MI and agents' app | Entra enterprise apps | Read-only set of §6 only |
| GitHub collaborators / teams / branch protection | GitHub settings | Owner admin; users read; CODEOWNERS = owner + deputy; secret scanning + push protection on |
| Copilot Studio sharing | Copilot Studio | Agent shared with `sg-…-users` only, delegated auth |
| Memory store | `memory_store.py list` | Notes conform to §8; stale notes deleted |
| Agent drift | drift alert history | No unexplained drift |

Standards implemented: ISO/IEC 27001:2022 A.5.15 (access control), A.5.16
(identity management), A.5.17 (authentication information), A.5.18 (access
rights — provisioning, review, removal), A.5.3 (segregation of duties),
A.6.5 (termination), A.8.2 (privileged access rights), A.8.3 (information
access restriction), A.8.5 (secure authentication); DORA Art. 5(2)
(management body accountability — the owner role), Art. 9(4)(c)–(d)
(access management, strong authentication), Art. 28 evidence retention;
NIS2 Art. 21(2)(i) (access control policies, asset management), (j) (MFA);
ISO/IEC 42001 A.3.2 (AI roles and responsibilities), A.6.2 (human
oversight in the lifecycle), A.9.2 (responsible use); EU AI Act Art. 14
and Art. 26(2) (human oversight assigned to natural persons with the
competence, training and authority — the approver groups), Art. 12/26(6)
(logs kept).

## 12. MCP-server access

| Mode | Identity | Who may use | Controls |
|---|---|---|---|
| Local stdio (`mcp-server/server.py`) — **default for the five** | the person's own `az login` (`DefaultAzureCredential`) | anyone in `sg-infosec-foundry-users` (their Azure AI User assignment is the gate; removal from the group revokes it) | CA policy (MFA + compliant device) applies to the token; `PROJECT_ENDPOINT` is not a secret; the server stamps `owner_upn` from the signed-in account into thread metadata |
| Hosted (Azure Container Apps, EU region) — only if the ENX gateway or shared tooling needs it | container MI with Azure AI User; caller authenticated by Easy Auth (Entra), allowed group `sg-infosec-foundry-users` | same group | The server copies `X-MS-CLIENT-PRINCIPAL-NAME` into thread metadata so attribution survives the MI hop; `save_memory` records the caller UPN |
| MCP **clients** | — | Only clients on the approved AI-tooling list `{register:approved-ai-clients}`: an MCP client whose model provider receives the agents' answers is an egress of Euronext data. Approved by default: internal tooling and the ENX gateway; Claude Desktop/Code or other third-party clients only under a Euronext-approved agreement (DPA, EU processing) recorded in the register | ISO 27001 A.5.19/A.5.20 (supplier), GDPR Art. 28, the "no Euronext data to the web" rule |

## 13. RACI

R = responsible, A = accountable, C = consulted, I = informed.
FGG = Francisco Gustavo Gomes (owner); DEP = deputy; USERS = José
Mogollon, Pedro Santos, José Meireles, Tânia Morais; LZ = Azure landing
zone / IAM platform team `{group:azure-platform}`; CUST = target-system
custodians (Jira, OneTrust, SharePoint, ENX gateway admins); CISO = CISO /
ISMS manager; DPO = DPO team; SOC = Euronext SOC/CSIRT.

| Activity | FGG | DEP | USERS | LZ | CUST | CISO | DPO | SOC |
|---|---|---|---|---|---|---|---|---|
| Platform creation (Bicep, agents, connections, pipelines) | **A/R** | C | C | R (subscription, CA, PIM, Graph consent) | R (credentials) | I | I (RoPA) | — |
| Planning (roadmap, tier tuning, new systems) | **A/R** | C | C | I | — | C | — | — |
| Maintenance (patching runtimes, SDK pins, Bicep drift, workflow health) | **A/R** | R (when owner absent) | I | C | — | I | — | — |
| Optimisation (token economy, capacity, quality tuning) | **A/R** | C | C (report quality feedback) | I | — | I | — | — |
| Updates / re-sync from export (`deploy.sh`, freshness markers) | **A/R** | C (code-owner review) | I | — | — | I | — | — |
| Template changes (req. j) | **A** (approves) | R (visual review of owner-authored proposals) | R (propose via template-manager) | — | — | I | — | — |
| Integration credential rotation | **A/R** (Foundry side, KV) | R when absent | I | I | R (issue/revoke) | I | — | — |
| Incident response (platform) | **A** / R (incident lead) | R (lead when absent) | R (triage, contain own runs) | C | C | I | I (personal-data breach: A for GDPR Art. 33 path) | C/R (escalation) |
| Evaluation review (monthly: verifier first-pass rate, approval vs rework, grounding) | **A/R** | C | C | — | — | I | — | — |
| Cost review (monthly: tokens per deliverable, capacity, tier moves) | **A/R** | C | I | C (FinOps) | — | I | — | — |
| User support (L1 peer, L2 owner, L3 platform/Microsoft) | **A** / R (L2) | R (L1/L2 backup) | R (L1) | R (L3) | C | — | — | — |
| Report approvals (Tier A / B) | R (Tier B) / **A** for the routing | R (Tier B) | R (Tier A) | — | — | I (Tier B decks) | I (DPO reports) | — |
| Quarterly access review | **A/R** (user groups) | C | I (attest) | R (privileged groups via line manager, PIM) | C | I | — | — |

## 14. Bootstrap order (first deployment)

1. LZ team creates the seven groups (§3), the CA policy, PIM policies,
   the deployer SP with a federated credential for
   `{github:org/repo}` environment `production`, and grants admin
   consent for the Graph permissions in §6.
2. Owner (PIM `Contributor`) runs `setup/provision.sh`; then deploys
   `team/rbac.bicep` with the group object ids (`rbac.parameters.example.json`).
3. Owner grants `Sites.Selected` (§5) to the three app identities.
4. Custodians place the service-account tokens in Key Vault; owner creates
   the `conn-*` connections referencing them.
5. Owner runs `deploy.sh`; the drift baseline is recorded.
6. Owner runs `access-review.sh` and files the output as the Q0 baseline.

## 15. Shared deltas (to be applied by the kit maintainers — not applied here)

| Target file | Delta (literal text) |
|---|---|
| `README.md` folder-layout tree | add `├── team/                      ← team, RBAC (rbac.bicep), approval routing, JML, access review` |
| `README.md` "What gets created in Azure" list | add `- Role assignments for the sg-infosec-foundry-* groups and managed identities (team/rbac.bicep)` |
| `infra/main.bicep` (after the storage resources) | `module rbac '../team/rbac.bicep' = { name: 'rbac', params: { foundryAccountName: foundry.name, projectName: project.name, logAnalyticsName: logAnalytics.name, appInsightsName: appInsights.name, storageAccountName: storage.name, usersGroupObjectId: usersGroupObjectId, ownerGroupObjectId: ownerGroupObjectId, readersGroupObjectId: readersGroupObjectId, pimGroupObjectId: pimGroupObjectId, deployerPrincipalId: deployerPrincipalId, logicAppPrincipalId: logicAppPrincipalId, deliveryFunctionPrincipalId: deliveryFunctionPrincipalId, keyVaultName: keyVaultName } }` plus the matching `param … string = ''` declarations at the top (`usersGroupObjectId`, `ownerGroupObjectId`, `readersGroupObjectId`, `pimGroupObjectId`, `deployerPrincipalId`, `logicAppPrincipalId`, `deliveryFunctionPrincipalId`, `keyVaultName`) |
| `infra/main.parameters.json` | add `"usersGroupObjectId": { "value": "{objectId:sg-infosec-foundry-users}" }, "ownerGroupObjectId": { "value": "{objectId:sg-infosec-foundry-owner}" }, "readersGroupObjectId": { "value": "{objectId:sg-infosec-foundry-readers}" }, "pimGroupObjectId": { "value": "{objectId:sg-infosec-foundry-admin-pim}" }` |
| `infra/main.bicep` storage resource | add `allowSharedKeyAccess: false` under `properties` (identity-based access only) |
| `setup/.env.example` | add `# --- Team / identity (team/README.md) ---`, `ENTRA_GROUP_USERS_OBJECT_ID={objectId:sg-infosec-foundry-users}`, `ENTRA_GROUP_OWNER_OBJECT_ID={objectId:sg-infosec-foundry-owner}`, `ENTRA_GROUP_APPROVERS_OBJECT_ID={objectId:sg-infosec-foundry-report-approvers}`, `ENTRA_GROUP_SENIOR_APPROVERS_OBJECT_ID={objectId:sg-infosec-foundry-senior-approvers}`, `APPROVAL_POLICY_PATH=../team/approval-policy.json` |
| `setup/provision.sh` (final echo block) | replace the self-grant hint with `echo ">> Assign roles by group, not by user: deploy ../team/rbac.bicep with the group object ids (team/README.md §4)"` |
| `deploy.sh` | add before step 7: `echo "==> [6d/7] Access model check (read-only)"; ../team/access-review.sh --quick || echo "note: run team/access-review.sh with az login to verify role assignments"` |
| `workflows/README.md` Authentication | replace `(\`Sites.ReadWrite.All\` or Sites.Selected)` with `(\`Sites.Selected\` read on the InfoSec Assurance site; all writes go through the delivery Function — team/README.md §5)`; add under Human approval gates: `The approval side enforces team/approval-policy.json: approver ∈ tier group, approver ≠ requestedBy, decision recorded with UPN/timestamp/correlationId.` |
| `workflows/report-delivery-pipeline.json` and the four workflow subscribe bodies | add `"kind": "{REPORT_KIND per team/approval-policy.json}"`, `"requestedBy": "@{triggerOutputs()?['headers']?['x-ms-client-principal-name']}"` (token claim, not body text) to each `Wait_for_approval_*` subscribe body; enable the Logic Apps Standard OAuth authorization policy on the Request triggers (issuer = tenant, audience = the trigger app id) |
| `governance/HUMAN_APPROVAL.md` Layer 3 | add `Who may approve is defined in ../team/README.md §7 and enforced from ../team/approval-policy.json (four-eyes: approver ≠ requester; Tier B = owner/deputy; template/platform = owner-only).` |
| `governance/DATA_PROTECTION_GUARDRAILS.md` §2 | replace `Graph \`Sites.Read.All\`` with `Graph \`Sites.Selected\` read on the one site (team/README.md §5–6)`; add `Identity/RBAC model: ../team/README.md.` |
| `integrations/registry.json` `_comment` | append ` Connection ownership, custodians and rotation: team/README.md §6 and team/ACCESS_REGISTER.md.` |
| `integrations/README.md` Authentication | replace `(\`SecurityIncident.Read.All\`, \`ThreatHunting.Read.All\`, \`Sites.ReadWrite.All\` as applicable)` with `granted to the Foundry project managed identity: \`SecurityIncident.Read.All\`, \`SecurityAlert.Read.All\`, \`ThreatHunting.Read.All\`, \`User.Read.All\`, \`Group.Read.All\`, \`Sites.Selected\` (read) — no client secrets (team/README.md §6)` |
| `functions/delivery/README.md` | add `Share links for \`Reports/DPO/\` use \`{"type":"view","scope":"users"}\` with the DPO group as recipient (team/README.md §5); prefer App Service authentication (Easy Auth, allowed identity = the Logic App MI) over the function key.` |
| `mcp-server/README.md` Security notes | add `- Clients: only MCP clients on the approved AI-tooling register may connect (team/README.md §12) — a client's model provider receives Euronext data.` |
| `orchestrator/README.md` Governance | add `Thread and memory conventions (ownership metadata, retention, note format, who may delete): ../team/README.md §8.` |
| `sharepoint/README.md` Permissions | add `Human roles on the site (owners/members/visitors, unique Read on Reports/ and Templates/): ../team/README.md §5.` |
