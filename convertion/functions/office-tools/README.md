# office-tools Function App (`{baseName}-office`)

The binary document toolchain the four converted document skills assume —
LibreOffice (`soffice`), pandoc, poppler, qpdf, tesseract, ImageMagick — in a
container of its own, because neither Foundry `code_interpreter` nor the
delivery Function image has it (`../../agents/document_agents_addendum.md`,
`../../agents/overlays/_foundry-environment.md`).

| Endpoint | Purpose | Byte-verified script executed |
|---|---|---|
| `POST /api/convert` | `soffice --convert-to` / `pandoc` / `pdftoppm`: legacy `.doc/.ppt/.xls` intake, DOCX→PDF for visual QA, Markdown→DOCX, PDF→page images | — (CLI) |
| `POST /api/recalc` | The xlsx skill's **mandatory** formula gate: LibreOffice `calculateAll()` + store, then every `#REF!/#VALUE!/…` reported. `gate.passed` is false unless `status=="success"` and `total_errors==0` | `xlsx/scripts/recalc.py` |
| `POST /api/accept_changes` | Flatten tracked changes into a clean DOCX | `docx/scripts/accept_changes.py` |
| `POST /api/thumbnail` | Labelled slide grid (`.pptx`) or rasterised pages (`.pdf`, office formats via PDF) for the "render it and look at it" step | `pptx/scripts/thumbnail.py` |
| `POST /api/validate` | OOXML XSD validation, `--auto-repair`, and the redlining/untracked-edit check (`--original` + `--author`) | `<family>/scripts/office/validate.py` |
| `GET /api/health` | Tool presence, staged toolchain, data boundary (anonymous, no content) | — |

Every script above is executed, never edited: that is what keeps
recalculation, redlining and validation semantics identical to the previous
claude.ai environment (`../../governance/THIRD_PARTY_IP.md`).

## Trust boundary (why this app is separate)

- **No Azure credential, no outbound call.** No `azure-identity`, no
  `requests`: every endpoint takes the file inline (`contentBase64`) and
  returns bytes inline. The callers that hold identity — the delivery
  Function (`/api/render` xlsx recalc gate, SharePoint) and the Logic App
  pipelines — fetch and store the bytes. LibreOffice never sees a token and
  never reaches the network.
- **Key-protected.** All routes are `AuthLevel.FUNCTION` (`x-functions-key`,
  the delivery Function reads it from `OFFICE_TOOLS_KEY`); `/api/health` is
  anonymous for the platform probe and returns no document content.
  `ALLOWED_CALLER_PRINCIPAL_IDS` pins the Easy Auth principal to the delivery
  Function / Logic Apps managed identities, and `infra/delivery.bicep`
  restricts inbound IP to the caller subnet (`callerSubnetId`).
- **No agent calls it.** It is not an OpenAPI tool connection; agents ask the
  pipeline, the pipeline asks this app. (`attach_integrations.py` strips
  non-GET operations anyway — read-only enterprise access.)
- **Defensive contracts.** Every body is `jsonschema`-validated
  (`REQUEST_SCHEMAS`) before a byte reaches disk: unknown properties,
  traversal-shaped `fileName`, non-base64 content and unsupported extensions
  are deterministic `400`s. Missing toolchain → `501`, toolchain timeout →
  `504`, failed quality gate → `422`.
- **Nothing persists.** Each call runs in its own `TemporaryDirectory` with a
  per-call LibreOffice profile; no file, no log line and no error detail
  carries document content beyond the response.

## Build and deploy

`toolchain/` is build output (like `../delivery/renderers/`), staged out of
the verified conversion build — never hand-edited:

```bash
python3 ../../scripts/convert_skills.py      # then verify_conversion.py
python3 stage_toolchain.py --strict          # build/agents/<skill>/code-tree -> toolchain/
az acr build -r {registryLoginServer%%.*} -t infosec-office-tools:{tag} .
az deployment group create -g {rg} -f ../../infra/main.bicep \
  -p main.parameters.prod.json \
  -p officeToolsImage={registry}.azurecr.io/infosec-office-tools:{tag}
```

Leaving `officeToolsImage` empty deploys the platform without this app
(`infra/delivery.bicep`); the delivery Function then has an empty
`OFFICE_TOOLS_BASE_URL` and the xlsx recalc gate degrades to
`{"passed": null, "reason": "office-tools not configured"}` rather than
silently passing — see `../delivery/function_app.py` `_recalc_gate`.

## App settings

| Setting | Meaning |
|---|---|
| `ALLOWED_CALLER_PRINCIPAL_IDS` | Easy Auth object ids allowed to call (delivery Function MI, Logic Apps MI). Empty = principal pinning off (key + IP restriction only) |
| `MAX_PAYLOAD_BYTES` | Request cap, default 50 MiB — same value as the delivery Function |
| `SOFFICE_TIMEOUT_SECONDS` | Per-conversion timeout, default 300 |
| `TOOLCHAIN_DIR` | Override the staged toolchain path (tests/local runs). Empty = `./toolchain` |
| `ENX_DATA_BOUNDARY` | `EU`, asserted by the `@allowed` location list of `main.bicep` and echoed by `/api/health` |
| `HOME` | `/tmp` — LibreOffice needs a writable home; the image sets it |

## Worked example — the xlsx release gate

```jsonc
// delivery /api/render produced Risk_Register_Acme_Portal_2026-09-12.xlsx
POST {OFFICE_TOOLS_BASE_URL}/recalc      // x-functions-key: {OFFICE_TOOLS_KEY}
{ "fileName": "Risk_Register_Acme_Portal_2026-09-12.xlsx",
  "contentBase64": "UEsDBBQ…", "timeoutSeconds": 60 }

// 200 — release allowed
{ "gate": {"passed": true, "checks": []}, "status": "success",
  "total_errors": 0, "total_formulas": 148, "error_summary": {},
  "contentBase64": "UEsDBBQ…", "fileName": "Risk_Register_…xlsx" }

// 200 — release refused by the delivery Function (422 to the pipeline)
{ "gate": {"passed": false,
           "checks": ["3 Excel error(s): #DIV/0!, #REF!"]},
  "status": "errors_found", "total_errors": 3,
  "error_summary": {"#REF!": {"count": 2, "locations": ["Register!D14", …]}} }
```

The recalculated workbook comes back in `contentBase64` — the delivery
Function uses **that** file (formulas cached with values) for the upload, so
the stored record opens with the numbers a reviewer approved.

## Operations

- Image lifecycle, tagging and rebuild: `../../operations/LIFECYCLE.md` V10,
  `../../operations/BACKUP_DR.md` S11.
- Change class for this code: `../../enterprise/UPDATE_AND_UPGRADE_REVIEW_POLICY.md`
  C9 (`py_compile`, local `func` run, `/convert` + `/recalc` smoke on the
  comparison set, image scan).
- Diagnostics go to the same Log Analytics workspace as the delivery Function
  (`infra/delivery.bicep` `diagnostics`); `FunctionAppLogs` carry file names
  and gate outcomes only, never document content.

## Where this is referenced

Four other files describe this container. On the next image change, check them
together — that is what this list is for:

| File | What it says about office-tools |
|---|---|
| `../../README.md` | folder layout + the Azure inventory entry `{baseName}-office` |
| `../../MAPPING.md` | the "local binary toolchain" row of the Non-skill components table — the decision record for why this container exists |
| `../../workflows/README.md` | where it sits in the render chain |
| `../../infra/README.md` | the `stage_toolchain.py` → `az acr build` build step, and the app-settings paragraph (`OFFICE_TOOLS_BASE_URL` / `OFFICE_TOOLS_KEY` on the delivery app only) |
| `../../agents/document_agents_addendum.md`, `../../agents/overlays/_foundry-environment.md` | which endpoint lives on which app, and that agents never call either app directly |
