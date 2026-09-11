#!/usr/bin/env python3
"""
relabel_speakers.py — Apply a human-readable speaker map to a transcript JSON.

Usage:
  python scripts/relabel_speakers.py --input transcript.json \
      --map '{"SPEAKER_00":"Patrícia","SPEAKER_01":"José Carlos"}'

  # Or load from a file:
  python scripts/relabel_speakers.py --input transcript.json --map-file speakers.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def apply_map(payload: dict, mapping: dict[str, str]) -> dict:
    for seg in payload.get("segments", []):
        sp = seg.get("speaker")
        if sp in mapping:
            seg["speaker"] = mapping[sp]
        for w in seg.get("words", []):
            if w.get("speaker") in mapping:
                w["speaker"] = mapping[w["speaker"]]
    for turn in payload.get("turns", []):
        if turn.get("speaker") in mapping:
            turn["speaker"] = mapping[turn["speaker"]]
    payload["speakers"] = sorted({t["speaker"] for t in payload.get("turns", []) if t.get("speaker")})
    return payload


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--input", "-i", required=True)
    p.add_argument("--output", "-o", help="Default: overwrite input.")
    p.add_argument("--map", help='JSON dict, e.g. \'{"SPEAKER_00":"Alice"}\'')
    p.add_argument("--map-file", help="Path to a JSON file with the mapping.")
    args = p.parse_args()

    if not args.map and not args.map_file:
        print("Provide --map or --map-file", file=sys.stderr)
        return 2

    mapping = json.loads(args.map) if args.map else json.loads(Path(args.map_file).read_text(encoding="utf-8"))

    src = Path(args.input)
    payload = json.loads(src.read_text(encoding="utf-8"))
    payload = apply_map(payload, mapping)

    out = Path(args.output) if args.output else src
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Updated {out} — speakers now: {payload['speakers']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
