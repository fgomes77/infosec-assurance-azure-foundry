#!/usr/bin/env python3
"""
chunk_extract.py — Stage 3 of pdf-full-coverage-analyzer (v2: multi-layer).

Slice a PDF into chunks of N pages. For each page, capture every
content layer (body / tables / annotations / image-text-OCR) with
explicit markers, so absence is provable. Headers include line, word,
char, and SHA256 anchors.

Per-page output format:

  [page N]
  --- BODY ---
  <body text, from the method that captured most non-whitespace chars>
  --- TABLES ---
  <pdfplumber tables, pipe-delimited>
  --- ANNOTATIONS ---
  <comments, highlights, sticky notes with author + content + highlighted text>
  --- IMAGE_TEXT_OCR ---
  <OCR of page raster — only when --image-text-pages includes this page>

Chunk header format:

  === CHUNK 3 | pages 21-30 | lines 412-587 | words 3120-4205 | chars 21888-29345 | sha256:... ===

Usage:
    python3 chunk_extract.py input.pdf --chunk-size 10 --output-dir ./chunks/

Flags:
    --ocr                       OCR every page (fully scanned)
    --ocr-pages 1,2,3           OCR only specified pages
    --image-text-pages 5,8      Add OCR alongside text for these pages
    --capture-tables on|off     (default on)
    --capture-annots on|off     (default on)
    --stream                    Don't keep chunks in memory
"""
from __future__ import annotations
import argparse
import hashlib
import os
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


# ── Layer extractors ──────────────────────────────────────────────

def get_body_text(pdf_path: str, page: int, use_ocr: bool) -> str:
    if use_ocr:
        return ocr_page(pdf_path, page)
    candidates = []
    try:
        import pdfplumber  # type: ignore
        with pdfplumber.open(pdf_path) as pdf:
            if 1 <= page <= len(pdf.pages):
                t = pdf.pages[page - 1].extract_text() or ""
                if t.strip():
                    candidates.append(("pdfplumber", t))
    except Exception:
        pass
    rc, t2, _ = _run(["pdftotext", "-layout",
                      "-f", str(page), "-l", str(page), pdf_path, "-"])
    if rc == 0 and t2.strip():
        candidates.append(("pdftotext", t2))
    try:
        import fitz  # type: ignore
        doc = fitz.open(pdf_path)
        if 1 <= page <= doc.page_count:
            t3 = doc[page - 1].get_text("text") or ""
            if t3.strip():
                candidates.append(("pymupdf", t3))
        doc.close()
    except Exception:
        pass
    if not candidates:
        return ""
    candidates.sort(key=lambda kv: sum(1 for c in kv[1] if not c.isspace()), reverse=True)
    name, text = candidates[0]
    return f"<source: {name}>\n{text}"


def get_tables_serialized(pdf_path: str, page: int) -> str:
    try:
        import pdfplumber  # type: ignore
        with pdfplumber.open(pdf_path) as pdf:
            if 1 <= page <= len(pdf.pages):
                tables = pdf.pages[page - 1].extract_tables() or []
                if not tables:
                    return ""
                out_parts = []
                for i, tbl in enumerate(tables, 1):
                    out_parts.append(f"<table {i}>")
                    for row in tbl:
                        cells = [(c if c is not None else "").replace("\n", " ").strip()
                                 for c in row]
                        out_parts.append(" | ".join(cells))
                    out_parts.append("</table>")
                return "\n".join(out_parts)
    except Exception:
        pass
    return ""


def get_annotations(pdf_path: str, page: int) -> str:
    try:
        import fitz  # type: ignore
        doc = fitz.open(pdf_path)
        out_parts = []
        if 1 <= page <= doc.page_count:
            p = doc[page - 1]
            for ann in (p.annots() or []):
                info = ann.info or {}
                content = (info.get("content") or "").strip()
                title = (info.get("title") or "").strip()
                subj = (info.get("subject") or "").strip()
                kind = ann.type[1] if ann.type else "annot"
                hl_text = ""
                try:
                    rect = ann.rect
                    hl_text = (p.get_text("text", clip=rect) or "").strip()
                except Exception:
                    pass
                parts = [f'<annot type="{kind}">']
                if title:    parts.append(f"author: {title}")
                if subj:     parts.append(f"subject: {subj}")
                if content:  parts.append(f"content: {content}")
                if hl_text:  parts.append(f"highlighted_text: {hl_text}")
                parts.append("</annot>")
                out_parts.append("\n".join(parts))
        doc.close()
        return "\n".join(out_parts)
    except Exception:
        return ""


def ocr_page(pdf_path: str, page: int, dpi: int = 300) -> str:
    import tempfile
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


# ── Metrics ──────────────────────────────────────────────────────

WORD_RE = re.compile(r"\S+")


def count_lines(text: str) -> int:
    return sum(1 for ln in (text or "").splitlines() if ln.strip())


def count_words(text: str) -> int:
    return len(WORD_RE.findall(text or ""))


def count_chars(text: str) -> int:
    return sum(1 for c in (text or "") if not c.isspace())


def short_sha256(text: str, length: int = 16) -> str:
    return hashlib.sha256((text or "").encode("utf-8", errors="replace")).hexdigest()[:length]


# ── Chunk builder ────────────────────────────────────────────────

def build_chunk(
    pdf_path: str,
    pages: list[int],
    chunk_index: int,
    start_line: int,
    start_word: int,
    start_char: int,
    ocr_pages: set[int],
    ocr_all: bool,
    image_text_pages: set[int],
    capture_tables: bool,
    capture_annots: bool,
) -> tuple[str, int, int, int]:
    parts: list[str] = []
    c_lines = c_words = c_chars = 0
    for page in pages:
        use_ocr = ocr_all or (page in ocr_pages)
        body = get_body_text(pdf_path, page, use_ocr)
        tables = get_tables_serialized(pdf_path, page) if capture_tables else ""
        annots = get_annotations(pdf_path, page) if capture_annots else ""
        image_text = ocr_page(pdf_path, page) if (page in image_text_pages and not use_ocr) else ""

        page_block = [f"[page {page}]"]
        page_block.append("--- BODY ---")
        page_block.append(body if body else "<no body text>")
        if capture_tables:
            page_block.append("--- TABLES ---")
            page_block.append(tables if tables else "<no tables>")
        if capture_annots:
            page_block.append("--- ANNOTATIONS ---")
            page_block.append(annots if annots else "<no annotations>")
        if page in image_text_pages and not use_ocr:
            page_block.append("--- IMAGE_TEXT_OCR ---")
            page_block.append(image_text if image_text else "<no image text recovered>")
        parts.append("\n".join(page_block) + "\n")

        full = (body + "\n" + tables + "\n" + annots + "\n" + image_text)
        c_lines += count_lines(full)
        c_words += count_words(full)
        c_chars += count_chars(full)

    body_text = "".join(parts)
    p1, p2 = pages[0], pages[-1]
    l1 = start_line
    l2 = start_line + c_lines - 1 if c_lines else start_line
    w1 = start_word
    w2 = start_word + c_words - 1 if c_words else start_word
    ch1 = start_char
    ch2 = start_char + c_chars - 1 if c_chars else start_char
    sha = short_sha256(body_text)
    header = (
        f"=== CHUNK {chunk_index} | pages {p1}-{p2} | "
        f"lines {l1}-{l2} | words {w1}-{w2} | chars {ch1}-{ch2} | "
        f"sha256:{sha} ===\n"
    )
    return header + body_text, c_lines, c_words, c_chars


def _parse_int_list(s: str) -> set[int]:
    out: set[int] = set()
    for tok in (s or "").split(","):
        tok = tok.strip()
        if tok.isdigit():
            out.add(int(tok))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Slice PDF into multi-layer chunks.")
    ap.add_argument("pdf_path")
    ap.add_argument("--chunk-size", type=int, default=10)
    ap.add_argument("--output-dir", default="./chunks")
    ap.add_argument("--ocr", action="store_true", help="OCR every page.")
    ap.add_argument("--ocr-pages", default="", help="Comma-separated pages to OCR.")
    ap.add_argument("--capture-tables", default="on", choices=["on", "off"])
    ap.add_argument("--capture-annots", default="on", choices=["on", "off"])
    ap.add_argument("--image-text-pages", default="",
                    help="Pages whose images should also be OCR'd alongside body text.")
    ap.add_argument("--stream", action="store_true")
    args = ap.parse_args()

    p = Path(args.pdf_path)
    if not p.exists():
        print(f"file not found: {args.pdf_path}", file=sys.stderr)
        return 2
    n_pages = page_count(args.pdf_path)
    if n_pages == 0:
        print("could not determine page count", file=sys.stderr)
        return 2
    if args.chunk_size < 1:
        print("chunk-size must be >= 1", file=sys.stderr)
        return 2

    ocr_set = _parse_int_list(args.ocr_pages)
    image_text_set = _parse_int_list(args.image_text_pages)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    chunk_idx = 1
    running_line = running_word = running_char = 1
    cs = args.chunk_size
    pad = max(3, len(str((n_pages // cs) + 1)))
    written = []

    for start in range(1, n_pages + 1, cs):
        end = min(start + cs - 1, n_pages)
        pages = list(range(start, end + 1))
        chunk_text, lines, words, chars = build_chunk(
            args.pdf_path, pages, chunk_idx,
            running_line, running_word, running_char,
            ocr_pages=ocr_set, ocr_all=args.ocr,
            image_text_pages=image_text_set,
            capture_tables=(args.capture_tables == "on"),
            capture_annots=(args.capture_annots == "on"),
        )
        running_line += lines
        running_word += words
        running_char += chars
        out_path = out_dir / f"chunk_{chunk_idx:0{pad}d}.txt"
        out_path.write_text(chunk_text, encoding="utf-8")
        written.append(str(out_path))
        if args.stream:
            del chunk_text
        chunk_idx += 1
        print(f"wrote {out_path}  ({lines} lines, {words} words, {chars} chars, pages {start}-{end})",
              file=sys.stderr)

    print(f"done: {len(written)} chunks, totals lines={running_line - 1} words={running_word - 1} chars={running_char - 1}",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
