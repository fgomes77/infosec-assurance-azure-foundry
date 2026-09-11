# OneTrust Infosec Form PDF — Extraction Methodology

## Overview

OneTrust Infosec Form PDFs follow a consistent structure. This document defines
the exact extraction rules for converting a PDF into the structured JSON required
by the CISO Executive Summary generator.

---

## 1. PDF Structure Map

OneTrust Infosec Form PDFs contain these sections in order:

```
Page 1:     Vendor block + Assessment details block
Section 1:  Supplier and service identification (DORA Scope, Criticality)
Section 12: Certification Validation
Sections:   Risk blocks (Operational + Security categories)
```

### 1.1 Vendor Block (Page 1)

| Field | Location | Extraction rule |
|-------|----------|-----------------|
| Vendor Name | `Name (...)` after "Vendor" heading | Text inside parentheses |
| Assessment ID | After vendor name on same line | Second value after pipe |
| Stage | `Stage` field | Exact text (e.g., "Completed") |
| Organisation | `Organization` field | Exact text |
| Status | `Status` field | Exact text (e.g., "Active") |

### 1.2 Assessment Details Block (Page 1)

| Field | Location | Extraction rule |
|-------|----------|-----------------|
| Template | `Template` field | Exact text (e.g., "Infosec Form") |
| Date created | `Date created` field | DD/MM/YYYY HH:MM format |
| Date completed | `Date completed` field | DD/MM/YYYY HH:MM format |
| Analyst Review | `Result comments` → first line | "Name - Result" pattern |
| Manager Review | `Result comments` → second line | "Name - Result" pattern |

### 1.3 Section 1: Supplier & Service Identification

| Field | Pattern | Values |
|-------|---------|--------|
| DORA Scope | "DORA Scope" → "Response" | Yes / No |
| Critical Supplier | "Is this a critical supplier?" → "Response" | Yes / No |
| Service Criticality | "Service Criticality" → "Response" | Critical/Important, Important, Standard |
| Supplier Type | First response block | Extract from pipe-separated metadata |

### 1.4 Section 12: Certification Validation

| Field | Pattern | Values |
|-------|---------|--------|
| Certification Status | "Are the certifications valid and in scope?" | "Certifications OK" / "Certifications Not OK" |
| Certification Types | "Type of certifications" → "Response" | ISO 27001, SOC2, etc. |

---

## 2. Risk Block Extraction

Each risk block in the PDF follows this exact structure:

```
Risk: [ID] - [Description text]

Type          ENX L3 Taxonomy      Inherent risk level    IT Residual Risk Score    Target risk score    Stage
[value]       [value]              [value]                [value]                   [value]              [value]

Controls
Control ID    Control name    Description    Category    Status
[row 1]
[row 2]
...
```

### 2.1 Risk Fields

| Field | Extraction rule |
|-------|-----------------|
| Risk ID | Numeric value after "Risk:" before the dash |
| Description | Full text after the dash, up to the next table |
| ENX L3 Taxonomy | Exact text from taxonomy column |
| Inherent Risk Level | Low / Medium / High |
| IT Residual Risk Score | Numeric value (may be integer or decimal) |
| Target Risk Score | Numeric value |
| Stage | "Treated" or "In Treatment" |

### 2.2 Control Fields

| Field | Extraction rule |
|-------|-----------------|
| Control ID | First column — exact text (e.g., "CIS 4.6-PR", "Euronext SOC") |
| Control Name | Second column — full control name |
| Description | Third column — full description text |
| Category | Fourth column — exact category text |
| Status | Fifth column — "Implemented", "Pending", "Partially Implemented", "Not Implemented" |

---

## 3. OCR Artifact Handling

OneTrust PDF exports contain systematic OCR artifacts where characters are doubled
or corrupted. Apply these corrections during extraction:

### 3.1 Common Doubled-Character Patterns

| OCR artifact | Correct text |
|-------------|-------------|
| Aces / Acess | Access |
| aplication | application |
| Suply | Supply |
| Comunication / Comunicating | Communication / Communicating |
| decomisioning | decommissioning |
| comitments | commitments |
| reasesment | reassessment |
| Clasify | Classify |
| Conecting / Transmiting | Connecting / Transmitting |
| Asign | Assign |
| adendum | addendum |
| acount | account |
| recomendation | recommendation |
| Aset / asets | Asset / assets |

### 3.2 Handling Rules

1. **Risk descriptions**: Normalise to correct English but preserve meaning exactly.
2. **Control IDs**: Preserve EXACTLY as printed (e.g., "CIS 4.6-PR" stays as-is).
3. **Control names and descriptions**: Normalise spelling but preserve meaning.
4. **Numeric scores**: Extract as-is. If a score appears corrupted, flag for manual review.
5. **Page number artifacts**: Remove trailing "X / Y" page numbers from descriptions
   (e.g., "...accountability. 3 / 1" → "...accountability.").

---

## 4. Perimeter Classification Rules

Controls are classified into perimeters based on the Control ID prefix:

| Control ID prefix | Perimeter | Owner |
|-------------------|-----------|-------|
| `Euronext` (any suffix) | **Internal** | Euronext NV |
| `CIS` (any suffix) | **External** | Vendor |
| `ISO` or numeric ISO ref (e.g., "5.22") | **External** | Vendor |
| `NIST` (any suffix) | **External** | Vendor |
| `SOC2` (any suffix) | **External** | Vendor |
| Any other prefix | **External** | Vendor (default) |

### 4.1 Euronext Control ID Patterns

Known Euronext control ID patterns from production assessments:

| Control ID | Full Name | Category |
|-----------|-----------|----------|
| Euronext IAM | IAM user lifecycle + PAM tools integration | Access Control |
| Euronext SOC | SOC logging and monitoring tools integration | Incident Management |
| Euronext AET | Pen test / vulnerability report review | Security Assessment |
| Euronext CTI | CTI continuous monitoring integration | Threat Management |
| Euronext BSC | CMDB integration | Asset Management |
| Euronext Risk & BCM Agreements | Risk & BCM requirements sharing | Supply Chain Risk Mgmt |
| Euronext Security Agreements | Cyber security requirements sharing | Supply Chain Risk Mgmt |
| Euronext Compliance Agreements | Compliance requirements sharing | Supply Chain Risk Mgmt |
| Euronext Finance Agreements | Finance requirements sharing | Supply Chain Risk Mgmt |
| Euronext Privacy Agreements | Privacy requirements sharing | Supply Chain Risk Mgmt |

---

## 5. Domain Classification Rules

Map each risk to exactly ONE of five security domains:

### 5.1 Primary Mapping (ENX L3 Taxonomy)

| ENX L3 Taxonomy value | Default domain |
|----------------------|----------------|
| Third-party security (ICT) | Use control categories to determine |
| Third-Party lifecycle management (ICT) | Use control categories to determine |

### 5.2 Secondary Mapping (Control Categories)

When ENX L3 taxonomy alone is ambiguous, use the predominant control category:

| Control category keywords | Domain |
|--------------------------|--------|
| Security Operations, Network Intrusion, Threat | Cybersecurity |
| Access Control, IAM, PAM, Authentication | Cybersecurity |
| Incident Management, Logging | Cybersecurity |
| Awareness And Training | Cybersecurity |
| Data Security, Data Classification, DLP, Encryption | Data Management |
| Asset Management, CMDB, Software Inventory | IT |
| Secure Development, SDLC, Change Control | IT |
| Continuity and Resilience, Backup, Recovery, BCM | Business Continuity |
| Supply Chain Risk Management, Vendor Management | Third-Parties |
| Risk Management (when tied to TP agreements) | Third-Parties |

### 5.3 Disambiguation Rules

1. If a risk has controls spanning multiple domains, assign to the domain
   with the MOST controls.
2. If tied, assign to the domain of the HIGHEST-scored control category.
3. If a risk has ONLY "Supply Chain Risk Management" controls → Third-Parties.
4. CIS 15.x (vendor management) → Third-Parties.
5. CIS 16.x (secure development) + threat modeling → IT (unless TP agreements dominate).
6. CIS 17.x (incident response) → Cybersecurity.
7. CIS 14.x (awareness/training) → Cybersecurity.
8. CIS 3.x (data security) → Data Management.
9. CIS 11.x (data recovery/backup) → Business Continuity.

### 5.4 Domain Score Computation

```
Domain Score = MAX(IT Residual Risk Score) for all risks in that domain
```

If a domain has zero risks mapped to it, assign score = 1.0 (minimal exposure).

---

## 6. Output JSON Schema

```json
{
  "supplier": {
    "name": "string",
    "assessment_id": "string",
    "organization": "string",
    "template": "string",
    "date_created": "string",
    "date_completed": "string",
    "analyst_review": "string",
    "manager_review": "string",
    "stage": "string",
    "status": "string",
    "supplier_type": "string",
    "dora_scope": "boolean",
    "critical_supplier": "boolean",
    "service_criticality": "string",
    "certifications": ["string"],
    "certifications_status": "string"
  },
  "risk_categories": {
    "operational": "number",
    "security": "number"
  },
  "risks": [
    {
      "id": "string",
      "description": "string",
      "short_title": "string (≤60 chars)",
      "enx_l3_taxonomy": "string",
      "inherent_risk_level": "string",
      "it_residual_risk_score": "number",
      "target_risk_score": "number",
      "stage": "string",
      "domain": "string",
      "controls": [
        {
          "id": "string",
          "name": "string",
          "description": "string",
          "category": "string",
          "status": "string",
          "perimeter": "Internal | External"
        }
      ]
    }
  ],
  "domain_scores": {
    "Cybersecurity": "number",
    "Data Management": "number",
    "IT": "number",
    "Business Continuity": "number",
    "Third-Parties": "number"
  },
  "overall_risk": "HIGH | MEDIUM | LOW",
  "euronext_controls": [
    {
      "id": "string",
      "name": "string",
      "category": "string",
      "status": "string",
      "linked_risk_ids": ["string"]
    }
  ],
  "risks_with_pending_controls": [
    {
      "risk_id": "string",
      "short_title": "string",
      "residual_score": "number",
      "stage": "string",
      "domain": "string",
      "pending_controls": [{ "id": "string", "status": "string" }]
    }
  ],
  "perimeter_matrix": {
    "Cybersecurity": { "internal": { "text": "string", "alert": "boolean" }, "external": { "text": "string", "alert": "boolean" } },
    "Data Management": { "internal": {}, "external": {} },
    "IT": { "internal": {}, "external": {} },
    "Business Continuity": { "internal": {}, "external": {} },
    "Third-Parties": { "internal": {}, "external": {} }
  }
}
```
