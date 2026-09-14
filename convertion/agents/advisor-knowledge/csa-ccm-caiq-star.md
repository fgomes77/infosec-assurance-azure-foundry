# CSA Cloud Controls Matrix v4, CAIQ v4 and STAR — Review Reference

*Advisor knowledge reference — authored 2026-09-12 to ground the persona
domain "CSA CCM/CAIQ" for tpa-evidence-analyzer, tpsrca and the advisor.
Verify against the Cloud Security Alliance publications (CCM v4.0.x,
CAIQ v4, STAR programme) before citing.*

## 1. CCM v4 — 17 domains, 197 control specifications

| Id | Domain | Controls | Assurance focus |
|---|---|---|---|
| A&A | Audit & Assurance | 6 | independent audits, remediation |
| AIS | Application & Interface Security | 7 | secure SDLC, API security |
| BCR | Business Continuity Mgmt & Operational Resilience | 11 | BIA, DR testing, backup |
| CCC | Change Control & Configuration Mgmt | 9 | change authorisation, baselines |
| CEK | Cryptography, Encryption & Key Mgmt | 21 | key lifecycle, customer-managed keys |
| DCS | Datacenter Security | 15 | physical, environmental, asset |
| DSP | Data Security & Privacy Lifecycle Mgmt | 19 | classification, retention, residency |
| GRC | Governance, Risk & Compliance | 8 | programme, policy, risk mgmt |
| HRS | Human Resources | 13 | screening, training, off-boarding |
| IAM | Identity & Access Mgmt | 16 | MFA, least privilege, reviews |
| IPY | Interoperability & Portability | 4 | exit, data portability |
| IVS | Infrastructure & Virtualization Security | 9 | segmentation, hardening |
| LOG | Logging & Monitoring | 13 | audit logs, SIEM, clock sync |
| SEF | Security Incident Mgmt, E-Discovery & Cloud Forensics | 8 | IR plan, notification, forensics |
| STA | Supply Chain Mgmt, Transparency & Accountability | 14 | fourth parties, SLAs, shared responsibility |
| TVM | Threat & Vulnerability Mgmt | 10 | patching, pentests, malware |
| UEM | Universal Endpoint Mgmt | 14 | endpoint controls |

Each control carries an id `DOM-NN`, a specification, and in the CCM
workbook the **implementation guidance**, **auditing guidelines** and the
**shared-responsibility model (SSRM)** column (CSP-owned / CSC-owned /
shared / third-party). Mappings published by CSA: ISO/IEC 27001/27002,
27017, 27018, NIST SP 800-53 r5, PCI DSS, AICPA TSC, CIS v8 and others.

## 2. CAIQ v4

- One yes/no/NA question per CCM control (≈261 questions), with columns:
  CSP CAIQ answer, SSRM control ownership, implementation description,
  CSC responsibilities. Version must match CCM v4 (CAIQ v3.1 = CCM v3.0.1
  = outdated).
- Reading rubric: **No** or **NA without justification** on IAM, CEK,
  DSP, LOG, SEF, STA, BCR, TVM = candidate findings; free-text
  implementation descriptions are self-attestation unless STAR Level 2
  backs them; "shared" ownership implies a Euronext-side control to
  assign.
- Scoring for TPRM: count of No/NA per domain; weight domains touching
  the Euronext service (data classes, connectivity); treat missing
  answers as No; cite `DOM-NN` ids in findings.

## 3. STAR registry

| Level | Meaning | Reliance |
|---|---|---|
| Level 1 — Self-assessment | CAIQ published on the STAR registry (annual renewal) | Self-attestation |
| Level 2 — Third-party audit | STAR Certification (ISO 27001 + CCM, by accredited CB) or STAR Attestation (SOC 2 + CCM, by CPA) | Independent assurance |
| STAR Continuous | continuous monitoring components | Emerging |

Validate the entry on the public STAR registry (supplier name only), note
the level, date and scope, and prefer the underlying certificate/report.

## 4. Mapping shortcuts

| CCM domain | ISO 27001:2022 Annex A | ISO 27017/27018 | DORA |
|---|---|---|---|
| STA | 5.19–5.23 | 27017 CLD.6.3.1 shared roles | Art. 28–30 |
| IPY | 5.23, 5.30 | 27017 CLD.12.4.5 / portability | Art. 28(8), 30(3)(f) exit |
| DSP | 5.12–5.14, 8.10–8.12 | 27018 PII controls | Art. 9(3), 30(2)(b) location |
| CEK | 8.24 | 27017 CLD.10.1 | Art. 9(3)(b) |
| LOG | 8.15–8.17 | 27017 CLD.12.4.5 | Art. 10 |
| BCR | 5.29–5.30, 8.13–8.14 | — | Art. 11–12 |
| SEF | 5.24–5.28 | 27017 16.1 | Art. 17–19 |
