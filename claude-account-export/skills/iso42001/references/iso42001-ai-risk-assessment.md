# AI Risk Assessment & AI System Impact Assessment — Methodology Guide

*Reconstructed reference — regenerated on 2026-09-11 to replace a file missing from the original skill upload; verify against the official ISO publications before relying on citations.*

This guide operationalises **Clause 6.1.2 (AI risk assessment)** and **Clause 6.1.4 (AI system impact assessment, AISIA)** of ISO/IEC 42001:2023, drawing on **ISO/IEC 23894** (AI risk management guidance), **ISO/IEC 42005** (AI system impact assessment guidance) and **ISO 31000** (risk management principles). The two processes are distinct but coupled:

| | AI risk assessment (6.1.2) | AISIA (6.1.4) |
|---|---|---|
| Lens | Risk **to the organisation** and its objectives (and to affected parties as risk sources) | Consequences **for individuals, groups and society** |
| Unit | Risk scenario (likelihood × severity) | AI system / use case (impact profile) |
| Output | Risk register, prioritised for treatment | Impact record informing control selection, transparency and oversight |
| Flow | AISIA results are a mandatory **input** to the risk assessment | Performed per system, refreshed on significant change |

---

## 1. Risk Criteria (Clause 6.1.1)

Define and document before assessing:

- **Likelihood scale** (e.g., 1–5: rare → almost certain), with AI-specific anchors (e.g., "drift expected within a retraining cycle" vs. "requires deliberate adversarial effort").
- **Severity scale** (1–5), scored on the worst credible consequence across dimensions: harm to individuals, legal/regulatory exposure, financial loss, reputational damage, operational disruption.
- **Risk acceptance thresholds** — which scores are acceptable, which require treatment, which require escalation to top management.
- **AISIA trigger criteria** — when an impact assessment is required: new AI system or use case, material model change/retrain, new data source, new affected population, deployment into a sensitive domain, or a relevant incident.
- **Roles**: risk owners approve treatment (Clause 6.1.3); assessors must include people who understand both the technology and the deployment context.

---

## 2. AI-Specific Harm Taxonomy

Use this taxonomy to structure both risk identification and AISIA consequence analysis. Every category should be explicitly considered (and "not applicable" recorded where justified).

| Category | Typical harms | Example scenarios |
|----------|--------------|-------------------|
| **Bias / discrimination** | Unfair outcomes for protected or vulnerable groups; disparate error rates | Recruitment screening disadvantaging a demographic; credit scoring proxy discrimination |
| **Safety** | Physical or psychological harm from AI-influenced actions | Faulty perception in autonomous equipment; unsafe medical triage suggestion |
| **Privacy** | Unlawful processing, re-identification, training-data leakage, surveillance overreach | Model memorises and regurgitates PII; inference of sensitive attributes |
| **Transparency / explainability** | Affected people cannot understand or contest decisions; hidden AI interaction | Unexplained automated rejection; chatbot not disclosed as AI |
| **Robustness / reliability** | Wrong outputs under distribution shift, drift, adversarial input; hallucination | Model drift degrading fraud detection; prompt injection; confidently false generated content |
| **Misuse / malicious use** | Use beyond intended purpose; enabling fraud, disinformation, harassment | Off-label use of an internal model; generated content used for phishing |
| **Environmental** | Excessive energy/water consumption from training and inference | Large-model retraining without necessity review |
| **Societal** | Labour displacement, erosion of human autonomy, misinformation at scale, chilling effects | Over-reliance deskilling operators; recommender amplifying polarising content |

Also assess **security-of-AI** risks jointly with the ISMS where one exists: data poisoning, model theft/extraction, adversarial evasion, supply-chain compromise of models and datasets.

---

## 3. Assessment Process — Step by Step

### 3.1 AI risk assessment (6.1.2)

1. **Inventory** — start from the AI system register (Clause 4.3 / A.4.2); one assessment scope per system or coherent use case.
2. **Establish context** — intended purpose, role (provider/user), lifecycle stage, dependencies (data, models, suppliers), applicable law.
3. **Identify risks** — walk the harm taxonomy plus operational and supply-chain categories; use the AISIA output to identify risks arising from impacts on others (liability, regulatory, reputational).
4. **Analyse** — score likelihood × severity per scenario; note detectability/oversight as a modifier where the methodology allows.
5. **Evaluate** — compare against acceptance criteria; prioritise.
6. **Treat (6.1.3)** — options: **modify** the system (retrain, guardrails, constrain scope), **accept with monitoring** (thresholds and alerting defined), **avoid** (do not deploy for this use case), **share/transfer** (contractual allocation via A.10). Select controls, verify against Annex A, update the **SoA**, and get risk-owner approval of the treatment plan.
7. **Record and repeat** — retain results; re-run at planned intervals and on significant change (Clause 8.2).

**Risk register columns:** AI System | Lifecycle Stage | Risk Category | Scenario | Existing Controls | Likelihood (1–5) | Severity (1–5) | Score | Evaluation | Treatment | Annex A Controls | Owner | Due Date | Residual Risk.

### 3.2 AI system impact assessment (6.1.4, aligned to ISO/IEC 42005 guidance)

1. **Scope the assessment** — system, version, deployment context, and the trigger that initiated it.
2. **Describe the system** — intended purpose and uses, **reasonably foreseeable misuse**, output type (prediction/decision/content/recommendation), degree of autonomy, human oversight arrangements.
3. **Identify interested parties** — directly affected individuals, groups (with attention to vulnerable populations: children, patients, job applicants, benefit claimants), and societal stakeholders.
4. **Analyse potential impacts** — both **harms and benefits**, per taxonomy category, for each affected party; consider scale (how many affected), severity, probability, and **reversibility/remediability** of harm.
5. **Classify impact level** — e.g., Low / Medium / High per the skill's classification table; classification drives control implications (enhanced transparency, mandatory human review, right to challenge).
6. **Determine measures** — oversight, transparency and disclosure measures (A.8), design mitigations (A.6), data measures (A.7).
7. **Document and integrate** — record per A.5.3; feed results into the risk assessment and SoA; make available to interested parties as appropriate.
8. **Review** — on the defined triggers and at planned intervals (Clause 8.4).

**AISIA record fields:** System & version | Trigger | Intended purpose | Foreseeable misuse | Output type & autonomy | Affected parties (incl. vulnerable groups) | Impacts per category (harm/benefit, severity, scale, reversibility) | Impact level | Oversight & transparency measures | Residual concerns | Assessor & approver | Date & next review.

---

## 4. Roles

| Role | Responsibility |
|------|----------------|
| Top management | Approve risk criteria and acceptance thresholds; review high-impact findings (Clause 9.3) |
| AI governance lead / AIMS owner | Own methodology; ensure coverage and cadence |
| AI system owner | Initiate assessments for their system; own treatment actions |
| Risk owner | Approve risk treatment plan and residual risk (6.1.3) |
| Assessors (multidisciplinary) | Data science/ML, legal/privacy, security, domain experts, ethics; affected-party representation where feasible |
| Internal audit | Verify the processes operate as documented (Clause 9.2) |

---

## 5. Integration with ISO 31000

The 6.1.2 process instantiates the ISO 31000 cycle: **scope/context/criteria → risk identification → analysis → evaluation → treatment**, wrapped in **communication & consultation** and **monitoring & review**. Practical implications:

- Reuse the enterprise risk methodology where one exists — extend scales with AI-specific anchors rather than inventing a parallel framework, so AI risks can roll up into enterprise risk reporting.
- ISO/IEC 23894 provides the AI-specific elaboration of 31000; cite it when defending methodology choices to auditors.
- If the organisation runs an ISO 27001 ISMS, run AI security risks through the ISMS risk process and cross-reference — one risk, one treatment, two SoAs where applicable.

---

## 6. Cross-Walk — EU AI Act Risk Tiers

The AISIA is the natural vehicle for EU AI Act classification. Map every assessed system to a tier and record the rationale:

| EU AI Act tier | Meaning | AISIA/AIMS implication |
|----------------|---------|------------------------|
| **Prohibited** (Art. 5) | Unacceptable-risk practices (e.g., social scoring, manipulative techniques, certain biometric uses) | Treatment = **avoid**; do not deploy |
| **High-risk** (Art. 6 + Annex III) | Safety components and listed use areas (employment, credit, education, essential services, law enforcement, etc.) | Expect AISIA level High; full provider/deployer obligations (risk management system, data governance, technical documentation, logging, human oversight, conformity assessment) — 42001 controls A.5–A.8 supply much of the evidence |
| **Limited risk** (Art. 50) | Transparency-triggering systems (chatbots, deepfakes, emotion recognition disclosure) | Transparency measures via A.8.2; disclosure records |
| **Minimal risk** | Everything else | Standard AIMS controls; voluntary codes |

GPAI model obligations (Arts. 51–55) sit alongside the tiers — if the organisation provides general-purpose models, record systemic-risk evaluation in the risk register. Note: an ISO 42001 certificate supports but does **not** substitute for EU AI Act conformity assessment.

## 7. Cross-Walk — NIST AI RMF Functions

| NIST AI RMF function | 42001 counterpart |
|----------------------|-------------------|
| **Govern** | Clauses 4–5, 7, 9–10; A.2 (policies), A.3 (roles), A.10 (third parties) |
| **Map** | Clause 4 context, AI system register; A.4 (resources), A.5 (impact assessment), 6.1.4 |
| **Measure** | 6.1.2 risk analysis; A.6.2.4 (verification & validation), A.7.4 (data quality), Clause 9.1 metrics |
| **Manage** | 6.1.3/8.3 treatment; A.6.2.6 (operation & monitoring), A.8.4 (incident communication), Clause 10 |

NIST's trustworthy-AI characteristics (valid & reliable, safe, secure & resilient, accountable & transparent, explainable & interpretable, privacy-enhanced, fair with harmful bias managed) map directly onto the harm taxonomy in §2 — use them as a completeness check on risk identification.

---

## 8. Common Audit Findings

1. AISIA and risk assessment merged into a single generic exercise — auditors expect two distinguishable processes with the AISIA feeding the risk assessment.
2. Impact assessed only for the intended use — **foreseeable misuse** not considered.
3. No defined re-assessment triggers, or triggers defined but never fired despite model changes.
4. Severity scored only on organisational loss — harm to affected individuals absent from criteria.
5. Vulnerable groups not identified among affected parties.
6. Risk treatment "accept" chosen without monitoring thresholds or risk-owner sign-off.
7. Third-party AI (SaaS AI features) missing from the register entirely, so never assessed.
