# Completeness Guarantees

How this skill proves nothing was missed — and the cases where it can still miss.

## The five coverage levels

Coverage is verified at five independent levels. Each catches a different failure mode of PDF extraction.

### 1. Page coverage (must be 100%)

**What it proves:** every page of the PDF was processed. None were silently skipped due to encryption errors, page-range bugs, or chunk-size arithmetic mistakes.

**How:** the inventory enumerates every page from `pdfinfo`. The chunk verifier collects `[page N]` markers from every chunk file and confirms the set matches.

**Catches:** entirely-missed pages, off-by-one chunk boundaries, duplicate pages (one page in two chunks), extra pages (a chunk page marker that isn't in the inventory).

**Does not catch:** content missed *within* a page.

### 2. Word coverage (must be ≥ 95%)

**What it proves:** the chunks contain at least 95% of the words the most-generous text extractor saw.

**How:** for every page, three extractors run in parallel (pdfplumber, pdftotext, PyMuPDF). The maximum word count across them sets the page's "expected" baseline. Sum across pages = `total_expected_words`. The chunk extractor picks the longest method per page for the BODY section, and chunk headers record actual word counts. Stage 5 reconciles.

**Catches:** large content gaps where one method extracted X words but the chunk has 0.7X.

**Why 95% not 100%:** chunks use one method per page (whichever extracted most), while the baseline is the max-of-three. On some pages, method A wins; on others, method B. So chunks may have slightly less than baseline on a per-page basis even when nothing is actually missing.

**Why the threshold isn't tighter:** because the baseline is paranoid. A 95% match against the most-generous baseline means almost all content was captured.

### 3. Character coverage (must be ≥ 95%)

**What it proves:** beyond just word counts, the actual character content matches.

**How:** same multi-method approach as words, but counting non-whitespace characters. Catches cases where word counts agree by coincidence but character lengths differ (e.g., one method truncated long words or numbers).

**Catches:** truncated multi-character tokens (long URLs, identifiers, numbers), encoding issues, character-level extraction bugs.

### 4. Layer coverage (must be 100%)

**What it proves:** every PDF content layer the inventory detected has its corresponding section in chunks.

**Layers tracked:**
- `BODY` — main text content
- `TABLES` — pdfplumber-detected tabular content
- `ANNOTATIONS` — sticky notes, highlights, comments, sticky-text
- `IMAGE_TEXT_OCR` — OCR of page raster for pages with image content

**How:** inventory's `layers` dict per page lists `has_tables`, `has_annotations`, etc. Chunk files include `--- LAYER ---` markers per page. Stage 5 cross-checks: if `has_tables: true`, the chunk's page block must include `--- TABLES ---`.

**Catches:** a chunk that processed body text but silently skipped a table on the page; annotations that the extractor didn't read; image-text-OCR not run when it was recommended.

### 5. Line coverage (informational; flagged if < 70%)

**What it proves:** approximately the same volume of line breaks were preserved.

**Why informational only:** line counts vary dramatically by extraction method. `pdftotext -layout` preserves spatial spacing as extra blank lines; `pdfplumber.extract_text()` reflows. A 92% line coverage might mean nothing was lost — just that one method's whitespace-handling differs from another's.

**Catches:** extreme line-count loss (< 70%), which signals real structural content loss.

---

## The optional Stage 5b cross-check

For high-stakes documents, the verify gate can be reinforced with a rasterize-and-OCR comparison.

**What it does:** for specified pages (or all), `cross_check.py`:
1. Rasterises the page at 300 DPI
2. Runs Tesseract OCR on the rendered image to recover every visible glyph
3. Tokenises both the OCR output and the chunk's text for that page
4. Reports words present in OCR but absent from the chunk

**What it catches that the first five levels do not:**
- Text rendered as vector graphics (charts, infographics, logos)
- Watermarks and stamps that text extractors ignore
- Headers/footers excluded by extraction settings
- Rotated or skewed text
- Text inside embedded images that wasn't flagged for image-text-OCR

**Interpretation:**
- **≥ 99% recall** → normal OCR noise; coverage is solid.
- **95–99% recall** → likely OCR noise OR a small extraction gap. Inspect `missing_words_sample`.
- **< 95% recall** → real coverage gap. Investigate immediately.

**When to run it:**
- Contracts, regulatory filings, court documents, medical records — anywhere a missed word has consequences.
- Documents flagged with `divergence_warnings` in the inventory.
- Documents with charts, infographics, or scanned-looking pages.
- Random 5–10% page sample for routine confidence checks.

---

## What this skill can still miss (honest limitations)

No PDF extraction pipeline is perfect. Here is what can still go wrong even with all five coverage levels green.

### Vector-graphic text

PDFs can render text as vector paths instead of as text objects. Common in:
- Infographics
- Charts from R, matplotlib, Excel
- Logos
- Some PowerPoint exports

Text extractors see nothing on those pages. The inventory flags such pages with `has_images: true` and sparse text → recommendation: run `--image-text-pages …` so the page raster is OCR'd alongside text extraction. **If you don't act on `image_text_ocr_recommended`, vector-graphic text will be missed.**

### Text in raster images embedded in text pages

Same principle as above, but on otherwise-text pages where a single embedded image carries critical content (e.g., a diagram label, a stamp, a scan-of-signature page).

**Mitigation:** Stage 5b cross-check will catch this if you run it.

### OCR errors on scanned pages

Tesseract's recognition accuracy on clean modern scans is ~98–99%. On old, faxed, or low-DPI scans it drops to 85–95%. The skill cannot recover what OCR fails to read.

**Mitigation:** raise DPI to 400, or pre-clean the source (deskew, denoise). For critical pages, manually proofread against a rendered page image.

### Hand-written annotations on scanned pages

Tesseract reads printed text only. Handwritten margin notes on scanned legal/medical documents will not be captured by the OCR path.

**Mitigation:** flag manually for human review.

### Layers that PyMuPDF cannot see

The skill captures: body text, tables (via pdfplumber), annotations (via PyMuPDF), form fields (via pypdf), bookmarks (via PyMuPDF), images (detected, optionally OCR'd).

Not captured by default:
- 3D models embedded in PDFs (very rare)
- Audio/video annotations (very rare)
- JavaScript actions / form behaviour
- File attachments — listed in `triage.json`'s `has_attachments` flag; if true, extract separately with `pdfdetach -saveall`

**Mitigation:** if `has_attachments` is true, extract attachments manually and run the analysis on them.

### Content order in scrambled multi-column / overlapping layouts

Text extractors generally preserve reading order, but on heavily designed pages (magazines, brochures, posters) the order can be wrong even if every word is captured.

**Mitigation:** flag such pages in `extraction_quality_notes`; consider rasterising for visual inspection.

### Semantic accuracy of paraphrase

This is the analysis layer (Stage 4), not the extraction layer. The skill captures every word but the analyst (Claude) writes the per-chunk JSON. Paraphrasing errors are possible — that is why the schema includes `exact_quote_if_critical` for cases where wording matters, and why the chunk file itself preserves the verbatim text for inspection.

**Mitigation:** keep the chunks. The user can always go back to the source text for any chunk and verify a finding.

---

## Practical guidance

| Stakes level | Recommended verification depth |
|---|---|
| Casual / informational | Stages 1–5; accept `COMPLETE` verdict |
| Professional / business | Stages 1–5 + cross-check on 5–10% page sample |
| Legal / regulatory / clinical | Stages 1–5 + cross-check on all pages; manual review of any chunk flagged with `extraction_quality_notes` |
| Litigation / certification evidence | All of the above + manual proofread of critical sections against rendered page images |

The skill cannot remove the need for human judgment on critical documents — but it can guarantee that the human reviewer is working from a complete, audit-trailed extraction rather than a confident skim.
