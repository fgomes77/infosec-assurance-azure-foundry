#!/usr/bin/env python3
"""
cross_check.py — optional Stage 5b of pdf-full-coverage-analyzer.

The paranoid sanity check. For specified pages (or all), rasterise the
page at 300 DPI, OCR the image, then compare the OCR word set against
the chunk's content for that page. Reports words present in OCR but
missing from chunk extraction.

Catches content text extractors silently miss:
  - Vector-rendered text in charts/infographics
  - Headers/footers / watermarks
  - Text inside embedded images
  - Rotated or skewed text
  - Hyphenation glitches

Usage:
    python3 cross_check.py --pdf input.pdf --chunks ./chunks/ \\
        --pages all                  (or "1,2,5-10")
        --out cross_check.json
"""
from __future__ import annotations
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

PAGE_MARKER = re.compile(r"^\[page (\d+)\]$")

WORD_RE = re.compile(r"[A-Za-zÀ-ÿ0-9][A-Za-zÀ-ÿ0-9\-']{1,}")
# Layer markers and source annotations to ignore in comparison
IGNORE_TOKENS = {
    "body", "tables", "annotations", "image", "text", "ocr", "source",
    "page", "pdfplumber", "pdftotext", "pymupdf", "annot", "type",
    "author", "subject", "content", "highlighted_text", "table",
    "no",
}


def _run(cmd: list[str], timeout: int = 300) -> tuple[int, str, str]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout, r.stderr
    except FileNotFoundError:
        return 127, "", f"binary not found: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"


def page_count(path: str) -> int:
    rc, out, _ = _run(["pdfinfo", path])
    if rc != 0:
        return 0
    for line in out.splitlines():
        if line.startswith("Pages:"):
            try:
                return int(line.split(":", 1)[1].strip())
            except ValueError:
                return 0
    return 0


def ocr_page(pdf_path: str, page: int, dpi: int = 300) -> str:
    with tempfile.TemporaryDirectory() as tmp:
        prefix = os.path.join(tmp, "page")
        rc, _, _ = _run(["pdftoppm", "-png", "-r", str(dpi),
                         "-f", str(page), "-l", str(page), pdf_path, prefix])
        if rc != 0:
            return ""
        candidates = sorted(Path(tmp).glob("page-*.png"))
        if not candidates:
            return ""
        img_path = str(candidates[0])
        try:
            import pytesseract  # type: ignore
            from PIL import Image  # type: ignore
            return pytesseract.image_to_string(Image.open(img_path)) or ""
        except Exception:
            rc2, out2, _ = _run(["tesseract", img_path, "-", "--psm", "3"])
            return out2 if rc2 == 0 else ""


def collect_page_texts(chunks_dir: str) -> dict[int, str]:
    """Return {page_num: full_text_of_that_page} across all chunks."""
    out: dict[int, str] = {}
    for cf in sorted(Path(chunks_dir).glob("chunk_*.txt")):
        text = cf.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        current_page: int | None = None
        buf: list[str] = []
        for ln in lines:
            m = PAGE_MARKER.match(ln)
            if m:
                if current_page is not None and buf:
                    out[current_page] = "\n".join(buf)
                current_page = int(m.group(1))
                buf = []
            else:
                if current_page is not None:
                    buf.append(ln)
        if current_page is not None and buf:
            out[current_page] = "\n".join(buf)
    return out


def tokenize(text: str) -> Counter:
    return Counter(w.lower() for w in WORD_RE.findall(text or "")
                   if w.lower() not in IGNORE_TOKENS)


def parse_pages_arg(s: str, max_page: int) -> list[int]:
    if not s or s.strip().lower() == "all":
        return list(range(1, max_page + 1))
    out: set[int] = set()
    for token in s.split(","):
        token = token.strip()
        if "-" in token:
            a, b = token.split("-", 1)
            if a.isdigit() and b.isdigit():
                out.update(range(int(a), int(b) + 1))
        elif token.isdigit():
            out.add(int(token))
    return sorted(p for p in out if 1 <= p <= max_page)


def cross_check(pdf_path: str, chunks_dir: str, pages: list[int],
                min_word_len: int = 3, top_n_report: int = 50) -> dict:
    chunk_page_texts = collect_page_texts(chunks_dir)
    per_page = []
    total_ocr_words = total_chunk_words = total_missing_words = 0

    for pg in pages:
        ocr_text = ocr_page(pdf_path, pg)
        chunk_text = chunk_page_texts.get(pg, "")
        ocr_tokens = tokenize(ocr_text)
        chunk_tokens = tokenize(chunk_text)
        missing = Counter()
        for w, c in ocr_tokens.items():
            if len(w) < min_word_len:
                continue
            if c > chunk_tokens.get(w, 0):
                missing[w] = c - chunk_tokens.get(w, 0)
        missing_sample = [{"word": w, "ocr_count": c}
                          for w, c in missing.most_common(top_n_report)]
        recall = round(
            100.0 * (1 - sum(missing.values()) / max(1, sum(ocr_tokens.values()))),
            2,
        )
        total_ocr_words += sum(ocr_tokens.values())
        total_chunk_words += sum(chunk_tokens.values())
        total_missing_words += sum(missing.values())
        per_page.append({
            "page": pg,
            "ocr_word_count": sum(ocr_tokens.values()),
            "chunk_word_count": sum(chunk_tokens.values()),
            "missing_word_total": sum(missing.values()),
            "extraction_recall_vs_ocr_pct": recall,
            "missing_words_sample": missing_sample,
        })
        print(f"page {pg}: ocr={sum(ocr_tokens.values())}  chunk={sum(chunk_tokens.values())}  "
              f"missing={sum(missing.values())}  recall={recall}%",
              file=sys.stderr)

    overall_recall = round(
        100.0 * (1 - total_missing_words / max(1, total_ocr_words)),
        2,
    )
    return {
        "pages_checked": pages,
        "total_ocr_words": total_ocr_words,
        "total_chunk_words": total_chunk_words,
        "total_missing_words": total_missing_words,
        "overall_recall_vs_ocr_pct": overall_recall,
        "per_page": per_page,
        "note": (
            "Recall < 100% means OCR saw words the chunk does not contain. "
            "Possible causes: text extraction skipped headers/footers/watermarks/charts/captions, "
            "OCR added noise, or a genuine extraction gap. Inspect missing_words_sample. "
            "Recall >= 98% is normal noise; < 95% suggests a real gap worth investigating."
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Cross-check chunk extraction against page-rasterize+OCR token sets."
    )
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--chunks", required=True)
    ap.add_argument("--pages", default="all",
                    help='Comma/range list, e.g. "1,2,5-10" or "all"')
    ap.add_argument("--min-word-len", type=int, default=3)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    n = page_count(args.pdf)
    if n == 0:
        print("could not determine page count", file=sys.stderr)
        return 2
    target_pages = parse_pages_arg(args.pages, n)
    if not target_pages:
        print("no valid pages to check", file=sys.stderr)
        return 2

    report = cross_check(args.pdf, args.chunks, target_pages,
                         min_word_len=args.min_word_len)
    text = json.dumps(report, indent=2, ensure_ascii=False)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"Wrote cross-check report to {args.out}", file=sys.stderr)
        print(f"overall recall vs OCR: {report['overall_recall_vs_ocr_pct']}%",
              file=sys.stderr)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
