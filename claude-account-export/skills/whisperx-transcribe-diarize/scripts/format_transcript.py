#!/usr/bin/env python3
"""
format_transcript.py — Convert transcribe_diarize JSON output to readable formats.

Usage:
  python scripts/format_transcript.py --input transcript.json --format md
  python scripts/format_transcript.py --input transcript.json --format html --template assets/transcript_template.html
"""

from __future__ import annotations

import argparse
import json
from datetime import timedelta
from pathlib import Path
from html import escape


def fmt_ts(seconds: float) -> str:
    td = timedelta(seconds=max(seconds, 0.0))
    total = int(td.total_seconds())
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def to_markdown(payload: dict) -> str:
    lines = [
        f"# Transcript — {Path(payload.get('source', '')).name}",
        "",
        f"- **Duration:** {fmt_ts(payload.get('duration_seconds', 0))}",
        f"- **Language:** {payload.get('language', 'unknown')}",
        f"- **Model:** {payload.get('model', '?')} ({payload.get('compute_type', '?')})",
        f"- **Diarized:** {'yes' if payload.get('diarized') else 'no'}",
        f"- **Speakers detected:** {', '.join(payload.get('speakers', [])) or 'n/a'}",
        "",
        "---",
        "",
    ]
    for turn in payload.get("turns", []):
        speaker = turn.get("speaker", "UNKNOWN")
        start = fmt_ts(turn["start"])
        end = fmt_ts(turn["end"])
        lines.append(f"### {speaker} — [{start} → {end}]")
        lines.append("")
        lines.append(turn["text"])
        lines.append("")
    return "\n".join(lines)


def to_text(payload: dict) -> str:
    lines = []
    for turn in payload.get("turns", []):
        lines.append(f"[{fmt_ts(turn['start'])} → {fmt_ts(turn['end'])}] {turn['speaker']}:")
        lines.append(f"    {turn['text']}")
        lines.append("")
    return "\n".join(lines)


def to_html(payload: dict, template_path: Path | None) -> str:
    palette = [
        "#00bfa5", "#ff9800", "#9c27b0", "#2196f3", "#e91e63",
        "#8bc34a", "#ff5722", "#607d8b", "#795548", "#3f51b5",
    ]
    speakers = payload.get("speakers", [])
    color_map = {sp: palette[i % len(palette)] for i, sp in enumerate(speakers)}

    legend_html = "".join(
        f'<span class="chip" style="background:{color_map[sp]}">{escape(sp)}</span>'
        for sp in speakers
    )

    turns_html_parts = []
    for turn in payload.get("turns", []):
        speaker = turn.get("speaker", "UNKNOWN")
        color = color_map.get(speaker, "#888")
        start = fmt_ts(turn["start"])
        end = fmt_ts(turn["end"])
        text = escape(turn["text"])
        turns_html_parts.append(
            f'<div class="turn">'
            f'  <div class="turn-head" style="border-left:4px solid {color}">'
            f'    <span class="sp" style="color:{color}">{escape(speaker)}</span>'
            f'    <span class="ts">[{start} → {end}]</span>'
            f'  </div>'
            f'  <div class="turn-body">{text}</div>'
            f'</div>'
        )
    turns_html = "\n".join(turns_html_parts)

    source_name = Path(payload.get("source", "")).name
    meta_html = (
        f"<dl>"
        f"<dt>Source</dt><dd>{escape(source_name)}</dd>"
        f"<dt>Duration</dt><dd>{fmt_ts(payload.get('duration_seconds', 0))}</dd>"
        f"<dt>Language</dt><dd>{escape(payload.get('language', '?'))}</dd>"
        f"<dt>Model</dt><dd>{escape(payload.get('model', '?'))} ({escape(payload.get('compute_type', '?'))})</dd>"
        f"<dt>Speakers</dt><dd>{len(speakers)}</dd>"
        f"</dl>"
    )

    if template_path and template_path.exists():
        tpl = template_path.read_text(encoding="utf-8")
        return (tpl
                .replace("{{TITLE}}", escape(source_name or "Transcript"))
                .replace("{{META}}", meta_html)
                .replace("{{LEGEND}}", legend_html)
                .replace("{{TURNS}}", turns_html))

    # Inline fallback
    return f"""<!DOCTYPE html><html lang="pt-BR"><head><meta charset="utf-8">
<title>Transcript — {escape(source_name)}</title>
<style>
body{{font-family:Verdana,sans-serif;max-width:900px;margin:2em auto;padding:0 1em;color:#222}}
header{{background:linear-gradient(135deg,#003530,#005048);color:#fff;padding:1.5em;border-radius:8px}}
h1{{margin:0;font-size:1.4em}}
dl{{display:grid;grid-template-columns:auto 1fr;gap:4px 12px;margin:1em 0}}
dt{{font-weight:bold;color:#003530}}
.chip{{display:inline-block;padding:4px 10px;border-radius:12px;color:#fff;margin:2px;font-size:.85em}}
.turn{{margin:1em 0}}
.turn-head{{padding:6px 10px;background:#f3f7f6}}
.sp{{font-weight:bold}}
.ts{{color:#666;margin-left:.8em;font-size:.85em}}
.turn-body{{padding:8px 14px;background:#fff;border:1px solid #e2ecea;border-top:none;line-height:1.6}}
</style></head><body>
<header><h1>{escape(source_name)}</h1></header>
{meta_html}
<div>{legend_html}</div>
{turns_html}
</body></html>"""


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--input", "-i", required=True, help="Input JSON produced by transcribe_diarize.py")
    p.add_argument("--output", "-o", help="Output path. Default: derived from input + format extension.")
    p.add_argument("--format", "-f", choices=["txt", "md", "html"], default="md")
    p.add_argument("--template", help="HTML template with {{TITLE}} {{META}} {{LEGEND}} {{TURNS}} placeholders.")
    args = p.parse_args()

    src = Path(args.input).expanduser().resolve()
    payload = json.loads(src.read_text(encoding="utf-8"))

    if args.format == "txt":
        content = to_text(payload)
        ext = ".txt"
    elif args.format == "md":
        content = to_markdown(payload)
        ext = ".md"
    else:
        tpl = Path(args.template).expanduser().resolve() if args.template else None
        content = to_html(payload, tpl)
        ext = ".html"

    out = Path(args.output) if args.output else src.with_suffix(ext)
    out.write_text(content, encoding="utf-8")
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
