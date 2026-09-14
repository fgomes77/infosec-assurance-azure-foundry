# ENX HTML design guide (knowledge pack)

*Authored 2026-09-12; the quality floor of the claude.ai `frontend-design`
platform skill with its palette/typography guidance REPLACED by the
Euronext tokens. Applies where agents author HTML freely: advisory HTML
files, the template-manager visual-review page, free areas of the
DeepSearch dashboard. It NEVER restyles a registered template.*

## Rule 0 — registered templates are not restyled

Templates in `templates/registry.json` (DeepSearch dashboard, CISO
executive summary HTML, decks, DOCX) define layout, colours, fonts and
thresholds. Fill them; do not "improve" them. Changes go through
`template-manager` and the approval workflow.

## ENX tokens (use these, not a "distinctive" palette)

| Token | Value |
|---|---|
| Primary teal | `rgb(0,141,127)` / `#008D7F` (headings, accents, chart primary) |
| Dark ground (dashboards) | `#0F2F2C` with teal accents |
| Text on light | `#1F2A2A`; muted `#5B6B6A` |
| Severity High / Medium / Low | red `#C0392B` (score ≥7.0) / amber `#E67E22` (≥4.0) / green `#2E8B57` (<4.0) |
| Score-colour bands used by slide templates | red ≥5.5 / amber ≥4.0 / green otherwise |
| Font | Verdana, fallback Geneva, Tahoma, sans-serif (safe fonts only; no web fonts) |
| Classification banner | "Euronext Internal" (or the stated classification) top and bottom |

## Quality floor (checklist before returning any HTML)

- Single self-contained file: inline CSS/JS, no external CDNs, no
  remote fonts/images (SharePoint serves it offline; no egress).
- Responsive: readable at 400 px width; tables in `overflow-x:auto`
  containers; no horizontal page scroll.
- Accessibility: visible focus styles; contrast ≥4.5:1 for text; colour is
  never the only carrier of severity (add the label); `prefers-reduced-motion`
  respected; semantic headings in order; `lang="en"`.
- Real content only: no lorem, no `{{TOKEN}}`, no placeholder images; every
  number traces to the source data; date and sources section present.
- CSS hygiene: class-based selectors, no `!important` chains, no inline
  style duplication across rows.
- Print: A4/A3 print stylesheet when the page is a report (page breaks
  before H2, hide interactive controls).

## Review-page pattern (template-manager step 4)

Side-by-side **before / after** panels (iframe `srcdoc` or two columns),
a **diff table** (element / old / new / affected data field), an
**impact list** (agents, pipelines, schemas), approver notes box — all
inline, no scripts that fetch anything.

## Self-critique loop (once, before returning)

Plan against the brief → build → check every item of the floor →
fix → return. Do not loop more than twice; state what could not be
verified (e.g. no renderer for a visual check).

## Data-visualisation rules (from the dataviz harness skill, template-governed)

- **Palette:** a colour-blind-safe series palette derived from the ENX teal
  `RGB(0,141,127)` theme (`templates/enx-theme.json`), every series ≥3:1
  contrast against the background and against its neighbours. Never encode a
  distinction by hue alone — pair it with shape, dash or direct labelling.
- **Every chart carries** a title, labelled axes **with units**, and a legend
  only when there is more than one series (one series → label it directly).
- **Spider graphs:** axes fixed to the five domains of the deliverable and
  scaled 0–max of that deliverable's own thresholds
  (`governance/RISK_THRESHOLDS.md`) — never auto-scaled to the data.
- **Gauges:** band colours come from the scale the score belongs to, not from
  a generic red/amber/green ramp.
- **Banned:** 3-D anything, dual y-axes, truncated value axes on bar charts,
  pie charts with more than five slices, and any chart whose numbers are not
  also available as text in the page.
- **Readable in both themes:** tooltip and value text legible on light and
  dark backgrounds; no colour that disappears when printed greyscale.
