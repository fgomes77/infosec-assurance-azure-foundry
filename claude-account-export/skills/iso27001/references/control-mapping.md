# ISO/IEC 27001 Control Mapping — 2013 ↔ 2022 Transition Reference

*Reconstructed reference — regenerated on 2026-09-11 to replace a file missing from the original skill upload; verify against the official ISO publications before relying on citations.*

This mapping follows the correspondence tables published in **ISO/IEC 27002:2022 Annex B** (B.1: 2022→2013; B.2: 2013→2022). Key facts:

- **No 2013 control was deleted without a successor** — all 114 were carried forward, merged or absorbed.
- **24 controls were merged** from 57 predecessor controls; **58 carried over** essentially one-to-one (renumbered/retitled); **11 are genuinely new** in 2022.
- One 2013 control (A.18.2.3 Technical compliance review) was **split** — its substance now sits in both 5.36 and 8.8.
- All 2013 certificates expired by **October 2025**; any residual 2013 documentation encountered today is legacy material to be migrated.

---

## The 11 New 2022 Controls (No 2013 Predecessor)

| 2022 Control | Title | Why it was added |
|--------------|-------|------------------|
| 5.7 | Threat intelligence | Formalises collection/analysis of threat information feeding risk assessment |
| 5.23 | Information security for use of cloud services | Cloud acquisition, shared responsibility and exit strategy |
| 5.30 | ICT readiness for business continuity | ICT continuity planning and testing tied to BC objectives (RTO/RPO) |
| 7.4 | Physical security monitoring | Continuous surveillance/detection of unauthorised physical access |
| 8.9 | Configuration management | Security baselines, configuration enforcement and drift detection |
| 8.10 | Information deletion | Deletion of information no longer required (retention alignment) |
| 8.11 | Data masking | Masking/pseudonymisation/anonymisation, esp. PII in non-production |
| 8.12 | Data leakage prevention | DLP measures on systems, networks and devices handling sensitive data |
| 8.16 | Monitoring activities | Anomaly monitoring of networks/systems/applications (SIEM-style) |
| 8.23 | Web filtering | Managed access to external websites to reduce malicious exposure |
| 8.28 | Secure coding | Secure coding principles across the development toolchain |

These require **fresh risk-treatment decisions and new evidence** — they cannot be evidenced by re-labelling old artefacts.

---

## Full 2022 → 2013 Correspondence Table

**Theme 5 — Organizational**

| 2022 | Title (2022) | 2013 predecessor(s) | Type |
|------|-------------|---------------------|------|
| 5.1 | Policies for information security | 5.1.1, 5.1.2 | Merged |
| 5.2 | Information security roles and responsibilities | 6.1.1 | Carried |
| 5.3 | Segregation of duties | 6.1.2 | Carried |
| 5.4 | Management responsibilities | 7.2.1 | Carried |
| 5.5 | Contact with authorities | 6.1.3 | Carried |
| 5.6 | Contact with special interest groups | 6.1.4 | Carried |
| 5.7 | Threat intelligence | — | **New** |
| 5.8 | Information security in project management | 6.1.5, 14.1.1 | Merged |
| 5.9 | Inventory of information and other associated assets | 8.1.1, 8.1.2 | Merged |
| 5.10 | Acceptable use of information and other associated assets | 8.1.3, 8.2.3 | Merged |
| 5.11 | Return of assets | 8.1.4 | Carried |
| 5.12 | Classification of information | 8.2.1 | Carried |
| 5.13 | Labelling of information | 8.2.2 | Carried |
| 5.14 | Information transfer | 13.2.1, 13.2.2, 13.2.3 | Merged |
| 5.15 | Access control | 9.1.1, 9.1.2 | Merged |
| 5.16 | Identity management | 9.2.1 | Carried |
| 5.17 | Authentication information | 9.2.4, 9.3.1, 9.4.3 | Merged |
| 5.18 | Access rights | 9.2.2, 9.2.5, 9.2.6 | Merged |
| 5.19 | Information security in supplier relationships | 15.1.1 | Carried |
| 5.20 | Addressing information security within supplier agreements | 15.1.2 | Carried |
| 5.21 | Managing information security in the ICT supply chain | 15.1.3 | Carried |
| 5.22 | Monitoring, review and change management of supplier services | 15.2.1, 15.2.2 | Merged |
| 5.23 | Information security for use of cloud services | — | **New** |
| 5.24 | Incident management planning and preparation | 16.1.1 | Carried |
| 5.25 | Assessment and decision on information security events | 16.1.4 | Carried |
| 5.26 | Response to information security incidents | 16.1.5 | Carried |
| 5.27 | Learning from information security incidents | 16.1.6 | Carried |
| 5.28 | Collection of evidence | 16.1.7 | Carried |
| 5.29 | Information security during disruption | 17.1.1, 17.1.2, 17.1.3 | Merged |
| 5.30 | ICT readiness for business continuity | — | **New** |
| 5.31 | Legal, statutory, regulatory and contractual requirements | 18.1.1, 18.1.5 | Merged |
| 5.32 | Intellectual property rights | 18.1.2 | Carried |
| 5.33 | Protection of records | 18.1.3 | Carried |
| 5.34 | Privacy and protection of PII | 18.1.4 | Carried |
| 5.35 | Independent review of information security | 18.2.1 | Carried |
| 5.36 | Compliance with policies, rules and standards | 18.2.2, 18.2.3 | Merged (18.2.3 split with 8.8) |
| 5.37 | Documented operating procedures | 12.1.1 | Carried |

**Theme 6 — People**

| 2022 | Title (2022) | 2013 predecessor(s) | Type |
|------|-------------|---------------------|------|
| 6.1 | Screening | 7.1.1 | Carried |
| 6.2 | Terms and conditions of employment | 7.1.2 | Carried |
| 6.3 | Information security awareness, education and training | 7.2.2 | Carried |
| 6.4 | Disciplinary process | 7.2.3 | Carried |
| 6.5 | Responsibilities after termination or change of employment | 7.3.1 | Carried |
| 6.6 | Confidentiality or non-disclosure agreements | 13.2.4 | Carried |
| 6.7 | Remote working | 6.2.2 | Carried (teleworking, broadened) |
| 6.8 | Information security event reporting | 16.1.2, 16.1.3 | Merged |

**Theme 7 — Physical**

| 2022 | Title (2022) | 2013 predecessor(s) | Type |
|------|-------------|---------------------|------|
| 7.1 | Physical security perimeters | 11.1.1 | Carried |
| 7.2 | Physical entry | 11.1.2, 11.1.6 | Merged |
| 7.3 | Securing offices, rooms and facilities | 11.1.3 | Carried |
| 7.4 | Physical security monitoring | — | **New** |
| 7.5 | Protecting against physical and environmental threats | 11.1.4 | Carried |
| 7.6 | Working in secure areas | 11.1.5 | Carried |
| 7.7 | Clear desk and clear screen | 11.2.9 | Carried |
| 7.8 | Equipment siting and protection | 11.2.1 | Carried |
| 7.9 | Security of assets off-premises | 11.2.6 | Carried |
| 7.10 | Storage media | 8.3.1, 8.3.2, 8.3.3, 11.2.5 | Merged |
| 7.11 | Supporting utilities | 11.2.2 | Carried |
| 7.12 | Cabling security | 11.2.3 | Carried |
| 7.13 | Equipment maintenance | 11.2.4 | Carried |
| 7.14 | Secure disposal or re-use of equipment | 11.2.7 | Carried |

**Theme 8 — Technological**

| 2022 | Title (2022) | 2013 predecessor(s) | Type |
|------|-------------|---------------------|------|
| 8.1 | User endpoint devices | 6.2.1, 11.2.8 | Merged |
| 8.2 | Privileged access rights | 9.2.3 | Carried |
| 8.3 | Information access restriction | 9.4.1 | Carried |
| 8.4 | Access to source code | 9.4.5 | Carried |
| 8.5 | Secure authentication | 9.4.2 | Carried |
| 8.6 | Capacity management | 12.1.3 | Carried |
| 8.7 | Protection against malware | 12.2.1 | Carried |
| 8.8 | Management of technical vulnerabilities | 12.6.1, 18.2.3 | Merged (18.2.3 split with 5.36) |
| 8.9 | Configuration management | — | **New** |
| 8.10 | Information deletion | — | **New** |
| 8.11 | Data masking | — | **New** |
| 8.12 | Data leakage prevention | — | **New** |
| 8.13 | Information backup | 12.3.1 | Carried |
| 8.14 | Redundancy of information processing facilities | 17.2.1 | Carried |
| 8.15 | Logging | 12.4.1, 12.4.2, 12.4.3 | Merged |
| 8.16 | Monitoring activities | — | **New** |
| 8.17 | Clock synchronization | 12.4.4 | Carried |
| 8.18 | Use of privileged utility programs | 9.4.4 | Carried |
| 8.19 | Installation of software on operational systems | 12.5.1, 12.6.2 | Merged |
| 8.20 | Networks security | 13.1.1 | Carried |
| 8.21 | Security of network services | 13.1.2 | Carried |
| 8.22 | Segregation of networks | 13.1.3 | Carried |
| 8.23 | Web filtering | — | **New** |
| 8.24 | Use of cryptography | 10.1.1, 10.1.2 | Merged |
| 8.25 | Secure development life cycle | 14.2.1 | Carried |
| 8.26 | Application security requirements | 14.1.2, 14.1.3 | Merged |
| 8.27 | Secure system architecture and engineering principles | 14.2.5 | Carried |
| 8.28 | Secure coding | — | **New** |
| 8.29 | Security testing in development and acceptance | 14.2.8, 14.2.9 | Merged |
| 8.30 | Outsourced development | 14.2.7 | Carried |
| 8.31 | Separation of development, test and production environments | 12.1.4, 14.2.6 | Merged |
| 8.32 | Change management | 12.1.2, 14.2.2, 14.2.3, 14.2.4 | Merged |
| 8.33 | Test information | 14.3.1 | Carried |
| 8.34 | Protection of information systems during audit testing | 12.7.1 | Carried |

---

## Practical Transition Guidance

### 1. Statement of Applicability (SoA) update
- Rebuild the SoA on the **93-control 2022 structure** — do not merely append a mapping column to the 2013 SoA.
- For each merged control, consolidate the 2013 justifications and evidence references into one 2022 entry; check the merged scope is fully covered (e.g., 5.17 must now cover password management systems as well as secret authentication handling).
- Make an explicit applicability decision, with justification, for each of the **11 new controls** — "not previously assessed" is not a valid exclusion rationale.
- Keep a traceability column (2013 refs) during transition; retire it after the first post-transition surveillance audit.

### 2. Risk-treatment re-mapping
- Re-point every risk register entry and risk treatment plan line from 2013 control IDs to their 2022 successors using the tables above.
- Run a delta risk assessment covering the topics the new controls address (threat intel, cloud, ICT continuity, physical monitoring, configuration, deletion, masking, DLP, monitoring, web filtering, secure coding) — several will surface risks the 2013 assessment never scoped.
- Where a 2013 control was split (18.2.3), check the treatment intent survives in both destinations (5.36 governance-side, 8.8 technical-side).

### 3. Policy and document updates
- Update policy control-mapping sections and cross-references to the new numbering; a bulk find-and-replace is unsafe because numbering collides (e.g., 2013 "A.8" = asset management, 2022 "8" = technological).
- Always write 2022 references without the "A." prefix ambiguity resolved by context, or state the year explicitly (e.g., "ISO 27001:2022 Annex A 8.9").

### 4. Audit expectations
- **Transition audits** (now historical — deadline October 2025) reviewed: updated SoA, updated risk assessment/treatment, evidence for new controls, and clause changes (6.3 planning of changes; 9.2/9.3 sub-clause splits).
- **Current audits** expect fully native 2022 documentation. Legacy 2013 numbering in live documents is a common minor nonconformity/OFI.
- Auditors sample the new controls disproportionately — prepare strongest evidence for 5.7, 5.23, 8.9, 8.16 (most frequently tested) and demonstrate the configuration baseline + drift-detection story for 8.9.
- For merged controls, expect auditors to test the *widest* predecessor scope (e.g., 8.32 change management must show application change control, platform-change technical review and package-change restrictions, not just infrastructure change tickets).

### 5. Common pitfalls
- Treating the transition as a renumbering exercise without new-control risk decisions.
- Forgetting clause-level changes (new 6.3; restructured 9.2/9.3) because attention centred on Annex A.
- SoA exclusions carried over without re-justification against the 2022 control's (often broader) purpose.
- Integrated ISMS/PIMS (27701) or sector schemes still keyed to 2013 numbering — align dependent frameworks in the same change cycle.
