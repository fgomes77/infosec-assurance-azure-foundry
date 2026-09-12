# Reading PDFs in Microsoft Foundry (knowledge pack)

*(Microsoft Foundry — formerly Azure AI Foundry.)*

*Authored 2026-09-12; adapted from the claude.ai `pdf-reading` platform
skill and its REFERENCE.md to the pure-Python `code_interpreter` sandbox.
Attached to the analyzers, dpia, ciso-* agents, pdf and
pdf-full-coverage-analyzer.*

## 1. Inventory first (never read blind)

```python
from pypdf import PdfReader
r = PdfReader(path)
n = len(r.pages); enc = r.is_encrypted
meta = dict(r.metadata or {})
fields = r.get_fields()                       # AcroForm fields (OneTrust exports, questionnaires)
attachments = list(getattr(r, "attachments", {}).keys())  # embedded files (evidence bundles)
sample = [ (i, len((r.pages[i].extract_text() or "").strip()))
           for i in {0, 1, n//2, n-2, n-1} if 0 <= i < n ]
```
Decide per page: **text layer present** (extract) vs **no/garbled text**
(scanned, doubled characters, font without ToUnicode) → rasterise/OCR path.

## 2. Text and tables

- Text: `pdfplumber.open(path).pages[i].extract_text()` (layout-aware),
  fall back to `pypdf` per page. Normalise OCR artefacts (doubled
  characters "Aces s" → "Access", split words) BEFORE matching field names.
- Tables: `page.extract_tables()`; for ruled tables use
  `table_settings={"vertical_strategy":"lines","horizontal_strategy":"lines"}`,
  for whitespace tables `"text"`. Validate column counts against the header.
- Form fields: `r.get_fields()` returns name → value; OneTrust exports
  often carry answers as field values that are absent from the text layer.
- Large documents: process in chunks of ≤25 pages, write per-chunk JSON,
  verify coverage (every page index accounted for) — the
  pdf-full-coverage-analyzer scripts implement this.

## 3. Page rendering (instead of pdftoppm)

```python
import pypdfium2 as pdfium
pdf = pdfium.PdfDocument(path)
img = pdf[i].render(scale=2).to_pil()   # 144 dpi
img.save(f"/mnt/data/outputs/page_{i+1}.png")
```
Use only for pages that need visual inspection (stamps, signatures,
certificate seals, diagrams). Image inspection requires a vision-capable
deployment; reasoning-tier agents hand the images to the pipeline (chat
tier) or to Document Intelligence rather than guessing.

## 4. Scanned or garbled pages → Document Intelligence (EU region)

- Call the delivery Function `POST /api/extract_pdf` (`prebuilt-read` for
  text, `prebuilt-layout` for tables) with the file id or the page range.
- Never use `pytesseract`/local OCR (absent) and never a public OCR
  service. Record "OCR via Document Intelligence, confidence X" in the
  sources; low-confidence passages are quoted with "(OCR)".

## 5. Encrypted PDFs

`r.decrypt(password)` with the user-supplied password; empty-string owner
passwords are tried first. The password is never written to outputs or
memory. Permissions-only encryption (no user password) opens with `""`.

## 6. Cost table (keep the context small)

| Content | Approx. tokens | Rule |
|---|---|---|
| 1 page of dense text | 600–900 | Extract, do not quote whole pages |
| 1 table row | 20–60 | Convert to JSON, quote only relevant rows |
| 1 rendered page image | 1,000–1,500 (vision) | Render only the pages that need it |
| 100-page SOC report | 60–90 k | Chunk + per-chunk JSON; never load whole |
| 300-page pentest with screenshots | 150 k+ | Chunk; images listed, not attached |

## 7. Reading guides by document class

- **OneTrust InfoSec Form PDF:** field/value pairs; residual-risk scores
  and classification often appear on the last pages; verify totals.
- **SOC report:** Section I opinion (pages 2–6), Section III system
  description, Section IV tests/exceptions (bulk), Section V other
  information (unaudited). See `soc-isae-assurance-reports.md`.
- **Pentest report:** executive summary + findings table + appendix with
  evidence; severity legend defines the scale. See
  `pentest-standards-owasp-ptes-cvss.md`.
- **Certificates:** one page; issuer, scope statement, dates, certificate
  number, accreditation mark. See `tpa-evidence-review-playbook.md`.
