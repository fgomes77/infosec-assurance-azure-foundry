# Delivery Function App

Python v2-model Azure Function App providing the three delivery endpoints
used by every Logic App pipeline (`../../workflows/`):

| Endpoint | Purpose |
|---|---|
| `POST /api/ensure_folder` | Idempotent Supplier/Service folder provisioning (the requirement rule: reuse existing supplier folder, create missing service folder) |
| `POST /api/upload` | Upload the rendered report into the folder (chunked >4 MiB), optional org-scoped share link |
| `POST /api/assign_label` | Assign the Purview sensitivity label to the stored file (finding C16). Called by `report-delivery-pipeline.json` immediately after `/upload`, with `{driveId, itemId, labelId, assignmentMethod, justification?, reportType?, runId?}`. `labelId` comes from `templates/registry.json` `sensitivity_label` for the report type, falling back to `workflows/pipelines.json` `shared.sensitivityLabel` (`SHAREPOINT_SENSITIVITY_LABEL_ID`); an empty value means the pipeline skips the call and the library default label applies. Graph `driveItem:assignSensitivityLabel` is **asynchronous, protected and metered** — `202 Accepted` + `Location` is the success case, and the per-file label supplements rather than replaces the library default. |
| `POST /api/render` | Render the agent's verified JSON/HTML into the final file: `html` (verbatim), `docx`/`xlsx` (Python renderers), `pptx` (Node generators — this app ships Node 20, which agent code_interpreter lacks) |

## Deploy

```bash
# Flex Consumption plan with managed identity; Node 20 side-installed for pptx
az functionapp create -g $RG -n $APP --storage-account $SA \
  --flex-consumption-location $LOC --runtime python --runtime-version 3.11 \
  --assign-identity [system]
func azure functionapp publish $APP
# Stage the byte-verified renderers out of the conversion build:
python3 ../../scripts/stage_renderers.py   # copies build/agents/*/code -> renderers/
```

## Graph permission (least privilege)

Grant the app's managed identity `Sites.Selected`, then grant **write** on
the single InfoSec Assurance site:

```
POST https://graph.microsoft.com/v1.0/sites/{siteId}/permissions
{ "roles": ["write"],
  "grantedToIdentities": [ { "application": {
      "id": "<function-managed-identity-appId>",
      "displayName": "infosec-delivery-fn" } } ] }
```

The same managed identity additionally needs `InformationProtectionPolicy.Read.All`
and the **metered-API approval** for `assignSensitivityLabel` (a protected,
pay-as-you-go Graph API) so `/api/assign_label` can label the stored file
(finding C16). Least privilege stays: `Sites.Selected` write on the one site
plus that protected-API grant — never `Files.ReadWrite.All`.

Resolving the managed identity's `appId`, granting the read roles to the
Foundry project MI and the Logic Apps MI, and listing or revoking grants:
`../../team/sharepoint-permissions.md` §3.

No other identity in the platform can write to SharePoint: agents get
read-only Graph tools, and human approval gates every pipeline before this
app is ever called.

## `renderers/` layout (staged, not committed)

```
renderers/
├── dpia/render.py                    # OneTrust PDF -> DPO DOCX (python-docx)
├── evidence-summary/render.py        # d2/e/f analyzer DOCX renderer
├── ciso-reporting/generate_slide.js  # 8-slide governance PPTX (pptxgenjs)
├── ciso-global/generate_slide.js     # Global CISO deck (req. d)
└── xlsx-generic/render.py            # tabular XLSX (openpyxl)
```

`stage_renderers.py` copies these from `build/agents/<name>/code/` after
`convert_skills.py` + `verify_conversion.py` have proven them identical to
the claude.ai originals — that is what keeps rendered outputs matching the
previous environment.

## Monitoring

Connect the app to `{baseName}-appi`; the `delivery-function-5xx` alert
(`../../operations/alerts.bicep`) keys on `AppRoleName` containing
`fn-delivery` — keep the app name `{baseName}-fn-delivery`.
