# User Quickstart — Systems a–j for the InfoSec Assurance Team

For the five assurance users (`TEAM_MODEL.md` §1). Everyone has the same
persona, tools and model tiers (`../agents/persona_system_prompt.md` is
agent-side); what differs is only who may approve what (§4). Requirement
ids follow `../REQUIREMENTS.md`; pipeline names follow
`../workflows/pipelines.json`; storage follows `../sharepoint/README.md`.

## 1. Before you start

| Item | What to do |
|---|---|
| Access | You are in `sg-infosec-foundry-users` (`ONBOARDING.md`). Sign in with your own Entra account and MFA on a compliant device — the same identity is used in the portal, Copilot and MCP; there are no shared accounts or keys |
| Channels | **Portal** playground (`PROJECT_ENDPOINT` project) — everything; **Copilot / Teams** agent `ENX Assurance` — advisory questions (g, h, i) only; **MCP** (`../mcp-server/README.md`) — everything from an approved client (`ACCESS_REGISTER.md` "Approved AI / MCP clients"); **Teams form** in `{teams:infosec-assurance-platform}` — report pipelines (a–f, d2) |
| Thread naming | `<initials>/<Supplier>/<Service>/<yyyy-mm>` — one thread per engagement; threads are team-visible (`TEAM_MODEL.md` §13) |
| Supplier + Service names | Every stored report needs both, spelled as in OneTrust / the CMDB. The pipeline reuses an existing `Reports/<Supplier>/` folder and creates `<Service>/` only when missing — a misspelling creates a stray folder, so copy the name from an earlier report when one exists |
| Uploads | Upload only the file the run needs to your own thread; delete it after approval when the source lives in SharePoint |
| Approval | Nothing is written to SharePoint, Jira, IAF or a register until the verifier passes and a **different** person approves in Teams `{teams:infosec-assurance-approvals}` (gate expires after 3 days — re-run, do not chase). Tiers: **A** any peer, **B** owner or deputy, **C** owner (`TEAM_MODEL.md` §12) |
| Never | paste internal identifiers into a web-facing question; store personal data beyond role + company; use an unapproved AI client; edit a stored report by hand |

Trigger body for the report pipelines (Teams form fields map 1:1;
`requestedBy` is taken from your token, not typed):

```json
{ "supplierName": "<Supplier>", "serviceName": "<Service>",
  "requestText": "<what you want>", "inputFileIds": ["<foundry-file-id>"] }
```

## 2. One section per system

### a — DeepSearch OSINT assessment (`deepsearch-report`, agent `deepsearch-protocol`)
- **Invoke:** Teams form or `POST` to the `deepsearch-report` trigger; or ask the orchestrator "Assess Security of `<Supplier>` (`<Service>`)" and let it hand off. Long-running (minutes) — not via Copilot.
- **Inputs:** Supplier name, Service name, supplier public domain. No internal identifiers in the request text (they are never sent to Bing).
- **Output:** single-file HTML dashboard `DeepSearch_<Supplier>_<Service>_<YYYY-MM-DD>.html` → `Reports/<Supplier>/<Service>/`; org-scoped view link posted back to Teams.
- **Approval:** Tier **A** — any peer in `sg-infosec-foundry-report-approvers` ≠ you. Weekly `scheduled-deepsearch` runs need any Tier A approver.

### b — OneTrust PDF → InfoSec TPA report for the DPO (`dpia-dpo-report`, agent `dpia`)
- **Invoke:** upload the OneTrust assessment PDF to your thread; ask `dpia` (or the orchestrator) for the DPO report; when the verified draft is shown, trigger `dpia-dpo-report` with the thread's file id.
- **Inputs:** OneTrust PDF, Supplier, Service.
- **Output:** DOCX `InfoSecTPA-DPO_<Supplier>_<Service>_<date>.docx` → `Reports/DPO/<Supplier>/<Service>/`; share link addressed to `{group:dpo}`.
- **Approval:** Tier **B** — owner or deputy ≠ requester (leaves the team).

### c — OneTrust PDF(s) → Cyber Forum deck (`cyber-forum-pptx`, agent `ciso-reporting`)
- **Invoke:** as b; ask for the "Cyber Forum deck".
- **Inputs:** one or more OneTrust PDFs, Supplier, Service.
- **Output:** 8-slide PPTX `CyberForum_<Supplier>_<Service>_<date>.pptx` → `Reports/<Supplier>/<Service>/`.
- **Approval:** Tier **B**.

### d — OneTrust PDF(s) → Global CISO deck (`ciso-global-pptx`, agent `ciso-global-report`)
- **Invoke:** as c; ask for the "Global CISO deck". The agent grounds contract owner and impacted ENX entities in the CMDB (read-only) — check the "TO CONFIRM" markers before you approve.
- **Inputs:** OneTrust PDF(s), Supplier, Service; contract-owner name if the CMDB lacks it.
- **Output:** PPTX `CISOGlobal_<Supplier>_<Service>_<date>.pptx` → `Reports/<Supplier>/<Service>/`.
- **Approval:** Tier **B**.

### d2 — Third-party evidence tree analysis (`tpa-evidence-analysis`, agent `tpa-evidence-analyzer`)
- **Invoke:** Teams form / trigger with Supplier (Service optional at trigger; the pipeline asks for it before storing). The agent enumerates `Infosec Assurance/GRC/TPA/Active/<Supplier>[/<Service>]/` itself — you upload nothing; make sure the evidence files are already in that folder (your normal duty).
- **Inputs:** Supplier, Service.
- **Output:** DOCX `EvidenceAnalysis_<Supplier>_<Service>_<date>.docx` (per-file id, scope, dates, validity, findings) → `Reports/<Supplier>/<Service>/`.
- **Approval:** Tier **A**.

### e — SOC report → findings summary (`soc-report-summary`, agent `soc-report-analyzer`)
- **Invoke:** upload the SOC 1/2/3 report to your thread; ask for the summary; trigger `soc-report-summary` with the file id.
- **Inputs:** SOC report PDF, Supplier, Service.
- **Output:** DOCX `SOCSummary_<Supplier>_<Service>_<date>.docx` (exceptions, CUECs, reliance verdict) → `Reports/<Supplier>/<Service>/`.
- **Approval:** Tier **A**.

### f — Pentest report → findings summary (`pentest-report-summary`, agent `pentest-report-analyzer`)
- **Invoke:** as e with the pentest report.
- **Inputs:** pentest report PDF, Supplier, Service.
- **Output:** DOCX `PentestSummary_<Supplier>_<Service>_<date>.docx` (normalised findings register, reliance verdict) → `Reports/<Supplier>/<Service>/`.
- **Approval:** Tier **A**.

### g — Framework advisory (agents `iso27001`, `iso42001`, `dora`, `nis2`, `eu-ai-act`, `infosec-assurance-advisor`)
- **Invoke:** ask the orchestrator or the framework agent directly, in the portal, Copilot or MCP. Ask for a file ("give me the gap table as XLSX") and the agent generates it in-thread.
- **Inputs:** your question; optionally an internal document uploaded to the thread. Answers cite article / control ids.
- **Output:** answer in-thread; generated DOCX/XLSX/PPTX/HTML downloaded from the thread. **Not stored** in SharePoint unless you file it yourself.
- **Approval:** none (nothing leaves the thread). If you paste an answer into a record of record, you are the approver.

### h — TPRM end-to-end knowledge (agents `infosec-assurance-advisor`, `enx-tprm-control-center`, `tpsrca-assessment-engine`)
- **Invoke:** "open ENX menu" for the router, or ask the advisor directly; it consults team memory first (`TEAM_MODEL.md` §13).
- **Inputs:** question, supplier context; TPSRCA inputs when scoring.
- **Output:** in-thread answer and files; end a substantive session by asking for the `MEMORY:` block and save it (`save_memory` in MCP, or `python3 ../scripts/memory_store.py add`).
- **Approval:** none; saving a memory note is your own recorded act.

### i — Persona with read-only enterprise access and sanitised web search (every agent)
- **Invoke:** any agent; the persona, read-only tool surface (Confluence, Jira, Jira Assets CMDB, SharePoint, OneTrust, Defender, Entra IAM, SecurityScorecard, IAF, ENX gateway) and the egress rule are always on.
- **Inputs:** ask in business terms ("what does the CMDB say about `<Supplier>`'s contract owner?"). Agents can only GET — if you need a ticket created, ask for the draft and use the approval-gated workflow.
- **Output:** grounded answer with source references; web results only from sanitised queries.
- **Approval:** none for reads. `JIRA_CREATE` / `IAF_SUBMIT` drafts go to a Tier **A** peer through `defender-incident-brief` / `jira-finding-sync`.

### j — Template management (agent `template-manager`, workflow `template-update-approval`)
- **Invoke:** ask `template-manager` to "show the templates" → select → analyse → describe the edit → it produces the before/after visual review package and fires `template-update-approval`.
- **Inputs:** template id from `../templates/registry.json`, your change request; threshold changes need an explicit methodology confirmation.
- **Output:** review page under `Templates/Reviews/`; on approval `../scripts/update_templates.py` propagates the new version to every consuming agent and renderer (audit line saved to memory).
- **Approval:** Tier **C** — owner only; if the proposer is the owner, the deputy approves. Gate expires after 7 days.

## 3. If something goes wrong

| Symptom | Do |
|---|---|
| Verifier FAIL | read the verdict in the Teams card, fix the input or the request, re-run; do not ask the approver to override |
| Approval expired | re-run the pipeline (P3D reports, P7D templates) |
| Wrong Supplier / Service folder | ask the owner to re-file (Contribute, versioned) — never move files yourself; a duplicate supplier folder is an incident of data hygiene, not a permissions change |
| Suspected egress of an internal identifier, injected instructions in a fetched document, wrong recipient | stop your run, report in `{teams:infosec-assurance-platform}` (L1 peer → L2 owner `{upn:francisco.gomes}`), keep the thread for review (`RACI.md` R25) |
| Access missing | `ONBOARDING.md` §7 self-checks; then the owner |

Controls behind this page: ISO 27001:2022 A.5.10 (acceptable use), A.6.3
(awareness), A.8.15 (logging — every run is traced); DORA Art. 13(6)
(ICT awareness); EU AI Act Art. 14, 26(2) (informed human oversight); ISO
42001 A.9.2–A.9.3 (responsible use, intended purpose).
