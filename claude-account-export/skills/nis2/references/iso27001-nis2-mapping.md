# ISO/IEC 27001:2022 ↔ NIS2 Mapping — Directive (EU) 2022/2555

*Reconstructed reference — regenerated on 2026-09-11 to replace a file missing from the original skill upload; verify against the official texts (EUR-Lex) before relying on citations.*

Cross-reference from each NIS2 Art. 21(2) measure to **ISO/IEC 27001:2022** management clauses and **Annex A** controls (2022 numbering), plus the Art. 23 incident-reporting mapping and a gap list of NIS2 obligations that ISO 27001 certification alone does not satisfy. Use it to leverage an existing ISMS as NIS2 evidence and to scope the delta.

**Positioning:** ISO 27001:2022 certification is strong, audit-ready evidence for most Art. 21 measures — ENISA's implementation guidance itself maps to it — but it is **not** a legal presumption of NIS2 conformity. The certificate's ISMS **scope statement** must actually cover the networks and information systems supporting the NIS2-relevant services, and the Statement of Applicability (SoA) must not exclude controls a supervisor would expect.

---

## Art. 21(2) → ISO/IEC 27001:2022 Mapping Table

| NIS2 Art. 21(2) | Measure | ISO 27001:2022 clauses | Annex A controls (2022) | Notes / delta |
|---|---|---|---|---|
| (a) | Policies on risk analysis & information system security | 4.1–4.4 context/ISMS; **5.1–5.3** leadership, policy, roles; **6.1.2–6.1.3** risk assessment & treatment; 8.2–8.3 operation | **5.1** policies for information security; 5.2 roles; 5.3 segregation of duties; 5.4 management responsibilities; 5.31 legal/regulatory requirements; 5.35 independent review; 5.36 compliance with policies | Near-complete coverage. NIS2 additionally demands **management-body** approval specifically (Art. 20(1)) — evidence board minutes, not just CISO sign-off. |
| (b) | Incident handling | 8.1 operational planning; 10.1–10.2 improvement | **5.24** incident management planning & preparation; **5.25** assessment & decision on events; **5.26** response; **5.27** learning from incidents; **5.28** evidence collection; 6.8 event reporting; 8.15 logging; 8.16 monitoring activities | Strong overlap. Delta: internal severity scheme must map to the NIS2 **significant incident** test and the 24 h/72 h/1-month regulator clock (see Art. 23 section below). |
| (c) | Business continuity, backup, DR, crisis management | 6.1 (continuity risks); 7.5 documented information | **5.29** security during disruption; **5.30** ICT readiness for business continuity; **8.13** information backup; 8.14 redundancy of information processing facilities | ISO 27001 covers *ICT* continuity; NIS2 expects full BC/DR and **crisis management**. Supplement with ISO 22301-style BIA, crisis-team structure, exercised plans. |
| (d) | Supply chain security | 6.1; 8.1 (outsourced processes) | **5.19** supplier relationships policy; **5.20** security within supplier agreements; **5.21** ICT supply chain; **5.22** monitoring, review & change management of supplier services; **5.23** cloud services | Delta: NIS2 Art. 21(3) requires factoring supplier-specific vulnerabilities, product quality, and secure-development practices, plus **Art. 22 EU coordinated risk assessments** — document how these feed the TPRM tiering. |
| (e) | Secure acquisition, development & maintenance; vulnerability handling & disclosure | 8.1 | **8.8** management of technical vulnerabilities; **8.25** secure development life cycle; 8.26 application security requirements; 8.27 secure architecture & engineering; 8.28 secure coding; 8.29 security testing in development & acceptance; 8.30 outsourced development; 8.31 environment separation; 8.32 change management; 8.9 configuration management; 8.19 installation of software; 5.37 documented operating procedures | Delta: NIS2 expects a **coordinated vulnerability disclosure** channel aligned to the national CVD policy (Art. 12) — 8.8 covers handling, not necessarily public disclosure intake. |
| (f) | Effectiveness assessment of measures | **9.1** monitoring, measurement, analysis, evaluation; **9.2** internal audit; **9.3** management review; 10.1–10.2 nonconformity & continual improvement | 5.35 independent review of information security; 5.36 compliance with policies/rules/standards; 8.34 protection during audit testing | Excellent coverage — ISO clause 9 *is* this measure. Ensure results reach the **management body** (Art. 20), not only the ISMS committee. |
| (g) | Cyber hygiene & security training | **7.2** competence; **7.3** awareness; 7.4 communication | **6.3** information security awareness, education & training; 5.10 acceptable use; 8.7 malware protection; 8.9 configuration management; 8.19 software installation; 5.15 access control (least-privilege hygiene) | Delta: NIS2 **Art. 20(2)** requires the *management body itself* to follow training — ISO has no board-training mandate. Track completion for directors by name. |
| (h) | Cryptography & encryption policies | 6.1.3 (SoA justification) | **8.24** use of cryptography (policy, key management); supporting: 5.33 protection of records; 8.20 network security (encrypted transport); 5.14 information transfer | Single-control mapping — build out the policy detail (approved algorithms, key lifecycle, HSM/KMS) beyond the 8.24 minimum. |
| (i) | HR security, access control, asset management | 7.2 | *HR:* **6.1** screening; **6.2** terms of employment; 6.4 disciplinary; **6.5** termination responsibilities; 6.6 NDAs. *Access:* **5.15** access control; **5.16** identity management; **5.17** authentication information; **5.18** access rights; **8.2** privileged access rights; 8.3 information access restriction; 8.5 secure authentication. *Assets:* **5.9** inventory of information & other associated assets; 5.10 acceptable use; 5.11 return of assets; **5.12** classification; 5.13 labelling; **5.14** information transfer; 7.9 off-site assets; 7.10 storage media; 7.14 secure disposal; plus data handling **8.10** information deletion; **8.11** data masking; **8.12** data leakage prevention | Broadest measure; the three sub-domains map cleanly. Physical security (**7.1–7.14** — perimeters, entry, offices, monitoring, utilities, cabling, maintenance) also evidences the all-hazards expectation of Art. 21(1). |
| (j) | MFA / continuous authentication; secured & emergency communications | 6.1.3 | **8.5** secure authentication (MFA); **5.17** authentication information; 5.16 identity management; 5.14 information transfer; 8.20–8.22 network security, security of network services, segregation; 8.1 user endpoint devices; 7.11 supporting utilities (resilient comms infrastructure) | Delta: ISO nowhere mandates MFA explicitly (8.5 implementation guidance recommends it) and has **no emergency-communications requirement** — add out-of-band crisis comms and test it. |

---

## Art. 23 Incident Reporting ↔ ISO 27001 Incident Clauses

NIS2 obligations for **significant incidents** (an incident that (a) has caused or is capable of causing severe operational disruption or financial loss, or (b) has affected or is capable of affecting other natural or legal persons by causing considerable material or non-material damage — Art. 23(3)):

| NIS2 obligation | Deadline | ISO/IEC 27001:2022 hook | Delta to implement |
|---|---|---|---|
| **Early warning** to CSIRT/competent authority — indicate suspected unlawful/malicious cause and possible cross-border impact | **≤ 24 hours** of awareness | 5.25 (assessment & decision on information security events); 6.8 (event reporting) | Add the significance test and the malicious/cross-border flags to the triage playbook; name a 24/7 decision-maker; pre-register on the national reporting portal. |
| **Incident notification** — update early warning; initial assessment of severity, impact, indicators of compromise | **≤ 72 hours** of awareness (trust service providers: 24 h) | 5.26 (response), 5.28 (evidence collection), 8.15/8.16 (logging & monitoring feed IoCs) | Notification template with severity, impact, IoC fields; forensic readiness so IoCs exist by hour 72. |
| **Intermediate report** | On CSIRT/authority request; status updates | 5.26 | Assign a regulator-liaison role in the IR plan. |
| **Final report** — detailed description incl. severity and impact; threat type / root cause; applied and ongoing mitigation; cross-border impact where relevant | **≤ 1 month** after the incident notification (progress report if still ongoing, final within 1 month of handling completion) | 5.27 (learning from incidents), 10.2 (nonconformity & corrective action) | Root-cause analysis method (5 whys/fishbone) producing regulator-grade narrative; corrective-action tracking. |
| **Recipient notification** — inform service recipients of significant incidents likely to adversely affect them, and of significant cyber threats incl. remedies (Art. 23(1)(2)) | Without undue delay | 7.4 communication | Customer-notification criteria and templates; align with GDPR Art. 34 where personal data involved. |

**GDPR parallel:** the NIS2 72-hour notification and the GDPR Art. 33 72-hour breach notification are **separate filings to separate authorities**; the NIS2 24-hour early warning has no GDPR analogue. Run both clocks from one triage step.

---

## What ISO/IEC 27001 Alone Does NOT Cover — NIS2 Delta List

| # | NIS2 requirement | Article | Why ISO 27001 falls short |
|---|---|---|---|
| 1 | **Management-body accountability** — approval of measures, oversight, and **personal liability**; possible temporary ban of managerial persons (essential entities) | Art. 20(1), 32(5) | ISO clause 5 requires "top management" leadership but creates no legal accountability or sanction on directors. Evidence must show the *statutory management body* acting. |
| 2 | **Management-body cybersecurity training** (and offering training to all employees) | Art. 20(2) | No ISO requirement that directors themselves be trained. |
| 3 | **Registration / entity identification** to national authority — entity details, sector, IP ranges, contacts (deadline set in transposition; digital-infrastructure entities also to the ENISA registry) | Art. 3(4), Art. 27 | Purely administrative NIS2 duty; nothing in ISO. |
| 4 | **Regulatory incident reporting** on the 24 h/72 h/1-month clock, to the CSIRT/competent authority, with prescribed content | Art. 23 | ISO requires internal handling and learning, not regulator notification or deadlines. |
| 5 | **Recipient/customer notification** of incidents and significant cyber threats with available remedies | Art. 23(1)–(2) | No ISO customer-notification duty. |
| 6 | **Jurisdiction & cross-border**: main-establishment rules, cooperation with other Member States' authorities, CyCLONe/cooperation-group ecosystem | Arts. 26, 28–37 | Out of ISO scope. |
| 7 | **Coordinated vulnerability disclosure** alignment with the national CVD policy and the European vulnerability database | Art. 12 | A.8.8 manages *your* vulnerabilities; a public intake/disclosure channel is extra. |
| 8 | **EU coordinated supply-chain risk assessments** must be taken into account in TPRM | Art. 22, 21(3) | ISO supplier controls do not reference EU-level assessments (e.g. 5G toolbox-style outcomes). |
| 9 | **Sector-specific implementing rules** — CIR (EU) 2024/2690 binding technical requirements and quantified significant-incident thresholds for digital-infrastructure and digital-provider entities | Art. 21(5), 23(11) | ISO controls are generic; the CIR Annex prescribes specifics (see `article-21-measures.md`). |
| 10 | **Use of certified ICT products / European cybersecurity certification schemes** where Member States or the Commission so require | Art. 24 | Procurement-side obligation outside the ISMS. |
| 11 | **Supervision exposure**: ex-ante audits/inspections/scans for essential entities; enforcement powers incl. instructions, deadlines, fines up to €10M/2% (EE) or €7M/1.4% (IE) | Arts. 32–34 | Certification does not immunise; it is evidence within supervision. |
| 12 | **Peer reviews and information-sharing arrangements** (voluntary but expected maturity signals) | Arts. 19, 29 | Not an ISO topic. |

---

## Reverse Lookup — Key ISO 27001:2022 Annex A Controls → NIS2 Measure

For SoA reviews: which Art. 21(2) measure each frequently cited 2022 control evidences.

| Annex A control (2022) | Title | Primary NIS2 measure | Secondary |
|---|---|---|---|
| 5.1 | Policies for information security | (a) | all |
| 5.7 | Threat intelligence | (b) incident handling | (e) vulnerability handling |
| 5.9 | Inventory of information & other associated assets | (i) asset management | (a) |
| 5.12–5.14 | Classification, labelling, information transfer | (i) | (h), (j) |
| 5.15–5.18 | Access control, identity mgmt, authentication info, access rights | (i) access control | (j) |
| 5.17 | Authentication information | (i) / (j) | — |
| 5.19–5.23 | Supplier relationships, agreements, ICT supply chain, monitoring, cloud | (d) supply chain | — |
| 5.24–5.28 | Incident planning, assessment, response, learning, evidence | (b) | Art. 23 reporting readiness |
| 5.29–5.30 | Security during disruption; ICT readiness for BC | (c) continuity | — |
| 5.31, 5.35–5.36 | Legal requirements; independent review; compliance | (a), (f) | — |
| 6.1–6.6 | Screening, terms, awareness (6.3), disciplinary, termination, NDAs | (i) HR security; 6.3 → (g) training | — |
| 7.1–7.14 | Physical security suite (perimeters, entry, monitoring, utilities, media, disposal) | Art. 21(1) all-hazards | (c), (i) |
| 8.1–8.5 | Endpoints, privileged access, access restriction, source code, secure authentication | (i), (j) MFA via 8.5 | — |
| 8.7 | Malware protection | (g) hygiene | (b) |
| 8.8 | Management of technical vulnerabilities | (e) | (b) |
| 8.9, 8.19, 8.32 | Configuration, software installation, change management | (e) | (g) |
| 8.10–8.12 | Information deletion, data masking, DLP | (i) data handling | (h) |
| 8.13–8.14 | Backup; redundancy | (c) | — |
| 8.15–8.16 | Logging; monitoring activities | (b) | (f), Art. 23 IoCs |
| 8.20–8.22 | Network security, network services, segregation | (j) | (e) |
| 8.24 | Use of cryptography | (h) | — |
| 8.25–8.31 | Secure SDLC suite | (e) | — |
| 8.34 | Protection during audit testing | (f) | — |

## Minimum NIS2 Evidence Pack (ISO-Certified Entity)

| # | Artefact | Satisfies | ISO artefact reusable? |
|---|---|---|---|
| 1 | Management-body minutes approving Art. 21 measures + director training records | Art. 20 | No — new |
| 2 | ISO certificate + scope statement + latest audit report + SoA | Art. 21(2)(a)–(j) baseline | Yes |
| 3 | Risk assessment & treatment plan covering NIS2 services | (a) | Yes |
| 4 | IR plan with significance test, 24 h/72 h/1-month workflow, portal registration | Art. 23 | Partially |
| 5 | BC/DR/crisis plans + latest exercise and restore-test reports | (c) | Partially (add crisis mgmt) |
| 6 | Supplier register, tiering, contract-clause sample, Art. 22 consideration note | (d), 21(3) | Partially |
| 7 | Vulnerability mgmt metrics + CVD policy/intake page | (e), Art. 12 | Partially (add CVD) |
| 8 | Clause 9 records: internal audit, metrics to board, management review | (f) | Yes |
| 9 | Training completion (all staff + management body), phishing-sim trends | (g), Art. 20(2) | Partially |
| 10 | Crypto policy, key-management records | (h) | Yes |
| 11 | JML/access-review/PAM evidence, asset inventory | (i) | Yes |
| 12 | MFA coverage report + emergency-comms test record | (j) | Partially (add emergency comms) |
| 13 | Registration confirmation with national authority | Art. 3(4)/27 | No — new |

---

## Practical Use

1. **Scope check first:** confirm the ISO certificate scope covers all NIS2-relevant services and systems; extend the ISMS scope before relying on it.
2. **SoA review:** flag any excluded Annex A control that maps to an Art. 21 measure above — exclusions need robust justification or reversal.
3. **Run the delta list** (items 1–12) as a standalone workstream — these are the findings an ISO-certified entity will still receive from a NIS2 supervisor.
4. **Evidence pack per measure:** pair each Art. 21(2) row with its ISO audit evidence (clause 9 records, control operating evidence) plus the NIS2-specific artefacts (board minutes, registration confirmation, reporting-portal readiness, CVD page).
5. Where the entity is in a **CIR 2024/2690 sector**, assess against the CIR Annex requirements as the binding baseline, using this table only as the ISMS leverage map.
