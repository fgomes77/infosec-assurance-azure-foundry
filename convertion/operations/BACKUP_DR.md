# Backup and Disaster Recovery — State Inventory, RPO/RTO, Restore, Region Failure

What state the platform holds, which of it can be rebuilt from git and
which must be backed up, the recovery objectives per class, the restore
procedures, and the playbook for losing the Azure region. Companion to
`LIFECYCLE.md` (what is versioned) and `RUNBOOK.md` (who acts, severities).
Principle: **the repository plus the claude.ai export rebuild everything
except three things** — the shared memory store `vs-assurance-memory`, the
records of record in SharePoint (which are not platform state and are
protected by Microsoft 365), and the operational logs. Backups are
read-only exports taken with standing roles; no backup step needs PIM. Files in this folder: `backup_vector_stores.py` (export / restore / EU blob upload) and `backup-job.bicep` (the nightly Container Apps Job that runs it with a managed identity).

Control: ISO 27001:2022 A.8.13 (information backup), A.8.14 (redundancy of
information processing facilities), A.5.29 (security during disruption),
A.5.30 (ICT readiness for business continuity), A.8.10; DORA Art. 11
(response and recovery), Art. 12 (backup policies and restoration and
recovery procedures and methods), Art. 9(4)(c); NIS2 Art. 21(2)(c)
(business continuity, backup management, DR); ISO 42001 A.6.2.5, A.6.2.8;
EU AI Act Art. 26(5).


> Role names follow the current Foundry RBAC naming (Foundry User / Foundry Owner /
> Foundry Account Owner / Foundry Project Manager); the underlying role definition
> GUIDs in `rbac.bicep` are unchanged — `enterprise/ENTERPRISE_BLUEPRINT.md` ID-1.

## 1. State inventory

Classes: **G** = rebuilt from git/export by `../deploy.sh` or Bicep (no
backup needed, RPO 0 by construction); **B** = must be backed up by the
platform; **M** = protected by Microsoft 365 / the tenant, outside the
platform's control; **T** = transient, deliberately not backed up.

| # | State | Lives in | Class | Backup mechanism | RPO | RTO | Restore (§4) | Custodian |
|---|---|---|---|---|---|---|---|---|
| S1 | Kit code, docs, workflows, Bicep, KQL, registry, templates registry | git `{github:org/repo}` | G | git (GitHub-side redundancy; owner keeps a clone) | 0 | 1 h (clone) | R7 | owner |
| S2 | claude.ai export (`../../claude-account-export/`) | git + claude.ai account | G | git; the claude.ai account is retained as the upstream (`ROLLOUT_PLAN.md` §6) | 0 | 1 h | R7 | owner |
| S3 | Live agents, `vs-<agent>` stores, `vs-assurance-combined`, verifier, advisor, orchestrator | Foundry project `{baseName}-proj` | G | `build/manifest.json` baseline + `deploy.sh` rebuild; file-list inventory by `backup_vector_stores.py` (for drift evidence, not for restore) | 0 | 4 business h (`deploy.sh` end-to-end) | R1 | owner |
| S4 | **Shared memory `vs-assurance-memory`** (team decisions, supplier facts, positions) | Foundry project | **B** | `backup_vector_stores.py` export (note files + manifest, SHA-256 per note) → the `backups` blob container (nightly Container Apps Job `backup-job.bicep`, EU, managed identity) and/or `Governance/Backups/{yyyy-mm-dd}/` on the site (manual) | **24 h** automated (`backup-job.bicep`, delta D-BDR-B3); 7 days manual fallback (RUNBOOK W8, delta D-BDR-RB1); 0 before every deploy (delta D-LC-D1) | 2 h | R2 | owner (RoPA `{ropa:infosec-foundry-memory}`) |
| S5 | Threads, uploaded thread files, in-flight runs | Foundry project | T | none — working papers; the deliverable of record is in SharePoint, the trace in App Insights | re-run | — | R1 (re-run the request) | each user |
| S6 | Reports of record `Reports/<Supplier>/<Service>/`, `Reports/DPO/`, `Templates/`, `Templates/Reviews/`, `Governance/`, `GRC/TPA/Active` | SharePoint site `{sharepoint:infosec-assurance}` | M | SharePoint versioning (≥ 50 major versions), recycle bin (93 days, two stages), site-collection restore by `{group:spo-admins}` (14-day Microsoft retention), Microsoft 365 Backup for the site where licensed (`{to-confirm}` with M365 admins) | minutes | 4 business h (recycle bin / version) · 1 business day (site restore) | R3 | owner (site owner) + `{group:spo-admins}` |
| S7 | Approval decision records `{list:ApprovalDecisions}` | SharePoint list | M | list versioning + Logic Apps run history in Log Analytics (S10) — two independent copies of every decision | minutes | 4 business h | R3 | owner |
| S8 | Key Vault `{baseName}-kv` secrets (service-account tokens, webhook URLs, Function key) | Key Vault | M/B | soft-delete (90 days) + purge protection (Bicep); every value is re-issuable by its custodian (`../team/TEAM_MODEL.md` §10) — no value is ever copied elsewhere | 0 (soft-delete) · re-issue on total loss | 1 business day (custodian re-issue) | R4 | owner + custodians |
| S9 | Logic Apps Standard `{baseName}-la`: definitions | git (`../workflows/`) + `build/logicapps/` | G | git; `build_logicapps.py` regenerates | 0 | 2 h | R5 | owner |
| S10 | Logic Apps run history, Foundry traces, audit tables | Log Analytics `{baseName}-logs` / App Insights `{baseName}-appi` (365 d) | M | workspace retention 365 d (delta D-OPS-B3); continuous export of the evidence tables to the `backups` container for the ISMS record schedule (delta D-BDR-B2, optional) | n/a (append-only) | n/a | R6 | owner |
| S11 | Delivery / office-tools Function images | ACR `{registry}.azurecr.io` (tags = release) + `../functions/` source | G | rebuild `az acr build` from the tagged commit | 0 | 2 h | R5 | owner |
| S12 | `deliverables` blob container (rendered artefacts in transit), Logic Apps runtime storage | Storage `{baseName}sa` (ZRS) | T | ZRS; blob soft delete 14 days (delta D-BDR-B1) — the same bytes exist in SharePoint once uploaded | re-run | — | R1 | owner |
| S13 | Entra groups, PIM policies, CA policy, access packages | Entra ID | M | tenant-managed; definition of record `../team/least-privilege/entra/groups.json`, `rbac.bicep`, `entra-groups.md` | 0 | 1 business day (IAM team) | R7 | `{group:iam-admins}` |
| S14 | Graph consents, `Sites.Selected` grants (three app identities) | Entra / SharePoint | M | recorded in `../team/ACCESS_REGISTER.md`; re-granted per `../team/sharepoint-permissions.md` §3 | 0 | 1 business day | R7 / R8 | IAM + owner |
| S15 | Copilot Studio agent | `{env:infosec-foundry}` | B | solution export `Governance/Releases/infosec-foundry-copilot-{release}.zip` at every release (`LIFECYCLE.md` V15) | one release | 4 h | R5 | owner |
| S16 | Bing grounding resource + key, RAI policy, model deployments, diagnostic settings, alerts, budget | RG `rg-infosec-foundry` | G | Bicep (`infra/main.bicep`, `operations/alerts.bicep`) | 0 | 2 h | R7 | owner |
| S17 | Comparison set (inputs + known-good baselines) | `Governance/ComparisonSet/` | M | as S6 | minutes | 4 h | R3 | owner |
| S18 | Operations evidence, backups folder, releases | `Governance/Operations/`, `Governance/Backups/`, `Governance/Releases/` | M | as S6 | minutes | 4 h | R3 | owner |

Data protection of backups: the memory export contains team facts about
suppliers (classification internal, no special-category data by charter —
`../team/TEAM_MODEL.md` §13). It is filed under `Governance/Backups/`,
which inherits the `Governance/` permissions (users Read, owner Edit,
readers Read) and the site sensitivity label; the optional blob copy sits
in the EU storage account with identity-based access only
(`allowSharedKeyAccess: false`, delta D-B4) and the owner's PIM `Storage
Blob Data Reader`. Retention of a backup = the retention of the notes it
contains (§13: supplier facts until exit + 1 year; decisions 5 years); a
backup older than 24 months is deleted at the quarterly review unless it
is the last one. Control: A.8.13 (backups protected like the source),
A.8.10; GDPR Art. 5(1)(e).

## 2. Recovery objectives

| Scenario | RPO | RTO | Who declares | Rationale |
|---|---|---|---|---|
| Single agent / vector store corrupted or hand-edited | 0 | 1 h (`create_agents.py --only`) | owner | drift alert → rebuild (RUNBOOK FM-15) |
| All agents / stores lost (project reset, SDK regression) | 0 (git) + memory ≤ 24 h | 4 business h | owner | `deploy.sh` + R2 |
| Memory store lost or polluted | ≤ 24 h automated / ≤ 7 days manual | 2 h | owner | S4 |
| Report file deleted / overwritten in SharePoint | minutes | 4 business h | owner | versioning + recycle bin |
| Key Vault secret deleted | 0 | 1 h (recover) · 1 business day (re-issue) | owner + custodian | soft-delete |
| Logic Apps / Function app deleted | 0 | 2 h | owner | Bicep + config-zip + image |
| Resource group deleted | 0 (git) + memory ≤ 24 h + logs lost (unless D-BDR-B2) | 1 business day | owner, line manager informed | R7 |
| **Azure region unavailable** | memory ≤ 24 h; logs of the outage window; in-flight runs | **2 business days** to run in another EU region (decision point at 8 business hours, §5) | owner (P1) | the platform is an internal ICT service; the team continues manually on SharePoint records meanwhile |
| Tenant-level outage (Entra, SharePoint, Graph) | n/a | Microsoft | — | out of scope; DORA major-incident path via the group process |

RTOs assume the owner or deputy is available (`../team/TEAM_MODEL.md`
§12.3 break-glass covers absence) and that the deploy pipeline works; the
manual path (owner PIM `Contributor` + `Foundry Owner`) is the
fallback and doubles the RTO. Control: DORA Art. 11(1)–(2), 12(2)–(3);
A.5.30.

## 3. Backup procedures

| # | What | How | When | Evidence |
|---|---|---|---|---|
| B1 | Memory store + vector-store inventory | `python3 operations/backup_vector_stores.py --out operations/backups/{yyyy-mm-dd}` (standing `Foundry User` data-plane read is enough — the owner's own `az login`; no PIM). Output: `manifest.json` (every `vs-*` store, its file ids, names, sizes, SHA-256 of downloaded notes), `memory/*.txt` (the notes), `README.txt` (restore steps). Upload the folder to `Governance/Backups/{yyyy-mm-dd}/` (owner Edit on `Governance/`) or add `--upload-account {baseName}sa` for the EU `backups` container; the nightly Container Apps Job (`backup-job.bicep`: system MI with `Foundry User` on the project + `Storage Blob Data Contributor` on that one container, image = the kit image with `azure-storage-blob`) runs the same command unattended — no CI runner outside the EU ever holds a note | nightly (job), weekly W8 (manual verification), before every non-dry `deploy.sh` (D-LC-D1) | manifest present; `backup_age_days` KPI R11 (`KPIS.md`) ≤ 1 (automated) / ≤ 7 (manual) |
| B2 | Drift baseline | `build/manifest.json` → `build/baseline-{date}.json` (`CHANGE_MANAGEMENT.md` §7) | every successful deploy | file in `Governance/Operations/baselines/` |
| B3 | Copilot solution export | Copilot Studio → export solution → `Governance/Releases/` | every release with instruction changes | zip present |
| B4 | Key Vault | nothing to export: soft-delete + purge protection on (`main.bicep`); `access-review.sh --quick` lists names and dates | continuous | W6 |
| B5 | SharePoint site | versioning ≥ 50 major versions on `Reports/`, `Templates/`, `Governance/` (`../team/sharepoint-permissions.md` §2); Microsoft 365 Backup policy for the site `{to-confirm}` | continuous | quarterly access review item 5 (site settings export) |
| B6 | Logs / evidence export | optional Log Analytics data export rule for `LogicAppWorkflowRuntime`, `AppDependencies`, `AzureDiagnostics`, `AzureActivity` to the `backups` container (D-BDR-B2) when the ISMS record schedule exceeds 365 days or requires custody outside the workspace | continuous | export rule present in `what-if` |
| B7 | Git | GitHub is the system of record; the owner's clone and the deploy runner are independent copies; branch protection prevents history rewrite | continuous | quarterly access review item 9 |

Backups are read-only actions; the only write is the upload of the export
folder to `Governance/Backups/` or the `backups` container, both inside
the EU tenant boundary. Nothing is backed up to a workstation for longer
than the upload takes. Control: A.8.13; DORA Art. 12(1)–(2) (backup
policies, segregated from the source system — SharePoint / storage vs
Foundry).

## 4. Restore procedures

Every restore is an incident or a change (`RUNBOOK.md` §3, `CHANGE_MANAGEMENT.md`
§8 when emergency): ticket first, PIM with the ticket id, evidence after.

| # | Scenario | Steps | Access | Verify |
|---|---|---|---|---|
| R1 | Agent / vector store drift, corruption, deletion; failed run | `python3 scripts/convert_skills.py && python3 scripts/verify_conversion.py` → `python3 scripts/create_agents.py --only <agent>` (or `create_delivery_agents.py --only`) → `attach_integrations.py --only <agent>` → `apply_advisory_profile.py` if advisory → `create_orchestrator.py` to re-wire | owner PIM `Foundry Owner` (or the pipeline: re-run `deploy.sh`) | RUNBOOK H8 (only that agent differs), W1–W3 |
| R2 | Memory store lost, recreated empty, or polluted | 1. `memory_store.py list` — record what is there; 2. if polluted: delete offending notes (author, else `MEMORY_DELETE` Tier C); 3. if lost: `python3 operations/backup_vector_stores.py --restore operations/backups/{date} --ticket {jira:INFOSEC-PLAT}-nnn --confirm` — re-adds every note whose SHA-256 is absent from the live store (idempotent, skips duplicates); 4. record the restored note count in the ticket; inform the DPO if notes were lost between backup and restore (RoPA integrity) | owner standing `Foundry User` (the restore writes only to the memory store, which every user may write to by charter). Because it is a bulk write on others' behalf it is a recorded **Tier C** act: the owner requests, the **deputy approves** the ticket (requester exclusion, `TEAM_MODEL.md` §12.2), and the approved ticket id is the `--ticket` value | `memory_store.py list` count = manifest count; advisor answers a known memory query (`search_memory`) |
| R3 | SharePoint file / folder deleted, wrong version stored | version history → restore previous version; recycle bin (first stage by the owner, second stage by `{group:spo-admins}`); site-collection restore only for wide loss (spo-admins, RTO 1 business day). A *corrected* report is a new pipeline run (users hold Read on `Reports/` — `TEAM_MODEL.md` §9), never a manual upload | owner (Contribute, no delete) / spo-admins | file present with expected version; `{list:ApprovalDecisions}` row matches; share link still organisation-scoped |
| R4 | Key Vault secret deleted / rotated by mistake | `az keyvault secret recover` (soft-delete, 90 days) → connection re-test; if unrecoverable, custodian issues a new token (`TEAM_MODEL.md` §10, F8) → new secret version → connection re-pointed | owner PIM `Key Vault Secrets Officer` 2 h + custodian | W4 connections green; `keyvault-human-secret-read` alert reconciled with the ticket |
| R5 | Logic Apps app, workflow, Function app or Copilot agent lost | Bicep module redeploy (pipeline) → `build_logicapps.py` + `ci/deploy_logicapps.sh` (config-zip) → `az acr build` (or re-tag) + `deliveryImage` param → Copilot: import the last solution zip and re-share to `sg-infosec-foundry-users` only | deploy SP via pipeline; owner PIM only if the pipeline is down | one pipeline to the verifier (no approval); `report-status.json` answers; Copilot answers with the same persona |
| R6 | Log Analytics workspace lost | not restorable in place; evidence for the lost window comes from B6 exports, SharePoint decision records (S7), GitHub logs and PIM audit; redeploy via Bicep, re-run D-OPS-B2 diagnostic settings, RUNBOOK H9 | pipeline | alerts fire on synthetic test (`egress-detection.kql` with a test marker in `dev`) |
| R7 | Resource group lost (or new subscription) | `../team/TEAM_MODEL.md` §18 bootstrap in order: groups/PIM/CA exist (S13) → `setup/provision.sh` → `provision_identity.sh --apply` + `rbac.bicep` → **new managed identities**: IAM re-consents Graph permissions and re-grants `Sites.Selected` to the three new app identities (`sharepoint-permissions.md` §3) — record new ids in `ACCESS_REGISTER.md` → custodians re-place tokens in the new Key Vault → owner recreates `conn-*` → `deploy.sh` → R2 memory restore → R5 workflows/functions/Copilot → `access-review.sh` full run → new baseline | owner PIM `Contributor` (line-manager approval) + IAM + custodians | `deploy.sh` step 7 smoke test; comparison set on every pipeline; access review sign-off (Q0 baseline) |
| R8 | Region failure | §5 | as R7 | as R7 |

Control: A.8.13 (restore tested), A.8.14; DORA Art. 12(3) (restoration
procedures documented, tested); ISO 42001 A.6.2.5.

## 5. Region-failure playbook

Facts that shape it: the Foundry basic agent setup keeps agents, threads,
files and vector stores in Microsoft-managed storage of the one deployment
region (`../infra/README.md` "Residency") — there is no cross-region
replica of agent state; Log Analytics, Key Vault, storage (ZRS = zonal,
not regional), Logic Apps and Functions are in the same region; Entra ID,
SharePoint, Teams, Graph and GitHub are not affected by an Azure regional
outage. The alternative regions are the EU allow-list in `main.bicep`
(`@allowed`), constrained by model availability on the EU Data Zone SKU.

| # | Phase | Action | Who | Time box |
|---|---|---|---|---|
| 1 | Detect | Azure Service Health regional advisory, or `RUNBOOK.md` H1/H5 failing platform-wide (`AppRequests` empty, ARM timeouts). Alerts are **silent** during the outage (the workspace is in the region) — H-checks are manual | owner / any user | 0–1 h |
| 2 | Declare | P1 (`RUNBOOK.md` §3); ticket; Teams post to `{teams:infosec-assurance-platform}`: platform unavailable, use SharePoint records, no manual uploads to `Reports/`; line manager and `{group:azure-platform}` informed; DORA major-incident assessment through the group process (an internal ICT service outage without client impact rarely qualifies — record the assessment) | owner (deputy via break-glass if absent) | ≤ 1 h |
| 3 | Decide | At **8 business hours** without a Microsoft ETA inside the 2-business-day RTO: relocate. Else: wait and re-assess every 4 h. Decision and rationale in the ticket | owner + line manager | 8 h |
| 4 | Prepare | Choose `AZURE_LOCATION` from the allow-list where `az cognitiveservices model list -l {region}` shows the three pinned models on `DataZoneStandard`; set `.env` and a `main.parameters.dr.json` (copy of prod with the new location, `baseName` suffix `-dr`); landing zone provides VNet/private DNS in the new region if `enablePrivateNetworking` is on (`{group:azure-platform}`) | owner, LZ | 2 h |
| 5 | Rebuild | R7 in the new region: `provision.sh` → `rbac.bicep` → **new MIs**: IAM re-consent + `Sites.Selected` re-grant (two-person control stays: owner cannot grant Graph consent himself) → custodians place tokens → `conn-*` → `deploy.sh` (pipeline with a temporary `production-dr` environment, same OIDC SP) → R2 from the latest `Governance/Backups/` (SharePoint is unaffected, so the backup is reachable) → workflows + functions + alerts → MCP endpoint / Copilot connector re-pointed (`PROJECT_ENDPOINT` changes) | owner (PIM), IAM, custodians, deploy SP | ≤ 1 business day |
| 6 | Verify | `deploy.sh` step 7 smoke; W1–W6; one Tier A pipeline end-to-end with a synthetic supplier to the verifier (gate rejected, nothing stored); `access-review.sh` full run filed as the DR baseline; egress detector confirmed on the new workspace (H9) | owner + deputy (independent check) | 2 h |
| 7 | Resume | Teams post; users re-register the local MCP endpoint (`../mcp-server/README.md`); pending approvals from before the outage are **expired by design** — requesters re-run (`HUMAN_APPROVAL.md`); memory notes written between the last backup and the outage are re-entered by their authors from thread exports if any survive, else accepted as lost and noted to the DPO | owner | — |
| 8 | Fail back | When the home region returns: decide within 5 business days whether to keep the DR region (it is equally EU-resident — a permanent move is a `main.parameters.prod.json` change, Tier C, *major* release) or to fail back by running §5.5 in reverse from a fresh memory export; never run both regions with users on each (two memory stores diverge) | owner + line manager | 5 business days |
| 9 | Close | Post-incident note (`RUNBOOK.md` §6): lost window, data lost (memory notes, in-flight runs), identities created/removed, secrets re-issued (old ones **disabled** by custodians once the home Key Vault is reachable), `ACCESS_REGISTER.md` updated, old RG decommissioned per `LIFECYCLE.md` §6 after the log export | owner | 5 business days |

Least-privilege notes for DR: the DR build uses the same groups, the same
PIM roles and the same deploy SP — no standing rights are added for the
emergency; break-glass (deputy) can *build* under its role set but still
cannot approve anything; the two-person control on integrations (owner
Foundry-side, custodian target-side) is preserved because tokens are
re-issued by custodians, never copied by the owner; the old region's Key
Vault keeps the old secret versions under purge protection until they are
disabled. Control: A.5.29, A.5.30, A.8.14; DORA Art. 11(1), 11(3) (test
of recovery plans), 12(2) (restoration in a secondary environment segregated from the primary);
NIS2 Art. 21(2)(c).

## 6. Testing and evidence

| Test | Cadence | Procedure | Pass | Evidence |
|---|---|---|---|---|
| Backup integrity | weekly (W8) | open the latest `manifest.json`; count of memory notes = `memory_store.py list` count; spot-check one note's SHA-256 | equal; hash matches | W8 log line in `Governance/Operations/{yyyy}-{mm}/` |
| Memory restore | semi-annual (`CHANGE_MANAGEMENT.md` §9, delta D-LC-C1) | in `dev` with **synthetic** data only (`LIFECYCLE.md` §7 — production notes never enter `dev`): seed `dev`'s own `vs-assurance-memory` with three synthetic notes, export it, delete the store, recreate it empty (`create_orchestrator.py`), `--restore`, run `search_memory` for the three facts | 3/3 found; note count equal | `Governance/Operations/dr-test-{date}.md` |
| Agent rebuild | semi-annual | in `dev`: delete two agents and their stores, run `deploy.sh`, H8 shows them restored to baseline hashes | hashes equal | same note |
| SharePoint restore | annual | restore a deleted synthetic report from the recycle bin and a previous version of a `Governance/` file | restored within RTO | same note |
| Key Vault recover | annual | delete and recover a **test** secret `kv-dr-test` | recovered; connection unaffected | same note |
| Region relocation (tabletop) | annual, and after any change to `main.bicep` regions/models | walk §5 with the landing-zone team and IAM; confirm model availability in the chosen DR region; confirm re-consent lead time | written confirmation of steps 4–5 feasibility | `Governance/Operations/dr-tabletop-{date}.md`; DORA Art. 11(6) input to the group ICT continuity testing |
| Full DR build (optional) | when the landing zone offers a second EU region and the ISMS requires it | execute §5.4–5.6 in `dev` | RTO met | same |

Findings from any test become backlog items (`CONTINUOUS_IMPROVEMENT.md`
§2) and, when a control failed, corrective actions (ISO 27001 cl. 10.2).
Control: A.8.13, A.8.14; DORA Art. 11(4), 11(6), 12(3); ISO 42001 cl. 10.2.

## 7. Shared deltas needed by this file (not applied here)

| Id | Target | Location | Literal text |
|---|---|---|---|
| D-BDR-B1 | `infra/main.bicep` | `blobService.properties` and after the `deliverables` container | `deleteRetentionPolicy: { enabled: true, days: 14 }` / `containerDeleteRetentionPolicy: { enabled: true, days: 14 }` and `resource backups 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = { parent: blobService, name: 'backups', properties: { publicAccess: 'None' } } // memory-store exports + evidence (operations/BACKUP_DR.md §3)` |
| D-BDR-B2 | `infra/main.bicep` | after `logAnalytics` (optional; `param enableLogExport bool = false`) | `resource logExport 'Microsoft.OperationalInsights/workspaces/dataExports@2023-09-01' = if (enableLogExport) { parent: logAnalytics, name: 'evidence-export', properties: { enable: true, tableNames: [ 'LogicAppWorkflowRuntime', 'AppDependencies', 'AzureDiagnostics', 'AzureActivity' ], destination: { resourceId: storage.id } } } // ISMS record schedule > 365 d (operations/BACKUP_DR.md S10)` |
| D-BDR-B3 | `infra/main.bicep` | after the `mcp` module | `@description('Deploy the nightly EU memory-store backup job (operations/backup-job.bicep)') param enableBackupJob bool = false` and `module backupJob '../operations/backup-job.bicep' = if (enableBackupJob) { name: 'backup-job' params: { baseName: baseName, location: location, projectEndpoint: project.properties.endpoints['AI Foundry API'], projectName: project.name, jobImage: mcpImage, registryServer: '', containerAppsEnvironmentId: enableMcpHosting ? mcp.outputs.environmentId : '', logAnalyticsName: logAnalytics.name, backupContainerName: 'backups' } dependsOn: [ backups ] }` (adjust the endpoint expression / `environmentId` output name to what `mcp-server.bicep` exposes); `main.parameters.prod.json`: `"enableBackupJob": { "value": true }` |
| D-BDR-RQ1 | `mcp-server/requirements.txt` (the image `backup-job.bicep` runs) | end | `azure-storage-blob==12.24.0   # operations/backup_vector_stores.py --upload-account (BACKUP_DR.md B1)` — and the image must copy `operations/backup_vector_stores.py` to `/app/operations/` |
| D-BDR-T1 | `team/TEAM_MODEL.md` | §5 additions ledger, after L16 | `\| L17 \| backup job MI (\`{baseName}-job-backup\`, only if deployed) \| \`Foundry User\` (project); \`Storage Blob Data Contributor\` on the \`backups\` container \| nightly memory-store export inside the EU boundary (\`../operations/BACKUP_DR.md\` B1) \| managed identity; no KV, no SharePoint, no AI Developer \|` and a matching row in `ACCESS_REGISTER.md` Non-human identities |
| D-BDR-RB1 | `operations/RUNBOOK.md` | "Weekly (owner)" table, after W7 | `\| W8 \| Backup integrity \| latest \`operations/backups/{date}/manifest.json\` (or \`backups/{date}\` blob) vs \`memory_store.py list\` count; age ≤ 1 day when the nightly job runs, ≤ 7 days otherwise (\`BACKUP_DR.md\` §6) \| counts equal; age within target \|` |
| D-BDR-RA1 | `team/RACI.md` | row R23 description | append ` — procedures: ../operations/BACKUP_DR.md (inventory §1, RPO/RTO §2, restore §4, region failure §5, tests §6)` |
| D-BDR-E1 | `setup/.env.example` | end | `# --- Backup / DR (operations/BACKUP_DR.md) ---` / `BACKUP_OUT_DIR=../operations/backups` / `BACKUP_STORAGE_ACCOUNT=<baseName>sa` / `BACKUP_CONTAINER=backups` |
| D-BDR-P1 | `governance/DATA_PROTECTION_GUARDRAILS.md` | §4 Auditability, end | ` Backups of the shared memory store are dated read-only exports filed under Governance/Backups/ (and the EU storage container backups/), protected like the source and retained per the note retention — operations/BACKUP_DR.md §1.` |
| D-BDR-GI1 | `.gitignore` (convertion) | end | `operations/backups/` (exports are filed in SharePoint / blob, never committed) |
