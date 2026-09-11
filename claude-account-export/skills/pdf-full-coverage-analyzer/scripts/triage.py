#!/usr/bin/env python3
"""
triage.py — Stage 1 of pdf-full-coverage-analyzer.

Run a fast diagnostic on a PDF and emit a JSON blob describing what
kind of document it is and how to chunk it for full-coverage analysis.

Usage:
    python3 triage.py input.pdf [--out triage.json]

Output JSON fields:
    file_path, file_size_bytes, page_count, pdf_version, encrypted,
    has_form_fields, has_attachments, has_extractable_text,
    scanned_page_ratio, fonts_embedded_ratio, recommended_strategy
"""
from __future__ import annotations
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def _run(cmd: list[str]) -> tuple[int, str, str]:
    """Run a shell command and capture output without raising."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        return r.returncode, r.stdout, r.stderr
    except FileNotFoundError:
        return 127, "", f"binary not found: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return 124, "", f"timeout: {' '.join(cmd)}"


def get_pdfinfo(path: str) -> dict:
    """Parse pdfinfo output into a dict."""
    rc, out, err = _run(["pdfinfo", path])
    info: dict = {"_raw_pdfinfo_rc": rc}
    if rc != 0:
        info["_pdfinfo_error"] = err.strip()
        return info
    for line in out.splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            info[k.strip()] = v.strip()
    return info


def quick_text_sample(path: str, page: int) -> str:
    """Extract one page of text quickly via pdftotext."""
    rc, out, _ = _run(
        ["pdftotext", "-f", str(page), "-l", str(page), path, "-"]
    )
    return out if rc == 0 else ""


def fonts_embedded_ratio(path: str) -> float | None:
    """Ratio of fonts that are embedded. None if no fonts or pdffonts unavailable."""
    rc, out, _ = _run(["pdffonts", path])
    if rc != 0 or not out.strip():
        return None
    lines = out.splitlines()
    # pdffonts has a 2-line header
    data = lines[2:] if len(lines) > 2 else []
    if not data:
        return None
    total = 0
    embedded = 0
    for line in data:
        parts = line.split()
        if len(parts) < 5:
            continue
        # 'emb' column varies in position by version; look for yes/no token
        total += 1
        if "yes" in [p.lower() for p in parts[:8]]:
            embedded += 1
    return round(embedded / total, 3) if total else None


def detect_scanned_ratio(path: str, page_count: int, sample_n: int = 5) -> float:
    """
    Sample N pages spread across the document and check how many produce
    no extractable text. Returns ratio in [0,1].
    """
    if page_count == 0:
        return 0.0
    sample_n = min(sample_n, page_count)
    if sample_n == 1:
        sample_pages = [1]
    else:
        step = max(1, page_count // sample_n)
        sample_pages = list(range(1, page_count + 1, step))[:sample_n]
    empty = 0
    for p in sample_pages:
        text = quick_text_sample(path, p).strip()
        if len(text) < 20:  # threshold — page is effectively blank to extractor
            empty += 1
    return round(empty / len(sample_pages), 3)


def has_form_fields(path: str) -> bool:
    try:
        from pypdf import PdfReader  # type: ignore
        r = PdfReader(path)
        fields = r.get_fields() or {}
        return len(fields) > 0
    except Exception:
        return False


def has_attachments(path: str) -> bool:
    rc, out, _ = _run(["pdfdetach", "-list", path])
    if rc != 0:
        return False
    # pdfdetach prints "0 embedded files" when there are none
    for line in out.splitlines():
        if "embedded files" in line.lower():
            try:
                n = int(line.strip().split()[0])
                return n > 0
            except (ValueError, IndexError):
                pass
    return False


def recommend_strategy(page_count: int, scanned_ratio: float) -> dict:
    """Pick chunking strategy. See SKILL.md decision matrix."""
    if scanned_ratio >= 0.5:
        return {
            "method": "ocr_per_page",
            "chunk_size_pages": 1,
            "rationale": "Majority of sampled pages have no extractable text; OCR required.",
            "tool_hint": "pytesseract via pdftoppm -r 300",
        }
    if scanned_ratio >= 0.1:
        return {
            "method": "hybrid_text_ocr",
            "chunk_size_pages": 5,
            "rationale": "Mixed document: some pages have text, some are scanned.",
            "tool_hint": "pdfplumber for text pages, pytesseract for scanned pages",
        }
    if page_count <= 20:
        return {
            "method": "single_pass",
            "chunk_size_pages": page_count,
            "rationale": "Small text PDF; one chunk suffices.",
            "tool_hint": "pdftotext -layout",
        }
    if page_count <= 150:
        return {
            "method": "chunked_text",
            "chunk_size_pages": 10,
            "rationale": "Medium text PDF; 10-page chunks balance context and granularity.",
            "tool_hint": "pdfplumber",
        }
    if page_count <= 500:
        return {
            "method": "chunked_text",
            "chunk_size_pages": 5,
            "rationale": "Large text PDF; tighter chunks for finer audit trail.",
            "tool_hint": "pdfplumber",
        }
    if page_count <= 1000:
        return {
            "method": "chunked_text",
            "chunk_size_pages": 3,
            "rationale": "Very large text PDF.",
            "tool_hint": "pdfplumber",
        }
    return {
        "method": "chunked_text_streaming",
        "chunk_size_pages": 2,
        "rationale": "Massive PDF (>1000 pages); stream chunks to disk.",
        "tool_hint": "pdfplumber + --stream flag in chunk_extract.py",
    }


def triage(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        return {"error": f"file not found: {path}"}
    info = get_pdfinfo(path)
    try:
        page_count = int(info.get("Pages", "0"))
    except ValueError:
        page_count = 0
    encrypted = info.get("Encrypted", "no").lower().startswith("yes")
    result: dict = {
        "file_path": str(p.resolve()),
        "file_size_bytes": p.stat().st_size,
        "page_count": page_count,
        "pdf_version": info.get("PDF version"),
        "encrypted": encrypted,
        "title": info.get("Title"),
        "producer": info.get("Producer"),
        "creator": info.get("Creator"),
    }
    if encrypted:
        result["recommended_strategy"] = {
            "method": "blocked",
            "rationale": "PDF is encrypted — ask user for password or unlocked copy.",
        }
        return result
    if page_count == 0:
        result["recommended_strategy"] = {
            "method": "blocked",
            "rationale": "pdfinfo could not determine page count; PDF may be corrupted.",
        }
        return result

    result["has_form_fields"] = has_form_fields(path)
    result["has_attachments"] = has_attachments(path)
    result["fonts_embedded_ratio"] = fonts_embedded_ratio(path)
    scanned_ratio = detect_scanned_ratio(path, page_count)
    result["scanned_page_ratio"] = scanned_ratio
    result["has_extractable_text"] = scanned_ratio < 0.9
    result["recommended_strategy"] = recommend_strategy(page_count, scanned_ratio)
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description="Triage a PDF for full-coverage analysis.")
    ap.add_argument("pdf_path")
    ap.add_argument("--out", default=None, help="Write JSON to this file (default: stdout).")
    args = ap.parse_args()
    report = triage(args.pdf_path)
    out_text = json.dumps(report, indent=2, ensure_ascii=False)
    if args.out:
        Path(args.out).write_text(out_text, encoding="utf-8")
        print(f"Wrote triage report to {args.out}", file=sys.stderr)
    else:
        print(out_text)
    return 0 if "error" not in report else 2


if __name__ == "__main__":
    sys.exit(main())
