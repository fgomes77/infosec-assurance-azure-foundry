---
name: dpia
description: "Analyzes OneTrust third-party assessment PDF reports and generates InfoSec TPA Reports in DOCX format for DPO team review. Use this skill when: (1) User uploads an OneTrust vendor/supplier assessment PDF, (2) User requests a DPO report, DPIA report, or InfoSec TPA report from an assessment, (3) User needs to extract risks, controls, and implementation status from third-party assessments, (4) User mentions OneTrust, vendor monitoring, supplier assessment, or third-party risk assessment reports."
---

# DPIA - InfoSec TPA Report Generator for DPO Team

Generate professional Word documents from OneTrust third-party assessment PDFs, extracting risks, controls, implementation status, and mapping to ISO 27001 security domains.

## Quick Start

1. Parse the OneTrust PDF to extract assessment data
2. Run `node scripts/generate_report.js` with extracted JSON data
3. Present the generated DOCX to user

## PDF Parsing Rules

### Assessment Header Data
Extract from page 1:
- **Supplier**: From "Name" field (vendor name before "_monitoring")
- **Organization**: From "Organization" field
- **DORA Scope**: From section 1.3
- **Service Criticality**: From section 1.4 (Critical/Important, etc.)
- **Certifications**: From section 12 (ISO 27001, SOC 2, ISAE 3402, etc.)
- **Assessment Date**: From "Date created" and "Completed date"
- **Residual Risk Level**: From "Residual risk level"
- **Residual Risk Score**: From "Residual risk score"
- **Result**: From "Result" (Approved/Conditional/Rejected)
- **Analyst/Manager**: From "Result comments"

### Risk Extraction
For each risk in PDF, extract:

| Field | Location |
|-------|----------|
| Risk Description | "Risk description" text |
| Risk Category | Security / Operational |
| Inherent Risk Score/Level | "Inherent risk score" (e.g., "12-Medium") |
| Target/Residual Score | "Target risk score" (e.g., "4-Low") |
| Stage | Treated / Triage / Open |
| Treatment Plan | "Treatment plan" text |

### Implementation Status Logic

| Residual Level | Stage | Status |
|----------------|-------|--------|
| Zero | Treated | Implemented |
| Low | Treated | Implemented |
| Medium | Treated/Triage | Pending |
| High | Open | Not Doing |

For monitoring assessments with "Residual risk level: Zero" and "Result: Approved", all controls = **Implemented**.

## Report Structure

### Section 1: Executive Summary
- Supplier info table (4x3 grid)
- **"Security measures in place to protect identifiable information:"** paragraph
- **Card-style statistics** with 4 boxes:
  - Total Risks
  - Total Controls
  - Implemented (count and %)
  - Pending / Not Doing (count and %)

### Section 2: Risk Register with Control Implementation Status
- Status legend row (Implemented=Green, Pending=Yellow, Not Doing=Red)
- Main table columns (NO Risk ID, NO Control ID):
  - **Inherent Risk** (Score-Level format, e.g., "12-Medium") - FIRST
  - **Residual Risk** (Score-Level format, e.g., "4-Low") - SECOND
  - **Risk Title** (merged for multiple controls)
  - **Control Name**
  - **Responsible** (Supplier or Euronext NV)
  - **Status** (Implemented/Pending/Not Doing)
  - **Due Date** (2 months if Pending, "N/A" otherwise)

### Section 3: InfoSec TPRM Conclusion
**"The security controls implemented are:"** followed by bold ISO 27001 domains:
- Information Security Policies / processes
- Organization of information security
- Human resources security
- Asset management
- Access control
- Cryptography
- Physical and environmental security
- Operations security
- Communications security
- System acquisition, development and maintenance
- Information security incident management
- Information security aspects of business continuity management
- Compliance

**Note:** Only list domains where controls are Implemented. Do not list domains for "Not Doing" controls.

- Risk Rating table (LOW/MODERATE/HIGH) - single row only
- Approval line (Analyst and Manager only, no DPO Review)

## Due Date Logic

| Status | Due Date Value |
|--------|----------------|
| Implemented | N/A |
| Pending | [Current date + 2 months] |
| Not Doing | N/A |

## Annexes

### First Annex: Five-Column Summary Table
| List of All Risks Identified | List of All Controls | List of all Status | List of all Responsable | List of All Due Dates |
|------------------------------|----------------------|--------------------|-----------------------|-----------------------|
| Risk titles | Unique control names | Implemented/Pending/Not Doing | Oracle Portugal/Euronext NV | N/A or DD/MM/YYYY |

### Annex 1: Privacy Issues & Risks
**IDENTIFIED PRIVACY ISSUES AND ASSOCIATED RISKS**

| REF | PRIVACY ISSUE | RAG | RISKS TO INDIVIDUAL(S) | COMPLIANCE RISK | CORPORATE RISK |
|-----|---------------|-----|----------------------|-----------------|----------------|
| PR3 | KEEPING THE PERSONAL DATA SAFE AND SECURE (analysis based on InfoSec assessment) + all risks listed | 6 MEDIUM | Breach of articles 5, 24 and 32 of the GDPR | Fines - article 83 of the GDPR | Fines - article 83 of the GDPR |

### Annex 2: Proposed Risk Solutions and Mitigating Actions
**PROPOSED RISK SOLUTIONS AND MITIGATING ACTIONS**

| REF | RISK | RAG | SOLUTION/MITIGATING ACTIONS | RESULT | OUTCOME | RAG |
|-----|------|-----|----------------------------|--------|---------|-----|
| PR3 | KEEPING THE PERSONAL DATA SAFE AND SECURE | 6 (Yellow) | All unique controls listed | Reduced | N/A | 4 LOW (Green) |

### Annex 3: Action Plan
**ACTION PLAN**

| REF | SOLUTION/MITIGATING ACTIONS | OWNER | STATUS | DUE DATE |
|-----|----------------------------|-------|--------|----------|
| PR_3 | All unique controls listed | Responsible party for each | Implemented/Pending/Not Doing | N/A or DD/MM/YYYY |

## ISO 27001 Control Domain Mapping

Map risks to these domains (see `references/iso27001_domains.md` for keywords):

1. **Information Security Policies / processes**
2. **Organization of information security**
3. **Human resources security**
4. **Asset management**
5. **Access control**
6. **Cryptography**
7. **Physical and environmental security**
8. **Operations security**
9. **Communications security**
10. **System acquisition, development and maintenance**
11. **Information security incident management**
12. **Information security aspects of business continuity management**
13. **Compliance**

In the conclusion, **bold the domain names** when listing implemented controls.

## Generating the Report

```bash
node scripts/generate_report.js
```

Edit the data object in the script with extracted assessment data before running.

## Output Formatting

### Colors (Hex)
- Euronext Teal: #008D7F
- Light Gray: #F0F0F0
- Implemented: #C6EFCE
- Pending: #FFEB9C
- Not Doing: #FFC7CE

### Page Setup
- Orientation: Portrait
- Size: A4 (11906 x 16838 twips / 210mm x 297mm)
- Margins: 720 twips
- Font: Arial

### Output Path
`/mnt/user-data/outputs/InfoSec_TPA_Report_[SupplierName]_[Year].docx`
