#!/usr/bin/env python3
"""Adapter: Azure AI Speech batch-transcription JSON -> WhisperX payload.

The exported whisperx-transcribe-diarize skill post-processes a JSON written
by scripts/transcribe_diarize.py (keys: source, duration_seconds, language,
model, compute_type, device, diarized, aligned, segments[], turns[],
speakers[]). In this environment transcription runs on Azure AI Speech
(EU region, workflows/speech-transcription.json), whose output is
`recognizedPhrases[]` with `speaker`, `offsetInTicks`, `durationInTicks`
and `nBest[0].display`/`words[]`. This adapter converts the Speech result
so the byte-verified scripts (format_transcript.py, relabel_speakers.py,
normalize_pt_br.py) run unchanged.

Usage (inside code_interpreter, after unzipping the skill package):
    python foundry/speech_to_whisperx.py --input speech.json \
        --output transcript.json [--source meeting.wav] [--language pt-BR]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

TICKS_PER_SECOND = 10_000_000


def _ticks(v) -> float:
    try:
        return float(v) / TICKS_PER_SECOND
    except (TypeError, ValueError):
        return 0.0


def _speaker(phrase: dict) -> str:
    s = phrase.get("speaker")
    return f"SPEAKER_{int(s):02d}" if isinstance(s, int) or str(s).isdigit() \
        else "SPEAKER_??"


def build_turns(segments: list[dict]) -> list[dict]:
    """Merge consecutive same-speaker segments (mirrors transcribe_diarize)."""
    turns: list[dict] = []
    for seg in segments:
        if turns and turns[-1]["speaker"] == seg["speaker"]:
            turns[-1]["end"] = seg["end"]
            turns[-1]["text"] = (turns[-1]["text"] + " " + seg["text"]).strip()
        else:
            turns.append({"speaker": seg["speaker"], "start": seg["start"],
                          "end": seg["end"], "text": seg["text"]})
    return turns


def convert(speech: dict, source: str = "", language: str = "") -> dict:
    phrases = sorted(speech.get("recognizedPhrases", []),
                     key=lambda p: p.get("offsetInTicks", 0))
    segments = []
    for ph in phrases:
        best = (ph.get("nBest") or [{}])[0]
        start = _ticks(ph.get("offsetInTicks"))
        end = start + _ticks(ph.get("durationInTicks"))
        speaker = _speaker(ph)
        words = [{
            "word": w.get("word", ""),
            "start": _ticks(w.get("offsetInTicks")),
            "end": _ticks(w.get("offsetInTicks")) + _ticks(w.get("durationInTicks")),
            "score": w.get("confidence"),
            "speaker": speaker,
        } for w in best.get("words", [])]
        segments.append({"start": start, "end": end, "speaker": speaker,
                         "text": (best.get("display") or best.get("lexical")
                                  or "").strip(), "words": words})
    turns = build_turns(segments)
    duration = _ticks(speech.get("durationInTicks")) or (
        segments[-1]["end"] if segments else 0.0)
    return {
        "source": source or speech.get("source", ""),
        "duration_seconds": duration,
        "language": language or (phrases[0].get("locale", "unknown")
                                 if phrases else "unknown"),
        "model": "azure-ai-speech-batch",
        "compute_type": "cloud-eu",
        "device": "azure",
        "diarized": any(p.get("speaker") is not None for p in phrases),
        "aligned": True,
        "segments": segments,
        "turns": turns,
        "speakers": sorted({t["speaker"] for t in turns if t["speaker"]}),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", "-i", required=True)
    ap.add_argument("--output", "-o", required=True)
    ap.add_argument("--source", default="")
    ap.add_argument("--language", default="")
    args = ap.parse_args()
    speech = json.loads(Path(args.input).read_text(encoding="utf-8"))
    payload = convert(speech, args.source, args.language)
    Path(args.output).write_text(json.dumps(payload, ensure_ascii=False,
                                            indent=2), encoding="utf-8")
    print(f"wrote {args.output}: {len(payload['segments'])} segments, "
          f"{len(payload['speakers'])} speakers")
    return 0


if __name__ == "__main__":
    sys.exit(main())
