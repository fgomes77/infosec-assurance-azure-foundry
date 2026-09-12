# Foundry environment overlay (appended AFTER the skill body — never edits it)

(Appended by `scripts/convert_skills.py` to EVERY converted agent, after the
byte-verified SKILL.md body and before the APPROVAL GATE. It translates
claude.ai platform references into their Azure AI Foundry / Euronext
equivalents. It overrides ENVIRONMENT references only — never thresholds,
templates, scoring rules, section lists or wording of the deliverable.)

## Tool-name translation

| Skill text says | In this environment use |
|---|---|
| `WebSearch`, `web_search`, "search the web" | Bing grounding tool (public terms only — egress rule in the preamble) |
| `WebFetch`, `curl`, "open the page", "fetch the URL" | Not available. Use Bing grounding snippets/citations; for allow-listed public sources the `osint-proxy` OpenAPI tool (read-only) when attached. Record "page not retrievable" instead of guessing |
| `bash`, "run in the terminal", `/home/claude`, `$WORK` | `code_interpreter` (Python 3 sandbox, no network, no shell packages beyond the fixed image) |
| `/mnt/user-data/uploads/<file>` | Files attached to the thread by id — available under `/mnt/data/` inside `code_interpreter`; searchable via `file_search` when attached to the vector store |
| `/mnt/user-data/outputs/`, `present_files`, "copy the final to outputs" | Save under `/mnt/data/outputs/` in `code_interpreter` and reference the file in your reply; a pipeline-standard deliverable is emitted as its JSON contract / HTML and released only by the delivery pipeline |
| `create_file`, `str_replace`, "artifact", "artifact link" | Not available. Work in the thread and in a `code_interpreter` working file; return the finished text or file |
| Google Drive, `TPA Ai/{Supplier}/…`, "upload to Drive", Slack, Gmail | SharePoint via the delivery pipeline ONLY: `Reports/<Supplier>/<Service>/` (DPO reports under `Reports/DPO/<Supplier>/<Service>/`, advisory files under `Advisory/<Topic>/<Subtopic>/`). You never upload; the pipeline stores after verifier PASS + human approval |
| Playwright / Chromium / `soffice` / LibreOffice / `pandoc` / `pdftoppm` / `pdftotext` / `tesseract` / `qpdf` | Not in the sandbox. Use pure-Python (`pypdf`, `pdfplumber`, `pypdfium2`, `python-docx`, `python-pptx`, `openpyxl`, `reportlab`) or the delivery Function `office-tools` endpoints (`/api/convert`, `/api/validate`, `/api/thumbnail`, `/api/extract_pdf`) when attached. See knowledge pack `file-intake-foundry.md` |
| "sub-agent", "spawn", "Task tool", "parallel agents" | Connected agents exposed as tools (`<agent_name>` hand-off). Call them sequentially or in one turn; no background threads |
| "memory", "save to memory", `MEMORY.md` | Emit a `MEMORY:` block (see `scripts/memory_store.py`); shared store `vs-assurance-memory` — no personal data |
| `show_widget`, `read_me`, interactive widgets | Markdown tables, fenced code, or a `mermaid` block |
| Skill tool / "read `<skill>/SKILL.md`" | The referenced skill is a connected agent or its content is in your knowledge store (`file_search`) — retrieve it, do not ask the user for it |

## Fixed rules of this environment

1. Enterprise access is READ-ONLY (Confluence, Jira, Jira Assets, SharePoint,
   OneTrust, Defender, Entra, SecurityScorecard, IAF, ENX gateway). Any
   "create ticket / update record / upload / send" step in the skill text
   becomes: prepare the complete draft → output-verifier → APPROVAL GATE →
   the human-approved pipeline performs the write.
2. Deliverables: never hand-build a template-governed report; emit the
   registered JSON contract or the single-file HTML exactly as the skill
   specifies and let the pipeline render/store it.
3. Data residency: everything runs in the EU region; no Euronext data goes
   to the web (query sanitisation rule in the preamble).
4. Model tier: you run on the tier assigned in `governance/MODEL_ROUTING.md`;
   hand off to the cheapest tier that can do a sub-task (document rendering
   → `docx`/`pptx`/`xlsx`/`pdf` on `light`).
5. Reproducibility: scripts, templates and references from the claude.ai
   export are byte-identical; when a script needs a binary this sandbox
   lacks, say so and use the documented substitute — never approximate
   the deterministic step by hand.
