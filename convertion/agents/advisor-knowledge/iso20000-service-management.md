# ISO/IEC 20000-1:2018 Service Management — Assurance Reference

*Advisor knowledge reference — authored 2026-09-12 to deepen the persona
claim "expert in ISO 20000". Verify against ISO/IEC 20000-1:2018 (and
ISO/IEC 20000-2 guidance) before citing.*

## 1. Clause summary

| Clause | Requirement essentials |
|---|---|
| 4 Context | Interested parties; **scope of the SMS** (services, locations, organisation); the SMS covers planning, design, transition, delivery and improvement of services |
| 5 Leadership | Service management policy, objectives, roles; **authority over other parties** involved in the service lifecycle |
| 6 Planning | Risks and opportunities; service management plan (resources, interfaces, authorities) |
| 7 Support | Resources, competence, awareness, communication, documented information; **7.6 knowledge** |
| 8 Operation | See §2 |
| 9 Performance evaluation | Monitoring/measurement, internal audit, management review, **9.4 service reporting** |
| 10 Improvement | Nonconformity and corrective action; continual improvement |

## 2. Clause 8 sub-clauses

| Sub-clause | Requirement | TPRM relevance |
|---|---|---|
| 8.1 Operational planning and control | Processes as planned | — |
| 8.2.1 Service delivery | Deliver per requirements | SLA evidence |
| 8.2.2 Plan the services | Requirements, criticality, dependencies | service criticality mapping |
| 8.2.3 Control of parties involved in the service lifecycle | Define and control processes operated by suppliers/internal groups | DORA subcontracting chain |
| 8.2.4 Service catalogue management | Catalogue with dependencies | service identification |
| 8.2.5 Asset management | Assets managed to deliver services | CMDB accuracy |
| 8.2.6 Configuration management | CIs recorded, controlled, audited | change impact analysis |
| 8.3.1–8.3.2 Business relationship management | Customers, complaints, satisfaction | — |
| 8.3.3 Service level management | Service targets agreed, monitored, reported | SLA/KPI review |
| **8.3.4 Supplier management** | Designated owner per supplier; documented agreement (scope, requirements, targets, interfaces, integration with the SMS); monitor performance; manage changes to contracts; **manage disputes**; lead suppliers manage sub-contracted suppliers | Core TPRM evidence set |
| 8.4.1 Budgeting and accounting | Costs per service | — |
| 8.4.2 Demand management | Current and forecast demand | capacity planning |
| 8.4.3 Capacity management | Capacity plan; monitor usage | resilience |
| 8.5.1 Change management | Policy for CIs under change control; **emergency change**; assessment of risk/impact; approval; review | change notice to Euronext |
| 8.5.2 Service design and transition | New/changed services designed, tested, accepted; removal of services | exit/transition |
| 8.5.3 Release and deployment management | Release policy, testing, rollback | change notification |
| 8.6.1 Incident management | Record, prioritise, escalate, resolve; **major incident** procedure | incident notification clauses |
| 8.6.2 Service request management | Fulfil requests | — |
| 8.6.3 Problem management | Root cause, known errors | recurring incidents |
| 8.7.1 Service availability management | Availability targets; monitor; unplanned unavailability investigated | SLA availability |
| 8.7.2 Service continuity management | Continuity plans per service; test; RTO/RPO-type targets | DORA Art. 11–12 |
| 8.7.3 Information security management | Policy, controls, incidents, changes assessed for security | ISMS interface |

## 3. Supplier-management evidence checklist (8.3.4)

1. Supplier owner named; contract register; agreement scope and targets.
2. Performance reports vs targets (periodic reviews, minutes).
3. Change-control records for contract changes.
4. Dispute/escalation procedure and its records.
5. Sub-contracted suppliers list with lead-supplier controls.
6. Interfaces with incident, change, continuity, security processes.

## 4. ISO 27001 ↔ ISO 20000-1 integration map

| ISO 20000-1 | ISO 27001:2022 |
|---|---|
| 8.2.5 / 8.2.6 asset and configuration | A 5.9, 8.9 |
| 8.3.4 supplier management | A 5.19–5.22 |
| 8.5.1 change management | A 8.32 |
| 8.5.3 release and deployment | A 8.19, 8.31 |
| 8.6.1 incident management | A 5.24–5.28 |
| 8.7.1 availability / 8.4.3 capacity | A 8.6, 8.14 |
| 8.7.2 service continuity | A 5.29, 5.30, 8.13 |
| 8.7.3 information security | ISMS clause 6.1 / Annex A set |
| 9.4 service reporting | ISMS 9.1 |

Integrated audits: one management-system audit programme (clauses 4–7,
9, 10 are common Annex SL text); different objects (service vs
information) — keep separate scopes and statements of applicability.
