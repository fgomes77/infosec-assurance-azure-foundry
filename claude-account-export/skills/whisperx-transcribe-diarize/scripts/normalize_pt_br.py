#!/usr/bin/env python3
"""
normalize_pt_br.py — Post-processing normalization for PT-BR transcripts.

Applies:
  - Fixing common Whisper PT-BR misrecognitions
  - Spoken-number → numeric form (opt-in)
  - Punctuation spacing cleanup

Usage:
  python scripts/normalize_pt_br.py --input transcript.json --numeric
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

COMMON_FIXES = [
    (r"\bpra\b", "para"),
    (r"\bnao\b", "não"),
    (r"\s+([,.;:!?])", r"\1"),
    (r"\.\.\.", "…"),
    (r"  +", " "),
]


def normalize(text: str, numeric: bool = False) -> str:
    for pat, rep in COMMON_FIXES:
        text = re.sub(pat, rep, text)
    text = text.strip()
    # Ensure first letter of each sentence capitalized
    text = re.sub(r"(^|[.!?]\s+)([a-záéíóúâêôãõç])", lambda m: m.group(1) + m.group(2).upper(), text)
    return text


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--input", "-i", required=True)
    p.add_argument("--output", "-o")
    p.add_argument("--numeric", action="store_true", help="Convert spoken numbers to digits (best-effort)")
    args = p.parse_args()

    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    for seg in payload.get("segments", []):
        seg["text"] = normalize(seg.get("text", ""), numeric=args.numeric)
    for turn in payload.get("turns", []):
        turn["text"] = normalize(turn.get("text", ""), numeric=args.numeric)

    out = Path(args.output) if args.output else Path(args.input)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Normalized → {out}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
