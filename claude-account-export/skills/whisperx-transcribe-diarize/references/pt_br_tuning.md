# PT-BR Tuning Reference

Specific tuning for **Brazilian Portuguese** transcription quality.

## 1. Model choice for PT-BR

| Model | Approx WER on clean PT-BR | Notes |
|---|---|---|
| `tiny` | ~25% | Testing only |
| `base` | ~18% | Not recommended for real work |
| `small` | ~13% | Acceptable for non-critical content |
| `medium` | ~10% | Good accuracy/speed tradeoff |
| `large-v2` | ~9% | Previous default |
| **`large-v3`** | **~6-8%** | **Recommended default** |

Always use `large-v3` unless RAM-constrained. The gains over `large-v2` for PT-BR specifically are substantial — noticeably better on idiomatic BR speech, informal register, and Brazilian proper nouns.

## 2. Forced alignment model selection

WhisperX uses wav2vec2 for word-level timestamps. Default for `pt`:

```
jonatasgrosman/wav2vec2-large-xlsr-53-portuguese
```

This model is trained on a mix of PT-PT and PT-BR but leans PT-PT. For pure PT-BR audio you can optionally swap to a BR-trained model. Edit `scripts/transcribe_diarize.py` around the `whisperx.load_align_model` call:

```python
# For PT-BR specifically:
align_model, align_metadata = whisperx.load_align_model(
    language_code="pt",
    device=device,
    model_name="Edresson/wav2vec2-large-xlsr-coraa-portuguese",  # BR
)
```

Other options worth testing:
- `lgris/wav2vec2-large-xlsr-open-brazilian-portuguese-v2` — CORAA + other BR datasets
- `facebook/wav2vec2-large-xlsr-53` — multilingual base (less accurate but always available)

## 3. Initial prompt trick

If your audio has specific proper nouns, acronyms or jargon (company names, technical vocabulary, legal terms), seed the first decoding step with them:

```bash
python scripts/transcribe_diarize.py \
    --input audio.m4a \
    --initial-prompt "Euronext, TPRM, DORA, NIS2, pyannote, WhisperX, Anthropic, Claude."
```

Keep the prompt short (< 200 chars). Include the exact casing/spelling you want. Whisper biases toward vocabulary it just "heard".

Examples for your use cases:

- Legal case (processo): `"Patrícia Santos, José Carlos Cabeço, Ana Luiza, Rafael, Nelas, Art. 152º CP, Lei 112/2009."`
- Henry Borel analysis: `"Henry Borel Medeiros, Dr. Jairinho, Monique Medeiros, laceração hepática, Instituto Médico Legal, rigor mortis."`
- TPRM calls: `"Euronext, DORA Article 28, OneTrust, TPSRCA, ENX-001, vendor risk assessment."`

## 4. Handling accented characters

Whisper sometimes outputs characters without diacritics ("nao" instead of "não"). The `normalize_pt_br.py` script fixes the most common cases. For comprehensive cleanup, run through a PT-BR grammar checker (e.g., `languagetool` local server).

## 5. Regional variation

Whisper large-v3 handles major BR regional accents well, but performance can dip for:

- Strong Nordeste / Pernambuco accents — consider the CORAA-trained alignment model
- Rural Minas Gerais / Goiás — same
- Heavy code-switching (PT + English tech terms) — consider transcribing twice: once with `--language pt`, once with `--language en` auto-detect, then manually reconcile

## 6. Overlapping speech

Diarization struggles with heavy overlap. For interview/debate-style audio where speakers cut each other:

```bash
python scripts/transcribe_diarize.py \
    --input audio.m4a \
    --min-speakers 2 --max-speakers 3 \
    --compute-type float32  # more stable alignment
```

Plan to manually review and fix the overlap regions. The JSON output flags word-level speaker, so you can spot contested words programmatically (adjacent words with different speakers within < 0.1s).

## 7. Numeric formatting

Whisper writes numbers inconsistently — sometimes "vinte e cinco", sometimes "25". For legal/audit use (where consistency matters), run:

```bash
python scripts/normalize_pt_br.py --input transcript.json --numeric
```

Or use the `initial-prompt` to bias toward one style: `"Use numerais em algarismos, não por extenso."`

## 8. Speech disfluencies

Whisper silently strips most "hum", "eh", "né". This is usually desirable but for forensic / testimonial work you may want them preserved. There's no flag for this — the workaround is to use the `raw` output from the underlying faster-whisper via a custom ASR options dict. If you need this, open an issue and we'll add a `--preserve-disfluencies` flag.
