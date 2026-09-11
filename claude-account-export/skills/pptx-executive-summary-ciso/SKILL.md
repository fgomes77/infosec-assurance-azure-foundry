---
name: pptx-executive-summary-ciso
description: >
  Full end-to-end TPRM (Third-Party Risk Management) executive summary slide generator.
  Use this skill whenever a user uploads a OneTrust/Infosec TPRM assessment PDF and asks
  for a slide, report, executive summary, risk presentation, or board-ready output.
  Also trigger for: "generate TPRM slide", "create risk summary", "analyse this assessment",
  "make a board slide from this PDF", "TPRM executive summary", or any mention of vendor
  risk assessment + slide/presentation/report. Always use this skill — never attempt to
  generate a TPRM slide without following this workflow, as brand consistency and data
  accuracy depend on it.
---

# TPRM Executive Summary Slide Generator

Generates a **board-ready, single-slide TPRM Executive Summary** from a OneTrust / Infosec
assessment PDF. Output is a fully branded `.pptx` file using the Euronext TPRM template.

---

## Workflow (execute in order)

### Step 1 — Extract PDF data
Run the extraction script to parse the assessment PDF into a structured JSON file:
```bash
python3 /home/claude/tprm-skill/scripts/extract_pdf.py \
  --input  <path-to-uploaded-pdf> \
  --output /home/claude/tprm_data.json
```
> The script handles the doubled-character OCR artifact common in OneTrust exports.
> Review the JSON and manually correct any misclassified domain scores before proceeding.

### Step 2 — Generate radar chart PNG
```bash
python3 /home/claude/tprm-skill/scripts/generate_radar.py \
  --data   /home/claude/tprm_data.json \
  --output /home/claude/radar_chart.png
```

### Step 3 — Generate PPTX slide
```bash
node /home/claude/tprm-skill/scripts/generate_slide.js \
  --data  /home/claude/tprm_data.json \
  --radar /home/claude/radar_chart.png \
  --out   /home/claude/<VendorName>_TPRM_ExecSummary.pptx
```

### Step 4 — Copy to outputs and present
```bash
cp /home/claude/<VendorName>_TPRM_ExecSummary.pptx /mnt/user-data/outputs/
```
Then call `present_files` with the output path.

---

## Domain Classification Rules

Map each identified risk to one of the 5 domains using the **ENX L3 Taxonomy** field and
the **Control Category** of its mitigation controls:

| Risk theme (keywords)                              | Domain             |
|----------------------------------------------------|--------------------|
| IDS/IPS, SOC, network security, threat detection  | Cybersecurity      |
| Access control, IAM, PAM, authentication          | Cybersecurity      |
| Data classification, privacy, GDPR, encryption    | Data Management    |
| Logging, asset management, CMDB, patching, SDLC   | IT                 |
| BCM, DRP, RTO, continuity, backup                 | Business Continuity|
| Supply chain, third-party, vendor, TP agreements  | Third-Parties      |

**Domain Score** = maximum Residual Risk Score among all risks mapped to that domain.
If no risk maps to a domain, assign score **1.0** (minimal residual exposure).

---

## Overall Risk Classification

| Max domain score | Overall Risk |
|-----------------|--------------|
| ≥ 7.0           | High         |
| ≥ 4.0 < 7.0     | Medium       |
| < 4.0           | Low          |

---

## Perimeter Classification Rules

Controls are classified as **Internal** or **External** based on the Control ID prefix:
- **Control ID starts with "Euronext"** → **Internal** (Euronext-owned control, in Euronext perimeter)
- **Control ID starts with "CIS", "ISO", "NIST", "SOC2"** → **External** (vendor-owned/implemented)

A domain cell shows:
- **"✔ Mitigated"** (green) if all controls in that perimeter have Status = Implemented
- **"⚠ [Risk name]"** (amber) if any control has Status = Pending

---

## Data JSON Schema

See `references/data_schema.md` for the full JSON structure.
Key fields used by `generate_slide.js`:

```json
{
  "vendor":         "Vendor Name",
  "assessment_id":  "AssessmentID_2026",
  "report_date":    "February 2026",
  "service_desc":   "Short service description — deployment type — key characteristics",
  "dora_scope":     false,
  "criticality":    "Not-Critical",
  "overall_risk":   "Medium",
  "certifications": ["ISO 27001"],
  "domain_scores":  { "Cybersecurity": 6.0, "Data Management": 1.0, "IT": 5.0,
                      "Business Continuity": 3.0, "Third-Parties": 4.8 },
  "top_risks": [
    { "id": "2525", "score": 6.0, "domain": "Cybersecurity",
      "title": "Unsecure Network Threat Detection",
      "detail": "IDS/IPS signatures not regularly updated" }
  ],
  "full_register": [
    { "id": "2525", "label": "Net", "score": 6.0 }
  ],
  "mitigations": [
    { "label": "Euronext SOC Integration",
      "detail": "SOC logging/monitoring — GrayLog & Microsoft Sentinel",
      "status": "Pending" }
  ],
  "perimeter": {
    "Cybersecurity":       { "internal": { "text": "⚠ Unsecure Network\nInadequate IAM", "alert": true },
                             "external": { "text": "✔ Mitigated", "alert": false } },
    "Data Management":     { "internal": { "text": "✔ Mitigated", "alert": false },
                             "external": { "text": "✔ Mitigated", "alert": false } },
    "IT":                  { "internal": { "text": "⚠ Assets not in CMDB", "alert": true },
                             "external": { "text": "✔ Mitigated", "alert": false } },
    "Business Continuity": { "internal": { "text": "✔ Mitigated", "alert": false },
                             "external": { "text": "✔ Mitigated", "alert": false } },
    "Third-Parties":       { "internal": { "text": "⚠ Security Agreements\npending", "alert": true },
                             "external": { "text": "✔ Mitigated", "alert": false } }
  },
  "findings": [
    "All vendor controls (CIS) are **Implemented**; key Euronext controls remain **Pending** — immediate action required.",
    "Highest residual risk 6.0 in Cybersecurity — SOC integration is the critical priority.",
    "Not-Critical, Not-DORA scope — standard monitoring cadence. **Next review: Q2 2026**"
  ]
}
```

---

## Template Brand Reference

All visual constants are defined in `assets/template_constants.js`.
Colors, layout dimensions, font sizes, and shadow settings are imported from this file.
**Never hardcode hex colors or pixel values** in slide scripts — always import from the template.

Key layout (LAYOUT_16x9 = 10" × 5.625"):
- Header band: y=0 → h=0.88"
- Footer band: y=5.24"
- Left column: x=0.13" w=5.44"
- Right column: x=5.70" w=4.17"
- Content area: y=0.95" → 5.22"

See `references/template_layout.md` for full layout diagram.

---

## Quality Checklist

Before delivering the file, verify:
- [ ] Vendor name matches PDF exactly
- [ ] All 5 domain scores set (none left at default)
- [ ] Top 3 risks are the highest Residual Risk Score values
- [ ] Pending vs Implemented correctly reflects PDF controls
- [ ] DORA scope correctly set (Yes/No)
- [ ] Radar PNG regenerated with correct scores (not from a previous run)
- [ ] Footer date matches assessment date from PDF
