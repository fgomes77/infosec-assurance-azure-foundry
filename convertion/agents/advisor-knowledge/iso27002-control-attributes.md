# ISO/IEC 27002:2022 Control Attributes — Taxonomy and Per-Control View

*Advisor knowledge reference — authored 2026-09-12 to ground the persona
domain "ISO/IEC 27002:2022 controls" (attribute layer) for the advisor and
iso27001. The 93-control catalogue itself is in the iso27001 agent's
references; this file adds the five attributes and how to use them.
Verify attribute values against ISO/IEC 27002:2022 Annex A before citing.*

## 1. The five attributes and their value sets

| Attribute | Values (hashtags as in the standard) |
|---|---|
| **Control type** | #Preventive · #Detective · #Corrective |
| **Information security properties** | #Confidentiality · #Integrity · #Availability |
| **Cybersecurity concepts** (NIST CSF functions) | #Identify · #Protect · #Detect · #Respond · #Recover |
| **Operational capabilities** | #Governance · #Asset_management · #Information_protection · #Human_resource_security · #Physical_security · #System_and_network_security · #Application_security · #Secure_configuration · #Identity_and_access_management · #Threat_and_vulnerability_management · #Continuity · #Supplier_relationships_security · #Legal_and_compliance · #Information_security_event_management · #Information_security_assurance |
| **Security domains** | #Governance_and_Ecosystem · #Protection · #Defence · #Resilience |

Organisations may add their own attributes (e.g. DORA article, NIST CSF
2.0 category, owner) — the standard's Annex A shows how to build views.

## 2. Per-control attribute view (control type · main operational capability)

Legend: P = Preventive, D = Detective, C = Corrective.

| Control | Type | Operational capability |
|---|---|---|
| 5.1 Policies for information security | P | Governance |
| 5.2 Roles and responsibilities | P | Governance |
| 5.3 Segregation of duties | P | Governance; Identity_and_access_management |
| 5.4 Management responsibilities | P | Governance |
| 5.5 Contact with authorities | P C | Governance |
| 5.6 Contact with special interest groups | P C | Governance |
| 5.7 Threat intelligence | P D C | Threat_and_vulnerability_management |
| 5.8 Information security in project management | P | Governance |
| 5.9 Inventory of information and other associated assets | P | Asset_management |
| 5.10 Acceptable use of information and assets | P | Asset_management; Information_protection |
| 5.11 Return of assets | P | Asset_management |
| 5.12 Classification of information | P | Information_protection |
| 5.13 Labelling of information | P | Information_protection |
| 5.14 Information transfer | P | Asset_management; Information_protection |
| 5.15 Access control | P | Identity_and_access_management |
| 5.16 Identity management | P | Identity_and_access_management |
| 5.17 Authentication information | P | Identity_and_access_management |
| 5.18 Access rights | P | Identity_and_access_management |
| 5.19 Information security in supplier relationships | P | Supplier_relationships_security |
| 5.20 Addressing information security within supplier agreements | P | Supplier_relationships_security |
| 5.21 Managing information security in the ICT supply chain | P | Supplier_relationships_security |
| 5.22 Monitoring, review and change management of supplier services | P | Supplier_relationships_security; Information_security_assurance |
| 5.23 Information security for use of cloud services | P | Supplier_relationships_security |
| 5.24 Incident management planning and preparation | C | Governance; Information_security_event_management |
| 5.25 Assessment and decision on information security events | D | Information_security_event_management |
| 5.26 Response to information security incidents | C | Information_security_event_management |
| 5.27 Learning from information security incidents | P | Information_security_event_management |
| 5.28 Collection of evidence | C | Information_security_event_management |
| 5.29 Information security during disruption | P C | Continuity |
| 5.30 ICT readiness for business continuity | C | Continuity |
| 5.31 Legal, statutory, regulatory and contractual requirements | P | Legal_and_compliance |
| 5.32 Intellectual property rights | P | Legal_and_compliance |
| 5.33 Protection of records | P | Legal_and_compliance; Asset_management; Information_protection |
| 5.34 Privacy and protection of PII | P | Information_protection; Legal_and_compliance |
| 5.35 Independent review of information security | P C | Information_security_assurance |
| 5.36 Compliance with policies, rules and standards | P | Legal_and_compliance; Information_security_assurance |
| 5.37 Documented operating procedures | P C | (all operational capabilities) |
| 6.1 Screening | P | Human_resource_security |
| 6.2 Terms and conditions of employment | P | Human_resource_security |
| 6.3 Awareness, education and training | P | Human_resource_security |
| 6.4 Disciplinary process | P C | Human_resource_security |
| 6.5 Responsibilities after termination or change of employment | P | Human_resource_security; Asset_management |
| 6.6 Confidentiality or non-disclosure agreements | P | Human_resource_security; Information_protection; Supplier_relationships_security |
| 6.7 Remote working | P | Asset_management; Information_protection; Physical_security; System_and_network_security |
| 6.8 Information security event reporting | D | Information_security_event_management |
| 7.1 Physical security perimeters | P | Physical_security |
| 7.2 Physical entry | P | Physical_security; Identity_and_access_management |
| 7.3 Securing offices, rooms and facilities | P | Physical_security; Asset_management |
| 7.4 Physical security monitoring | P D | Physical_security |
| 7.5 Protecting against physical and environmental threats | P | Physical_security |
| 7.6 Working in secure areas | P | Physical_security |
| 7.7 Clear desk and clear screen | P | Physical_security |
| 7.8 Equipment siting and protection | P | Physical_security; Asset_management |
| 7.9 Security of assets off-premises | P | Physical_security; Asset_management |
| 7.10 Storage media | P | Physical_security; Asset_management |
| 7.11 Supporting utilities | P D | Physical_security |
| 7.12 Cabling security | P | Physical_security |
| 7.13 Equipment maintenance | P | Physical_security; Asset_management |
| 7.14 Secure disposal or re-use of equipment | P | Physical_security; Asset_management |
| 8.1 User endpoint devices | P | Asset_management; Information_protection |
| 8.2 Privileged access rights | P | Identity_and_access_management |
| 8.3 Information access restriction | P | Identity_and_access_management |
| 8.4 Access to source code | P | Identity_and_access_management; Application_security; Secure_configuration |
| 8.5 Secure authentication | P | Identity_and_access_management |
| 8.6 Capacity management | P D | Continuity |
| 8.7 Protection against malware | P D C | System_and_network_security; Information_protection |
| 8.8 Management of technical vulnerabilities | P | Threat_and_vulnerability_management |
| 8.9 Configuration management | P | Secure_configuration |
| 8.10 Information deletion | P | Information_protection; Legal_and_compliance |
| 8.11 Data masking | P | Information_protection |
| 8.12 Data leakage prevention | P D | Information_protection |
| 8.13 Information backup | C | Continuity |
| 8.14 Redundancy of information processing facilities | P | Continuity; Asset_management |
| 8.15 Logging | D | Information_security_event_management |
| 8.16 Monitoring activities | D C | Information_security_event_management |
| 8.17 Clock synchronization | D | Information_security_event_management |
| 8.18 Use of privileged utility programs | P | System_and_network_security; Secure_configuration; Application_security |
| 8.19 Installation of software on operational systems | P | Secure_configuration; Application_security |
| 8.20 Networks security | P D | System_and_network_security |
| 8.21 Security of network services | P D | System_and_network_security |
| 8.22 Segregation of networks | P | System_and_network_security |
| 8.23 Web filtering | P | System_and_network_security |
| 8.24 Use of cryptography | P | Secure_configuration |
| 8.25 Secure development life cycle | P | Application_security; System_and_network_security |
| 8.26 Application security requirements | P | Application_security; System_and_network_security |
| 8.27 Secure system architecture and engineering principles | P | Application_security; System_and_network_security |
| 8.28 Secure coding | P | Application_security; System_and_network_security |
| 8.29 Security testing in development and acceptance | P | Application_security; Information_security_assurance; System_and_network_security |
| 8.30 Outsourced development | P D | System_and_network_security; Application_security; Supplier_relationships_security |
| 8.31 Separation of development, test and production environments | P | Application_security; System_and_network_security |
| 8.32 Change management | P | Application_security; System_and_network_security |
| 8.33 Test information | P | Information_protection |
| 8.34 Protection of information systems during audit testing | P | System_and_network_security; Information_protection |

## 3. Using attribute views

- **SoA / treatment views:** filter by #Corrective to check recovery
  capability; by #Supplier_relationships_security (5.19–5.23, 6.6, 8.30)
  for the TPRM control set; by #Detect for monitoring coverage.
- **TPRM questionnaire design:** the supplier controls Euronext relies
  on are mostly #Protect + #Detect within
  #Identity_and_access_management, #Information_protection,
  #System_and_network_security, #Continuity, #Information_security_event_management.
- **Cross-framework:** cybersecurity-concept attributes map 1:1 to NIST
  CSF 2.0 functions (GOVERN is new in CSF 2.0 and corresponds to the
  #Governance capability); security domains align with ENISA/ANSSI
  taxonomies.
- **Annex B of 27002:2022** provides the 2013 ↔ 2022 correspondence
  (merged, new, renamed controls) — use it for transition audits.

## 4. New controls introduced in 2022 (frequent gap-analysis items)

5.7 Threat intelligence · 5.23 Cloud services · 5.30 ICT readiness for
BC · 7.4 Physical security monitoring · 8.9 Configuration management ·
8.10 Information deletion · 8.11 Data masking · 8.12 DLP · 8.16
Monitoring activities · 8.23 Web filtering · 8.28 Secure coding.
