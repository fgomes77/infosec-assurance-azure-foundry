# Delivery Function App

Python v2-model Azure Function App providing the three delivery endpoints
used by every Logic App pipeline (`../../workflows/`):

| Endpoint | Purpose |
|---|---|
| `POST /api/ensure_folder` | Idempotent Supplier/Service folder provisioning (the requirement rule: reuse existing supplier folder, create missing service folder) |
| `POST /api/upload` | Upload the rendered report into the folder (chunked >4 MiB), optional org-scoped share link |
| `POST /api/assign_label` | Assign the Purview sensitivity label to the stored file (finding C16). Called by `report-delivery-pipeline.json` immediately after `/upload`, with `{driveId, itemId, labelId, assignmentMethod, justification?, reportType?, runId?}`. `labelId` comes from `templates/registry.json` `sensitivity_label` for the report type, falling back to `workflows/pipelines.json` `shared.sensitivityLabel` (`SHAREPOINT_SENSITIVITY_LABEL_ID`); an empty value means the pipeline skips the call and the library default label applies. Graph `driveItem:assignSensitivityLabel` is **asynchronous, protected and metered** — `202 Accepted` + `Location` is the success case, and the per-file label supplements rather than replaces the library default. |
| `POST /api/render` | Render the agent's verified JSON/HTML into the final file: `html` (verbatim), `docx`/`xlsx` (Python renderers), `pptx` (Node generators — this app ships Node 20, which agent code_interpreter lacks). Every `xlsx` it produces then passes the **recalc gate** (below) before it is returned |
| `POST /api/fetch_evidence` | Attach a SharePoint evidence file to the Foundry project (`{driveId, itemId}` → `fileId`) without streaming it through the conversation. Body is jsonschema-validated (`REQUEST_SCHEMAS`) |
| `POST /api/extract_pdf` | OCR / layout extraction on **Azure AI Document Intelligence** (EU) for scanned or garbled evidence: `{model: prebuilt-read\|prebuilt-layout, pages?, contentBase64\|driveId+itemId\|fileId, attachToProject?}` → `{content, pages, tables, confidence:{mean,min}, source}`. Document Intelligence is reachable **only** from this app, with its managed identity (`main.bicep` sets `disableLocalAuth`) — never an agent tool. Fallback order stays pure-Python → office-tools (poppler) → here (`agents/knowledge-packs/pdf-reading-foundry.md` §4) |

## Deploy

This app runs as a **Linux custom container** on the Elastic Premium plan
created by `../../infra/delivery.bicep` — not on Flex Consumption, which has
no Node runtime for the pptx/diagram renderers and no Chromium:

```bash
# 1. Stage the byte-verified renderers out of the conversion build
python3 ../../scripts/stage_renderers.py --strict     # renderers-src/ + build/agents/*/code-tree -> renderers/
# 2. Build the image into the private registry (managed-identity pull)
az acr build -r {registryLoginServer%%.*} -t infosec-delivery:{tag} .
# 3. Point the app at the new tag
az deployment group create -g {rg} -f ../../infra/main.bicep \
  -p main.parameters.prod.json \
  -p deliveryImage={registry}.azurecr.io/infosec-delivery:{tag}
```

The office toolchain is a second image built the same way from
`../office-tools` (`officeToolsImage`); `OFFICE_TOOLS_BASE_URL` and
`OFFICE_TOOLS_KEY` connect the two.

## Graph permission (least privilege)

**Bootstrap the Graph side first.** Run
`python3 ../../scripts/sharepoint_bootstrap.py --site-url https://{tenant}.sharepoint.com/sites/{site} --function-app-id {function-mi-appId}` — it resolves the site, performs the `Sites.Selected` grant for the Function's managed identity, and prints `SHAREPOINT_SITE_ID`, `SHAREPOINT_REPORTS_DRIVE_ID`, `SHAREPOINT_REPORTS_ROOT_ITEM_ID`, `SHAREPOINT_DPO_ROOT_ITEM_ID`, `SHAREPOINT_ADVISORY_ROOT_ITEM_ID` and `SHAREPOINT_TEMPLATES_REVIEWS_ITEM_ID` for `setup/.env`. Doing it by hand is where the ids get mistyped.

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
├── ciso-reporting/render.py          # 8-slide governance PPTX + A3 PDF + HTML
├── ciso-global/generate_slide.js     # Global CISO deck (req. d, pptxgenjs)
├── docx-generic/render.py            # advisory DOCX (house style)
├── pptx-generic/render.py            # advisory PPTX (16:9 house style)
├── xlsx-generic/render.py            # tabular XLSX (openpyxl) + recalc gate
├── transcript/render.py              # diarized transcript -> md + html + docx
├── charts/render.py                  # matplotlib spider/gauge/bar/heatmap
├── diagrams/generate_slide.js        # mermaid-cli -> SVG/PNG
├── whisperx/…                        # scripts for POST /api/speaker_clips
└── pdf-coverage/…                    # scripts for POST /api/pdf/{stage}
```

Entry-name convention: **`render.py`** for python renderers, **`generate_slide.js`**
for node ones — the names `templates/registry.json` (`renderer`),
`scripts/stage_renderers.py` (`SHIMS`) and `function_app._manifest` all fall
back to. A renderer whose verified layout keeps the entry under `scripts/`
gets a one-line shim at its root instead of being renamed.

> **Staging gap (shared delta, `scripts/` is not this area's to edit):**
> `stage_renderers.py` stages only the folders named by a `renderer` field in
> `templates/registry.json`, so the renderers that are reached by template name
> or by a dedicated endpoint — `charts`, `diagrams`, `transcript`,
> `form-b-fill`, `whisperx`, `pdf-coverage`, plus the two `renderer_pending`
> ones (`ciso-exec-summary`, `tprm-board-slide`) — are never copied into
> `renderers/` and answer **404 / 501** at runtime. The fix is a `SOURCES`
> entry per folder (and a registry entry for `transcript`); see the delta list
> returned with this change.

`stage_renderers.py` copies these from `renderers-src/` and
`build/agents/<name>/code-tree/` after `convert_skills.py` +
`verify_conversion.py` have proven them identical to the claude.ai originals —
that is what keeps rendered outputs matching the previous environment. The
folder is build output: it is never edited by hand, and `.dockerignore` keeps
`renderers-src/` **out** of the image so only staged renderers ship.

## Image split review (delivery vs office-tools)

Reviewed against `../office-tools/Dockerfile` (both images build from
`mcr.microsoft.com/azure-functions/python:4-python3.11` onto the same Elastic
Premium plan):

| Tool | Here | office-tools | Why |
|---|---|---|---|
| Node 20 + pptxgenjs/docx/mermaid-cli | yes | no | The pptx/docx/diagram renderers run here |
| Playwright Chromium | yes | no | HTML→PDF/PNG, spider PNG, dashboard screenshots |
| poppler, tesseract | yes | yes | pdf-coverage scripts run **here**; the pdf-skill helpers run **there**. Deliberate duplication, not drift |
| ffmpeg | yes | no | `/api/speaker_clips` |
| LibreOffice, pandoc, qpdf, ImageMagick | **no** | yes | Doubling this image for LibreOffice was the reason for the split; conversions are an HTTP call to office-tools |
| defusedxml / lxml | no | yes | OOXML XSD + redlining validation is an office-tools endpoint |
| Azure credential (managed identity) | yes (Graph, Foundry, Document Intelligence) | **none** | office-tools holds no token and makes no outbound call |

Findings applied in this pass:

1. The mermaid-cli browser download no longer ends in `|| true` — a build that
   cannot fetch it now fails at build time instead of at the first diagram
   render in production.
2. `.dockerignore` added: `renderers-src/`, `tests/`, caches and
   `local.settings.json` no longer ship in the image.
3. The xlsx recalc gate is now actually wired (`_recalc_gate` →
   `POST {OFFICE_TOOLS_BASE_URL}/recalc` with `OFFICE_TOOLS_KEY`): every
   workbook leaving `/api/render` is recalculated by LibreOffice and must
   report `total_errors=0`, and the **recalculated** bytes are what get
   uploaded. With no office-tools app configured the gate is reported as
   `{"passed": null, "reason": …}` — visible to the verifier and the
   approver — never as a silent pass.
4. No missing runtime dependency was found for the staged renderers: their
   only third-party imports are `playwright`, `matplotlib`/`numpy`,
   `python-docx`/`python-pptx`/`openpyxl`, `pypdf`/`pdfplumber`/`PyMuPDF`,
   all pinned in `requirements.txt`.

## Monitoring

Connect the app to `{baseName}-appi`; the `delivery-function-5xx` alert
(`../../operations/alerts.bicep`) keys on `AppRoleName` containing
`fn-delivery` — keep the app name `{baseName}-fn-delivery`.
