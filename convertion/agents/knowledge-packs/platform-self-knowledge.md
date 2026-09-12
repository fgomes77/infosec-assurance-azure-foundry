# Platform self-knowledge (knowledge pack)

*Authored 2026-09-12. This platform is **Microsoft Foundry (formerly
Azure AI Foundry)** and runs the Agents v2 runtime (conversations and
responses; the classic threads/runs API retires 2027-03-31). It replaces
the claude.ai `product-self-knowledge` skill: Anthropic product content
is EXCLUDED because this deployment does not use Anthropic models — not
because they are unavailable. Correction of an earlier statement in this
kit: **Claude models ARE offered on Microsoft Foundry**; they are
excluded here by the EU data-residency rule (no EU data zone for them at
the time of writing), a decision to be re-checked against the model
region-availability and retirement pages each quarter. The transferable
rule is kept — never answer questions about THIS platform's capabilities
from memory; retrieve this file. The
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
5. Model tiers: `light` for document agents and routing; `chat` for
   template-driven generation; `reasoning` for analysis, advisors and the
   orchestrator. The pinned model per tier and its version are in
   `governance/MODEL_ROUTING.md` — quote that file, never a model name
   from memory.
6. Tool compatibility is a property of the MODEL, not of the tier name:
   OpenAPI, MCP, AI Search / `file_search`, SharePoint grounding and Web
   Search tools work on the `light` and `chat` tiers and on `reasoning`
   only when that tier is pinned to a tool-capable reasoning model
   (reasoning models of the o3-mini class support none of those tools).
   Every agent that carries the read-only enterprise toolset must
   therefore sit on a tool-capable model; the tool-compatibility matrix
   in `governance/MODEL_ROUTING.md` is authoritative.
7. SharePoint has two read routes: the native SharePoint grounding tool
   (preview, on-behalf-of the signed-in user, permission-trimmed, rate-
   and result-capped) for interactive advisory reads only, and the
   Microsoft Graph OpenAPI tool (application identity, read-only) plus
   the delivery Function for every pipeline, evidence scan and write.
8. Specialists are reached by A2A (agent-to-agent) hand-off or by an
   Agent Framework orchestration step. "Connected agents" do not exist on
   this runtime.
9. Accountable owner of the platform: Francisco Gustavo Gomes (platform
   admin, approver of template and platform changes); four assurance
   users approve reports as lead/peer.

## Agent inventory (see build/manifest.json for the deployed set)

| Agent | Purpose | Tier | Pipeline |
|---|---|---|---|
| orchestrator | single entry point, A2A routing, verifier loop | reasoning | — |
| infosec-assurance-advisor | cross-framework advisory, combined knowledge + memory; IS the advisory system for ISO 27005, NIST CSF, CIS, 27002 attributes, ITIL/COBIT/COSO/TOGAF/PMBOK/ISO 20000/agile/Lean, GDPR Art. 28/SCCs/27701, cloud/ICT assurance | reasoning | advisory-file-delivery |
| output-verifier | rule-based verdict on every draft deliverable | reasoning | all |
| enx-tprm-control-center | menu router (options 1–13), A2A hand-off to the workers | chat | — |
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
