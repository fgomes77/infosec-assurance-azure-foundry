# Templates — registry, field reference and change procedure

`registry.json` is the **authoritative template inventory** for the
`template-manager` system (requirement j). Nothing renders from a file that is
not registered here, and no registered file changes without a recorded
approval.

## Field reference (`registry.json` → `templates[]`)

| Field | Required | Meaning |
|---|---|---|
| `id` | yes | Stable key. Referenced by pipelines, renderers and the audit log; never renamed (retire and add instead). |
| `name` | yes | Human title shown by the template-manager. |
| `format` | yes | Primary output format (`html`, `docx`, `pptx`, `xlsx`, `json`). |
| `formats` | no | Full list when a template produces a multi-file pack (e.g. `tpsrca-report`). |
| `source` | yes | **Exactly one file**, path relative to the repo root — the conversion source of truth that `scripts/update_templates.py` overwrites after a recorded approval. Never a directory, never a `#fragment` of a byte-verified `SKILL.md`. `scripts/verify_kit.py` fails the kit if it does not exist. |
| `source_note` | no | Where the file came from and why, when the provenance is not obvious. |
| `sample` | no | Sanitised **synthetic** dataset under `templates/samples/` used for the before/after preview, the regression run and `/api/preview`. Contains no Euronext data. |
| `schema` | no | JSON Schema in `templates/` that the delivery Function validates the agent's contract against **before** rendering (`SCHEMA_DIRS`). |
| `style` | no | Free-form record of the visual contract (theme, font, section/button counts). The tokens themselves live in `enx-theme.json`. |
| `consumers` | yes | Agents that produce content for this template — the list `update_templates.py` recreates after an approved change. |
| `pipelines` | yes | Logic App pipelines that render it (keys of `workflows/pipelines.json`). Empty means "not wired to a pipeline yet". |
| `renderer` | no | Staged renderer entry the Function invokes (`scripts/stage_renderers.py`). |
| `renderer_pending` | no | Renderer source that is **not** yet registered in `stage_renderers.SOURCES` — see "Pending" below. |
| `pipeline_pending` | no | Pipeline that does not exist yet, with the shape it will take. |
| `binary` | no | `true` when the source is a binary asset (e.g. a `.pptx` template). |
| `fragment_markers` | no | Markers delimiting the template inside a larger document, when the source is a section of a charter. |
| `slides` | no | Slide inventory for deck templates. |
| `version` | yes | Bumps on **every** approved change. |
| `last_approved` | yes | Date of the last approval run; `null` = never approved on this platform, so its first production use requires one approval run (`operations/ROLLOUT_PLAN.md` P1 exit criterion). |
| `promoted_agent_versions` | yes | The `<agent>:<version>` refs the last approved propagation promoted (finding C19). `scripts/update_templates.py` writes it from the deploy ledger `build/agent-versions.json` (via `_foundry_runtime.pinned_ref`) after the consuming agents have been recreated, and appends the same list as `agent_versions=…` to `templates/audit.log`. Pipelines pin `<agent>:<version>`, so this field is the link between an approved template change and the agent versions actually serving traffic — and the rollback target. `[]` means it has not been propagated through `update_templates.py` yet (or the runtime does not version agents). **Never hand-edit: it is evidence, not configuration.** |
| `sensitivity_label` | no | The per-report-type Purview sensitivity label id (finding C16). `scripts/build_logicapps.py` prefers it over `workflows/pipelines.json` `shared.sensitivityLabel` when setting the pipeline's `sensitivityLabelId` parameter, and the delivery Function's `/api/assign_label` route applies it to the stored file. **Empty means the Reports library's default label is sufficient** and no per-file assignment is made; the per-file label supplements, never replaces, the library default. |
| `deprecated_on` | no | `YYYY-MM-DD` marks a retired template (`operations/LIFECYCLE.md` §6): the delivery Function refuses to render it and `template-manager` lists it as retired. Remove the entry only after the next quarterly template review. |
| `notes` | no | Anything an operator must know that no field above carries. |

## Assets in this folder

| Path | Content |
|---|---|
| `enx-theme.json` | Euronext house-style tokens — the **only** permitted theme. Palette, risk colours, HTML-entity glyph set, typography, layout, chart CDN, classification strings and Office tokens. Every renderer and every HTML template reads from it, and the verifier's house-style rule checks deliverables against it. |
| `assets/deepsearch-dashboard.html` | Template of record for the DeepSearch OSINT dashboard (v17.02.11): 9 accordion sections, 6-axis Chart.js radar, self-contained download. Agents fill `{{PLACEHOLDERS}}` only — never the structure, ids, palette or script. The PHASE 5 quality gate keys on the nine section ids, `chart.umd.min.js`, `spiderChart` and `downloadReport`. (The gate's "file > 20 KB" check applies to the **filled** report, not to the empty template.) |
| `assets/tpsrca-report.html` | Primary HTML of the TPSRCA assessment pack; section ids map 1:1 to the engine's `output_schema.json` top-level keys. Not yet approved (`last_approved: null`); its renderer and pipeline are pending. |
| `samples/` | Sanitised **synthetic** dataset per template (`sample` field) — one per registered template, listed below. No Euronext data, no real people, placeholder UPNs only. |
| `skill-decisions.json` | Machine-readable include/exclude decision for all **35 exported + 41 platform skills** (plus the harness skills, unenforced). The machine form of `MAPPING.md` and `governance/PLATFORM_SKILLS_DECISION.md`; `scripts/verify_conversion.py` enforces it (see its `enforcement.checks`). |
| `themes/` | House-style prose (`euronext-house.md`); the machine-readable tokens are `enx-theme.json`. |
| `*.schema.json` | The JSON Schemas named by the `schema` field, plus `ciso_exec_summary_render.schema.json` (named by that renderer's `manifest.json`). |

## Changing a template

A template change is a **methodology change**, not a content edit:

1. `template-update-approval.json` raises the gate (expiry **P7D**, owner tier —
   deputy when the owner is the proposer; `governance/HUMAN_APPROVAL.md`).
2. On approval — and only then — the workflow re-renders this template's
   `sample` (`samples/<id>.json`) with the **proposed** template through the
   delivery Function `/render` and runs `output-verifier` on the result. A
   schema mismatch (400), a failed quality gate (422) or anything but
   `VERDICT: PASS` stops the run and changes nothing. The theme tokens
   (`enx-theme`, no renderer) are verified as source text instead. This is why
   the review package must carry `sampleFormat`, `sampleDataJson` and — for
   HTML templates — `sampleHtml`.
3. Then `scripts/update_templates.py --approved-by … --approval-run …` (it
   **refuses to run without `--approval-run`**)
   writes the source, re-runs convert → verify → `create_*.py --only <consumers>`
   → `stage_renderers.py`, bumps `version` and `last_approved`, records
   `promoted_agent_versions`, and appends a line to `templates/audit.log`.
4. Consumers update **together** — a template can never be live in one consumer
   and stale in another (`operations/LIFECYCLE.md` §4).
5. Rollback = switching the agents back to the `promoted_agent_versions` of the
   previous entry, not redeploying: promoted agent versions are immutable.

## Pending

`renderer_pending` / `pipeline_pending` entries are tracked in
`operations/LIFECYCLE.md` §4 and in the template-manager charter
(`agents/template-manager_instructions.md`). A template with a pending renderer
can be previewed but not delivered by a pipeline.

## Schema resolution — which contracts are actually enforced

The delivery Function resolves a contract by the **pipeline's `renderTemplate`**
(`workflows/pipelines.json`), not by the `schema` field here and not by the
renderer's `manifest.json`: `_validate_schema()` looks for
`templates/<renderTemplate>.schema.json` and `templates/<renderTemplate with
dashes→underscores>.schema.json`, and **returns without validating when neither
exists** (`function_app.py` `SCHEMA_DIRS`). So a schema whose file name does not
match the `renderTemplate` is documentation, not a gate.

| Template (`id`) | `renderTemplate` | Schema file | Enforced by the Function today |
|---|---|---|---|
| `evidence-summary-docx` | `evidence-summary` | `evidence_summary.schema.json` | **yes** |
| `docx-generic` | `docx-generic` | `docx_generic.schema.json` | **yes** |
| `pptx-generic` | `pptx-generic` | `pptx_generic.schema.json` | **yes** |
| `xlsx-generic` | `xlsx-generic` | `xlsx_generic.schema.json` | **yes** |
| `tprm-board-slide` | `tprm-board-slide` | `tprm_board_slide.schema.json` | **yes** (plus the `tprm-board-slide` data gate) |
| `tpsrca-report` | *(pipeline pending)* | `tpsrca_report.schema.json` | not yet — preview only |
| `dpia-dpo-docx` | `dpia` | `dpia_report.schema.json` | **no** — name mismatch (`dpia.schema.json` expected) |
| `ciso-reporting-deck` | `ciso-reporting` | `ciso_reporting_assessment.schema.json` | **no** — name mismatch |
| `ciso-global-deck` | `ciso-global` | `ciso_global_deck.schema.json` | **no** — name mismatch |
| `ciso-executive-summary-html` | *(empty — html path)* | `ciso_exec_summary_render.schema.json` | no — the HTML is checked by `gates.ciso_exec_summary_html` |
| `deepsearch-html-dashboard` | *(empty — html path)* | `deepsearch_dashboard.schema.json` | no — the HTML is checked by `gates.deepsearch_dashboard` |

The four "name mismatch" rows are a **fail-open gate**: an off-contract payload
reaches the renderer and produces a plausible-looking wrong report. The fix is
outside this folder (shared delta): either teach `_validate_schema()` to read
the schema name from the renderer's `manifest.json` / this registry, or rename
the files to the `renderTemplate`. Do not rename here alone — the manifests and
the agent charters cite the current names.

## Renderer path convention (`renderer` / `renderer_pending`)

Every registered entry names **the file the Function actually invokes**:
`render.py` for the `python` runtime, `generate_slide.js` for `node` — the
`entry` of that renderer's `manifest.json`, under
`functions/delivery/renderers/<renderer>/` (staged) or
`functions/delivery/renderers-src/<renderer>/` (source).

The byte-verified skill generators are **never** registered directly:

| Skill generator (byte-verified, never edited) | Registered entry |
|---|---|
| `ciso-reporting/scripts/generate_reports_v2.py` | `functions/delivery/renderers/ciso-reporting/render.py` (wrapper: runs it with the skill's own layout and enforces its `PASS - zero unsubstituted tokens` line) |
| `dpia/scripts/generate_report.js` | `functions/delivery/renderers/dpia/render.py` (python-docx port, layout 1:1) |
| `tprm-slide-generator/scripts/generate_radar.py` + `generate_slide.js` | `functions/delivery/renderers-src/tprm-board-slide/render.py` (wrapper) |
| `ciso-executive-summary/scripts/html_to_pdf.py`, `render_sections.py`, `generate_pptx_template.js` | `functions/delivery/renderers-src/ciso-exec-summary/render.py` (wrapper, constants rebound in memory) |

`scripts/stage_renderers.py` stages only the folders named by a `renderer`
field and writes a shim when the entry lives under `scripts/` in the verified
layout; a `renderer_pending` entry is not staged at all.

## Samples (`samples/`)

**Regression run:** `python3 ../evaluation/run_regression.py` checks every
registered template against its own sample — the sample parses, validates
against the template's declared schema, and passes its `gates.GATES` entry
(an HTML gate runs on the template asset filled with the sample). `--render`
additionally executes each staged renderer; a runtime the machine lacks is
reported as a skip, never a failure. Attach its output to every template
approval package (`../operations/LIFECYCLE.md` §4).


One synthetic dataset per registered template, used by the template-manager
before/after preview, the regression run and `/api/preview`. Every file carries
a `_sample_note`; renderers and schemas ignore it.

| Sample | Shape | Validated by |
|---|---|---|
| `deepsearch-html-dashboard.json` | `{{PLACEHOLDER}}` → value map (30 keys) | `deepsearch_dashboard.schema.json`; filling the template yields 21.5 KB (the PHASE 5 gate needs > 20 KB) |
| `ciso-executive-summary-html.json` | `{html, vendor, assessment, baseName}` | `ciso_exec_summary_render.schema.json`; the HTML passes `gates.ciso_exec_summary_html` |
| `ciso-reporting-deck.json` | verified assessment JSON | `ciso_reporting_assessment.schema.json` |
| `tprm-board-slide.json` | slide data contract | `tprm_board_slide.schema.json` |
| `ciso-global-deck.json` | 9-slide deck contract | `ciso_global_deck.schema.json` |
| `dpia-dpo-docx.json` | DPO report contract | `dpia_report.schema.json`; renders through `renderers-src/dpia/render.py` |
| `evidence-summary-docx.json` | SOC/pentest/TPA summary | `evidence_summary.schema.json`; renders through `renderers-src/evidence-summary/render.py` |
| `xlsx-generic.json` | 2 sheets incl. a formula row and a `risk_band` column | `xlsx_generic.schema.json`; renders through `renderers-src/xlsx-generic/render.py` |
| `docx-generic.json` | advisory note with a table | `docx_generic.schema.json`; renders through `renderers-src/docx-generic/render.py` |
| `pptx-generic.json` | 3-slide advisory readout | `pptx_generic.schema.json`; renders through `renderers-src/pptx-generic/render.py` |
| `tpsrca-report.json` | `{{PLACEHOLDER}}` → value map (45 keys) | `tpsrca_report.schema.json` |
| `enx-theme.json` | token preview (swatches, glyphs, KPI/row examples quoted from `enx-theme.json`) | no schema — preview dataset only |

Sample rules: synthetic supplier (`Northwind Cloud Services BV`) and service,
invented scores and findings, role names or `{upn:…}` placeholders instead of
people, no hostnames beyond `*.example`, and nothing that could be mistaken for
a Euronext assessment.

## Known template defects (need an approval run)

`templates/assets/deepsearch-dashboard.html` is an approved template of record,
so these are recorded here rather than patched in place
(`scripts/update_templates.py --approved-by … --approval-run …`):

1. `<body>` carries no `data-overall-score` attribute, so every filled report
   fails `gates.deepsearch_dashboard`'s ENX-addendum check. Fix:
   `<body data-overall-score="{{OVERALL_SCORE}}">` plus an `OVERALL_SCORE`
   entry in `deepsearch_dashboard.schema.json` and in the sample.
2. The header comment contains the literal `{{PLACEHOLDERS}}`, which the same
   gate reports as *placeholder text present* whenever the agent keeps the
   comment — while the "fill placeholders only, never edit structure" rule
   forbids the agent from deleting it. Fix: reword the comment without braces.
   `assets/tpsrca-report.html` carries the same comment (no gate keys on it
   yet, so it is not blocking).

Both are recorded in the `notes` field of the affected registry entries.
