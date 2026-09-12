#!/usr/bin/env python3
"""Shared chart renderer (matplotlib, headless) — PNG/SVG for decks, DOCX
reports and dossier infographics rendered inside the EU boundary.

Usage: charts.py <data.json> <out.png|out.svg>

data.json: {"chart": "spider"|"gauge"|"bar"|"heatmap"|"exposure", ...}
  spider:   {"labels": [5 domains]?, "values": [0-10 x5], "title": str?, "max": 10?}
            (same 5-axis geometry/colour bands as the ciso-reporting spider)
  gauge:    {"value": 6.3, "label": "Residual risk", "max": 10}
  bar:      {"labels": [...], "values": [...], "title": str?, "band": true?}
  heatmap:  {"rows": [...], "cols": [...], "values": [[...]], "title": str?}
  exposure: {"service": str, "internal": [{"node","risk","note"?}], "external": [...]}
            (the Global CISO exposure diagram - internal | service | external)
Palette and thresholds come from palette.json (governance/RISK_THRESHOLDS.md).
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch, Wedge  # noqa: E402

PAL = json.loads((Path(__file__).resolve().parent / "palette.json").read_text(encoding="utf-8"))
B, R = PAL["brand"], PAL["risk_bands"]
plt.rcParams["font.family"] = [PAL["font"], PAL["font_fallback"], "sans-serif"]


def band(v: float, slide: bool = False) -> str:
    if slide:
        return R["high"]["fill"] if v >= PAL["slide_bands"]["red"] else R["medium"]["fill"] if v >= PAL["slide_bands"]["amber"] else R["low"]["fill"]
    return R["high"]["fill"] if v >= R["high"]["min"] else R["medium"]["fill"] if v >= R["medium"]["min"] else R["low"]["fill"]


def spider(d, out):
    labels = d.get("labels") or PAL["domains_5"]
    vals = [float(v) for v in d["values"]]
    mx = float(d.get("max", 10))
    n = len(labels)
    ang = [2 * math.pi * i / n for i in range(n)]
    fig = plt.figure(figsize=(6, 6), dpi=200)
    ax = fig.add_subplot(111, polar=True)
    ax.set_theta_offset(math.pi / 2)
    ax.set_theta_direction(-1)
    for lvl, col in ((R["low"], R["low"]["pale"]), (R["medium"], R["medium"]["pale"]), (R["high"], R["high"]["pale"])):
        top = mx if lvl is R["high"] else (R["medium"]["min"] if lvl is R["low"] else R["high"]["min"])
        ax.fill_between(ang + ang[:1], lvl["min"], top, color=col, alpha=0.55, zorder=1)
    ax.plot(ang + ang[:1], vals + vals[:1], color=B["teal"], linewidth=2.2, zorder=5)
    ax.fill(ang + ang[:1], vals + vals[:1], color=B["teal"], alpha=0.25, zorder=4)
    for a, v in zip(ang, vals):
        ax.scatter([a], [v], s=45, color=band(v), edgecolor="white", zorder=6)
        ax.annotate(f"{v:.1f}", (a, v), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=8, color=B["ink"])
    ax.set_xticks(ang)
    ax.set_xticklabels(labels, fontsize=9, color=B["ink"])
    ax.set_ylim(0, mx)
    ax.set_yticks([R["medium"]["min"], R["high"]["min"], mx])
    ax.set_yticklabels([f"{R['medium']['min']:.0f}", f"{R['high']['min']:.0f}", f"{mx:.0f}"], fontsize=7, color=B["grey"])
    ax.grid(color=B["greyLight"])
    if d.get("title"):
        ax.set_title(d["title"], color=B["teal"], fontsize=12, pad=18)
    fig.savefig(out, bbox_inches="tight", facecolor="white")


def gauge(d, out):
    v, mx = float(d["value"]), float(d.get("max", 10))
    fig, ax = plt.subplots(figsize=(4, 2.4), dpi=200)
    ax.set_aspect("equal")
    ax.axis("off")
    segs = [(0, R["medium"]["min"], R["low"]["fill"]), (R["medium"]["min"], R["high"]["min"], R["medium"]["fill"]), (R["high"]["min"], mx, R["high"]["fill"])]
    for lo, hi, col in segs:
        ax.add_patch(Wedge((0, 0), 1.0, 180 - hi / mx * 180, 180 - lo / mx * 180, width=0.28, color=col, alpha=0.35))
    ax.add_patch(Wedge((0, 0), 1.0, 180 - v / mx * 180, 180, width=0.28, color=band(v)))
    ax.text(0, 0.05, f"{v:.1f}", ha="center", va="center", fontsize=22, fontweight="bold", color=band(v))
    ax.text(0, -0.25, d.get("label", ""), ha="center", va="center", fontsize=9, color=B["grey"])
    ax.set_xlim(-1.1, 1.1)
    ax.set_ylim(-0.4, 1.1)
    fig.savefig(out, bbox_inches="tight", facecolor="white")


def bar(d, out):
    labels, vals = d["labels"], [float(v) for v in d["values"]]
    fig, ax = plt.subplots(figsize=(max(4, 0.9 * len(labels) + 1), 3.2), dpi=200)
    cols = [band(v) for v in vals] if d.get("band") else [PAL["categorical"][i % len(PAL["categorical"])] for i in range(len(vals))]
    ax.bar(labels, vals, color=cols, width=0.62)
    for i, v in enumerate(vals):
        ax.text(i, v + 0.1, f"{v:.1f}", ha="center", fontsize=8, color=B["ink"])
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.spines["left"].set_color(B["greyLight"]); ax.spines["bottom"].set_color(B["greyLight"])
    ax.tick_params(labelsize=8, colors=B["ink"])
    ax.set_ylim(0, float(d.get("max", max(vals + [1]) * 1.15)))
    if d.get("title"):
        ax.set_title(d["title"], color=B["teal"], fontsize=11, loc="left")
    fig.savefig(out, bbox_inches="tight", facecolor="white")


def heatmap(d, out):
    rows, cols, vals = d["rows"], d["cols"], d["values"]
    fig, ax = plt.subplots(figsize=(0.9 * len(cols) + 2, 0.5 * len(rows) + 1.2), dpi=200)
    seq = PAL["sequential_teal"]
    mx = max(max(r) for r in vals) or 1
    for i, r in enumerate(vals):
        for j, v in enumerate(r):
            ax.add_patch(FancyBboxPatch((j, len(rows) - 1 - i), 0.96, 0.96, boxstyle="round,pad=0,rounding_size=0.08",
                                        color=seq[min(len(seq) - 1, int(v / mx * (len(seq) - 1)))]))
            ax.text(j + 0.48, len(rows) - 1 - i + 0.48, f"{v:g}", ha="center", va="center", fontsize=8,
                    color="white" if v / mx > 0.55 else B["ink"])
    ax.set_xlim(0, len(cols)); ax.set_ylim(0, len(rows))
    ax.set_xticks([j + 0.5 for j in range(len(cols))]); ax.set_xticklabels(cols, fontsize=8, rotation=30, ha="right")
    ax.set_yticks([len(rows) - 1 - i + 0.5 for i in range(len(rows))]); ax.set_yticklabels(rows, fontsize=8)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0)
    if d.get("title"):
        ax.set_title(d["title"], color=B["teal"], fontsize=11, loc="left")
    fig.savefig(out, bbox_inches="tight", facecolor="white")


def exposure(d, out):
    """Internal surface | service | external surface with drawn connectors
    (the ciso-global slide-7 diagram; embedded by generate_slide.js addImage)."""
    fig, ax = plt.subplots(figsize=(13, 6.2), dpi=200)
    ax.axis("off"); ax.set_xlim(0, 13); ax.set_ylim(0, 6.2)
    ax.text(0.4, 5.9, "INTERNAL SURFACE", fontsize=11, fontweight="bold", color=B["grey"], va="top")
    ax.text(12.6, 5.9, "EXTERNAL SURFACE", fontsize=11, fontweight="bold", color=B["grey"], va="top", ha="right")
    cx, cy, cw, ch = 5.45, 2.5, 2.1, 1.2
    ax.add_patch(FancyBboxPatch((cx, cy), cw, ch, boxstyle="round,pad=0.02,rounding_size=0.15", color=B["teal"]))
    ax.text(cx + cw / 2, cy + ch / 2, d.get("service", ""), ha="center", va="center", fontsize=10, fontweight="bold", color="white", wrap=True)
    band_of = {"High": R["high"]["fill"], "Medium": R["medium"]["fill"], "Low": R["low"]["fill"]}

    def draw(nodes, x_box, x_from, x_to):
        for i, n in enumerate(nodes[:6]):
            y = 5.0 - i * 0.85
            col = band_of.get(str(n.get("risk", "")).title(), B["grey"])
            ax.plot([x_from, x_to], [y + 0.3, cy + ch / 2], color="#AAAAAA", linewidth=1, zorder=1)
            ax.add_patch(FancyBboxPatch((x_box, y), 4.4, 0.6, boxstyle="round,pad=0.02,rounding_size=0.1",
                                        facecolor="white", edgecolor=col, linewidth=2, zorder=2))
            ax.text(x_box + 0.12, y + 0.3, f"{n.get('node', '')}{' — ' + n['note'] if n.get('note') else ''}",
                    va="center", fontsize=8.5, color=B["ink"], zorder=3)
            ax.add_patch(plt.Circle((x_box + 4.15, y + 0.3), 0.12, color=col, zorder=3))
    draw(d.get("internal", []), 0.4, 4.8, cx)
    draw(d.get("external", []), 8.2, cx + cw, 8.2)
    ax.text(0.4, 0.15, "● red = High   ● amber = Medium   ● green = Low  (bands: High ≥7.0, Medium ≥4.0)", fontsize=8.5, color=B["grey"])
    fig.savefig(out, bbox_inches="tight", facecolor="white")


CHARTS = {"spider": spider, "gauge": gauge, "bar": bar, "heatmap": heatmap, "exposure": exposure}

if __name__ == "__main__":
    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    kind = data.get("chart", "spider")
    if kind not in CHARTS:
        sys.exit(f"unknown chart {kind}; one of {sorted(CHARTS)}")
    CHARTS[kind](data, sys.argv[2])
    print("OK", sys.argv[2])
