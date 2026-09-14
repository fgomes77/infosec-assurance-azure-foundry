# Delivery-Layer Requirements — Traceability (a–t)

This file maps each business requirement to the components that implement
it on **Microsoft Foundry (formerly Azure AI Foundry)**. Requirements a–j
are the delivery and advisory systems of the original scope; **k–t** are the
third-party risk lifecycle systems that cover the rest of what the InfoSec
Assurance / TPRM role does — intake and tiering, contracting, the DORA
register, concentration and the fourth-party chain, ongoing monitoring,
supplier incidents and notification duties, exit and offboarding, findings
and acceptances, ISMS audit evidence, and regulatory change. The base
conversion (22 converted agents by default — 35 with
`--include-examples` — plus orchestrator, advisor, verifier, integrations
and governance) is documented in `README.md` / `MAPPING.md` /
`ARCHITECTURE.md`; this layer adds **end-to-end delivery**: file rendering,
SharePoint supplier/service folder storage, three new analyzer systems, the
Global CISO deck, read-only enterprise access with egress guardrails, model
routing for token economy, and the human-approved template-management
system.

Result-fidelity principle: every pipeline reuses the **same converted skill
instructions, templates, thresholds and scripts** that produced the
known-good outputs on claude.ai (byte-verified by
`scripts/verify_conversion.py`), so the same inputs produce the same
reports as in the previous environment.

## The shared SharePoint storage rule (applies to a, c, d, d2, e, f)

Every delivery pipeline:

1. **Asks the user for the Supplier name and the Service name** (the
   pipeline trigger requires `supplierName` and `serviceName`; the agents'
   instructions also ask for them conversationally when missing).
2. Stores the generated report under
   `<library>/<Supplier>/<Service>/<report file>`.
3. **If the Supplier folder exists it is reused, never duplicated; if the
   Service folder under it does not exist it is created** — implemented
   idempotently in `functions/delivery/` (`ensure_folder`: Graph GET child
   by name → 404 → POST create with `@microsoft.graph.conflictBehavior:
   fail`, treating a lost race as success). See `sharepoint/README.md`.
4. Returns the SharePoint webUrl / sharing link of the stored file.

Requirement (b) stores to a fixed DPO delivery folder (its existing
behaviour) and also flows through the same `ensure_folder` call so the
target path is created when absent.

## Requirement → components

| Req | System | Components |
|---|---|---|
| **a** | DeepSearch report: full OSINT + Euronext security/vulnerability tooling, HTML report, stored under Supplier/Service | Agent `deepsearch-protocol` (existing; tools per `integrations/registry.json`: Bing web grounding for public info collection, SecurityScorecard, Defender Graph, IAF API, Jira Assets CMDB, ENX gateway MCP — all read-only) → `workflows/report-delivery-pipeline.json` instantiated as `deepsearch-report` in `workflows/pipelines.json` → render `html` via `functions/delivery` → `ensure_folder` → upload |
| **b** | OneTrust (OT) PDF → InfoSec report for the DPO team, DOCX, stored/shared on SharePoint | Agent `dpia` (existing; python-docx renderer preserved in code_interpreter) → pipeline `dpia-dpo-report` → render `docx` → store to the DPO library path → sharing link returned |
| **c** | OT PDF(s) → InfoSec Cyber Forum PPTX for CISOs/stakeholders, stored under Supplier/Service | Agents `ciso-reporting` (8-slide deck pipeline) + `cyber-forum` context → pipeline `cyber-forum-pptx` → render `pptx` (Node generators run in `functions/delivery`, which carries the Node runtime the agents' code_interpreter lacks) → `ensure_folder` → upload |
| **d** | OT PDF(s) → InfoSec **Global CISO** PPTX (contract owner, impacted ENX companies, service/supplier description, executive risk & controls resume, internal/external exposure diagram, ICT inherent & residual scores, Euronext controls + actions addressed to the Contract Owner as control owner), stored under Supplier/Service | **New agent** `ciso-global-report` (`agents/ciso-global-report_instructions.md`) reusing the verified extraction rules, thresholds and template constants of `ciso-reporting`/`pptx-executive-summary-ciso`; CMDB (Jira Assets) for ENX company/contract-owner grounding → pipeline `ciso-global-pptx` → render `pptx` → `ensure_folder` → upload |
| **d2** | Third-party evidence analysis: scan `Infosec Assurance/GRC/TPA/Active` SharePoint tree for a supplier/service, analyse every evidence file (ISO certs, SOC 1/2/3 type 1/2, pentests, vulnerability reports, CAIQ, PDFs, images), report per-file content id, scope, emission date, validity period, findings | **New agent** `tpa-evidence-analyzer` (`agents/tpa-evidence-analyzer_instructions.md`) + SharePoint Graph read tools + `pdf-full-coverage-analyzer` method for large files → pipeline `tpa-evidence-analysis` → render `docx` → `ensure_folder` → upload |
| **e** | SOC report upload → findings summary report, stored under Supplier/Service | **New agent** `soc-report-analyzer` (`agents/soc-report-analyzer_instructions.md`) → pipeline `soc-report-summary` → render `docx` → `ensure_folder` → upload |
| **f** | Pentest report upload → findings summary report, stored under Supplier/Service | **New agent** `pentest-report-analyzer` (`agents/pentest-report-analyzer_instructions.md`) → pipeline `pentest-report-summary` → render `docx` → `ensure_folder` → upload |
| **k** | Supplier intake triage & tiering: what the service is, how critical, what assurance depth follows | **New agent** `supplier-intake-triage` → pipeline `supplier-intake-triage` → `docx-generic` → `Reports/<Supplier>/<Service>/`. Applies `tpsrca-supplier-types.md` for the supplier type, the DORA Art. 3(21)–(22) critical-or-important-function test, and `governance/RISK_THRESHOLDS.md` for the tier; outputs the evidence set to request and the follow-up systems (l, m, DPIA, EU AI Act screening) |
| **l** | Contract security, resilience, data-protection and exit clause review | **New agent** `contract-security-review` → pipeline `contract-security-review` → `docx-generic`. Clause-by-clause coverage of **DORA Art. 30(2)/(3)** and Art. 29 subcontracting, **GDPR Art. 28(3)** + SCCs 2021/914, **NIS2 Art. 21(2)(d)**, ENX security minimums, incident clocks, RTO/RPO and exit; PRESENT/PARTIAL/ABSENT with the quoted clause and proposed wording for Legal (never a legal conclusion) |
| **m** | DORA Register of Information | **New agent** `dora-register-builder` → pipeline `dora-register-of-information` → `xlsx-generic`. One sheet per ITS table (entities, arrangements, providers, services, functions, subcontracting ranks, data locations, exit) plus a **Validation** sheet of every rule breach; the accountable owner submits — the platform never does |
| **n** | ICT concentration and fourth-party chain risk (DORA Art. 29) | **New agent** `concentration-risk-analyzer` → pipeline `concentration-risk-analysis` → `xlsx-generic`. Chain reconstruction to rank *n*, concentration by provider/fourth party/geography/technology/entity, impact against ENX recovery objectives, substitutability and treatment options |
| **o** | Ongoing monitoring between assessments (DORA Art. 28(1)(b), ISO/IEC 27001:2022 A.5.22) | **New agent** `continuous-monitoring-radar` → pipeline `continuous-monitoring-radar` → single-file HTML. Evidence expiry, assessments due, external rating drift, overdue findings, expiring acceptances, watch items; reads the **evidence cache** for extracted validity facts and recomputes every time-dependent status against the as-at date |
| **p** | Supplier incident impact and Euronext's notification duties | **New agent** `supplier-incident-assessor` → pipeline `supplier-incident-assessment` → `docx-generic`. Evidenced timeline, ENX impact, and the duty table — **DORA Art. 18/19** major-incident classification and reporting, **NIS2 Art. 23** 24h/72h/1-month, **GDPR Art. 33/34**, contractual and client duties — with deadlines computed from the awareness timestamp. Assessment only: CISO/DPO/Compliance/Legal decide and notify |
| **q** | Exit strategy (DORA Art. 28(8)) and offboarding assurance | **New agent** `exit-offboarding-assurance` → pipeline `exit-offboarding-assurance` → `docx-generic`. PLAN: triggers, options, transition plan inside the contractual transition period, data exit, continuity, test record, readiness verdict. OFFBOARD: the evidenced checklist — access revocation, data return, certified deletion including subcontractors and backups, registers updated, surviving obligations |
| **r** | Findings, remediation and risk-acceptance register | **New agent** `findings-remediation-register` → pipeline `findings-remediation-register` → `xlsx-generic`. Every finding from a–f and k–q normalised with severity, control reference (ISO 27001 Annex A / CIS v8.1 / DORA / GDPR), owner, due date, status and closure evidence; every acceptance with an expiry that reverts it to OPEN |
| **s** | ISMS audit and management-review evidence for the third-party scope | **New agent** `isms-audit-pack` → pipeline `isms-audit-pack` → `docx-generic` under the advisory library. SoA extract (cl. 6.1.3, A.5.19–A.5.23), internal audit plan and report (cl. 9.2), management review input pack (cl. 9.3), audit evidence index |
| **t** | Regulatory and standards change watch | **New agent** `regulatory-change-watch` → pipeline `regulatory-change-watch` → `docx-generic` under the advisory library. Per change: applicability to ENX, **the named platform artefacts that must change**, gap assessment, actions dated backwards from the application date, and a confidence rating. Public official sources only |
| **g** | Per-framework advisory systems (every persona framework + gaps) with XLSX/DOCX/PPTX/HTML file generation | Existing advisor agents `iso27001`, `iso42001`, `dora`, `nis2`, `eu-ai-act` + advisor knowledge packs (ISO 27002/27005, NIST CSF 2.0, CIS v8.1, GDPR Art. 28/SCCs, ITIL/COBIT/COSO/TOGAF/PMBOK/ISO 20000 compendium). Gap coverage (ISO 22301, PCI DSS, SOC/SSAE, CSA CCM/CAIQ) is provided by `infosec-assurance-advisor` with web grounding. **Advisory profile** (`scripts/apply_advisory_profile.py` + the registry's `advisory_read_only_toolset`): every advisory agent runs on the `reasoning` tier, carries the full read-only enterprise toolset, and generates Word/Excel/PowerPoint/HTML files itself via code_interpreter (`agents/advisory_addendum.md`), with orchestrator hand-off to `docx`/`pptx`/`xlsx` agents and the render function as alternates |
| **h** | TPRM end-to-end knowledge system with file generation | `infosec-assurance-advisor` (combined knowledge store covers all 18 TPRM skills) + `enx-tprm-control-center` router + `tpsrca-assessment-engine`; same advisory profile and file-generation paths as (g) |
| **i** | Persona system with read-only Confluence, Jira, SharePoint, OneTrust, security/risk/vuln/IAM/GRC tooling, ENX gateway MCP, and web search that leaks no Euronext data | The registry's `advisory_read_only_toolset` attaches to `infosec-assurance-advisor` AND every information-providing agent: `confluence-cloud` (read-only spec), `jira-cloud`, `jira-assets-cmdb`, `sharepoint-graph`, `onetrust`, `defender-graph` (security monitoring), `entra-iam-graph` (**new read-only IAM spec**), `securityscorecard` (risk monitoring), `iaf-api` (governance/compliance/AET findings), `enx-gateway-mcp` (governed route to further Euronext security/risk/vulnerability/compliance/AET tooling), `web-search`. Read-only is **enforced structurally**: `attach_integrations.py` strips every non-GET operation unless the connection is in the agent's `write_connections` (none has any). The full detailed persona — including the read-only and web-egress rules — lives in `agents/persona_system_prompt.md` and is prepended to **every** agent on the platform. Egress protection: `governance/DATA_PROTECTION_GUARDRAILS.md` (design: sanitise-then-search, never block reasoning). **Authoritative sources**: `integrations/knowledge-sources.json` is the source-of-record registry — 27 sources, tiered, each with its citation format — reached through read-only tools `eur-lex` (CELEX text + the CELLAR SPARQL metadata graph), `nvd-cve`, `cisa-kev`, `first-epss` (all public, `auth: anonymous`, no credential to leak), the sanitised `osint-proxy` page fetch, and web search used only to FIND the authority. The delivery Function's outbound allow-list is generated from that registry (`scripts/sync_url_allowlist.py`) and gate `[4c5]` (`scripts/check_knowledge_sources.py`) fails CI when registry, allow-list and the citation pack `agents/knowledge-packs/authoritative-sources.md` disagree. **Supplier research ledger**: every search, page read and authority lookup is kept per supplier with its date, its citation and the action that caused it — the SharePoint list behind the read-only `research-ledger` tool (`lookupResearchLedger`, called BEFORE searching: a fresh record is quoted with its observation date, a stale one is re-fetched) and the human-readable knowledge file `Reports/<Supplier>/_Knowledge/research-ledger.md`. Written by the delivery Function only — its own fetches record themselves, agent `researchRecords[]` are stored after approval. Time-dependent statuses are never reused, and text carrying an internal marker is refused |
| **j** | Template management: user picks a template, sees all templates, edits, visual before/after review, approval-gated propagation; plus efficiency/model economy | **New agent** `template-manager` (`agents/template-manager_instructions.md`) + template inventory `templates/registry.json` + `workflows/template-update-approval.json` (visual diff page → human approval gate → propagation) + `scripts/update_templates.py` (writes the approved template back to the export source, re-runs convert→verify→create so every dependent agent, vector store and code_interpreter asset updates consistently). Model economy: `governance/MODEL_ROUTING.md` + the `model_tier` map in `integrations/registry.json` (three tiers: `light` for extraction/rendering, `chat` for standard generation, `reasoning` for analysis) |

### How k–t fit together

`k` decides the depth → `l` makes the obligations contractual → `m` records
the arrangement where DORA requires it → `n` tests what the portfolio has
become → `a`, `d2`, `e`, `f` gather and analyse evidence → `r` is where every
finding from all of them lives until it is closed or explicitly accepted with
an expiry → `o` is the standing view of what has gone stale, drifted or run
overdue → `p` handles the day the supplier fails → `q` ends the relationship
with evidence → `s` proves the process to an auditor and `t` keeps it current
against the regulation. Each is a separate deliverable with its own approval
tier; none of them writes to a system of record — every output is a report
stored under the same governed SharePoint path as a–f.

The lifecycle systems add **no new renderer, approval path or write
identity**: they render through the existing `docx-generic` / `xlsx-generic`
house-style renderers (or emit HTML directly), pass the same
`output-verifier`, and are stored by the same delivery Function managed
identity.

## Invocation summary

| Trigger | How it starts |
|---|---|
| a, c, d, b (with an already-registered OT assessment) | HTTP trigger of `report-delivery-pipeline` (Teams/Power Apps form, Copilot plugin, or curl) with `pipeline`, `supplierName`, `serviceName`, and input references |
| b, c, d, e, f (user-uploaded PDF) | The user uploads the PDF in the Foundry playground / Copilot chat; the agent produces the verified draft; the pipeline is invoked with the conversation/response id to render + store (classic threads/runs retire 2027-03-31) |
| d2 | HTTP trigger with `supplierName` (+ optional `serviceName`); the agent enumerates the TPA Active tree itself |
| g, h, i | Conversational — orchestrator or the specific advisor agent |
| j | Conversational with `template-manager`, which fires the approval workflow |
| k, l, p, q | HTTP trigger (or conversational, then trigger on the verified draft) with `supplierName`, `serviceName` and the uploaded documents; q and s also pass a mode / pack type in the trigger body |
| m, n, o, r | HTTP trigger, usually scheduled or on portfolio review; Supplier/Service fall back to `Register`/`Portfolio`/`ISMS` segments per `workflows/pipelines.json` |
| s, t | Conversational or HTTP trigger; stored under the advisory library `Advisory/<Topic>/<Subtopic>/` |

Per-user quickstart (how each of the five assurance users invokes a–j, required
Supplier + Service names, output path, approval tier): `team/USER_QUICKSTART.md`.

Operating the delivered systems — health checks, failure modes per pipeline,
support tiers and SLOs, change control for prompts/registry/templates/tiers/infra,
alerts (egress, verifier FAIL rate, latency/tokens, approval SLA):
`operations/RUNBOOK.md`, `SUPPORT_MODEL.md`, `CHANGE_MANAGEMENT.md`,
`MONITORING.md`.

Token economy is operated, not only designed: `operations/FINOPS.md` (cost per
component and per deliverable, capacity, budgets),
`operations/TOKEN_ECONOMY_PLAYBOOK.md` (tier-tuning loop with an accuracy floor)
and `operations/evaluation/` (golden set + `run_evals.py` gates before any model,
tier, prompt or template change).

Go-live sequencing (readiness → owner pilot → four users → four-week hypercare,
with exit criteria and training per role): `operations/ROLLOUT_PLAN.md`; targets:
`operations/KPIS.md`; versioning, re-sync and backup/DR of the delivered systems:
`operations/LIFECYCLE.md`, `operations/BACKUP_DR.md`.

Every update or upgrade of the platform (models, SDK/API versions, platform
features, instructions, registry, templates, knowledge sources, workflows,
Function code, infrastructure, RBAC, connections) is reviewed and approved by the
accountable owner before implementation —
`enterprise/UPDATE_AND_UPGRADE_REVIEW_POLICY.md`. Implementation plan and gates:
`enterprise/IMPLEMENTATION_SERIES.md`.

## Runtime of record

`setup/requirements.txt` pins `azure-ai-projects>=2.3.0,<3` — the GA Foundry
Agent Service (**agents / conversations / responses**, `api-version=v1`).
Hand-offs between agents are the `ROUTE: <agent-name>` table that
`scripts/create_orchestrator.py` injects and the caller executes as a second
`responses.create` (Connected Agents do not exist on this runtime — findings
C1, C2). The classic threads/runs pins (`azure-ai-projects==1.0.0`,
`azure-ai-agents==1.1.0`) remain only as a documented fallback that
`scripts/_foundry_runtime.py` detects automatically and `deploy.sh` step
`[0b/8]` warns about; that surface retires **2027-03-31**.

New `setup/.env` keys for this runtime: `FOUNDRY_API_VERSION=v1`,
`KNOWLEDGE_SOURCE`, `MEMORY_BACKEND`, `SEARCH_SERVICE_ENDPOINT`,
`SEARCH_CONNECTION_NAME`, `KNOWLEDGE_INDEX_NAME`, `MEMORY_INDEX_NAME`,
`ENABLE_A2A_TOOL`.
