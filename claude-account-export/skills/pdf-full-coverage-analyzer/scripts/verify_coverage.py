#!/usr/bin/env python3
"""
verify_coverage.py — Stage 5 of pdf-full-coverage-analyzer (v2).

Audit gate. Reads inventory.json (v2 schema with words/chars/layers) and
the chunk files, parses each chunk's header AND per-page layer markers,
then verifies coverage at FOUR levels:

  1. Pages       — every inventoried page appears in some chunk
  2. Words       — chunk word count >= 95% of inventory baseline
  3. Chars       — chunk char count >= 95% of inventory baseline
  4. Layers      — every page that the inventory says has tables /
                   annotations / images-with-text must have the
                   corresponding section in the chunk file
Plus lines, reported informationally (lines vary across extractors;
flag only if < 70%).

Emits a JSON report with verdict COMPLETE / PARTIAL / INVALID.

Usage:
    python3 verify_coverage.py --inventory inventory.json --chunks ./chunks/ \\
        [--out coverage_report.json]
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path

HEADER_RE = re.compile(
    r"^=== CHUNK (\d+) \| pages (\d+)-(\d+) \| "
    r"lines (\d+)-(\d+) \| words (\d+)-(\d+) \| chars (\d+)-(\d+) \| "
    r"sha256:([0-9a-f]+) ===$"
)
PAGE_MARKER_RE = re.compile(r"^\[page (\d+)\]$")
LAYER_MARKER_RE = re.compile(r"^--- ([A-Z_]+) ---$")

# Thresholds. Pages must be 100%. Words and chars are robust across
# methods (95%). Lines vary too much across extractors — informational,
# flagged only if < 70%.
WORD_THRESHOLD = 0.95
CHAR_THRESHOLD = 0.95
LINE_INFO_THRESHOLD = 0.70


def parse_chunk(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    if not lines:
        return {"path": str(path), "error": "empty file"}
    m = HEADER_RE.match(lines[0])
    if not m:
        return {"path": str(path), "error": "missing or malformed header"}
    (idx, p1, p2, l1, l2, w1, w2, ch1, ch2, sha) = m.groups()
    pages_in_body: list[int] = []
    page_layers: dict[int, set[str]] = {}
    non_empty = 0
    current_page: int | None = None
    for ln in lines[1:]:
        pm = PAGE_MARKER_RE.match(ln)
        if pm:
            current_page = int(pm.group(1))
            pages_in_body.append(current_page)
            page_layers[current_page] = set()
            continue
        lm = LAYER_MARKER_RE.match(ln)
        if lm and current_page is not None:
            page_layers[current_page].add(lm.group(1))
            continue
        if ln.strip():
            non_empty += 1
    return {
        "path": str(path),
        "chunk_index": int(idx),
        "header_pages": (int(p1), int(p2)),
        "header_lines": (int(l1), int(l2)),
        "header_words": (int(w1), int(w2)),
        "header_chars": (int(ch1), int(ch2)),
        "header_sha256_16": sha,
        "pages_in_body": pages_in_body,
        "page_layers": {k: sorted(v) for k, v in page_layers.items()},
        "non_empty_lines_in_body": non_empty,
        "header_lines_count": int(l2) - int(l1) + 1 if int(l1) <= int(l2) else 0,
        "header_words_count": int(w2) - int(w1) + 1 if int(w1) <= int(w2) else 0,
        "header_chars_count": int(ch2) - int(ch1) + 1 if int(ch1) <= int(ch2) else 0,
    }


def verify(inventory_path: str, chunks_dir: str) -> dict:
    inv = json.loads(Path(inventory_path).read_text(encoding="utf-8"))
    if "error" in inv:
        return {"verdict": "INVALID", "reason": f"inventory error: {inv['error']}"}

    expected_pages: set[int] = {p["page_number"] for p in inv["pages"]}
    exp_total_pages = inv["total_pages"]
    exp_total_lines = inv["total_expected_lines"]
    exp_total_words = inv["total_expected_words"]
    exp_total_chars = inv["total_expected_chars"]

    # Layers the inventory says exist per page
    expected_layers_per_page: dict[int, list[str]] = {}
    for p in inv["pages"]:
        pn = p["page_number"]
        layers = p.get("layers", {})
        expected = []
        if layers.get("has_body_text") or p.get("expected_words", 0) > 0:
            expected.append("BODY")
        if layers.get("has_tables"):
            expected.append("TABLES")
        if layers.get("has_annotations"):
            expected.append("ANNOTATIONS")
        if p.get("image_text_ocr_recommended"):
            expected.append("IMAGE_TEXT_OCR")
        expected_layers_per_page[pn] = expected

    chunk_files = sorted(Path(chunks_dir).glob("chunk_*.txt"))
    if not chunk_files:
        return {"verdict": "INVALID", "reason": f"no chunk files in {chunks_dir}"}

    parsed: list[dict] = []
    errors: list[str] = []
    pages_covered: list[int] = []
    duplicates: list[int] = []
    analyzed_lines = analyzed_words = analyzed_chars = 0
    layer_gaps: list[dict] = []

    for cf in chunk_files:
        info = parse_chunk(cf)
        if "error" in info:
            errors.append(f"{cf.name}: {info['error']}")
            continue
        parsed.append(info)
        analyzed_lines += info["header_lines_count"]
        analyzed_words += info["header_words_count"]
        analyzed_chars += info["header_chars_count"]
        for pg in info["pages_in_body"]:
            if pg in pages_covered:
                duplicates.append(pg)
            pages_covered.append(pg)
        hdr_p1, hdr_p2 = info["header_pages"]
        if set(info["pages_in_body"]) != set(range(hdr_p1, hdr_p2 + 1)):
            errors.append(
                f"{cf.name}: header pages {hdr_p1}-{hdr_p2} != body pages {info['pages_in_body']}"
            )
        for pg in info["pages_in_body"]:
            expected = set(expected_layers_per_page.get(pg, []))
            actual = set(info["page_layers"].get(pg, []))
            missing_layers = expected - actual
            if missing_layers:
                layer_gaps.append({
                    "page": pg,
                    "missing_layers": sorted(missing_layers),
                    "chunk_file": cf.name,
                })

    covered_set = set(pages_covered)
    missing_pages = sorted(expected_pages - covered_set)
    extra_pages = sorted(covered_set - expected_pages)

    def pct(num: int, den: int) -> float:
        return round(100.0 * num / max(1, den), 2)

    cov_lines = pct(analyzed_lines, exp_total_lines)
    cov_words = pct(analyzed_words, exp_total_words)
    cov_chars = pct(analyzed_chars, exp_total_chars)
    cov_pages = pct(len(covered_set & expected_pages), exp_total_pages)

    verdict = "COMPLETE"
    reasons: list[str] = []

    if missing_pages:
        verdict = "PARTIAL"
        reasons.append(f"{len(missing_pages)} page(s) not in any chunk")
    if extra_pages:
        verdict = "INVALID"
        reasons.append(f"{len(extra_pages)} page(s) in chunks but not in inventory")
    if duplicates:
        verdict = "INVALID"
        reasons.append(f"{len(set(duplicates))} page(s) appear in multiple chunks")
    if errors:
        verdict = "INVALID"
    if cov_words < 100 * WORD_THRESHOLD and verdict == "COMPLETE":
        verdict = "PARTIAL"
        reasons.append(f"word coverage {cov_words}% < {WORD_THRESHOLD*100}%")
    if cov_chars < 100 * CHAR_THRESHOLD and verdict == "COMPLETE":
        verdict = "PARTIAL"
        reasons.append(f"char coverage {cov_chars}% < {CHAR_THRESHOLD*100}%")
    if cov_lines < 100 * LINE_INFO_THRESHOLD and verdict == "COMPLETE":
        verdict = "PARTIAL"
        reasons.append(
            f"line coverage {cov_lines}% < {LINE_INFO_THRESHOLD*100}% "
            f"(unusually low — investigate)"
        )
    if layer_gaps and verdict == "COMPLETE":
        verdict = "PARTIAL"
        reasons.append(f"{len(layer_gaps)} page(s) missing declared content layers")

    ocr_followup = inv.get("pages_requiring_ocr_followup", [])
    inv_divergences = inv.get("divergence_warnings", [])

    return {
        "verdict": verdict,
        "reasons": reasons,
        "errors": errors,
        "expected_total_pages": exp_total_pages,
        "analyzed_total_pages": len(covered_set & expected_pages),
        "expected_total_lines": exp_total_lines,
        "analyzed_total_lines": analyzed_lines,
        "expected_total_words": exp_total_words,
        "analyzed_total_words": analyzed_words,
        "expected_total_chars": exp_total_chars,
        "analyzed_total_chars": analyzed_chars,
        "coverage_pct_pages": cov_pages,
        "coverage_pct_lines": cov_lines,
        "coverage_pct_words": cov_words,
        "coverage_pct_chars": cov_chars,
        "missing_pages": missing_pages,
        "extra_pages": extra_pages,
        "duplicate_pages": sorted(set(duplicates)),
        "missing_layers_per_page": layer_gaps,
        "ocr_followup_pages_in_inventory": ocr_followup,
        "divergence_warnings_from_inventory": inv_divergences,
        "chunk_count": len(parsed),
        "inventory_path": str(Path(inventory_path).resolve()),
        "chunks_dir": str(Path(chunks_dir).resolve()),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Verify multi-level chunk coverage against inventory.")
    ap.add_argument("--inventory", required=True)
    ap.add_argument("--chunks", required=True)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    report = verify(args.inventory, args.chunks)
    text = json.dumps(report, indent=2, ensure_ascii=False)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"Wrote coverage report to {args.out}", file=sys.stderr)
        print(
            f"verdict={report['verdict']}  "
            f"pages={report['analyzed_total_pages']}/{report['expected_total_pages']}  "
            f"lines={report['analyzed_total_lines']}/{report['expected_total_lines']} ({report['coverage_pct_lines']}%)  "
            f"words={report['analyzed_total_words']}/{report['expected_total_words']} ({report['coverage_pct_words']}%)  "
            f"chars={report['analyzed_total_chars']}/{report['expected_total_chars']} ({report['coverage_pct_chars']}%)",
            file=sys.stderr,
        )
    else:
        print(text)
    return 0 if report["verdict"] == "COMPLETE" else 1


if __name__ == "__main__":
    sys.exit(main())
