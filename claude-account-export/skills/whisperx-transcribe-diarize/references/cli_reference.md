# CLI Reference — `transcribe_diarize.py`

Full documentation of every flag.

## Invocation

```bash
python scripts/transcribe_diarize.py [OPTIONS]
```

## Required

### `--input`, `-i PATH`
Path to the audio or video file. Supported (via ffmpeg): `.m4a .mp3 .wav .flac .ogg .opus .aac .mp4 .mov .webm .mkv` and anything else ffmpeg can demux.

## Output

### `--output-dir`, `-o DIR`
Directory where output files are written. Created if missing.
Default: `./transcripts`

### `--formats STRING`
Comma-separated list of formats to generate.
Options: `txt`, `srt`, `vtt`, `json`
Default: `txt,srt,vtt,json`

Example: `--formats txt,json`

## ASR

### `--language`, `-l CODE`
ISO 639-1 language code. Pass `auto` (or omit) for auto-detection.
Common values: `pt` (Portuguese), `en` (English), `es` (Spanish), `fr` (French), `de` (German), `it` (Italian).
Default: `pt`

Full list: https://github.com/openai/whisper/blob/main/whisper/tokenizer.py

### `--model`, `-m NAME`
Whisper model size.
Options: `tiny`, `base`, `small`, `medium`, `large-v2`, `large-v3`, `distil-large-v3`
Default: `large-v3`

Distil models are ~6× faster with ~2% WER cost — good for drafts.

### `--compute-type TYPE`
CTranslate2 quantization format.
Options:
- `int8` — fastest on Apple Silicon CPU (default, recommended)
- `int8_float16` — hybrid, slightly more accurate than pure int8
- `float16` — fast on NVIDIA GPUs, slow on CPU
- `float32` — max accuracy, slowest, highest RAM

Default: `int8`

### `--device`
Inference device.
Options:
- `auto` — picks `cpu` on Apple Silicon, `cuda` if available
- `cpu`
- `cuda` — NVIDIA GPU
- `mps` — Apple Silicon GPU (unreliable with int8 currently)

Default: `auto`

### `--batch-size N`
Batch size for Whisper. Lower values = less RAM.
Default: `8`

Guidance: 16 on M1 Pro/Max with 32GB+, 8 on 16GB M1/M2, 4 if you hit OOM.

### `--initial-prompt TEXT`
Prompt to bias the first decoding step (helps with proper nouns, jargon).
Default: none.

Example: `--initial-prompt "Euronext, TPRM, DORA, NIS2, Claude"`

Keep under 200 characters.

## Alignment

### `--no-align`
Skip forced alignment. Faster, but no word-level timestamps — only segment-level.

## Diarization

### `--no-diarize`
Skip speaker diarization entirely. Use for monologue / single-speaker content. Saves ~30-40% runtime.

### `--min-speakers N`
Hint: minimum number of speakers to detect.
Default: none (let pyannote decide).

### `--max-speakers N`
Hint: maximum number of speakers to detect.
Default: none.

Tip: if you know there are exactly 2 speakers (1:1 interview), set `--min-speakers 2 --max-speakers 2` to avoid over-segmentation.

### `--hf-token TOKEN`
HuggingFace access token. Overrides `HF_TOKEN` environment variable.
Default: reads from `$HF_TOKEN`.

## Misc

### `--verbose`, `-v`
Increase logging output.

### `--help`, `-h`
Show this help and exit.

## Examples

**Standard meeting transcription (PT-BR, 2-6 speakers):**
```bash
python scripts/transcribe_diarize.py \
    --input meeting.m4a \
    --language pt \
    --min-speakers 2 --max-speakers 6
```

**Fast draft of a podcast episode:**
```bash
python scripts/transcribe_diarize.py \
    --input podcast.mp3 \
    --model distil-large-v3 \
    --no-diarize \
    --formats txt,srt
```

**Max-quality forensic transcription:**
```bash
python scripts/transcribe_diarize.py \
    --input testimony.wav \
    --model large-v3 \
    --compute-type float32 \
    --language pt \
    --min-speakers 2 --max-speakers 4 \
    --initial-prompt "Patrícia Santos, José Carlos Cabeço, Nelas, processo 277/22."
```

**English interview, auto-detect speaker count:**
```bash
python scripts/transcribe_diarize.py \
    --input interview.wav \
    --language en
```

**Memory-constrained (low RAM):**
```bash
python scripts/transcribe_diarize.py \
    --input long.m4a \
    --compute-type int8 \
    --batch-size 4 \
    --model medium
```

## Exit codes

- `0` — success
- `1` — missing Python dependency
- `2` — input file not found
- `3` — HF token missing (diarization requested but no token)
- other non-zero — underlying exception raised by whisperx/pyannote
