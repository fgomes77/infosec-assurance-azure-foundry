# RACI — InfoSec Assurance Platform on Azure AI Foundry

Responsibility matrix for every lifecycle activity of the conversion kit,
companion to `TEAM_MODEL.md` (§16 summarises it; §12 fixes who may
approve, §7 who may change). Exactly one **A** per row. Nothing here
changes what agents produce; it fixes who does, decides, is asked and is
told. Placeholders in `{braces}`; no real UPNs or object ids.

## 1. Parties

| Code | Party | Identity / group in `TEAM_MODEL.md` |
|---|---|---|
| **FGG** | Francisco Gustavo Gomes — **accountable owner** (creation, planning, maintenance, optimisation, updates / re-sync); assurance user | `{upn:francisco.gomes}`; `sg-infosec-foundry-owner`, `-admin-pim` (eligible), `-senior-approvers`, `-users`, `-report-approvers` |
| **JMo** | José Mogollon — assurance user, report approver | `{upn:jose.mogollon}`; `-users`, `-report-approvers` |
| **PSa** | Pedro Santos — assurance user, report approver | `{upn:pedro.santos}`; `-users`, `-report-approvers` |
| **JMe** | José Meireles — assurance user, report approver | `{upn:jose.meireles}`; `-users`, `-report-approvers` |
| **TMo** | Tânia Morais — assurance user, report approver | `{upn:tania.morais}`; `-users`, `-report-approvers` |
| **DEP** | Deputy — **overlay** on one of JMo / PSa / JMe / TMo, nominated by FGG, confirmed by LM, named in `ACCESS_REGISTER.md` | `{upn:deputy-approver}`; `-senior-approvers`, `-breakglass` (eligible), GitHub Write (reviews) |
| **LM** | Line manager / CISO delegate | `{upn:line-manager}`; owner of `-owner`, `-senior-approvers`, `-admin-pim`, `-breakglass` |
| **LZ** | Azure landing-zone team + Entra IAM team | `{group:azure-platform}`, `{group:iam-admins}` |
| **CUST** | Target-system custodians (Jira, Confluence, OneTrust, SecurityScorecard, IAF, ENX gateway) | `{group:jira-admins}`, `{group:onetrust-admins}`, `{group:enx-gateway}`, `{upn:iaf-owner}`, … (`TEAM_MODEL.md` §10) |
| **M365** | SharePoint / Power Platform admins | `{group:spo-admins}`, Power Platform admins |
| **DPO** | Data-protection office | `{group:dpo}` |
| **AUD** | ISMS / internal audit | `{group:isms-audit}` via `sg-infosec-foundry-readers` |
| **SOC** | Euronext SOC / CSIRT on-call | `{group:soc-oncall}` |

Reading rules:

- The four assurance users have the **identical persona experience and
  identical R/C/I** by design (`TEAM_MODEL.md` §1) — the columns are
  named so that each person can find their duties, not because the duties
  differ. The only per-person difference is the DEP overlay: the person
  holding it carries the DEP cell **in addition to** their own.
- "R (≠ requester)" means any of the named people except the one who
  requested the item — the requester-exclusion rule enforced by
  `approval-policy.json`.
- FGG is A for every activity except the four rows where accountability
  must sit outside the person being controlled: review of his own
  privileged access (R32), approval of break-glass (R26), deputy
  nomination / owner succession (R34), and the GDPR Art. 33 path (R36).
- Cadence tells how often the row is exercised; "event" = on demand.

## 2. Team matrix (the five, deputy overlay, line manager)

| Id | Activity | Cadence | FGG | JMo | PSa | JMe | TMo | DEP | LM |
|---|---|---|---|---|---|---|---|---|---|
| **Create** | | | | | | | | | |
| R1 | Platform design and architecture decisions (agents, tiers, connections, pipelines, guardrails — `../ARCHITECTURE.md`) | event | **A/R** | C | C | C | C | C | I |
| R2 | Infrastructure provisioning (`../infra/main.bicep`, `rbac.bicep`, Key Vault, Logic Apps, delivery Function, storage, monitoring) | event | **A/R** (PIM window or deploy SP) | I | I | I | I | C | I |
| R3 | Identity bootstrap — seven groups, CA policy, PIM policies, deploy SP federation, Graph consent, `Sites.Selected` grants, site permissions (`TEAM_MODEL.md` §18) | once + change | **A/R** (requests, grants site-side) | I | I | I | I | C | R (approves privileged-group setup) |
| R4 | Agent conversion and deployment — `../deploy.sh` convert → verify → create → attach → orchestrator → advisory profile | event | **A/R** | I | I | I | I | C (code-owner review) | I |
| R5 | Integration onboarding — `conn-*` connections, read-only service accounts, tokens into Key Vault by name | event | **A/R** (Foundry side) | I | I | I | I | C | I |
| R6 | SharePoint structure — `Reports/`, `Reports/DPO/`, `Templates/`, `Governance/`, unique permissions, versioning, labels (`../sharepoint/README.md`, §9) | once + change | **A/R** (site owner) | I | I | I | I | I | I |
| R7 | Copilot Studio publication to `sg-infosec-foundry-users`; MCP endpoints (local default, hosted optional); approved-client register | event | **A/R** | I | I | I | I | C | I |
| R8 | Go-live validation — smoke test, known-good comparison set, verifier PASS on every report type (`../scripts/smoke_test.py`, `../scripts/verify_conversion.py`) | release | **A/R** | R (domain samples) | R (domain samples) | R (domain samples) | R (domain samples) | C | I |
| **Plan** | | | | | | | | | |
| R9 | Roadmap — new systems / agents / integrations, tier assignments, sequencing | quarterly | **A/R** | C | C | C | C | C | C |
| R10 | Capacity and budget planning (model TPM capacity, App Insights retention, Bing quota) | quarterly | **A/R** | I | I | I | I | I | C (budget) |
| **Run** | | | | | | | | | |
| R11 | Request and produce reports a–f, d2 through the pipelines (`../workflows/pipelines.json`) with Supplier + Service | daily | R | R | R | R | R | — | — |
| R11 | ↳ accountability for the delivery layer behaving as specified | — | **A** | | | | | | |
| R12 | Tier A approvals — `DeepSearch`, `EvidenceAnalysis`, `SOCSummary`, `PentestSummary`, `JIRA_CREATE`, `IAF_SUBMIT` (peer four-eyes) | daily | **A** (routing) / R (≠ requester) | R (≠ requester) | R (≠ requester) | R (≠ requester) | R (≠ requester) | — | — |
| R13 | Tier B approvals — `InfoSecTPA-DPO`, `CyberForum`, `CISOGlobal` (senior four-eyes; FGG's own requests → DEP) | weekly | **A** / R (≠ requester) | I (requester) | I (requester) | I (requester) | I (requester) | R (≠ requester; 2-business-day fallback rule) | — |
| R14 | Advisory use g / h / i — threads named and tagged per §13, uploads limited to the run, thread clean-up after approval | daily | **A** / R | R | R | R | R | — | — |
| R15 | Template proposals (j) via `template-manager` — select, analyse, edit, visual before / after review package | event | R | R | R | R | R | — | — |
| R15 | ↳ accountability for the template library (`../templates/registry.json`) | — | **A** | | | | | | |
| R16 | Tier C approval of `TEMPLATE_UPDATE` and propagation (`../scripts/update_templates.py`); proposals authored by FGG → DEP approves after visual-diff review | event | **A** / R (approves others' proposals) | I | I | I | I | R (approves FGG's proposals) | — |
| R17 | Shared memory `vs-assurance-memory` — add notes under own identity; delete own; owner deletes any via recorded `MEMORY_DELETE` (DEP approves when FGG is the author) | daily / quarterly prune | **A** / R (prune) | R | R | R | R | R (`MEMORY_DELETE` on FGG-authored notes) | — |
| R18 | Evidence library upkeep — `GRC/TPA/Active/<Supplier>[/<Service>]/` inputs for d2 (pre-existing job duty) | daily | **A** / R | R | R | R | R | — | — |
| **Maintain** | | | | | | | | | |
| R19 | Maintenance — runtime / SDK pins (`../setup/requirements.txt`), renderer re-staging, workflow health, drift remediation (re-run `../deploy.sh`) | monthly + event | **A/R** | I | I | I | I | R (when FGG absent, via break-glass) | I |
| R20 | Platform change (`PLATFORM_CHANGE`) — PR, CODEOWNERS review, `production` environment approval, deployment; scope per §12.1 | event | **A** / R (author, merge, approve deployment) | C (may propose via PR) | C (may propose via PR) | C (may propose via PR) | C (may propose via PR) | R (required reviewer of FGG-authored PRs) | I |
| R21 | Updates / re-sync from a fresh claude.ai export — `../deploy.sh`, fidelity verify, drift baseline refresh, release note | event | **A/R** | I (release note) | I (release note) | I (release note) | I (release note) | C (review) | I |
| R22 | Integration credential rotation — new Key Vault secret version, connection re-pointed, register updated (§10 periods) | 90 / 180 d | **A/R** (Foundry, KV) | I | I | I | I | C (verifies ticket ↔ secret version at the quarterly sample) | I |
| R23 | Backup / DR — templates and knowledge in git + export, vector stores rebuilt by `../deploy.sh`, memory store export, Logic Apps definitions in repo, SharePoint versioning | quarterly test | **A/R** | I | I | I | I | R (restore drill when FGG absent) | I |
| R24 | Monitoring and alert triage — egress alert, verifier FAIL rate, latency, cost, agent drift, PIM / break-glass activity (`../governance/DATA_PROTECTION_GUARDRAILS.md` §1 detective layer) | daily | **A/R** | I | I | I | I | R (when FGG absent) | I (monthly PIM report) |
| R25 | Incident response (platform) — contain (disable connection / workflow / tool / secret), investigate, fix forward, record | event | **A/R** (lead) | R (report, stop own runs) | R (report, stop own runs) | R (report, stop own runs) | R (report, stop own runs) | R (lead when FGG absent) | I (P1 / P2) |
| R26 | Break-glass activation (owner unavailable > 2 business days with a pending Tier C item, or P1 / P2 incident) — activate, act within the ticket, deactivate (`../operations/access-governance/BREAK_GLASS.md`) | event | I (post-review ≤ 5 business days) | — | — | — | — | R (activates, acts) | **A** (approves; or SOC on-call) |
| R27 | User support — L1 peer help, L2 owner, L3 landing-zone / Microsoft; Teams channel `{teams:infosec-assurance-platform}` | daily | **A/R** (L2) | R (L1) | R (L1) | R (L1) | R (L1) | R (L2 backup) | I |
| **Optimise** | | | | | | | | | |
| R28 | Monthly evaluation review — verifier first-pass rate, approval vs rework, grounding rate, known-good comparison (`../ARCHITECTURE.md` metrics) | monthly | **A/R** | R (domain samples) | R (domain samples) | R (domain samples) | R (domain samples) | C | I (quarterly summary) |
| R29 | Monthly cost / token-economy review — tokens per deliverable, capacity, tier moves (`../governance/MODEL_ROUTING.md` rule 7; a tier change is a Tier C change) | monthly | **A/R** | I | I | I | I | I | I (budget) |
| R30 | Prompt / knowledge / RAG tuning — instructions, knowledge packs, retrieval settings (always through R20) | event | **A/R** | C (quality feedback) | C (quality feedback) | C (quality feedback) | C (quality feedback) | R (reviews FGG's changes) | — |
| **Govern** | | | | | | | | | |
| R31 | Quarterly access review — user-facing groups (`-users`, `-report-approvers`, `-readers`), RBAC vs `rbac.bicep`, SharePoint, connections, GitHub, Copilot, drift, memory, approval sampling (`../operations/access-governance/QUARTERLY_ACCESS_REVIEW.md`) | quarterly | **A/R** | C (attest own access) | C (attest own access) | C (attest own access) | C (attest own access) | R (independent checks: connections, drift, memory, sampling) | I |
| R32 | Quarterly access review — privileged groups (`-owner`, `-senior-approvers`, `-admin-pim`, `-breakglass`), PIM activations, GitHub protections, ledger re-confirmation | quarterly | R (provides evidence) | — | — | — | — | C | **A/R** |
| R33 | Joiner / mover / leaver (`../operations/access-governance/ACCESS_LIFECYCLE.md`) — access package, onboarding attestation, `-report-approvers` after attestation, same-day removal, thread re-tagging | event | **A/R** | R (peer approver on the joiner's first report) | R (peer approver on the joiner's first report) | R (peer approver on the joiner's first report) | R (peer approver on the joiner's first report) | C | R (requests via access package; triggers removal) |
| R34 | Deputy nomination / change and owner succession (hand-over checklist §14) | event | R (nominates; hands over) | C | C | C | C | R (successor by default) | **A** (confirms / appoints) |
| R35 | AIMS / EU AI Act deployer records — Art. 26 deployer file, ISO 42001 A.6 lifecycle evidence, RoPA entry `{ropa:infosec-foundry-memory}`, platform DPIA, Copilot channel scope | annual + change | **A/R** | C | C | C | C | I | C |
| R36 | Personal-data breach path (GDPR Art. 33 / 34) when an incident touches personal data | event | R (facts, containment) | I | I | I | I | R (when FGG absent) | I |
| R36 | ↳ notification decision | — | | | | | | | (A = DPO, table §3) |
| R37 | Registers — `ACCESS_REGISTER.md` (people, groups, non-human identities, approved MCP clients, change log), approval decision records under `Governance/Approvals/` | continuous | **A/R** | I | I | I | I | C | I |
| R38 | Decommissioning / exit — disable connections, revoke `Sites.Selected` grants and Graph consent, delete agents and vector stores, export records of record, empty groups | event | **A/R** | I | I | I | I | C | C |

## 3. External parties per activity

| Id | LZ | CUST | M365 | DPO | AUD | SOC |
|---|---|---|---|---|---|---|
| R1 | C (region, policy, private endpoints) | I | I | I (platform DPIA) | I | — |
| R2 | R (subscription, RG, policy, budgets) | — | — | — | I | — |
| R3 | R (groups, CA, PIM, deploy SP, admin consent) | — | R (site-collection backup owner) | — | I | — |
| R4 | I | — | — | — | I | — |
| R5 | C (app registrations, federated credentials) | R (issue read-only identities and tokens, revoke) | — | — | I | — |
| R6 | — | — | C (site provisioning, labels, audit log retention) | C (`Reports/DPO/` visitor scope) | I | — |
| R7 | C (Container Apps, Easy Auth) | C (ENX gateway registration) | R (Copilot environment, DLP, tenant approval) | I | I | — |
| R8 | — | — | — | — | I | — |
| R9 | I | I | I | — | I | — |
| R10 | C (FinOps, cost alerts) | — | — | — | — | — |
| R11 | — | — | — | I (DPO reports, b) | — | — |
| R12 | — | — | — | — | — | — |
| R13 | — | — | — | I (b) | — | — |
| R14 | — | — | — | — | — | — |
| R15 | — | — | — | C (templates carrying personal-data fields) | — | — |
| R16 | — | — | — | C (DPO template) | I | — |
| R17 | — | — | — | I (RoPA, count reported quarterly) | — | — |
| R18 | — | — | I | — | — | — |
| R19 | C (platform issues) | I | I | — | I | — |
| R20 | I (RBAC / CA / PIM changes need LZ execution) | I (scope changes) | I | I | I | — |
| R21 | — | — | — | — | I | — |
| R22 | C (federated identity migration) | R (issue new token / scope, revoke old) | C (Graph grants) | — | I | — |
| R23 | C (backup policy, region pairs) | — | C (SharePoint restore) | — | I | — |
| R24 | C (Azure Monitor, Defender for Cloud signals) | I | — | — | — | C (correlated alerts) |
| R25 | C (containment at subscription level) | C (revoke credential) | C (SharePoint containment) | I (A on the R36 path) | I | C / R (escalation) |
| R26 | R (PIM activation record; detective alerts on ARM writes, agent edits, KV SecretGet) | — | — | — | I | R (may approve when the line manager is unavailable) |
| R27 | R (L3 Azure) | R (L3 integration) | R (L3 SharePoint / Copilot) | — | — | — |
| R28 | — | — | — | — | I | — |
| R29 | C (FinOps) | — | — | — | — | — |
| R30 | — | — | — | — | — | — |
| R31 | R (Entra access reviews, PIM data) | I | C (site permissions export) | I | I (receives evidence) | — |
| R32 | R (PIM audit log, group data) | — | — | — | I | — |
| R33 | R (execute group changes, revoke sessions) | I | R (site membership follows group) | I | — | — |
| R34 | R (transfer group ownership, eligibilities) | I (custodian rows) | R (site ownership transfer) | I (RoPA owner) | I | — |
| R35 | I | I | I | C | C | — |
| R36 | C | C | C | **A** (notification decision, Art. 33 / 34) | I | C |
| R37 | I | I | — | I | I (reads at review) | — |
| R38 | R (delete resources, groups, SP) | R (revoke identities) | R (revoke grants, archive site content) | C (records retention) | I | — |

## 4. Control mapping per activity group

| Rows | Control implemented | ISO/IEC 27001:2022 | DORA | ISO/IEC 42001 / EU AI Act / other |
|---|---|---|---|---|
| R1–R8 | Accountable owner for creation; RBAC-as-code; identity bootstrap outside the owner's own control; validated go-live | A.5.2, A.5.8, A.8.9, A.8.29, A.8.32 | Art. 5(2), 8, 9(4)(e) | ISO 42001 A.6.2.2–A.6.2.4; EU AI Act Art. 26(1) |
| R9–R10 | Planned change and capacity | A.5.8, A.8.6 | Art. 9(2), 11(1) | ISO 42001 A.6.1.2 |
| R11–R14, R18 | Human-in-the-loop release of records of record; requester exclusion; peer / senior four-eyes | A.5.3, A.8.15 | Art. 9(4)(c), 28(1) | EU AI Act Art. 14, 26(2); ISO 42001 A.9.2, A.9.3 |
| R15–R16 | Template change control with visual review and owner-only approval; deputy on owner's own items | A.5.3, A.8.32 | Art. 9(4)(e) | ISO 42001 A.6.2.6; EU AI Act Art. 26(5) |
| R17 | Minimised, attributable, deletable shared memory; recorded deletion | A.5.12, A.5.34, A.8.10 | Art. 28 (evidence) | ISO 42001 A.7.2–A.7.4; GDPR Art. 5(1)(c), (e) |
| R19–R21, R30 | Maintenance and change through the pipeline; drift detection and reversion | A.8.9, A.8.32, A.8.31 | Art. 9(4)(e), 11(3) | ISO 42001 A.6.2.6, A.8.4 |
| R22 | Credential lifecycle; two-person custody (Foundry side + custodian) | A.5.17, A.5.19, A.5.20, A.5.3 | Art. 28–30 (ICT third-party register) | ISO 42001 A.10.3 |
| R23 | Backup and restore drills | A.8.13, A.8.14 | Art. 11, 12 | ISO 42001 A.6.2.5 |
| R24–R26 | Monitoring, detection, incident management, break-glass under third-party approval | A.8.15, A.8.16, A.5.24–A.5.27, A.8.2 | Art. 10, 17, 19 | NIS2 Art. 21(2)(b), 23; ISO 42001 A.6.2.8, A.8.4 |
| R27 | Support model (L1 / L2 / L3) | A.5.24 (reporting path), A.6.3 | Art. 13 (learning) | ISO 42001 A.4.5 |
| R28–R29 | Continuous evaluation and token-economy review | A.5.36, A.9.1 | Art. 6(5), 13 | ISO 42001 A.6.2.6, A.9.4; EU AI Act Art. 26(5), 72 |
| R31–R32 | Access review with independent review of the owner's privilege | A.5.18, A.5.35, A.8.2 | Art. 9(4)(c) | NIS2 Art. 21(2)(i); EU AI Act Art. 26(6) |
| R33–R34 | Joiner / mover / leaver; competence attestation; succession | A.5.16, A.5.18, A.6.1, A.6.5, A.6.3 | Art. 5(2), 9(4)(c), 11 | EU AI Act Art. 26(2); ISO 42001 A.4.6 |
| R35 | AI management-system records and deployer obligations | A.5.31, A.5.36 | Art. 28(3) (register of information) | ISO 42001 cl. 7.5, A.2.2–A.2.4, A.5.2; EU AI Act Art. 26, 49(3) where applicable |
| R36 | Personal-data breach path owned by the DPO | A.5.34, A.5.26 | Art. 19 (where ICT-related) | GDPR Art. 33, 34 |
| R37 | Registers and decision records ≥ 1 year | A.5.16, A.5.18, A.5.33 | Art. 28(1), 28(3) | ISO 42001 cl. 7.5; EU AI Act Art. 12, 26(6) |
| R38 | Controlled decommissioning and record export | A.5.10, A.5.33, A.7.14 | Art. 28(8) (exit) | ISO 42001 A.6.2.6 (retirement) |

## 5. Consistency rules

1. **One A per row.** Where a row has two accountability points that
   cannot sit with the same person, the row is split (`↳`) so each part
   still has exactly one A (R11, R15, R36).
2. **The owner is never the only pair of eyes on his own item**: his
   Tier A reports go to any peer, his Tier B reports and template
   proposals to the deputy, his PRs to the deputy as required reviewer,
   his privileged access to the line manager (`TEAM_MODEL.md` §12.2).
3. **Deputy overlay is a role, not a person**: it moves with the
   nomination in `ACCESS_REGISTER.md`; the matrix does not change when
   the deputy changes.
4. **External parties execute, the owner remains accountable** for
   platform outcomes (R2, R3, R5, R22, R33); the exceptions are listed in
   §1 and are the only places accountability leaves the owner.
5. **Changes to this matrix are Tier C** (`PLATFORM_CHANGE`): a PR
   reviewed by the deputy when the owner authors it.
