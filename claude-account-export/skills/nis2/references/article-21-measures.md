# Article 21 Risk-Management Measures — NIS2 Directive (Directive (EU) 2022/2555)

*Reconstructed reference — regenerated on 2026-09-11 to replace a file missing from the original skill upload; verify against the official texts (EUR-Lex) before relying on citations.*

Implementation guide to the ten cybersecurity risk-management measures of **Art. 21(2)(a)–(j)**, for use in gap assessments and remediation planning for essential and important entities. Each measure is presented as: requirement → implementing controls → evidence an auditor/supervisor expects → common gaps.

---

## Art. 21(1) — The Proportionality Principle

Entities must take **appropriate and proportionate technical, operational and organisational measures** to manage risks to the security of network and information systems used for their operations or service provision, and to prevent or minimise the impact of incidents on recipients and on other services. Measures must:

- follow an **all-hazards approach** (Art. 21(2) chapeau) — cyber attack, physical failure, power outage, natural hazard, human error;
- ensure a level of security **appropriate to the risks posed**, taking into account the **state of the art**, relevant European/international standards (ISO/IEC 27001 series, ETSI, IEC 62443), and **cost of implementation**;
- be proportionate to the entity's **exposure to risks, size, likelihood of incidents and their severity**, including societal and economic impact.

Practical reading: proportionality is a calibration dial, not an exemption. A small important entity may implement lighter-weight controls, but every one of the ten (a)–(j) domains must be demonstrably addressed; Art. 21(4) requires **corrective measures without undue delay** where non-compliance is found. Under Art. 20, the **management body must approve** these measures and oversee their implementation — link every measure below to a board-approved policy.

---

## The Ten Measures — Art. 21(2)(a)–(j)

### (a) Policies on risk analysis and information system security

**Requires:** a documented, management-approved information-security policy framework and a risk-analysis methodology governing all other measures.

**Implementing controls:** ISMS-style governance (policy hierarchy: top-level policy → topic policies → standards/procedures); defined risk assessment methodology (e.g. ISO 27005, EBIOS RM) with criteria, scales, ownership; risk register with treatment plans; defined risk-acceptance authority; annual policy review cycle; scope covering all networks and information systems supporting in-scope services.

**Auditor evidence:** approved and version-controlled policy set with management-body signature/minutes; current risk assessment and register; risk-treatment plan with owners and dates; review records.

**Common gaps:** policies exist but are not approved by the *management body* (Art. 20 defect); risk assessment done once at certification and never refreshed; scope excludes OT/legacy systems; no traceability from risks to controls.

### (b) Incident handling

**Requires:** capabilities and procedures to prevent, detect, analyse, contain, respond to and recover from incidents.

**Implementing controls:** incident response plan and playbooks (ransomware, BEC, DDoS, data breach, OT); severity classification aligned to the Art. 23 "significant incident" definition; detection tooling (SIEM/EDR/NDR, log centralisation); 24/7 escalation path or SOC arrangement; roles (incident manager, comms, legal); CSIRT/competent-authority notification procedure wired to the 24 h/72 h/1-month clock; evidence preservation and forensics arrangements; post-incident review and lessons learned.

**Auditor evidence:** IR plan and playbooks; incident log/tickets showing classification and timelines; regulatory-notification templates and any filed reports; exercise/tabletop reports; SOC/MDR contract and SLAs.

**Common gaps:** no mapping from internal severity levels to the NIS2 significance test; nobody owns the 24-hour early-warning decision out of hours; detection coverage gaps (unmanaged assets, SaaS); lessons learned never feed back into controls.

### (c) Business continuity, backup management, disaster recovery, and crisis management

**Requires:** the ability to maintain or rapidly restore services — explicitly including backups, DR, and crisis management.

**Implementing controls:** BIA identifying critical services, RTO/RPO; business continuity plans; backup policy following 3-2-1 with at least one **immutable/offline** copy; regular restoration tests; DR plans and alternate infrastructure/site or cloud failover; crisis-management structure (crisis team, activation criteria, out-of-band communications); annual BC/DR exercises including a ransomware-restore scenario.

**Auditor evidence:** BIA; tested RTO/RPO vs targets; backup job reports and restore-test records; DR exercise reports with findings tracked to closure; crisis-team roster and contact tree.

**Common gaps:** backups exist but restores are never tested end-to-end; backup infrastructure reachable from the production domain (encryptable by ransomware); crisis comms depend on the corporate systems that are down; third-party-hosted services excluded from the BIA.

### (d) Supply chain security

**Requires:** security of supply chains, including security-related aspects of relationships between each entity and its **direct suppliers or service providers**.

**Implementing controls:** supplier inventory with criticality tiering; security requirements embedded in contracts (right to audit, incident notification to the entity within defined hours, secure development, sub-contractor flow-down, exit/termination assistance); onboarding due-diligence and periodic reassessment proportionate to tier; consideration of the **Art. 21(3) factors** — vulnerabilities specific to each supplier, overall quality of products and cybersecurity practices of suppliers, including secure development procedures — and of any **Art. 22 EU coordinated risk assessments** of critical supply chains; concentration-risk view; monitoring of supplier incidents and advisories.

**Auditor evidence:** supplier register with tiers; completed assessments/questionnaires or certifications reviewed; contract clauses (sampled); reassessment schedule; documented treatment of findings on critical suppliers.

**Common gaps:** TPRM covers only new suppliers, legacy contracts never remediated; assessment stops at the questionnaire with no evidence validation; no incident-notification SLA in supplier contracts; fourth-party/sub-processor risk invisible.

### (e) Security in network and information systems acquisition, development and maintenance, including vulnerability handling and disclosure

**Requires:** security built into the acquisition, development, and maintenance lifecycle, plus a working vulnerability-management and disclosure process.

**Implementing controls:** security requirements in procurement specifications; secure SDLC (threat modelling, code review, SAST/DAST, dependency scanning); hardening baselines (CIS benchmarks) and configuration management; segregation of environments; change management; patch management with risk-based SLAs (e.g. critical/KEV: days, high: weeks); vulnerability scanning and periodic penetration testing; asset-based exposure management; a **coordinated vulnerability disclosure (CVD) policy** and intake channel (security.txt), aligned to the national CVD framework under Art. 12; monitoring of the ENISA EU vulnerability database and CSIRT advisories.

**Auditor evidence:** SDLC/procurement standards; scan reports with remediation SLAs measured; pen-test reports and closure evidence; patch-compliance metrics; published CVD policy; change records.

**Common gaps:** patching SLA exists for endpoints but not for network appliances, hypervisors, or OT; no inventory therefore no coverage assurance; pen tests scoped to avoid crown jewels; no CVD channel at all.

### (f) Policies and procedures to assess the effectiveness of cybersecurity risk-management measures

**Requires:** the entity must *measure whether its own measures work* — an assurance loop.

**Implementing controls:** internal audit programme covering the ten domains on a multi-year cycle; KPI/KRI set reported to the management body (patch latency, phishing failure rate, MFA coverage, restore-test success, incident MTTD/MTTR); control self-assessments; independent assurance (ISO 27001 certification audits, SOC 2, red-team/purple-team exercises); management review with documented decisions; corrective-action tracking (Art. 21(4)).

**Auditor evidence:** audit plan and reports; metrics packs presented to the board (minutes); nonconformity/CAPA log with closure; management-review records.

**Common gaps:** effectiveness equated with "policy exists"; metrics collected but never reach the management body; findings raised repeatedly without closure; no independent challenge of first-line assertions.

### (g) Basic cyber hygiene practices and cybersecurity training

**Requires:** baseline hygiene across the organisation and training for staff (management-body training is separately mandated by Art. 20(2)).

**Implementing controls:** hygiene baseline — inventoried assets, hardened default configurations, least privilege, removal of unsupported software, network segmentation, email/web filtering, endpoint protection, USB/media controls; security-awareness programme for all staff at onboarding and at least annually; phishing simulations; role-based training (developers, admins, finance); **specific training for the management body** (Art. 20(2)) and equivalent offering to all employees; competence records.

**Auditor evidence:** training completion rates incl. management body; phishing-simulation trend data; hygiene-baseline standard and compliance measurement; onboarding checklists.

**Common gaps:** generic e-learning with no role-based depth; management body exempted in practice from Art. 20(2) training; contractors and third-party staff excluded; hygiene baseline not measured (assumed).

### (h) Policies and procedures regarding the use of cryptography and, where appropriate, encryption

**Requires:** a governed approach to cryptography — what is encrypted, with what, and how keys are managed.

**Implementing controls:** cryptography policy specifying approved algorithms/protocols and prohibited ones (deprecate TLS <1.2, SHA-1, RSA <2048); encryption at rest (databases, endpoints, backups, removable media) and in transit; key-management lifecycle (generation, storage — HSM/KMS, rotation, revocation, destruction); certificate lifecycle management; crypto-agility and quantum-transition roadmap awareness; e-mail transport security (TLS, DMARC/DKIM/SPF).

**Auditor evidence:** crypto policy and approved-algorithm standard; key inventory and rotation records; TLS/config scan results; certificate expiry monitoring; encrypted-backup verification.

**Common gaps:** encryption claimed but keys stored beside the data; no crypto inventory (unknown legacy protocols internally); certificate expiries causing outages (a symptom of no lifecycle management); policy silent on key escrow and leaver scenarios.

### (i) Human resources security, access control policies and asset management

**Requires:** the personnel-security, access-control, and asset-management triad.

**Implementing controls:** *HR security* — screening proportionate to role and law, security terms in employment contracts, disciplinary process, joiner/mover/leaver (JML) procedure with same-day deprovisioning; *access control* — access-control policy, RBAC/least privilege, segregation of duties, privileged access management (vaulting, session recording, just-in-time elevation), periodic access recertification, service-account governance; *asset management* — complete asset inventory (hardware, software, SaaS, data, OT) with owners, classification scheme, handling rules, secure disposal.

**Auditor evidence:** JML tickets sampled against HR records; access-review campaigns with revocations evidenced; PAM coverage report; asset inventory completeness checks; disposal certificates.

**Common gaps:** leavers retain SaaS/VPN access (JML covers only AD); privileged access shared or standing; recertification rubber-stamped; shadow IT and SaaS outside the inventory; asset ownership unassigned so recertification has no reviewer.

### (j) Use of multi-factor authentication or continuous authentication solutions, secured voice, video and text communications and secured emergency communication systems

**Requires:** MFA/continuous authentication and secured (emergency) communications, **where appropriate** — the "where appropriate" qualifies the deployment scope, not permission to skip the analysis.

**Implementing controls:** MFA on all remote access, all administrative/privileged access, cloud consoles and email as a minimum; phishing-resistant factors (FIDO2/passkeys, certificates) for admins and high-risk users; conditional access/continuous authentication signals (device posture, impossible travel); secured communications for sensitive content (E2E-encrypted messaging/voice/video approved for business use); **out-of-band emergency communications** that survive compromise or outage of primary systems (separate provider/channel, pre-shared contact tree, hard copies for crisis team).

**Auditor evidence:** MFA coverage reports by population (users, admins, remote, service providers); conditional-access policy export; approved-tools standard for secure comms; crisis-communication test records.

**Common gaps:** MFA on VPN but not on internal admin interfaces or legacy protocols (bypass paths); SMS OTP for administrators; exceptions list unbounded and unreviewed; emergency comms plan assumes corporate email/Teams will be available.

---

## CIR (EU) 2024/2690 — Technical Requirements for Digital-Infrastructure Entities

Commission Implementing Regulation (EU) 2024/2690 (17 October 2024) lays down technical and methodological requirements for the Art. 21(2) measures — and criteria for significant incidents under Art. 23(3) — for a specific population: **DNS service providers, TLD name registries, cloud computing service providers, data centre service providers, CDN providers, managed service providers (MSP), managed security service providers (MSSP), providers of online marketplaces, online search engines and social networking platforms, and trust service providers**.

Key points for practice:

- **The Annex is binding for these entities**: it specifies, per Art. 21(2) measure, concrete requirements (e.g. policy content and review cadence, incident-handling process detail, backup and redundancy expectations, supplier-directory and contract expectations, MFA specifics, logging, network segmentation, physical and environmental security) with limited flexibility ("where appropriate" items must be justified and documented when not applied — a **comply-or-document** pattern).
- **Significant-incident thresholds** are quantified per service type (e.g. complete unavailability of a DNS service > 30 minutes; cloud service unavailable or integrity/confidentiality compromised beyond defined user/duration thresholds; recurring incidents — ≥2 in 6 months with the same apparent root cause — count cumulatively).
- Entities in these sectors should run their Art. 21 gap assessment **against the CIR Annex, not only the Directive text**; other sectors may still use the Annex as a state-of-the-art benchmark, alongside ENISA's technical implementation guidance (June 2025) which maps each requirement to ISO/IEC 27001:2022 and NIST CSF 2.0.

---

## Using This Reference in a Gap Assessment

Recommended output table per measure:

| Art. 21(2) | Requirement summary | Current state | Evidence held | Gap | Risk / penalty exposure | Priority | Owner | Target date |
|---|---|---|---|---|---|---|---|---|

Prioritise by: (1) measures that also protect the Art. 23 reporting capability (b, c, j); (2) management-body accountability items (a, f, g — Art. 20 linkage, personal liability); (3) externally visible controls a supervisor can test remotely (MFA, CVD channel, patching of internet-facing systems). Remember Art. 32/33: essential entities face **ex-ante** supervision (audits, inspections, scans at any time); important entities **ex-post** — but the substantive Art. 21 duties are identical.
