# CISO Executive Summary — HTML Template Specification

## Canonical Reference

The canonical template is `assets/template.html` (Vermeg baseline). This document
specifies every component, dimension, colour rule, and layout constraint.

---

## 1. Design System

### 1.1 Typography

| Role | Font | Weight | Size |
|------|------|--------|------|
| Body text | IBM Plex Sans | 400 | 13px |
| Headers (h1) | IBM Plex Sans | 700 | 22px |
| Card titles | IBM Plex Sans | 700 | 13px |
| KPI values | IBM Plex Sans | 700 | 24px |
| Score badges | IBM Plex Mono | 700 | 11px |
| Risk IDs | IBM Plex Mono | 600 | — |
| Section labels | IBM Plex Sans | 700 | 10px uppercase |
| Table headers | IBM Plex Sans | 700 | 9px uppercase |
| Table body | IBM Plex Sans | 400 | 12px |

Font import: `https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap`

### 1.2 Colour System

#### Threshold Colours (mandatory — supersedes all other colour definitions)

| Variable | Hex | Usage |
|----------|-----|-------|
| `--high-red` | #DC2626 | Score > 12, HIGH classification |
| `--high-bg` | #FEE2E2 | Background for HIGH elements |
| `--medium-amber` | #D97706 | Score > 4 and ≤ 12, MEDIUM classification |
| `--medium-bg` | #FEF3C7 | Background for MEDIUM elements |
| `--low-teal` | #007D71 | Score ≤ 4, LOW classification |
| `--low-bg` | #E0F5F2 | Background for LOW elements |

#### Brand Colours

| Variable | Hex | Usage |
|----------|-----|-------|
| `--teal-900` | #003530 | Header gradient start |
| `--teal-800` | #005048 | Header gradient mid |
| `--teal-700` | #007D71 | Primary accent, card title border |
| `--teal-100` | #E0F5F2 | Light teal backgrounds |
| `--teal-50` | #F0FAF8 | Table hover, section backgrounds |

#### Perimeter Colours

| Variable | Hex | Usage |
|----------|-----|-------|
| `--int-blue` | #1D4ED8 | Internal perimeter chip text |
| `--int-blue-light` | #DBEAFE | Internal perimeter chip background |
| `--ext-purple` | #7C3AED | External perimeter chip text |
| `--ext-purple-light` | #EDE9FE | External perimeter chip background |

#### Neutral Palette

| Variable | Hex | Usage |
|----------|-----|-------|
| `--green-700` | #047857 | Implemented status text |
| `--green-600` | #059669 | Success accents |
| `--green-100` | #D1FAE5 | Implemented backgrounds |
| `--slate-900` | #0F172A | Body text |
| `--slate-700` | #334155 | Secondary text |
| `--slate-500` | #64748B | Tertiary text, labels |
| `--slate-300` | #CBD5E1 | Borders |
| `--slate-100` | #F1F5F9 | Table row borders, backgrounds |

### 1.3 Layout

- Container: max-width 1340px, 24px padding, centred
- Cards: white background, 10px border-radius, 1px slate-300 border, 20px padding
- Border shadow: `0 1px 3px rgba(0,0,0,0.06)`

---

## 2. Component Specifications

### 2.1 Report Header

```
Layout: CSS Grid — 1fr auto
Background: linear-gradient(135deg, teal-900 0%, teal-700 100%)
Padding: 26px 32px
Border-radius: 12px
Decorative circle: position absolute, right -60px top -60px, 240px, rgba white 0.04
```

Left column:
- h1: Vendor name (22px, 700, -0.5px letter-spacing)
- Subtitle: Assessment ID, completion date, template (12px, 300, 0.8 opacity)

Right column (badges):
- Overall Risk badge: threshold-coloured (MEDIUM=amber bg white text, etc.)
- DORA badge: always red (#DC2626) with white text if DORA=Yes, omit if No
- Criticality badge: #FCA5A5 bg, #7F1D1D text if Critical; omit if Standard

### 2.2 KPI Row

```
Layout: CSS Grid — repeat(5, 1fr), 14px gap
Cards: white, 10px radius, 16px 18px padding
```

Five cards in order:
1. **Overall Risk**: value = classification text, threshold-coloured; sub = max residual
2. **Total Risks**: value = count; sub = "Operational: X | Security: Y"
3. **Treated / In Treatment**: value = "X / Y" (green/amber); sub = percentage treated
4. **Euronext Controls**: value = "X / Y" (green/red); sub = "Implemented / Pending"
5. **Certification**: value = cert type(s); sub = validation status

### 2.3 Main Grid (Spider + Profile + Bars)

```
Layout: CSS Grid — 380px 1fr, 16px gap
Left: Spider chart card
Right: Flex column with Profile card + Domain bars card
```

#### Spider Chart SVG

```
ViewBox: 0 0 400 400
Centre: (200, 195)
Radius: 150px
Scale: 0–25 (OneTrust)
Pentagon angles: -90°, -18°, 54°, 126°, 198°
```

Five rings at scores 4, 8, 12, 17, 25:
- Ring radius formula: `(score / 25) × 150`
- Ring 4 (r=24): teal dashed stroke, 1.2px, dasharray 4,3
- Ring 8 (r=48): slate stroke, 0.5px
- Ring 12 (r=72): red dashed stroke, 1px, dasharray 6,3, opacity 0.35
- Ring 17 (r=102): slate stroke, 0.5px
- Ring 25 (r=150): slate stroke, 0.5px

Ring number labels along top axis (right of centre, y at each ring level).

Data polygon:
- Each vertex at `(score / 25) × 150` from centre, at the domain's angle
- Fill: `rgba(0,125,113,0.22)`, stroke: teal-700, 2.5px
- Dots at each vertex: 5px radius, threshold-coloured

Axis labels: 12px IBM Plex Sans 700, positioned outside the polygon.
Score badges: rounded rect (rx=4) with threshold-coloured fill + monospace text.

Legend at bottom: two items showing LOW/MED boundary and MED/HIGH boundary lines.

#### Supplier Profile Card

Fields (2-column grid, 8px row gap, 24px column gap):
- Supplier Name
- Supplier Type
- Organisation
- Service Criticality (red if Critical)
- DORA Scope (red if Yes)
- Critical Supplier (red if Yes)
- Certification (green)
- Analyst Review
- Manager Review

**DO NOT include ENX L3 Taxonomy.**

#### Domain Score Bars

Horizontal bars for each domain (sorted by score descending):
```
Grid: 140px label | 1fr track | 90px stage chip
Track height: 24px
Fill: threshold-coloured gradient (bar-medium or bar-low)
Width: (score / 25) × 100%
Label inside bar: score value (IBM Plex Mono 11px 700 white)
```

Below bars: threshold legend line showing ≤4 LOW | >4–≤12 MEDIUM | >12 HIGH

### 2.4 Inherent Risk Rationale

Teal callout box (`callout-teal`): 4px left border teal-700, teal-100 background.
Content: single paragraph explaining the inherent risk level using PDF data only.

### 2.5 Risks with Pending Controls Table

Full-width table showing ONLY risks with stage "In Treatment" or controls with
status ≠ Implemented.

Columns: Risk ID | Risk Description | Residual (score-badge) | Target | Stage (chip) | Domain | Pending Euronext Control(s)

Score badges use threshold colours. Stage chips use chip-in-treatment style.

### 2.6 Euronext Controls Register Table

Full table of ALL Euronext controls (deduplicated by Control ID).

Columns: Euronext Control | Description | Category | Perimeter (chip) | Status (chip) | Linked Risks

Row styling:
- Pending rows: `background: rgba(254,226,226,0.25)` (red tint)
- Implemented rows: `background: rgba(209,250,229,0.2)` (green tint)

Sort: Pending first, then Implemented.

### 2.7 Dual-Perimeter Matrix

Table: 6 columns (Perimeter label + 5 domains).
Two rows: External (Vendor) and Internal (Euronext).

Cell styling:
- Mitigated: green-100 bg, green-700 text, "✔ Mitigated"
- Alert: medium-bg, medium-amber text (if MEDIUM risk) or high-bg, high-red text (if HIGH)

Below the table: amber callout box identifying the "All-Internal Residual Exposure"
pattern if applicable.

### 2.8 Bottom Grid (Findings + Actions)

```
Layout: CSS Grid — 1fr 1fr, 16px gap
```

**Left card — Critical Findings:**
3–4 finding items, each with:
- Icon (26px square, rounded, threshold-coloured background)
- Text with bold lead sentence

Typical findings pattern:
1. Pending Euronext controls (amber/red icon)
2. Overall risk classification with threshold context (amber icon)
3. Vendor performance (green icon)
4. Assessment outcome (teal icon)

**Right card — DORA Status & Actions:**
- DORA status box: red background if DORA=Yes, teal if No
- 4–5 numbered action items (rec-num circles in teal-700)

### 2.9 Footer

```
Text-align: center
Padding: 14px
Font-size: 10px
Color: slate-500
Border-top: 2px solid teal-700
Content: "EURONEXT NV — Information Security Assurance | TPRM Executive Summary —
  Strategic Risk Intelligence Dashboard | [Vendor Name] | [Month Year] | CONFIDENTIAL"
```

---

## 3. Print Styles

```css
@media print {
  body { background: white; font-size: 11px; }
  .report-container { padding: 0; max-width: 100%; }
  .card, .kpi-card { box-shadow: none; border: 1px solid #ddd; }
  .report-header { border-radius: 0; }
}
```

---

## 4. Spider Chart Geometry Reference

Pentagon vertex computation for any score `s` at domain index `i` (0-indexed):

```
angle = (i × 72° - 90°) × π / 180
x = (s / 25) × 150 × cos(angle)
y = (s / 25) × 150 × sin(angle)
```

Domain index mapping:
- 0: Cybersecurity (top, -90°)
- 1: Data Management (right, -18°)
- 2: IT (bottom-right, 54°)
- 3: Business Continuity (bottom-left, 126°)
- 4: Third-Parties (left, 198°)

Ring vertices follow the same formula with `s` = ring value (4, 8, 12, 17, 25).
