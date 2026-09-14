# SharePoint Permissions — Site Roles for the Five, `Sites.Selected` for the App Identities

Executable companion to `TEAM_MODEL.md` §8 (Graph application
permissions) and §9 (site roles) for the InfoSec Assurance site
`{sharepoint:infosec-assurance}` whose taxonomy is fixed in
`../sharepoint/README.md` (`Reports/<Supplier>/<Service>/`,
`Reports/DPO/<Supplier>/<Service>/`, `Infosec Assurance/GRC/TPA/Active/`,
`Templates/`). Site ids come from `../setup/.env` (`SHAREPOINT_SITE_ID`,
`SHAREPOINT_REPORTS_DRIVE_ID`, `SHAREPOINT_REPORTS_ROOT_ITEM_ID`,
`SHAREPOINT_DPO_ROOT_ITEM_ID`, `SHAREPOINT_TPA_ACTIVE_PATH`). Run by the
owner as site owner (§2, §4) and by `{group:spo-admins}` / `{group:iam-admins}`
where tenant rights are needed (§3). Placeholders throughout.

Principle: humans **read** reports of record; the delivery Function's
managed identity is the **only writer**; agents read through the Foundry
project managed identity; every grant is on this one site
(`Sites.Selected`), never tenant-wide.

## 1. Human roles — the five and the supporting groups

Permission is granted to Entra groups only (`entra-groups.md`); no person
is added to a SharePoint group individually. The five assurance users have
**identical** rights; the owner differs only as site owner.

| Principal | SharePoint group / level | Site root | `Reports/` | `Reports/DPO/` | `GRC/TPA/Active/` | `Templates/` (+ `Reviews/`) | `Governance/` |
|---|---|---|---|---|---|---|---|
| `{upn:jose.mogollon}`, `{upn:pedro.santos}`, `{upn:jose.meireles}`, `{upn:tania.morais}`, `{upn:francisco.gomes}` — via `sg-infosec-foundry-users` | Members → **Edit** on the root | Edit | **Read** (unique) | Read (unique) | Edit (pre-existing evidence duty) | Read (unique) | Read (unique) |
| `{upn:francisco.gomes}` — via `sg-infosec-foundry-owner` | Site Owners → Full Control; custom level `Contribute (no delete)` on `Reports/` | Full Control | Contribute (no delete) | Contribute (no delete) | Edit | Edit | Edit |
| `{group:spo-admins}` | Site Owners (site-collection backup) | Full Control | — | — | — | — | — |
| `{group:dpo}` | Visitors on `Reports/DPO/` only | — | — | Read | — | — | — |
| `sg-infosec-foundry-readers` | Visitors | Read | — | — | — | — | Read |

Why Members are Read on `Reports/`: a report of record is never edited by
hand — a correction is a new pipeline run, and versioning keeps history
(ISO 27001:2022 A.5.12, A.8.3; DORA Art. 28 evidence). Why the owner is
Contribute without delete: he may re-file or annotate but never remove a
version (A.8.10 — deletion is a governed act, not a click).

## 2. Configure the site (PnP PowerShell, run as site owner)

```powershell
Connect-PnPOnline -Url "https://{tenant}.sharepoint.com/sites/{sharepoint:infosec-assurance}" -Interactive

# 2a. Site groups ← Entra groups (claims form c:0t.c|tenant|<objectId>)
$users   = "c:0t.c|tenant|{objectId:sg-infosec-foundry-users}"
$owner   = "c:0t.c|tenant|{objectId:sg-infosec-foundry-owner}"
$readers = "c:0t.c|tenant|{objectId:sg-infosec-foundry-readers}"
$dpo     = "c:0t.c|tenant|{objectId:dpo}"
Add-PnPGroupMember -Group "InfoSec Assurance Members"  -LoginName $users
Add-PnPGroupMember -Group "InfoSec Assurance Owners"   -LoginName $owner
Add-PnPGroupMember -Group "InfoSec Assurance Owners"   -LoginName "c:0t.c|tenant|{objectId:spo-admins}"
Add-PnPGroupMember -Group "InfoSec Assurance Visitors" -LoginName $readers

# 2b. Custom permission level for the owner on reports of record
Add-PnPRoleDefinition -RoleName "Contribute (no delete)" -Clone "Contribute" `
  -Exclude DeleteListItems, DeleteVersions -Description "TEAM_MODEL.md §9 / L9"

# 2c. Break inheritance where report-of-record integrity requires it (and nowhere else)
$lib = "Documents"    # the library that holds Reports/, Templates/, Governance/ (SHAREPOINT_REPORTS_DRIVE_ID)
foreach ($f in @("Reports", "Reports/DPO", "Templates", "Templates/Reviews", "Governance")) {
  Set-PnPFolderPermission -List $lib -Identity $f -Group "InfoSec Assurance Members" -AddRole "Read" -RemoveRole "Edit"
}
Set-PnPFolderPermission -List $lib -Identity "Reports"     -Group "InfoSec Assurance Owners" -AddRole "Contribute (no delete)" -RemoveRole "Full Control"
Set-PnPFolderPermission -List $lib -Identity "Reports/DPO" -User  $dpo -AddRole "Read"
Set-PnPFolderPermission -List $lib -Identity "Governance"  -User  $readers -AddRole "Read"
# GRC/TPA/Active keeps inheritance (Members = Edit): evidence upload is the team's existing duty

# 2d. Versioning, labels, sharing
Set-PnPList -Identity $lib -EnableVersioning $true -MajorVersions 50 -EnableMinorVersions $false
Set-PnPList -Identity $lib -DefaultSensitivityLabelForLibrary "{label:confidential-internal}"
Set-PnPSite -DefaultSharingLinkType Internal -DefaultLinkPermission View -DisableSharingForNonOwners
```

`Set-PnPFolderPermission` breaks inheritance on the folder when it is
still inherited; confirm with `Get-PnPFolderPermission` (§5). Anonymous
links are disabled at tenant level (`../sharepoint/README.md` "Sharing");
the delivery Function creates organisation-scoped **view** links, and
`{"type":"view","scope":"users"}` addressed to `{group:dpo}` for
`Reports/DPO/` (delta D-F1).

## 3. `Sites.Selected` grants for the application identities

Exactly **three** grants exist on the site; no identity on the platform
holds `Sites.Read.All` or `Sites.ReadWrite.All` (ISO 27001:2022 A.8.3;
DORA Art. 9(4)(c)). Step 1 (IAM team): add the `Sites.Selected`
application permission to each managed identity's service principal and
grant admin consent — a managed identity has no app registration, so the
app role is assigned with Graph
(`POST /servicePrincipals/{miObjectId}/appRoleAssignments`, resource =
Microsoft Graph, app role `Sites.Selected`
`883ea226-0bf2-4a8f-9f9d-92c9162a727d`). Step 2 (owner, needs
`Sites.FullControl.All` on the granting principal or a SharePoint admin
running it): grant the per-site role below.

| Identity | Placeholder | Role on the site | Used for | Ledger |
|---|---|---|---|---|
| Delivery Function MI | `{mi:infosec-delivery-fn}` | **write** | `ensure_folder`, `upload`, `createLink` (`../functions/delivery/README.md`) — the single write path after verifier PASS + human approval | L13 |
| Foundry project MI | `{mi:infosecfoundry-proj}` | **read** | `sharepoint-graph` read tools; `tpa-evidence-analyzer` (d2) tree listing; template reads | L14 |
| Logic Apps MI | `{mi:infosecfoundry-la}` | **read** | `scheduled-deepsearch` watchlist list read | L12 |
| Logic Apps MI | same | write — **time-boxed exception** | two direct `PUT …/content` uploads in `onetrust-assessment-intake` and `scheduled-deepsearch` until delta D-W3 routes them through the Function; expiry date in `ACCESS_REGISTER.md` | L12x |

```bash
# Resolve the site id once (or take SHAREPOINT_SITE_ID from setup/.env)
SITE=$(az rest --method GET --url "https://graph.microsoft.com/v1.0/sites/{tenant}.sharepoint.com:/sites/{sharepoint:infosec-assurance}" --query id -o tsv)
# appId of a managed identity = its service principal's appId
FN_APP=$(az ad sp show --id "{principalId:mi-infosec-delivery-fn}" --query appId -o tsv)
PROJ_APP=$(az ad sp show --id "{principalId:mi-infosecfoundry-proj}" --query appId -o tsv)
LA_APP=$(az ad sp show --id "{principalId:mi-infosecfoundry-la}" --query appId -o tsv)

grant() {  # appId, displayName, role
  az rest --method POST --url "https://graph.microsoft.com/v1.0/sites/$SITE/permissions" --body "{
    \"roles\": [\"$3\"],
    \"grantedToIdentities\": [ { \"application\": { \"id\": \"$1\", \"displayName\": \"$2\" } } ] }"
}
grant "$FN_APP"   "infosec-delivery-fn"   write   # L13
grant "$PROJ_APP" "infosecfoundry-proj"   read    # L14
grant "$LA_APP"   "infosecfoundry-la"     read    # L12  (write only while L12x is open)

# List — the quarterly evidence (item 4): expect exactly three entries with the roles above
az rest --method GET --url "https://graph.microsoft.com/v1.0/sites/$SITE/permissions" \
  --query "value[].{id:id,roles:roles,app:grantedToIdentities[0].application.displayName,appId:grantedToIdentities[0].application.id}" -o table

# Change a role (e.g. L12x expiry: Logic Apps MI write -> read) or revoke (offboarding of an identity)
az rest --method PATCH  --url "https://graph.microsoft.com/v1.0/sites/$SITE/permissions/{permissionId}" --body '{"roles":["read"]}'
az rest --method DELETE --url "https://graph.microsoft.com/v1.0/sites/$SITE/permissions/{permissionId}"
```

Rules: a grant is created only after the ledger row exists
(`TEAM_MODEL.md` §5); a new grant, a role upgrade or a fourth identity is
a Tier C platform change; the Copilot connector runs delegated (OBO) and
therefore needs **no** application grant — the caller's own site rights
apply (`TEAM_MODEL.md` §11).

## 4. What agents can and cannot do on the site

| Path | Agents (project MI, GET-only tools) | Pipelines (Logic Apps MI) | Delivery Function MI | Humans |
|---|---|---|---|---|
| `Infosec Assurance/GRC/TPA/Active/<Supplier>[/<Service>]/` | list + download (d2) | — | — | Members upload evidence by hand |
| `Reports/<Supplier>/<Service>/` | read (cross-reference earlier reports) | list (watchlist) | ensure folder, upload, share link | read; owner contributes without delete |
| `Reports/DPO/<Supplier>/<Service>/` | read | — | upload, share link to `{group:dpo}` | read; DPO read |
| `Templates/`, `Templates/Reviews/` | read (template-manager analysis) | — | write review pages (j) | read; owner edits after Tier C approval |
| `Governance/` | none | — | — | read; owner edits; readers read |

Non-GET Graph operations are stripped from every agent tool by
`../scripts/attach_integrations.py` (`../governance/HUMAN_APPROVAL.md`
Layer 1); the table above is the credential-layer view of the same rule.

## 5. Verification and quarterly evidence (review item 4)

```powershell
# Site groups and their Entra members
Get-PnPGroup | ForEach-Object { $_.Title; Get-PnPGroupMember -Group $_ | Select-Object LoginName }
# Unique permissions per governed folder → site-permissions.json
foreach ($f in @("Reports","Reports/DPO","Templates","Templates/Reviews","Governance","Infosec Assurance/GRC/TPA/Active")) {
  Get-PnPFolderPermission -List "Documents" -Identity $f | Select-Object @{n="folder";e={$f}}, PrincipalName, PermissionLevels
}
Get-PnPList -Identity "Documents" | Select-Object EnableVersioning, MajorVersionLimit
```

Pass criteria: Members hold Read (not Edit) on the five governed folders;
Owners hold `Contribute (no delete)` on `Reports/`; `{group:dpo}` appears
only under `Reports/DPO/`; readers only on root Read and `Governance/`;
`GET /sites/{id}/permissions` returns exactly three application grants
with the roles of §3 (Logic Apps MI `read` once L12x has expired);
versioning on with ≥ 50 major versions. File the outputs as
`Governance/AccessReviews/{yyyy}-Q{n}/snapshot/site-permissions.json`
(`../operations/access-governance/scripts/access_snapshot.sh` collects the
Graph part).

## 6. Controls implemented here

| Control | Where |
|---|---|
| ISO 27001:2022 A.5.12, A.8.3 | unique Read on reports of record §1–§2; `Sites.Selected` per identity §3 |
| ISO 27001:2022 A.8.10, A.5.33 | no-delete owner level, versioning ≥ 50 §2 |
| ISO 27001:2022 A.5.15, A.5.18 | group-only membership §2; quarterly evidence §5 |
| DORA Art. 9(4)(c), Art. 28 | least-privilege app grants §3; reports of record preserved as evidence §2 |
| GDPR Art. 5(1)(f), 28 | DPO deliverables shared to the DPO group only §2–§4 |
| ISO 42001 A.9.2; EU AI Act Art. 14 | agents read, humans approve, one identity writes §4 |
