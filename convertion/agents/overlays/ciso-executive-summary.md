# ciso-executive-summary — Foundry overlay

(Appended after the SKILL.md body; environment mapping only.)

- `scripts/html_to_pdf.py` / `render_sections.py` need Playwright, which
  is absent in `code_interpreter`; the `ciso-exec-summary` pipeline calls
  the delivery Function to render PDF/PNG from your verified HTML. Produce
  the HTML (template `ciso-executive-summary-html`) and the extracted JSON;
  do not fabricate PDF/PPTX by hand.
- `/home/claude/...` and `/mnt/user-data/outputs/` → `/mnt/data/outputs/`.
- Storage: `Reports/<Supplier>/<Service>/` (pipeline). Intake: Supplier +
  Service names.
- OCR-noisy OneTrust PDFs: apply `pdf-reading-foundry.md` (pypdf/pdfplumber;
  Document Intelligence for scanned pages).
