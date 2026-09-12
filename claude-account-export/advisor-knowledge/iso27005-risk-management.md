# ISO/IEC 27005:2022 — Information Security Risk Management

*Advisor knowledge reference — authored 2026-09-11 to ground the persona domain in the combined knowledge base; verify against the official publication before citing in formal deliverables.*

## Purpose and positioning

ISO/IEC 27005:2022 (4th edition) is the guidance standard for managing information
security risk. It is not certifiable and imposes no mandatory method; instead it
elaborates *how* to satisfy the risk requirements that ISO/IEC 27001:2022 states
in clauses 6.1.2, 6.1.3, 8.2 and 8.3. Where 27001 says "the organization shall
define and apply a risk assessment process", 27005 supplies the working detail:
what a risk criterion looks like, how to identify and analyse risks, and how to
run treatment and acceptance as a repeatable cycle.

### Relationship to ISO/IEC 27001:2022 clause 6

| 27001 requirement | What 27005:2022 adds |
|---|---|
| 6.1.2(a) — establish and maintain risk criteria (acceptance + assessment) | Detailed guidance on designing consequence, likelihood and acceptance criteria, including scales and their calibration |
| 6.1.2(c) — identify risks to confidentiality, integrity, availability | Two recognised identification routes: the event-based (scenario) approach and the asset-based approach |
| 6.1.2(d) — analyse risks (consequence, likelihood, level) | Qualitative, semi-quantitative and quantitative analysis techniques and their trade-offs |
| 6.1.2(e) — evaluate risks against criteria and prioritise | Evaluation as a comparison against acceptance criteria, producing a prioritised list for treatment |
| 6.1.3 — risk treatment, SoA, treatment plan, owner approval | The four treatment option families, control selection logic, and residual-risk acceptance |
| 8.2 / 8.3 — perform assessments and implement treatment at planned intervals | Monitoring, review and re-assessment triggers |
| 9 / 10 — evaluation and improvement | Feeding risk monitoring results into management review and improvement |

### Relationship to ISO 31000

27005 is the information-security specialisation of ISO 31000:2018. It reuses
31000's architecture — principles, framework, and the process of scope/context,
assessment (identification, analysis, evaluation), treatment, recording,
monitoring, and communication — and adds security-specific content: threats,
vulnerabilities, CIA consequences, and the coupling to an ISMS. An organisation
with an enterprise risk function built on 31000 can slot 27005 in as the
security domain method without inventing a parallel vocabulary.

## The risk management process

### 1. Context establishment

- Define scope and boundaries consistent with the ISMS scope (27001 clause 4.3).
- Understand internal and external issues, interested parties and their
  requirements — these shape what "consequence" means for the organisation.
- Design the **risk criteria** before assessing anything (see below).
- Assign roles: risk owners (accountable for the risk and treatment approval),
  assessors, and the acceptance authority.

### 2. Risk identification

27005:2022 gives two complementary approaches:

- **Event-based (scenario) approach** — start from strategic risk scenarios:
  risk sources (threat actors, environmental hazards, insiders), their desired
  end states, and the events that would produce a consequence. Faster to run,
  well suited to top-management engagement and to a first assessment cycle.
- **Asset-based approach** — start from an inventory of primary assets
  (information, business processes) and supporting assets (hardware, software,
  networks, people, sites, suppliers), then pair threats with the
  vulnerabilities they could exploit. More granular and operational; produces
  results that map cleanly onto control selection.

Good practice is to combine them: event-based scenarios to frame what matters,
asset-based decomposition where the scenario touches critical services. In both
routes the identification output records: risk source/threat, event,
vulnerability or contributing condition, affected asset or process, consequence
type (C/I/A plus legal, financial, reputational, safety), and existing controls.

### 3. Risk analysis

Determine, for each identified risk:

- **Consequence** — magnitude of impact if the event occurs, judged against the
  consequence criteria (per impact category, at the level of the business, not
  the IT component).
- **Likelihood** — plausibility of the event occurring and succeeding, taking
  existing controls into account. 27005:2022 encourages thinking in terms of
  threat capability, motivation, opportunity, and control strength rather than
  bare historical frequency.
- **Level of risk** — the combination of the two, via matrix, formula, or
  quantitative model.

### 4. Risk evaluation

Compare analysed risk levels against the **risk acceptance criteria** and rank
them. Outcomes per risk: treat, accept as-is, investigate further, or reject
the underlying activity. Evaluation is where criteria design pays off — a badly
calibrated matrix makes everything "medium" and the ranking useless.

### 5. Risk treatment

Four option families (they can be combined):

| Option | Meaning | Typical TPRM expression |
|---|---|---|
| Modify (reduce) | Apply or improve controls to change likelihood or consequence | Contractual security clauses, supplier remediation plan, added monitoring |
| Retain (accept) | Informed decision to accept the risk against criteria | Documented acceptance by risk owner for a low-residual supplier finding |
| Avoid | Withdraw from or not start the risk-bearing activity | Do not onboard the supplier; decommission the integration |
| Share | Transfer part of the risk to another party | Insurance, indemnities, shifting processing to the supplier under contract — note: accountability is never transferred |

Treatment produces the **risk treatment plan** (controls, owners, deadlines,
expected residual risk) and drives the **Statement of Applicability**: chosen
controls are compared against Annex A to confirm nothing necessary was
overlooked. Residual risk must be formally accepted by the risk owner.

### 6. Risk acceptance

A distinct, recorded decision — not the absence of a decision. Acceptances
outside the standing criteria (exceptions) need explicit justification and a
defined review date.

### 7. Communication and consultation

Continuous, not a phase: risk owners, top management, and affected functions
(legal, procurement, DPO for supplier risks) are consulted during assessment
and informed of results and acceptances.

### 8. Monitoring and review

- Monitor risk factors: new threats, new vulnerabilities, asset and supplier
  changes, control performance, incidents and near misses.
- Review the assessment at planned intervals and on significant change
  (27001 8.2); review criteria themselves periodically.
- Feed results into management review (27001 clause 9.3).

## Designing risk criteria

- **Consequence criteria**: define 4–5 levels per impact category (financial,
  operational/service, legal-regulatory, reputational, safety/privacy) with
  concrete anchors ("regulatory fine likely", "> 4h outage of a critical
  service"). Anchor the top level to what genuinely threatens objectives.
- **Likelihood criteria**: define levels with time-bounded descriptions
  ("plausible within 12 months given current controls"), not vague adjectives.
- **Acceptance criteria**: state which risk levels may be accepted, by whom
  (delegation ladder), and under what conditions; allow for cost-benefit,
  regulatory floors (some risks may never be accepted, e.g. legal breaches),
  and temporary acceptance pending treatment.
- Keep scales consistent across the organisation so supplier risks, project
  risks and operational risks are comparable in one register.

## Qualitative vs quantitative analysis

| Aspect | Qualitative | Quantitative |
|---|---|---|
| Scales | Ordinal levels (Low–Critical) | Monetary/probabilistic values (e.g. loss exceedance, ALE) |
| Effort/data | Low; expert judgement | High; needs loss data, frequencies, modelling (e.g. FAIR-style) |
| Strengths | Fast, communicable, workable with sparse data | Comparable to other business risks, supports cost-benefit of controls |
| Weaknesses | Ordinal arithmetic abuse, matrix compression, rater bias | False precision if inputs are guesses; expensive to maintain |
| Typical use | ISMS-wide register, supplier triage | High-stakes decisions: cyber insurance limits, major investment cases |

Semi-quantitative (scored) methods sit between the two and dominate practice;
be explicit that scores are ordinal and avoid multiplying them as if cardinal.

## Worked TPRM example — supplier risk scenario

**Context**: SaaS supplier "Acme Analytics" will process customer transaction
data for a regulated financial-services entity. Event-based identification,
semi-quantitative 5×5 analysis.

- **Scenario**: external attacker compromises Acme's multi-tenant platform via
  an unpatched internet-facing service; customer transaction data exfiltrated.
- **Risk source / threat**: financially motivated intruder; **vulnerability**:
  Acme's assessment shows patching SLA of 90 days for high-severity CVEs and
  no independent penetration test in 24 months; **asset**: customer PII and
  transaction records (primary), Acme platform (supporting).
- **Consequence**: level 4/5 — personal-data breach with regulatory
  notification, probable supervisory attention, customer churn.
- **Likelihood**: level 3/5 — internet-exposed multi-tenant platform, weak
  patch cadence, but MFA and network segmentation evidenced.
- **Risk level**: 4×3 = High → exceeds acceptance criteria (accept only ≤ Medium
  for personal-data scenarios).
- **Treatment (modify + share)**: contractual remediation — 30-day patch SLA
  for critical/high CVEs, annual independent pentest with summary shared,
  breach notification within 24h; GDPR Art. 28 terms and audit rights;
  continuous external attack-surface monitoring by the TPRM team.
- **Residual risk**: Medium (likelihood 2, consequence 4) — accepted by the
  business risk owner, review at next annual reassessment or on any Acme
  security incident.
- **Records**: risk register entry, treatment plan actions in the supplier
  file, acceptance sign-off, SoA unchanged (controls already applicable).

## Mapping: 27005 process steps → typical ISMS artefacts

| 27005 process step | Primary artefact(s) | Related 27001 reference |
|---|---|---|
| Context establishment | Risk management method/policy; risk criteria definition; ISMS scope statement | 4.3, 6.1.2(a) |
| Risk identification | Risk register (new entries); asset inventory; threat catalogue; supplier register | 6.1.2(c), A.5.9 |
| Risk analysis | Risk register (consequence, likelihood, level fields); analysis worksheets | 6.1.2(d) |
| Risk evaluation | Prioritised risk list; evaluation record vs criteria | 6.1.2(e) |
| Risk treatment | Risk treatment plan; **Statement of Applicability**; control implementation evidence | 6.1.3, 6.2 |
| Risk acceptance | Residual-risk acceptance records; exception register | 6.1.3(f) |
| Communication & consultation | Management review inputs; risk reporting packs; stakeholder communications | 7.4, 9.3 |
| Monitoring & review | Reassessment schedule and records; KRI dashboards; incident-to-risk feedback log | 8.2, 9.1, 10.2 |

## Practitioner cautions

- Do not let the tool (register spreadsheet, GRC platform) dictate the method;
  the method must satisfy 27001's requirement for consistent, valid,
  comparable results (6.1.2(b)).
- Revisit "existing controls" honestly — assuming controls operate as designed
  without evidence quietly understates risk.
- In TPRM, the supplier's assessment answers are claims, not evidence; adjust
  likelihood confidence to the strength of evidence obtained (certifications,
  test reports, contractual commitments, independent telemetry).
