# TPSRCA Supplier Type Catalogue (A.01–D.05) and Assessment Scope Matrix

*Advisor knowledge reference — authored 2026-09-12 to replace the
`tpsrca-supplier-classifier` skill that the TPSRCA engine references but
the claude.ai export does not contain. The tier → scope/weighting rows are
copied from `tpsrca-assessment-engine/SKILL.md` (Assessment Scope Matrix,
Framework Weighting by Tier); the type catalogue is authored from the
team's ICT supplier taxonomy and DORA Art. 28–30 criticality logic.
Confirm the type with the assessor when ambiguous.*

## 1. Tier logic

| Tier | Meaning | Typical DORA status |
|---|---|---|
| **A** | Critical ICT services supporting market-critical / regulated functions; outage or breach = critical or important function impact | Critical or important function support (Art. 28(4)); candidates for RoI critical flag |
| **B** | Important ICT services with direct access to Euronext data or networks | Important function support |
| **C** | Standard ICT services with limited data or indirect connectivity | Non-critical ICT |
| **D** | Low-risk / commodity services, no Euronext data, no connectivity | Non-ICT or negligible ICT |

## 2. Type catalogue

| Id | Supplier / service type | Examples of scope | Default tier drivers |
|---|---|---|---|
| A.01 | Trading, clearing, settlement or market-data platform provider | matching engines, CCP/CSD connectivity, market-data feeds | Critical function, regulator-visible |
| A.02 | Core infrastructure / data-centre / colocation / network carrier | DC hosting, WAN/MPLS, extranet, DDoS scrubbing | Availability of critical functions |
| A.03 | Cloud hyperscaler or managed cloud platform hosting critical workloads | IaaS/PaaS landing zones, managed Kubernetes, DBaaS | Concentration risk (DORA Art. 29), exit strategy required |
| B.01 | Security service provider with privileged or monitoring access | MDR/SOC, SIEM SaaS, EDR, PAM, IAM/IDP, PKI, vulnerability scanning | Privileged access, telemetry of internal systems |
| B.02 | Business-critical SaaS processing Euronext or client data | GRC/TPRM platforms, HR/payroll, finance/ERP, CRM, e-mail/collaboration | Confidential/personal data, integration to core |
| B.03 | Software vendor with production code or maintenance access | trading/back-office application vendors, custom development, DevOps tooling | Supply-chain integrity, remote support access |
| C.01 | Standard SaaS with limited internal data | survey, e-learning, ticketing, document e-signature, marketing tools | Limited data classes, SSO-integrated |
| C.02 | IT consultancy, staff augmentation, professional services | project delivery, audit support, PMO, testing services | Individual access, NDAs, device policy |
| C.03 | Telecommunications / end-user services | mobile fleet, conferencing, printing/MPS, VoIP | Availability, limited data |
| D.01 | Hardware / peripherals reseller without services | laptops, screens, cabling | No data, no connectivity |
| D.02 | Facilities and physical services with site access | cleaning, catering, physical security guarding, maintenance | Physical access only |
| D.03 | Content, research, training and events providers | market research subscriptions, training, conferences | Public or licensed content only |
| D.04 | Legal, advisory and financial services without ICT access | law firms, notaries, tax advisors, insurers | Confidential documents by e-mail only |
| D.05 | Marketplace / one-off purchases and utilities | utilities, small online purchases, subscriptions | Negligible |

Escalation rules: a D-type supplier that gains network connectivity or
data access is re-typed to C/B; any supplier supporting a function on the
critical-or-important list is at least B; personal data of employees or
clients moves a C-type to B.02 for the GDPR weighting.

## 3. Assessment scope matrix (from the engine SKILL.md)

| Tier | Agents to run | Frameworks | Depth |
|---|---|---|---|
| A.01–A.03 | All 12 | All 10 | Full + Enhanced |
| B.01–B.03 | All 12 | All 10 | Full |
| C.01–C.03 | 1–9, 11–12 | Core 6 | Standard |
| D.01–D.05 | 1–3, 8, 12 | Basic 3 | Lite |

Core 6 = DORA, ISO 27001, GDPR, NIST CSF, NIS2, CIS v8.1. Basic 3 =
ISO 27001, GDPR, NIST CSF. "All 10" adds EU AI Act, ISO 42001, SOC 2 TSC,
CSA CCM. Framework weighting by tier and the L1–L5 rating scale are in
the engine SKILL.md and MUST come from `calculation_engine.py`.

## 4. Classification record (emit in the assessment JSON)

`supplier_type`, `tier`, `rationale` (function supported, data classes,
connectivity, privileged access, substitutability), `classified_by`
(agent + assessor confirmation), `date`.
