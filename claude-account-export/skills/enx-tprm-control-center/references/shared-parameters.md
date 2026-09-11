# ENX TPRM — Shared Parameters (Single Source of Truth)

Cross-cutting constants for every ENX TPRM worker skill. **Constants only** —
this file stays lean so workers can read it cheaply. Verbose reference material
(full ISO/IEC 27005:2022 tables, the 42 ICT supplier types A.01–D.05, the
55 risk categories) is **not** here; it lives in the relevant worker's own
`references/` folder and is read only when that worker needs it.

If a worker's `SKILL.md` conflicts with this file on **risk thresholds** or
**design tokens**, this file wins (standing TPRM Risk Threshold Override).

---

## 1. Risk threshold override — OneTrust 1–25 scale

Supersedes any threshold stated in an individual worker `SKILL.md`.

| Band | Condition (residual score) | Colour | Hex |
|------|----------------------------|--------|-----|
| HIGH | score > 12 | Red | `#FCA5A5` |
| MEDIUM | score > 4 and ≤ 12 | Amber | `#FCD34D` |
| LOW | score ≤ 4 | Teal | `#6EE7B7` |

- OneTrust operates a **1–25 risk scale** (Likelihood × Impact, 1–5 each).
- **Domain score = MAX residual score** of any risk within that domain.
- Radar / spider graph rings are drawn at **4, 8, 12, 17, 25**.
- L×I equivalence: ≤4 = 1–4 Low · >4–12 = 5–12 Medium · >12 = 13–25 High.

## 2. TPSRCA assessment result bands

Applied to the overall weighted score (0–100) of a TPSRCA / DeepSearch
assessment.

| Score | Result |
|-------|--------|
| ≥ 80 | APPROVE |
| 65–79 | CONDITIONAL |
| 50–64 | EDD (Enhanced Due Diligence) |
| 35–49 | NOT RECOMMENDED |
| < 35 | REJECT |

## 3. Confidence bands (OSINT evidence quality)

| Band | Range | Meaning |
|------|-------|---------|
| 🟢 | ≥ 90% | Verified via primary sources (Trust Center, cert registries, regulators) |
| 🟠 | 75–89% | Corroborated via secondary sources |
| 🔴 | < 75% | Limited or conflicting evidence |

## 4. Perimeter model

Every risk is tagged to one perimeter. All-internal residual exposure is the key
analytical pattern to surface.

- **Internal** — Euronext-side controls and exposure ("Euronext Perimeter").
- **External** — vendor-side controls and exposure.

## 5. HTML design tokens

Two deliverables use **two distinct teal tokens** — do not unify them.

### 5a. DeepSearch Report Dashboard (dark theme)
| Token | Value |
|-------|-------|
| Body background | `#0a1a1f` |
| Header gradient | `#003530` → `#005048` |
| Primary accent / section bg | `#008D7F` (RGB 0,141,127) |
| Secondary accent | `#5ce0d2` |
| Highlight accent | `#00B5A3` |
| Text | White |
| Font | Verdana |

### 5b. CISO canonical HTML (light theme, v3.0/v3.1)
| Token | Value |
|-------|-------|
| Primary teal | `#007D71` |
| Header gradient | `#003530` → `#005048` |
| Fonts | Sora (headings) · IBM Plex (body/mono) |
| Minimum font size | 11 px |
| KPI cards | Frosted-glass, 2×2 grid |

### 5c. Status colours (shared by both)
| State | Hex |
|-------|-----|
| Implemented / Yes / Pass | `#6EE7B7` (or DOCX `#C6EFCE`) |
| Pending / Partial | `#FCD34D` (or DOCX `#FFEB9C`) |
| Not Doing / No / Fail | `#FCA5A5` (or DOCX `#FFC7CE`) |
| Euronext teal (DOCX) | `#008D7F` |

## 6. Standard emoji set (HTML entities — never literal Unicode)

| Glyph | Entity | Meaning |
|-------|--------|---------|
| 🟢 | `&#x1F7E2;` | Low risk / Yes |
| 🟡 | `&#x1F7E1;` | Low-Medium |
| 🟠 | `&#x1F7E0;` | Medium risk |
| 🔴 | `&#x1F534;` | High risk / Critical |
| ✅ | `&#x2705;` | Present |
| ❌ | `&#x274C;` | Absent |
| — | `&mdash;` | Em dash |

## 7. Regulatory frameworks in scope

DORA (Art. 28/30) · NIS2 (Art. 21) · GDPR (Art. 28/33, SCCs 2021/914) ·
EU AI Act · ISO/IEC 27001:2022 · ISO/IEC 27002:2022 · ISO/IEC 27005:2022 ·
ISO/IEC 42001:2023 · ISO 22301 · ISO 27701 · NIST CSF 2.0 · CIS v8.1 ·
PCI DSS · SOC 2 Type II.

## 8. Output conventions

- Working directory: `/home/claude/` — copy final deliverables to
  `/mnt/user-data/outputs/` and deliver with `present_files`.
- All Python scripts: `# -*- coding: utf-8 -*-` header and `encoding='utf-8'`
  on every `open()`.
- Documents: exhaustive technical detail. CISO reports: high-level summary only.
- Language: English (standard for all ENX outputs).
- Handle OneTrust OCR doubled-character artefacts when parsing PDFs.
