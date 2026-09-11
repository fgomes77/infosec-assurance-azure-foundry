# GPAI Models, Governance, Penalties and Timeline — EU AI Act (Regulation (EU) 2024/1689)

*Reconstructed reference — regenerated on 2026-09-11 to replace a file missing from the original skill upload; verify against the official texts (EUR-Lex) before relying on citations.*

Covers Chapter V (general-purpose AI models, Arts. 51–56), the governance architecture (Chapter VII), penalties (Arts. 99–101), the phase-in timeline (Art. 113), and cross-framework mapping. GPAI obligations apply from **2 August 2025**; models placed on the market before that date have until **2 August 2027** to comply (Art. 111(3)).

---

## Key Definitions (Art. 3)

| Term | Definition (abridged) |
|---|---|
| **GPAI model** — Art. 3(63) | An AI model, including where trained with a large amount of data using self-supervision at scale, that displays **significant generality** and is capable of competently performing a **wide range of distinct tasks**, and that can be integrated into a variety of downstream systems or applications. Excludes models used for research, development, or prototyping before market placement. |
| **GPAI system** — Art. 3(66) | An AI system based on a GPAI model, capable of serving a variety of purposes, directly or integrated into other systems. (A GPAI *system* used in an Annex III context can itself be high-risk; model obligations and system obligations stack on different actors.) |
| **Systemic risk** — Art. 3(65) | Risk specific to high-impact capabilities of GPAI models, having a significant impact on the Union market due to reach or actual/reasonably foreseeable negative effects on public health, safety, public security, fundamental rights, or society as a whole, propagable at scale across the value chain. |
| **High-impact capabilities** — Art. 3(64) | Capabilities matching or exceeding those recorded in the most advanced GPAI models. |
| **Downstream provider** — Art. 3(68) | A provider of an AI system, including a GPAI system, which integrates an AI model, whether self-supplied or supplied by another entity. |

---

## Art. 51 — Classification as GPAI Model with Systemic Risk

A GPAI model is classified as posing **systemic risk** where:

- **(a)** it has high-impact capabilities, evaluated on the basis of appropriate technical tools and methodologies, including indicators and benchmarks; **or**
- **(b)** the Commission so decides, *ex officio* or following a **qualified alert from the scientific panel** (Art. 90), based on the **Annex XIII criteria** (parameters, dataset size/quality, training compute, input/output modalities, benchmarks and capability evaluations, reach — presumed significant at ≥10,000 registered EU business users — and number of registered end-users).

**The 10²⁵ FLOP presumption (Art. 51(2)):** a model is **presumed** to have high-impact capabilities when the cumulative amount of computation used for its training, measured in floating-point operations, is **greater than 10²⁵ FLOPs**. The presumption is rebuttable: the provider may present arguments that, despite meeting the threshold, the model does not present systemic risk (Art. 52(2)); the Commission may accept, reject (Art. 52(3)), and may update thresholds via delegated acts (Art. 51(3)).

**Procedure (Art. 52):** the provider must **notify the Commission without delay and in any event within 2 weeks** of the threshold being met or it becoming known it will be met (including projections before training completes). The Commission maintains and publishes a **list of GPAI models with systemic risk** (Art. 52(6), respecting IP and confidentiality). Reassessment can be requested no earlier than 6 months after designation.

---

## Art. 53 — Obligations for ALL Providers of GPAI Models

1. **(a) Technical documentation** of the model — drawn up and kept up to date, containing at minimum the **Annex XI** elements (training and testing process, evaluation results; general description: tasks, architecture and parameters, modalities, licence, acceptable-use policies, distribution methods, training methodologies, data used — type, provenance, curation — compute and known/estimated energy consumption). Provided to the AI Office and national competent authorities **on request**.
2. **(b) Information and documentation to downstream providers** who intend to integrate the model — the **Annex XII** elements enabling downstream providers to understand capabilities and limitations and comply with their own obligations (technical means for integration, modalities, acceptable use, architecture, input/output specifications). Kept up to date; IP and trade secrets respected.
3. **(c) Copyright policy** — put in place a policy to comply with Union copyright law, in particular to identify and comply with **reservations of rights (opt-outs) under Art. 4(3) of Directive (EU) 2019/790** (CDSM/TDM exception), including through state-of-the-art technologies.
4. **(d) Public summary of training content** — draw up and make publicly available a **sufficiently detailed summary** of the content used for training, according to the **AI Office template** (published July 2025).

**Open-source exception (Art. 53(2)):** obligations (a) and (b) do **not** apply to models released under a free and open-source licence allowing access, use, modification, and distribution, whose **parameters, including weights, architecture information, and usage information, are made publicly available** — **unless** the model is a GPAI model with systemic risk. Obligations (c) and (d) always apply.

**Compliance pathways (Art. 53(4)):** providers may rely on a **code of practice** (Art. 56) to demonstrate compliance until a harmonised standard is published; those not adhering must demonstrate **alternative adequate means** for Commission assessment. **Art. 54:** non-EU model providers must appoint an authorised representative in the Union before placing on the market (open-source exemption mirrors Art. 53(2), absent systemic risk).

---

## Art. 55 — Additional Obligations: GPAI Models with Systemic Risk

In addition to Arts. 53–54, providers of systemic-risk models shall:

- **(a) Model evaluation** — perform evaluations in accordance with standardised protocols and tools reflecting the state of the art, including conducting and documenting **adversarial testing (red-teaming)** to identify and mitigate systemic risks;
- **(b) Risk assessment and mitigation** — assess and mitigate possible **systemic risks at Union level**, including their sources, that may stem from development, placing on the market, or use;
- **(c) Serious incident reporting** — keep track of, document, and report **without undue delay to the AI Office** (and, as appropriate, national competent authorities) relevant information about **serious incidents** and possible corrective measures;
- **(d) Cybersecurity** — ensure an adequate level of cybersecurity protection for the model **and its physical infrastructure** (protection of model weights, insider-threat controls, secured compute).

Same pathway logic (Art. 55(2)): codes of practice / harmonised standards / alternative adequate means.

## Art. 56 — GPAI Code of Practice

The AI Office facilitated the drawing-up of the **General-Purpose AI Code of Practice** (published 10 July 2025; Commission adequacy confirmation Aug 2025), with three chapters: **Transparency** (a Model Documentation Form operationalising Annex XI/XII), **Copyright** (Art. 53(1)(c) policy measures), and **Safety and Security** (systemic-risk models only — operationalising Art. 55: risk taxonomy, evaluation and red-teaming commitments, safety and security frameworks, incident reporting). Adherence is **voluntary** and provides a presumption-style compliance route with reduced administrative burden and greater trust; signatories are published by the AI Office. Non-signatories must demonstrate alternative adequate means. Training-data summaries follow the separate **AI Office template** (an implementing measure, not part of the Code).

---

## Governance Architecture (Chapter VII)

| Body | Basis | Composition | Role |
|---|---|---|---|
| **AI Office** | Art. 64; Commission Decision C(2024) 390 | Within the Commission (DG CNECT) | Develops Union expertise; **exclusive supervision and enforcement of GPAI model obligations** (Art. 88, with Art. 75 powers: documentation requests, evaluations, mitigation measures, recall); facilitates codes of practice (Arts. 50(7), 56); training-summary template; coordinates with market surveillance authorities. |
| **European Artificial Intelligence Board (AI Board)** | Arts. 65–66 | One representative per Member State; EDPS observer; AI Office attends | Advises and assists the Commission and Member States on consistent, effective application: coordination of national authorities, opinions on codes of practice/conduct, guidance, standing sub-groups (incl. market surveillance and notified-body sub-groups). |
| **Advisory Forum** | Art. 67 | Balanced stakeholders: industry (incl. SMEs), start-ups, civil society, academia; permanent members incl. ENISA, FRA, CEN/CENELEC/ETSI | Technical expertise and stakeholder input to the Board and Commission. |
| **Scientific Panel of Independent Experts** | Art. 68 | Independent experts selected by the Commission | Supports GPAI enforcement: advises on systemic-risk classification, tools/methodologies and benchmarks, and may issue **qualified alerts** (Art. 90) to the AI Office where a model presents concrete identifiable Union-level risk or meets Art. 51 conditions. |
| **National competent authorities** | Art. 70 | ≥1 notifying authority + ≥1 market surveillance authority per Member State (designated by 2 Aug 2025) | Market surveillance of AI *systems* under Reg. (EU) 2019/1020; single points of contact; Art. 74(8): for Annex III points 1, 6–8 in law-enforcement contexts, data protection authorities (or equivalent) act as market surveillance authorities. |

Supporting mechanisms: **Art. 57** — each Member State ensures at least one **AI regulatory sandbox** (operational by 2 Aug 2026); **Arts. 60–61** — real-world testing of high-risk systems outside sandboxes with informed consent; **Art. 62** — SME measures (priority sandbox access, reduced fees); **Art. 72** — post-market monitoring plans; **Art. 73** — serious-incident reporting (≤15 days; ≤2 days widespread infringement/critical-infrastructure incidents; ≤10 days death); **Art. 85** — right of any person to lodge a complaint with a market surveillance authority.

---

## Penalties (Arts. 99–101)

| Infringement | Maximum administrative fine | Basis |
|---|---|---|
| Prohibited practices (Art. 5) | **€35,000,000 or 7%** of total worldwide annual turnover, whichever is **higher** | Art. 99(3) |
| Non-compliance with operator or notified-body obligations (Arts. 16, 22–27, 28–31, 33(1)/(3)/(4), 34, 50) | **€15,000,000 or 3%**, whichever is higher | Art. 99(4) |
| Supplying incorrect, incomplete, or misleading information to notified bodies or national competent authorities | **€7,500,000 or 1%**, whichever is higher | Art. 99(5) |
| **SMEs and start-ups** | Same tiers, but whichever is **lower** of the fixed amount and percentage | Art. 99(6) |
| **GPAI model providers** (intentional/negligent infringement of Chapter V, or failure to comply with Art. 75 measures / document requests) | **€15,000,000 or 3%**, whichever is higher — imposed by the **Commission** | Art. 101 |
| Union institutions, bodies, agencies | Up to €1,500,000 (prohibited practices) / €750,000 (other) — EDPS | Art. 100 |

Art. 99(7) proportionality factors: nature/gravity/duration, intentional or negligent character, prior fines by other authorities, size and market share, mitigating actions, cooperation. Member States lay down rules on penalties (incl. non-fine measures) and notify the Commission by 2 Aug 2025. GPAI fines: Court of Justice has unlimited jurisdiction to review (Art. 101(4)).

---

## Phase-In Timeline (Art. 113)

| Date | What applies |
|---|---|
| 1 Aug 2024 | Entry into force (20 days after OJ publication, 12 Jul 2024) |
| **2 Feb 2025** | Chapters I–II: general provisions, **Art. 4 AI literacy**, **Art. 5 prohibited practices** |
| **2 Aug 2025** | **Chapter V GPAI model obligations (Arts. 51–55)**; Chapter VII governance (AI Office operational, Board, scientific panel); notified-body chapter (Arts. 28–39); **Art. 99 penalties** (except Art. 101 timing nuances); Member State authority designation; confidentiality (Art. 78) |
| **2 Aug 2026** | **General application**: high-risk Annex III systems (Arts. 8–27, 43–49), Art. 50 transparency, sandboxes, post-market monitoring, EU database fully live |
| **2 Aug 2027** | **Art. 6(1)** Annex I product-safety high-risk systems; deadline for **pre-Aug-2025 GPAI models** to comply (Art. 111(3)) |
| 31 Dec 2030 | Legacy large-scale IT systems (Annex X) placed on market before 2 Aug 2027 |

Grandfathering (Art. 111(2)): high-risk systems placed on the market before 2 Aug 2026 fall in scope only upon **significant change in design**; public-authority-operated high-risk systems must comply by 2 Aug 2030 regardless.

---

## Cross-Framework Mapping

| AI Act requirement | ISO/IEC 42001:2023 | NIST AI RMF 1.0 | GDPR |
|---|---|---|---|
| Art. 9 risk management | Cl. 6.1, 8.2; Annex A.5 (impact assessment), A.6 | GOVERN 1, MAP 1–5, MANAGE 1–4 | Art. 35 DPIA (partial overlap) |
| Art. 10 data governance | A.7.2–7.6 (data for AI systems) | MAP 2.3, MEASURE 2.2 | Arts. 5, 6, 9 (lawfulness, minimisation, special categories) |
| Art. 11 technical documentation | A.6.2.7 (documentation), Cl. 7.5 | GOVERN 1.4 | Art. 30 records (analogue) |
| Art. 12 logging | A.6.2.8 (event logs) | MEASURE 2.x | Art. 5(2) accountability |
| Art. 13 transparency | A.8.2–8.5 (information for users) | GOVERN 4.1, MAP 3.4 | Arts. 13–15 |
| Art. 14 human oversight | A.9.2 (human oversight processes) | GOVERN 3.2, MANAGE 2.x | Art. 22 automated decisions |
| Art. 15 accuracy/robustness/security | A.6.2.4, A.6.2.6; ISO/IEC 27001 for security | MEASURE 2.5–2.9 | Arts. 5(1)(d), 32 |
| Art. 17 QMS | The AIMS itself (Cl. 4–10) | GOVERN (all) | — |
| Art. 27 FRIA | A.5.4/A.5.5 impact assessment | MAP 5.1–5.2 | Art. 35 DPIA |
| Art. 55 systemic-risk evaluation | A.6.2.4 verification & validation | MEASURE 1–2, MANAGE 4 | — |

**Positioning:** ISO/IEC 42001 certification is strong organisational evidence but is **not** a presumption of conformity — only harmonised standards cited in the OJEU (CEN-CENELEC JTC 21 work programme) confer the Art. 40 presumption. GDPR applies in parallel whenever personal data is processed; the AI Act is without prejudice to it (Art. 2(7)).
