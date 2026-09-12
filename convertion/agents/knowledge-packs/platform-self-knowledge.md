# Platform self-knowledge (knowledge pack)

*Authored 2026-09-12. Replaces the claude.ai `product-self-knowledge`
skill: Anthropic product content is EXCLUDED (no Claude models on this
platform); the transferable rule is kept — never answer questions about
THIS platform's capabilities from memory; retrieve this file. The
deploy step `scripts/build_self_knowledge.py` regenerates the tables
below from `build/manifest.json`, `integrations/registry.json`,
`workflows/pipelines.json`, `templates/registry.json` and
`governance/HUMAN_APPROVAL.md`; this hand-authored version is the
fallback until that script runs.*

## Rules the platform enforces

1. Enterprise systems are READ-ONLY for every agent (Confluence, Jira,
   Jira Assets CMDB, SharePoint, OneTrust, Defender, Entra ID,
   SecurityScorecard, IAF API, ENX gateway MCP). Non-GET operations are
   stripped from every OpenAPI tool.
2. Every write of record goes: producing agent → `output-verifier` →
   human approval (Teams/Logic App) → pipeline performs the write.
3. Deliverables are stored by the delivery pipelines under
   `Reports/<Supplier>/<Service>/` (DPO: `Reports/DPO/<Supplier>/<Service>/`;
   advisory: `Advisory/<Topic>/<Subtopic>/`). Agents cannot upload.
4. Web search: public terms only; no Euronext data leaves the tenant.
   All resources are in the EU region.
5. Model tiers: `light` (gpt-4o-mini class) for document agents and
   routing; `chat` (gpt-4o class) for template-driven generation;
   `reasoning` (o3-mini class) for analysis, advisors and the orchestrator.
6. Accountable owner of the platform: Francisco Gustavo Gomes (platform
   admin, approver of template and platform changes); four assurance
   users approve reports as lead/peer.

## Agent inventory (see build/manifest.json for the deployed set)

| Agent | Purpose | Tier | Pipeline |
|---|---|---|---|
| orchestrator | single entry point, routing, verifier loop | reasoning | — |
| infosec-assurance-advisor | cross-framework advisory, combined knowledge + memory; IS the advisory system for ISO 27005, NIST CSF, CIS, 27002 attributes, ITIL/COBIT/COSO/TOGAF/PMBOK/ISO 20000/agile/Lean, GDPR Art. 28/SCCs/27701, cloud/ICT assurance | reasoning | advisory-file-delivery |
| output-verifier | rule-based verdict on every draft deliverable | reasoning | all |
| enx-tprm-control-center | menu router (options 1–13) | chat | — |
| deepsearch-protocol / ai-deepsearch-osint-gathering-report | supplier OSINT dashboards | reasoning | deepsearch-report / ai-deepsearch-report |
| dpia | OneTrust PDF → InfoSec TPA DPO report | chat | dpia-dpo-report |
| ciso-reporting / ciso-executive-summary / tprm-slide-generator / pptx-executive-summary-ciso | CISO deliverables from OT assessments | chat | cyber-forum-pptx / ciso-exec-summary |
| ciso-global-report | 9-slide Global CISO PPTX | reasoning | ciso-global-pptx |
| tpa-evidence-analyzer / soc-report-analyzer / pentest-report-analyzer | evidence, SOC, pentest analysis DOCX | reasoning | tpa-evidence-analysis / soc-report-summary / pentest-report-summary |
| cyber-forum | security Q&A and threat-intel briefs | reasoning | cyber-forum-brief |
| onetrust-form-b | Form B answers with sign-off gate | chat | (xlsx round-trip via approval) |
| tpsrca-assessment-engine | deterministic TPRM scoring | reasoning | via ciso-global-pptx |
| dora, nis2, eu-ai-act, iso27001, iso42001 | framework advisors | reasoning | advisory-file-delivery |
| docx, pdf, pptx, xlsx | document transformation | light | generic-docx/pptx-deliverable, xlsx-generic |
| pdf-full-coverage-analyzer | exhaustive chunked PDF review | reasoning | — |
| template-manager | controlled template changes | chat | template-update-approval |
| whisperx-transcribe-diarize | transcript summaries (knowledge only) | chat | transcript-summary |
| learn, doc-coauthoring (adapted examples) | tutoring; structured co-authoring | chat | advisory-file-delivery |
| enterprise-explorer | read-only reconnaissance across enterprise sources | light | — |
| research-coordinator / research-worker / research-writer | multi-source research briefs | reasoning / chat / chat | research-brief |

## How to answer capability questions

- "Can you store this under the supplier folder?" → yes via the pipeline
  after verifier + approval; name the pipeline id.
- "Is Jira read-only?" → yes; a finding becomes a DRAFT ticket for
  approval (`jira-finding-sync` workflow performs the write).
- "Which agent does X?" → retrieve the table above; if absent, say the
  capability is not deployed rather than improvising.
