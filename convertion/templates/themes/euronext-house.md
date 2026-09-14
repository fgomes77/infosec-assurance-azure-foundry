# Euronext house style — the only permitted theme

Prose form of `templates/enx-theme.json`. The JSON holds the machine-readable
tokens every renderer and HTML template reads; this file explains **why** each
rule exists and what an author may and may not change. Where the two disagree,
`enx-theme.json` wins — and changing either is a template change
(`templates/README.md` "Changing a template"), never an ad-hoc restyle.

`theme-factory` and `brand-guidelines` are **not deployed**
(`templates/skill-decisions.json`): there is no per-deliverable theming step.

## 1. Palette

| Use | Token | Value |
|---|---|---|
| Primary (headings, table header fill, KPI accents) | `palette.primary` | `#008D7F` — RGB(0,141,127), the DeepSearch dark-teal identity |
| Secondary (section titles, chart line) | `palette.secondary` | `#5ce0d2` |
| Dashboard background / surfaces | `palette.body_background`, `palette.surface` | `#0a1a1f`, `#0f2429` |
| Office documents | white page, teal headings, grey 8 pt classification header | — |

Risk colours are fixed by band, never by taste: critical `#d64545`,
high `#e06c3c`, medium `#e0b23c`, low `#3cb371`, not found `#8fa3a1`
(`risk_colours`). Bands come from `governance/RISK_THRESHOLDS.md`
(High ≥ 7.0, Medium ≥ 4.0, Low < 4.0 on the TPRM 10-scale); a renderer never
invents a threshold.

Office workbooks add the financial-model convention: **blue = hard-coded
input, black = formula**, teal header = column title.

## 2. Glyphs

Status and risk markers are **HTML entities only** (`risk_glyphs`), never
literal Unicode: `&#x1F534;` high, `&#x1F7E0;` medium, `&#x1F7E1;` low-medium,
`&#x1F7E2;` low, `&#x2705;` yes, `&#x274C;` no, `&mdash;` for "not applicable".
Literal emoji break the self-contained HTML download and the PDF renderer's
font fallback (DeepSearch PHASE 4B rule 3).

## 3. Typography

Verdana (`Geneva`, `DejaVu Sans` fallbacks) everywhere; `DejaVu Sans Mono` for
code. Minimum 11 px on screen, 13 px body, 20 px headings, 28 px KPI numbers,
line height 1.45. Office documents use the size set fixed by each renderer
(DPO report: Arial 9 pt body, reproducing the byte-verified original 1:1).

## 4. Layout

Dashboards target 1920×1200 with a 420 px right column, 10 px radius, 16 px
gaps and a maximum content width of 1800 px. Decks are 16:9. Nothing is
responsive beyond that: these are documents of record, not web pages.

## 5. Charts

Chart.js 4.x from `cdnjs.cloudflare.com` only — the single external reference
any deliverable may carry (`charts.cdn`; the delivery Function's gates reject
every other external `src`/`href`). Radar charts use 6 axes scored 1–5 for
DeepSearch; the CISO dashboards use 5 domains on the 10-scale.

## 6. Classification

Every deliverable carries a classification string — default `Confidential` for
dashboards, `Euronext Internal` for advisory documents — in the header or
footer: `Euronext - Information Security Assurance - <classification>`.
The **Purview sensitivity label** applied to the stored file is a separate
control (`registry.json` `sensitivity_label` and the library default), not a
theme token.

## 7. What an author may change

Nothing in this file or in `enx-theme.json` without an approval run
(`scripts/update_templates.py --approved-by … --approval-run …`). Content —
wording, rows, findings — is free; colour, font, glyph set, thresholds, layout
and the chart source are not.
