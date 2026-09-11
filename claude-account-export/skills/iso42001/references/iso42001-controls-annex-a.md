# ISO/IEC 42001:2023 Annex A — Full Control Catalogue (38 Controls)

*Reconstructed reference — regenerated on 2026-09-11 to replace a file missing from the original skill upload; verify against the official ISO publications before relying on citations.*

Annex A of ISO/IEC 42001:2023 (normative) contains **38 controls under 9 control objectives (A.2–A.10)**. Within each theme, the ".1" item states the control objective; controls begin at ".2". Theme A.6 is subdivided into A.6.1 (development-phase objectives/processes) and A.6.2 (life cycle stages). Implementation guidance for each control is given in **Annex B** of the standard.

Every control must appear in the **Statement of Applicability** (Clause 6.1.3) with an applicability decision and justification. Applicability depends heavily on the organisation's role: **provider** controls concentrate in A.4–A.7, **user** controls in A.9 and A.10, and both roles need A.2, A.3, A.5 and A.8.

| Theme | Objective | Controls |
|-------|-----------|----------|
| A.2 | Policies related to AI | 3 |
| A.3 | Internal organization | 2 |
| A.4 | Resources for AI systems | 5 |
| A.5 | Assessing impacts of AI systems | 4 |
| A.6 | AI system life cycle | 9 |
| A.7 | Data for AI systems | 5 |
| A.8 | Information for interested parties of AI systems | 4 |
| A.9 | Use of AI systems | 3 |
| A.10 | Third-party and customer relationships | 3 |
| **Total** | | **38** |

---

## A.2 — Policies related to AI

*Objective (A.2.1): provide management direction and support for AI systems according to business requirements, laws and regulations.*

**A.2.2 AI policy** — Document a policy for the development or use of AI systems, framed by business strategy, organisational values, risk appetite and applicable law. It anchors all other AIMS documents; signed by top management (see Clause 5.2).

**A.2.3 Alignment with other organizational policies** — Determine where other policies (information security, privacy, quality, HR, procurement) can be affected by or apply to AI, and keep them consistent with the AI policy; avoid contradictory obligations.

**A.2.4 Review of the AI policy** — Review the AI policy at planned intervals and when significant changes occur (new regulation, new AI use cases, incidents) to ensure continuing suitability, adequacy and effectiveness.

---

## A.3 — Internal organization

*Objective (A.3.1): establish accountability within the organisation to uphold its responsible approach to AI.*

**A.3.2 AI roles and responsibilities** — Define and allocate roles and responsibilities for AI across the lifecycle (governance lead, system owners, data stewards, risk/impact assessors, oversight functions); document them so accountability for each AI system is unambiguous.

**A.3.3 Reporting of concerns** — Provide a process for personnel (and, as appropriate, other parties) to report concerns about the organisation's role with respect to an AI system — without fear of reprisal — and to have those concerns assessed and acted on.

---

## A.4 — Resources for AI systems

*Objective (A.4.1): ensure the organisation accounts for the resources of the AI system to fully understand and address risks and impacts.*

**A.4.2 Resource documentation** — Identify and document all resources required for each AI system lifecycle stage: data, tooling, models/algorithms, compute, and human resources. This inventory underpins risk and impact assessment.

**A.4.3 Data resources** — Document information about the data resources used for each AI system (provenance, categories, intended use in training/validation/test, rights and quality characteristics). Cornerstone for bias and privacy analysis.

**A.4.4 Tooling resources** — Document the tooling used across the AI lifecycle (frameworks, libraries, ML platforms, evaluation and monitoring tools), supporting reproducibility and supply-chain understanding.

**A.4.5 System and computing resources** — Document system and compute resources for each lifecycle stage (infrastructure, hardware/accelerators, environments), including location and capacity considerations relevant to risk (and, where relevant, environmental footprint).

**A.4.6 Human resources** — Document the human resources and their competences needed across the lifecycle (development, deployment, operation, oversight, decommissioning), including roles for human oversight of AI outputs.

---

## A.5 — Assessing impacts of AI systems

*Objective (A.5.1): assess AI system impacts on individuals, groups of individuals, and societies throughout the system life cycle.*

**A.5.2 AI system impact assessment process** — Establish a process to assess potential consequences of each AI system for individuals, groups and society across its lifecycle — the operational engine of Clause 6.1.4. See `iso42001-ai-risk-assessment.md` for methodology.

**A.5.3 Documentation of AI system impact assessments** — Document AISIA results and retain them for a defined period; make results available to relevant interested parties as appropriate (transparency and audit trail).

**A.5.4 Assessing AI system impact on individuals or groups of individuals** — Specifically assess impacts on individuals and groups: fairness/discrimination, safety, privacy, economic and legal effects, especially for vulnerable populations and automated decisions affecting rights.

**A.5.5 Assessing societal impacts of AI systems** — Assess broader societal impacts: environmental sustainability, economic and labour effects, effects on culture, norms, misinformation and democratic processes, as relevant to the system's scale and purpose.

---

## A.6 — AI system life cycle

*Objectives: A.6.1.1 — ensure responsible development objectives and processes are identified and integrated; A.6.2.1 — define lifecycle stage criteria and requirements for responsible development and operation.*

**A.6.1.2 Objectives for responsible development of AI system** — Identify and document objectives guiding responsible development (e.g., fairness, safety, transparency, robustness, privacy) and take them into account in lifecycle activities; they should be measurable where possible.

**A.6.1.3 Processes for responsible design and development of AI systems** — Define and document the specific design and development processes and lifecycle stages the organisation applies (gates, reviews, approvals), embedding responsible-AI checkpoints.

**A.6.2.2 AI system requirements and specification** — Specify and document requirements for new AI systems or material enhancements: intended purpose, performance criteria, data needs, constraints, oversight and safety requirements.

**A.6.2.3 Documentation of AI system design and development** — Document design and development choices (architecture, model selection, training approach, evaluation design) against the requirements, so decisions are traceable and reviewable.

**A.6.2.4 AI system verification and validation** — Define and apply verification and validation measures (testing against requirements, evaluation metrics including fairness/robustness where relevant, acceptance criteria) and specify when they are used.

**A.6.2.5 AI system deployment** — Document a deployment plan and verify requirements are met before release (release criteria, approvals, rollback plan, environment readiness, communication to users).

**A.6.2.6 AI system operation and monitoring** — Define and document the elements needed for ongoing operation: performance and drift monitoring, incident identification (including repair/update/support processes), and criteria triggering re-assessment.

**A.6.2.7 AI system technical documentation** — Provide technical documentation appropriate for each relevant interested party (users, operators, regulators): capabilities, limitations, instructions, oversight measures. Aligns with EU AI Act Annex IV-style expectations.

**A.6.2.8 AI system recording of event logs** — Enable automatic recording of event logs during operation of the AI system, retained to support traceability, incident investigation and accountability for outputs/decisions.

---

## A.7 — Data for AI systems

*Objective (A.7.1): ensure the organisation understands the role and impacts of data in AI systems, across acquisition, quality, provenance and preparation.*

**A.7.2 Data for development and enhancement of AI systems** — Define, document and implement data management processes for AI development (privacy/security implications, data lifecycle for training/validation/test sets).

**A.7.3 Acquisition of data** — Determine and document details about how data is acquired and selected: sources, rights and consent, licensing, collection method, and criteria for inclusion.

**A.7.4 Quality of data for AI systems** — Define and document data quality requirements (accuracy, completeness, representativeness, currency, relevance to intended purpose) and ensure the data used meets them — the primary bias-prevention control.

**A.7.5 Data provenance** — Define and document a process to record the provenance of data used over its lifecycle (origin, transformations, lineage), enabling accountability and reproducibility.

**A.7.6 Data preparation** — Define and document the data preparation criteria and methods used (cleaning, labelling, transformation, augmentation, sampling), since preparation choices materially affect model behaviour and bias.

---

## A.8 — Information for interested parties of AI systems

*Objective (A.8.1): ensure relevant interested parties have the necessary information to understand and assess the AI system and its impacts.*

**A.8.2 System documentation and information for users** — Determine and provide the necessary information to users: that they are interacting with an AI system, its purpose, capabilities, limitations, and how to use it correctly (transparency and instructions for use).

**A.8.3 External reporting** — Provide capabilities for interested parties to report adverse impacts or concerns about the AI system to the organisation (feedback/complaint channel beyond internal reporting in A.3.3).

**A.8.4 Communication of incidents** — Determine and document a plan for communicating AI system incidents to users and other affected parties (what, when, to whom), integrated with the organisation's incident response process.

**A.8.5 Information for interested parties** — Determine and document the obligations for reporting information about AI systems to other interested parties (regulators, customers, the public), including timing and content — supports regulatory disclosure duties.

---

## A.9 — Use of AI systems

*Objective (A.9.1): ensure the organisation uses AI systems responsibly and according to organisational policies.*

**A.9.2 Processes for responsible use of AI systems** — Define and document processes for responsible use of AI systems (approval of use cases, acceptable-use rules, oversight arrangements) — the anchor for an AI Acceptable Use Policy.

**A.9.3 Objectives for responsible use of AI system** — Identify and document objectives guiding responsible use (fairness, transparency to affected people, human oversight) and take them into account when using AI systems.

**A.9.4 Intended use of the AI system** — Ensure each AI system is used according to its intended purpose and the provider's documentation/instructions; detect and address off-label or scope-creep usage.

---

## A.10 — Third-party and customer relationships

*Objective (A.10.1): ensure the organisation understands its responsibilities and remains accountable when third parties are involved, and that risks are apportioned appropriately.*

**A.10.2 Allocating responsibilities** — Ensure responsibilities within the AI lifecycle are allocated between the organisation, its partners, suppliers, customers and third parties — a documented shared-responsibility model (critical when models, data and hosting come from different parties).

**A.10.3 Suppliers** — Establish a process to ensure that the organisation's use of supplier-provided services, products or materials (including third-party AI models and APIs) aligns with its responsible-AI approach: due diligence, contractual clauses, ongoing monitoring.

**A.10.4 Customers** — Ensure the responsible approach to AI considers customer requirements and expectations, and that customers receive the information and support needed to use provided AI systems responsibly.

---

## SoA Quick-Reference — Typical Applicability by Role

| Theme | AI Provider | AI User |
|-------|-------------|---------|
| A.2 Policies | Yes | Yes |
| A.3 Internal organization | Yes | Yes |
| A.4 Resources | Yes (full) | Partial (document what is known of third-party resources) |
| A.5 Impact assessment | Yes | Yes (for deployed use cases) |
| A.6 Life cycle | Yes (full) | Partial (A.6.2.5–A.6.2.6 for deployment/operation of acquired systems) |
| A.7 Data | Yes (full) | Partial (data supplied to or produced by third-party AI) |
| A.8 Information for interested parties | Yes | Yes (towards its own users/affected parties) |
| A.9 Use | If also using AI | Yes (core) |
| A.10 Third parties/customers | Yes (customers) | Yes (suppliers) |

Exclusions must be justified in the SoA; "we only use AI, we don't build it" narrows but does not blanket-exclude A.4–A.7.
