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

Configure the actual site id and library root once in
`../setup/.env` (`SHAREPOINT_SITE_ID`, `SHAREPOINT_REPORTS_ROOT`); the
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

Per-user site roles for the five assurance users, the owner and the DPO, the
custom "Contribute (no delete)" level, the unique permissions on `Reports/`,
`Templates/` and `Governance/`, and the grant/list/revoke commands for the
three `Sites.Selected` identities: `../team/sharepoint-permissions.md`.
