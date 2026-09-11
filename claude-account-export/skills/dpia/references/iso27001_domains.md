# ISO 27001 Control Domain Mapping Reference

Map OneTrust risks to ISO 27001:2022 control domains using the keywords below.

## Domain Keyword Mapping

| Domain | Keywords in Risk/Treatment |
|--------|---------------------------|
| **Information Security Policies / processes** | policy, policies, procedures, standards, governance, framework, management review |
| **Organization of information security** | roles, responsibilities, segregation, contact authorities, project management, mobile devices, teleworking |
| **Human resources security** | training, awareness, screening, employment, termination, disciplinary, personnel |
| **Asset management** | asset inventory, data classification, data flows, data handling, media, acceptable use, return of assets |
| **Access control** | access control, authentication, privileged access, password, user access, authorization, logical access |
| **Cryptography** | encryption, cryptographic, keys, key management, TLS, SSL |
| **Physical and environmental security** | physical security, secure areas, equipment, cabling, environmental, data center |
| **Operations security** | operational procedures, change control, capacity, malware, backup, logging, monitoring, clock synchronization, installation, vulnerability |
| **Communications security** | network, firewall, IDS, IPS, intrusion, network security, segregation, transfer |
| **System acquisition, development and maintenance** | SDLC, development, secure coding, testing, system changes, application security, software development |
| **Information security incident management** | incident, breach, logging, monitoring, response, forensics, evidence, reporting |
| **Information security aspects of business continuity management** | business continuity, disaster recovery, BCP, DRP, resilience, availability, backup, exercising, testing |
| **Compliance** | legal, regulatory, compliance, contractual, privacy, GDPR, audit, records, intellectual property |

## Risk-to-Domain Examples

| Risk Description Pattern | Primary Domain |
|-------------------------|----------------|
| Software inventory, systems tracking | Asset management |
| Data classification, data mapping | Asset management |
| BCM testing, disaster recovery | Business continuity management |
| Supplier services, third-party tracking | Compliance; Operations security |
| Access controls, unauthorized access | Access control |
| IDS/IPS signatures, network security | Communications security |
| Change control, operational procedures | Operations security |
| Logging, monitoring, breach detection | Incident management; Operations security |
| SDLC, secure development | System acquisition, development and maintenance |
| Remote desktop, acceptable use | Information Security Policies |
| Security testing, vulnerability management | System acquisition, development and maintenance |
| Supply chain security | Organization of information security; Compliance |
| Legal/regulatory requirements | Compliance |
| Supplier risk monitoring | Organization of information security |
| Cybersecurity training | Human resources security |
| Risk response planning | Information Security Policies |

## Writing the Conclusion

When all controls are implemented, list domains in bold:

> The supplier demonstrates comprehensive security controls across: **Information Security Policies / processes**; **Asset management**; **Access control**; **Operations security**; **Communications security**; **System acquisition, development and maintenance**; **Information security incident management**; **Information security aspects of business continuity management**; and **Compliance**.

When there are gaps, mention concerns:

> **Concerns:** Gaps identified in **Information security incident management** (10 controls pending) and **System acquisition, development and maintenance** (SDLC controls not implemented).
