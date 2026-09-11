# CIS Critical Security Controls v8.1

*Advisor knowledge reference — authored 2026-09-11 to ground the persona domain in the combined knowledge base; verify against the official publication before citing in formal deliverables.*

## What the CIS Controls are

The CIS Critical Security Controls are a prioritised, prescriptive set of
18 top-level Controls decomposed into **Safeguards** (153 in v8.1), maintained
by the Center for Internet Security and grounded in observed attack data.
Unlike outcome frameworks (NIST CSF) or management-system standards
(ISO 27001), the CIS Controls tell you concretely what to implement and in
what order. Version 8.1 (June 2024) is an iterative update to v8 — same
18 Controls, same Safeguard numbering — refined for governance and CSF 2.0
alignment (see below).

## The 18 Controls

| # | Control | Summary |
|---|---|---|
| 01 | Inventory and Control of Enterprise Assets | Actively manage all enterprise assets (end-user devices, network gear, IoT, servers) so only known, authorised assets connect; unknown assets are found and handled. |
| 02 | Inventory and Control of Software Assets | Maintain a software inventory; ensure only authorised, supported software executes, and unauthorised software is removed or blocked. |
| 03 | Data Protection | Classify, handle, retain and dispose of data with defined processes; encrypt sensitive data at rest and in transit; know where data lives and flows. |
| 04 | Secure Configuration of Enterprise Assets and Software | Establish and maintain hardened configurations for devices, OSs and applications, replacing insecure defaults. |
| 05 | Account Management | Manage the lifecycle of user, administrator and service accounts — inventory, unique credentials, disabling dormant accounts, restricting admin privileges. |
| 06 | Access Control Management | Grant, manage and revoke access on least privilege and need-to-know; enforce MFA for remote, admin and externally exposed access. |
| 07 | Continuous Vulnerability Management | Continuously assess and remediate vulnerabilities on a risk-ranked basis, tracking against defined remediation timelines. |
| 08 | Audit Log Management | Collect, retain, protect and review audit logs sufficient to detect, investigate and recover from attacks. |
| 09 | Email and Web Browser Protections | Harden the two most common initial-access vectors: browser/email client hygiene, DNS filtering, malicious attachment and URL defences. |
| 10 | Malware Defenses | Deploy and centrally manage anti-malware/EDR; prevent execution and spread of malicious code, including via removable media. |
| 11 | Data Recovery | Maintain and test backups (isolated where warranted) sufficient to restore in-scope assets to a trusted, pre-incident state. |
| 12 | Network Infrastructure Management | Keep network devices current and securely configured; maintain network diagrams; segregate and securely administer network infrastructure. |
| 13 | Network Monitoring and Defense | Operate detection and defence across the network: centralised alerting, IDS/IPS, traffic filtering between segments, port-level access control. |
| 14 | Security Awareness and Skills Training | Run a security awareness programme with role-appropriate content (phishing, data handling, credential hygiene) delivered regularly. |
| 15 | Service Provider Management | Inventory and classify service providers; set contractual security requirements; assess, monitor and securely decommission providers holding data or critical functions. |
| 16 | Application Software Security | Manage the security lifecycle of in-house and third-party application software: secure development, dependency management, testing, hardening. |
| 17 | Incident Response Management | Establish an IR capability: designated personnel, plans, reporting thresholds, communications, exercises and post-incident review. |
| 18 | Penetration Testing | Test the effectiveness of defences by simulating attacker actions — regular external/internal pentests and remediation of findings. |

## Implementation Groups (IG1–IG3)

IGs are the CIS prioritisation scheme — cumulative bands of Safeguards
calibrated to organisational risk profile and capability:

| IG | Safeguards (v8.1) | Profile it fits |
|---|---|---|
| IG1 | 56 | "Essential cyber hygiene" — every enterprise's minimum baseline; limited security expertise, mainly commodity threats; the definitional floor. |
| IG2 | IG1 + 74 = 130 | Organisations with departmental risk profiles, staff dedicated to security, and moderately sensitive data or regulatory exposure. |
| IG3 | IG2 + 23 = 153 | Organisations facing sophisticated/targeted attacks, holding highly sensitive data, or where compromise causes public-order or safety harm. |

Every Control has IG1 Safeguards except Control 18 (penetration testing starts
at IG2); Control 13 also has no IG1 Safeguards.

### Using IGs for supplier proportionality in TPRM

IGs give the assurance team a defensible, graduated yardstick instead of a
one-size questionnaire:

- **Tier the expectation to the relationship**: low-criticality suppliers with
  no sensitive data → evidence of IG1; suppliers processing personal or
  confidential data, or supporting important functions → IG2; suppliers running
  critical or high-privilege services (e.g. within DORA scope for critical or
  important functions) → IG3-oriented scrutiny.
- **Question sets**: derive supplier questionnaires from the Safeguard list of
  the target IG, keeping questions verifiable ("show the asset inventory
  refresh cadence") rather than aspirational.
- **Gap articulation**: findings expressed as missing Safeguards (e.g.
  "no 7.1 vulnerability management process") are concrete, remediable and
  easy to put on a treatment plan with a deadline.
- **Proportionality defence**: when a small supplier pushes back, IG1 is a
  published, consensus minimum — a credible floor to hold in negotiation.
- Control 15 (Service Provider Management) is simultaneously what *we* run the
  TPRM programme against and what we ask suppliers to demonstrate for *their*
  own fourth parties (flow-down).

## What v8.1 changed

v8.1 is deliberately compatible with v8 (no renumbering, no Safeguards
removed). The updates:

- **Governance made explicit**: "Governance" was added as a security function
  in the Safeguard taxonomy, aligning the Controls with the new **GOVERN**
  Function of NIST CSF 2.0; mappings to CSF 2.0 were published alongside.
- **Asset classes revised**: clearer, expanded asset-class definitions
  (devices, software, data, users, networks, and documentation added as an
  asset class) so each Safeguard states more precisely what it acts on.
- **Wording and glossary clarifications**: refreshed Safeguard descriptions
  ("sensitive data" usage, plan-review language, documentation expectations)
  without changing intent — e.g. several policy/process Safeguards now say
  explicitly that documented artefacts must be reviewed and updated annually
  or on significant enterprise change.

Practically: v8 evidence remains valid under v8.1, but expect assessors to
probe documented governance artefacts (policies, review cadences) harder.

## Mapping: CIS Controls v8.1 → ISO/IEC 27001:2022 Annex A

Indicative main correspondences (Annex A themes: 5.x Organizational,
6.x People, 7.x Physical, 8.x Technological). Many-to-many in reality; use the
official CIS mapping workbook for formal crosswalks.

| CIS Control | Principal ISO 27001:2022 Annex A controls |
|---|---|
| 01 Enterprise Assets | 5.9 inventory of information and other associated assets; 8.1 user endpoint devices |
| 02 Software Assets | 5.9; 8.19 installation of software on operational systems |
| 03 Data Protection | 5.12–5.14 classification, labelling, transfer; 5.33 records; 8.10–8.12 deletion, masking, DLP; 8.24 cryptography |
| 04 Secure Configuration | 8.9 configuration management; 8.20–8.22 network security & segregation (config aspects) |
| 05 Account Management | 5.16 identity management; 5.17 authentication information; 8.2 privileged access |
| 06 Access Control | 5.15 access control; 5.18 access rights; 8.3 information access restriction; 8.5 secure authentication |
| 07 Vulnerability Management | 8.8 management of technical vulnerabilities; 5.7 threat intelligence (input) |
| 08 Audit Logs | 8.15 logging; 8.17 clock synchronisation |
| 09 Email & Browser | 8.23 web filtering; 5.14 information transfer; 8.7 malware protection (overlap) |
| 10 Malware Defenses | 8.7 protection against malware |
| 11 Data Recovery | 8.13 information backup; 8.14 redundancy; 5.29–5.30 continuity |
| 12 Network Infrastructure | 8.20 networks security; 8.21 security of network services; 8.22 segregation of networks |
| 13 Network Monitoring | 8.16 monitoring activities; 8.15 logging; 5.25 assessment of events |
| 14 Awareness & Training | 6.3 information security awareness, education and training |
| 15 Service Provider Management | 5.19–5.22 supplier relationships, agreements, ICT supply chain, monitoring; 5.23 cloud services |
| 16 Application Security | 8.25–8.31 secure development lifecycle; 8.26 application security requirements; 8.28 secure coding |
| 17 Incident Response | 5.24–5.28 incident management planning through evidence; 6.8 event reporting |
| 18 Penetration Testing | 8.29 security testing in development and acceptance; 5.35 independent review; 8.8 (validation) |

## Practitioner cautions

- The Controls assume an enterprise IT estate; for pure-SaaS suppliers,
  interpret Safeguards through the shared-responsibility lens (their platform
  and corporate estate, not your tenant configuration).
- IG level is about the *enterprise's* risk profile, not company size alone —
  a ten-person fintech processing payment data is not an IG1 case.
- Do not treat Safeguard counts as a maturity score; presence of a Safeguard
  says nothing about operating effectiveness without evidence.
