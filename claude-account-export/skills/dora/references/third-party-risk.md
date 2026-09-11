# ICT Third-Party Risk Management — Chapter V Deep Dive (Art. 28–44)

*Reconstructed reference — regenerated on 2026-09-11 to replace a file missing from the original skill upload; verify against the official texts (EUR-Lex) before relying on citations.*

Working reference for DORA Chapter V: Section I (Art. 28–30, obligations on
financial entities) and Section II (Art. 31–44, the Oversight Framework for
critical ICT third-party service providers). Key implementing texts:
**CDR (EU) 2024/1773** (policy on ICT services supporting critical/important
functions), **CIR (EU) 2024/2956** (Register of Information templates),
**CDR (EU) 2025/532** (subcontracting), **CDR (EU) 2024/1502** (CTPP designation
criteria), **CDR (EU) 2024/1505** (oversight fees), **CDR (EU) 2025/295** and
**CDR (EU) 2025/420** (oversight harmonisation / JETs).

**Governing principle (Art. 28(1)(a)):** financial entities remain **fully
responsible** for compliance with DORA at all times — outsourcing transfers
activity, never accountability. Chapter V applies **proportionately** (Art. 28(1)
second subpara., Art. 4).

---

## 1. Art. 28 — General Principles

### 1.1 Strategy and policy (Art. 28(2), CDR 2024/1773)

- Adopt, and review at least yearly, a **strategy on ICT third-party risk**,
  including a **policy on the use of ICT services supporting critical or
  important functions** (management-body approved; the management body reviews
  risks of these arrangements — Art. 5(2)(h)).
- CDR 2024/1773 requires the policy to cover the full arrangement life-cycle:
  planning, ex-ante risk assessment, due diligence, contracting (referencing
  Art. 30), monitoring (incl. audit/assurance approach), exit and termination;
  plus governance (roles, three lines, documentation, conflicts of interest).
- Entities using the Art. 16 simplified framework do not apply the full policy
  RTS but must still manage third-party risk within their simplified RMF.

### 1.2 Register of Information (Art. 28(3), CIR (EU) 2024/2956)

Maintain and keep updated a Register of Information (RoI) covering **all** ICT
service contractual arrangements (not only critical ones), at entity,
sub-consolidated and consolidated level, distinguishing arrangements that
support critical or important functions. Report the full RoI to the CA **at
least yearly**; report **at least annually the number of new arrangements,
service categories and functions**; make the RoI (or sections) available on
request; and **inform the CA in a timely manner of any planned arrangement
supporting critical or important functions and when a function becomes
critical/important**.

The CIR template is a relational set of tables. Core fields:

| Template area | Key fields |
|---------------|-----------|
| Entity maintaining the RoI | LEI, name, country, entity type, consolidation scope, group structure |
| Contractual arrangements | Arrangement reference number, type (standalone / master / subsequent), overarching arrangement links, start/end dates, notice periods (entity and provider side), governing law, annual expense/estimated cost, currency |
| ICT third-party providers | Provider identification (LEI or EUID; other code for non-EU), name, HQ country, type of person, ultimate parent, substitutability assessment (with reason: alternatives / migration difficulty), date of last audit |
| ICT services | Service type per the CIR taxonomy (e.g. ICT project management, development, cloud IaaS/PaaS/SaaS, data analysis, telecom, security services), storage of data (Y/N), data location (processing and storage countries), data sensitivity |
| Functions supported | Function identifier, licensed activity, function name, criticality assessment (Y/N + date of assessment + reasons), impact of discontinuation, RTO/RPO of the function |
| Supply chain | Rank (1 = direct provider, 2+ = subcontractors), linkage of each subcontractor to the service it underpins |
| Exit / termination | Exit plan existence, reintegration possibility, alternative providers identified |

**Practice notes:** the RoI is validated on submission (LEI checks, referential
integrity between tables); first collection cycle ran in 2025 and feeds CTPP
designation. Treat the RoI as regulatory data: assign a data owner, reconcile
against contracts and the Art. 8 asset/function inventory, and version each
submission. A vendor list or procurement export does not comply.

### 1.3 Pre-contracting assessment (Art. 28(4))

Before entering any ICT arrangement, the entity must:
- (a) assess whether the arrangement covers a **critical or important function**;
- (b) assess whether **supervisory conditions** for contracting are met;
- (c) identify and assess all relevant risks, **including ICT concentration risk** (→ Art. 29);
- (d) undertake **due diligence** on the prospective provider (suitability, information-security standards, financial soundness, reputation, expertise);
- (e) identify and assess **conflicts of interest**.

### 1.4 Security standards, audit, termination, exit (Art. 28(5)–(8))

- **28(5):** contract only with TPSPs complying with appropriate information
  security standards; for critical/important functions, weigh use of the most
  up-to-date and highest-quality standards/certifications.
- **28(6):** exercise access, inspection and **audit rights**; set audit
  frequency and areas risk-based; where high technical complexity makes audits
  impractical, evidence auditor skills or reliance arrangements (pooled audits,
  third-party certifications — with conditions in CDR 2024/1773).
- **28(7):** ensure contracts can be **terminated** at least where: (a) significant
  breach of laws/contract; (b) circumstances identified through monitoring that
  could alter the function's performance (incl. material changes affecting the
  arrangement or the provider's situation); (c) demonstrated weaknesses in the
  provider's overall ICT risk management (esp. availability, authenticity,
  integrity, confidentiality of data); (d) the CA can no longer effectively
  supervise the entity as a result of the arrangement.
- **28(8): exit strategies** for ICT services supporting critical or important
  functions: account for provider failure, service deterioration, business
  disruption and contract termination risks; ensure exit without disrupting
  business, limiting compliance, or harming service continuity; plans must be
  documented, sufficiently **tested**, reviewed periodically; identify
  alternative solutions and define **transition plans** (data/asset/workload
  migration and knowledge transfer).

---

## 2. Art. 29 — Preliminary Assessment of ICT Concentration Risk

When performing the Art. 28(4)(c) assessment, evaluate whether the envisaged
arrangement would lead to:

1. **Non-substitutability:** contracting a TPSP that is **not easily
   substitutable** (limited alternative providers; migration difficulty due to
   complexity, proprietary technology, or data-portability constraints); or
2. **Multiple arrangements:** having several arrangements for critical/important
   functions with the **same TPSP or closely connected TPSPs** (group-linked
   providers).

Also required:
- Weigh **benefits and costs of alternatives**, e.g. different providers,
  multi-vendor architectures, on-prem retention — a documented options analysis.
- Where the arrangement includes **subcontracting possibilities** for
  critical/important functions by providers in a **third country**, consider:
  insolvency law provisions and their enforceability, EU **data protection**
  compliance, effective enforcement in the third country, and — for **long or
  complex subcontracting chains** — the impact on the entity's ability to
  monitor and on the CA's ability to supervise (Art. 29(2)).

**Practice:** run the assessment **before signature** for every
critical/important-function arrangement and record it in the due diligence file;
aggregate concentration exposure across the group (single cloud provider
supporting multiple critical functions is the canonical finding). ICT
concentration risk is defined at Art. 3(29).

---

## 3. Art. 30 — Key Contractual Provisions

**Art. 30(1):** rights and obligations must be allocated in a **written**
contract, including SLAs, in one written document available on paper or in a
downloadable/accessible format.

### 3.1 Provisions for ALL ICT service contracts — Art. 30(2)(a)–(i)

| Ref | Provision |
|-----|-----------|
| (a) | Clear and complete **description of all functions and ICT services** to be provided, whether subcontracting of ICT services supporting a critical or important function (or material parts) is permitted and, if so, its conditions |
| (b) | **Locations** (regions/countries) where the functions and services are provided and where data is processed (incl. storage), and obligation to **notify in advance** any envisaged change of locations |
| (c) | Provisions on **availability, authenticity, integrity and confidentiality** of data, including personal data |
| (d) | Provisions on **access, recovery and return** of personal and non-personal data, in an easily accessible format, upon insolvency, resolution, discontinuation of operations, or termination |
| (e) | **Service level descriptions**, including updates and revisions |
| (f) | Obligation to provide **assistance at no additional cost** (or at ex-ante determined cost) when an ICT incident related to the service occurs |
| (g) | Obligation to **fully cooperate** with the entity's competent authorities and resolution authorities, including persons appointed by them |
| (h) | **Termination rights** and related minimum **notice periods**, in line with CA/resolution-authority expectations |
| (i) | Conditions for the provider's **participation in the entity's ICT security awareness programmes** and digital operational resilience training (Art. 13(6)) |

### 3.2 ADDITIONAL provisions where the service supports CRITICAL or IMPORTANT functions — Art. 30(3)(a)–(f)

| Ref | Provision |
|-----|-----------|
| (a) | **Full service level descriptions with precise quantitative and qualitative performance targets**, enabling monitoring and prompt corrective action when levels are not met |
| (b) | **Notice periods and reporting obligations** of the TPSP to the entity, including notification of any development with a **material impact** on its ability to deliver the service per agreed levels |
| (c) | Obligation to implement and test **business contingency plans**; ICT security measures/tools/policies giving an appropriate level of security aligned with the entity's regulatory framework |
| (d) | Obligation to **participate and fully cooperate in the entity's TLPT** (Art. 26–27) |
| (e) | **Unrestricted rights of access, inspection and audit** for the financial entity (or appointed third party) **and the competent authority**: right to take copies of relevant documentation on-site, effective exercise not impeded by other arrangements; agreed alternative assurance levels where other clients are affected; full cooperation during inspections by CA, Lead Overseer, entity or appointee; details on scope, modalities and frequency |
| (f) | **Exit strategies**: a mandatory **adequate transition period** during which the TPSP continues providing the services (to reduce disruption or ensure resolution/restructuring continuity) and allowing migration to another provider or in-house — with support obligations |

**Art. 30(4):** parties may consider **standard contractual clauses** developed
by public authorities. **Art. 30(5):** RTS mandate on subcontracting →
**CDR (EU) 2025/532**.

**Remediation practice:** run a clause-by-clause gap review of legacy contracts
against 30(2) and (where applicable) 30(3); prioritise critical/important
arrangements; typical fail points are audit/access rights with hyperscalers,
termination notice asymmetry, missing transition-period commitments, and
missing TLPT-participation clauses. Where a provider refuses required clauses,
the Art. 28(7) termination analysis and exit strategy must reflect that.

### 3.3 Subcontracting — CDR (EU) 2025/532 (Art. 30(5))

For ICT services supporting critical or important functions, the entity must:
- decide, risk-based and documented, **whether and under what conditions**
  subcontracting is permitted (fed by due diligence on the provider's
  subcontracting practices);
- ensure the contract requires the direct TPSP to: remain **responsible** for
  subcontracted services; flow down monitoring, security, location and
  audit-enabling obligations to subcontractors effectively underpinning the
  service; maintain **visibility of the chain** (feeding RoI supply-chain
  ranks);
- secure **advance notification of material changes** to subcontracting
  arrangements, with a defined window for the entity to **risk-assess and
  object**, and **termination rights** where the entity objects or the change
  creates unmanageable risk.

---

## 4. Section II — Oversight of Critical ICT Third-Party Providers (Art. 31–44)

### 4.1 Designation (Art. 31, CDR (EU) 2024/1502)

ESAs, through the Joint Committee and on recommendation of the Oversight Forum,
designate TPSPs as **critical** based on:

| Criterion (Art. 31(2)) | Substance (as quantified in CDR 2024/1502) |
|------------------------|--------------------------------------------|
| (a) Systemic impact | Impact on stability/continuity of financial services if the provider faced large-scale operational failure — share of client FEs by value of assets |
| (b) Systemic character of clients | Number/importance of G-SIIs and O-SIIs relying on the provider, and their interdependencies |
| (c) Reliance for critical/important functions | Degree of FE reliance on the provider for services underpinning critical or important functions (drawn from RoI data) |
| (d) Substitutability | Availability of alternatives in the market; difficulty of migrating data/workloads (technical complexity, cost, time) |

Also: **opt-in** on request for non-designated providers (Art. 31(11));
**exclusions** (Art. 31(8)) include FEs providing ICT to other FEs (as such),
intra-group providers, and providers operating solely in one Member State (per
the conditions there); providers are notified and may object before designation;
the ESAs publish and update the CTPP list. **Art. 31(12):** FEs may only use a
third-country TPSP that would qualify as critical if it **establishes an EU
subsidiary within 12 months** of designation — check this when contracting
non-EU providers at scale. Designation never dilutes the FE's own Chapter V
obligations.

### 4.2 Oversight architecture (Art. 32, 34, 40)

- **Lead Overseer:** EBA, ESMA or EIOPA — the ESA responsible for the largest
  share of client FE assets — leads oversight of each CTPP (Art. 31(1)(b)).
- **Oversight Forum:** Joint Committee sub-committee; cross-sector risk
  assessments, benchmarking, annual oversight priorities (Art. 32).
- **Joint Oversight Network (JON):** coordination between the three Lead
  Overseers — common methodology and consistent approaches (Art. 34).
- **Joint Examination Teams (JETs):** ESA + CA staff conducting the actual
  examinations per CTPP, composition/tasks per **CDR (EU) 2025/420** (Art. 40).

### 4.3 Lead Overseer powers (Art. 33, 35–39)

| Power | Article | Notes |
|-------|---------|-------|
| Assess CTPP ICT risk arrangements; annual oversight plan | 33 | Covers security, resilience, incident practices, subcontracting, governance |
| Request information and documentation | 35(1)(a), 37 | By simple request or binding decision |
| General investigations | 35(1)(b), 38 | Examine records, question staff |
| On-site and off-site inspections | 35(1)(b), 39 | Incl. third-country premises under Art. 36 conditions |
| Require post-oversight reports and remediation measures | 35(1)(c) | Templates per CDR (EU) 2025/295 |
| Issue **recommendations** | 35(1)(d) | On ICT security/resilience, terms of service to FEs, subcontracting — incl. recommending **refraining from subcontracting** where risks unmanaged |
| **Periodic penalty payments** | 35(6)–(8) | Up to **1% of average daily worldwide turnover** in the preceding business year, per day, up to 6 months, for non-cooperation with information requests/investigations/inspections; public disclosure |

### 4.4 Follow-up, fees, cooperation (Art. 42–44)

- **Comply-or-explain (Art. 42):** within 60 days the CTPP notifies intent to
  follow recommendations or gives a reasoned explanation; the Lead Overseer may
  publicly disclose non-compliance. CAs inform FEs of the risks of
  non-compliance; and — **as a last resort** — may require FEs to **suspend or
  terminate** the use of the non-compliant CTPP's services (Art. 42(6)),
  considering timing and a plan for orderly migration. FEs should build this
  scenario into exit strategies.
- **Fees (Art. 43, CDR 2024/1505):** CTPPs pay oversight fees based on
  applicable turnover, fully covering Lead Overseer costs.
- **International cooperation (Art. 44):** ESA administrative arrangements with
  third-country authorities; 5-yearly confidential report on third-country risk
  developments.

**Important framing for advice:** oversight is **not supervision** of the CTPP's
whole business and creates no compliance safe harbour for FEs — recommendations
address the ICT risk posed to FEs. The FE's Art. 28–30 obligations toward a
designated CTPP remain unchanged, and RoI accuracy is what drives designation
data.

---

## 5. Programme Checklist (Chapter V readiness)

| # | Deliverable | Anchor |
|---|-------------|--------|
| 1 | Board-approved ICT third-party risk strategy + policy for critical/important-function services, reviewed yearly | Art. 28(2); CDR 2024/1773 |
| 2 | Register of Information complete at all consolidation levels, validated, submitted annually; CA pre-notification workflow for new critical/important arrangements | Art. 28(3); CIR 2024/2956 |
| 3 | Pre-contract assessment pack: criticality, due diligence, conflicts, concentration analysis with options/cost-benefit | Art. 28(4), 29 |
| 4 | Contract clause library covering 30(2)(a)–(i) + 30(3)(a)–(f); legacy remediation plan with priority tiers | Art. 30 |
| 5 | Subcontracting conditions, chain visibility, notification/objection mechanism in templates | Art. 30(5); CDR 2025/532 |
| 6 | Audit/assurance plan per key TPSP (own, pooled, or certification-based with justification) | Art. 28(6) |
| 7 | Exit strategy + tested transition plan per critical/important arrangement, incl. Art. 42(6) forced-exit scenario | Art. 28(8); 30(3)(f) |
| 8 | Concentration risk dashboard aggregated at group level | Art. 29; Art. 3(29) |
| 9 | Watch list: which of our TPSPs are designated CTPPs; track Lead Overseer recommendations affecting them | Art. 31–42 |
