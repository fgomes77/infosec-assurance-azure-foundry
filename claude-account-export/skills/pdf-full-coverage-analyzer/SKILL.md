---
name: pdf-full-coverage-analyzer
description: "Exhaustive, accuracy-grade PDF analysis: process documents of any size in deterministic chunks and guarantee every line is read, every detail preserved, every passage understood in context — for any topic (legal, medical, scientific, technical, financial, regulatory, narrative, transcript). ALWAYS use when the user asks to analyze, review, audit, summarize, or extract from a PDF and any of these holds: (a) the PDF is large or its size unknown; (b) the user says 'all lines', 'every detail', 'nothing missed', 'full coverage', 'exhaustive', 'in parts', 'page by page', 'analyze carefully', 'maintain accuracy', or 'analyze the context'; (c) accuracy and completeness matter more than speed; (d) the document carries real stakes (contracts, regulations, medical records, research, filings, specs, evidence, transcripts). Performs triage → inventory → chunked extraction → context-and-detail analysis → synthesis → coverage verification, with a verifiable audit trail. Trigger on partial requests too."
license: User-owned. Built for Francisco Gustavo Gomes.
metadata:
  version: "2.0.0"
---

# PDF Full-Coverage Analyzer

Process any PDF — any size, any topic — in deterministic chunks. **Read every word. Capture every layer. Preserve every detail. Understand every context. Prove it.**

This skill exists because language models routinely skim long PDFs, hallucinate from headers, summarize away nuance, miss content trapped in tables / annotations / charts, and confidently report on documents they only partially read. This skill makes that impossible. The pipeline produces a verifiable audit trail showing that every page, every line, every word, and every declared content layer was processed.

## When to use this skill

Use whenever **accuracy and completeness matter** and the PDF is non-trivial. Trigger phrases:

- "Analyze this PDF carefully" / "Go through the whole document"
- "Extract every X" / "Find every reference to Y" / "List all Z"
- "Don't miss anything" / "Don't lose any detail" / "Be exhaustive"
- "Understand the context" / "What is this document really saying"
- "Review this contract / report / paper / record / filing"
- "This is a 300-page PDF" / "It's a long document"

For a 1–2 page PDF visible in one glance, this skill is overkill — read directly.

## What "full coverage" means here

The skill guarantees coverage at **five independent levels**, all checked at the end:

| Level | What it proves | Threshold |
|---|---|---|
| **Pages** | every PDF page appears in some chunk | 100% (strict) |
| **Words** | sum of chunk word counts ≥ inventory baseline | ≥ 95% |
| **Characters** | sum of chunk non-whitespace chars ≥ inventory baseline | ≥ 95% |
| **Layers** | for every page with tables / annotations / images-with-text, the corresponding section appears in chunks | 100% |
| **Lines** | reported informationally (lines vary across extractors) | flagged if < 70% |

The inventory baseline itself is **paranoid**: it runs three independent text extractors (pdfplumber, pdftotext, PyMuPDF) per page and takes the **maximum** word/char count seen by any of them. Anything one extractor misses, another catches, and the maximum sets the bar.

If you want one more layer of certainty, run the optional **cross-check** script (Stage 5b) — it rasterises pages and OCRs them, then reports words present in the rendered page but absent from extraction. That catches text trapped in images, charts, watermarks, or skipped by every extractor.

## What content gets captured per page

Every page block in a chunk file declares the layers it captured:

```
[page 21]
--- BODY ---           <body text, from whichever method extracted most>
--- TABLES ---         <pdfplumber-extracted tables, pipe-delimited>
--- ANNOTATIONS ---    <sticky notes, highlights, comments — content + author + highlighted text>
--- IMAGE_TEXT_OCR --- <OCR of page raster — only when image_text_ocr_recommended>
```

If a layer is absent on the page, the marker still appears with `<no tables>` / `<no annotations>` — that proves the layer was checked and nothing was silently skipped. Stage 5 verifies every layer the inventory said exists has its marker in the corresponding chunk.

---

## Workflow (5 stages, + optional 5b)

Each stage has a dedicated script under `scripts/`. Run them in order.

### Stage 1 — Triage

```bash
python3 <skill-path>/scripts/triage.py <input.pdf> --out triage.json
```

Outputs page count, encryption, text-extractability, scanned-page ratio, font health, and a recommended chunking strategy. See `references/strategy-matrix.md`; the short version:

| Page count | Scanned? | Chunk size | Method |
|---|---|---|---|
| ≤ 20 | No | full doc | `pdftotext -layout` |
| 21–150 | No | 10 pages | `pdfplumber` |
| 151–500 | No | 5 pages | `pdfplumber` |
| 501–1000 | No | 3 pages | `pdfplumber` |
| > 1000 | No | 2 pages | `pdfplumber` + `--stream` |
| any | Yes (>50%) | 1 page | OCR (`--ocr`, DPI 300) |
| any | Mixed (10–50%) | 5 pages | hybrid: text + OCR per page |
| any | encrypted | STOP | ask user for password |

Override smaller for: heavy tables, legal text where every clause matters, multi-column layouts.

### Stage 2 — Multi-method inventory (the audit anchor)

```bash
python3 <skill-path>/scripts/inventory.py <input.pdf> --out inventory.json
```

For every page, runs three extractors in parallel and records:

- **lines / words / chars** per method (so you can see which method captured most)
- **expected_words / expected_chars / expected_lines** = MAX across methods (the baseline)
- **layers detected**: `has_body_text`, `has_tables`, `has_annotations`, `has_images`, `has_rotated_text`, with counts
- **divergence_warnings**: pages where methods disagreed on word count by > 20% (potential gap)
- **pages_requiring_ocr_followup**: pages with near-zero extractable text (scanned)
- **image_text_ocr_recommended**: pages with images but sparse text (text might live in an image)
- **document-level**: form-field presence, bookmark/TOC tree

If the inventory flags `pages_requiring_ocr_followup` or `image_text_ocr_recommended`, decide before proceeding:
- Re-run `chunk_extract.py --ocr-pages …` for fully scanned pages
- Re-run with `--image-text-pages …` to add OCR of page rasters alongside body text for pages with image content

### Stage 3 — Multi-layer chunked extraction

```bash
python3 <skill-path>/scripts/chunk_extract.py <input.pdf> \
    --chunk-size <N> \
    --output-dir ./chunks/
```

Optional flags:
- `--ocr` — OCR every page (fully scanned PDFs)
- `--ocr-pages 12,13,14` — OCR only these specific pages
- `--image-text-pages 5,8,9` — keep text extraction AND add image-OCR for these pages
- `--capture-tables on|off` (default `on`)
- `--capture-annots on|off` (default `on`)
- `--stream` — write each chunk to disk immediately, don't buffer (for very large PDFs)

Per chunk, produces `chunks/chunk_NNN.txt` with the header:

```
=== CHUNK 3 | pages 21-30 | lines 412-587 | words 3120-4205 | chars 21888-29345 | sha256:... ===
```

and per-page layer-delimited content. For each page, the extractor picks the **longest** of the three text methods (most non-whitespace chars) for the BODY section, so methods that happen to truncate on a specific page don't determine the output.

### Stage 4 — Per-chunk analysis (context + detail)

This is where accuracy is won or lost. For every chunk file, apply a **consistent two-axis analysis** — never substitute summarization for it. Process one chunk at a time. Use the template in `references/analysis-patterns.md`.

For each chunk, produce a JSON record with both **CONTEXT** and **DETAILS**:

```json
{
  "chunk": 3,
  "pages": [21, 22, "...", 30],
  "context": {
    "what_this_section_is_about": "...",
    "document_role": "background | argument | evidence | conclusion | appendix | ...",
    "structural_position": "...",
    "key_entities_introduced": ["..."],
    "key_entities_referenced": ["..."],
    "relation_to_prior_chunks": "...",
    "open_threads_for_later_chunks": ["..."]
  },
  "details": [
    {
      "page": 23,
      "type": "fact | claim | definition | number | name | date | condition | requirement | exception | citation | example | other",
      "content": "the detail itself, faithfully paraphrased",
      "exact_quote_if_critical": "≤15 words verbatim, only when wording matters legally/technically",
      "qualifiers": "any caveats or conditions"
    }
  ],
  "open_questions": ["..."],
  "user_query_relevance": "high | medium | low | none",
  "extraction_quality_notes": "..."
}
```

**Rules that protect accuracy:**

1. **Process one chunk at a time.** Don't try to "feel out" the whole document. The point of chunking is undivided attention per chunk.
2. **Distinguish text from inference.** Inferences go in `context`; facts in the text go in `details`. Never mix.
3. **Anchor every detail to a page.** Always `[page N]`. Always.
4. **Verbatim only when wording matters.** For legal / technical / contractual / clinical text, capture the exact quote (≤ 15 words). Otherwise paraphrase faithfully.
5. **Process every layer.** When a chunk has `--- TABLES ---`, `--- ANNOTATIONS ---`, or `--- IMAGE_TEXT_OCR ---` sections, extract details from them too — don't only read BODY.
6. **No skipping.** If a chunk's content seems irrelevant, record `"user_query_relevance": "none"` with a one-line context note. Silence equals data loss.
7. **No premature synthesis.** Save the whole-document meaning for Stage 5.
8. **Handle uncertainty honestly.** OCR noise, ambiguous wording, layout glitches → say so in `extraction_quality_notes`.

### Stage 5 — Coverage verification

```bash
python3 <skill-path>/scripts/verify_coverage.py \
    --inventory inventory.json \
    --chunks ./chunks/ \
    --out coverage_report.json
```

Verdict possibilities:

- **`COMPLETE`** — pages 100%, words ≥ 95%, chars ≥ 95%, every declared layer captured. **Only then proceed to synthesis.**
- **`PARTIAL`** — something below threshold. List the gaps, tell the user, ask how to close them (OCR specific pages? re-extract with different settings? accept the gap?).
- **`INVALID`** — duplicate pages, extra pages, malformed chunk headers. Re-run extraction.

### Stage 5b — Cross-check (optional, paranoid)

```bash
python3 <skill-path>/scripts/cross_check.py \
    --pdf input.pdf \
    --chunks ./chunks/ \
    --pages all \
    --out cross_check.json
```

For specified pages, rasterises at 300 DPI and OCRs the rendered image, then compares word sets against the chunk content. Reports words present in OCR but missing from extraction — the ultimate "did we miss anything visible on the page?" check.

**When to run cross-check:**
- High-stakes documents (contracts, regulatory filings, medical, legal evidence)
- Documents with mixed content (charts, infographics, scanned-looking pages)
- Any time the verify_coverage report flagged `divergence_warnings`
- On a random 5–10% sample of pages for spot-check confidence

Recall ≥ 98% is normal noise. < 95% suggests a real coverage gap — inspect `missing_words_sample` to judge.

---

## Cross-chunk synthesis (after Stage 5 returns COMPLETE)

With the per-chunk JSONs in hand, build the user's actual answer.

- **"Extract every X"** → walk every chunk's `details`, pick entries where `type` or `content` matches X, deduplicate (preserve qualifiers), cite pages.
- **"Summarise"** → walk every chunk's `context`, weave them into a structural summary, pull in details only where they exemplify or anchor summary points.
- **Specific question** → pull `details` from chunks with `user_query_relevance` of high/medium, plus `context` from neighbouring chunks for proper meaning. If the document does not answer the question, say so explicitly.

Always: flag contradictions between chunks, flag silence when the user's question implies the document should address it, carry forward `extraction_quality_notes`.

---

## Final deliverable to the user

1. **Direct answer** with `[page N]` citations on every claim.
2. **Coverage statement**: *"Read X pages, Y words, Z characters across N chunks. Verdict: COMPLETE."*
3. **Per-chunk context map** (when long / multi-topic) — table mapping chunk → pages → what it's about.
4. **Audit artefacts**: `triage.json`, `inventory.json`, `coverage_report.json`, optionally `cross_check.json`, plus `./chunks/`.
5. **Honest limitations**: OCR confidence, ambiguities, gaps explicitly flagged.

---

## Edge cases and accuracy guards

### Scanned PDFs
Triage flags scanned ratio ≥ 50% as `ocr_per_page`. OCR at DPI 300; for old/faxed documents, 400.

### Mixed text + scans
`inventory.py` auto-flags `pages_requiring_ocr_followup`. Re-run `chunk_extract.py --ocr-pages …` before Stage 4.

### Pages with images that might contain text
`inventory.py` flags `image_text_ocr_recommended`. Re-run with `--image-text-pages …` so chunks get text extraction AND OCR of the page raster.

### Tables
The `--- TABLES ---` section uses pdfplumber's table detection. Scrambled? Flag in `extraction_quality_notes`; consider rasterising for visual inspection.

### Annotations / comments / sticky notes
PyMuPDF reads them in Stage 3, captured under `--- ANNOTATIONS ---` with author, subject, content, AND underlying highlighted text.

### Multi-column layouts
Body extractor picks the longest result among the three methods. If scrambled, flag in `extraction_quality_notes`.

### Garbled fonts (mojibake)
Run `pdffonts`. Re-run affected pages with `--ocr-pages …` to recover via OCR.

### Forms
Detected at document level. Extract field values via `pypdf.get_fields()` as a sidecar.

### Encrypted PDFs
Stop. Ask for password / unlocked copy.

### Very large PDFs (> 1000 pages)
Use `--chunk-size 2 --stream`. Run Stage 4 in batches. Coverage verification operates on disk and doesn't need analyses in-context.

### Token budget on very long documents — "skim and dive"
1. First pass: read only `inventory.json` and chunk headers to build a map.
2. Identify chunks relevant to the user's question.
3. Deep-read only those chunks.
4. **Coverage is still verified for all chunks** — extraction happened on disk for everything. Be explicit about which chunks were deep-analysed vs only mapped.

---

## Reference files

- `references/strategy-matrix.md` — chunking strategy decision matrix with rationale.
- `references/output-schema.md` — exact JSON schemas for every artefact.
- `references/analysis-patterns.md` — per-chunk context-and-detail template + adaptations for different document types.
- `references/completeness-guarantees.md` — how the five-level coverage check works and what each level catches.

---

## Mantras

1. **Inventory before analysis.** Build "expected" before producing "actual" — that's what makes coverage provable.
2. **Three extractors, take the MAX.** No single method is trusted; the most generous count sets the bar.
3. **Capture every layer.** Body, tables, annotations, image-text, forms, bookmarks — each gets its own marker.
4. **One chunk at a time.** Undivided attention per chunk is how detail survives at scale.
5. **Cite the page.** Every claim, every detail — anchored.
6. **Verify before delivering.** No result is final until the coverage gate returns `COMPLETE`.
7. **Cross-check when stakes are high.** OCR of the rendered page is the final word on what's actually there.
8. **Honest about limits.** Flag OCR noise, ambiguity, gaps.
