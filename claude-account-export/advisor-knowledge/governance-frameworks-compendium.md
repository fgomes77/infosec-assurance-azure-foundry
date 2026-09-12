# Governance & Management Frameworks Compendium for Security Assurance

*Advisor knowledge reference — authored 2026-09-11 to ground the persona domain in the combined knowledge base; verify against the official publication before citing in formal deliverables.*

How the persona's management-framework expertise is applied to information
security assurance and TPRM work: each section states what the framework is,
then how the assurance team actually uses it.

## PMBOK 7 — delivering security programmes as projects

PMBOK Guide 7th edition (2021) moved from process groups to **12 principles**
(stewardship, team, stakeholders, value, systems thinking, leadership,
tailoring, quality, complexity, risk, adaptability/resiliency, change) and
**8 performance domains** (Stakeholders, Team, Development Approach & Life
Cycle, Planning, Project Work, Delivery, Measurement, Uncertainty).

Assurance application:

- Remediation programmes (post-audit, post-assessment supplier remediation,
  ISO 27001 certification projects) are run as projects: the **Uncertainty**
  domain hosts the project-level risk register that feeds the ISMS register;
  **Measurement** supplies the KPI discipline for control-implementation
  tracking; **Stakeholders** covers regulators, auditors and supplier contacts.
- The **tailoring** principle legitimises choosing predictive delivery for
  certification milestones and adaptive delivery for continuous-assurance
  tooling — document the tailoring decision.
- Benefits language from the **value** principle helps state security work in
  risk-reduction terms the board funds.

## ITIL 4 — service management around the controls

ITIL 4 is built on the **Service Value System (SVS)**: guiding principles,
governance, the **service value chain** (plan, improve, engage, design &
transition, obtain/build, deliver & support), 34 practices, and continual
improvement. Value is co-created with consumers through service relationships.

Practices most relevant to security and service assurance:

| ITIL 4 practice | Assurance use |
|---|---|
| Information security management | The umbrella practice — hangs the ISMS interface into service management |
| Risk management | Aligns with ISO 27005 / 31000 methods at service level |
| Supplier management | Operational twin of the TPRM programme; contracts, performance, integration |
| Service level management | Where security SLAs/XLAs (patch windows, incident response times) live and are reported |
| Incident & problem management | Feeds security incident handling (ISO 27035 alignment) and root-cause learning |
| Change enablement | The control gate that stops unassessed risk entering production (Annex A 8.32) |
| Service configuration management / IT asset management | Source of truth for asset inventory (CIS 01/02, Annex A 5.9) |
| Monitoring and event management | Detection pipeline (NIST CSF DE.CM) |
| Service continuity management | BC/DR integration (Annex A 5.29–5.30) |
| Release & deployment, service validation and testing | Secure-release evidence for audits |
| Availability & capacity and performance management | Resilience outcomes (CSF PR.IR) |
| Continual improvement | The Deming loop shared with ISMS clause 10 |

**ISO/IEC 20000-1 relationship**: ITIL 4 is the practice guidance most often
used to *implement* an ISO 20000-1 service management system (SMS); 20000-1 is
the certifiable requirements standard, ITIL the how-to. They are aligned but
not identical — an auditor certifies against 20000-1, never "against ITIL".

## COBIT 2019 — governance of enterprise I&T

COBIT distinguishes **governance** (evaluate, direct, monitor — board level)
from **management** (plan, build, run, monitor — executive level). Its core
model has 40 objectives in five domains:

- **EDM** (Evaluated, Directed, Monitored) — 5 governance objectives, e.g.
  EDM03 *Ensured Risk Optimisation*.
- **APO** (Align, Plan, Organise) — includes APO12 *Managed Risk*, APO13
  *Managed Security* (the ISMS anchor), APO10 *Managed Vendors* (the TPRM
  anchor).
- **BAI** (Build, Acquire, Implement) — change, projects, configuration.
- **DSS** (Deliver, Service, Support) — DSS05 *Managed Security Services*
  (operational security controls), DSS04 *Managed Continuity*.
- **MEA** (Monitor, Evaluate, Assess) — performance, internal control
  (MEA02), compliance (MEA03), assurance (MEA04).

**Design factors** (enterprise strategy, risk profile, threat landscape,
compliance requirements, sourcing model, IT implementation methods, etc.)
tailor a governance system to the enterprise — the analytical basis for
arguing, for example, that a heavily outsourced ICT estate must weight APO10
and third-party controls more heavily. Assurance use: COBIT gives the language
for board-level accountability questions ("who evaluates, who directs, who
monitors third-party risk?") and its capability levels (0–5, CMMI-derived)
provide a defensible maturity scale for programme reporting.

## COSO Internal Control — Integrated Framework (2013)

Five components and seventeen principles (paraphrased):

| Component | Principles (condensed) |
|---|---|
| Control Environment | 1 integrity & ethics; 2 board oversight independence; 3 structures, reporting lines, authorities; 4 competence commitment; 5 accountability |
| Risk Assessment | 6 suitable objectives; 7 identify & analyse risk; 8 assess fraud risk; 9 identify & assess significant change |
| Control Activities | 10 select & develop control activities; 11 general controls over technology; 12 deploy through policies & procedures |
| Information & Communication | 13 relevant quality information; 14 internal communication; 15 external communication |
| Monitoring Activities | 16 ongoing and separate evaluations; 17 evaluate & communicate deficiencies |

Effective internal control requires all five components present, functioning
and operating together. **ERM linkage**: COSO ERM (2017, "Integrating with
Strategy and Performance") sits above ICIF — ERM sets appetite and
strategy-level risk decisions; ICIF assures the controls executing them.
Assurance use: SOX-style ICFR testing, mapping security controls into the
enterprise control framework, and framing IT general controls (principle 11)
so internal audit and infosec test once, satisfy both. In TPRM, COSO is the
lens external auditors bring to SOC reports — SOC 2 control environments are
described in COSO terms, which is why we read Section III of a SOC 2 before
the control matrix.

## TOGAF 10 — where security architecture engages

The TOGAF Standard, 10th Edition organises the **ADM** (Architecture
Development Method) phases: Preliminary; A Architecture Vision; B Business
Architecture; C Information Systems Architectures (data + application);
D Technology Architecture; E Opportunities & Solutions; F Migration Planning;
G Implementation Governance; H Architecture Change Management; with
Requirements Management at the centre.

Security engagement points:

- **Preliminary/A**: security principles, risk appetite and regulatory
  constraints enter the architecture principles catalogue; security architect
  is named as a stakeholder.
- **B–D**: security requirements shape each layer — data classification and
  flows (C), trust zones, control placement and shared-responsibility
  boundaries (D). The Open Group's integration guidance (SABSA alignment,
  Enterprise Security Architecture practitioner guidance) rides here.
- **E–F**: security work packages priced and sequenced into the roadmap
  rather than bolted on later.
- **G**: architecture compliance reviews are an assurance control — deviations
  become risk-register entries.
- **H + Requirements Management**: threat-landscape and regulatory change
  drive architecture change requests.

Assurance use: TOGAF artefacts (solution building blocks, data-flow views)
are first-rate evidence for supplier architecture reviews and DPIA data
mapping; conversely, TPRM findings should feed phase H as change drivers.

## Agile and Lean IT in security work

- **Iterative assurance**: run assessments in timeboxed increments with a
  ranked backlog (highest-risk suppliers/controls first) instead of annual
  big-bang cycles; definition-of-done includes evidence captured and register
  updated. Security requirements enter product backlogs as acceptance criteria
  and abuser stories; "compliance as code" pipelines make control evidence a
  build artefact.
- **Lean waste in control operation** (translated from the classic seven):
  over-processing = collecting evidence nobody evaluates; inventory = finding
  backlogs aging past relevance; waiting = approvals queued on single
  reviewers; defects = false-positive alerts and rework of rejected supplier
  responses; motion/transport = swivel-chair transfer between GRC tools;
  over-production = reports no decision consumes. Value-stream mapping the
  supplier assessment pipeline routinely halves cycle time.
- Guardrail: iteration never waives mandatory control gates (change approval,
  risk acceptance authority); agility is about batch size, not skipping
  governance.

## ISO/IEC 20000-1:2018 — the SMS and its ISMS interface

Harmonized-structure clauses: 4 context, 5 leadership, 6 planning, 7 support,
8 operation, 9 performance evaluation, 10 improvement. Clause 8 carries the
service-management specifics: 8.2 service portfolio, 8.3 relationship and
agreement (business relationship, service level, **supplier management**),
8.4 supply and demand, 8.5 service design/build/transition, 8.6 resolution and
fulfilment (incident, service request, problem), 8.7 **service assurance** —
availability, continuity, **information security management** (8.7.3).

ISMS interface: 8.7.3 requires an information security policy, risk-treated
security controls, and security-incident handling inside the SMS — organisations
running both 20000-1 and 27001 integrate them: one risk method, one incident
process with a security classification branch, shared internal audit and
management review. Clause 8.3.4 supplier management is the SMS hook for TPRM:
documented supplier contracts, defined service integration, and performance
monitoring — evidence the assurance team can reuse when the supplier is also a
data processor.

## Cloud and ICT service assurance

- **Shared responsibility**: assurance scope depends on the service model —
  IaaS leaves guest OS upward to the customer; SaaS leaves mainly identity,
  data and configuration. Always draw the boundary before assessing; "the
  provider is certified" only covers the provider's side of the line.
- **Evidence stack**: SOC 2 Type II (operating effectiveness over a period —
  read scope, period, CUECs/complementary user entity controls, exceptions and
  subservice carve-outs); ISO/IEC 27001 certificate (check scope statement and
  the certificate covers the entity actually serving you); **ISO/IEC 27017**
  (cloud-specific control guidance for provider and customer); **ISO/IEC
  27018** (PII protection in public cloud for processors); CSA STAR/CAIQ as a
  structured questionnaire baseline. For EU financial entities, layer DORA
  Art. 30 contract provisions and the Register of Information on top.
- Contract-side assurance: exit and portability, data location and transfer
  terms (see the Art. 28/SCC reference), sub-outsourcing notification,
  audit/pooled-audit rights, incident notification windows.

## Cross-walk: framework → what the assurance team uses it for

| Framework | Primary assurance use |
|---|---|
| PMBOK 7 | Structuring remediation and certification programmes; project risk feeding the ISMS register; benefits framing for security investment |
| ITIL 4 | Operational home of security-relevant service practices; SLAs, change gates, asset/config truth, incident pipeline |
| COBIT 2019 | Board-level governance language; EDM/APO/BAI/DSS/MEA objective mapping; capability-level maturity reporting; design-factor tailoring arguments |
| COSO ICIF 2013 | Internal-control framing for audits and SOC report interpretation; ITGC alignment; ERM linkage for appetite-setting |
| TOGAF 10 | Security engagement in architecture lifecycle; architecture evidence for supplier reviews; compliance reviews as controls |
| Agile / Lean IT | Iterative, backlog-driven assurance delivery; waste elimination in control operation and assessment pipelines |
| ISO/IEC 20000-1:2018 | Certifiable SMS whose 8.7.3 and 8.3.4 clauses interface the ISMS and TPRM; integrated audits |
| ISO 27017 / 27018 / SOC 2 | Cloud supplier evidence evaluation under the shared-responsibility boundary |

## Practitioner caution

These frameworks overlap by design; the skill is choosing one *lens per
question* (governance → COBIT, delivery → PMBOK/agile, operations → ITIL/20000,
control assurance → COSO, structure → TOGAF) and mapping the answer back to
the ISMS rather than running all frameworks in parallel bureaucracies.
