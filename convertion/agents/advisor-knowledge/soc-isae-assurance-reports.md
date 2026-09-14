# SOC 1 / SOC 2 / SOC 3 and ISAE 3402 / ISAE 3000 Reliance Guide

*Advisor knowledge reference — authored 2026-09-12 to ground the persona
domain "SOC 1/2/3 reliance" for soc-report-analyzer, tpa-evidence-analyzer
and the advisor. Based on the AICPA SOC suite (SSAE 18 / AT-C 320 for SOC 1,
AT-C 205 + TSP section 100 (TSC 2017, 2022 points-of-focus revision) for
SOC 2/3) and IAASB ISAE 3402 / ISAE 3000 (Revised). Verify quotes against
the report at hand.*

## 1. Report taxonomy

| Report | Standard | Subject | Users | Distribution |
|---|---|---|---|---|
| SOC 1 | SSAE 18 (AT-C 320) / ISAE 3402 | Controls at a service organisation relevant to user entities' **internal control over financial reporting** (ICFR) | User entities' financial auditors, management | Restricted |
| SOC 2 | AT-C 205 + TSC 2017 / ISAE 3000 | Controls relevant to **Security** (mandatory common criteria) and optionally Availability, Processing integrity, Confidentiality, Privacy | Customers, regulators, TPRM | Restricted (NDA) |
| SOC 3 | Same criteria as SOC 2 | General-use summary with the opinion, no test detail | Public | Public seal |
| Type 1 | — | Design and implementation **at a point in time** | Limited reliance | — |
| Type 2 | — | Design **and operating effectiveness over a period** (usually 6–12 months) | Reliance basis for TPRM | — |

ISAE 3402 is the international equivalent of SOC 1; ISAE 3000 (Revised)
underlies international SOC 2-style reports (often "ISAE 3000 SOC 2").
Other assurance letters (agreed-upon procedures, ISRS 4400) are NOT
opinions and give no reliance.

## 2. Report sections (SOC 2 Type 2)

| Section | Content | What to extract |
|---|---|---|
| I — Independent service auditor's report | Opinion, scope, period, criteria, inclusive/carve-out method, responsibilities | Opinion type verbatim; period start/end; audit firm; opinion date |
| II — Management's assertion | Management asserts the description is fair and controls were effective | Confirms scope boundaries |
| III — System description | Services, infrastructure, software, people, procedures, data; **subservice organisations**; **CUECs** | System boundaries vs the Euronext service; subservice list; CUEC list |
| IV — Trust services criteria, controls, tests and results | Every control, the auditor's test, **results incl. exceptions / deviations** | All exceptions (control id, nature, management response); criteria mapped |
| V — Other information provided by the service organisation | Unaudited (management responses, future plans) | Treat as unaudited assertions |

## 3. Opinion types

| Opinion | Meaning | Reliance |
|---|---|---|
| **Unqualified** (unmodified) | Description fair, controls suitably designed and (Type 2) operating effectively | Full |
| **Qualified** | "except for" one or more matters (control failures, description misstatement) | Partial — analyse the exception scope |
| **Adverse** | Controls not effective / description materially misstated | None |
| **Disclaimer** | Auditor could not obtain evidence | None |

Quote the opinion paragraph verbatim in summaries; an "except for"
sentence defines the boundary of the qualification.

## 4. Trust services categories (TSC 2017)

- **Security (Common Criteria CC1–CC9)** — CC1 control environment, CC2
  communication, CC3 risk assessment, CC4 monitoring, CC5 control
  activities, CC6 logical and physical access, CC7 system operations
  (monitoring, incidents), CC8 change management, CC9 risk mitigation
  incl. vendors. Mandatory in every SOC 2.
- **Availability (A1)**, **Processing integrity (PI1)**, **Confidentiality
  (C1)**, **Privacy (P1–P8)** — optional; check which are IN SCOPE before
  asserting coverage (e.g. no Availability = no assurance on DR/BC).

## 5. Exceptions, CUECs, subservice organisations

- **Exception / deviation:** a test result showing the control did not
  operate as described. Assess: control id, criteria affected, frequency
  (1 of 25 samples?), compensating controls, management response,
  relevance to the Euronext service. Aggregate exceptions may not change
  the opinion but change YOUR reliance.
- **CUEC (complementary user-entity controls):** controls Euronext must
  operate for the service organisation's controls to achieve the
  criteria (e.g. user-access reviews, MFA configuration). Every CUEC is
  mapped to a Euronext owner or listed as a gap.
- **CSOC (complementary subservice organisation controls):** controls
  assumed at subservice providers (typically the cloud hyperscaler).
- **Carve-out vs inclusive:** carve-out excludes the subservice
  organisation's controls — obtain that organisation's own SOC report
  (chain of reliance). Inclusive includes them.

## 6. Period, currency and bridge letters

- Type 2 period should cover ≥6 months; a period ending **>12 months**
  before the assessment date gives stale assurance → request the new
  report or a **bridge (gap) letter** from management covering the
  interval (a bridge letter is a management assertion, not audited —
  accept for ≤3–6 months only).
- Check the report date vs the fieldwork end; check the report covers the
  **locations/services actually used** by Euronext.
- ISO 27001 certificate ≠ SOC 2: different objects (ISMS conformity vs
  control operating effectiveness); both may be needed.

## 7. Reading procedure (analyzer)

1. Section I: opinion, period, criteria in scope, method (carve-out).
2. Section III: system boundary vs Euronext service; subservice list;
   CUECs.
3. Section IV: enumerate EVERY exception with control id, criterion,
   description, management response — no sampling.
4. Section V: note unaudited claims separately.
5. Verdict: reliance **Full / Partial (conditions) / None** with
   rationale; open actions (bridge letter, subservice SOC, CUEC owners).

## 8. Cross-framework map

| SOC element | ISO 27001:2022 Annex A | DORA | Other |
|---|---|---|---|
| Vendor reliance on SOC reports | 5.19–5.22 (supplier relationships, ICT supply chain, monitoring) | Art. 28(2), Art. 30(2)(e)/(3)(e) audit and access rights | NIST CSF GV.SC; CIS 15 |
| CC6 logical access | 5.15–5.18, 8.2–8.5 | Art. 9 protection and prevention | CIS 5/6 |
| CC7 operations / incidents | 5.24–5.28, 8.15–8.16 | Art. 10–11, 17 | CIS 8/17 |
| CC8 change management | 8.32 | Art. 9(4)(e) | CIS 16 |
| CC9 risk mitigation & vendors | 5.7, 5.19 | Art. 28–29 | COSO principle 7 |
| A1 availability | 5.29–5.30, 8.14 | Art. 11–12 | ISO 22301 |
