# Step 05 — SharePoint site and the delivery Function

**Objective.** Make the one InfoSec Assurance SharePoint site the system
of record for deliverables (`Reports/<Supplier>/<Service>/`,
`Reports/DPO/…`, `Infosec Assurance/GRC/TPA/Active/…`, `Templates/`,
`Governance/`), grant `Sites.Selected` **write** to the delivery
Function's managed identity and **read** to the Foundry project managed
identity, deploy the delivery Function (`functions/delivery/`) with the
byte-verified renderers, and capture the site/drive/item ids the
workflows need.

**Owner / effort.** `{upn:francisco.gomes}` with `{group:spo-admins}`;
3 days. Countersign: SPO admins. **Depends on** 02, 03.

## 1. Platform facts

| Fact | Status / source |
|---|---|
| The delivery Function is the **only** SharePoint writer; agents read through Graph with the project MI; writes occur only after verifier PASS + human approval | kit invariant — `sharepoint/README.md`, `governance/HUMAN_APPROVAL.md` |
| `Sites.Selected` grants are per site via `POST /sites/{siteId}/permissions` with `roles` `read` or `write` | kit — `functions/delivery/README.md`; `team/sharepoint-permissions.md` §3 |
| Sensitivity labels on generated files: Graph `driveItem: assignSensitivityLabel` is asynchronous, protected and metered (pay-as-you-go) — a library default label (PnP `DefaultSensitivityLabelForLibrary`) is the zero-cost route the kit already uses | [GA] https://learn.microsoft.com/en-us/graph/api/driveitem-assignsensitivitylabel (2026-08-19) |
| Code Interpreter runs Python only in ACA dynamic sessions with no outbound network; the pptx generators are Node — hence the Function carries Node 20 | [GA] https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/code-interpreter (2026-08-05) |
| Purview supports Foundry interactions (DSPM for AI, Audit, DLP prompt-blocking) — labels on SharePoint output are the ENX classification control | [GA] https://learn.microsoft.com/en-us/purview/ai-azure-foundry (2026-05-01) |

## 2. Click-path

**SharePoint admin center / site.** Active sites → `{sharepoint:infosec-assurance}`
(prod) / `{sharepoint:infosec-assurance-test}` (test) → Site permissions:
Members ← `sg-infosec-foundry-users`, Owners ← `sg-infosec-foundry-owner`
(or `-platform-admins`) + `{group:spo-admins}`, Visitors ←
`sg-infosec-foundry-readers` / `-auditors` → Documents library → create
folders `Reports`, `Reports/DPO`, `Reports/Advisory`, `Templates`,
`Templates/Reviews`, `Governance` (+ `Governance/Implementation/{env}`) →
library settings: versioning on (50 major), default sensitivity label
`{label:confidential-internal}` → unique permissions on `Reports/`,
`Reports/DPO/`, `Templates/`, `Governance/` per
`team/sharepoint-permissions.md` §1–2. Create the lists `TPRM Portfolio`
and `TPSRCA History` (used by `/api/portfolio_update`, `/api/history_append`)
and the `SupplierWatchlist` list (`workflows/scheduled-deepsearch.json`).
**Azure portal.** Function App `{baseName}-fn-delivery` → *Identity* →
system-assigned on (object id → `{mi:infosec-delivery-fn}`) → *Deployment
center* → image `{registry}.azurecr.io/infosec-delivery:{tag}` → *Configuration*:
`PROJECT_ENDPOINT`, `KEY_VAULT_NAME`, `SHAREPOINT_SITE_ID`,
`SHAREPOINT_REPORTS_DRIVE_ID`, `DOCINTEL_ENDPOINT`, `ENX_DATA_BOUNDARY=EU`
(all set by `infra/delivery.bicep`) → *Networking*: VNet integration
`snet-apps`, inbound restricted to the Logic Apps subnet
(`callerSubnetId`). **Foundry portal.** nothing (the Function never calls
Foundry; agents reach it only through `conn-osint-proxy`).

## 3. CLI / Bicep / kit scripts

```powershell
# site roles, folders, unique permissions, versioning, default label — as site owner
# (script in team/sharepoint-permissions.md §2; placeholders in braces)
Connect-PnPOnline -Url "https://{tenant}.sharepoint.com/sites/{sharepoint:infosec-assurance}" -Interactive
```

```bash
# ids the workflows and .env need (read-only Graph, owner's own token)
az rest --url "https://graph.microsoft.com/v1.0/sites/{tenant}.sharepoint.com:/sites/{sharepoint:infosec-assurance}" --query id -o tsv   # SHAREPOINT_SITE_ID
az rest --url "https://graph.microsoft.com/v1.0/sites/{siteId}/drives" --query "value[?name=='Documents'].id | [0]" -o tsv           # SHAREPOINT_REPORTS_DRIVE_ID
az rest --url "https://graph.microsoft.com/v1.0/drives/{driveId}/root:/Reports" --query id -o tsv                                    # SHAREPOINT_REPORTS_ROOT_ITEM_ID
az rest --url "https://graph.microsoft.com/v1.0/drives/{driveId}/root:/Reports/DPO" --query id -o tsv                                # SHAREPOINT_DPO_ROOT_ITEM_ID
az rest --url "https://graph.microsoft.com/v1.0/drives/{driveId}/root:/Reports/Advisory" --query id -o tsv                           # SHAREPOINT_ADVISORY_ROOT_ITEM_ID

# Sites.Selected grants (SPO admin; app ids of the two managed identities)
az rest --method POST --url "https://graph.microsoft.com/v1.0/sites/{siteId}/permissions" --body '{
  "roles": ["write"], "grantedToIdentities": [ { "application": { "id": "{appId:infosec-delivery-fn}", "displayName": "infosec-delivery-fn" } } ] }'
az rest --method POST --url "https://graph.microsoft.com/v1.0/sites/{siteId}/permissions" --body '{
  "roles": ["read"],  "grantedToIdentities": [ { "application": { "id": "{appId:infosecfoundry-proj-mi}", "displayName": "infosecfoundry-proj" } } ] }'

# Function: image + renderers
cd convertion/scripts && python3 convert_skills.py && python3 verify_conversion.py && python3 stage_renderers.py   # renderers/ from the verified build
cd ../functions/delivery && az acr build -r {registry} -t infosec-delivery:{tag} .        # needs a Dockerfile — see gap G-05 below
az deployment group create -g {rg} --template-file ../../infra/main.bicep --parameters ../../infra/main.parameters.prod.json deliveryImage={registry}.azurecr.io/infosec-delivery:{tag}
```

Gap **G-05** (returned as shared delta S-11): `functions/delivery/` has no
`Dockerfile` although `infra/delivery.bicep` deploys a container image
(`DOCKER_REGISTRY_SERVER_URL`, `deliveryImage`). Literal file to add —
`functions/delivery/Dockerfile`:

```dockerfile
FROM mcr.microsoft.com/azure-functions/python:4-python3.11
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
 && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && apt-get install -y nodejs \
 && rm -rf /var/lib/apt/lists/*
ENV AzureWebJobsScriptRoot=/home/site/wwwroot AzureFunctionsJobHost__Logging__Console__IsEnabled=true
COPY requirements.txt /home/site/wwwroot/
RUN pip install --no-cache-dir -r /home/site/wwwroot/requirements.txt
COPY . /home/site/wwwroot
RUN for d in /home/site/wwwroot/renderers/*/; do [ -f "$d/package.json" ] && (cd "$d" && npm ci --omit=dev) || true; done
```

## 4. Values captured into `setup/.env`

| Variable | Source |
|---|---|
| `SHAREPOINT_SITE_ID`, `SHAREPOINT_REPORTS_DRIVE_ID`, `SHAREPOINT_REPORTS_ROOT_ITEM_ID`, `SHAREPOINT_DPO_ROOT_ITEM_ID` | §3 Graph reads (already in `.env.example`) |
| `SHAREPOINT_ADVISORY_ROOT_ITEM_ID` | new (S-04) — `workflows/pipelines.json` `shared.advisoryRoot` expects it |
| `SHAREPOINT_TPA_ACTIVE_PATH` | `Infosec Assurance/GRC/TPA/Active` |
| `DELIVERY_FUNCTION_BASE_URL` | Bicep output `deliveryFunctionBaseUrl` |
| Key Vault secret `kv-delivery-function-key` | `az functionapp keys list` → stored by the owner under PIM; referenced by `infra/logicapp.bicep` `secretNames.DELIVERY_FUNCTION_KEY` |

## 5. Verification

| # | Check | Pass when |
|---|---|---|
| V1 | `POST /api/ensure_folder` twice with `{"driveId","rootItemId","segments":["Acme Test","Managed SOC"]}` | same folder id both times; a second call with `"Acme Test "` (trailing space) resolves to the same supplier folder (normalisation) |
| V2 | `POST /api/render` for `html`, `docx`, `pptx`, `xlsx` with the comparison-set inputs | files byte-identical to the stored known-good outputs (`operations/CHANGE_MANAGEMENT.md` §4) |
| V3 | `POST /api/upload` to the **test** site, then `createLink` | file under `Reports/Acme Test/Managed SOC/`, link scope `organization`, no anonymous link possible |
| V4 | Graph permission listing `GET /sites/{siteId}/permissions` | exactly two application grants: Function = write, project MI = read |
| V5 | A user in `sg-infosec-foundry-users` opens `Reports/` | read-only; upload to `GRC/TPA/Active/` allowed |
| V6 | Function inbound from outside the Logic Apps subnet | 403 (network restriction) |
| V7 | Uploaded file shows the library default sensitivity label | label visible in the file card |
| V8 | `renderers/` in the image equals `build/agents/*/code` sources | `stage_renderers.py` log; image digest recorded |

**Rollback.** Remove the `Sites.Selected` grant (`DELETE
/sites/{siteId}/permissions/{id}`); redeploy the previous image tag
(`deliveryImage`); SharePoint versioning keeps every stored file.
**ISMS evidence.** V1–V8 outputs, permission listing, image digest —
ISO 27001:2022 A.5.12–A.5.13 (classification, labelling), A.5.33 (records),
A.8.3, A.8.10; DORA Art. 28 (evidence retention); EU AI Act Art. 12.

## Sources
- [GA] assignSensitivityLabel — https://learn.microsoft.com/en-us/graph/api/driveitem-assignsensitivitylabel (2026-08-19)
- [GA] Code Interpreter sandbox — https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/code-interpreter (2026-08-05)
- [GA] Purview for Foundry — https://learn.microsoft.com/en-us/purview/ai-azure-foundry (2026-05-01)
- Kit: `sharepoint/README.md`, `functions/delivery/README.md`, `team/sharepoint-permissions.md`, `infra/delivery.bicep`
