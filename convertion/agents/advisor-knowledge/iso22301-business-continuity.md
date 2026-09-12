# ISO 22301:2019 Business Continuity — Assurance Reference

*Advisor knowledge reference — authored 2026-09-12 to ground the persona
domain "ISO 22301 business continuity" for the advisor, tpa-evidence-analyzer
and the DORA/NIS2 advisors. Verify against ISO 22301:2019 and ISO 22313
guidance before citing in formal deliverables.*

## 1. Structure (Annex SL clauses)

| Clause | Requirement essentials |
|---|---|
| 4 Context | Interested parties, legal/regulatory requirements, **scope** of the BCMS (products, services, sites) |
| 5 Leadership | BC policy, roles, top-management commitment |
| 6 Planning | Risks/opportunities, BC objectives |
| 7 Support | Resources, competence, awareness, communication, documented information |
| 8 Operation | **8.2 Business impact analysis (BIA) and risk assessment**; **8.3 BC strategies and solutions**; **8.4 BC plans and procedures** (response structure, warning and communication, plans, recovery); **8.5 Exercise programme**; 8.6 Evaluation of BC documentation and capabilities |
| 9 Performance evaluation | Monitoring, internal audit, management review |
| 10 Improvement | Nonconformity, corrective action, continual improvement |

## 2. Key terms and metrics

- **BIA** determines prioritised activities and their impact over time.
- **MTPD / MAO** — maximum tolerable period of disruption before impacts
  become unacceptable.
- **RTO** — target time to resume an activity (must be < MTPD).
- **RPO** — maximum data loss tolerated (age of data at recovery).
- **MBCO** — minimum business continuity objective (minimum level of
  service acceptable during disruption).
- **Exercising:** walkthroughs, tabletop, simulation, full live tests;
  frequency and scope must be defined and results fed into improvement.

## 3. Reading a supplier's ISO 22301 certificate / BC evidence

| Check | Rule |
|---|---|
| Scope statement | Names the services and sites; must cover the service delivered to Euronext, not only HQ or another business line |
| Validity | 3-year cycle with annual surveillance; dates inside the certificate; certificate number; accreditation mark (national body under IAF) |
| Evidence beyond the certificate | Latest BIA summary, RTO/RPO for the Euronext service, DR test results (date, scenario, outcome, issues), crisis communication procedure, dependency on subcontractors' continuity |
| Cloud/hosted services | Region/zone architecture, backup location and residency, tested failover, exit and data-return capability |
| Red flags | RTO/RPO not defined per service; tests older than 12 months or "planned"; single site; untested backups; continuity relying on a subservice with no evidence |

## 4. Regulatory mapping

| Topic | DORA (EU 2022/2554) | NIS2 (EU 2022/2555) | ISO 27001:2022 Annex A |
|---|---|---|---|
| ICT business continuity policy, plans | Art. 11(1)–(4) | Art. 21(2)(c) business continuity, backup, DR, crisis management | 5.29, 5.30 (ICT readiness for BC) |
| Backup and restoration | Art. 12 | Art. 21(2)(c) | 8.13 |
| Testing of plans | Art. 11(6) at least yearly incl. critical functions; Art. 11(4) scenarios incl. cyber-attacks | Art. 21(2)(f) effectiveness assessment | 5.30 |
| Third-party continuity and exit | Art. 28(8) exit strategies; Art. 30(3)(c),(f) contractual BC/exit provisions | Art. 21(2)(d) supply-chain security | 5.19–5.22 |
| Redundancy of infrastructure | Art. 12(2) | Art. 21(2)(c) | 8.14 |
| Communication and crisis management | Art. 14 | Art. 21(2)(c) | 5.24, 5.26 |

## 5. Assurance verdict pattern

Certificate valid + scope covers the service + tested RTO/RPO meet
Euronext's MTPD → **Adequate**. Missing test evidence or scope mismatch →
**Adequate with actions** (request test report/BIA extract). No
certificate and no tests → **Inadequate** for Critical/Important services.
