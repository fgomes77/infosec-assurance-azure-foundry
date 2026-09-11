#!/usr/bin/env python3
"""
inventory.py — Stage 2 of pdf-full-coverage-analyzer (v2: multi-method).

Builds a per-page inventory using THREE text extractors in parallel
(pdfplumber, pdftotext, PyMuPDF). The per-page expected baseline is the
MAXIMUM lines/words/chars seen by any method — anything one extractor
misses, another catches. Also enumerates every PDF content layer
(body, tables, annotations, images, form fields, bookmarks) so chunk
coverage can be verified layer-by-layer.

Usage:
    python3 inventory.py input.pdf [--out inventory.json] [--ocr-pages 1,2,3]
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


def _run(cmd: list[str], timeout: int = 600) -> tuple[int, str, str]:
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


# ── Three text extraction methods ─────────────────────────────────────

def extract_pdfplumber(path: str, page: int) -> str:
    try:
        import pdfplumber  # type: ignore
        with pdfplumber.open(path) as pdf:
            if 1 <= page <= len(pdf.pages):
                return pdf.pages[page - 1].extract_text() or ""
    except Exception:
        pass
    return ""


def extract_pdftotext(path: str, page: int) -> str:
    rc, out, _ = _run([
        "pdftotext", "-layout",
        "-f", str(page), "-l", str(page), path, "-",
    ])
    return out if rc == 0 else ""


def extract_pymupdf(path: str, page: int) -> str:
    try:
        import fitz  # type: ignore
        doc = fitz.open(path)
        if 1 <= page <= doc.page_count:
            txt = doc[page - 1].get_text("text") or ""
            doc.close()
            return txt
        doc.close()
    except Exception:
        pass
    return ""


def extract_via_ocr(path: str, page: int, dpi: int = 300) -> str:
    import tempfile
    import os
    with tempfile.TemporaryDirectory() as tmp:
        prefix = os.path.join(tmp, "page")
        rc, _, _ = _run([
            "pdftoppm", "-png", "-r", str(dpi),
            "-f", str(page), "-l", str(page), path, prefix,
        ])
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


# ── Layer detection ─────────────────────────────────────────────────

def detect_layers(path: str, page: int) -> dict:
    layers = {
        "has_body_text": False,
        "has_tables": False,
        "has_annotations": False,
        "has_images": False,
        "has_rotated_text": False,
        "image_count": 0,
        "annotation_count": 0,
        "table_count": 0,
    }
    try:
        import pdfplumber  # type: ignore
        with pdfplumber.open(path) as pdf:
            if 1 <= page <= len(pdf.pages):
                p = pdf.pages[page - 1]
                if (p.extract_text() or "").strip():
                    layers["has_body_text"] = True
                tables = p.find_tables() or []
                layers["table_count"] = len(tables)
                layers["has_tables"] = bool(tables)
    except Exception:
        pass
    try:
        import fitz  # type: ignore
        doc = fitz.open(path)
        if 1 <= page <= doc.page_count:
            p = doc[page - 1]
            imgs = p.get_images(full=True) or []
            layers["image_count"] = len(imgs)
            layers["has_images"] = bool(imgs)
            annots = list(p.annots() or [])
            layers["annotation_count"] = len(annots)
            layers["has_annotations"] = bool(annots)
            try:
                raw = p.get_text("rawdict")
                for block in raw.get("blocks", []):
                    for line in block.get("lines", []):
                        d = line.get("dir", (1.0, 0.0))
                        if abs(d[1]) > 0.1:
                            layers["has_rotated_text"] = True
                            break
                    if layers["has_rotated_text"]:
                        break
            except Exception:
                pass
        doc.close()
    except Exception:
        pass
    return layers


def doc_level_form_fields(path: str) -> bool:
    try:
        from pypdf import PdfReader  # type: ignore
        return bool(PdfReader(path).get_fields() or {})
    except Exception:
        return False


def doc_level_bookmarks(path: str) -> list:
    try:
        import fitz  # type: ignore
        doc = fitz.open(path)
        toc = doc.get_toc() or []
        doc.close()
        return toc
    except Exception:
        return []


# ── Metrics ─────────────────────────────────────────────────────────

WORD_RE = re.compile(r"\S+")


def count_words(text: str) -> int:
    return len(WORD_RE.findall(text or ""))


def count_non_empty_lines(text: str) -> int:
    return sum(1 for ln in (text or "").splitlines() if ln.strip())


def count_chars(text: str) -> int:
    return sum(1 for c in (text or "") if not c.isspace())


def short_sha256(text: str, length: int = 16) -> str:
    return hashlib.sha256((text or "").encode("utf-8", errors="replace")).hexdigest()[:length]


# ── Build inventory ────────────────────────────────────────────────

def build_inventory(
    pdf_path: str,
    ocr_pages: set[int] | None = None,
    auto_ocr_threshold_words: int = 3,
) -> dict:
    p = Path(pdf_path)
    if not p.exists():
        return {"error": f"file not found: {pdf_path}"}
    n_pages = page_count(pdf_path)
    if n_pages == 0:
        return {"error": "could not determine page count"}

    ocr_pages = ocr_pages or set()
    pages_out: list[dict] = []
    tot_lines = tot_words = tot_chars = 0
    auto_ocr_flagged: list[int] = []
    divergence_warnings: list[dict] = []

    has_forms = doc_level_form_fields(pdf_path)
    toc = doc_level_bookmarks(pdf_path)

    for page in range(1, n_pages + 1):
        method_texts = {
            "pdfplumber": extract_pdfplumber(pdf_path, page),
            "pdftotext":  extract_pdftotext(pdf_path, page),
            "pymupdf":    extract_pymupdf(pdf_path, page),
        }
        if page in ocr_pages:
            method_texts["ocr"] = extract_via_ocr(pdf_path, page)

        method_metrics = {}
        for name, txt in method_texts.items():
            method_metrics[name] = {
                "lines": count_non_empty_lines(txt),
                "words": count_words(txt),
                "chars": count_chars(txt),
                "sha256_16": short_sha256(txt),
            }

        max_lines = max(m["lines"] for m in method_metrics.values())
        max_words = max(m["words"] for m in method_metrics.values())
        max_chars = max(m["chars"] for m in method_metrics.values())

        word_counts = [m["words"] for m in method_metrics.values() if m["words"] > 0]
        if len(word_counts) >= 2:
            disagree = (max(word_counts) - min(word_counts)) / max(1, max(word_counts))
            if disagree > 0.20:
                divergence_warnings.append({
                    "page": page,
                    "type": "extraction_method_disagreement",
                    "word_counts_by_method": {n: m["words"] for n, m in method_metrics.items()},
                    "disagreement_ratio": round(disagree, 3),
                    "note": "Methods disagree on word count by >20%. One method may be missing content.",
                })

        requires_ocr = max_words < auto_ocr_threshold_words
        if requires_ocr and page not in ocr_pages:
            auto_ocr_flagged.append(page)

        layers = detect_layers(pdf_path, page)
        image_text_recommended = (
            layers["has_images"] and max_chars < 50 and not requires_ocr
        )
        if image_text_recommended:
            divergence_warnings.append({
                "page": page,
                "type": "images_with_no_text",
                "note": "Page has images but extracted text is sparse — OCR recommended.",
                "image_count": layers["image_count"],
            })

        tot_lines += max_lines
        tot_words += max_words
        tot_chars += max_chars

        pages_out.append({
            "page_number": page,
            "expected_lines": max_lines,
            "expected_words": max_words,
            "expected_chars": max_chars,
            "method_metrics": method_metrics,
            "layers": layers,
            "requires_ocr": requires_ocr,
            "image_text_ocr_recommended": image_text_recommended,
        })

    return {
        "pdf_path": str(p.resolve()),
        "total_pages": n_pages,
        "total_expected_lines": tot_lines,
        "total_expected_words": tot_words,
        "total_expected_chars": tot_chars,
        "pages_requiring_ocr_followup": auto_ocr_flagged,
        "divergence_warnings": divergence_warnings,
        "document_has_form_fields": has_forms,
        "document_bookmarks_count": len(toc),
        "document_bookmarks": toc[:200],
        "pages": pages_out,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Multi-method per-page inventory of a PDF.")
    ap.add_argument("pdf_path")
    ap.add_argument("--out", default=None)
    ap.add_argument("--ocr-pages", default="",
                    help="Comma-separated page numbers to also OCR.")
    args = ap.parse_args()
    ocr_set: set[int] = set()
    if args.ocr_pages.strip():
        for tok in args.ocr_pages.split(","):
            tok = tok.strip()
            if tok.isdigit():
                ocr_set.add(int(tok))
    inv = build_inventory(args.pdf_path, ocr_pages=ocr_set)
    text = json.dumps(inv, indent=2, ensure_ascii=False, default=str)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"Wrote inventory to {args.out}", file=sys.stderr)
        if inv.get("pages_requiring_ocr_followup"):
            pages = ",".join(map(str, inv["pages_requiring_ocr_followup"]))
            print(f"NOTE: pages may need OCR — re-run with --ocr-pages {pages}",
                  file=sys.stderr)
        if inv.get("divergence_warnings"):
            print(f"NOTE: {len(inv['divergence_warnings'])} divergence warning(s).",
                  file=sys.stderr)
    else:
        print(text)
    return 0 if "error" not in inv else 2


if __name__ == "__main__":
    sys.exit(main())
