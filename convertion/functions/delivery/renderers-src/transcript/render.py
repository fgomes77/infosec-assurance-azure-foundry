#!/usr/bin/env python3
"""Diarized transcript renderer (template `transcript`).

Usage: render.py <data.json> <outdir>        # writes transcript.{md,html,docx}

Renders the output of the two transcription paths this platform has — Azure
AI Speech batch transcription with diarization (workflows/speech-transcription.json,
the EU-resident replacement for the local WhisperX pipeline) and any
whisperx-transcribe-diarize JSON kept from before — into the three shapes a
transcript is actually consumed as: Markdown for the agent that summarises it,
HTML for reading in the browser, DOCX for the record in
`Reports/<Supplier>/<Service>/`.

Layout and timestamp format follow the byte-verified
claude-account-export/skills/whisperx-transcribe-diarize/scripts/format_transcript.py
(HH:MM:SS, one block per turn, speaker legend); the palette does NOT — a
Euronext deliverable uses the house style of templates/enx-theme.json
(Verdana, teal RGB(0,141,127), classification footer) per
agents/document_agents_addendum.md §"Delivery binding". The original script
stays the reference for the turn model and is never edited.

Accepted input shapes (whichever the caller has — all normalised to `turns`):

  A. WhisperX / format_transcript.py
     {"source","duration_seconds","language","model","compute_type",
      "diarized","speakers":[...],
      "turns":[{"speaker","start","end","text"}]}
  B. Azure AI Speech v3.2 batch result (as fetched by Get_transcript_json)
     {"duration"|"durationInTicks", "recognizedPhrases":[
        {"speaker":1,"offset":"PT12.3S"|"offsetInTicks":123000000,
         "duration"|"durationInTicks", "nBest":[{"display","confidence"}]}],
      "combinedRecognizedPhrases":[{"display": "..."}]}
  C. Already-normalised segments: {"segments":[{speaker,start,end,text}]}

Envelope fields (all optional, house style applied when absent):
  title, supplier, service, recordingDate ("YYYY-MM-DD"), classification,
  locale, engine, speakerNames {"Speaker 1": "Assurance lead", ...},
  participants [str], summary [str], actions [{action,owner,due?}],
  sources [str], notes [str]

`speakerNames` is the governed equivalent of the skill's
`scripts/relabel_speakers.py`: mapping a diarization label to a real person is
an assertion, so it is supplied in the approved contract rather than guessed
here. Nothing in this renderer invents, summarises or corrects speech — the
text of every turn is copied verbatim (the skill's `normalize_pt_br.py`
normalisation, if wanted, happens upstream and is recorded in `notes`).
"""

from __future__ import annotations

import json
import re
import sys
from datetime import date, timedelta
from html import escape
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, RGBColor

# House tokens — templates/enx-theme.json (palette.primary / office.*).
TEAL_HEX = "008D7F"
TEAL = RGBColor(0x00, 0x8D, 0x7F)
HEADER_FROM, HEADER_TO = "#003530", "#005048"
FONT = "Verdana"
SPEAKER_COLOURS = ["#008D7F", "#00B5A3", "#5ce0d2", "#e0b23c", "#e06c3c",
                   "#3cb371", "#8fa3a1", "#d64545", "#6f8fb0", "#b07fbf"]
TICKS_PER_SECOND = 10_000_000
_ISO_DUR = re.compile(r"^P(?:(\d+)D)?T(?:(\d+)H)?(?:(\d+)M)?(?:([\d.]+)S)?$", re.I)


# ------------------------------------------------------------------ helpers
def fmt_ts(seconds: float) -> str:
    """HH:MM:SS — identical to format_transcript.fmt_ts."""
    total = int(timedelta(seconds=max(float(seconds or 0), 0.0)).total_seconds())
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def to_seconds(value) -> float:
    """Accept seconds (number), ISO-8601 duration ('PT1M2.3S') or ticks."""
    if value is None or value == "":
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    m = _ISO_DUR.match(str(value).strip())
    if m:
        d, h, mi, sec = (float(g or 0) for g in m.groups())
        return d * 86400 + h * 3600 + mi * 60 + sec
    try:
        return float(value)
    except ValueError:
        return 0.0


def speaker_label(raw, names: dict) -> str:
    """Speech returns an int speaker id, WhisperX a 'SPEAKER_00' label."""
    if raw is None or raw == "":
        label = "UNKNOWN"
    elif isinstance(raw, int) or str(raw).isdigit():
        label = f"Speaker {int(raw)}"
    else:
        label = str(raw)
    return names.get(label, names.get(str(raw), label))


def normalise_turns(data: dict) -> list[dict]:
    """Every accepted input shape -> [{speaker, start, end, text, confidence}]."""
    names = data.get("speakerNames") or {}
    raw = data.get("turns") or data.get("segments")
    turns: list[dict] = []
    if raw:
        for t in raw:
            text = str(t.get("text", "")).strip()
            if not text:
                continue
            start = to_seconds(t.get("start", t.get("offset")))
            end = to_seconds(t.get("end", start + to_seconds(t.get("duration"))))
            turns.append({"speaker": speaker_label(t.get("speaker"), names),
                          "start": start, "end": max(end, start),
                          "text": text, "confidence": t.get("confidence")})
        return turns

    for p in data.get("recognizedPhrases") or []:
        best = (p.get("nBest") or [{}])[0]
        text = str(best.get("display") or best.get("lexical") or "").strip()
        if not text:
            continue
        start = to_seconds(p.get("offset")) or (p.get("offsetInTicks", 0) or 0) / TICKS_PER_SECOND
        dur = to_seconds(p.get("duration")) or (p.get("durationInTicks", 0) or 0) / TICKS_PER_SECOND
        turns.append({"speaker": speaker_label(p.get("speaker"), names),
                      "start": start, "end": start + dur, "text": text,
                      "confidence": best.get("confidence")})
    if turns:
        return turns

    # No diarization at all: keep the combined text as one undiarized turn
    # rather than silently producing an empty transcript.
    for c in data.get("combinedRecognizedPhrases") or []:
        text = str(c.get("display") or c.get("lexical") or "").strip()
        if text:
            turns.append({"speaker": "UNKNOWN", "start": 0.0,
                          "end": to_seconds(data.get("duration")), "text": text,
                          "confidence": None})
    return turns


def _default_title(data: dict) -> str:
    """Name the deliverable after what it is about: Supplier / Service when
    the contract carries them (the naming convention of
    Reports/<Supplier>/<Service>/), else the source recording."""
    sup, svc = data.get("supplier", ""), data.get("service", "")
    if sup or svc:
        return f"Transcript — {sup}{' / ' if sup and svc else ''}{svc}"
    return f"Transcript — {Path(str(data.get('source', ''))).name or 'recording'}"


def meta_of(data: dict, turns: list[dict]) -> dict:
    names = data.get("speakerNames") or {}
    # Declared speakers go through the same relabelling as the turns, or the
    # legend colours would not match the blocks they label.
    declared = [speaker_label(s, names) for s in (data.get("speakers") or [])]
    seen = sorted({t["speaker"] for t in turns})
    speakers = [s for s in declared if s in seen] or seen
    confs = [t["confidence"] for t in turns if isinstance(t.get("confidence"), (int, float))]
    duration = to_seconds(data.get("duration_seconds", data.get("duration")))
    return {
        "title": data.get("title") or _default_title(data),
        "supplier": data.get("supplier", ""),
        "service": data.get("service", ""),
        "date": data.get("recordingDate") or date.today().isoformat(),
        "classification": data.get("classification", "Euronext Internal"),
        "locale": data.get("locale") or data.get("language") or "unknown",
        "engine": data.get("engine") or (f"WhisperX {data.get('model')}" if data.get("model")
                                         else "Azure AI Speech (batch, diarization, EU)"),
        "duration": duration or (max((t["end"] for t in turns), default=0.0)),
        "diarized": bool(data.get("diarized", len(speakers) > 1)),
        "speakers": speakers,
        "turns": len(turns),
        "confidence": round(sum(confs) / len(confs), 4) if confs else None,
    }


# -------------------------------------------------------------------- views
def to_markdown(m: dict, turns: list[dict], data: dict) -> str:
    out = [f"# {m['title']}", ""]
    if m["supplier"] or m["service"]:
        out.append(f"**Supplier / Service:** {m['supplier']} — {m['service']}")
    out += [f"- **Date:** {m['date']}",
            f"- **Duration:** {fmt_ts(m['duration'])}",
            f"- **Locale:** {m['locale']}",
            f"- **Engine:** {m['engine']}",
            f"- **Diarized:** {'yes' if m['diarized'] else 'no'}",
            f"- **Speakers:** {', '.join(m['speakers']) or 'n/a'}",
            f"- **Classification:** {m['classification']}"]
    if m["confidence"] is not None:
        out.append(f"- **Mean recognition confidence:** {m['confidence']}")
    if data.get("participants"):
        out.append(f"- **Participants:** {', '.join(data['participants'])}")
    out += ["", "---", ""]
    if data.get("summary"):
        out += ["## Summary", ""] + [f"- {s}" for s in data["summary"]] + [""]
    out += ["## Transcript", ""]
    for t in turns:
        out += [f"### {t['speaker']} — [{fmt_ts(t['start'])} → {fmt_ts(t['end'])}]", "", t["text"], ""]
    if data.get("actions"):
        out += ["## Actions", "", "| Action | Owner | Due |", "|---|---|---|"]
        out += [f"| {a.get('action','')} | {a.get('owner','')} | {a.get('due','')} |"
                for a in data["actions"]] + [""]
    if data.get("notes"):
        out += ["## Notes", ""] + [f"- {n}" for n in data["notes"]] + [""]
    out += ["## Sources", ""]
    out += [f"- {s}" for s in (data.get("sources") or [f"Recording transcribed by {m['engine']}"])]
    out += ["", f"_{m['classification']} — verified and human-approved before storage._"]
    return "\n".join(out)


def to_html(m: dict, turns: list[dict], data: dict) -> str:
    colours = {sp: SPEAKER_COLOURS[i % len(SPEAKER_COLOURS)] for i, sp in enumerate(m["speakers"])}
    legend = "".join(f'<span class="chip" style="background:{colours[sp]}">{escape(sp)}</span>'
                     for sp in m["speakers"])
    rows = "".join(
        f'<div class="turn"><div class="head" style="border-left:4px solid {colours.get(t["speaker"], "#8fa3a1")}">'
        f'<span class="sp" style="color:{colours.get(t["speaker"], "#8fa3a1")}">{escape(t["speaker"])}</span>'
        f'<span class="ts">[{fmt_ts(t["start"])} &rarr; {fmt_ts(t["end"])}]</span></div>'
        f'<div class="body">{escape(t["text"])}</div></div>'
        for t in turns)
    meta_rows = "".join(f"<dt>{escape(k)}</dt><dd>{escape(str(v))}</dd>" for k, v in [
        ("Supplier", m["supplier"] or "—"), ("Service", m["service"] or "—"),
        ("Date", m["date"]), ("Duration", fmt_ts(m["duration"])),
        ("Locale", m["locale"]), ("Engine", m["engine"]),
        ("Speakers", str(len(m["speakers"]))), ("Turns", str(m["turns"])),
        ("Mean confidence", "n/a" if m["confidence"] is None else str(m["confidence"]))])
    summary = ("<h2>Summary</h2><ul>" + "".join(f"<li>{escape(s)}</li>" for s in data["summary"]) + "</ul>"
               if data.get("summary") else "")
    actions = ("<h2>Actions</h2><table><tr><th>Action</th><th>Owner</th><th>Due</th></tr>"
               + "".join(f"<tr><td>{escape(str(a.get('action','')))}</td>"
                         f"<td>{escape(str(a.get('owner','')))}</td>"
                         f"<td>{escape(str(a.get('due','')))}</td></tr>" for a in data["actions"])
               + "</table>") if data.get("actions") else ""
    sources = "".join(f"<li>{escape(s)}</li>" for s in
                      (data.get("sources") or [f"Recording transcribed by {m['engine']}"]))
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(m['title'])}</title>
<style>
body{{font-family:{FONT}, Geneva, 'DejaVu Sans', sans-serif;font-size:13px;line-height:1.45;
 max-width:980px;margin:0 auto;padding:0 16px 48px;color:#12211f;background:#fff}}
header{{background:linear-gradient(135deg,{HEADER_FROM},{HEADER_TO});color:#fff;
 padding:20px;border-radius:10px;margin:16px 0}}
h1{{margin:0;font-size:20px}}
h2{{color:#{TEAL_HEX};font-size:16px;margin-top:28px}}
dl{{display:grid;grid-template-columns:auto 1fr;gap:4px 16px;margin:12px 0}}
dt{{font-weight:bold;color:#003530}}
.chip{{display:inline-block;padding:4px 10px;border-radius:12px;color:#fff;margin:2px;font-size:11px}}
.turn{{margin:14px 0}}
.head{{padding-left:8px}}
.sp{{font-weight:bold}}
.ts{{color:#5a6b69;margin-left:8px;font-size:11px}}
.body{{margin:4px 0 0 12px}}
table{{border-collapse:collapse;width:100%;margin:8px 0}}
th,td{{border:1px solid #d5e2e0;padding:6px 8px;text-align:left}}
th{{background:#00463f;color:#fff}}
footer{{margin-top:32px;border-top:1px solid #d5e2e0;padding-top:8px;font-size:11px;color:#5a6b69}}
</style></head><body>
<header><h1>{escape(m['title'])}</h1>
<div>{escape(m['classification'])}</div></header>
<dl>{meta_rows}</dl>
<div>{legend}</div>
{summary}
<h2>Transcript</h2>
{rows}
{actions}
<h2>Sources</h2><ul>{sources}</ul>
<footer>Euronext — Information Security Assurance — {escape(m['classification'])}.
Generated by the InfoSec Assurance platform; verified and human-approved before storage.
Speech content is reproduced verbatim.</footer>
</body></html>"""


def to_docx(m: dict, turns: list[dict], data: dict, path: Path) -> None:
    doc = Document()
    normal = doc.styles["Normal"].font
    normal.name, normal.size = FONT, Pt(10)

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = title.add_run(m["title"])
    r.font.size, r.font.bold, r.font.color.rgb = Pt(18), True, TEAL
    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub.add_run(f"{m['supplier']} — {m['service']}  |  {m['date']}  |  {m['classification']}")

    def h(text, level=1):
        p = doc.add_heading(text, level=level)
        for run in p.runs:
            run.font.color.rgb = TEAL

    h("Recording")
    t = doc.add_table(rows=0, cols=2)
    t.style = "Light Grid Accent 1"
    for k, v in [("Duration", fmt_ts(m["duration"])), ("Locale", m["locale"]),
                 ("Engine", m["engine"]), ("Diarized", "yes" if m["diarized"] else "no"),
                 ("Speakers", ", ".join(m["speakers"]) or "n/a"), ("Turns", str(m["turns"])),
                 ("Mean confidence", "n/a" if m["confidence"] is None else str(m["confidence"]))]:
        cells = t.add_row().cells
        cells[0].text, cells[1].text = k, str(v)
        for run in cells[0].paragraphs[0].runs:
            run.font.bold = True

    if data.get("summary"):
        h("Summary")
        for s in data["summary"]:
            doc.add_paragraph(str(s), style="List Bullet")

    h("Transcript")
    for turn in turns:
        p = doc.add_paragraph()
        lead = p.add_run(f"{turn['speaker']}  [{fmt_ts(turn['start'])} → {fmt_ts(turn['end'])}]")
        lead.font.bold, lead.font.size, lead.font.color.rgb = True, Pt(9), TEAL
        body = doc.add_paragraph(turn["text"])
        body.paragraph_format.left_indent = Pt(18)

    if data.get("actions"):
        h("Actions")
        at = doc.add_table(rows=1, cols=3)
        at.style = "Light Grid Accent 1"
        for i, c in enumerate(("Action", "Owner", "Due")):
            at.rows[0].cells[i].text = c
            for run in at.rows[0].cells[i].paragraphs[0].runs:
                run.font.bold = True
        for a in data["actions"]:
            cells = at.add_row().cells
            cells[0].text = str(a.get("action", ""))
            cells[1].text = str(a.get("owner", ""))
            cells[2].text = str(a.get("due", ""))

    if data.get("notes"):
        h("Notes")
        for n in data["notes"]:
            doc.add_paragraph(str(n), style="List Bullet")

    h("Sources")
    for s in (data.get("sources") or [f"Recording transcribed by {m['engine']}"]):
        doc.add_paragraph(str(s), style="List Bullet")

    foot = doc.add_paragraph(
        f"Euronext — Information Security Assurance — {m['classification']}. "
        "Generated by the InfoSec Assurance platform; verified and human-approved "
        "before storage. Speech is reproduced verbatim; speaker names come from "
        "the approved contract, not from the transcription engine.")
    foot.runs[0].font.size = Pt(8)
    doc.save(str(path))


def main() -> int:
    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    outdir = Path(sys.argv[2])
    # argv[2] may be a file path when a single format was requested: the
    # Function passes {outdir} (manifest "outputs": "dir"), but stay tolerant.
    if outdir.suffix:
        outdir = outdir.parent
    outdir.mkdir(parents=True, exist_ok=True)

    turns = normalise_turns(data)
    if not turns:
        print("ERROR: no transcript turns found (turns / segments / "
              "recognizedPhrases / combinedRecognizedPhrases all empty)", file=sys.stderr)
        return 2
    m = meta_of(data, turns)

    (outdir / "transcript.md").write_text(to_markdown(m, turns, data), encoding="utf-8")
    (outdir / "transcript.html").write_text(to_html(m, turns, data), encoding="utf-8")
    to_docx(m, turns, data, outdir / "transcript.docx")
    print(f"PASS - {len(turns)} turn(s), {len(m['speakers'])} speaker(s), "
          f"{fmt_ts(m['duration'])} rendered to md/html/docx")
    return 0


if __name__ == "__main__":
    sys.exit(main())
