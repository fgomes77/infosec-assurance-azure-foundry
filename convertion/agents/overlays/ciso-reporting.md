# ciso-reporting — Foundry overlay

(Appended after the SKILL.md body; environment mapping only.)

- Playwright/Chromium are NOT present. The A3 PDF and the section PNGs are
  produced by the delivery Function (`office-tools` `/api/convert`,
  HTML→PDF→PNG) during the `cyber-forum-pptx` pipeline; your job ends at
  the **verified assessment JSON** + the HTML dashboard. Do not "degrade
  gracefully" by skipping the PDF — state that rendering is delegated.
- `--outdir /mnt/user-data/outputs` → `/mnt/data/outputs/` in `code_interpreter`
  (the orchestrator script and its Python renderers run there; Node-only
  steps are executed by the Function renderer `ciso-reporting-deck`).
- Storage: `Reports/<Supplier>/<Service>/` via the pipeline after
  verifier PASS + approval. Intake: Supplier name + Service name.
- OneTrust PDFs are read with the pure-Python path in knowledge pack
  `pdf-reading-foundry.md`; scanned pages go to Document Intelligence via
  the Function, never to local OCR.
