# Risk Classification — EU AI Act (Regulation (EU) 2024/1689)

*Reconstructed reference — regenerated on 2026-09-11 to replace a file missing from the original skill upload; verify against the official texts (EUR-Lex) before relying on citations.*

This reference sets out the full four-tier classification methodology: prohibited practices (Art. 5), high-risk classification (Art. 6, Annexes I and III), limited-risk transparency systems (Art. 50), and minimal risk. Apply the decision flow at the end of this file for any classification exercise.

---

## Tier 0 — Preliminary: Is it an AI system at all?

**Art. 3(1) definition:** a machine-based system designed to operate with varying levels of autonomy, that may exhibit adaptiveness after deployment, and that, for explicit or implicit objectives, **infers from the input it receives how to generate outputs** such as predictions, content, recommendations, or decisions that can influence physical or virtual environments.

Key discriminator (Recital 12): the capacity to **infer**. Systems based solely on rules defined entirely by natural persons to automatically execute operations (classic deterministic software, simple statistical lookup) fall outside the definition. If the system is not an AI system, the Regulation does not apply (though GPAI *model* obligations may still apply to a model under Arts. 51–55 — see `gpai-governance.md`).

Also confirm territorial scope (Art. 2): providers placing on the EU market or putting into service in the EU wherever established; deployers established in the EU; providers/deployers in third countries where the **output is used in the EU**. Exclusions: exclusively military/defence/national security purposes; scientific research and development; personal non-professional use; and (partially) free and open-source AI other than prohibited, high-risk, or Art. 50 systems.

---

## Tier 1 — Prohibited Practices (Art. 5) — applicable from 2 February 2025

Any match below means the practice **cannot lawfully be placed on the market, put into service, or used** in the EU. Penalties: up to €35M or 7% of global annual turnover (Art. 99(3)).

| # | Article | Prohibited practice | Conditions / limits / exceptions |
|---|---|---|---|
| 1 | Art. 5(1)(a) | **Subliminal, manipulative or deceptive techniques** beyond a person's consciousness, or purposefully manipulative/deceptive techniques | Prohibited only where the technique **materially distorts behaviour** by appreciably impairing informed decision-making, causing a decision the person would not otherwise have taken, in a manner that causes or is reasonably likely to cause **significant harm** to that person, another person, or a group. |
| 2 | Art. 5(1)(b) | **Exploitation of vulnerabilities** due to age, disability, or a specific social or economic situation | Same qualifiers: the exploitation must have the objective or effect of materially distorting behaviour in a manner causing or reasonably likely to cause significant harm. |
| 3 | Art. 5(1)(c) | **Social scoring** — evaluation/classification of natural persons or groups over time based on social behaviour or known/inferred/predicted personal or personality characteristics | Prohibited only where the score leads to detrimental or unfavourable treatment (i) in **social contexts unrelated** to the context in which the data was generated/collected, or (ii) that is **unjustified or disproportionate** to the social behaviour or its gravity. Applies to public and private actors. |
| 4 | Art. 5(1)(d) | **Predictive criminal-risk assessment of individuals** — assessing/predicting the risk of a natural person committing a criminal offence based **solely** on profiling or on assessment of personality traits and characteristics | **Exception:** does not apply to AI systems used to **support human assessment** of involvement in criminal activity that is **already based on objective and verifiable facts directly linked** to that activity. |
| 5 | Art. 5(1)(e) | **Untargeted scraping of facial images** from the internet or CCTV footage to create or expand facial recognition databases | No exceptions. (The Clearview-style use case.) |
| 6 | Art. 5(1)(f) | **Emotion inference in the workplace and education institutions** | **Exception:** permitted where intended for **medical or safety reasons** (e.g. driver-fatigue monitoring). Emotion recognition outside workplace/education is not prohibited but is high-risk under Annex III point 1(c) and carries Art. 50(3) transparency duties. |
| 7 | Art. 5(1)(g) | **Biometric categorisation** inferring race, political opinions, trade-union membership, religious or philosophical beliefs, sex life, or sexual orientation from biometric data | **Exception:** labelling/filtering of lawfully acquired biometric datasets (e.g. by law enforcement), and categorisation of biometric data in the law-enforcement domain. |
| 8 | Art. 5(1)(h) | **Real-time remote biometric identification (RBI) in publicly accessible spaces for law-enforcement purposes** | Permitted **only** where strictly necessary for one of three objectives: (i) targeted search for victims of abduction, trafficking, sexual exploitation, or missing persons; (ii) prevention of a specific, substantial and imminent threat to life/physical safety or a genuine and present/foreseeable threat of terrorist attack; (iii) localisation/identification of a suspect of an Annex II-listed offence punishable by ≥4 years. Safeguards (Art. 5(2)–(7)): prior authorisation by a judicial or independent administrative authority (urgency: within 24 h), fundamental-rights impact assessment, registration, national law authorising the use, notification of market surveillance and data protection authorities, and annual Commission reporting. |

**Practice note:** items 1–4 turn on *effect* qualifiers (material distortion, significant harm, detrimental treatment). Document the assessment of each qualifier — a negative Art. 5 screen should be evidenced, not asserted. The Commission's Guidelines on prohibited practices (C(2025) 884, Feb 2025) are the primary interpretive aid.

---

## Tier 2 — High-Risk (Art. 6)

### Path A — Art. 6(1): Annex I product-safety route

An AI system is high-risk when **both** conditions are met:

1. It is intended to be used as a **safety component** of a product, or is itself a product, covered by the **Union harmonisation legislation listed in Annex I**; **and**
2. That product (or the AI system as a product) is required to undergo a **third-party conformity assessment** under that Annex I legislation.

Annex I, Section A (New Legislative Framework acts) includes, among others: Machinery (2006/42/EC, now Reg. (EU) 2023/1230), Toys (2009/48/EC), Recreational craft (2013/53/EU), Lifts (2014/33/EU), ATEX (2014/34/EU), Radio Equipment (2014/53/EU), Pressure equipment (2014/68/EU), Cableways (2016/424), PPE (2016/425), Gas appliances (2016/426), **Medical Devices (2017/745)** and **IVD (2017/746)**. Annex I, Section B (old-approach acts) covers aviation, motor vehicles, agricultural vehicles, marine equipment, rail interoperability — for Section B, only Art. 102–109 amendments and Art. 6(1) classification apply via the sectoral procedures.

Application date for Art. 6(1) systems: **2 August 2027**.

### Path B — Art. 6(2): Annex III use-case route

AI systems falling under any of the eight Annex III areas are high-risk (subject to the Art. 6(3) derogation below). Application date: **2 August 2026**.

**Annex III — the 8 areas in full:**

1. **Biometrics** (where permitted under Union/national law):
   - (a) remote biometric identification systems (excluding pure biometric *verification* confirming a person is who they claim to be);
   - (b) biometric categorisation according to sensitive or protected attributes/characteristics based on inference of those attributes;
   - (c) emotion recognition systems.
2. **Critical infrastructure:** safety components in the management and operation of critical digital infrastructure, road traffic, or the supply of water, gas, heating, or electricity.
3. **Education and vocational training:**
   - (a) determining access/admission or assigning persons to institutions;
   - (b) evaluating learning outcomes (including where used to steer the learning process);
   - (c) assessing the appropriate level of education a person will receive or be able to access;
   - (d) monitoring and detecting prohibited behaviour of students during tests (proctoring).
4. **Employment, workers management and access to self-employment:**
   - (a) recruitment or selection — targeted job ads, analysing/filtering applications, evaluating candidates;
   - (b) decisions affecting work-related relationships — promotion, termination, task allocation based on individual behaviour or personal traits, monitoring and evaluating performance and behaviour.
5. **Access to and enjoyment of essential private services and essential public services and benefits:**
   - (a) evaluating eligibility for essential public assistance benefits and services (including healthcare), and granting, reducing, revoking, or reclaiming them;
   - (b) creditworthiness evaluation / credit scoring of natural persons (**exception:** detecting financial fraud);
   - (c) risk assessment and pricing in **life and health insurance** for natural persons;
   - (d) evaluating and classifying emergency calls, or dispatching / prioritising emergency first-response services (police, fire, medical, triage).
6. **Law enforcement** (where permitted under Union/national law):
   - (a) assessing the risk of a person becoming a victim of criminal offences;
   - (b) polygraphs and similar tools;
   - (c) evaluating the reliability of evidence in investigation/prosecution;
   - (d) assessing risk of (re-)offending **not solely** based on profiling (Art. 5(1)(d) covers "solely"), or assessing personality traits/past criminal behaviour;
   - (e) profiling (Directive (EU) 2016/680 Art. 3(4)) in detection, investigation, or prosecution.
7. **Migration, asylum and border control management** (where permitted):
   - (a) polygraphs and similar tools;
   - (b) assessing security, irregular-migration, or health risks posed by a person entering/having entered a Member State;
   - (c) examining applications for asylum, visa, residence permits and associated complaints, including reliability-of-evidence assessment;
   - (d) detecting, recognising or identifying natural persons in this context (excluding travel-document verification).
8. **Administration of justice and democratic processes:**
   - (a) assisting judicial authorities in researching and interpreting facts and law and applying the law to facts (or used the same way in alternative dispute resolution);
   - (b) influencing the outcome of an election or referendum or voting behaviour (**exception:** tools not directly interacting with persons — campaign logistics, administrative organisation).

### Art. 6(3) derogation — the "no significant risk" carve-out

An Annex III system is **not** high-risk where it does not pose a significant risk of harm to health, safety, or fundamental rights, **including by not materially influencing the outcome of decision-making**. This applies where **any one** of the four conditions is fulfilled:

- **(a)** the system performs a **narrow procedural task**;
- **(b)** the system **improves the result of a previously completed human activity**;
- **(c)** the system **detects decision-making patterns or deviations** from prior patterns and is not meant to replace or influence the previously completed human assessment without proper human review;
- **(d)** the system performs a **preparatory task** to an assessment relevant for an Annex III use case.

**Absolute carve-out from the carve-out:** an Annex III system that performs **profiling of natural persons** (GDPR Art. 4(4)) is **always high-risk** — the derogation cannot be invoked (Art. 6(3), third subparagraph).

Procedural requirements: a provider relying on Art. 6(3) must **document the assessment before placing on the market** (Art. 6(4)), still **register** the system in the EU database under Art. 49(2) (Annex VIII Section B lite entry), and provide the documentation to national authorities on request. Misclassification to evade high-risk status carries Art. 99 exposure. Commission guidelines with practical examples are mandated by Art. 6(5) (due 2 Feb 2026).

---

## Tier 3 — Limited Risk: Art. 50 transparency obligations

These apply **regardless of risk tier** (they can stack on high-risk) but define the "limited-risk" tier where no other obligations attach. Applicable from 2 August 2026.

| Provision | System | Obligation | Exceptions |
|---|---|---|---|
| Art. 50(1) | AI systems **interacting directly with natural persons** (chatbots, voice agents) | Provider must design so persons are informed they are interacting with AI | Unless obvious to a reasonably well-informed, observant, circumspect person; law-enforcement carve-out |
| Art. 50(2) | **Generative AI** (systems, incl. GPAI systems, generating synthetic audio, image, video, or text) | Provider must mark outputs in machine-readable format as artificially generated/manipulated (watermarking/provenance — effective, interoperable, robust, reliable so far as technically feasible) | Assistive/standard-editing functions; law-enforcement authorised uses |
| Art. 50(3) | **Emotion recognition and biometric categorisation** systems | Deployer must inform exposed persons of operation; process personal data per GDPR/LED | Law-enforcement carve-out (with safeguards) |
| Art. 50(4) | **Deep fakes** (image/audio/video) and **AI-generated text published to inform the public on matters of public interest** | Deployer must disclose artificial generation/manipulation | Art/satire/fiction (disclosure in a manner not hampering the work); human editorial review with editorial responsibility (text); law-enforcement |

Information must be provided clearly and distinguishably **at the latest at the time of first interaction or exposure** (Art. 50(5)). The AI Office facilitates codes of practice on detection and labelling (Art. 50(7)).

---

## Tier 4 — Minimal Risk

Everything else: spam filters, AI in video games, inventory optimisation, recommender systems outside Annex III contexts, most internal productivity tooling. **No mandatory obligations** under the Regulation. Voluntary codes of conduct are encouraged (Art. 95), and general AI-literacy duties (Art. 4, from 2 Feb 2025) still apply to providers and deployers of *all* AI systems.

---

## Step-by-Step Decision Flow

```
STEP 0  Is it an AI system per Art. 3(1) (capacity to infer)?
        ├─ No  → Out of scope (check GPAI model obligations separately)
        └─ Yes → continue. Confirm Art. 2 territorial scope & exclusions.

STEP 1  Screen against all 8 Art. 5 prohibited practices,
        applying each practice's effect qualifiers and exceptions.
        ├─ Match, no exception applies → PROHIBITED. Stop. Cannot deploy in EU.
        └─ No match → continue (document the negative screen).

STEP 2  Art. 6(1): safety component of / product under Annex I
        requiring third-party conformity assessment?
        ├─ Yes → HIGH-RISK (Path A). Obligations from 2 Aug 2027,
        │        integrated into the sectoral conformity procedure.
        └─ No  → continue.

STEP 3  Does the intended purpose fall under any Annex III area 1–8?
        ├─ No  → go to STEP 5.
        └─ Yes → STEP 4.

STEP 4  Art. 6(3) derogation test:
        Does the system profile natural persons?
        ├─ Yes → HIGH-RISK. Derogation unavailable.
        └─ No  → Does at least one of conditions (a)–(d) apply
                 (narrow procedural task / improves prior human work /
                  pattern-deviation detection with human review /
                  preparatory task)?
                 ├─ Yes → NOT high-risk. Document assessment (Art. 6(4)),
                 │        register under Art. 49(2), check STEP 5.
                 └─ No  → HIGH-RISK (Path B). Obligations from 2 Aug 2026.

STEP 5  Art. 50 transparency triggers (can stack on any tier):
        human interaction / synthetic content / emotion recognition or
        biometric categorisation / deep fakes or public-interest text?
        ├─ Yes → LIMITED RISK obligations apply (Art. 50).
        └─ No  → MINIMAL RISK. Voluntary codes (Art. 95); AI literacy (Art. 4).

PARALLEL  If a GPAI model is involved (Art. 3(63)), run the Arts. 51–55
          analysis separately — model obligations attach to the model
          provider independently of system-level classification.
```

**Output of a classification exercise** should always record: role (provider/deployer/importer/distributor per Art. 3 and Art. 25 re-qualification), intended purpose as stated in instructions for use, the tier, the article/annex point relied on, exceptions or derogations invoked with reasoning, and the applicable compliance date.
