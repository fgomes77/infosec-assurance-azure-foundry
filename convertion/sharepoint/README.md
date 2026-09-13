# SharePoint Delivery Module — Supplier/Service Folder Taxonomy

All generated deliverables are stored in the Euronext InfoSec Assurance
SharePoint site under a fixed, idempotent taxonomy. This module documents
the rules; the executable implementation is the Azure Function in
`../functions/delivery/` (called by every Logic App pipeline in
`../workflows/`), and the read surface agents use is
`../integrations/openapi/sharepoint-graph.yaml`.

## Site and libraries

| Purpose | Path (site-relative) | Used by |
|---|---|---|
| Generated assessment reports | `Reports/<Supplier>/<Service>/` | pipelines a, c, d, d2, e, f |
| DPO deliverables | `Reports/DPO/<Supplier>/<Service>/` | pipeline b |
| Evidence repository (read-only input) | `Infosec Assurance/GRC/TPA/Active/<Supplier>[/<Service>]/` | tpa-evidence-analyzer (d2) |
| Template library (managed by req. j) | `Templates/` | template-manager |
| Advisory deliverables (g/h, living documents) | `Advisory/<Framework-or-Topic>/<Subtopic>/` | pipeline `advisory-file-delivery` (`SHAREPOINT_ADVISORY_ROOT_ITEM_ID`) |
| Threat-intel briefs not tied to a vendor | `Reports/General/Threat-Intel/` | pipeline `cyber-forum-brief` |
| Evidence received by e-mail | `Infosec Assurance/GRC/TPA/Inbox/<Supplier>/<Service>/` | workflow `mailbox-intake` (a human moves it to `TPA/Active/`) |
| Personal morning briefs | the user's own OneDrive `/Morning Brief/` (7-day retention) | workflow `morning-brief` |

Configure the actual site id and library root once in
`../setup/.env` (`SHAREPOINT_SITE_ID`, `SHAREPOINT_REPORTS_ROOT_ITEM_ID`); the
Function and the workflows read them from parameters — no hard-coded ids.

## The folder rule (verbatim requirement)

> Ask the user the name of the supplier and the service name and store the
> report in the supplier folder and under it in the folder service name.
> If the supplier name folder exists don't create a new one, and if the
> service name folder under the supplier folder doesn't exist, create a
> new folder under the supplier.

Implementation (`functions/delivery/function_app.py::ensure_folder`):

```
ensure_path(driveId, root, [Supplier, Service]):
  parent = root
  for segment in [Supplier, Service]:
    GET /drives/{driveId}/items/{parent}:/{segment}
      200 -> reuse existing folder (NEVER create a duplicate)
      404 -> POST /drives/{driveId}/items/{parent}/children
             { "name": segment, "folder": {},
               "@microsoft.graph.conflictBehavior": "fail" }
             409 (lost a concurrent race) -> re-GET and reuse
    parent = folder.id
  return parent
```

Properties this guarantees:

- **Idempotent** — running any pipeline twice never duplicates folders.
- **Race-safe** — `conflictBehavior: fail` + re-read handles two pipelines
  delivering to the same new supplier simultaneously.
- **Name normalisation** — supplier/service names are trimmed and the
  Graph-illegal characters `" * : < > ? / \ |` are replaced with `-`
  before lookup, so "Acme Corp." and "Acme Corp. " land in one folder.
  Matching is case-insensitive (SharePoint folder names are).

## HTML dashboards in the Reports library

The DeepSearch and CISO executive-summary dashboards are stored as
**self-contained `.html` files**. SharePoint serves an `.html` file as a
download rather than rendering it inline; that is the accepted default —
the downloaded file is byte-identical to the artefact the agent produced and
opens locally with no network access. Rendered hosting is optional
(`../infra/static-web-app.bicep`, `enableStaticWebApp`: an EU-region Azure
Static Web App with Entra Easy Auth serving approved dashboards from the
deliverables container — **not deployed by default**). Registered HTML
templates must therefore never reference a CDN script (Chart.js and any
other vendor library is inlined), so the file opens offline and no Euronext
data is fetched from the web.

Naming convention mapping: the claude.ai-era Google Drive path
`TPA Ai/{Supplier}/TPSRCA_*.html` maps to
`Reports/<Supplier>/<Service>/DeepSearch_*.html` here.

## Lists written only by the delivery Function

Both lists live on the same site and are written **exclusively by the
delivery Function's managed identity, after the human approval gate** — no
Logic App connector and no agent can write to them.

| List | Columns |
|---|---|
| `TPRM Portfolio` | `SupplierName`, `ServiceName`, `TPAStatus` (`Ongoing` \| `Complete`), `LastDeepSearchUrl`, `LastCisoDeckUrl`, `UpdatedBy`, `UpdatedAt` — upserted on `SupplierName`+`ServiceName` by `POST /api/portfolio_update` |
| `TPSRCA History` | `SupplierName`, `ServiceName`, `AssessmentDate`, `Composite`, `ReportType`, `ReportUrl`, `RunId` — append-only via `POST /api/history_append` |
| `TPA Evidence Cache` | `CacheKey` (`<driveId>\|<itemId>`, indexed), `DriveId`, `ItemId`, `ETag`, `FileName`, `Facts` (multi-line text: the extracted JSON), `ExtractorRef`, `RunId`, `StoredAt` — upserted on `CacheKey` by `POST /api/evidence_cache` **after approval only**; read by the analyzer through the read-only `GET /api/evidence_cache` |

**Why the evidence cache exists.** The TPA evidence analysis is the heaviest
recurring run in the platform: a whole supplier tree read on the reasoning tier
with the chunked full-coverage method. Between two assessments almost none of
those files change, yet every reassessment re-read all of them. The cache turns
that into a delta — the analyzer asks, per file, what a previously approved run
extracted, and reads in full only what the eTag says actually moved.

Three invalidations keep it honest: a changed eTag (the file was edited or
replaced), a changed `ExtractorRef` (a new charter version reads documents
differently), and age (`EVIDENCE_CACHE_MAX_AGE_DAYS`, so nothing is trusted
indefinitely). **No time-dependent value is ever cached**: VALID / EXPIRING ≤90
days / EXPIRED / period-gap are recomputed against each report date, because a
certificate valid in March is not valid in September. Every inventory row says
`fresh` or `reused:<runId>`, so the approver signs off on evidence whose
provenance they can see.

The `Supplier Watchlist` list (read by `workflows/scheduled-deepsearch.json`)
carries `SupplierName`, **`ServiceName`** (text) and **`Active`** (Yes/No) in
addition to its existing columns; the Logic App reads it and never writes it.

## File naming

`<ReportType>_<Supplier>_<Service>_<YYYY-MM-DD>.<ext>` — e.g.
`DeepSearch_AcmeCorp_ManagedSOC_2026-09-12.html`. A same-day rerun uploads
with `@microsoft.graph.conflictBehavior: replace` (the report of record is
the latest approved version; SharePoint versioning preserves history).

## Sharing

After upload the pipeline creates an organisation-scoped view link
(`POST /drives/{driveId}/items/{itemId}/createLink` with
`{"type": "view", "scope": "organization"}`) and returns it to the caller
and to the Teams notification. No anonymous links, ever.

## Permissions

**Google Drive → SharePoint (Graph) mapping.** Agents are read-only
(`Sites.Selected` read: `listDrives`, `listChildren`, `listChildrenByPath`,
`getItemByPath`, `driveSearch`, small-file download); the delivery Function's
managed identity is the only writer (`Sites.Selected` write); share links are
organisation-scoped view links; the DPO library `Reports/DPO/` carries unique
permissions (DPO Visitors read, delivery MI write, no agent access).

The delivery Function's managed identity is the ONLY writer
(`Sites.Selected` granted write on the InfoSec Assurance site). Agents hold
read-only Graph tools (non-GET operations stripped by
`attach_integrations.py`), so no agent can write to SharePoint directly —
writes happen exclusively after the verifier PASS and the human approval
gate in the Logic App pipelines. This is the same three-layer control as
`../governance/HUMAN_APPROVAL.md`.

The same managed identity also carries `InformationProtectionPolicy.Read.All`
and the metered-API approval for `driveItem:assignSensitivityLabel`, so the
Function's `/api/assign_label` endpoint can apply the per-report **Purview
sensitivity label** right after the upload (finding C16). The per-file label
supplements, and does not replace, the Reports library's default label: when
no `sensitivity_label` is configured for the report type
(`../templates/registry.json`) and `SHAREPOINT_SENSITIVITY_LABEL_ID` is empty,
the pipeline skips the call and the library default stands. Labelling is a
write, so it stays with the one writer — no agent and no Logic App connector
ever labels a file.

**Bootstrap.** `../scripts/sharepoint_bootstrap.py` (see
`../functions/delivery/README.md`) performs the `Sites.Selected` grant and
prints `SHAREPOINT_SITE_ID`, `SHAREPOINT_REPORTS_DRIVE_ID`,
`SHAREPOINT_REPORTS_ROOT_ITEM_ID`, `SHAREPOINT_DPO_ROOT_ITEM_ID`,
`SHAREPOINT_ADVISORY_ROOT_ITEM_ID` and `SHAREPOINT_TEMPLATES_REVIEWS_ITEM_ID`
for `../setup/.env`.

Per-user site roles for the five assurance users, the owner and the DPO, the
custom "Contribute (no delete)" level, the unique permissions on `Reports/`,
`Templates/` and `Governance/`, and the grant/list/revoke commands for the
three `Sites.Selected` identities: `../team/sharepoint-permissions.md`.

## `{list:PlatformFeedback}` (learning loop)

A SharePoint list on the same site, with columns mirroring
`../enterprise/memory/feedback-schema.json`:

`id`, `timestamp`, `source`, `submitted_by`, `channel`, `agent`,
`agent_version`, `pipeline`, `requirement`, `run_id`, `conversation_id`,
`category`, `thumbs`, `rating`, `verdict`, `finding_code`, `description`,
`severity`, `ai_concern`, `triage_status`, `ticket`, `retain_until`.

Read/write for `sg-infosec-foundry-users`. **No report content and no personal
data** — identifiers and generic descriptions only (`learning_loop.py` masks
e-mail/IP/secret-like strings and flags the record). Retention 24 months
(`retain_until`). Exported monthly to
`build/learning/inbox/feedback-{yyyy-mm}.json` for
`../enterprise/memory/learning_loop.py`.
