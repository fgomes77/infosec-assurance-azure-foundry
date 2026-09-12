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
| `samples/` | Sanitised synthetic datasets per template (`sample` field). |
| `themes/` | House-style prose (`euronext-house.md`); the machine-readable tokens are `enx-theme.json`. |
| `*.schema.json` | The JSON Schemas named by the `schema` field. |

## Changing a template

A template change is a **methodology change**, not a content edit:

1. `template-update-approval.json` raises the gate (expiry **P7D**, owner tier —
   deputy when the owner is the proposer; `governance/HUMAN_APPROVAL.md`).
2. On approval, `scripts/update_templates.py --approved-by … --approval-run …`
   writes the source, re-runs convert → verify → `create_*.py --only <consumers>`
   → `stage_renderers.py`, bumps `version` and `last_approved`, records
   `promoted_agent_versions`, and appends a line to `templates/audit.log`.
3. Consumers update **together** — a template can never be live in one consumer
   and stale in another (`operations/LIFECYCLE.md` §4).
4. Rollback = switching the agents back to the `promoted_agent_versions` of the
   previous entry, not redeploying: promoted agent versions are immutable.

## Pending

`renderer_pending` / `pipeline_pending` entries are tracked in
`operations/LIFECYCLE.md` §4 and in the template-manager charter
(`agents/template-manager_instructions.md`). A template with a pending renderer
can be previewed but not delivered by a pipeline.
