# Cloud and ICT Service Assurance Reference

*Advisor knowledge reference — authored 2026-09-12 to ground the persona
domain "cloud and ICT services" for the advisor, deepsearch-protocol,
tpsrca and tpa-evidence-analyzer. Verify against ISO/IEC 27017:2015,
27018:2019, the EBA Guidelines on outsourcing arrangements
(EBA/GL/2019/02), ESMA Guidelines on outsourcing to cloud service
providers (ESMA50-164-4285), EIOPA cloud guidelines, and DORA before
citing.*

## 1. Shared-responsibility matrix

| Layer | IaaS | PaaS | SaaS |
|---|---|---|---|
| Physical, network, hypervisor | CSP | CSP | CSP |
| OS, middleware, runtime | Customer | CSP | CSP |
| Application | Customer | Customer | CSP |
| Data classification, encryption keys (option), access management, configuration | Customer | Customer (shared) | Customer (identity, data, settings) |
| Logging/monitoring | Shared | Shared | CSP provides, customer reviews |
| BC/DR | Shared (customer designs multi-zone) | Shared | CSP (verify SLA, RTO/RPO) |

Ask for the supplier's responsibility matrix (CCM SSRM column, PCI 12.8.5,
Azure/AWS/GCP shared-responsibility documents) and assign every "customer"
row to a Euronext owner.

## 2. ISO/IEC 27017 and 27018 (cloud-specific controls)

- **27017:2015** — cloud extensions to 27002 plus 7 additional controls:
  CLD.6.3.1 shared roles and responsibilities; CLD.8.1.5 removal of
  cloud customer assets; CLD.9.5.1 segregation in virtual environments;
  CLD.9.5.2 virtual machine hardening; CLD.12.1.5 administrator's
  operational security; CLD.12.4.5 monitoring of cloud services;
  CLD.13.1.4 alignment of security management for virtual and physical
  networks.
- **27018:2019** — PII protection for public-cloud processors: consent
  and purpose limitation, no use for marketing, breach notification,
  return/transfer/disposal of PII, disclosure of sub-processors and
  locations, customer control of PII, encryption in transit/at rest.
- A 27017/27018 certificate is issued as an extension of a 27001
  certificate — check the base certificate and scope.

## 3. CSA STAR levels — see `csa-ccm-caiq-star.md`.

## 4. European supervisory guidance

| Source | Key expectations for cloud/ICT outsourcing |
|---|---|
| EBA/GL/2019/02 outsourcing | Register of outsourcing; criticality assessment; pre-outsourcing due diligence; contractual requirements (access/audit rights, data location, sub-outsourcing, termination/exit); business continuity; concentration risk; notification to CA for critical/important |
| ESMA cloud guidelines (2021) | Governance, documentation, pre-outsourcing analysis, contractual requirements, information security, exit strategies, access/audit, sub-outsourcing, notification, supervision |
| EIOPA cloud guidelines (2020) | Same structure for insurers |
| **DORA Art. 28–30** (lex specialis from 17 Jan 2025) | Art. 28: strategy, register of information (CIR 2024/2956), pre-contract due diligence, concentration, exit strategies (28(8)); Art. 29: concentration risk and sub-contracting chain; Art. 30: mandatory contractual provisions — description of functions, locations of data processing/storage, availability/integrity/confidentiality, incident assistance, cooperation with authorities, termination rights, exit; for critical/important functions additionally SLAs with quantitative targets, notice periods, participation in TLPT, unrestricted access/audit rights, exit plans; RTS on subcontracting (2024) |
| **DORA Art. 31–44** | Oversight of critical ICT third-party providers (CTPPs) by the ESAs — designated hyperscalers fall under Lead Overseer oversight; does not replace the entity's own due diligence |

## 5. Cloud evidence expectations by service model

| Item | IaaS/PaaS | SaaS |
|---|---|---|
| Certificates | 27001 + 27017 (+27018 if PII), SOC 2 Type 2 (Security, Availability, Confidentiality), CSA STAR L2 | 27001 (+27018), SOC 2 Type 2 |
| Architecture | Regions/zones used for Euronext, tenancy isolation, encryption + key management (BYOK/HYOK options), network exposure | Tenant isolation, SSO/SCIM, data residency (EU), encryption, API security |
| Operations | Patch SLAs, vulnerability management, logging export, incident notification ≤ contractual hours (DORA Art. 19 timing support) | Same + release management notices |
| Continuity | Multi-AZ/region design, tested failover, backup residency | RTO/RPO in SLA, DR tests |
| Exit | Data export formats, deletion certificates, transition assistance, notice periods | Same |
| Sub-outsourcing | Subcontractor chain for critical functions (DORA RTS), locations | Sub-processor list, change notice |

## 6. Concentration-risk and exit checklist

- Is the CSP (or its region) a single point of failure for several
  Euronext critical functions? Alternative provider identified?
- Portability: open formats, documented APIs, IaC reproducibility.
- Exit plan tested (tabletop at least); data return and deletion
  evidence; notice period ≥ migration time.
- Contract: step-in, termination rights (DORA Art. 28(7)), audit rights
  incl. pooled audits and third-party certifications acceptance.
- Register of Information fields: provider LEI, rank, function
  supported, data location, substitutability, exit plan reference.
