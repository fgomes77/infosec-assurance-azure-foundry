# GDPR Article 28 Processor Contracts and the 2021 SCCs

*Advisor knowledge reference — authored 2026-09-11 to ground the persona domain in the combined knowledge base; verify against the official publication before citing in formal deliverables.*

## Scope of this reference

Two related but distinct instruments the TPRM team meets in supplier reviews:

1. **GDPR Article 28** — the mandatory content of any contract under which a
   processor handles personal data on a controller's behalf (the "DPA").
2. **Standard Contractual Clauses (SCCs)** under **Commission Implementing
   Decision (EU) 2021/914** — the Commission's Art. 46(2)(c) transfer tool for
   exports of personal data to third countries lacking adequacy. (A separate
   2021/915 decision provides optional intra-EEA Art. 28 clauses; do not
   confuse the two.)

They intersect: SCC Modules Two and Three embed Art. 28-compliant terms, so a
transfer under those modules does not need a second DPA layered on top.

## Article 28 essentials

- A controller may use **only** processors providing "sufficient guarantees" of
  appropriate technical and organisational measures (Art. 28(1)) — the legal
  root of pre-contract due diligence in TPRM.
- Processing must be governed by a **binding written contract** (or other legal
  act) setting out subject matter, duration, nature and purpose of processing,
  data types, categories of data subjects, and the parties' obligations and
  rights (Art. 28(3) chapeau).
- Processing outside the controller's documented instructions makes the
  processor a controller for that processing (Art. 28(10)) — a useful lever in
  negotiations over supplier "product improvement" data use.

### The eight mandatory clauses — Art. 28(3)(a)–(h)

| Ref | Obligation | What to check in a supplier contract |
|---|---|---|
| (a) | Process only on the controller's **documented instructions**, including for international transfers, unless EU/Member State law requires otherwise (with prior notice of that law where permitted) | Instructions mechanism defined; carve-outs limited to legal compulsion; no open-ended "legitimate business purposes" processing rights for the supplier |
| (b) | Persons authorised to process are bound by **confidentiality** (contractual or statutory) | Staff/contractor confidentiality undertakings; extension to sub-processor personnel |
| (c) | Take all measures required by **Art. 32 (security of processing)** | Security annex with concrete TOMs (encryption, access control, resilience, testing), not a bare recital; alignment with the assurance assessment findings |
| (d) | Respect the **sub-processor conditions of Art. 28(2) and (4)** | Prior specific or general written authorisation; notification and objection mechanics for changes; same obligations flowed down; processor remains fully liable to the controller for sub-processor failures |
| (e) | **Assist** the controller, by appropriate technical and organisational measures insofar as possible, in responding to **data-subject rights** requests (Ch. III) | Defined assistance process and turnaround; no unreasonable fees that would deter compliance |
| (f) | **Assist** the controller with Arts. 32–36 obligations: security, **breach notification**, DPIAs and prior consultation, taking account of the nature of processing and information available | Breach notification to the controller "without undue delay" — negotiate a concrete window (24–48h is common practice; 72h is the controller's own regulator deadline, so the processor must be faster); DPIA support commitment |
| (g) | At the end of services, **delete or return** all personal data at the controller's choice, and delete existing copies unless EU/Member State law requires storage | Exit/offboarding clause with deletion certification, defined timescale, and backup-cycle carve-out that is bounded and justified |
| (h) | Make available all information necessary to **demonstrate compliance** and allow and contribute to **audits and inspections** by the controller or its mandated auditor; inform the controller if an instruction infringes data protection law | Audit rights not reduced to "SOC 2 report only"; mandated-auditor option preserved; the "illegal instruction" red-flag duty present |

## Controller–processor chains and flow-down

- **Roles first**: qualify the supplier factually (who determines purposes and
  means?) before drafting — mislabelled "processors" that decide purposes are
  joint or independent controllers (Art. 26 territory) and Art. 28 terms will
  not cure that.
- **Sub-processor chain**: Art. 28(4) requires the *same* data-protection
  obligations to be imposed down the chain by contract; the prime processor
  carries full liability upward. In review: obtain the current sub-processor
  list, verify the notification/objection mechanism actually operates (mailing
  list, portal), and check whether any sub-processor is itself outside the EEA
  (triggering Chapter V analysis at that hop).
- **Fourth parties**: for critical suppliers, ask how the prime verifies its
  sub-processors (their Art. 28(1) "sufficient guarantees" duty), not merely
  that a contract exists.

## The 2021/914 SCCs

A single modular instrument replacing the pre-GDPR 2001/2004/2010 sets
(old-SCC contracts had to migrate by 27 December 2022 — any surviving legacy
set found in review is a finding).

### The four modules

| Module | Relationship | When it applies |
|---|---|---|
| One (C2C) | Controller → Controller | Exporter shares data with a non-EEA party that determines its own purposes (e.g. group HR data to a US parent acting as controller) |
| Two (C2P) | Controller → Processor | Classic SaaS/outsourcing: EEA controller engages a non-EEA processor; embeds Art. 28 content — no separate DPA needed for that transfer |
| Three (P2P) | Processor → (Sub-)Processor | EEA processor exports to a non-EEA sub-processor; instructions flow from the controller via the exporting processor |
| Four (P2C) | Processor → Controller | EEA processor sends data back to its non-EEA controller-client (lightest module; largely disapplied where the controller merely gets its own data back) |

Structural features to verify:

- **Docking clause (Clause 7, optional)**: allows new entities to accede to an
  executed SCC by completing the Annexes — check whether it was adopted; it is
  the clean mechanism for group entities and newly added sub-processors.
- **Hierarchy (Clause 5)**: SCCs prevail over conflicting commercial terms —
  a supplier MSA cannot dilute them.
- **No modification** of the clauses themselves (Clause 2), though they may sit
  inside a broader contract and parties may add non-contradictory terms.
- **Third-party beneficiary rights** for data subjects (Clause 3); governing
  law and forum must be a Member State that recognises them (Clauses 17–18).
- SCCs are only needed where the importer's processing is **not itself subject
  to GDPR** for that processing; for importers already caught by Art. 3(2),
  the 2021 set is not designed to apply (a known gap the Commission has
  acknowledged — record the analysis rather than papering it with SCCs).
- **UK/Swiss variants**: UK transfers need the IDTA or the UK Addendum to the
  EU SCCs; Swiss transfers need FDPIC-recognised adaptations. Check the right
  instrument is attached for the actual exporting jurisdictions.

### Annexes and their relationship to Art. 28

| SCC Annex | Content | Art. 28 linkage |
|---|---|---|
| Annex I | A: parties; B: description of transfer (data subjects, data categories, special categories, frequency, nature/purpose, retention); C: competent supervisory authority | Mirrors the Art. 28(3) chapeau particulars — subject matter, duration, nature, purpose, data types, data-subject categories |
| Annex II | Technical and organisational measures, described **specifically** (not generic) | Operationalises Art. 28(3)(c)/Art. 32; the assurance team should compare Annex II against assessment evidence — vague Annex II entries are a review finding |
| Annex III | List of authorised sub-processors (Modules Two/Three, where specific authorisation chosen) | Implements Art. 28(2)/(d) sub-processor authorisation |

Module Two/Three clauses reproduce the Art. 28(3)(a)–(h) obligations
(instructions, confidentiality, security, sub-processing, assistance, breach
notification, deletion/return, audit), so a correctly executed Module Two SCC
*is* the DPA for the transferred processing.

## Schrems II and transfer impact assessments (TIAs)

The CJEU's *Schrems II* judgment (C-311/18, 2020) invalidated Privacy Shield
and held that SCCs remain valid **only if** the parties verify, case by case,
that the clauses can be honoured in practice in the destination country.
Clause 14 of the 2021 SCCs codifies this:

1. **Map the transfer**: data categories, importer role, destination country,
   onward transfers, supporting sub-processors.
2. **Assess destination law and practice**: government access regimes
   (e.g. surveillance statutes), their applicability to this importer and data,
   and available redress — using objective sources and, per Clause 14,
   documented practical experience.
3. **Supplementary measures** where the assessment shows risk (EDPB
   Recommendations 01/2020): technical (state-of-the-art encryption with keys
   held in the EEA, pseudonymisation before export), contractual (transparency
   and challenge commitments — see also Clause 15 duties on government access
   requests), organisational (access policies, minimisation).
4. **Document and keep under review**; make the TIA available to the
   supervisory authority on request. If no combination of measures works,
   suspend or end the transfer.
5. **EU–US note**: the 2023 Data Privacy Framework adequacy decision covers
   transfers to *DPF-certified* US importers; for non-certified importers, SCCs
   plus TIA remain the route (and the DPF's fate is litigation-exposed — keep
   SCC fallback clauses in place).

## TPRM review checklist — processor agreements

1. Roles correctly characterised (controller / processor / joint) and
   consistent with the actual service description.
2. Art. 28(3) chapeau particulars complete: subject matter, duration, nature,
   purpose, data types, data-subject categories.
3. All eight (a)–(h) obligations present and not diluted by the MSA
   (watch limitation-of-liability clauses swallowing breach-assistance costs).
4. Security annex (TOMs) specific, current, and consistent with assurance
   assessment findings; commitment not to degrade TOMs materially.
5. Sub-processing: authorisation model, live sub-processor list, change
   notification with a real objection window, full flow-down and liability.
6. Breach notification window to the controller defined in hours, with content
   requirements (Art. 33(3) elements) and a named contact channel.
7. Data-subject request assistance: process, timescale, cost treatment.
8. Exit: deletion/return at controller's choice, timescale, certification,
   bounded backup carve-out.
9. Audit rights: information provision plus genuine audit/inspection right;
   reliance on certifications (ISO 27001, SOC 2) positioned as *contribution*
   to, not replacement of, the audit right.
10. Transfers: any non-EEA processing hop identified; correct SCC module (and
    UK/Swiss instrument where relevant) executed with completed Annexes I–III;
    docking clause status noted.
11. TIA on file for each third-country destination, with supplementary
    measures recorded and a review trigger defined.
12. Consistency check: sub-processor list vs architecture diagrams vs the
    supplier's questionnaire answers — discrepancies are findings.

## Practitioner cautions

- Art. 28 terms do not legitimise the processing itself — lawful basis,
  transparency and Art. 44+ transfer compliance are separate tests.
- An SCC signature with empty or boilerplate Annexes is a compliance artefact,
  not compliance; regulators read the Annexes first, and so should we.
- "We are ISO 27001 certified" answers part of clause (c) diligence; it answers
  nothing about (a), (d), (g) or (h).
