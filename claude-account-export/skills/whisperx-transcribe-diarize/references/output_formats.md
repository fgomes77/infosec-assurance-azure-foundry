# Output Formats

The main script produces up to four outputs per run, selected via `--formats`.

## TXT (default)

Human-readable, grouped by speaker turn:

```
[00:00:03 → 00:00:14] SPEAKER_00:
    Bom dia, muito obrigado por estarem aqui hoje. Vamos começar com a revisão do trimestre.

[00:00:14 → 00:00:22] SPEAKER_01:
    Bom dia. Antes de começarmos, posso fazer uma pergunta rápida sobre a agenda?
```

Use for: quick review, sharing with non-technical stakeholders, copy-paste into reports.

## SRT (SubRip)

Standard subtitle format, universally supported:

```
1
00:00:03,120 --> 00:00:06,440
[SPEAKER_00] Bom dia, muito obrigado por estarem aqui hoje.

2
00:00:06,440 --> 00:00:14,000
[SPEAKER_00] Vamos começar com a revisão do trimestre.
```

Use for: video editing (Premiere, DaVinci, Final Cut), YouTube/Vimeo upload, VLC playback.

## VTT (WebVTT)

HTML5-native subtitle format with voice tags:

```
WEBVTT

00:00:03.120 --> 00:00:06.440
<v SPEAKER_00>Bom dia, muito obrigado por estarem aqui hoje.
```

Use for: web players (`<track kind="subtitles">`), accessibility workflows.

## JSON (most complete)

Full structured output with segment-level and word-level data:

```json
{
  "source": "/Users/francisco/audio.m4a",
  "duration_seconds": 16380.5,
  "language": "pt",
  "model": "large-v3",
  "compute_type": "int8",
  "device": "cpu",
  "diarized": true,
  "aligned": true,
  "segments": [
    {
      "start": 3.12,
      "end": 6.44,
      "speaker": "SPEAKER_00",
      "text": "Bom dia, muito obrigado por estarem aqui hoje.",
      "words": [
        {"word": "Bom", "start": 3.12, "end": 3.32, "score": 0.98, "speaker": "SPEAKER_00"},
        {"word": "dia,", "start": 3.34, "end": 3.56, "score": 0.99, "speaker": "SPEAKER_00"}
      ]
    }
  ],
  "turns": [
    {"speaker": "SPEAKER_00", "start": 3.12, "end": 14.00, "text": "Bom dia... trimestre."}
  ],
  "speakers": ["SPEAKER_00", "SPEAKER_01"]
}
```

Use for: programmatic processing, feeding into other tools (LLM summarization, search indexing, analytics).

## Markdown (post-processed)

Generate with `format_transcript.py`:

```bash
python scripts/format_transcript.py --input transcript.json --format md
```

Produces a GitHub/Notion-friendly document with headers per turn.

## HTML dashboard (post-processed)

Teal-themed viewer matching your TPSRCA visual standard:

```bash
python scripts/format_transcript.py \
    --input transcript.json \
    --format html \
    --template assets/transcript_template.html
```

Features:
- Dark teal header (`#003530` → `#005048`) with Verdana
- Collapsible turn cards
- Color-coded speaker chips (WCAG AA compliant)
- Clickable timestamps (can sync with embedded audio player if you add one)
- Print-friendly CSS

## DOCX (requires python-docx)

Not included in the core pipeline but easy to add:

```python
from docx import Document
from docx.shared import Pt, RGBColor
import json

payload = json.load(open("transcript.json"))
doc = Document()

# Header
doc.add_heading(f"Transcript — {payload['source']}", level=1)
doc.add_paragraph(f"Duration: {payload['duration_seconds']/3600:.1f}h  |  Speakers: {len(payload['speakers'])}")

# Turns
for turn in payload["turns"]:
    p = doc.add_paragraph()
    p.add_run(f"[{turn['start']:.0f}s] {turn['speaker']}: ").bold = True
    p.add_run(turn["text"])

doc.save("transcript.docx")
```

Use for: legal delivery, signed/notarized documents, client-facing reports.

## Choosing a format

| Use case | Recommended |
|---|---|
| Review / share with peers | TXT |
| Edit video with subtitles | SRT |
| Embed in web page | VTT |
| Feed to LLM for summarization | JSON (just the `turns` array) |
| Formal client deliverable | DOCX or HTML |
| Legal evidence / forensic | JSON (most information) + DOCX (signed copy) |
| Search / analytics | JSON indexed into Elasticsearch/Meilisearch |
