# PPTX Template Specification — G.CISO TPRM Governance Meeting Report

## Overview

The PPTX report mirrors the HTML CISO Executive Summary by embedding rendered HTML
sections as high-resolution PNG images into branded Euronext slides. This creates a
board-ready presentation for the Group CISO Governance Meeting.

---

## Slide Structure (8 slides)

| Slide | Title | Content | Source |
|-------|-------|---------|--------|
| 1 | Title Slide | "Current TP Risks above risk appetite" | Static — Euronext branded |
| 2 | Assessment Summary | Vendor table + key findings bullets | Generated from PDF data |
| 3 | TPRM Executive Summary | KPI row + Spider + Profile + Domain bars | HTML section screenshot |
| 4 | Open Risks | Inherent risk rationale + Risks table | HTML section screenshot |
| 5 | Mitigation Controls | Euronext controls register + Perimeter matrix | HTML section screenshot |
| 6 | TPRM Summary (cont.) | Critical Findings + DORA & Actions | HTML section screenshot |
| 7 | Closing | Euronext logo | Static |
| 8 | Disclaimer | Legal text | Static |

---

## Layout Specifications

### Global
- **Layout:** LAYOUT_WIDE (13.33" × 7.5")
- **Fonts:** Arial (titles), Calibri (body)
- **Brand colours:** Teal #007D71, Dark teal #003530, White, Black #0F172A

### Slide 1 — Title
- Full dark teal background (#003530)
- Title: 40pt Arial Bold White, positioned x:0.8 y:2.5
- EURONEXT footer: 16pt Arial Bold White at y:6.2

### Slides 2–6 — Content Slides
- **Teal accent bar:** 0.08" wide × 0.95" tall rectangle at (0, 0.05), fill #007D71
- **Title:** 28pt Arial Bold, x:0.3 y:0.15
- **Footer:** EURONEXT logo (14pt teal), subtitle (8pt gray centre), PRIVATE label (8pt gold), slide number (9pt teal right)
- **Image area:** x:0.15 y:1.0, width 13.0" (fills most of slide)

### Slide 2 — Assessment Table
- 5-column table: Vendor/Service, Service Description, Company, Infosec Risk Score, Service Criticality
- Header row: fill #007D71, white bold text
- Bullet points below table: key findings summary (3 bullets)

### Slides 3–6 — HTML Section Screenshots
- Generated using Playwright with viewport 1400px wide
- Section clipping regions (from full-page render):
  - S3 (Executive Summary): y:0 → h:820px — KPI row, spider, profile, domain bars
  - S4 (Open Risks): y:820 → h:550px — Inherent risk rationale, risks table
  - S5 (Mitigation Controls): y:1370 → h:700px — Euronext controls, perimeter matrix
  - S6 (Findings/Actions): y:2070 → h:520px — Critical findings, DORA/actions
- Embedded as PNG images with `sizing: { type: "contain" }`

### Slide 7 — Closing
- White background
- Teal footer bar: full width at y:6.8
- EURONEXT text: 36pt Arial Bold teal, centred

### Slide 8 — Disclaimer
- Standard legal disclaimer text (8pt Calibri gray)
- EURONEXT footer

---

## Generation Workflow

### Step 1: Render HTML sections
```python
python3 scripts/render_sections.py
```
Reads the HTML report, renders full page in Playwright (viewport 1400×3000),
clips 4 section images to `/home/claude/pptx_sections/`.

### Step 2: Generate PPTX
```bash
node scripts/generate_pptx_template.js
```
Uses pptxgenjs to build 8-slide PPTX embedding the section PNGs.
Requires: `npm install pptxgenjs`

### Step 3: QA
```bash
python scripts/office/soffice.py --headless --convert-to pdf output.pptx
pdftoppm -jpeg -r 150 output.pdf slide
```
Visual inspection of all slides.

---

## Section Clipping Notes

The clipping coordinates depend on HTML report height, which varies by vendor
(more risks = taller page). The render script uses these defaults:

```python
SECTIONS = [
    {"name": "s3_exec_summary",      "clip": {"x": 0, "y": 0,    "width": 1340, "height": 820}},
    {"name": "s4_open_risks",        "clip": {"x": 0, "y": 820,  "width": 1340, "height": 550}},
    {"name": "s5_controls_perimeter","clip": {"x": 0, "y": 1370, "width": 1340, "height": 700}},
    {"name": "s6_findings_actions",  "clip": {"x": 0, "y": 2070, "width": 1340, "height": 520}},
]
```

For vendors with many risks/controls, adjust y-offsets and heights accordingly.
The render script should be tuned per-vendor to ensure clean section breaks
(no clipped text at boundaries).
