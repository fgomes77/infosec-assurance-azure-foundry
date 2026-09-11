---
name: ciso-executive-summary
description: >
  Generates a CISO-grade TPRM Executive Summary HTML report from OneTrust Infosec Form
  assessment PDFs. ALWAYS use this skill when the user uploads a OneTrust PDF and asks for
  a CISO report, executive summary, risk dashboard, board report, or vendor risk summary.
  Also trigger for: "generate CISO report", "create executive summary", "analyse this
  assessment for the CISO", "TPRM executive summary", "vendor risk report", "risk dashboard",
  or any mention of OneTrust assessment + CISO/executive/board/summary/report. This skill
  produces a single-file interactive HTML dashboard using the Strategic Risk Intelligence
  Dashboard template with corrected TPRM thresholds, 5-domain spider graph, dual-perimeter
  analysis, and Euronext controls register. Use this skill even for partial requests like
  "summarise this PDF" or "what's the risk posture of this vendor" when a OneTrust PDF
  is attached. Never attempt to generate a CISO executive summary without this skill.
---

# CISO Executive Summary Generator

Produces a **board-ready, single-file HTML TPRM Executive Summary** from a OneTrust
Infosec Form assessment PDF. Output follows the Strategic Risk Intelligence Dashboard
template with corrected TPRM thresholds and dual-perimeter analysis.

---

## Declarative Prompt (copy into your working context)

```
You are a Principal Security Assurance Consultant generating a Group CISO Executive
Summary from a OneTrust Infosec Form PDF. Follow these instructions precisely.

═══ PHASE 1: DATA EXTRACTION ═══

Read `references/extraction-methodology.md` for the full extraction ruleset, then
parse the uploaded PDF extracting every data point listed below. Handle OneTrust OCR
doubled-character artifacts (e.g., "Aces" → "Access", "aplication" → "application",
"Suply" → "Supply") by normalising to correct English.

Extract into a structured JSON object:

1. SUPPLIER PROFILE
   - Vendor name (exact), Organisation, Assessment ID, Template name
   - Date created, Date completed
   - Infosec Analyst Review (name + result)
   - Infosec Manager Review (name + result)
   - Stage, Status
   - DORA Scope (Yes/No)
   - Critical Supplier (Yes/No)
   - Service Criticality (Critical/Important, Important, Standard)
   - Supplier Type (from service identification section)
   - Certifications (types + validation status)

2. RISK REGISTER — for EVERY risk in the PDF:
   - Risk ID (numeric)
   - Full risk description text
   - Short title (you generate, ≤60 chars, from the description)
   - ENX L3 Taxonomy (exact text from PDF)
   - Inherent Risk Level (Low/Medium/High)
   - IT Residual Risk Score (numeric, OneTrust 1–25 scale)
   - Target Risk Score (numeric)
   - Stage (Treated / In Treatment)

3. CONTROLS — for EVERY control under each risk:
   - Control ID (exact text, e.g., "CIS 16.1-GV", "Euronext SOC")
   - Control name (full name)
   - Description (full description text)
   - Category (exact text from PDF)
   - Status (Implemented / Pending / Partially Implemented / Not Implemented)
   - Perimeter classification:
     • Control ID starts with "Euronext" → Internal (Euronext perimeter)
     • Control ID starts with "CIS", "ISO", "NIST", "SOC2", or any other
       non-Euronext prefix → External (vendor perimeter)

═══ PHASE 2: DOMAIN CLASSIFICATION ═══

Map each risk to exactly ONE of five domains using the ENX L3 Taxonomy field
AND the Control Category fields:

| Risk theme / Control categories                    | Domain             |
|----------------------------------------------------|--------------------|
| IDS/IPS, SOC, network, threat, pen test, awareness | Cybersecurity      |
| Data classification, privacy, GDPR, encryption,    |                    |
|   DLP, data flows, data retention                  | Data Management    |
| Asset inventory, CMDB, SDLC, change control,       |                    |
|   patching, software inventory                     | IT                 |
| BCM, DRP, RTO, continuity, backup, recovery        | Business Continuity|
| Supply chain, third-party, vendor, TP agreements,  |                    |
|   supplier monitoring, service provider mgmt       | Third-Parties      |

Special rules:
- If a risk has ONLY Euronext Supply Chain RM controls → Third-Parties
- If a risk spans domains, use the PREDOMINANT control category
- Access control/IAM risks → Cybersecurity
- Incident management/logging risks → Cybersecurity
- Vendor management (CIS 15.x) risks → Third-Parties

Domain Score = MAX IT Residual Risk Score among all risks in that domain.
If no risk maps to a domain, assign score 1.0.

═══ PHASE 3: THRESHOLD APPLICATION ═══

Apply these thresholds EVERYWHERE (scores, badges, bars, spider dots, header):

| Condition      | Classification | Colour         | CSS variable      |
|----------------|---------------|----------------|--------------------|
| Score > 12     | HIGH          | Red #DC2626    | --high-red         |
| Score > 4 ≤ 12 | MEDIUM        | Amber #D97706  | --medium-amber     |
| Score ≤ 4      | LOW           | Teal #007D71   | --low-teal         |

Overall Risk = classification of the MAX domain score.
Individual score badges follow the same thresholds.

Spider chart radar rings MUST be at: 4, 8, 12, 17, 25
- Ring at 4: LOW/MEDIUM boundary (teal dashed)
- Ring at 12: MEDIUM/HIGH boundary (red dashed)
- Scale maximum: 25 (OneTrust scale)
- Chart radius: 150px, pentagon geometry

═══ PHASE 4: PERIMETER ANALYSIS ═══

For each domain, determine the Internal and External perimeter status:

External (Vendor) perimeter:
- "✔ Mitigated" (green) if ALL non-Euronext controls have Status = Implemented
- "⚠ [issue]" (amber/red) if ANY non-Euronext control is not Implemented

Internal (Euronext) perimeter:
- "✔ Mitigated" (green) if ALL Euronext controls have Status = Implemented
- "⚠ [issue]" (amber/red) if ANY Euronext control is not Implemented

KEY ANALYTICAL PATTERN: If ALL residual risk gaps are caused by Internal
(Euronext) controls while External (vendor) is fully mitigated → call this out
explicitly as "All-Internal Residual Exposure" in the perimeter matrix callout.

═══ PHASE 5: INHERENT RISK RATIONALE ═══

Write a concise paragraph explaining WHY the inherent risk level is what it is,
using ONLY data from the PDF:
- Supplier type and criticality classification
- DORA scope status
- ENX L3 taxonomy distribution (count of security vs operational risks)
- Certification status
- Nature of ICT services provided
Do NOT speculate beyond the PDF data.

═══ PHASE 6: HTML REPORT GENERATION ═══

Read `references/html-template-spec.md` for the canonical template specification.
Generate a SINGLE self-contained HTML file following the Strategic Risk Intelligence
Dashboard layout. The template in `assets/template.html` is the canonical reference.

Report sections (in order):
1. HEADER — vendor name, assessment ID, completion date, template type
   + badges: Overall Risk (threshold-coloured), DORA scope, Criticality
2. KPI ROW — 5 cards: Overall Risk, Total Risks (oper/security split),
   Treated/In Treatment, Euronext Controls (Impl/Pending), Certification
3. SPIDER GRAPH + SUPPLIER PROFILE + DOMAIN BARS — two-column layout
   - Left: SVG spider with 5 rings at 4,8,12,17,25; threshold-coloured dots
   - Right top: Supplier Profile (name, type, org, criticality, DORA, cert,
     analyst, manager — NO ENX L3 Taxonomy field)
   - Right bottom: Horizontal domain score bars with threshold colours + stage chips
4. INHERENT RISK RATIONALE — teal callout box
5. RISKS WITH PENDING CONTROLS — table of In Treatment risks with linked
   pending Euronext controls
6. EURONEXT CONTROLS REGISTER — full table of ALL Euronext controls with
   status, category, perimeter chip, linked risks. Pending rows: red tint.
   Implemented rows: green tint.
7. PERIMETER MATRIX — 5-domain × 2-perimeter table + analytical callout
8. CRITICAL FINDINGS + DORA STATUS & ACTIONS — two-column bottom grid
   - Left: 3–4 finding cards with severity icons
   - Right: DORA status box + numbered action items

═══ PHASE 7: QUALITY CHECKLIST ═══

Before delivering, verify ALL of the following:
□ Vendor name matches PDF exactly
□ ALL risks from PDF are extracted (count matches)
□ ALL controls from PDF are extracted
□ IT Residual Risk Scores match PDF exactly (watch OCR artifacts)
□ Domain scores = MAX residual per domain (not average)
□ Thresholds: >12=HIGH(red), >4≤12=MEDIUM(amber), ≤4=LOW(teal)
□ Spider rings at 4, 8, 12, 17, 25 on 25-point scale
□ Score badges use correct threshold colours
□ DORA scope correctly extracted (Yes/No)
□ Criticality correctly extracted
□ Certification type and status correct
□ Perimeter: Euronext=Internal, CIS/ISO/NIST=External
□ Pending vs Implemented correctly reflects PDF control statuses
□ Inherent risk rationale uses only PDF data
□ No ENX L3 Taxonomy field in Supplier Profile card
□ Footer date matches current date
□ HTML is a single self-contained file with embedded CSS and SVG
□ All fonts load from Google Fonts CDN
□ Print-friendly CSS included
```

---

## Workflow (execute in order)

### Step 1 — Read reference files

```
view /mnt/skills/user/ciso-executive-summary/references/extraction-methodology.md
view /mnt/skills/user/ciso-executive-summary/references/html-template-spec.md
```

### Step 2 — Extract PDF data

Parse the uploaded OneTrust PDF following the extraction methodology. Build the
complete JSON data object in memory. Handle OCR doubled-character artifacts.

Cross-check: count total risks, total controls, total Euronext controls.
Verify every IT Residual Risk Score against the PDF.

### Step 3 — Classify domains and compute scores

Map each risk to one of the 5 domains. Compute domain scores (MAX residual per domain).
Apply threshold classification to overall risk and each domain.

### Step 4 — Analyse perimeters

For each domain, classify all controls as Internal or External. Determine the
perimeter status (Mitigated vs Alert) for each domain × perimeter combination.
Identify the all-internal exposure pattern if applicable.

### Step 5 — Generate HTML report

Read the canonical template from `assets/template.html`. Generate the complete
single-file HTML report, replacing all template placeholders with extracted data.
All SVG spider chart geometry must be computed from the actual domain scores.

Save to: `/home/claude/<VendorName>_CISO_ExecSummary.html`

### Step 6 — Generate PDF from HTML

Use Playwright/Chromium to render the HTML to a pixel-identical PDF:

```bash
python3 scripts/html_to_pdf.py /home/claude/<VendorName>_CISO_ExecSummary.html /home/claude/<VendorName>_CISO_ExecSummary.pdf
```

Settings: A3 landscape, print backgrounds, 10mm margins.

### Step 7 — Generate PPTX (G.CISO Governance Meeting Report)

Read `references/pptx-template-spec.md` for the full PPTX layout specification.

**7a. Render HTML sections as PNGs:**

Using Playwright, render the HTML report at 1400px viewport width and clip 4 sections:
- S3: KPI row + Spider + Profile + Domain bars (y:0, h:~820px)
- S4: Inherent risk rationale + Risks table (y:~820, h:~550px)
- S5: Euronext controls register + Perimeter matrix (y:~1370, h:~700px)
- S6: Critical Findings + DORA/Actions (y:~2070, h:~520px)

Adjust y-offsets and heights based on actual page height (varies by vendor risk count).

**7b. Build PPTX with pptxgenjs:**

Generate an 8-slide PPTX following the Euronext G.CISO TPRM Governance template:

| Slide | Content |
|-------|---------|
| 1 | Title: "Current TP Risks above risk appetite" (dark teal background) |
| 2 | Assessment summary table + key findings bullets (generated from data) |
| 3 | TPRM Executive Summary screenshot (s3_exec_summary.png) |
| 4 | Open Risks screenshot (s4_open_risks.png) |
| 5 | Mitigation Controls screenshot (s5_controls_perimeter.png) |
| 6 | TPRM Summary continuation screenshot (s6_findings_actions.png) |
| 7 | Euronext closing slide |
| 8 | Disclaimer |

Layout: LAYOUT_WIDE (13.33" × 7.5"). Brand: teal accent bar + EURONEXT footer + PRIVATE label.

Save to: `/home/claude/<VendorName>_CISO_TPRM_Governance.pptx`

### Step 8 — Copy all outputs and present

```bash
cp /home/claude/<VendorName>_CISO_ExecSummary.html /mnt/user-data/outputs/
cp /home/claude/<VendorName>_CISO_ExecSummary.pdf /mnt/user-data/outputs/
cp /home/claude/<VendorName>_CISO_TPRM_Governance.pptx /mnt/user-data/outputs/
```

Call `present_files` with all three output paths.

### Step 9 — Provide CISO briefing summary

After presenting the files, provide a concise text summary covering:
- Overall risk classification and max residual
- Domain scores with threshold colours
- Key finding: where the residual risk sits (Internal vs External)
- DORA status and immediate action required
- Next reassessment target

---

## Output Deliverables (3 files per vendor)

| File | Format | Purpose |
|------|--------|---------|
| `<Vendor>_CISO_ExecSummary.html` | HTML | Interactive dashboard — web viewing |
| `<Vendor>_CISO_ExecSummary.pdf` | PDF | Print-ready — A3 landscape, exact HTML layout |
| `<Vendor>_CISO_TPRM_Governance.pptx` | PPTX | G.CISO Governance Meeting — 8-slide Euronext branded deck |

---

## Risk Threshold Reference (supersedes ALL other threshold definitions)

| Score range | Classification | Badge colour | Bar gradient              |
|-------------|---------------|-------------|---------------------------|
| > 12        | HIGH          | #DC2626 red | #EF4444 → #DC2626         |
| > 4 and ≤ 12| MEDIUM        | #D97706 amber| #FBBF24 → #D97706        |
| ≤ 4         | LOW           | #007D71 teal| #00B4A0 → #007D71         |

Spider chart rings: 4, 8, 12, 17, 25 (pentagon geometry, radius 150px, scale /25×150)

---

## Files in this skill

| File | Purpose |
|------|---------|
| `SKILL.md` | This file — workflow, declarative prompt, thresholds |
| `references/extraction-methodology.md` | PDF parsing rules, OCR handling, field mapping |
| `references/html-template-spec.md` | Canonical HTML template specification |
| `references/pptx-template-spec.md` | PPTX slide structure, layout, clipping coordinates |
| `scripts/html_to_pdf.py` | Playwright HTML → PDF converter |
| `scripts/render_sections.py` | Playwright HTML → section PNGs for PPTX |
| `scripts/generate_pptx_template.js` | pptxgenjs PPTX generator (reference implementation) |
| `assets/template.html` | Reference HTML template (canonical) |
