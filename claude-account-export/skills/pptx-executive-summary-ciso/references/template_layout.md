# Euronext TPRM Slide — Template Layout Reference

*Reconstructed reference — regenerated on 2026-09-11 from the skill's scripts and template constants to replace a file missing from the original skill upload.*

Layout, colour and typography values below are taken directly from `assets/template_constants.js`, `scripts/generate_slide.js` and `scripts/generate_template.js`. All positions and sizes are in **inches** on a `LAYOUT_16x9` slide (10.0" × 5.625"). Font face is **Calibri** everywhere; radar chart labels use **DejaVu Sans** (matplotlib).

---

## Layout constants (`L` in template_constants.js)

| Constant | Value | Meaning |
|---|---|---|
| `W` × `H` | 10 × 5.625 | Slide size (16:9) |
| `HDR_H` | 0.88 | Header band height (y = 0 → 0.88) |
| `FTR_Y` | 5.24 | Footer band top (y = 5.24 → 5.625) |
| `TOP` / `BOT` | 0.95 / 5.22 | Content area vertical bounds |
| `GAP` | 0.03 | Vertical gap between stacked cards |
| `LX` / `LW` | 0.13 / 5.44 | Left column x / width |
| `RX` / `RW` | 5.70 / 4.17 | Right column x / width |

## Colour palette (`C` in template_constants.js)

| Token | Hex | Token | Hex | Token | Hex |
|---|---|---|---|---|---|
| brandDark | 0A2926 | red | B83228 | blue | 1A4F8A |
| brandDeep | 0D3D3A | redDark | 8B1E16 | blueDark | 122E57 |
| brandMid | 0E6B68 | redPale | FCECEA | bluePale | EBF3FC |
| brandBright | 12B5AF | amber | C97A00 | white | FFFFFF |
| brandPale | E8F6F5 | amberDark | 8B5200 | offWhite | F8FAFA |
| brandPaleMid | C4E8E6 | amberPale | FEF3E2 | bg | ECF2F2 |
| green | 1A6B3C | greenPale | E6F5EE | cardBg | FFFFFF |
| border | C8DCDB | borderLight | E4EEEE | dark | 0D1F1E |
| body | 2A3B3A | muted | 5A706E | | |

Domain colours (blue ramp, `DOMAINS` order): Cybersecurity `domB1` 1B3A6B · Data Management `domB2` 1E5799 · IT `domB3` 2471A3 · Business Continuity `domB4` 2980B9 · Third-Parties `domB5` 3498DB.

Score thresholds (used everywhere a score is coloured): **≥ 5.5** red B83228 (bg FCECEA, dark 8B1E16) · **≥ 4.0** amber C97A00 (bg FEF3E2, dark 8B5200) · **< 4.0** green 1A6B3C (bg E6F5EE).

Shadow `sh(op)`: outer, colour 000000, opacity 0.08 default (0.09 on right-column cards), blur 7, offset 3, angle 135. Card style: white fill (`cardBg`), border C8DCDB @ 0.6 pt, left accent stripe 0.055" wide.

---

## Slide region diagram

```
0"                                                                        10"
┌──────────────────────────────────────────────────────────────────────────┐ 0
│▐ HEADER (brandPale, h=0.88)                                              │
│▐ "{Vendor} — Security Risks" (22pt bold)   ┌OVERALL RISK┐ ┌CRITICALITY┐  │
│▐ "Executive Summary · TPRM …" (8pt)        │  KPI box   │ │  KPI box  │  │
├══════ brandBright rule 1.8pt ══════════════╧════════════╧═╧═══════════╧══┤ 0.88
│  LEFT COLUMN  x=0.13 w=5.44          │  RIGHT COLUMN  x=5.70 w=4.17      │ 0.95 (TOP)
│ ┌──────────────────────────────────┐ │ ┌───────────────────────────────┐ │
│ │ SERVICE & DEPLOYMENT banner      │ │ │ SECURITY RISK ASSESSMENT hdr  │ │
│ │ h=0.42 · accent brandBright      │ │ │ (brandDeep bar, h=0.29)       │ │
│ └──────────────────────────────────┘ │ │ subtitle · scale legend       │ │
│ ┌──────────────────────────────────┐ │ │                               │ │
│ │ ▲ TOP 3 EURONEXT IMPACT RISKS    │ │ │      RADAR CHART PNG          │ │
│ │ h=1.82 · accent red              │ │ │   (5-domain spider chart)     │ │
│ │  [score panel][title/detail] ×3  │ │ │        card h=2.34            │ │
│ │  Full Register strip (h=0.20)    │ │ └───────────────────────────────┘ │
│ └──────────────────────────────────┘ │ ┌───────────────────────────────┐ │
│ ┌──────────────────────────────────┐ │ │ EURONEXT PERIMETER · ATTACK   │ │
│ │ ✦ TOP 3 MITIGATION CONTROLS      │ │ │ SURFACE MAP (brandDeep bar)   │ │
│ │ h=0.92 · accent brandMid         │ │ │        │🏢 Internal│🌐 External│ │
│ │  (n) [badge] Label — Detail ×3   │ │ │ Cyber  │  status  │  status   │ │
│ └──────────────────────────────────┘ │ │ DataMgt│  status  │  status   │ │
│ ┌──────────────────────────────────┐ │ │ IT     │  status  │  status   │ │
│ │ 💡 KEY FINDINGS & RECOMMENDATIONS│ │ │ BusCont│  status  │  status   │ │
│ │ fills to BOT · accent blue,      │ │ │ 3rd-P  │  status  │  status   │ │
│ │ bluePale fill · (n) finding ×3   │ │ │   (fills to BOT=5.22)         │ │
│ └──────────────────────────────────┘ │ └───────────────────────────────┘ │
├══════ brandBright rule 1.8pt ════════╧═══════════════════════════════════┤ 5.24 (FTR_Y)
│▐ EURONEXT   *TPRM risk evaluation reflects Residual risk …          | 1  │
└──────────────────────────────────────────────────────────────────────────┘ 5.625
 ▐ = brandBright edge stripe (w=0.22) + brandMid pinstripe (w=0.035, header only)
```

Left-column vertical stack (y positions): Service banner y=0.95 h=0.42 → Top-3 Risks y=1.40 h=1.82 → Mitigations y=3.25 h=0.92 → Key Findings y=4.20 h=1.02 (to BOT=5.22). Gap between cards = 0.03. Right column: Radar card y=0.95 h=2.34 → Perimeter card y=3.32 h=1.90 (to BOT).

---

## Element table

### Header band (y=0 → 0.88)

| Element | x, y | w × h | Fill / line | Font |
|---|---|---|---|---|
| Band | 0, 0 | 10 × 0.88 | brandPale E8F6F5 | — |
| Left edge stripe | 0, 0 | 0.22 × 0.88 | brandBright 12B5AF | — |
| Pinstripe | 0.22, 0 | 0.035 × 0.88 | brandMid 0E6B68 | — |
| Bottom rule (line) | 0, 0.88 | 10 × 0 | brandBright, 1.8 pt | — |
| Title `"{vendor} — Security Risks"` | 0.36, 0.09 | 5.2 × 0.44 | — | 22 pt bold, brandDark 0A2926 |
| Subtitle `"Executive Summary · TPRM Risk Assessment · {report_date}"` | 0.36, 0.55 | 5.4 × 0.21 | — | 8 pt, brandMid, charSpacing 1.2 |

### KPI boxes (header, right side)

| Element | x, y | w × h | Colours | Font |
|---|---|---|---|---|
| OVERALL RISK box | 6.16, 0.09 | 1.74 × 0.71 | bg/border/text by `riskKpi(overall_risk)`: High red/redPale, Medium amber/amberPale, else green/greenPale; header strip h=0.20 in same accent | Label 6 pt bold white, charSpacing 2, centered; value 18 pt bold, centered (y=0.28 h=0.47) |
| CRITICALITY box | 8.02, 0.09 | 1.74 × 0.71 | bg brandPale, border/header/text brandMid, 1.5 pt border | Label 6 pt bold white; value 13 pt bold brandMid, centered |

### Left column cards (all: cardBg fill, border 0.6 pt C8DCDB, shadow sh(0.08), left accent stripe 0.055")

**Service & Deployment banner** — x=0.13 y=0.95, 5.44 × 0.42, accent brandBright. One rich-text line (Calibri, valign middle, x=LX+0.13): `"Service & Deployment  "` 9 pt bold brandDeep · `service_desc` 8.5 pt body · `"DORA: "` 8.5 pt body · `"Yes ✔"` green / `"No ✗"` amber 8.5 pt bold · `"Certs: …"` 8 pt muted.

**Top 3 Euronext Impact Risks** — x=0.13 y=1.40, 5.44 × 1.82, accent red.
- Section header strip: x=LX+0.055 y=1.40, (LW−0.055) × 0.27, fill redPale; text `"▲   TOP 3 EURONEXT IMPACT RISKS"` 9.5 pt bold red, charSpacing 0.3.
- 3 risk rows, each h=0.40, first at y=RSK_Y+0.29, pitch 0.44 (0.40 + 0.04 gap). Odd rows (i=1) get offWhite F8FAFA background band.
  - Score panel: w=1.72, fill `scoreBg(score)`, 0.04" left bar `scoreColor(score)`, right divider line border 0.6 pt. Caption `"RESIDUAL RISK SCORE"` 6 pt bold `scoreDark`, charSpacing 1.2, centered; value `score.toFixed(1)` 20 pt bold `scoreColor`, centered.
  - Title: 9.5 pt bold dark 0D1F1E, valign middle. Detail (optional, max 80 chars): 7.2 pt italic muted.
- Full Register strip: x=LX+0.055, y=RSK_Y+RSK_H−0.20, h=0.20, fill EFF5F4, top rule border 0.5 pt. Text 6.8 pt: `"Full Register (N risks — In Treatment):"` bold muted, then per risk `id` bold in `scoreColor(score)` + `"label score"` in body, separated by `" · "`.

**Top 3 Mitigation Controls** — x=0.13 y=3.25, 5.44 × 0.92, accent brandMid.
- Header strip 0.27 h, fill brandPale; `"✦   TOP 3 MITIGATION CONTROLS"` 9.5 pt bold brandDeep.
- 3 rows starting y=MIT_Y+0.30, pitch 0.20: numbered circle (OVAL 0.20 × 0.20, fill brandMid, digit 8 pt bold white centered) at x=LX+0.12; status badge 0.60 × 0.17 at x=LX+0.37 (Pending: redPale fill, red border 0.75 pt, `"⏳  Pending"` 6.5 pt bold red; else greenPale/green, `"✔  Done"`); text at x=LX+1.02, 7.8 pt: label bold dark + `"—  detail"` muted.

**Key Findings & Recommendations** — x=0.13 y=4.20, 5.44 × 1.02 (h=BOT−KF_Y), accent blue, card fill **bluePale EBF3FC**.
- Header strip 0.25 h, fill D2E5F6; `"💡   KEY FINDINGS & RECOMMENDATIONS"` 9.5 pt bold blue, charSpacing 0.2.
- 3 rows starting y=KF_Y+0.28, pitch 0.22: numbered circle (OVAL 0.18 × 0.18, fill blue, digit 7.5 pt bold white) at x=LX+0.13; finding text 7.8 pt at x=LX+0.37, valign middle — `**bold**` segments render bold in blue (word `Pending` red, `Implemented` green), normal text in body 2A3B3A.

### Right column — Radar card (x=5.70 y=0.95, 4.17 × 2.34; cardBg, border 0.6 pt, shadow sh(0.09))

| Element | Position | Style |
|---|---|---|
| Title bar | RX, RAD_Y, RW × 0.29 | fill brandDeep; brandBright accent 0.055 × 0.29 |
| Title `"SECURITY RISK ASSESSMENT"` | RX+0.10, +0.03, (RW−0.14) × 0.22 | 7.8 pt bold white, centered, charSpacing 1.8 |
| Legend `"Residual risk per domain · Scale 0–10 · 🔴 High ≥7 🟡 Medium 4–7 🟢 Low ≤4"` | RX+0.06, +0.30, (RW−0.12) × 0.13 | 6.0 pt muted, centered |
| Radar PNG image | RX+0.02, RAD_Y+0.44, (RW−0.04) × (RAD_H−0.46) | from `generate_radar.py` |

Radar PNG internals (generate_radar.py): figure 4.8 × 4.4 in @ 320 dpi, white bg; pentagon risk-zone fills at r=1.0/0.70/0.40 (red FDECED / amber FEF4E2 / green E6F7EE with dashed edges E8AAAA/DEBA70/7EC89A); grid rings at 2/4/6/8/10 (key rings 4/6/8 darker 96BCBA @1.2, others CCE0DE @0.6); teal data polygon (fill 0E6B68 layered alphas, stroke 12B5AF 2.8 pt, glow 0FA39F); per-spoke score badges at r=0.80 (10.5 pt bold white on rounded box coloured by score threshold, white edge); domain labels 9 pt bold in domain blues with white outline stroke; tick labels 6.2 pt on the Third-Parties spoke. First spoke (Cybersecurity) points up, order proceeds clockwise.

### Right column — Perimeter table card (x=5.70 y=3.32, 4.17 × 1.90; cardBg, border 0.6 pt, shadow sh(0.09))

| Element | Position | Style |
|---|---|---|
| Title bar | RX, TBL_Y, RW × 0.28 | fill brandDeep; brandBright accent 0.055 × 0.28 |
| Title `"EURONEXT PERIMETER  ·  ATTACK SURFACE MAP"` | RX+0.10, +0.03 | 7.5 pt bold white, centered, charSpacing 0.8 |

Table geometry: TX=RX+0.055; column widths CW0=1.44 (domain), CW1=1.26 (Internal), CW2=1.38 (External). Column header row at CH_Y=TBL_Y+0.29, h=0.26: Internal header fill brandPale / border brandPaleMid 0.6 pt, `"🏢  Internal"` 7.8 pt bold brandDeep centered; External header fill bluePale / border BCCDE8, `"🌐  External"` 7.8 pt bold blue centered.

5 data rows, ROW_H=(TBL_H−0.26−0.29)/5 ≈ 0.27 each, in `DOMAINS` order:

| Cell | Fill | Text |
|---|---|---|
| Domain label | domain colour (domB1…domB5) | domain name, 7.5 pt bold white, centered, valign middle |
| Internal status | alert → amberPale FEF3E2; else alt-row F6FEFD / F4 row FAFFFE; border borderLight 0.5 pt | 7.5 pt (7 pt when alert), bold when alert; amber when alert else green; centered |
| External status | alt-row F4F7FD / F8FAFF; border borderLight 0.5 pt | 7.5 pt, bold when alert; amber when alert else green; centered |

### Footer band (y=5.24 → 5.625)

| Element | x, y | w × h | Style |
|---|---|---|---|
| Band | 0, 5.24 | 10 × 0.385 | brandPale E8F6F5 |
| Top rule (line) | 0, 5.24 | 10 × 0 | brandBright, 1.8 pt |
| Left edge stripe | 0, 5.24 | 0.22 × 0.385 | brandBright |
| `"EURONEXT"` | 0.32, 5.30 | 1.30 × 0.24 | 8.5 pt bold brandDark, charSpacing 2.5 |
| Disclaimer `"*TPRM risk evaluation reflects Residual risk in present reporting week"` | 1.76, 5.31 | 7.0 × 0.22 | 6.8 pt brandMid, centered |
| Page number `"| 1"` | 9.60, 5.31 | 0.36 × 0.22 | 8 pt muted, right-aligned |

---

## generate_template.js differences (blank brand template)

`scripts/generate_template.js` renders the same chrome with grey placeholder text (8 pt italic 999999 on F0F0F0 header strips; radar placeholder box F5F5F5 with CCCCCC border at RX+0.3, TOP+0.50, (RW−0.6) × 1.70). Its OVERALL RISK KPI shows an amber `[Medium]` example at 16 pt, and its perimeter table y is TBL_Y=TOP+2.37 (vs 2.34+GAP≈3.32 — same position). **Known issue:** it references `C.bannerBg` for the header/footer band fill, but `bannerBg` is not defined in `template_constants.js` — the live slide generator uses `C.brandPale` (E8F6F5) instead, which should be treated as the canonical band colour.
