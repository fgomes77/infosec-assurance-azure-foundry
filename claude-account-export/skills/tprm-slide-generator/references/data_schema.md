# TPRM Data JSON Schema (`tprm_data.json`)

*Reconstructed reference — regenerated on 2026-09-11 from the skill's scripts and template constants to replace a file missing from the original skill upload.*

This document specifies the full JSON structure **produced** by `scripts/extract_pdf.py` and **consumed** by `scripts/generate_radar.py` and `scripts/generate_slide.js`. Field names and structure below are taken directly from the code and must match exactly.

Default file location (as used by the scripts' CLI defaults): `/home/claude/tprm_data.json`.

---

## Top-level object

| Field | Type | Required | Allowed values / format | Produced by | Consumed by | Notes |
|---|---|---|---|---|---|---|
| `vendor` | string | Yes | Free text (vendor name exactly as in PDF) | `extract_pdf.py` (regex `Name\s*\((.+?)\)`; fallback `"Unknown Vendor"`) | `generate_slide.js` | Used in presentation title and header text `"{vendor} — Security Risks"`. |
| `assessment_id` | string | No (may be `""`) | Free text, e.g. `"AssessmentID_2026"` | `extract_pdf.py` | *(not read by generators)* | Extracted metadata; kept for traceability. |
| `report_date` | string | Yes | Human-readable month + year, e.g. `"February 2026"` | `extract_pdf.py` (hardcoded default — **correct manually** to match the assessment date) | `generate_slide.js` | Rendered in the header subtitle line. |
| `service_desc` | string | Yes | Free text, one line | `extract_pdf.py` (heuristic default — override manually) | `generate_slide.js` | Shown in the Service & Deployment banner. Keep short (single banner line). |
| `dora_scope` | boolean | Yes | `true` / `false` | `extract_pdf.py` | `generate_slide.js` | Rendered as `"Yes ✔"` (green) or `"No ✗"` (amber) in the service banner. |
| `criticality` | string | Yes | `"Critical"` \| `"Not-Critical"` | `extract_pdf.py` | `generate_slide.js` | Shown in the CRITICALITY KPI box. |
| `overall_risk` | string | Yes | `"High"` \| `"Medium"` \| `"Low"` | `extract_pdf.py` (`score_to_severity` of max domain score: ≥7.0 High, ≥4.0 Medium, else Low) | `generate_slide.js` | Drives the OVERALL RISK KPI colour scheme (`riskKpi`): High=red, Medium=amber, otherwise green. Any other string falls through to green. |
| `certifications` | array of string | No (defaults to `[]`) | e.g. `["ISO 27001"]` | `extract_pdf.py` (regex `ISO\s*\d{5}`, deduplicated) | `generate_slide.js` | Joined with `", "`; empty array renders as `"None"`. |
| `domain_scores` | object | Yes | See below | `extract_pdf.py` | `generate_radar.py`, indirectly the slide via the radar PNG | Exactly 5 keys expected. |
| `top_risks` | array of object | Yes | Max 3 rendered (`.slice(0,3)`) | `extract_pdf.py` (3 highest-score risks) | `generate_slide.js` | See **top_risks[]** below. |
| `full_register` | array of object | Yes (may be `[]`) | All risks, any length | `extract_pdf.py` | `generate_slide.js` | Rendered as the one-line "Full Register (N risks — In Treatment)" strip. |
| `mitigations` | array of object | Yes (may be `[]`) | Max 3 rendered (`.slice(0,3)`) | `extract_pdf.py` (first 3 unique Pending controls) | `generate_slide.js` | See **mitigations[]** below. |
| `perimeter` | object | Yes | See below | `extract_pdf.py` | `generate_slide.js` | 5 keys, one per domain. Missing keys fall back to `✔ Mitigated` / `✔ Mitigated`. |
| `findings` | array of string | Yes | Max 3 rendered (`.slice(0,3)`) | `extract_pdf.py` | `generate_slide.js` | Supports `**bold**` markdown; see **findings[]** below. |
| `_raw_risks` | array of object | No | Full parsed risk list | `extract_pdf.py` | *(reference only — not read by any generator)* | Internal/debug field; see **_raw_risks[]** below. |

---

## `domain_scores` (object)

Exactly these 5 keys — the canonical domain names used throughout the skill (`DOM_KEYS` in `generate_radar.py`, `DOMAINS[].key` in `template_constants.js`):

| Key | Type | Required | Allowed values |
|---|---|---|---|
| `"Cybersecurity"` | number | Yes | 0.0–10.0 |
| `"Data Management"` | number | Yes | 0.0–10.0 |
| `"IT"` | number | Yes | 0.0–10.0 |
| `"Business Continuity"` | number | Yes | 0.0–10.0 |
| `"Third-Parties"` | number | Yes | 0.0–10.0 |

- Semantics: **maximum Residual Risk Score** among risks mapped to that domain; `1.0` when no risk maps to the domain (minimal residual exposure).
- `generate_radar.py` reads them in the fixed order above via `d["domain_scores"].get(k, 1.0)` — a missing key silently becomes `1.0`.
- Score colour thresholds used by both radar badges and slide score panels: **≥ 5.5 red**, **≥ 4.0 amber**, **< 4.0 green**. (Note this differs from the High/Medium/Low overall classification, which uses ≥ 7.0 / ≥ 4.0.)

## `top_risks[]` (array of objects)

Sorted by `score` descending; the slide renders at most the first 3.

| Field | Type | Required | Allowed values | Used by slide |
|---|---|---|---|---|
| `id` | string | Yes | Risk ID from the PDF, e.g. `"2525"` | No (not rendered here, kept for traceability) |
| `score` | number | Yes | 0.0–10.0 (Residual Risk Score) | Yes — big number, formatted `toFixed(1)`, colour by threshold (≥5.5 red / ≥4.0 amber / else green) |
| `domain` | string | Yes | One of the 5 domain names above | No (informational) |
| `title` | string | Yes | Concise standardised title (see `map_risk_title` in `extract_pdf.py`) | Yes — bold row title |
| `detail` | string | No | Free text; slide truncates to 80 chars (`substring(0,80)`); extractor supplies first 90 chars of description | Yes — italic sub-line, only if present |

Standardised titles produced by `map_risk_title` (free text is allowed, but these are the canonical values): `"Unsecure Network Threat Detection"`, `"Inadequate Access Management"`, `"Security Incidents Not Properly Managed"`, `"Security Risks Not Managed"`, `"Unregistered Assets in CMDB"`, `"Third-Parties Relationship Not Properly Managed"`, `"Inadequate Vulnerability Management"`, `"Lack of Business Continuity and DR Capabilities"`, `"Insufficient Data Protection Lifecycle"`, or the first 60 chars of the description as fallback.

## `full_register[]` (array of objects)

One entry per risk (all risks, not just top 3), sorted by score descending.

| Field | Type | Required | Allowed values | Used by slide |
|---|---|---|---|---|
| `id` | string | Yes | Risk ID, e.g. `"2525"` | Yes — bold, coloured by score threshold |
| `label` | string | Yes | Short label (≤ ~8 chars). Canonical `LABEL_MAP` values: `"Net"`, `"IAM"`, `"Incidents"`, `"Sec risks"`, `"Assets"`, `"Supply"`, `"BC/DR"`; fallback: first 8 chars of the title | Yes |
| `score` | number | Yes | 0.0–10.0 | Yes — printed after the label; also colours the `id` |

## `mitigations[]` (array of objects)

The slide renders at most the first 3. The extractor emits the first 3 unique **Pending** controls (deduplicated by control `id`).

| Field | Type | Required | Allowed values | Used by slide |
|---|---|---|---|---|
| `label` | string | Yes | Control ID / short name, e.g. `"Euronext SOC Integration"` | Yes — bold |
| `detail` | string | Yes | Control description | Yes — after an em-dash, muted |
| `status` | string | Yes | `"Pending"` \| `"Implemented"` (any value other than `"Pending"` is treated as done; missing defaults to `"Pending"`) | Yes — `"⏳ Pending"` badge (red) vs `"✔ Done"` badge (green) |

## `perimeter` (object)

Keys: the 5 domain names (`"Cybersecurity"`, `"Data Management"`, `"IT"`, `"Business Continuity"`, `"Third-Parties"`). Each value:

```
{ "internal": { "text": <string>, "alert": <boolean> },
  "external": { "text": <string>, "alert": <boolean> } }
```

| Field | Type | Required | Allowed values / behaviour |
|---|---|---|---|
| `internal.text` / `external.text` | string | Yes | `"✔ Mitigated"` (extractor emits `"✔  Mitigated"` with two spaces) when clean, or `"⚠  <pending control name(s)>"` when alerting. May contain `\n` for a second line (extractor joins up to 2 internal pending names). Extractor truncates each control name to 22 chars. |
| `internal.alert` / `external.alert` | boolean | Yes | `true` → amber bold text (internal cell also gets amber-pale background); `false` → green text on default cell background. |

- **Internal** = Euronext-owned controls (Control ID starts with `"Euronext"`). **External** = vendor-side controls (any other prefix — `CIS`, `ISO`, `NIST`, `SOC2`).
- A domain missing from `perimeter` (or a missing `perimeter` object) defaults in `generate_slide.js` to `{internal:{text:"✔ Mitigated",alert:false}, external:{text:"✔ Mitigated",alert:false}}`.

## `findings[]` (array of strings)

At most 3 rendered, as numbered blue-chip bullets. Inline `**bold**` markdown is parsed by `generate_slide.js`: bold segments render bold and coloured — the exact word `Pending` in red, the exact word `Implemented` in green, any other bold text in blue; non-bold text renders in body colour.

## `_raw_risks[]` (array of objects, reference only)

Full parsed risk list written by `extract_pdf.py` (`default=str` serialisation). Not consumed by any generator script — kept for manual review/correction.

| Field | Type | Description |
|---|---|---|
| `id` | string | Risk ID |
| `score` | number | Residual Risk Score |
| `description` | string | Verbatim (undoubled) risk description paragraph |
| `title` | string | Standardised title from `map_risk_title` |
| `domain` | string | One of the 5 domains (from `classify_domain`) |
| `controls[]` | array of objects | Each: `id` (string, e.g. `"CIS 8.2"` / `"Euronext ..."`), `name` (string), `category` (string), `status` (`"Implemented"` \| `"Pending"`) |

---

## Annotated example

```json
{
  "vendor": "Vendor Name",                          // exact name from PDF — appears in slide title/header
  "assessment_id": "AssessmentID_2026",             // traceability only; not rendered
  "report_date": "February 2026",                   // header subtitle; verify against assessment date
  "service_desc": "SaaS HR Talent Assessment Platform — pre-employment cognitive & behavioral testing, team analytics",
  "dora_scope": false,                              // boolean → "No ✗" (amber) in banner
  "criticality": "Not-Critical",                    // "Critical" | "Not-Critical" → CRITICALITY KPI
  "overall_risk": "Medium",                         // "High" | "Medium" | "Low" → KPI colour
  "certifications": ["ISO 27001"],                  // [] renders as "Certs: None"

  "domain_scores": {                                // exactly these 5 keys, 0–10; 1.0 = no residual risk mapped
    "Cybersecurity": 6.0,
    "Data Management": 1.0,
    "IT": 5.0,
    "Business Continuity": 3.0,
    "Third-Parties": 4.8
  },

  "top_risks": [                                    // sorted by score desc; slide shows first 3
    {
      "id": "2525",
      "score": 6.0,                                 // rendered "6.0"; ≥5.5 → red
      "domain": "Cybersecurity",
      "title": "Unsecure Network Threat Detection",
      "detail": "IDS/IPS signatures not regularly updated"   // truncated to 80 chars on slide
    }
  ],

  "full_register": [                                // ALL risks; one-line strip under Top-3 card
    { "id": "2525", "label": "Net", "score": 6.0 }
  ],

  "mitigations": [                                  // slide shows first 3
    {
      "label": "Euronext SOC Integration",
      "detail": "SOC logging/monitoring — GrayLog & Microsoft Sentinel",
      "status": "Pending"                           // "Pending" → red badge; anything else → "✔ Done"
    }
  ],

  "perimeter": {                                    // one entry per domain; missing → "✔ Mitigated"
    "Cybersecurity": {
      "internal": { "text": "⚠ Unsecure Network\nInadequate IAM", "alert": true },
      "external": { "text": "✔ Mitigated", "alert": false }
    },
    "Data Management": {
      "internal": { "text": "✔ Mitigated", "alert": false },
      "external": { "text": "✔ Mitigated", "alert": false }
    },
    "IT": {
      "internal": { "text": "⚠ Assets not in CMDB", "alert": true },
      "external": { "text": "✔ Mitigated", "alert": false }
    },
    "Business Continuity": {
      "internal": { "text": "✔ Mitigated", "alert": false },
      "external": { "text": "✔ Mitigated", "alert": false }
    },
    "Third-Parties": {
      "internal": { "text": "⚠ Security Agreements\npending", "alert": true },
      "external": { "text": "✔ Mitigated", "alert": false }
    }
  },

  "findings": [                                     // slide shows first 3; **bold** parsed
    "All vendor controls (CIS) are **Implemented**; key Euronext controls remain **Pending** — immediate action required.",
    "Highest residual risk 6.0 in Cybersecurity — SOC integration is the critical priority.",
    "Not-Critical, Not-DORA scope — standard monitoring cadence. **Next review: Q2 2026**"
  ],

  "_raw_risks": [                                   // extractor debug output; not consumed downstream
    {
      "id": "2525",
      "score": 6.0,
      "description": "IDS/IPS signatures not regularly updated ...",
      "title": "Unsecure Network Threat Detection",
      "domain": "Cybersecurity",
      "controls": [
        { "id": "Euronext SOC Integration", "name": "SOC logging/monitoring",
          "category": "Detect", "status": "Pending" },
        { "id": "CIS 13.1", "name": "Centralize Security Event Alerting",
          "category": "Detect", "status": "Implemented" }
      ]
    }
  ]
}
```

---

## Validation reminders (from the SKILL.md quality checklist)

- All 5 `domain_scores` keys must be present and deliberately set (none left at the default `1.0` unless truly no risk maps there).
- `top_risks` must be the 3 highest Residual Risk Score entries.
- `overall_risk` must equal `score_to_severity(max(domain_scores))`: ≥ 7.0 High, ≥ 4.0 Medium, else Low.
- `report_date` must match the assessment date from the PDF (the extractor hardcodes `"February 2026"` — always review).
- `service_desc` is a heuristic default from the extractor — override with the real service description.
