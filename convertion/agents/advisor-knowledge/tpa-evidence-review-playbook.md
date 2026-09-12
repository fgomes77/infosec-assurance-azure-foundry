# TPA Evidence Review Playbook (certificates, reports, questionnaires)

*Advisor knowledge reference — authored 2026-09-12 for tpa-evidence-analyzer
(and the advisor). Public-terms-only rule applies to any registry lookup.*

## 1. Evidence-type catalogue — what to verify

| Evidence | Verify | Typical validity |
|---|---|---|
| ISO/IEC 27001 certificate (also 27017, 27018, 27701, 22301, 9001, 20000-1, 42001) | Certification body (CB) name; CB accredited by an IAF-member body (mark on certificate); certificate number; **scope statement** and sites; issue/expiry; version (27001:2022 — transition from 2013 completed 31 Oct 2025, 2013 certificates are invalid after that date); status on the CB's public registry or IAF CertSearch (suspended/withdrawn) | 3 years; annual surveillance; recertification audit before expiry |
| SOC 1/2/3 report, ISAE 3402/3000 | See `soc-isae-assurance-reports.md`: opinion, period, criteria, CUECs, subservice carve-outs, exceptions | Type 2 period ≤12 months old; bridge letter ≤6 months |
| Penetration-test report | See `pentest-standards-owasp-ptes-cvss.md`: scope, method, tester, findings, retest | ≤12 months |
| Vulnerability scan report | Tool, date, targets, unpatched Critical/High age | ≤3 months |
| PCI DSS AOC / SAQ / ASV | See `pci-dss-v4-supplier-assurance.md` | AOC ≤12 months; ASV quarterly |
| CSA STAR / CAIQ | See `csa-ccm-caiq-star.md`: level, version, No/NA answers | Annual |
| SIG questionnaire (Shared Assessments) | SIG Core (~19 domains, full) vs SIG Lite (subset); version year; answers with evidence references; "N/A" justifications | Annual |
| Cyber-insurance certificate | Insurer, policy period, limits, cyber cover named | Annual |
| Policies (security, BC, incident, access, supplier) | Owner, approval date (<24 months), version, scope covers the service, review cadence | Reviewed ≤2 years |
| DPA / contract security schedule | GDPR Art. 28(3) clauses, SCC module, audit rights, sub-processor list, DORA Art. 30 provisions | Per contract |
| DR/BC test report | Date, scenario, RTO/RPO achieved vs targets, issues | ≤12 months |
| Sub-processor / fourth-party list | Names, locations, services; matches DPA | Current |
| Screenshots / self-declarations | Self-attestation only; date; who signed | Low weight |

## 2. Validity status rules (recompute at report date)

| Status | Rule |
|---|---|
| VALID | today within [issue, expiry] / audit period end ≤12 months ago |
| EXPIRING | expiry ≤90 days away |
| EXPIRED | expiry passed / SOC period ended >12 months ago without bridge letter |
| PERIOD-GAP | gap between consecutive SOC periods or pentests > 3 months |
| UNDETERMINED | dates not stated in the document (say so; do not infer from file metadata) |

## 3. Scope-match test

State the assessed scope verbatim; compare with the Euronext service
(entities, locations, product/service names, cloud regions). Outcomes:
**Covers** / **Partially covers** (state the missing element) / **Does
not cover** / **Cannot determine**.

## 4. Registry verification (public terms only)

- ISO certificates: CB's online registry or IAF CertSearch — search by
  supplier public name and certificate number; never include Euronext
  identifiers.
- STAR registry, PCI validated-provider lists, accreditation-body lists
  (e.g. national accreditation bodies under IAF/EA), CREST member list.
- Record: registry, date checked, result (found/not found/mismatch).

## 5. Questionnaire reading (SIG / CAIQ / CCM / bespoke)

1. Confirm version and completion date; identify the responder role.
2. Extract all **No / Partial / N/A** answers; group by domain.
3. Cross-check answers against independent evidence (certificate scope,
   SOC exceptions, pentest findings) — inconsistencies are findings.
4. Assess N/A justifications against the service model (a SaaS provider
   claiming N/A for application security is a finding).

## 6. Consolidated verdict per service criticality

| Criticality | Minimum evidence set |
|---|---|
| Critical / Important (DORA) | Valid ISO 27001 (2022) or SOC 2 Type 2 (Security + Availability) + pentest ≤12 months + BC/DR test + DPA/contract with Art. 30 provisions + sub-processor list |
| Standard | ISO 27001 or SOC 2 or completed SIG/CAIQ + pentest or scan + DPA |
| Low | Questionnaire + policy set |

Missing items become **Gaps & recommendations** with the evidence to
request and a due date.
