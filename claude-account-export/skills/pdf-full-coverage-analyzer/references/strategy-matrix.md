# Chunking Strategy Matrix

Use this matrix to pick the right `--chunk-size` and extraction method.
The defaults in `triage.py` already implement these rules; this document
explains the *why*.

## Decision factors

1. **Page count** — drives chunk granularity.
2. **Text-extractability** — text-layer vs scanned vs hybrid.
3. **Token budget** — every chunk you read into context costs tokens.
4. **Audit granularity required** — tighter chunks = more precise citations.

## Matrix

| Page count | Scanned ratio | Chunk size | Method | Notes |
|---|---|---|---|---|
| 1–20 | < 10% | full doc (1 chunk) | `pdftotext -layout` | Small enough to fit in one pass. Still produce a chunk file for audit trail consistency. |
| 21–150 | < 10% | 10 pages | `pdfplumber` | Default sweet spot for most ENX vendor reports, SOC 2s, OneTrust outputs. |
| 151–500 | < 10% | 5 pages | `pdfplumber` | Tighter chunks: more files, finer citation, lower per-chunk token cost. |
| 501–1000 | < 10% | 3 pages | `pdfplumber` | Manageable chunk count (~330 files max). |
| > 1000 | < 10% | 2 pages | `pdfplumber` + `--stream` | Stream to disk; never buffer in memory. |
| any | 10–50% | 5 pages | hybrid: text + OCR per page | `inventory.py` flags `requires_ocr` per page; re-run `chunk_extract.py --ocr-pages …` for those. |
| any | > 50% | 1 page | OCR every page (`--ocr`) | Treat as fully scanned. DPI 300, tesseract PSM 3. |

## Why chunk sizes go down as page count goes up

It seems counterintuitive (bigger doc → smaller chunks?), but the reasoning is:

- A 1000-page document with 10-page chunks = 100 chunks of ~5K tokens each = ~500K tokens total to read. That exceeds most context windows.
- A 1000-page document with 2-page chunks = 500 chunks of ~1K tokens each = same total, but now each chunk is small enough that you can selectively re-read the relevant ones without dragging the whole document context with you.
- Smaller chunks also produce more precise citations — "page 487 in chunk 244" beats "somewhere in chunk 50 spanning pages 491–500" for audit purposes.

## When to override the defaults

- **Heavy tables / data-heavy report** → smaller chunks (2–3 pages) so each table fits in one chunk's context cleanly.
- **Long narrative report with cross-references** → larger chunks (10–15 pages) so cross-references don't span chunks.
- **Legal / regulatory text where every clause matters** → 1 page per chunk, regardless of size. Pair with a more thorough analysis prompt per chunk.
- **Pentest report with appendices** → split into two passes: main body at 5/chunk, appendices at 10/chunk (they're usually less dense).

## Memory and disk footprint

- Each chunk file is plain UTF-8 text, typically 2–20 KB.
- A 500-page PDF chunked at 5 pages/chunk = 100 chunks ≈ 1–2 MB of chunk files.
- A 1000-page PDF at 2 pages/chunk = 500 chunks ≈ 5–10 MB of chunk files.
- All chunks fit comfortably on disk; the concern is context window, not disk.

## OCR DPI guidance

- **DPI 150** — fast, fine for clean modern PDFs that just need a layout-preserving re-read.
- **DPI 300** — default for OCR. Compliance-grade legibility.
- **DPI 400+** — old scans of legal documents, faxed pages, small-font footnotes. Slower but recovers more text.
