# PCI DSS v4.0.1 — Supplier Assurance Reference

*Advisor knowledge reference — authored 2026-09-12; restores PCI DSS
coverage that the previous environment treated as in scope. Relevant only
where a supplier stores, processes or transmits cardholder data (CHD) or
can affect its security (payment processors, acquirers' gateways, PSPs,
hosting providers of CDE components). Verify against the PCI SSC
Document Library before citing.*

## 1. The 12 requirements (v4.0.1, effective 31 Mar 2024; future-dated
requirements mandatory from 31 Mar 2025)

| Goal | Req. | Title |
|---|---|---|
| Build and maintain a secure network and systems | 1 | Install and maintain network security controls |
| | 2 | Apply secure configurations to all system components |
| Protect account data | 3 | Protect stored account data |
| | 4 | Protect CHD with strong cryptography during transmission over open, public networks |
| Vulnerability management | 5 | Protect all systems and networks from malicious software |
| | 6 | Develop and maintain secure systems and software |
| Strong access control | 7 | Restrict access to system components and CHD by business need to know |
| | 8 | Identify users and authenticate access to system components |
| | 9 | Restrict physical access to CHD |
| Monitor and test | 10 | Log and monitor all access to system components and CHD |
| | 11 | Test security of systems and networks regularly |
| Information security policy | 12 | Support information security with organisational policies and programmes — **12.8** manage TPSP risk (list, due diligence, written agreements, monitoring compliance at least annually); **12.9** TPSPs acknowledge responsibility in writing and provide status/responsibility information on request |

## 2. Validation documents

| Document | Who | What it proves |
|---|---|---|
| **AOC** (Attestation of Compliance) | Merchant or service provider, signed by QSA/ISA and executive | Summary of the assessment: entity, services assessed, date, result (compliant / not), assessor |
| **ROC** (Report on Compliance) | Level 1 service providers / merchants, by QSA | Full assessment detail — rarely shared; request the AOC |
| **SAQ** (Self-Assessment Questionnaire) | Smaller merchants/providers | Self-attestation; SAQ D-SP for service providers |
| **ASV scan attestation** | Approved Scanning Vendor | Quarterly external vulnerability scans (Req. 11.3.2) |
| Responsibility matrix | TPSP | Which requirements the TPSP covers vs the customer (Req. 12.8.5) |

Service-provider levels (card brands): Level 1 (>300k transactions/yr or
brand-designated) → annual ROC by QSA; Level 2 → annual SAQ D-SP.

## 3. Reading an AOC

1. Part 1: legal entity name, DBA, contact — must match the contracted
   supplier.
2. Part 2: **services assessed** and services NOT assessed; facilities /
   locations; **date of assessment**; assessor; whether the description
   of "in-scope services" covers what Euronext uses.
3. Part 3: overall result **Compliant** / Non-compliant / Compliant with
   legal exception; signatures; requirements marked "Not applicable" or
   "Not tested".
4. Validity: AOC dated within 12 months; ASV scans quarterly; re-assess
   on scope change.
5. Verify listing on the card brands' registries of validated service
   providers where applicable (public terms only).

## 4. Assurance mapping

| PCI element | ISO 27001:2022 Annex A | DORA | Other |
|---|---|---|---|
| Req. 12.8 / 12.9 TPSP management | 5.19–5.22 | Art. 28–30 | NIST CSF GV.SC |
| Req. 3–4 cryptography | 8.24 | Art. 9(3)(b), (4)(d) | CIS 3 |
| Req. 6 secure development | 8.25–8.29 | Art. 9(4)(e) | OWASP ASVS |
| Req. 10 logging | 8.15 | Art. 10 | CIS 8 |
| Req. 11 testing | 8.8, 8.29 | Art. 24–26 | CIS 7, 18 |

## 5. Verdict pattern

Compliant AOC (≤12 months, scope covers the service, responsibility
matrix received) → **Adequate**; expired/limited scope → **Adequate with
actions**; no AOC where CHD is handled → **Inadequate**.
