#!/usr/bin/env bash
# check_env.sh — Non-destructive diagnostic. Reports status of each dependency.

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$SKILL_DIR/.venv"

ok()   { printf "  \033[1;32m✓\033[0m %s\n" "$*"; }
bad()  { printf "  \033[1;31m✗\033[0m %s\n" "$*"; }
info() { printf "  \033[1;34mi\033[0m %s\n" "$*"; }

echo "=== whisperx-transcribe-diarize — environment check ==="
echo ""

# OS / arch
UNAME="$(uname -sm)"
if [[ "$UNAME" == "Darwin arm64" ]]; then
  ok "macOS Apple Silicon detected ($UNAME)"
else
  info "OS/arch: $UNAME (not Apple Silicon — CPU fallback will be slow)"
fi

# Homebrew
if command -v brew >/dev/null 2>&1; then
  ok "Homebrew: $(brew --version | head -1)"
else
  bad "Homebrew missing — install from https://brew.sh"
fi

# ffmpeg
if command -v ffmpeg >/dev/null 2>&1; then
  ok "ffmpeg: $(ffmpeg -version | head -1 | cut -d' ' -f1-3)"
else
  bad "ffmpeg missing — brew install ffmpeg"
fi

# Python 3.11
if command -v python3.11 >/dev/null 2>&1; then
  ok "Python 3.11: $(python3.11 --version)"
elif command -v python3 >/dev/null 2>&1; then
  info "python3 present: $(python3 --version) — pyannote prefers 3.10 or 3.11"
else
  bad "No python3 on PATH"
fi

# venv
if [[ -d "$VENV_DIR" ]]; then
  ok "venv present at .venv"
  # shellcheck disable=SC1091
  source "$VENV_DIR/bin/activate"

  for pkg in torch whisperx pyannote.audio faster_whisper ctranslate2; do
    if python -c "import $pkg" 2>/dev/null; then
      ok "  $pkg imports OK"
    else
      bad "  $pkg not installed in venv"
    fi
  done
else
  bad "venv missing at $VENV_DIR — run scripts/install.sh"
fi

# HF token
if [[ -n "${HF_TOKEN:-}" ]]; then
  ok "HF_TOKEN set (length ${#HF_TOKEN})"
else
  bad "HF_TOKEN not set — required for pyannote diarization"
  info "  Get one at https://huggingface.co/settings/tokens"
  info "  Then: export HF_TOKEN=hf_xxx"
fi

# Disk
AVAIL_GB=$(df -g "$HOME" | awk 'NR==2 {print $4}')
if (( AVAIL_GB > 10 )); then
  ok "Disk free in \$HOME: ${AVAIL_GB} GB"
else
  bad "Disk free in \$HOME: ${AVAIL_GB} GB — models need ~10 GB"
fi

# Model cache
HF_CACHE="${HF_HOME:-$HOME/.cache/huggingface}"
if [[ -d "$HF_CACHE" ]]; then
  CACHE_SIZE=$(du -sh "$HF_CACHE" 2>/dev/null | awk '{print $1}')
  info "HuggingFace cache: $HF_CACHE ($CACHE_SIZE)"
fi

echo ""
echo "Done. If all checks above are ✓ you're ready to transcribe."
