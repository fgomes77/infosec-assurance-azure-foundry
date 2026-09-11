# High-Risk AI System Obligations — EU AI Act (Regulation (EU) 2024/1689)

*Reconstructed reference — regenerated on 2026-09-11 to replace a file missing from the original skill upload; verify against the official texts (EUR-Lex) before relying on citations.*

Detailed requirements for high-risk AI systems: the substantive requirements of Chapter III Section 2 (Arts. 8–15), provider duties (Arts. 16–17), value-chain provisions (Art. 25), deployer duties (Arts. 26–27), conformity assessment and CE marking (Arts. 43–48), and registration (Art. 49). Requirements apply from **2 August 2026** (Annex III systems) / **2 August 2027** (Art. 6(1) Annex I systems).

Art. 8 frames the section: high-risk systems must comply with Arts. 9–15 taking into account intended purpose and the generally acknowledged state of the art, with the Art. 9 risk management system as the lens for how compliance is achieved.

---

## Art. 9 — Risk Management System

A **continuous, iterative process planned and run throughout the entire lifecycle**, requiring regular systematic review and updating. Steps (Art. 9(2)):

1. **Identify and analyse** known and reasonably foreseeable risks to health, safety, and fundamental rights when used per intended purpose;
2. **Estimate and evaluate** risks arising under intended purpose and under **reasonably foreseeable misuse**;
3. **Evaluate other risks** emerging from post-market monitoring data (Art. 72);
4. **Adopt targeted risk management measures** addressing the identified risks.

Measures hierarchy (Art. 9(5)): (a) eliminate or reduce risks as far as technically feasible through design and development; (b) mitigation and control measures for risks that cannot be eliminated; (c) information/instructions to deployers and, where appropriate, training. Residual risk (overall and per hazard) must be judged **acceptable**.

Testing (Art. 9(6)–(8)): test against prior-defined metrics and probabilistic thresholds appropriate to intended purpose, at any point in development and before placing on market; real-world testing per Art. 60 where used. Art. 9(9): specific consideration of impact on **persons under 18 and other vulnerable groups**. Art. 9(10): providers subject to other Union-law risk-management requirements (e.g. MDR) may integrate this into those procedures.

**Evidence:** risk management plan/file, hazard log with acceptance rationale, test reports tied to defined metrics, review records showing lifecycle iteration.

## Art. 10 — Data and Data Governance

Training, validation, and testing datasets must be subject to **data governance and management practices appropriate for the intended purpose**, covering (Art. 10(2)): design choices; data origin and (for personal data) original collection purpose; preparation operations (annotation, labelling, cleaning, enrichment, aggregation); formulation of assumptions about what the data measures/represents; assessment of availability, quantity, suitability; **examination for possible biases** likely to affect health/safety/fundamental rights or produce prohibited discrimination; **measures to detect, prevent and mitigate** those biases; identification of relevant data gaps and how they are addressed.

Art. 10(3): datasets must be **relevant, sufficiently representative, and to the best extent possible free of errors and complete in view of the intended purpose**, with appropriate statistical properties for the persons/groups on whom the system is intended to be used. Art. 10(4): account for characteristics particular to the specific geographical, contextual, behavioural, or functional setting of use.

Art. 10(5) **special-category data for bias detection/correction** — permitted only where strictly necessary and all conditions met: no synthetic/anonymised alternative suffices; technical limitations on re-use plus state-of-the-art security and privacy measures (incl. pseudonymisation); strict access controls and documentation; no transmission or transfer to other parties; deletion once bias is corrected or retention period ends; DPO records under GDPR Art. 30 / EUDPR.

Art. 10(6): for high-risk systems **not** using model-training techniques, paragraphs 2–5 apply only to the testing datasets.

## Art. 11 — Technical Documentation (Annex IV)

Drawn up **before** placing on the market / putting into service; kept up to date. Must demonstrate compliance with Arts. 9–15 and give authorities the information needed to assess it. **Annex IV content:** (1) general description (intended purpose, provider, version, interactions with hardware/software, forms of placing on market, hardware requirements, product photographs/illustrations, deployer UI, instructions for use); (2) detailed description of elements and development process (methods, third-party/pre-trained components, design specifications and logic, architecture, data requirements per Art. 10, human oversight measures per Art. 14, pre-determined changes and continuous-learning arrangements, validation and testing procedures, metrics, logs of testing, cybersecurity measures); (3) monitoring, functioning, and control information; (4) appropriateness of performance metrics; (5) risk management system per Art. 9; (6) lifecycle changes; (7) list of harmonised standards applied (or other solutions); (8) copy of the EU declaration of conformity; (9) post-market monitoring plan per Art. 72.

SMEs including startups may provide the Annex IV elements in a **simplified form** via the Commission's SME template (Art. 11(1)). Annex I products: one single set of documentation combining AI Act and sectoral content.

## Art. 12 — Record-Keeping (Logging)

The system must **technically allow automatic recording of events (logs)** over its lifetime, ensuring traceability appropriate to intended purpose — in particular to identify Art. 79(1) risk situations and substantial modifications, and to facilitate Art. 72 post-market monitoring and Art. 26(5) deployer monitoring. For Annex III 1(a) remote biometric identification, minimum log content: period of each use (start/end date and time), the reference database checked, input data yielding a match, identification of natural persons involved in verification of results (Art. 12(3)). Log retention: provider — Art. 19 (appropriate to purpose, ≥6 months unless other law provides); deployer — Art. 26(6) (≥6 months).

## Art. 13 — Transparency and Provision of Information to Deployers

Design so operation is **sufficiently transparent for deployers to interpret output and use it appropriately**, and to enable both parties to meet their obligations. **Instructions for use** must be concise, complete, correct, clear, relevant, accessible, comprehensible, and include: provider identity/contact; characteristics, capabilities and **limitations of performance** — intended purpose; accuracy (incl. metrics), robustness and cybersecurity levels tested against and foreseeable circumstances affecting them; known/foreseeable circumstances of risk under intended use and reasonably foreseeable misuse; technical capabilities to explain output where applicable; performance regarding specific persons/groups; input-data specifications; information to interpret output; pre-determined changes; Art. 14 human oversight measures (incl. technical measures aiding interpretation); computational/hardware needs, expected lifetime, maintenance and care; mechanisms for deployers to collect, store and interpret logs.

## Art. 14 — Human Oversight

Design (incl. human-machine interface tools) so natural persons can **effectively oversee** the system while in use, aiming to prevent or minimise risks to health, safety, and fundamental rights. Measures may be built into the system by the provider and/or identified for implementation by the deployer. Oversight persons must be enabled, as appropriate and proportionate, to (Art. 14(4)):

- (a) properly understand capacities and limitations and duly monitor operation (incl. anomaly, dysfunction and unexpected-performance detection);
- (b) remain aware of **automation bias** (over-reliance);
- (c) correctly interpret output, considering available interpretation tools/methods;
- (d) decide **not to use** the system or otherwise disregard, override or reverse its output;
- (e) intervene or **interrupt via a "stop" button** or similar procedure halting in a safe state.

Reinforced rule (Art. 14(5)): for Annex III 1(a) RBI, no action/decision on the basis of an identification unless **separately verified and confirmed by at least two natural persons** with competence, training, and authority (derogation for law enforcement/migration/border/asylum where disproportionate under Union/national law).

## Art. 15 — Accuracy, Robustness and Cybersecurity

Achieve **appropriate levels** of accuracy, robustness, and cybersecurity, performing consistently throughout the lifecycle. Accuracy levels and relevant metrics must be **declared in the instructions for use** (Art. 15(3)). Robustness: resilience to errors, faults, inconsistencies, and to interaction with persons or other systems; technical redundancy solutions (backup/fail-safe plans) as appropriate. **Continuous-learning systems:** eliminate or reduce as far as possible the risk of biased outputs influencing future input (**feedback loops**), with mitigations addressed. Cybersecurity: resilience against attempts by unauthorised third parties to alter use, outputs, or performance by exploiting vulnerabilities — solutions to prevent, detect, respond to, resolve and control **data poisoning, model poisoning, adversarial examples/model evasion, confidentiality attacks, and model flaws**. Commission benchmarking guidance via Art. 15(2).

## Art. 16 — Provider Obligations (checklist)

Providers of high-risk AI systems shall: (a) ensure compliance with Arts. 9–15; (b) indicate name/trade mark and contact address on the system, packaging, or documentation; (c) have an Art. 17 QMS; (d) keep Art. 18 documentation (10 years); (e) keep automatically generated logs under their control (Art. 19); (f) undergo the relevant Art. 43 conformity assessment before placing on market; (g) draw up the EU declaration of conformity (Art. 47); (h) affix CE marking (Art. 48); (i) register in the EU database (Art. 49); (j) take corrective actions and provide information (Art. 20 — withdraw/disable/recall non-conforming systems, inform distributors, deployers, authorised representative, importers); (k) demonstrate conformity to a competent authority on reasoned request (Art. 21); (l) ensure accessibility requirements (Directives (EU) 2016/2102 and 2019/882). Non-EU providers must appoint an **authorised representative** (Art. 22); importers and distributors carry verification duties (Arts. 23–24).

## Art. 17 — Quality Management System

Documented systematically (written policies, procedures, instructions), proportionate to the provider's size, covering at minimum: (a) regulatory-compliance strategy incl. conformity assessment and modification management; (b) design, design control, design verification techniques and procedures; (c) development, quality control, quality assurance; (d) examination, test, validation procedures (before, during, after development, and their frequency); (e) technical specifications and standards applied (and means to meet Arts. 9–15 where harmonised standards not fully applied); (f) data management systems and procedures (acquisition through to any pre-market operation); (g) the Art. 9 risk management system; (h) post-market monitoring (Art. 72); (i) serious-incident reporting procedures (Art. 73); (j) communication handling with authorities, notified bodies, other operators, customers; (k) record-keeping systems and procedures; (l) resource management incl. security-of-supply; (m) an accountability framework for management and staff responsibilities. Financial institutions under Union financial-services law satisfy most of this via their existing internal-governance rules (Art. 17(4)).

---

## Art. 25 — Value Chain: When You Become the Provider

Any **distributor, importer, deployer, or other third party** is considered a provider of a high-risk AI system (assuming all Art. 16 obligations) where they:

- (a) put their **name or trademark** on a high-risk system already on the market (contractual allocation of obligations aside);
- (b) make a **substantial modification** to a high-risk system already placed/put into service such that it remains high-risk under Art. 6;
- (c) **modify the intended purpose** of an AI system (including GPAI) which was *not* high-risk, in such a way that it becomes high-risk.

The initial provider then ceases to be provider for that system but must cooperate: hand over technical documentation and reasonably expected access/information needed for the new provider's compliance (Art. 25(2)) — unless it clearly excluded the change to high-risk use. For Annex I products, the product manufacturer is the provider in the Art. 25(3) scenarios. Art. 25(4): providers of high-risk systems and third parties supplying tools/services/components must specify by **written agreement** the information, capabilities, technical access, and assistance needed for compliance (exception: third parties supplying under free and open-source licences, other than GPAI models). The AI Office may develop model contractual terms.

---

## Conformity Assessment, CE Marking, Registration (Arts. 43–49)

### Art. 43 — which procedure

| System | Procedure |
|---|---|
| Annex III **point 1** (biometrics) | Provider's choice: **internal control (Annex VI)** *if* harmonised standards / common specifications applied in full; otherwise **notified-body assessment of QMS + technical documentation (Annex VII)** is mandatory. Annex VII also mandatory where standards exist but were not (fully) applied, or the standard was published with restrictions. |
| Annex III **points 2–8** | **Internal control (Annex VI)** — self-assessment only, no notified body. |
| **Art. 6(1)** Annex I Section A products | Follow the **sectoral third-party conformity procedure** of the relevant Annex I act, with Arts. 9–15 checked within it (Annex VII points 4.3–4.5 applicable); one combined procedure and one notified body where possible. |

**Substantial modification** → new conformity assessment (Art. 43(4)); **not** a substantial modification: changes pre-determined by the provider and assessed at initial conformity assessment (continuous learning within declared bounds). Art. 44: notified-body certificates valid up to 5 years (Annex III) / 4 years (Annex I), extendable on re-assessment. Art. 46: market-surveillance authorities may authorise **derogation** from conformity assessment for exceptional reasons (public security, protection of life and health, environment, key assets) for a limited period.

### Arts. 47–49

- **Art. 47 — EU Declaration of Conformity:** one per system (Annex V content), machine-readable, signed; identifies the system, declares conformity with the AI Act (and GDPR where relevant); kept **10 years** after placing on market; may be combined with sectoral DoCs.
- **Art. 48 — CE marking:** affixed visibly, legibly, indelibly (or digitally for digital-only systems); followed by the notified body's identification number where Annex VII applied; general principles of Reg. (EC) 765/2008 apply.
- **Art. 49 — Registration (EU database, Art. 71):** the **provider** (or authorised representative) registers themselves and the system **before** placing on market/putting into service — Annex VIII Section A data (public, except Section C). Providers relying on **Art. 6(3)** register under Art. 49(2) with the Annex VIII **Section B** reduced data set, including the derogation reasoning. **Deployers that are public authorities/bodies** (or acting on their behalf) register their use under Art. 49(3)/Annex VIII Section C. Law-enforcement / migration / asylum / border systems (Annex III points 1, 6, 7): registration in a **secure non-public section**. Art. 60(4)(c): real-world-testing registration in a dedicated section.

---

## Art. 26 — Deployer Obligations

Deployers of high-risk AI systems shall:

1. Take appropriate **technical and organisational measures** to use the system in accordance with the **instructions for use** (26(1));
2. Assign **human oversight** to natural persons with the necessary **competence, training, authority, and support** (26(2));
3. Ensure **input data** under their control is relevant and sufficiently representative for the intended purpose (26(4));
4. **Monitor operation** per instructions; where use per instructions may create an Art. 79(1) risk, inform the provider/distributor and the market surveillance authority **without undue delay** and **suspend use**; on identifying a **serious incident**, immediately inform first the provider, then the importer/distributor and market surveillance authorities (26(5));
5. **Retain logs** under their control ≥ 6 months, unless other Union/national law (incl. GDPR) provides otherwise (26(6));
6. **Before putting into service at the workplace:** inform workers' representatives and affected workers (26(7));
7. Public-authority deployers: verify the system is registered in the EU database; if not, do not use it and inform the provider/distributor (26(8));
8. Use Art. 13 information to conduct any **DPIA** under GDPR Art. 35 / LED Art. 27 (26(9));
9. **Post-RBI** (law enforcement): request judicial/administrative authorisation within 48 h for each use (targeted search of a convicted/suspected person); cease and delete on refusal (26(10));
10. **Inform natural persons** subject to decisions made or assisted by an Annex III high-risk system (26(11)); cooperate with authorities (26(12)).

Note also **Art. 86**: affected persons' right to obtain from the deployer a clear and meaningful **explanation** of the role of the AI system in individual decision-making producing legal or similarly significant adverse effects.

## Art. 27 — Fundamental Rights Impact Assessment (FRIA)

**Who:** deployers that are **bodies governed by public law** or **private entities providing public services**, and — for Annex III **points 5(b) creditworthiness and 5(c) life/health insurance** — all deployers. **When:** before first use (may rely on previously conducted FRIAs; update when elements change). **Content (Art. 27(1)):**

- (a) description of the deployer's processes in which the system will be used, in line with intended purpose;
- (b) period and frequency of intended use;
- (c) categories of natural persons and groups likely to be affected;
- (d) specific risks of harm to those categories, using the provider's Art. 13 information;
- (e) description of human oversight measures per instructions for use;
- (f) measures to be taken where risks materialise — internal governance and complaint arrangements.

**Notify** the market surveillance authority of the outcome (Art. 27(3), completed AI Office template questionnaire; exemption from notification for Art. 46 derogation cases). Overlap with GDPR: a DPIA under GDPR Art. 35 / LED Art. 27 satisfies the FRIA in part — the FRIA complements it (Art. 27(4)).

---

## Quick reference — retention and timing

| Item | Duration / deadline | Article |
|---|---|---|
| Technical documentation, QMS docs, DoC, notified-body decisions | 10 years after placing on market | Art. 18 |
| Provider log retention | Appropriate to purpose, ≥ 6 months | Art. 19 |
| Deployer log retention | ≥ 6 months | Art. 26(6) |
| Serious incident report to market surveillance authority | Immediately, and ≤ 15 days from awareness (≤ 2 days for widespread infringement / death ≤ 10 days) | Art. 73 |
| Post-RBI judicial authorisation request | ≤ 48 h per use | Art. 26(10) |
| Annex III obligations apply | 2 Aug 2026 | Art. 113 |
| Annex I (Art. 6(1)) obligations apply | 2 Aug 2027 | Art. 113 |
