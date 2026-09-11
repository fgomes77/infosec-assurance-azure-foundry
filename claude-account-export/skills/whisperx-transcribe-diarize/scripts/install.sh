#!/usr/bin/env bash
# install.sh — One-shot setup for whisperx-transcribe-diarize on macOS (Apple Silicon)
#
# Usage:
#   cd <skill-dir>
#   bash scripts/install.sh
#
# What it does:
#   1. Verifies Homebrew + ffmpeg + Python 3.11
#   2. Creates a local venv at .venv
#   3. Installs PyTorch (CPU build), WhisperX, pyannote.audio
#   4. Prints next steps for HuggingFace token setup

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$SKILL_DIR/.venv"

say() { printf "\033[1;36m[install]\033[0m %s\n" "$*"; }
warn() { printf "\033[1;33m[warn]\033[0m %s\n" "$*"; }
die() { printf "\033[1;31m[fatal]\033[0m %s\n" "$*" >&2; exit 1; }

# --- 1. System dependencies ---------------------------------------------------

if ! command -v brew >/dev/null 2>&1; then
  die "Homebrew not found. Install from https://brew.sh then re-run."
fi

say "Checking ffmpeg..."
if ! command -v ffmpeg >/dev/null 2>&1; then
  say "Installing ffmpeg via Homebrew..."
  brew install ffmpeg
else
  say "ffmpeg OK ($(ffmpeg -version | head -1))"
fi

# --- 2. Python 3.11 -----------------------------------------------------------

PY_BIN=""
for cand in python3.11 /opt/homebrew/bin/python3.11 /usr/local/bin/python3.11; do
  if command -v "$cand" >/dev/null 2>&1; then
    PY_BIN="$cand"
    break
  fi
done

if [[ -z "$PY_BIN" ]]; then
  say "Installing Python 3.11 via Homebrew..."
  brew install python@3.11
  PY_BIN="$(brew --prefix)/opt/python@3.11/bin/python3.11"
fi

say "Using Python: $PY_BIN ($($PY_BIN --version))"

# --- 3. Virtual environment ---------------------------------------------------

if [[ ! -d "$VENV_DIR" ]]; then
  say "Creating venv at $VENV_DIR"
  "$PY_BIN" -m venv "$VENV_DIR"
else
  say "venv already exists at $VENV_DIR"
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

python -m pip install --upgrade pip wheel setuptools

# --- 4. Core packages ---------------------------------------------------------
#
# Notes on pins:
#   - torch 2.2+ on macOS arm64 via pip wheels
#   - whisperx pulls faster-whisper + ctranslate2 + pyannote.audio
#   - numpy < 2 required by some transitive deps as of writing

say "Installing PyTorch (CPU build for Apple Silicon)..."
pip install --upgrade "torch>=2.2,<3" "torchaudio>=2.2,<3"

say "Installing WhisperX and friends..."
pip install --upgrade \
    "whisperx>=3.3.1" \
    "pyannote.audio>=3.1" \
    "faster-whisper>=1.0" \
    "ctranslate2>=4.4" \
    "numpy<2" \
    "soundfile" \
    "librosa"

# --- 5. Sanity check ---------------------------------------------------------

say "Running import check..."
python - <<'PY'
import sys
try:
    import torch, whisperx, pyannote.audio, faster_whisper
    print(f"  torch:           {torch.__version__}")
    print(f"  whisperx:        {whisperx.__version__ if hasattr(whisperx, '__version__') else 'ok'}")
    print(f"  pyannote.audio:  {pyannote.audio.__version__}")
    print(f"  faster-whisper:  {faster_whisper.__version__}")
except Exception as e:
    print(f"Import failed: {e}", file=sys.stderr)
    sys.exit(1)
PY

say "Installation complete."
echo ""
echo "Next steps:"
echo "  1. Create a HuggingFace account at https://huggingface.co and accept the EULAs:"
echo "       https://hf.co/pyannote/speaker-diarization-3.1"
echo "       https://hf.co/pyannote/segmentation-3.0"
echo "  2. Create a READ token at https://huggingface.co/settings/tokens"
echo "  3. Export it:  export HF_TOKEN=hf_xxx_your_token_xxx"
echo "     (add to ~/.zshrc for persistence)"
echo "  4. Activate the venv in any new shell:  source $VENV_DIR/bin/activate"
echo "  5. Run:        python scripts/transcribe_diarize.py --input YOUR_AUDIO.m4a"
