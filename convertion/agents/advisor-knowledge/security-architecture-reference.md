# Security Architecture Reference (cybersecurity-architect capability)

*Advisor knowledge reference — authored 2026-09-12 to ground the persona
claim "cybersecurity architect" and TOGAF security engagement for the
advisor, deepsearch-protocol and tpa-evidence-analyzer. Verify against
SABSA, NIST SP 800-207, TOGAF 10 / Open Group security guides, CIS v8.1
and ISO 27001:2022 before citing.*

## 1. SABSA layers (business-driven architecture)

| Layer | View | Assurance question |
|---|---|---|
| Contextual | Business | What business attributes (availability, confidentiality, compliance) must the service protect? |
| Conceptual | Architect | Security strategy, trust model, risk appetite |
| Logical | Designer | Security services (authentication, authorisation, encryption, monitoring), policies |
| Physical | Builder | Mechanisms (IdP, PAM, WAF, HSM, SIEM), technology standards |
| Component | Tradesman | Products, configurations, keys |
| Operational | Service manager | Run, monitor, measure — ties to ITIL/ISO 20000 |

## 2. Zero-trust tenets (NIST SP 800-207)

1. All data sources and computing services are resources. 2. All
communication is secured regardless of location. 3. Access is granted per
session. 4. Access is determined by dynamic policy (identity, device,
behaviour). 5. Integrity and security posture of all assets is monitored.
6. Authentication and authorisation are dynamic and strictly enforced
before access. 7. Collect as much information as possible about assets,
network and communications to improve posture.
Core components: policy engine, policy administrator, policy enforcement
point; deployment models: enhanced identity governance, micro-segmentation,
software-defined perimeter.

## 3. Reference patterns

- **Segmentation / trust zones:** internet-facing DMZ, application tier,
  data tier, management plane, OT/market-connectivity zones; east-west
  controls; jump hosts/PAM for admin access; separate environments
  (dev/test/prod — Annex A 8.31).
- **Identity-centric access:** SSO (SAML/OIDC), MFA everywhere, SCIM
  provisioning, JIT privileged access, conditional access, service
  identities (managed identities, no shared secrets).
- **Data-flow protection:** classification-driven encryption in transit
  (TLS 1.2+) and at rest (customer-managed keys for confidential data),
  tokenisation/masking, DLP, key management in HSM/KMS.
- **Cloud landing zone:** hub-and-spoke networks, private endpoints,
  no public storage, policy-as-code guardrails, centralised logging,
  IaC with review gates, EU residency.
- **Secure SDLC / DevSecOps gates:** threat modelling at design, SAST/SCA
  in CI, secrets scanning, DAST/pentest before release, SBOM, signed
  artefacts, dependency and container scanning, change approval.
- **Monitoring and response:** central log collection (Annex A 8.15/8.16),
  SIEM/EDR/NDR, retention, alert triage, playbooks, tabletop exercises.
- **Resilience:** multi-AZ/region, immutable backups, tested failover,
  DDoS protection, capacity headroom.

## 4. Supplier architecture-review checklist

| Area | Ask for / verify |
|---|---|
| Boundaries | Architecture diagram with trust zones; internet exposure; admin paths |
| Identity | IdP integration, MFA, privileged access model, service accounts |
| Data flows | What Euronext data, where processed/stored (EU), encryption, keys ownership, sub-processors |
| Segmentation | Tenant isolation model (SaaS), network segmentation, dev/prod separation |
| Secure development | SDLC evidence: threat models, code scanning, pentest cadence, SBOM |
| Operations | Patch SLAs, vulnerability management, logging/monitoring scope, incident SLAs |
| Resilience | RTO/RPO, DR tests, redundancy, backup residency |
| Change | Change/release control, customer notification |
| Exit | Portability, deletion, transition support |

## 5. Mapping

| Pattern | ISO 27001:2022 Annex A | CIS v8.1 | NIST CSF 2.0 | DORA |
|---|---|---|---|---|
| Segmentation / network security | 8.20–8.23 | 12, 13 | PR.IR | Art. 9(2)–(4) |
| Identity and access | 5.15–5.18, 8.2–8.5 | 5, 6 | PR.AA | Art. 9(4)(c),(d) |
| Data protection | 5.12–5.14, 8.10–8.12, 8.24 | 3 | PR.DS | Art. 9(3) |
| Secure SDLC | 8.25–8.29, 8.31–8.32 | 16 | PR.PS | Art. 9(4)(e), Art. 24 |
| Logging and monitoring | 8.15–8.17 | 8 | DE.CM | Art. 10 |
| Resilience | 5.29–5.30, 8.13–8.14 | 11 | RC.RP | Art. 11–12 |
| Architecture governance (TOGAF ADM security) | 5.8, 8.27 | — | GV.OC, ID.AM | Art. 6 (ICT risk framework) |
