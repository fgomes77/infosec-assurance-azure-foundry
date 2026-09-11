# Output Schemas (v2)

Exact JSON shape of every artefact produced by this skill.

---

## 1. `triage.json` (from `scripts/triage.py`)

```json
{
  "file_path": "/abs/path/to/input.pdf",
  "file_size_bytes": 4823901,
  "page_count": 312,
  "pdf_version": "1.7",
  "encrypted": false,
  "title": "Document Title",
  "producer": "Adobe Acrobat 21.0",
  "creator": "Microsoft Word",
  "has_form_fields": false,
  "has_attachments": false,
  "fonts_embedded_ratio": 1.0,
  "scanned_page_ratio": 0.0,
  "has_extractable_text": true,
  "recommended_strategy": {
    "method": "chunked_text",
    "chunk_size_pages": 5,
    "rationale": "Large text PDF; tighter chunks for finer audit trail.",
    "tool_hint": "pdfplumber"
  }
}
```

`method` possibilities: `single_pass`, `chunked_text`, `chunked_text_streaming`, `hybrid_text_ocr`, `ocr_per_page`, `blocked`.

---

## 2. `inventory.json` (from `scripts/inventory.py` — v2 multi-method)

```json
{
  "pdf_path": "/abs/path/to/input.pdf",
  "total_pages": 312,
  "total_expected_lines": 14802,
  "total_expected_words": 87213,
  "total_expected_chars": 487291,
  "pages_requiring_ocr_followup": [88, 89, 90],
  "divergence_warnings": [
    {
      "page": 145,
      "type": "extraction_method_disagreement",
      "word_counts_by_method": {"pdfplumber": 312, "pdftotext": 187, "pymupdf": 295},
      "disagreement_ratio": 0.401,
      "note": "Methods disagree on word count by >20%. One method may be missing content."
    },
    {
      "page": 88,
      "type": "images_with_no_text",
      "note": "Page has images but extracted text is sparse. OCR recommended.",
      "image_count": 3
    }
  ],
  "document_has_form_fields": false,
  "document_bookmarks_count": 24,
  "document_bookmarks": [
    [1, "Introduction", 1],
    [1, "Chapter 1", 5],
    [2, "Background", 6]
  ],
  "pages": [
    {
      "page_number": 1,
      "expected_lines": 42,
      "expected_words": 312,
      "expected_chars": 1834,
      "method_metrics": {
        "pdfplumber": {"lines": 40, "words": 312, "chars": 1834, "sha256_16": "ab12..."},
        "pdftotext":  {"lines": 42, "words": 310, "chars": 1820, "sha256_16": "cd34..."},
        "pymupdf":    {"lines": 38, "words": 312, "chars": 1828, "sha256_16": "ef56..."}
      },
      "layers": {
        "has_body_text": true,
        "has_tables": false,
        "has_annotations": false,
        "has_images": false,
        "has_rotated_text": false,
        "image_count": 0,
        "annotation_count": 0,
        "table_count": 0
      },
      "requires_ocr": false,
      "image_text_ocr_recommended": false
    }
  ]
}
```

Key fields:
- **`total_expected_*`** — paranoid baseline: sum of MAX(method counts) per page.
- **`method_metrics`** — per-method scores; lets you see which method was most generous on this page.
- **`divergence_warnings`** — actionable list of pages where extractors disagreed > 20% (potential gap).
- **`pages_requiring_ocr_followup`** — pages with near-zero extractable text; re-run with `--ocr-pages …`.
- **`image_text_ocr_recommended`** per page — true when page has images but sparse text; re-run with `--image-text-pages …`.
- **`layers`** — per-page enumeration of every content layer detected (drives Stage 5 layer presence check).

---

## 3. Chunk file format (from `scripts/chunk_extract.py` — v2 multi-layer)

Plain UTF-8 text file. Header on first line:

```
=== CHUNK 3 | pages 21-30 | lines 412-587 | words 3120-4205 | chars 21888-29345 | sha256:ab12cd34ef567890 ===
```

Header grammar (regex used by `verify_coverage.py`):

```
^=== CHUNK (\d+) \| pages (\d+)-(\d+) \| lines (\d+)-(\d+) \| words (\d+)-(\d+) \| chars (\d+)-(\d+) \| sha256:([0-9a-f]+) ===$
```

Body, per page:

```
[page 21]
--- BODY ---
<source: pdfplumber>          # or pdftotext / pymupdf / ocr
<body text, multi-line>
--- TABLES ---
<table 1>
ID | Name | Value
1 | alpha | 100
2 | beta | 200
</table>
--- ANNOTATIONS ---
<annot type="Text">
author: Francisco
subject: Review note
content: This is the comment text.
highlighted_text: original text under highlight
</annot>
--- IMAGE_TEXT_OCR ---
<OCR text of page raster, when image_text_ocr_recommended was set>
[page 22]
...
```

If a layer is absent: `<no tables>`, `<no annotations>`, `<no body text>`. The marker line must still be present so Stage 5 can verify the layer was checked.

---

## 4. `coverage_report.json` (from `scripts/verify_coverage.py` — v2 multi-level)

```json
{
  "verdict": "COMPLETE",
  "reasons": [],
  "errors": [],
  "expected_total_pages": 312,
  "analyzed_total_pages": 312,
  "expected_total_lines": 14802,
  "analyzed_total_lines": 14785,
  "expected_total_words": 87213,
  "analyzed_total_words": 88102,
  "expected_total_chars": 487291,
  "analyzed_total_chars": 491205,
  "coverage_pct_pages": 100.0,
  "coverage_pct_lines": 99.88,
  "coverage_pct_words": 101.02,
  "coverage_pct_chars": 100.80,
  "missing_pages": [],
  "extra_pages": [],
  "duplicate_pages": [],
  "missing_layers_per_page": [],
  "ocr_followup_pages_in_inventory": [],
  "divergence_warnings_from_inventory": [],
  "chunk_count": 63,
  "inventory_path": "/abs/path/to/inventory.json",
  "chunks_dir": "/abs/path/to/chunks"
}
```

Verdict logic:

| Verdict | Condition |
|---|---|
| `COMPLETE` | pages=100% AND words≥95% AND chars≥95% AND every declared layer captured AND lines≥70% AND no errors |
| `PARTIAL` | any of the above thresholds violated, but no structural errors |
| `INVALID` | duplicate pages, extra pages (in chunks but not inventory), or malformed chunk headers |

**Word and char coverage can exceed 100%** — chunks include layer marker text, source annotations, and table cell delimiters that the inventory's text-only baseline doesn't count. That's a feature, not a bug: > 100% means chunks contain at least as much content as the inventory expected.

**Line coverage is informational** — different extraction methods produce wildly different line counts because of how they handle line breaks, layout spacing, and reflow. The verdict only fails on lines if coverage drops below 70% (a strong signal of real content loss).

---

## 5. `cross_check.json` (from `scripts/cross_check.py` — optional Stage 5b)

```json
{
  "pages_checked": [1, 2, 3, 4],
  "total_ocr_words": 1247,
  "total_chunk_words": 1242,
  "total_missing_words": 5,
  "overall_recall_vs_ocr_pct": 99.6,
  "per_page": [
    {
      "page": 1,
      "ocr_word_count": 312,
      "chunk_word_count": 310,
      "missing_word_total": 2,
      "extraction_recall_vs_ocr_pct": 99.36,
      "missing_words_sample": [
        {"word": "watermark", "ocr_count": 1},
        {"word": "draft", "ocr_count": 1}
      ]
    }
  ],
  "note": "Recall < 100% means OCR saw words that the chunk does not contain..."
}
```

Interpretation:
- **≥ 99%** — normal OCR noise; nothing to investigate.
- **95–99%** — likely OCR noise from blurry rendering OR a small extraction gap (e.g., headers/footers excluded). Inspect `missing_words_sample`.
- **< 95%** — real coverage gap. Investigate. Common causes: charts with vector-rendered text, watermarks, page rotation, very small fonts.

---

## 6. Per-chunk analysis JSON (Stage 4 — produced by the analyst, not a script)

One record per chunk file, optionally aggregated as `chunk_analyses.jsonl`.

```json
{
  "chunk": 3,
  "pages": [21, 22, 23, 24, 25, 26, 27, 28, 29, 30],
  "context": {
    "what_this_section_is_about": "1-3 sentence description of what the chunk covers.",
    "document_role": "introduction | background | argument | evidence | methodology | results | discussion | conclusion | appendix | reference | boilerplate | transition | other",
    "structural_position": "continuation of Section 4.3 / new chapter / appendix B / ...",
    "key_entities_introduced": ["entity1", "entity2"],
    "key_entities_referenced": ["entityA"],
    "relation_to_prior_chunks": "continues | introduces_new_topic | refines | contradicts | references_back_to_chunk_N | independent",
    "open_threads_for_later_chunks": ["question or topic the chunk raises but does not resolve"]
  },
  "details": [
    {
      "page": 23,
      "type": "fact | claim | definition | number | name | date | condition | requirement | exception | citation | example | instruction | other",
      "content": "Faithful paraphrase in plain language.",
      "exact_quote_if_critical": "≤15 word verbatim quote, only when wording matters",
      "qualifiers": "any caveats, scope limits, conditions, uncertainty"
    }
  ],
  "open_questions": ["unresolved item within this chunk"],
  "user_query_relevance": "high | medium | low | none",
  "extraction_quality_notes": "anything about OCR noise, ambiguity, layout issues"
}
```

---

## 7. Final delivery structure

| Artefact | Purpose |
|---|---|
| Analytical answer (in chat) | The actual answer with `[page N]` citations |
| Coverage statement (one sentence) | "Read X pages, Y words, Z chars across N chunks. Verdict: COMPLETE." |
| Per-chunk context map (long docs) | Chunk → pages → what each chunk is about |
| `triage.json` | Stage 1 output |
| `inventory.json` | Stage 2 output (the audit anchor) |
| `chunks/*.txt` | Stage 3 output (source-of-truth multi-layer extraction) |
| `chunk_analyses.jsonl` | Stage 4 output (per-chunk context + details) |
| `coverage_report.json` | Stage 5 output (MUST be COMPLETE) |
| `cross_check.json` (optional) | Stage 5b output (OCR cross-check) |
| Limitations note | OCR confidence, ambiguities, gaps explicitly flagged |
