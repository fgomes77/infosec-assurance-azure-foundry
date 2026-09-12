# NIST Cybersecurity Framework (CSF) 2.0

*Advisor knowledge reference — authored 2026-09-11 to ground the persona domain in the combined knowledge base; verify against the official publication before citing in formal deliverables.*

## What CSF 2.0 is

NIST released CSF 2.0 in February 2024 — the first full revision since v1.1
(2018). It is a voluntary, outcome-oriented taxonomy of cybersecurity results,
not a control catalogue: each Subcategory states *what* should be true, leaving
*how* to implementers and to informative references (SP 800-53, CIS Controls,
ISO 27001, etc.). Two headline changes from v1.1:

- Scope widened from "critical infrastructure" to **all organisations** of any
  size or sector.
- A sixth Function, **GOVERN**, was added and placed at the centre — strategy,
  roles, policy, oversight and supply-chain risk were pulled out of the other
  Functions and elevated to a cross-cutting layer that informs the rest.

The Framework Core is organised as Functions → Categories → Subcategories.
The Category identifiers below are the authoritative 2.0 set.

## The six Functions and their Categories

### GOVERN (GV) — establish and monitor the cybersecurity risk strategy, expectations and policy

| ID | Category | One-line summary |
|---|---|---|
| GV.OC | Organizational Context | The mission, stakeholder expectations, legal/regulatory requirements and dependencies that frame cyber-risk decisions are understood. |
| GV.RM | Risk Management Strategy | Risk appetite, tolerance statements and how cyber risk is assessed, prioritised and communicated are established and agreed. |
| GV.RR | Roles, Responsibilities, and Authorities | Accountability for cyber risk — leadership ownership, resourcing, and clear roles across the workforce — is defined and exercised. |
| GV.PO | Policy | Organisational cybersecurity policy is established, communicated and kept current with risk and mission changes. |
| GV.OV | Oversight | Results of risk management activities are reviewed to steer and improve the strategy itself. |
| GV.SC | Cybersecurity Supply Chain Risk Management | C-SCRM strategy, supplier roles, contractual requirements, due diligence, monitoring and end-of-relationship handling are planned and managed. |

### IDENTIFY (ID) — understand the organisation's assets and risks

| ID | Category | One-line summary |
|---|---|---|
| ID.AM | Asset Management | Hardware, software, services, data, people and their flows are inventoried and prioritised by criticality. |
| ID.RA | Risk Assessment | Vulnerabilities, threats, likelihoods and impacts — including from suppliers — are analysed to inform risk responses; disclosure and exception processes operate. |
| ID.IM | Improvement | Lessons from assessments, tests, incidents and exercises drive improvements to processes and plans across all Functions. |

### PROTECT (PR) — safeguards to manage cybersecurity risk

| ID | Category | One-line summary |
|---|---|---|
| PR.AA | Identity Management, Authentication, and Access Control | Identities are proofed and bound to credentials; access (physical and logical) is authenticated and authorised to least privilege. |
| PR.AT | Awareness and Training | Personnel and specialised roles are trained so they act in a security-conscious way. |
| PR.DS | Data Security | Data at rest, in transit and in use is protected consistent with its classification; backups are maintained and protected. |
| PR.PS | Platform Security | Hardware, software and services are configured, patched, logged and lifecycle-managed securely, including secure development practices. |
| PR.IR | Technology Infrastructure Resilience | Networks and environments are protected against unauthorised access and engineered for resilience, capacity and continuity. |

### DETECT (DE) — find and analyse possible cybersecurity attacks and compromises

| ID | Category | One-line summary |
|---|---|---|
| DE.CM | Continuous Monitoring | Networks, endpoints, personnel activity, and external service providers are monitored to spot anomalies and potentially adverse events. |
| DE.AE | Adverse Event Analysis | Anomalies are analysed, correlated and triaged to determine whether an incident has occurred and to estimate its scope. |

### RESPOND (RS) — act on a detected cybersecurity incident

| ID | Category | One-line summary |
|---|---|---|
| RS.MA | Incident Management | Responses are executed and coordinated per plan: reports triaged, incidents categorised, prioritised and escalated. |
| RS.AN | Incident Analysis | Investigation establishes what happened, root cause, magnitude, and preserves evidence with integrity. |
| RS.CO | Incident Response Reporting and Communication | Internal and external stakeholders — including regulators and affected parties — are notified and kept informed as required. |
| RS.MI | Incident Mitigation | Incidents are contained and eradicated to prevent expansion and reduce effects. |

### RECOVER (RC) — restore assets and operations after an incident

| ID | Category | One-line summary |
|---|---|---|
| RC.RP | Incident Recovery Plan Execution | Restoration is executed: backup integrity verified before use, restoration priorities followed, normal status confirmed and declared. |
| RC.CO | Incident Recovery Communication | Recovery progress and public messaging are coordinated with internal and external parties. |

## Profiles and Tiers

- **Organizational Profiles** describe the organisation's posture in CSF terms:
  a **Current Profile** (outcomes achieved today) and a **Target Profile**
  (outcomes required by risk appetite, obligations and mission). The gap
  between them is the improvement roadmap. **Community Profiles** are shared
  baselines for a sector or use case and are a useful TPRM device: express your
  minimum supplier expectations as a target profile and assess vendors
  against it.
- **Tiers (1–4: Partial, Risk Informed, Repeatable, Adaptive)** characterise
  the rigour of cyber-risk *governance and management* practices — how
  institutionalised and risk-informed they are. Tiers apply to the Profile as
  context, are not maturity certification levels, and Tier 4 is not
  automatically the right target; the appropriate tier follows from risk,
  obligations and resources.

## GV.SC and third-party risk management

GV.SC is the CSF 2.0 home for C-SCRM and maps almost one-to-one onto a TPRM
lifecycle:

- Strategy, objectives and policy for supply-chain risk (GV.SC-01) and
  supplier roles/responsibilities (GV.SC-02) → TPRM policy and operating model.
- Integration of C-SCRM into wider risk management (GV.SC-03) and supplier
  criticality tiering (GV.SC-04) → inherent-risk classification of suppliers.
- Contractual security requirements (GV.SC-05) → security schedules, GDPR
  Art. 28 terms, DORA Art. 30 provisions.
- Pre-contract due diligence (GV.SC-06) and ongoing monitoring of supplier
  risk through the relationship (GV.SC-07) → onboarding assessment and
  continuous monitoring / reassessment.
- Inclusion of suppliers in incident planning and response (GV.SC-08) and
  secure-by-design integration across the technology lifecycle (GV.SC-09).
- Post-relationship handling — offboarding, data return/destruction, access
  revocation (GV.SC-10) → termination and exit controls.

Supporting outcomes sit elsewhere: ID.RA covers assessing supplier-originated
risk, DE.CM includes monitoring external service providers, and RS.CO covers
coordinated notification with third parties.

## Mapping: CSF 2.0 Functions → ISO/IEC 27001:2022

Indicative correspondences (outcome-level, not exhaustive; Annex A themes are
Organizational 5.x, People 6.x, Physical 7.x, Technological 8.x):

| CSF 2.0 Function | ISO 27001:2022 clauses | Representative Annex A controls |
|---|---|---|
| GOVERN | 4 (context), 5 (leadership, policy, roles), 6 (risk & objectives), 7.1–7.3, 9.3 (management review) | 5.1 policies; 5.2 roles; 5.4 management responsibilities; 5.19–5.23 supplier & cloud relationships; 5.31 legal requirements; 5.35–5.36 reviews & compliance |
| IDENTIFY | 6.1.2 (risk assessment), 8.2, 9.1, 10 (improvement) | 5.9 asset inventory; 5.12 classification; 8.8 technical vulnerability management; 5.7 threat intelligence |
| PROTECT | 7.2–7.3 (competence, awareness), 8.1 (operational planning) | 5.15–5.18 & 8.2–8.5 access and authentication; 6.3 awareness training; 8.24 cryptography; 8.13 backup; 8.9 configuration; 8.19/8.25–8.31 platform & secure development; 7.x physical |
| DETECT | 9.1 (monitoring, measurement, analysis) | 8.15 logging; 8.16 monitoring activities; 5.25 assessment of security events |
| RESPOND | 10.2 (nonconformity — partial analogue) | 5.24 incident planning; 5.26 response; 5.27 learning; 5.28 evidence collection; 6.8 event reporting |
| RECOVER | 8.1 (via continuity planning) | 5.29 security during disruption; 5.30 ICT readiness for business continuity; 8.13/8.14 backup & redundancy |

Use direction matters: CSF Profiles describe outcomes and gaps; ISO 27001
supplies the certifiable management system and auditable control set that
closes them. The pairing is complementary, not redundant.

## Practitioner cautions

- Cite Category IDs exactly (e.g. PR.AA, not the v1.1 PR.AC) — v1.1 identifiers
  such as ID.BE, ID.GV, ID.SC, PR.IP, DE.DP, RS.RP and RC.IM were retired or
  redistributed in 2.0, and stale mappings are a common defect in supplier
  questionnaire responses.
- The CSF states outcomes, not evidence; when assessing a supplier "aligned to
  NIST CSF", ask which Profile, which Subcategories, and what evidence
  demonstrates each outcome.
- NIST's online CSF 2.0 Reference Tool and Informative References provide
  living mappings — prefer them to memorised crosswalks for formal work.
