---
name: whisperx-transcribe-diarize
description: "Transcribe audio or video files locally on macOS (Apple Silicon M1/M2/M3) with speaker diarization and word-level timestamps using WhisperX, pyannote.audio, and Whisper large-v3. ALWAYS use this skill when the user asks to transcribe audio, transcribe with speakers, identify speakers, ask quem fala quando, request transcrição com diarização, speaker diarization, split audio by speaker, or who said what; when converting .m4a/.mp3/.wav/.mp4/.mov/.flac/.ogg/.opus to text with timestamps; or when uploading an audio/video file and asking for a transcript. Outputs include TXT with timestamped speaker blocks, SRT and VTT subtitles, JSON with word-level timestamps, and optionally per-speaker audio clips. Optimized for PT-BR (Portuguese Brazilian) but supports 99 languages. Handles long files (4h+) via VAD chunking. Runs 100% locally — no upload, no API keys for transcription (HuggingFace token required only for one-time diarization model download)."
---

# WhisperX Local Transcription with Speaker Diarization (PT-BR)

## 1. Purpose

This skill transcribes audio/video files **locally on macOS (Apple Silicon)** producing transcripts that answer three questions at once:

1. **What was said** (Whisper large-v3 ASR)
2. **When it was said** (word-level timestamps via forced alignment with wav2vec2)
3. **Who said it** (speaker diarization via pyannote.audio 3.1)

Default language is **Portuguese (Brazilian)**. The skill handles long-form audio (4h+) that exceeds Whisper's 30s window via VAD (Voice Activity Detection) chunking.

## 2. When to trigger

Trigger on any of these user intents:

- "Transcreve este áudio", "transcribe this", "make a transcript"
- "Identifica os falantes", "who spoke when", "diariza este ficheiro"
- "Legendas para este vídeo" (SRT/VTT)
- User uploads `.m4a .mp3 .wav .mp4 .mov .flac .ogg .opus .webm .aac` and asks anything about its content
- "Split this recording by speaker"
- Requests for meeting minutes, interview transcripts, podcast transcription, legal/forensic audio analysis

If the user just wants **what was said** (no speakers), you can still use this skill but pass `--no-diarize` to save ~40% runtime.

## 3. Pre-flight checks (run once per machine)

Before running the transcription script, verify the environment is ready. Run `scripts/check_env.sh` — it reports on each dependency. If something is missing, point the user to `references/installation.md`.

Minimum requirements:

- macOS 12+ on Apple Silicon (M1/M2/M3/M4) — also works on x86 with CPU fallback
- Python 3.10 or 3.11 (pyannote 3.1 does not support 3.12+ reliably yet)
- `ffmpeg` installed via Homebrew (`brew install ffmpeg`)
- ~10 GB free disk (models cache in `~/.cache/huggingface/` and `~/.cache/whisper/`)
- HuggingFace token with access to `pyannote/speaker-diarization-3.1` (one-time EULA acceptance — see `references/installation.md` §3)

## 4. Core workflow

### Step 1 — Locate the input file

The audio is typically at `/mnt/user-data/uploads/<filename>` (when user uploaded it) **or** the user tells you a local path on their Mac. Since this skill is designed to run on the user's Mac, **the script is meant to be executed by the user locally, not inside Claude's sandbox.**

Your job in the sandbox is to:
1. Generate/customize the transcription command for their specific file and preferences
2. Explain exactly what to paste into their Terminal
3. After they run it, help them interpret/post-process the output

### Step 2 — Build the command

The canonical invocation is:

```bash
python scripts/transcribe_diarize.py \
  --input "/path/to/audio.m4a" \
  --output-dir "./transcripts" \
  --language pt \
  --model large-v3 \
  --compute-type int8 \
  --device auto \
  --min-speakers 2 \
  --max-speakers 6 \
  --hf-token "$HF_TOKEN" \
  --formats txt,srt,vtt,json
```

Key parameter decisions — apply these defaults unless the user overrides:

| Scenario | Recommended flags |
|---|---|
| Meeting / interview PT-BR, unknown speaker count | `--language pt --min-speakers 2 --max-speakers 8` |
| Known N-participant call (e.g. 1-on-1) | `--language pt --min-speakers 2 --max-speakers 2` |
| Podcast / monologue | `--language pt --no-diarize` |
| Legal / forensic (Henry Borel / processo style) | `--language pt --model large-v3 --compute-type float32 --formats txt,srt,json` (max accuracy) |
| Long file 4h+ on 16GB RAM M1 | `--compute-type int8 --batch-size 8` |
| English audio | `--language en` |
| Auto-detect language | omit `--language` |

**Device selection:** Apple Silicon users should prefer `--device auto` which resolves to CPU with int8 quantization. WhisperX's CTranslate2 backend runs faster on CPU int8 than on MPS for most M1/M2 configurations as of 2026, because MPS support for int8 is still incomplete. For M3 Pro/Max and M4, test both.

### Step 3 — Execute

In the sandbox, you **cannot** run the actual transcription (no GPU, no pyannote models, no HF token). Instead:

- Present the exact command block for the user to copy
- Tell them to `cd` into the skill directory first
- Warn about first-run model downloads (~3 GB Whisper + ~500 MB pyannote)
- Estimate runtime: roughly **1× real-time on M1 Pro with int8** for ASR, plus **~0.3× real-time** for diarization. So a 4h33m file ≈ 5–6h total on first run.

If the user uploaded the audio to the sandbox and wants you to just show them what the transcript *would* look like on a short snippet, you can extract a 60s sample with ffmpeg and produce a structural mock-up — but make clear it is a mock, not a real transcription.

### Step 4 — Parse and present results

After the user runs the script, they will share the output files. Parse the JSON (most information-dense) using `scripts/format_transcript.py` to produce the final deliverable in the format they want:

- **Readable TXT** with `[00:03:12] SPEAKER_01: ...` blocks grouped by turn
- **Markdown** with speaker headers and timestamps
- **HTML dashboard** (teal theme, Verdana) with clickable timestamps and speaker color-coding — use `assets/transcript_template.html`
- **DOCX** for legal delivery — via `python-docx`, see `references/output_formats.md`

### Step 5 — Post-processing (optional)

Common follow-ups:

- **Speaker relabeling**: `SPEAKER_00 → "Patrícia"`, `SPEAKER_01 → "Interviewer"`. Use `scripts/relabel_speakers.py --map '{"SPEAKER_00":"Patrícia"}'`
- **Per-speaker clip extraction**: `scripts/extract_speaker_clips.py` splits the source audio into one file per speaker
- **Summary / minute generation**: feed the TXT back to Claude for summarization — keep the timestamps so claims are auditable
- **Translation**: pass the JSON through Whisper's `--task translate` (English only) or through a separate MT step

## 5. Chunking very long files

Whisper internally windows at 30s but WhisperX's VAD handles unlimited length. However, RAM is the limit: on a 16GB M1 Pro, files > 3h with diarization can OOM because pyannote holds the full embedding matrix in memory.

If the user has a 4h+ file and 16GB RAM, use `scripts/chunked_pipeline.sh` which:

1. Splits the source at silence boundaries using ffmpeg silencedetect (keeps speaker continuity better than blind slicing)
2. Transcribes each chunk independently
3. Runs diarization globally across all chunks with a shared embedding space (via `pyannote/embedding` cached once)
4. Stitches the final JSON with consistent SPEAKER_XX labels

This is slower than monolithic runs but avoids OOM and supports resume-on-failure.

## 6. Accuracy notes for PT-BR

- **large-v3** significantly outperforms large-v2 for Brazilian Portuguese (WER ~6–9% on clean audio, vs ~12% for large-v2).
- WhisperX's forced alignment for PT uses `jonatasgrosman/wav2vec2-large-xlsr-53-portuguese`. This is **PT-PT trained** but works acceptably for PT-BR. If word timestamps look off for a specific speaker, the skill can swap to `Edresson/wav2vec2-large-xlsr-coraa-portuguese` (BR-trained) — see `references/pt_br_tuning.md`.
- Diarization accuracy degrades below 2s of speech per speaker and with overlapping speech > 20%. For forensic work flag segments with overlap for manual review.
- Numbers and proper nouns: Whisper often writes "vinte e cinco" vs "25" inconsistently. Apply normalization with `scripts/normalize_pt_br.py` if the user needs consistent formatting.

## 7. Troubleshooting quick reference

| Symptom | Likely cause | Fix |
|---|---|---|
| `401 Unauthorized` on pyannote load | HF token missing or EULA not accepted | Log in at huggingface.co, accept the model cards, regenerate token |
| OOM killed | Batch size too high or file too long | `--batch-size 4 --compute-type int8`, or use `chunked_pipeline.sh` |
| Speakers swap mid-file | Long silence or channel switch | Increase `--min-speakers`, or run diarization separately then merge |
| Gibberish transcription | Wrong language detected | Force `--language pt` |
| Slow on M1 (>3× real-time) | CPU thread contention | `export OMP_NUM_THREADS=4` before running |
| `ffmpeg: command not found` | Homebrew missing | `brew install ffmpeg` |
| Segfault on load | Python 3.12 | Downgrade to 3.11: `brew install python@3.11` |

Full troubleshooting and environment recovery in `references/troubleshooting.md`.

## 8. Reference files

- `references/installation.md` — First-time setup: Homebrew, Python 3.11, venv, pip install, HF token, EULA acceptance
- `references/pt_br_tuning.md` — Language-specific tuning, alternative alignment models, domain prompts
- `references/output_formats.md` — TXT / SRT / VTT / JSON / DOCX / HTML spec with examples
- `references/troubleshooting.md` — Deep diagnostic guide, log inspection, cache cleanup
- `references/cli_reference.md` — Full flag-by-flag documentation for `transcribe_diarize.py`

## 9. Scripts

- `scripts/check_env.sh` — Validates Python, ffmpeg, packages, HF token, disk space
- `scripts/install.sh` — One-shot installer (Homebrew + venv + pip)
- `scripts/transcribe_diarize.py` — Main pipeline
- `scripts/format_transcript.py` — JSON → readable TXT/MD/HTML
- `scripts/relabel_speakers.py` — Apply human speaker name map
- `scripts/extract_speaker_clips.py` — Split source audio by speaker
- `scripts/chunked_pipeline.sh` — Long-file safe mode with silence-aware splitting
- `scripts/normalize_pt_br.py` — Number/punctuation normalization for PT-BR

## 10. Assets

- `assets/transcript_template.html` — Teal-themed Verdana HTML viewer with collapsible turns, timestamp anchors, and speaker color legend. Matches your ENX/TPSRCA visual standard (dark teal `#003530` header).
- `assets/speaker_palette.json` — 10 accessible speaker colors (WCAG AA on white)

## 11. Privacy & compliance notes

Everything runs locally: **no audio ever leaves the user's Mac** once models are cached. This matters for:

- GDPR Art. 28 processing minimization
- DORA operational resilience (no third-party ICT dependency for the transcription pipeline after initial setup)
- Legal-privilege audio (forensic / `processo` cases)
- Corporate meetings under NDA

The only network traffic is the one-time model download from HuggingFace Hub. After that, you can run fully offline with `HF_HUB_OFFLINE=1`.
