# DORA RTS/ITS Guide — Technical Standards Under Regulation (EU) 2022/2554

*Reconstructed reference — regenerated on 2026-09-11 to replace a file missing from the original skill upload; verify against the official texts (EUR-Lex) before relying on citations.*

DORA is a framework regulation: most operational detail sits in Regulatory
Technical Standards (RTS, adopted as Commission Delegated Regulations, "CDR")
and Implementing Technical Standards (ITS, adopted as Commission Implementing
Regulations, "CIR") drafted jointly by the ESAs (EBA, ESMA, EIOPA). This guide
lists each standard with its mandating DORA article, adopted regulation number,
status, and what it means in practice. Always cite the CDR/CIR number, not just
"the RTS on X".

**Convention:** where a number below is stated, it has been verified against the
skill's authoritative citations; if you encounter a discrepancy with EUR-Lex,
EUR-Lex prevails.

---

## Summary Table

| # | Standard | Mandate | Adopted as | Status |
|---|----------|---------|------------|--------|
| 1 | RTS on ICT risk management framework and simplified framework | Art. 15, Art. 16(3) | **CDR (EU) 2024/1774** | In force; applies with DORA (17 Jan 2025) |
| 2 | RTS on classification of ICT-related incidents and significant cyber threats | Art. 18(3) | **CDR (EU) 2024/1772** | In force; applies with DORA |
| 3 | RTS on the policy on ICT services supporting critical or important functions | Art. 28(10) | **CDR (EU) 2024/1773** | In force; applies with DORA |
| 4 | ITS on the Register of Information (templates) | Art. 28(9) | **CIR (EU) 2024/2956** | In force; first RoI submissions collected 2025 |
| 5 | RTS on criteria for designation of critical ICT TPSPs (CTPPs) | Art. 31(6) | **CDR (EU) 2024/1502** | In force; first CTPP designations announced 2025 |
| 6 | Delegated Regulation on oversight fees for CTPPs | Art. 43(2) | **CDR (EU) 2024/1505** | In force |
| 7 | RTS on content and time limits of major-incident reports and cyber-threat notifications | Art. 20, first subpara. point (a) | **CDR (EU) 2025/301** | In force 2025 |
| 8 | ITS on standard forms, templates and procedures for incident reporting | Art. 20, first subpara. point (b) | **CIR (EU) 2025/302** | In force 2025 |
| 9 | RTS on subcontracting of ICT services supporting critical or important functions | Art. 30(5) | **CDR (EU) 2025/532** | In force 2025 (adopted after ESA/Commission revision of the chain-monitoring provision) |
| 10 | RTS on threat-led penetration testing (TLPT) | Art. 26(11) | **CDR (EU) 2025/1190** | In force 2025 |
| 11 | RTS on harmonisation of oversight conditions | Art. 41 | **CDR (EU) 2025/295** | In force 2025 |
| 12 | RTS on Joint Examination Teams (composition and conduct of oversight) | Art. 41(1)(c) | **CDR (EU) 2025/420** | In force 2025 |

Related non-RTS deliverables: the ESAs' **feasibility report on centralised
incident reporting** (Art. 21, delivered January 2025 — no entity obligation);
ESA **Guidelines on aggregated costs and losses estimation** from major incidents
(Art. 11(11)); and Joint Guidelines on oversight cooperation between ESAs and
CAs. Cite these as guidance, not as technical standards.

---

## 1. RTS on ICT Risk Management Framework — CDR (EU) 2024/1774

- **Mandate:** Art. 15 (full framework) and Art. 16(3) (simplified framework).
- **Structure:** Title II specifies the Art. 6–14 framework — ICT security
  policies, ICT asset management, encryption and cryptographic controls, ICT
  operations security, network security, ICT project and change management,
  physical security, HR/identity and access management, incident detection and
  response elements, ICT business continuity, and reporting on the RMF review.
  Title III specifies the **simplified** framework for Art. 16(1) entities
  (governance, risk management, asset management, BCM, incident handling —
  materially lighter but still documented and reviewable).
- **Practical implications:** This is the audit yardstick for Chapter II. Map
  every internal policy to its CDR 2024/1774 article; supervisors will. Common
  findings: no documented cryptographic key management policy; ICT change
  management not distinguishing emergency changes; access rights not re-certified
  on a defined cycle. Entities eligible for Art. 16 must evidence eligibility
  before relying on Title III — if unconfirmed, apply the full framework.

## 2. RTS on Incident Classification — CDR (EU) 2024/1772

- **Mandate:** Art. 18(3).
- **Content:** Quantified materiality thresholds for the Art. 18(1) criteria
  (clients/counterparts/transactions, reputational impact, duration and service
  downtime, geographical spread, data losses, criticality of services affected,
  economic impact); the rule set determining when an incident is **major**;
  criteria for **significant cyber threats**; and the rule for recurring
  incidents (aggregation of incidents with the same apparent root cause that
  cumulatively meet the major thresholds).
- **Practical implications:** Build the classification decision tree directly
  from this CDR and embed it in the incident tooling — see
  `incident-classification.md` for the full criteria and thresholds. The
  classification timestamp starts the reporting clocks, so the process must run
  fast and be evidenced.

## 3. RTS on the ICT Third-Party Policy — CDR (EU) 2024/1773

- **Mandate:** Art. 28(10) — RTS on the detailed content of the policy on
  arrangements for ICT services supporting **critical or important functions**.
- **Content:** Governance of the policy (board approval, role of the management
  body, three-lines involvement); full life-cycle requirements: planning of
  arrangements, ex-ante risk assessment and due diligence (including information
  security standards, TPSP resilience, subcontracting stance, location factors),
  contract conclusion referencing Art. 30, monitoring and audit approach
  (including pooled audits and third-party certifications, with conditions),
  exit and termination.
- **Practical implications:** A generic procurement/vendor policy does not
  satisfy Art. 28(2). The policy must be ICT-specific, distinguish critical/
  important-function arrangements, and be reviewed at least yearly. Evidence
  supervisors ask for: the approved policy, due diligence files per arrangement,
  and audit/assurance plans over key TPSPs.

## 4. ITS on the Register of Information — CIR (EU) 2024/2956

- **Mandate:** Art. 28(9).
- **Content:** The standard templates (a relational set of linked tables, keyed
  by LEI/EUID and arrangement reference numbers) for the Register of Information
  on **all** ICT service arrangements — entity level, sub-consolidated and
  consolidated. Tables cover: the entity(ies), contractual arrangements, the
  TPSPs and their supply chains (subcontractor ranks), the ICT services (per the
  CIR's service-type taxonomy), the functions supported and their criticality
  assessment, and substitutability/exit information.
- **Practical implications:** The RoI is a supervisory data submission, not an
  internal spreadsheet: validation rules reject incomplete files. Hard parts in
  practice: obtaining LEIs for providers, mapping subcontracting chains beyond
  rank 1, keeping the function-criticality assessment consistent with the Art. 8
  asset inventory, and reconciling group-level registers. First full collection
  cycle ran in 2025 (CA deadlines around April 2025, onward transmission to the
  ESAs for CTPP designation). See `third-party-risk.md` for field guidance.

## 5. RTS on CTPP Designation Criteria — CDR (EU) 2024/1502

- **Mandate:** Art. 31(6).
- **Content:** Quantitative and qualitative sub-criteria for the Art. 31(2)
  criticality criteria: share of FEs relying on the provider (value of assets of
  client FEs), number of G-SIIs/O-SIIs served, reliance for critical or important
  functions, interdependence, and substitutability (market structure, migration
  complexity).
- **Practical implications:** Relevant mainly to large TPSPs (cloud/hyperscalers,
  core banking and market-data providers) assessing designation likelihood, and
  to FEs anticipating which of their providers will fall under ESA oversight.
  Designation does **not** transfer the FE's responsibility (Art. 28(1)): FEs
  keep full contractual and risk-management obligations toward designated CTPPs.

## 6. Oversight Fees — CDR (EU) 2024/1505

- **Mandate:** Art. 43(2).
- **Content:** Determination of fees charged to CTPPs (based on applicable
  turnover) covering the Lead Overseer's oversight expenditure, and payment
  modalities; fees also for opt-in CTPPs.
- **Practical implications:** A cost borne by CTPPs, not FEs; relevant when
  advising providers weighing voluntary opt-in under Art. 31(11).

## 7. RTS on Incident Reporting Content and Time Limits — CDR (EU) 2025/301

- **Mandate:** Art. 20, first subparagraph, point (a) (with Art. 19 procedure).
- **Content:** The data fields for the initial notification, intermediate report
  and final report, and the **time limits**: initial notification within **4
  hours of classification as major and no later than 24 hours after becoming
  aware** of the incident; intermediate report within **72 hours of the initial
  notification** (and updates when status changes materially); final report
  within **one month** of the intermediate report (in practice cite: 4h/24h →
  72h → 1 month); rules for weekend/holiday submissions, reclassification and
  outsourced reporting.
- **Practical implications:** The 4-hour clock runs from classification, the
  24-hour backstop from awareness — an entity cannot delay classification to buy
  time. Build the report field set into the incident SOP so the first responder
  captures required data during triage. See `incident-classification.md`.

## 8. ITS on Incident Reporting Templates — CIR (EU) 2025/302

- **Mandate:** Art. 20, first subparagraph, point (b).
- **Content:** The standard forms and templates (structured data fields, single
  template usable across the three stages) for major-incident reports and for
  voluntary significant-cyber-threat notifications, and submission procedures to
  CAs.
- **Practical implications:** Use the template natively — do not free-text
  incident reports. Many CAs expose the template through their reporting portals;
  pre-register portal access and test submission before an incident occurs.

## 9. RTS on Subcontracting — CDR (EU) 2025/532

- **Mandate:** Art. 30(5) — conditions for subcontracting ICT services that
  support **critical or important functions**.
- **Content:** Risk-based conditions the FE must impose and verify when its TPSP
  subcontracts (or materially changes subcontracting of) services supporting
  critical/important functions: ex-ante assessment of the subcontracting chain,
  contractual requirements to flow down monitoring/audit/security/location
  obligations, notification of material changes with an objection window and
  termination rights where the FE objects or risks are unmanageable. (An earlier
  draft provision extending direct monitoring duties across the whole chain was
  removed in the adoption process — obligations concentrate on the direct TPSP
  and material subcontractors.)
- **Practical implications:** Contract templates must give the FE: visibility of
  the subcontracting chain (feeding the RoI supply-chain tables), a defined
  notice-and-objection mechanism for changes, and termination triggers. Verify
  legacy contracts against this RTS during remediation, not just against
  Art. 30(2)–(3).

## 10. RTS on TLPT — CDR (EU) 2025/1190

- **Mandate:** Art. 26(11).
- **Content:** Criteria for identifying entities required to perform TLPT;
  requirements on scope, testing methodology and phases (preparation, threat
  intelligence, red-team testing, closure/remediation, purple-teaming elements),
  use of internal testers, supervisory cooperation, attestation and mutual
  recognition. Aligned with **TIBER-EU**; TLPT authorities in each Member State
  run the process.
- **Practical implications:** If designated, expect a 6–9 month end-to-end
  exercise on **live production** systems every 3 years, with an external threat
  intelligence provider always required and strict tester requirements per
  Art. 27. Budget, secrecy (need-to-know "white team"), and TPSP participation/
  pooled testing arrangements are the recurring planning issues.

## 11. RTS on Oversight Harmonisation — CDR (EU) 2025/295

- **Mandate:** Art. 41.
- **Content:** Harmonises conduct of oversight: information a TPSP provides in a
  voluntary opt-in request (Art. 31(11)), content of the reports CTPPs submit
  under Art. 35(1)(c), and details for the Lead Overseer's assessment of CTPP
  risk management.
- **Practical implications:** Primarily CTPP-facing; FEs interact indirectly
  (e.g. when a CTPP's remediation plan under a recommendation affects contracted
  services, and via Art. 42(6) suspension powers).

## 12. RTS on Joint Examination Teams — CDR (EU) 2025/420

- **Mandate:** Art. 41(1)(c) (with Art. 40).
- **Content:** Criteria for composition of JETs (members from the three ESAs and
  relevant CAs), designation and tasks of JET coordinators, and working
  arrangements for on-site/off-site examinations of CTPPs.
- **Practical implications:** Explains who shows up at a CTPP examination and
  how findings feed Lead Overseer recommendations. Useful when advising CTPPs on
  examination readiness.

---

## Citation Hygiene

- **CDR** = Commission **Delegated** Regulation (adopts an RTS or Art. 57
  delegated act). **CIR** = Commission **Implementing** Regulation (adopts an
  ITS). Do not mix the prefixes: the RoI standard is **CIR** 2024/2956, not CDR.
- Number format: "CDR (EU) 2024/1774", article citations as
  "Art. 13 CDR (EU) 2024/1774".
- If a user cites a **consultation-paper or draft-RTS numbering** (e.g.
  "JC 2023 72"), map it to the adopted regulation before advising — draft and
  adopted texts differ (notably the subcontracting RTS).
- If you are not certain of a regulation number for a standard not listed here,
  describe it by mandate ("the RTS under Art. X on …") rather than guessing a
  number, and direct the user to EUR-Lex.
