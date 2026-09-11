#!/usr/bin/env python3
"""
extract_speaker_clips.py — Split source audio into one file per speaker (concatenated turns).

Usage:
  python scripts/extract_speaker_clips.py \
      --input transcript.json \
      --audio original.m4a \
      --output-dir ./speaker_clips
"""
from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path


def fmt_ts(seconds: float) -> str:
    return f"{seconds:.3f}"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--input", "-i", required=True, help="Transcript JSON from transcribe_diarize.py")
    p.add_argument("--audio", "-a", required=True, help="Original audio file")
    p.add_argument("--output-dir", "-o", default="./speaker_clips")
    p.add_argument("--format", default="m4a", choices=["m4a", "mp3", "wav"])
    args = p.parse_args()

    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    audio = Path(args.audio).expanduser().resolve()
    if not audio.exists():
        print(f"Audio not found: {audio}", file=sys.stderr)
        return 2

    out_dir = Path(args.output_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    by_speaker: dict[str, list[tuple[float, float]]] = {}
    for turn in payload.get("turns", []):
        sp = turn.get("speaker", "UNKNOWN")
        by_speaker.setdefault(sp, []).append((turn["start"], turn["end"]))

    codec = {"m4a": "aac", "mp3": "libmp3lame", "wav": "pcm_s16le"}[args.format]

    for speaker, ranges in by_speaker.items():
        # Build ffmpeg filter_complex: concat of aselect segments
        # Safer approach: extract each range to tmp, then concat. For simplicity
        # we use the aselect+atrim filter which handles this in one pass.
        filters = []
        for i, (s, e) in enumerate(ranges):
            filters.append(f"[0:a]atrim={fmt_ts(s)}:{fmt_ts(e)},asetpts=PTS-STARTPTS[a{i}]")
        concat_inputs = "".join(f"[a{i}]" for i in range(len(ranges)))
        filters.append(f"{concat_inputs}concat=n={len(ranges)}:v=0:a=1[out]")
        filter_graph = ";".join(filters)

        safe_speaker = "".join(c if c.isalnum() or c in "-_" else "_" for c in speaker)
        out_path = out_dir / f"{audio.stem}__{safe_speaker}.{args.format}"

        cmd = [
            "ffmpeg", "-y", "-i", str(audio),
            "-filter_complex", filter_graph,
            "-map", "[out]",
            "-c:a", codec,
            str(out_path),
        ]
        print(f"  → {out_path.name} ({len(ranges)} segments)")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"    ffmpeg failed: {result.stderr[-500:]}", file=sys.stderr)

    print(f"Done. Clips in {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
