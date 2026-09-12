# Delivery-Layer Requirements — Traceability (a–j)

This file maps each business requirement to the components that implement
it. The base conversion (35 agents, orchestrator, advisor, verifier,
integrations, governance) is documented in `README.md` / `MAPPING.md` /
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
| **g** | Per-framework advisory systems (every persona framework + gaps) with XLSX/DOCX/PPTX/HTML file generation | Existing advisor agents `iso27001`, `iso42001`, `dora`, `nis2`, `eu-ai-act` + advisor knowledge packs (ISO 27002/27005, NIST CSF 2.0, CIS v8.1, GDPR Art. 28/SCCs, ITIL/COBIT/COSO/TOGAF/PMBOK/ISO 20000 compendium). Gap coverage (ISO 22301, PCI DSS, SOC/SSAE, CSA CCM/CAIQ) is provided by `infosec-assurance-advisor` with web grounding. File generation: orchestrator hands the advisor's content to the `docx`/`pptx`/`xlsx` agents or the render function (`functions/delivery` `/api/render`) — all four formats |
| **h** | TPRM end-to-end knowledge system with file generation | `infosec-assurance-advisor` (combined knowledge store covers all 18 TPRM skills) + `enx-tprm-control-center` router + `tpsrca-assessment-engine`; same file-generation path as (g) |
| **i** | Persona system with read-only Confluence, Jira, SharePoint, OneTrust, security/risk/vuln/IAM/GRC tooling, ENX gateway MCP, and web search that leaks no Euronext data | `infosec-assurance-advisor` registry entry (`integrations/registry.json`) attaches: `confluence-cloud` (**new spec**, read-only), `jira-cloud`, `jira-assets-cmdb`, `sharepoint-graph`, `onetrust`, `defender-graph`, `securityscorecard`, `iaf-api`, `enx-gateway-mcp`, `web-search`. Read-only is **enforced structurally**: `attach_integrations.py` strips every non-GET operation unless the connection is in the agent's `write_connections` (none for the advisor). Egress protection: `governance/DATA_PROTECTION_GUARDRAILS.md` (design: sanitise-then-search, never block reasoning) |
| **j** | Template management: user picks a template, sees all templates, edits, visual before/after review, approval-gated propagation; plus efficiency/model economy | **New agent** `template-manager` (`agents/template-manager_instructions.md`) + template inventory `templates/registry.json` + `workflows/template-update-approval.json` (visual diff page → human approval gate → propagation) + `scripts/update_templates.py` (writes the approved template back to the export source, re-runs convert→verify→create so every dependent agent, vector store and code_interpreter asset updates consistently). Model economy: `governance/MODEL_ROUTING.md` + the `model_tier` map in `integrations/registry.json` (three tiers: `light` for extraction/rendering, `chat` for standard generation, `reasoning` for analysis) |

## Invocation summary

| Trigger | How it starts |
|---|---|
| a, c, d, b (with an already-registered OT assessment) | HTTP trigger of `report-delivery-pipeline` (Teams/Power Apps form, Copilot plugin, or curl) with `pipeline`, `supplierName`, `serviceName`, and input references |
| b, c, d, e, f (user-uploaded PDF) | The user uploads the PDF in the Foundry playground / Copilot chat; the agent produces the verified draft; the pipeline is invoked with the thread/run id to render + store |
| d2 | HTTP trigger with `supplierName` (+ optional `serviceName`); the agent enumerates the TPA Active tree itself |
| g, h, i | Conversational — orchestrator or the specific advisor agent |
| j | Conversational with `template-manager`, which fires the approval workflow |
