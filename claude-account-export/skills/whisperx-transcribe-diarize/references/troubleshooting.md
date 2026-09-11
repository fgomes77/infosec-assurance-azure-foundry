# Troubleshooting

## Installation issues

### `ERROR: Could not build wheels for ...`
Usually a compiler/Xcode issue on macOS.
```bash
xcode-select --install
brew install cmake
```
Then retry `bash scripts/install.sh`.

### `Segmentation fault` immediately on `import whisperx`
You're almost certainly on Python 3.12+. Downgrade:
```bash
brew install python@3.11
rm -rf .venv
bash scripts/install.sh
```

### `fatal error: 'portaudio.h' file not found`
Only matters if you install `pyaudio`. The skill doesn't need it; ignore.

## Runtime issues

### `OSError: Model not found: pyannote/speaker-diarization-3.1`
Your HuggingFace token is missing or you haven't accepted the EULA.
1. Verify: `echo $HF_TOKEN`
2. Go to https://hf.co/pyannote/speaker-diarization-3.1 and click "Agree"
3. Go to https://hf.co/pyannote/segmentation-3.0 and click "Agree"
4. Re-run.

### `401 Client Error: Unauthorized` during model download
Token is invalid or lacks Read access. Regenerate at https://huggingface.co/settings/tokens with Role = Read.

### `Killed: 9` mid-transcription
Out of memory (macOS killed the process). Options in order:
1. `--compute-type int8 --batch-size 4`
2. Use `chunked_pipeline.sh` instead
3. Close other RAM-heavy apps (Chrome tabs, Docker, VMs)
4. Use a smaller model: `--model medium`

### `RuntimeError: CUDA out of memory`
You're on a non-Apple GPU with too little VRAM. Use `--device cpu --compute-type int8`.

### Transcription completes but speakers = all `SPEAKER_00`
Diarization didn't produce multiple clusters. Causes:
- Audio is actually a single speaker
- Very short file (< 30s) — diarization needs data
- Heavy compression killed speaker embeddings — try a higher-bitrate source
Force: `--min-speakers 2`

### Speakers detected but all turns labelled wrong
Look at the raw diarization before Whisper merges:
```python
from whisperx.diarize import DiarizationPipeline
import whisperx, os
pipe = DiarizationPipeline(use_auth_token=os.environ["HF_TOKEN"], device="cpu")
diar = pipe(whisperx.load_audio("audio.m4a"))
for turn, _, speaker in diar.itertracks(yield_label=True):
    print(f"{turn.start:7.2f}-{turn.end:7.2f}  {speaker}")
```
If diarization itself is wrong, try constraining: `--min-speakers N --max-speakers N` where N is the true count.

### Gibberish output like "Obrigado por assistir!" at the end
Whisper hallucination — the model learned that YouTube videos end with these phrases. If the last segment looks like YouTube boilerplate, just trim it manually.

### Slow transcription (> 3× real-time on M1 Pro)
```bash
export OMP_NUM_THREADS=4        # don't oversubscribe
export TOKENIZERS_PARALLELISM=false
```
Also check Activity Monitor — if another process is using CPU, that's the culprit.

### `ffmpeg: Unknown input format`
Your file extension doesn't match the container. Let ffmpeg probe it:
```bash
ffmpeg -i mystery_file -c copy mystery_file.m4a
```
Or re-encode to a known format:
```bash
ffmpeg -i mystery_file -ar 16000 -ac 1 clean.wav
```

## Cache cleanup

If models get corrupted (rare, usually from aborted downloads):
```bash
rm -rf ~/.cache/huggingface/hub/models--pyannote*
rm -rf ~/.cache/huggingface/hub/models--Systran*
rm -rf ~/.cache/huggingface/hub/models--jonatasgrosman*
# Then re-run — models will re-download
```

Nuclear option — wipe entire HuggingFace cache:
```bash
rm -rf ~/.cache/huggingface/
```
You'll re-download ~5 GB on next run.

## Log collection for bug reports

```bash
python scripts/transcribe_diarize.py --input ... --verbose 2>&1 | tee run.log
bash scripts/check_env.sh >> run.log
pip freeze >> run.log
```
Attach `run.log` when asking for help.
