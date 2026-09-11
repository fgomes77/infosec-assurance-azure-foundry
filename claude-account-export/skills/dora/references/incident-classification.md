# ICT Incident Classification and Reporting — Art. 17–23 DORA + CDR (EU) 2024/1772 + CDR (EU) 2025/301 / CIR (EU) 2025/302

*Reconstructed reference — regenerated on 2026-09-11 to replace a file missing from the original skill upload; verify against the official texts (EUR-Lex) before relying on citations.*

Working reference for classifying ICT-related incidents and cyber threats under
**Art. 18 DORA** and the classification RTS **CDR (EU) 2024/1772**, and for
reporting major incidents under **Art. 19** with the timelines and content of
**CDR (EU) 2025/301** and the templates of **CIR (EU) 2025/302**. Threshold
figures below reflect CDR 2024/1772; confirm exact figures against the CDR text
before quoting them in formal deliverables.

---

## 1. Key Definitions (Art. 3 DORA)

| Term | Definition (paraphrased) | Art. |
|------|--------------------------|------|
| ICT-related incident | A single event or series of linked events unplanned by the entity that compromises the security of network and information systems and has an adverse impact on availability, authenticity, integrity or confidentiality of data or on services | 3(8) |
| Major ICT-related incident | An ICT-related incident with a high adverse impact on network and information systems supporting **critical or important functions** | 3(10) |
| Operational or security payment-related incident | Incident (ICT-related or not) affecting payment-related services of CI/PI/AISP/EMI | 3(9), Art. 23 |
| Cyber threat | Per Art. 2(8) Cybersecurity Act — potential circumstance/event that may damage or disrupt systems | 3(12) |
| Significant cyber threat | Cyber threat whose technical characteristics indicate it **could** have the potential to result in a major incident or major payment-related incident | 3(13) |
| Critical or important function | Function whose disruption would materially impair financial performance, soundness/continuity of services, or regulatory compliance | 3(22) |

**Classify every ICT incident** (Art. 17(2) requires recording all incidents and
significant cyber threats); **report only major ones** (Art. 19(1)); voluntary
notification of significant cyber threats (Art. 19(2)).

---

## 2. Classification Criteria — Art. 18(1) + CDR (EU) 2024/1772

CDR 2024/1772 operationalises seven criteria. For each, the CDR defines when the
criterion is "met"; a combination rule (Section 4) then determines majority.

### 2.1 Clients, financial counterparts and transactions affected (Art. 1–2 CDR)

Criterion is met when any of:
- **> 10%** of all clients using the affected service, or
- **> 100,000** clients affected, or
- **> 30%** of financial counterparts carrying out activities with the entity, or
- **> 10%** of the daily average number or value of transactions of the affected service, or
- identified impact on clients or counterparts which have been **identified as relevant** (e.g. systemically connected counterparts).

Where actual numbers cannot be determined, use **estimates** (highest reasonable
estimate — the CDR expressly requires estimation rather than "unknown").

### 2.2 Reputational impact (Art. 3 CDR)

Met when at least one of: media reflection of the incident; repetitive
complaints from clients or counterparts; likely inability to meet regulatory
requirements visible externally; likely loss of clients or counterparts with a
material impact on the business.

### 2.3 Duration and service downtime (Art. 4 CDR)

Met when:
- incident **duration > 24 hours**, or
- **service downtime > 2 hours** for ICT services supporting **critical or important functions**.

Duration runs from occurrence (or detection, if occurrence unknown — if the
moment of occurrence cannot be established, measure from detection or from
recording in network/system logs) until resolution. Downtime runs from full or
partial unavailability to restoration of regular operation.

### 2.4 Geographical spread (Art. 5 CDR)

Met when the incident has an impact in **two or more Member States**, with regard
to clients/counterparts, branches or group entities, or financial market
infrastructures/third parties affected in those Member States.

### 2.5 Data losses (Art. 6 CDR)

Met when the incident impacts, with an adverse effect on the achievement of the
entity's business objectives or on regulatory compliance:
- **availability** (data not accessible on demand),
- **authenticity** (trustworthiness of data origin compromised),
- **integrity** (data inaccurately modified), or
- **confidentiality** (data accessed or disclosed without authorisation).

Any successful, malicious **unauthorised access** to network and information
systems is treated with particular severity — see Section 4 (it can make an
incident major on its own where systems supporting critical/important functions
are, or may be, affected).

### 2.6 Criticality of the services affected (Art. 7 CDR)

Met when:
- the incident affects ICT services or network and information systems that support **critical or important functions**, or
- financial services requiring **authorisation/registration** are affected, or
- there has been **successful, malicious and unauthorised access** to network and information systems supporting critical or important functions (actual or presumed).

### 2.7 Economic impact (Art. 8 CDR)

Met when gross direct **and indirect costs and losses > EUR 100,000**. Include:
expropriated funds/assets, replacement/relocation costs (software, hardware,
infrastructure), staff costs (incl. overtime and recovery-specific hires),
third-party fees, client compensation and redress, lost revenues, communication
costs, advisory costs (legal/forensic/remediation). **Exclude** funds/assets
recovered (report gross then actuals in the final report) and internal
"business-as-usual" costs. Financial penalties later imposed are not part of the
initial estimate but appear in the final report's actual figures.

---

## 3. Materiality: When Is an Incident **Major**? (Art. 9 CDR 2024/1772)

An ICT-related incident is classified as **major** when:

1. It has affected ICT services or network and information systems supporting
   **critical or important functions** (i.e. the *criticality of services*
   criterion is met), **and**
2. **either** of the following holds:
   - **(a)** successful, malicious and unauthorised access occurred to network and
     information systems, where it **may result in data losses** (this alone
     suffices), **or**
   - **(b)** at least **two other** classification criteria among: clients/
     counterparts/transactions, reputational impact, duration and service
     downtime, geographical spread, data losses, economic impact — are met at
     their thresholds.

**Recurring incidents (Art. 10 CDR):** incidents that individually miss the
thresholds are classified as one major incident when they (a) have occurred at
least twice within 6 months, (b) share the **same apparent root cause**, and
(c) **cumulatively** meet the major-incident conditions. Track recurring
patterns explicitly — this is a commonly missed obligation.

**Payment-related incidents (Art. 23):** for CI/PI/AISP/EMI, apply the same
classification machinery to operational or security payment-related incidents,
ICT-related or not.

**Practical decision flow:**
1. Does the incident touch systems/services supporting a critical or important function? If no → not major (still record it).
2. Malicious successful unauthorised access with possible data loss? If yes → **major**.
3. Count the other criteria met (thresholds above). ≥ 2 → **major**.
4. Same root cause as incidents in the past 6 months? Aggregate and re-test.
5. Document the assessment and timestamp of classification — this starts the clock.

---

## 4. Significant Cyber Threats (Art. 18(2) + Art. 11 CDR 2024/1772)

Classify a cyber threat as **significant** when all of:
- the threat, if materialised, **could** affect critical or important functions
  (or affect other FEs, TPSPs or clients/counterparts),
- it has a **high probability of materialisation** at the entity or at other
  financial entities (based on threat actor capability/intent, observed
  reconnaissance or targeting), and
- if materialised, it **would meet** the major-incident conditions.

Reporting is **voluntary** (Art. 19(2)), but where a significant cyber threat
may affect clients, the entity **must inform potentially affected clients** of
appropriate protection measures (Art. 19(3), second subparagraph — this part is
not voluntary). Use the CIR 2025/302 threat-notification template.

---

## 5. Reporting Major Incidents — Art. 19 + CDR (EU) 2025/301 + CIR (EU) 2025/302

### 5.1 Timeline table

| Stage | Deadline (CDR 2025/301) | Core content |
|-------|--------------------------|--------------|
| **Initial notification** | Within **4 hours of classifying** the incident as major, and in any case **no later than 24 hours after becoming aware** of the incident | Incident reference, entity identification, detection/classification timestamps, description, classification criteria triggered, Member States affected, discovery method, activation of BC plans, other authorities informed |
| **Intermediate report** | Within **72 hours of the initial notification** — even if status is unchanged; plus updated reports without undue delay on material status change and when regular activities are restored | Updated impact figures (clients, transactions, downtime, geography), incident type, threat/attack vectors, affected functions and infrastructure components, indicators of compromise, TPSP involvement, actions taken/planned |
| **Final report** | Within **one month** of the intermediate report (or of its latest update) | Root cause analysis, actual direct and indirect costs and losses (gross and net of recoveries), recurrence assessment, resolution details, lessons learned/remediation, whether the incident was reported as a crime |

Additional CDR 2025/301 rules:
- **Weekends/holidays:** where the initial or intermediate deadline falls on a
  weekend or bank holiday and the entity has no 24/7 reporting arrangements,
  submission may be deferred to **noon the next working day** — but this relief
  does not apply to significant credit institutions and does not defer the
  obligation to classify.
- **Combined reports:** stages may be merged if the information for a later
  stage is available before an earlier deadline (e.g. initial+intermediate).
- **Reclassification:** if the incident turns out not to be major, notify the CA
  that it is declassified.
- **Outsourced reporting:** a third party may submit reports, but responsibility
  remains fully with the financial entity (Art. 19(5) DORA — CA notification of
  the outsourcing arrangement required).
- **Templates:** all stages use the CIR (EU) 2025/302 structured template/data
  fields; submit via the CA's designated channel/portal.

### 5.2 Who reports to whom

- Report to the **competent authority** identified per **Art. 46** (e.g. the
  NCA/ECB for credit institutions, the PSD2 CA for PIs).
- The CA forwards to ESAs, ECB, and NIS2 authorities/CSIRTs as relevant
  (Art. 19(6)) — the entity does **not** multi-file under DORA, but parallel
  regimes may still apply (GDPR Art. 33 breach notification to the DPA within
  72h, NIS2 for non-DORA group entities, PSD2 legacy where not displaced by
  Art. 23, national criminal reporting). Maintain a **notification matrix**.
- **Clients:** where a major incident impacts clients' financial interests,
  inform them without undue delay of the incident and of measures taken to
  mitigate adverse effects (Art. 19(3)).

### 5.3 Supervisory feedback and aggregate reporting

- CAs acknowledge receipt and may provide feedback or guidance (Art. 22).
- ESAs publish anonymised, aggregated annual reports on major incidents.
- Art. 11(11) guidelines: entities estimate **aggregated annual costs and
  losses** from major incidents and report them to the CA on request.

---

## 6. Operational Checklist (embed in the incident SOP)

| # | Step | Owner | Evidence |
|---|------|-------|----------|
| 1 | Detect and log incident (Art. 17(2): record **all** incidents) | SOC | Incident ticket with timestamps |
| 2 | Triage against critical/important function mapping (Art. 8 inventory) | Incident manager | Function-mapping lookup |
| 3 | Run CDR 2024/1772 classification (criteria + thresholds; estimates where exact figures unavailable) | Incident manager + risk | Completed classification matrix, classification timestamp |
| 4 | If major: start 4h clock; notify senior management and board line (Art. 17(3)) | Incident manager | Escalation record |
| 5 | Submit initial notification (≤ 4h from classification / ≤ 24h from awareness) via CA portal, CIR 2025/302 template | Reporting officer | Submission receipt |
| 6 | Client communication where financial interests impacted (Art. 19(3)) | Comms per Art. 14 plan | Client notice |
| 7 | Intermediate report ≤ 72h; further updates on material change and on recovery | Reporting officer | Submission receipts |
| 8 | Final report ≤ 1 month after (latest) intermediate report, with root cause and gross/net costs | Reporting officer + finance | Submission receipt |
| 9 | Post-incident review (Art. 13(2)); feed lessons into RMF (Art. 6(5) review trigger) | Risk / CISO | PIR document |
| 10 | Test recurring-incident aggregation over trailing 6 months | Risk | Recurrence log |
| 11 | Parallel regime check: GDPR / NIS2 (group) / PSD2-Art. 23 / criminal | Legal/DPO | Notification matrix sign-off |

---

## 7. Common Errors

| Error | Correction |
|-------|------------|
| Waiting for full facts before classifying (blowing the 24h backstop) | Classify on best estimates; CDR 2024/1772 mandates estimation; refine in later reports |
| Treating the 4h clock as running from detection | It runs from **classification as major**; the 24h backstop runs from awareness |
| Reporting only one intermediate report | Updated intermediate reports are due on material status change and on recovery |
| Counting only direct costs against the EUR 100,000 threshold | The economic-impact criterion is **direct and indirect** gross costs and losses |
| Ignoring near-threshold repeat incidents | Recurring incidents with the same apparent root cause aggregate over 6 months (Art. 10 CDR) |
| Filing free-text reports | CIR 2025/302 structured templates are mandatory |
| Assuming DORA reporting satisfies GDPR | GDPR Art. 33 DPA notification is a separate, parallel obligation |
| Skipping client notice for a significant cyber threat | Art. 19(3) client information duty applies even though CA notification of threats is voluntary |
