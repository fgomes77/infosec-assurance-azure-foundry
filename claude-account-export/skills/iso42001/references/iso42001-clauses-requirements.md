# ISO/IEC 42001:2023 — Clause-by-Clause Requirements (Clauses 4–10)

*Reconstructed reference — regenerated on 2026-09-11 to replace a file missing from the original skill upload; verify against the official ISO publications before relying on citations.*

ISO/IEC 42001:2023 follows the Harmonized Structure (HLS / Annex SL), so clauses 4–10 mirror ISO 27001/9001/14001 — with AI-specific additions, most notably the **AI risk assessment (6.1.2)**, **AI risk treatment with SoA (6.1.3)** and the **AI system impact assessment (6.1.4)**. Cite clauses precisely (e.g., "Clause 6.1.4") in all outputs.

---

## Clause 4 — Context of the Organisation

### 4.1 Understanding the organisation and its context
Determine external and internal issues relevant to the AIMS and its intended outcomes. AI-specific expectation: consider the organisation's **role(s)** with respect to AI systems (provider, developer, user, importer/distributor, data provider, relevant authority) and the climate/regulatory/societal context of its AI use.
- **Auditor expects**: documented context analysis (PESTLE or equivalent) that names AI roles; evidence of periodic refresh.
- **Documented information**: context analysis, AI role determination.

### 4.2 Understanding the needs and expectations of interested parties
Identify interested parties relevant to the AIMS and their relevant requirements (including legal/regulatory — e.g., EU AI Act, sector rules) and decide which will be addressed through the AIMS.
- **Auditor expects**: stakeholder/interested-party register mapping parties to requirements, including affected individuals and society (not only customers and regulators).
- **Documented information**: interested-party register, applicable requirements list.

### 4.3 Determining the scope of the AI management system
Define AIMS boundaries and applicability, considering the issues (4.1), requirements (4.2) and the organisation's AI roles. Scope must be available as documented information.
- **Auditor expects**: a scope statement naming the AI systems, products/services, organisational units, locations and roles in scope, with justified exclusions.
- **Documented information**: AIMS scope document; in practice, an **AI system register** underpins it.

### 4.4 AI management system
Establish, implement, maintain and continually improve the AIMS, including needed processes and their interactions.
- **Auditor expects**: process map or AIMS manual showing how AIMS processes interact with existing management systems (e.g., ISMS).

---

## Clause 5 — Leadership

### 5.1 Leadership and commitment
Top management must demonstrate leadership: ensuring the AI policy and objectives are set and compatible with strategy, integrating AIMS requirements into business processes, resourcing the AIMS, communicating its importance, and promoting continual improvement.
- **Auditor expects**: interview evidence from top management; management review participation; resourcing decisions traceable to AIMS needs.

### 5.2 AI policy
Establish an AI policy appropriate to the organisation's purpose that provides a framework for AI objectives, includes commitments to meet applicable requirements and to continual improvement, and considers alignment with other organisational policies. It must be documented, communicated, and available to interested parties as appropriate.
- **Auditor expects**: signed, versioned AI policy referencing responsible-AI principles (fairness, transparency, safety, accountability, privacy, human oversight) and its relationship to security/quality/privacy policies.
- **Documented information**: AI policy (mandatory).

### 5.3 Roles, responsibilities and authorities
Assign and communicate responsibilities and authorities for AIMS conformity and for reporting AIMS performance to top management.
- **Auditor expects**: RACI or role descriptions (e.g., AI governance lead, AI system owners, data stewards); evidence people know their roles.

---

## Clause 6 — Planning

### 6.1 Actions to address risks and opportunities

**6.1.1 General** — When planning, consider the issues (4.1) and requirements (4.2) and determine risks/opportunities that need addressing to assure the AIMS achieves its outcomes, prevent undesired effects and achieve continual improvement. Define and document **risk criteria**, including criteria for when AI system impact assessments are triggered.

**6.1.2 AI risk assessment** — Define and apply an AI risk assessment process that: is aligned with the risk criteria; identifies risks related to the development, provision or use of AI systems; analyses likelihood and consequences; and evaluates risks against criteria and prioritises for treatment. Results must be repeatable, comparable and retained.
- **Auditor expects**: documented methodology; a risk register covering every in-scope AI system; evidence of re-assessment on change.
- **Documented information**: AI risk assessment process and results (mandatory).

**6.1.3 AI risk treatment** — Select treatment options, determine necessary controls (comparing with Annex A to verify no necessary control is omitted), produce a **Statement of Applicability** listing necessary controls with justification for inclusion and exclusion, and formulate an AI risk treatment plan approved by risk owners.
- **Auditor expects**: SoA covering all Annex A controls (A.2–A.10, 38 controls) with per-control applicability decisions; treatment plan with owners and dates; risk-owner approval records.
- **Documented information**: risk treatment process, SoA, risk treatment plan (mandatory).

**6.1.4 AI system impact assessment** — Define and apply a process to assess the potential consequences of AI systems for **individuals, groups of individuals and societies** across the system lifecycle. Consider intended use, foreseeable misuse, technical/societal context, and legal requirements. Results must be documented, retained, and used as an input to the risk assessment (6.1.2) and, as appropriate, made available to interested parties. See `iso42001-ai-risk-assessment.md` for methodology (aligned to ISO/IEC 42005 guidance).
- **Auditor expects**: an AISIA record per in-scope AI system, refreshed on significant change; traceability from AISIA findings into risk register and control selection.
- **Documented information**: AISIA process and results (mandatory).

### 6.2 AI objectives and planning to achieve them
Establish measurable AI objectives at relevant functions/levels, consistent with the AI policy, monitored, communicated and updated; plan what will be done, resources, responsibility, timescale and evaluation of results.
- **Auditor expects**: objectives with metrics and targets (not just principles); progress tracking evidence.
- **Documented information**: AI objectives and achievement plans (mandatory).

### 6.3 Planning of changes
Changes to the AIMS must be carried out in a planned manner.
- **Auditor expects**: change records showing AIMS impacts considered (e.g., new AI system onboarding triggering scope, risk and AISIA updates).

---

## Clause 7 — Support

### 7.1 Resources
Determine and provide resources for the AIMS (people, compute, data, tooling, budget).

### 7.2 Competence
Determine necessary competence for people affecting AI performance, ensure competence (education, training, experience), take actions to acquire it, and retain evidence.
- **Auditor expects**: competence matrix for AI-relevant roles (data science, ML engineering, AI ethics/governance); training records; gap-closure actions.
- **Documented information**: competence evidence (mandatory).

### 7.3 Awareness
Persons doing work under the organisation's control must be aware of the AI policy, their contribution to AIMS effectiveness, and implications of nonconformity.
- **Auditor expects**: awareness programme covering responsible-AI expectations for all staff who build or use AI, not just specialists.

### 7.4 Communication
Determine internal and external communications relevant to the AIMS: what, when, with whom, and how.
- **Auditor expects**: communication plan including transparency communications to users/affected parties (links to Annex A.8).

### 7.5 Documented information
Create, update and control documented information required by the standard and needed for AIMS effectiveness: identification, format, review/approval, availability, protection, distribution, retention and disposition; control documents of external origin.
- **Auditor expects**: document control procedure (may be shared with an existing ISMS/QMS); version-controlled AIMS documents.

---

## Clause 8 — Operation

### 8.1 Operational planning and control
Plan, implement and control processes needed to meet requirements and implement the actions from Clause 6; control planned changes, review unintended changes, and ensure **externally provided processes, products or services relevant to the AIMS are controlled** (critical for third-party AI models/APIs).
- **Auditor expects**: operational procedures for AI lifecycle stages; criteria for process control; evidence that outsourced/third-party AI is governed (links to Annex A.10).
- **Documented information**: evidence processes were carried out as planned (mandatory).

### 8.2 AI risk assessment (operational)
Perform AI risk assessments at planned intervals and when significant changes occur; retain results.
- **Auditor expects**: dated, repeated assessments — not a single point-in-time exercise.

### 8.3 AI risk treatment
Implement the AI risk treatment plan and retain results; re-treat when assessments surface new risks.

### 8.4 AI system impact assessment (operational)
Perform AISIAs at planned intervals or upon significant change, per the 6.1.4 process; retain results.
- **Auditor expects**: triggers defined (new system, new use case, model retrain, new affected population) and demonstrably firing.

---

## Clause 9 — Performance Evaluation

### 9.1 Monitoring, measurement, analysis and evaluation
Determine what to monitor and measure (including AI system performance against intended purpose — accuracy, drift, fairness metrics as applicable), methods, timing and responsibility; evaluate AIMS performance and effectiveness; retain evidence.
- **Documented information**: monitoring and measurement results (mandatory).

### 9.2 Internal audit
Conduct internal audits at planned intervals to verify the AIMS conforms to the organisation's own requirements and to ISO 42001, and is effectively implemented. Establish an audit programme (frequency, methods, responsibilities, reporting), define criteria and scope per audit, select objective/impartial auditors, report results to management, and retain evidence.
- **Auditor expects**: at least one full internal audit cycle before Stage 2; auditor independence from the AI work audited.
- **Documented information**: audit programme and audit results (mandatory).

### 9.3 Management review
Top management reviews the AIMS at planned intervals. Inputs: status of prior actions, changes in issues/requirements, AIMS performance (nonconformities, monitoring results, audit results, objectives), interested-party feedback, risk assessment/treatment status, and improvement opportunities. Outputs: decisions on improvement and any AIMS changes.
- **Auditor expects**: minutes evidencing genuine top-management engagement with AI-specific inputs (incidents, AISIA outcomes, regulatory change such as EU AI Act milestones).
- **Documented information**: management review results (mandatory).

---

## Clause 10 — Improvement

### 10.1 Continual improvement
Continually improve the suitability, adequacy and effectiveness of the AIMS.

### 10.2 Nonconformity and corrective action
On nonconformity: react and deal with consequences; evaluate the need to eliminate root causes; implement actions; review effectiveness; update AIMS if needed. Retain evidence of the nature of nonconformities, actions taken and results.
- **Auditor expects**: a live nonconformity/corrective-action log — including AI incidents treated as improvement inputs (bias findings, model failures, misuse events).
- **Documented information**: nonconformity and corrective action records (mandatory).

---

## Mandatory Documented Information — Quick Checklist

| Clause | Document/Record |
|--------|-----------------|
| 4.3 | AIMS scope |
| 5.2 | AI policy |
| 6.1.2 / 8.2 | AI risk assessment process + results |
| 6.1.3 / 8.3 | AI risk treatment process, **Statement of Applicability**, treatment plan + results |
| 6.1.4 / 8.4 | AI system impact assessment process + results |
| 6.2 | AI objectives |
| 7.2 | Competence evidence |
| 8.1 | Operational planning/control evidence |
| 9.1 | Monitoring and measurement results |
| 9.2 | Internal audit programme + results |
| 9.3 | Management review results |
| 10.2 | Nonconformities + corrective actions |
