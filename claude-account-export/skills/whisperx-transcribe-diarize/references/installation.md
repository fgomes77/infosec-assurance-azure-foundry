# Installation Reference

Complete first-time setup for `whisperx-transcribe-diarize` on **macOS Apple Silicon (M1/M2/M3/M4)**.

## 1. Homebrew + system packages

If you don't have Homebrew yet:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Install the system dependencies:

```bash
brew install ffmpeg python@3.11
```

**Why Python 3.11?** `pyannote.audio` 3.1's pinned `torch` / `torchaudio` wheels and some transitive deps (notably `asteroid-filterbanks`) are not yet fully reliable on 3.12+. Stick with 3.11 until pyannote ships 3.2.

## 2. Skill installation

Assuming you've downloaded/extracted the skill to a folder (e.g. `~/skills/whisperx-transcribe-diarize`):

```bash
cd ~/skills/whisperx-transcribe-diarize
bash scripts/install.sh
```

This creates a venv at `.venv/` inside the skill directory and installs:

- `torch` + `torchaudio` (CPU build for arm64)
- `whisperx` (≥ 3.3.1)
- `pyannote.audio` (≥ 3.1)
- `faster-whisper`, `ctranslate2`
- `soundfile`, `librosa`

Total install size: ~3.5 GB.

## 3. HuggingFace token & EULA (REQUIRED for diarization)

Pyannote's diarization model is gated. You must:

1. **Create a HuggingFace account**: https://huggingface.co/join
2. **Accept the model cards** (click "Agree and access repository" on each):
   - https://hf.co/pyannote/speaker-diarization-3.1
   - https://hf.co/pyannote/segmentation-3.0
3. **Generate a READ token**: https://huggingface.co/settings/tokens → "New token" → Role: **Read**
4. **Export it** in your shell:

```bash
# Add to ~/.zshrc for persistence
echo 'export HF_TOKEN="hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"' >> ~/.zshrc
source ~/.zshrc
```

Verify:
```bash
echo $HF_TOKEN  # Should print your token
```

## 4. First run — sanity check

Activate the venv and run the environment check:

```bash
cd ~/skills/whisperx-transcribe-diarize
source .venv/bin/activate
bash scripts/check_env.sh
```

All green? Try a 60-second test file:

```bash
# Create a test clip from any audio you have
ffmpeg -i ~/Downloads/meeting.m4a -t 60 -c copy /tmp/test60.m4a

# Transcribe it
python scripts/transcribe_diarize.py \
    --input /tmp/test60.m4a \
    --output-dir ./transcripts \
    --language pt \
    --min-speakers 2 --max-speakers 4
```

First run will download:
- Whisper large-v3 (~3 GB) to `~/.cache/huggingface/hub/`
- Wav2vec2 PT alignment model (~1.2 GB)
- Pyannote diarization + segmentation (~500 MB)

Subsequent runs skip the downloads.

## 5. Offline mode

After models are cached, you can run with no network at all:

```bash
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
python scripts/transcribe_diarize.py --input ...
```

This is the recommended mode for forensic / privileged / GDPR-sensitive material.

## 6. Model cache locations

Default cache paths (macOS):

- Whisper / wav2vec2 / pyannote: `~/.cache/huggingface/hub/`
- CTranslate2 converted models: `~/.cache/huggingface/hub/models--Systran--faster-whisper-large-v3/`

You can relocate with:
```bash
export HF_HOME=/path/to/large/disk/hf_cache
```

## 7. Upgrading

```bash
cd ~/skills/whisperx-transcribe-diarize
source .venv/bin/activate
pip install --upgrade whisperx pyannote.audio faster-whisper
```

Check the [WhisperX changelog](https://github.com/m-bain/whisperX/releases) for breaking changes — the `DiarizationPipeline` import path has moved between versions. The main script handles both old and new locations.
