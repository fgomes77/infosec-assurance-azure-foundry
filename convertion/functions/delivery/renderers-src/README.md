# `renderers-src/` — renderer sources for the delivery Function

Source of the generators the delivery Function executes. `scripts/stage_renderers.py`
copies each folder named here (or the matching `build/agents/<skill>/code-tree/`)
into `../renderers/<template>/` before the image is built; nothing in this
folder ships in the container (`../.dockerignore`) and nothing here is edited
at runtime.

Two kinds of renderer live here:

* **Ports / adapters** (`dpia`, `evidence-summary`, `docx-generic`,
  `pptx-generic`, `xlsx-generic`, `transcript`, `charts`, `diagrams`,
  `ciso-global`) — written for this platform, driven by a `data.json`
  contract, house style from `templates/enx-theme.json`.
* **Wrappers around byte-verified skill code** (`ciso-reporting`,
  `form-b-fill`, `tprm-board-slide`, `ciso-exec-summary`, and the
  endpoint-only `whisperx`, `pdf-coverage`) — the original script is staged
  as `<skill>-scripts.zip`, unpacked in place by
  `function_app._materialise`, and executed unchanged. The zip is the
  fidelity guarantee: never edit it, never reimplement what it does.

## Conventions

| Rule | Why |
|---|---|
| Entry is `render.py` (python) or `generate_slide.js` (node) | The name `templates/registry.json` (`renderer`), `stage_renderers.py` (`SHIMS`) and `function_app._manifest` all fall back to. A verified tree that keeps its entry under `scripts/` gets a generated one-line shim at the root instead of being renamed — byte-verified files are never moved |
| `manifest.json` beside the entry | Declares `runtime`, `entry`, `argv`, `formats`, `outputs`, optional `timeout`, `schema`, `stdout_must_contain`, `cwd`, and a `source` line naming the origin |
| `argv` placeholders | `{data}` `{out}` `{outdir}` `{renderer}` `{tmp}`, plus `{input}` for renderers that take a user file (`form-b-fill`) |
| `outputs: "single"` vs `"dir"` | `single` writes exactly `{out}`; `dir` writes every deliverable into `{outdir}` and `/api/render` returns them all in `files[]` with the requested format as the primary |
| Contract validation | A `templates/<id>.schema.json` is applied by `_validate_schema` before the renderer starts (400 on mismatch, fail-closed) |
| Quality gate | Deterministic checks live in `../gates.py` (data/HTML gates, 422) or as `stdout_must_contain` in the manifest; `xlsx` additionally passes the office-tools recalc gate |
| House style | `templates/enx-theme.json` tokens only — Verdana, teal RGB(0,141,127), classification footer. The skills' own Anthropic palettes are not used for Euronext deliverables (`agents/document_agents_addendum.md`) |
| No network, no secrets | Renderers run offline in a temp dir; anything needing Graph/Foundry/OCR is an endpoint of the Function, not a renderer |

## Inventory

| Folder | Entry | Formats | Reached as |
|---|---|---|---|
| `dpia` | `render.py` | docx | template `dpia` |
| `evidence-summary` | `render.py` | docx | template `evidence-summary` |
| `docx-generic` | `render.py` | docx | template `docx-generic` |
| `pptx-generic` | `render.py` | pptx | template `pptx-generic` |
| `xlsx-generic` | `render.py` | xlsx | template `xlsx-generic` (+ recalc gate) |
| `ciso-reporting` | `render.py` | pptx, pdf, html, png | template `ciso-reporting` |
| `ciso-global` | `generate_slide.js` | pptx | template `ciso-global` |
| `ciso-exec-summary` | `render.py` | html, pdf | template `ciso-executive-summary-html` (`renderer_pending`) |
| `tprm-board-slide` | `render.py` | pptx | template `tprm-board-slide` (`renderer_pending`) |
| `form-b-fill` | `render.py` | xlsx | template `form-b-fill` (takes the original OneTrust export as `{input}`) |
| `transcript` | `render.py` | md, html, docx | template `transcript` (Speech/WhisperX diarized output) |
| `charts` | `render.py` | png, svg | template `charts` |
| `diagrams` | `generate_slide.js` | svg, png | template `diagrams` |
| `whisperx` | `scripts/extract_speaker_clips.py` | — | endpoint `POST /api/speaker_clips` |
| `pdf-coverage` | `scripts/*.py` | — | endpoint `POST /api/pdf/{stage}` |

The last two are **not** render templates: the Function builds the script path
itself, so their `manifest.json` `entry` intentionally points into `scripts/`
(the verified layout) rather than at a root entry file.

## Adding a renderer

1. Create `renderers-src/<id>/render.py` (or `generate_slide.js`) plus
   `manifest.json`; take the contract from a `templates/<id>.schema.json` and
   add a sanitised sample under `templates/samples/`.
2. Register it in `templates/registry.json` (`renderer`, `schema`, `sample`,
   `consumers`, `pipelines`) and add the folder to `stage_renderers.SOURCES`,
   or it is never staged and `/api/render` answers 404.
3. Validate: `python3 render.py sample.json out/` (or `node --check`),
   `python3 -m json.tool manifest.json`, then the `/api/render` smoke of
   `operations/CHANGE_MANAGEMENT.md` §4 against the comparison set.
