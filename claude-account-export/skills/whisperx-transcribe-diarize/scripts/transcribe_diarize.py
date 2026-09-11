#!/usr/bin/env python3
"""
transcribe_diarize.py — Local audio transcription with speaker diarization.

Pipeline:
  1. Load audio via ffmpeg, resample to 16kHz mono
  2. WhisperX ASR (Whisper large-v3 via CTranslate2, int8 or float32)
  3. Forced alignment with wav2vec2 (word-level timestamps)
  4. pyannote.audio 3.1 speaker diarization
  5. Assign speakers to words, merge into turns
  6. Emit TXT / SRT / VTT / JSON outputs

Runs locally on macOS (Apple Silicon) — no data leaves the machine after the
one-time model download from HuggingFace.

Author: Claude for Francisco Gomes (Euronext TPRM / InfoSec Assurance)
License: MIT
"""

from __future__ import annotations

import argparse
import gc
import json
import os
import sys
import time
from datetime import timedelta
from pathlib import Path
from typing import Any

# Third-party imports deferred to main() so --help works without deps installed


def fmt_ts(seconds: float, comma: bool = False) -> str:
    """Format seconds as HH:MM:SS,mmm (SRT) or HH:MM:SS.mmm (VTT/plain)."""
    td = timedelta(seconds=max(seconds, 0.0))
    total_ms = int(td.total_seconds() * 1000)
    hours, rem = divmod(total_ms, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    secs, ms = divmod(rem, 1000)
    sep = "," if comma else "."
    return f"{hours:02d}:{minutes:02d}:{secs:02d}{sep}{ms:03d}"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Local transcription with speaker diarization (WhisperX + pyannote).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--input", "-i", required=True, help="Path to audio/video file.")
    p.add_argument("--output-dir", "-o", default="./transcripts", help="Output directory.")
    p.add_argument("--language", "-l", default="pt", help="Language code (pt, en, es, ...). Omit or 'auto' to auto-detect.")
    p.add_argument("--model", "-m", default="large-v3", help="Whisper model: tiny, base, small, medium, large-v2, large-v3.")
    p.add_argument("--compute-type", default="int8", choices=["int8", "int8_float16", "float16", "float32"],
                   help="CT2 compute type. int8 is fastest on Apple Silicon CPU.")
    p.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda", "mps"],
                   help="Inference device. 'auto' picks cpu on Apple Silicon.")
    p.add_argument("--batch-size", type=int, default=8, help="Batch size for transcription.")
    p.add_argument("--no-diarize", action="store_true", help="Skip speaker diarization (faster).")
    p.add_argument("--min-speakers", type=int, default=None, help="Minimum speakers hint for pyannote.")
    p.add_argument("--max-speakers", type=int, default=None, help="Maximum speakers hint for pyannote.")
    p.add_argument("--hf-token", default=os.environ.get("HF_TOKEN"),
                   help="HuggingFace token for pyannote. Env: HF_TOKEN.")
    p.add_argument("--formats", default="txt,srt,vtt,json",
                   help="Comma-separated list of output formats.")
    p.add_argument("--initial-prompt", default=None,
                   help="Optional prompt to bias transcription (e.g. proper nouns).")
    p.add_argument("--no-align", action="store_true", help="Skip forced alignment (no word timestamps).")
    p.add_argument("--verbose", "-v", action="store_true")
    return p.parse_args()


def resolve_device(choice: str) -> str:
    if choice != "auto":
        return choice
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
    except ImportError:
        pass
    # On Apple Silicon, CPU + int8 via CT2 beats MPS for Whisper as of 2026.
    return "cpu"


def build_turns(segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merge contiguous same-speaker segments into turns."""
    turns: list[dict[str, Any]] = []
    for seg in segments:
        speaker = seg.get("speaker", "SPEAKER_??")
        text = seg.get("text", "").strip()
        if not text:
            continue
        if turns and turns[-1]["speaker"] == speaker and (seg["start"] - turns[-1]["end"]) < 1.5:
            turns[-1]["end"] = seg["end"]
            turns[-1]["text"] += " " + text
        else:
            turns.append({
                "speaker": speaker,
                "start": seg["start"],
                "end": seg["end"],
                "text": text,
            })
    return turns


def write_txt(turns: list[dict[str, Any]], path: Path) -> None:
    with path.open("w", encoding="utf-8") as f:
        for t in turns:
            f.write(f"[{fmt_ts(t['start'])} → {fmt_ts(t['end'])}] {t['speaker']}:\n")
            f.write(f"    {t['text']}\n\n")


def write_srt(segments: list[dict[str, Any]], path: Path) -> None:
    with path.open("w", encoding="utf-8") as f:
        for i, seg in enumerate(segments, 1):
            speaker = seg.get("speaker", "")
            prefix = f"[{speaker}] " if speaker else ""
            f.write(f"{i}\n")
            f.write(f"{fmt_ts(seg['start'], comma=True)} --> {fmt_ts(seg['end'], comma=True)}\n")
            f.write(f"{prefix}{seg['text'].strip()}\n\n")


def write_vtt(segments: list[dict[str, Any]], path: Path) -> None:
    with path.open("w", encoding="utf-8") as f:
        f.write("WEBVTT\n\n")
        for i, seg in enumerate(segments, 1):
            speaker = seg.get("speaker", "")
            prefix = f"<v {speaker}>" if speaker else ""
            f.write(f"{fmt_ts(seg['start'])} --> {fmt_ts(seg['end'])}\n")
            f.write(f"{prefix}{seg['text'].strip()}\n\n")


def write_json(payload: dict[str, Any], path: Path) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def main() -> int:
    args = parse_args()

    # Late imports — keeps --help responsive when deps missing
    try:
        import whisperx
        import torch
    except ImportError as e:
        print(f"[fatal] Missing dependency: {e}", file=sys.stderr)
        print("        Run scripts/install.sh or: pip install whisperx pyannote.audio", file=sys.stderr)
        return 1

    input_path = Path(args.input).expanduser().resolve()
    if not input_path.exists():
        print(f"[fatal] Input not found: {input_path}", file=sys.stderr)
        return 2

    out_dir = Path(args.output_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = input_path.stem
    formats = {fmt.strip().lower() for fmt in args.formats.split(",") if fmt.strip()}

    device = resolve_device(args.device)
    language = None if (args.language or "").lower() == "auto" else args.language

    t0 = time.time()
    print(f"[1/5] Loading audio: {input_path.name}")
    audio = whisperx.load_audio(str(input_path))
    duration_s = len(audio) / 16000.0
    print(f"      Duration: {fmt_ts(duration_s)} ({duration_s:.1f}s)")

    print(f"[2/5] Transcribing with Whisper {args.model} on {device} ({args.compute_type})")
    asr_opts: dict[str, Any] = {}
    if args.initial_prompt:
        asr_opts["initial_prompt"] = args.initial_prompt

    model = whisperx.load_model(
        args.model,
        device=device,
        compute_type=args.compute_type,
        language=language,
        asr_options=asr_opts or None,
    )
    result = model.transcribe(audio, batch_size=args.batch_size)
    detected_language = result.get("language", language or "pt")
    print(f"      Language: {detected_language} | Segments: {len(result['segments'])}")

    # Free ASR model before alignment to save RAM
    del model
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    if not args.no_align:
        print(f"[3/5] Aligning words (forced alignment, wav2vec2)")
        try:
            align_model, align_metadata = whisperx.load_align_model(
                language_code=detected_language,
                device=device,
            )
            result = whisperx.align(
                result["segments"],
                align_model,
                align_metadata,
                audio,
                device,
                return_char_alignments=False,
            )
            del align_model
            gc.collect()
        except Exception as e:
            print(f"      [warn] Alignment failed: {e}. Continuing without word timestamps.")
    else:
        print("[3/5] Alignment skipped (--no-align)")

    if not args.no_diarize:
        print(f"[4/5] Diarizing speakers (pyannote 3.1)")
        if not args.hf_token:
            print("      [fatal] HuggingFace token required for diarization.", file=sys.stderr)
            print("              Set HF_TOKEN env var or pass --hf-token.", file=sys.stderr)
            return 3
        try:
            # whisperx>=3.2 renamed this; handle both
            try:
                from whisperx.diarize import DiarizationPipeline
            except ImportError:
                from whisperx import DiarizationPipeline  # type: ignore

            diarize_model = DiarizationPipeline(
                use_auth_token=args.hf_token,
                device=device,
            )
            diarize_segments = diarize_model(
                audio,
                min_speakers=args.min_speakers,
                max_speakers=args.max_speakers,
            )
            result = whisperx.assign_word_speakers(diarize_segments, result)
            del diarize_model
            gc.collect()
        except Exception as e:
            print(f"      [warn] Diarization failed: {e}")
            print( "             Continuing without speaker labels.")
    else:
        print("[4/5] Diarization skipped (--no-diarize)")

    # Ensure every segment carries a speaker field (default UNKNOWN) + strip junk
    segments: list[dict[str, Any]] = []
    for seg in result.get("segments", []):
        segments.append({
            "start": float(seg.get("start", 0.0)),
            "end": float(seg.get("end", 0.0)),
            "speaker": seg.get("speaker", "SPEAKER_??" if not args.no_diarize else ""),
            "text": seg.get("text", "").strip(),
            "words": [
                {
                    "word": w.get("word", ""),
                    "start": w.get("start"),
                    "end": w.get("end"),
                    "score": w.get("score"),
                    "speaker": w.get("speaker"),
                }
                for w in seg.get("words", [])
            ],
        })

    turns = build_turns(segments)

    print(f"[5/5] Writing outputs → {out_dir}")
    written: list[Path] = []
    if "txt" in formats:
        p = out_dir / f"{stem}.txt"
        write_txt(turns, p)
        written.append(p)
    if "srt" in formats:
        p = out_dir / f"{stem}.srt"
        write_srt(segments, p)
        written.append(p)
    if "vtt" in formats:
        p = out_dir / f"{stem}.vtt"
        write_vtt(segments, p)
        written.append(p)
    if "json" in formats:
        p = out_dir / f"{stem}.json"
        payload = {
            "source": str(input_path),
            "duration_seconds": duration_s,
            "language": detected_language,
            "model": args.model,
            "compute_type": args.compute_type,
            "device": device,
            "diarized": not args.no_diarize,
            "aligned": not args.no_align,
            "segments": segments,
            "turns": turns,
            "speakers": sorted({t["speaker"] for t in turns if t["speaker"]}),
        }
        write_json(payload, p)
        written.append(p)

    elapsed = time.time() - t0
    rtf = elapsed / duration_s if duration_s > 0 else 0
    print(f"\nDone in {elapsed/60:.1f} min (RTF={rtf:.2f}×)")
    print("Files:")
    for p in written:
        print(f"  {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
