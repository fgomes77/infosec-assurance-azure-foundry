#!/usr/bin/env bash
# chunked_pipeline.sh — Memory-safe pipeline for files > 3 hours on 16GB M1.
#
# Strategy:
#   1. Detect silences in the source audio (ffmpeg silencedetect)
#   2. Split at the nearest silence boundary to ~30min chunks
#   3. Transcribe each chunk separately (no diarization yet)
#   4. Run a single global diarization pass on the full audio
#   5. Align global speaker IDs with chunk transcripts
#
# Usage:
#   bash scripts/chunked_pipeline.sh /path/to/long_audio.m4a
#
# Output: ./transcripts/<stem>_merged.json

set -euo pipefail

INPUT="${1:?Usage: chunked_pipeline.sh <audio-file>}"
CHUNK_MINUTES="${CHUNK_MINUTES:-30}"
OUT_DIR="${OUT_DIR:-./transcripts}"
WORK_DIR="${WORK_DIR:-./.chunked_work}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
VENV="$SKILL_DIR/.venv/bin/activate"

# shellcheck disable=SC1090
[[ -f "$VENV" ]] && source "$VENV"

mkdir -p "$OUT_DIR" "$WORK_DIR"

STEM="$(basename "$INPUT" | sed 's/\.[^.]*$//')"

echo "[chunked] Detecting silences..."
ffmpeg -i "$INPUT" -af "silencedetect=noise=-35dB:d=0.8" -f null - 2> "$WORK_DIR/silences.log"

echo "[chunked] Splitting into ~${CHUNK_MINUTES}-minute chunks at silence boundaries..."
python - <<PY > "$WORK_DIR/split_points.txt"
import re, sys
log = open("$WORK_DIR/silences.log").read()
silence_ends = [float(m.group(1)) for m in re.finditer(r"silence_end:\s+(\d+\.?\d*)", log)]
target = ${CHUNK_MINUTES} * 60
points = []
last = 0
for t in silence_ends:
    if t - last >= target:
        points.append(t)
        last = t
print("\n".join(f"{p:.3f}" for p in points))
PY

# Build ffmpeg segment command
SPLIT_POINTS=$(tr '\n' ',' < "$WORK_DIR/split_points.txt" | sed 's/,$//')
if [[ -z "$SPLIT_POINTS" ]]; then
    echo "[chunked] Audio short enough — falling back to single-pass."
    python "$SCRIPT_DIR/transcribe_diarize.py" --input "$INPUT" --output-dir "$OUT_DIR"
    exit 0
fi

echo "[chunked] Split points: $SPLIT_POINTS"
ffmpeg -y -i "$INPUT" -f segment -segment_times "$SPLIT_POINTS" -c copy \
    "$WORK_DIR/${STEM}_chunk_%03d.${INPUT##*.}"

echo "[chunked] Transcribing chunks (no diarization yet)..."
for chunk in "$WORK_DIR/${STEM}_chunk_"*.*; do
    echo "  → $(basename "$chunk")"
    python "$SCRIPT_DIR/transcribe_diarize.py" \
        --input "$chunk" \
        --output-dir "$WORK_DIR" \
        --no-diarize \
        --formats json
done

echo "[chunked] Running global diarization on full audio..."
python - <<PY
import os, json
from pathlib import Path
from whisperx.diarize import DiarizationPipeline
import whisperx

hf = os.environ.get("HF_TOKEN")
if not hf:
    raise SystemExit("HF_TOKEN not set")

audio = whisperx.load_audio("$INPUT")
pipe = DiarizationPipeline(use_auth_token=hf, device="cpu")
diar = pipe(audio)

# Save diarization to disk for the merge step
out = Path("$WORK_DIR/global_diarization.json")
records = []
for turn, _, speaker in diar.itertracks(yield_label=True):
    records.append({"start": turn.start, "end": turn.end, "speaker": speaker})
out.write_text(json.dumps(records, indent=2))
print(f"Saved {len(records)} diarization turns")
PY

echo "[chunked] Merging chunk transcripts with global diarization..."
python - <<PY > "$OUT_DIR/${STEM}_merged.json"
import json, glob
from pathlib import Path

diar = json.loads(Path("$WORK_DIR/global_diarization.json").read_text())
# Time offsets from split points
points = [0.0] + [float(x) for x in open("$WORK_DIR/split_points.txt").read().split()]

merged_segments = []
for i, cj in enumerate(sorted(glob.glob("$WORK_DIR/${STEM}_chunk_*.json"))):
    offset = points[i]
    data = json.loads(Path(cj).read_text())
    for seg in data["segments"]:
        seg["start"] += offset
        seg["end"] += offset
        for w in seg.get("words", []):
            if w.get("start") is not None: w["start"] += offset
            if w.get("end") is not None: w["end"] += offset
        merged_segments.append(seg)

# Assign speaker by majority overlap with diarization turns
for seg in merged_segments:
    best_speaker, best_overlap = None, 0.0
    for d in diar:
        overlap = max(0, min(seg["end"], d["end"]) - max(seg["start"], d["start"]))
        if overlap > best_overlap:
            best_overlap = overlap
            best_speaker = d["speaker"]
    seg["speaker"] = best_speaker or "SPEAKER_??"

payload = {
    "source": "$INPUT",
    "segments": merged_segments,
    "speakers": sorted({s["speaker"] for s in merged_segments}),
}
# Simple turn merge
turns = []
for s in merged_segments:
    if turns and turns[-1]["speaker"] == s["speaker"] and s["start"] - turns[-1]["end"] < 1.5:
        turns[-1]["end"] = s["end"]
        turns[-1]["text"] += " " + s["text"].strip()
    else:
        turns.append({"speaker": s["speaker"], "start": s["start"], "end": s["end"], "text": s["text"].strip()})
payload["turns"] = turns
print(json.dumps(payload, ensure_ascii=False, indent=2))
PY

echo "[chunked] Done. Output: $OUT_DIR/${STEM}_merged.json"
