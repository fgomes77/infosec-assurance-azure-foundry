# Document-agents addendum (docx · pdf · pptx · xlsx)

(Appended by `scripts/convert_skills.py` after the byte-verified SKILL.md
body of the four Anthropic document skills, before the APPROVAL GATE. It
maps the skills' binary tool-chain to what exists in this environment and
binds their outputs to the delivery pipelines. It never changes the
skills' editing rules, validation semantics or file formats.)

## Runtime map

| Skill step | Here |
|---|---|
| Node `docx` / `pptxgenjs` / `react-icons` / `sharp` create path | Not in `code_interpreter`. (a) Preferred: `python-docx` / `python-pptx` for ordinary documents; (b) for pixel-faithful template decks or the skill's Node pipeline: emit the data JSON (or the generated `.js` script) and call the delivery Function renderer `docx-generic` / `pptx-generic` (Node 20 in the Function) through the `generic-docx-deliverable` / `generic-pptx-deliverable` pipeline |
| `unzip` → edit XML → `zip`, `merge_runs.py`, `validate.py`, `comment.py`, `clean.py`, `add_slide.py` (pure Python) | Run as-is in `code_interpreter` from the `<skill>-scripts.zip` package (unzip it first; keep the `office/` package directory so `from office.helpers …` imports work) |
| `pandoc`, `markitdown`, LibreOffice (`soffice.py`, `accept_changes.py`, `thumbnail.py`), `pdftoppm`, `qpdf`, `pdftk`, `tesseract`, ImageMagick | Not in the sandbox. Read: `python-docx` / `python-pptx` / `openpyxl` / `pypdf` / `pdfplumber`. Convert / render / accept-changes / thumbnails / formula recalculation: the **office-tools** Function (`/api/convert`, `/api/accept_changes`, `/api/thumbnail`, `/api/validate`, `/api/recalc`) — note `/api/extract_pdf` is on the DELIVERY Function, not here (see "Which Function serves which endpoint" below); otherwise state that the step is delegated to the pipeline and skip the visual check, never claim it was done |
| `.xsd` schema validation (`validate.py`) | Schemas ship inside `<skill>-scripts.zip`; run the validator from the unzipped tree |
| Visual QA "render to PDF → images → look" | Function `/api/convert` + `/api/thumbnail`; the images come back to the conversation. If unavailable, perform the structural checks only and say so |
| OCR of scanned PDFs (`pytesseract`) | Azure AI Document Intelligence (EU region) via the **delivery** Function's `/api/extract_pdf` — Document Intelligence is reachable only from there; never local OCR, never a public OCR site |
| `/mnt/user-data/outputs/` | `/mnt/data/outputs/` |

## Fallback order for any PDF task

1. pure-Python (`pypdf`, `pdfplumber`, `pypdfium2`, `reportlab`) →
2. Function `office-tools` (poppler/qpdf in the container) →
3. Document Intelligence (scanned/garbled pages) — see knowledge pack
   `pdf-reading-foundry.md`. Each fallback is recorded in the output's
   sources section.

## Secrets and encrypted files

- PDF/Office passwords supplied by the user are used once, in the
  sandbox, and never echoed in outputs, memory blocks or logs; decrypted
  copies live only under `/mnt/data/` for the run and are not delivered
  unless the user explicitly asks for the decrypted document.
- Never request or store certificates, private keys or credentials
  embedded in documents; redact them in outputs.

## Delivery binding

- A Word/PowerPoint/Excel deliverable the user wants **stored** is
  emitted through the generic pipelines (`generic-docx-deliverable`,
  `generic-pptx-deliverable`, `xlsx-generic` template) → output-verifier
  → human approval → `Reports/<Supplier>/<Service>/` (or
  `Advisory/<Topic>/<Subtopic>/`). Ask for Supplier and Service (or
  Topic/Subtopic) at intake. Files returned in the conversation only are not
  records.
- House style for anything generated (unless a registered template
  governs it): Verdana; headings/accents teal RGB(0,141,127); severity
  colours red/amber/green per High ≥7.0 / Medium ≥4.0; classification
  "Euronext Internal"; title, date and sources section present. The
  skills' own Anthropic palette examples are NOT used for Euronext
  deliverables.
- Model tier: `light` (deterministic transformation). If a task needs
  judgement (what to write, how to score) hand it back to the requesting
  agent — you format, you do not assess.
