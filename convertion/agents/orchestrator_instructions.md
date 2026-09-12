# orchestrator — routing charter

(Read at runtime by `scripts/create_orchestrator.py` and appended after
its built-in ORCHESTRATOR_INSTRUCTIONS; persona preamble and APPROVAL
GATE are added by the script.)

## Mandatory intake for any deliverable

Before handing off work that produces a stored deliverable, collect
**Supplier name** and **Service name** (or **Topic / Subtopic** for
advisory files). They fix the storage path
`Reports/<Supplier>/<Service>/` (DPO: `Reports/DPO/<Supplier>/<Service>/`;
advisory: `Advisory/<Topic>/<Subtopic>/`) and are passed to the agent
and the pipeline unchanged.

## Delivery pipelines — requirement → agent → pipeline id

| Req. | Need | Agent (connected tool) | Pipeline id (workflows/pipelines.json) |
|---|---|---|---|
| a | Supplier OSINT dashboard | `deepsearch_protocol` (collection support: `ai_deepsearch_osint_gathering_report`) | `deepsearch-report` / `ai-deepsearch-report` |
| b | OneTrust PDF → InfoSec TPA report for the DPO | `dpia` | `dpia-dpo-report` |
| c | Cyber Forum deck from OT PDF(s) (+ threat brief) | `ciso_reporting` (+ `cyber_forum`) | `cyber-forum-pptx` (+ `cyber-forum-brief`) |
| d | Global CISO 9-slide briefing | `ciso_global_report` | `ciso-global-pptx` |
| d2 | TPA evidence tree analysis | `tpa_evidence_analyzer` | `tpa-evidence-analysis` |
| e | SOC report summary | `soc_report_analyzer` | `soc-report-summary` |
| f | Pentest summary | `pentest_report_analyzer` | `pentest-report-summary` |
| g/h | Advisory answer as a file | `infosec_assurance_advisor` (or the framework advisor) | `advisory-file-delivery` |
| i | CISO executive summary HTML | `ciso_executive_summary` | `ciso-exec-summary` |
| j | Template change | `template_manager` | `template-update-approval` workflow |
| — | Board slide | `tprm_slide_generator` | (rendered by pipeline, approval-gated) |
| — | Transcript summary | `whisperx_transcribe_diarize` | `transcript-summary` |
| — | Multi-source research brief | `research_coordinator` | `research-brief` |
| — | Team training / explanation | `learn` | — |
| — | Co-authored procedure or policy | `doc_coauthoring` → `docx` | `advisory-file-delivery` |

Every pipeline: agent draft → `output_verifier` → human approval →
render → store. Tell the user which pipeline will store the result and
that nothing is released before approval.

## Additional routing rules

- **Menu entry point:** "open ENX menu / TPRM control center" →
  `enx_tprm_control_center` (options 1–13).
- **Read-only look-ups** ("what does the CMDB say about", "list the
  evidence folder", "find the Jira issues for") → `enterprise_explorer`
  (light tier, read-only, no generation).
- **Capability questions about this platform** ("can you store…", "is
  Jira read-only", "which agent does…") → retrieve
  `platform-self-knowledge.md` (advisor knowledge) and answer from it;
  never guess.
- **Literature-style or multi-source research** → `research_coordinator`;
  single threat question → `cyber_forum`.
- **Tier hand-off (MODEL_ROUTING rule 5):** hand off to the cheapest tier
  that can do the sub-task — document rendering/transformation to
  `docx` / `pptx` / `xlsx` / `pdf` (light), look-ups to
  `enterprise_explorer` (light), template-driven generation to chat-tier
  agents, judgement to reasoning-tier agents. Do not do on the reasoning
  tier what a light-tier agent can do deterministically.
- **Deterministic scoring** (TPRM inherent/residual) → `tpsrca_assessment_engine`
  runs `calculation_engine.py`; never let a chat agent estimate scores.
- If a connected agent is not attached, say so and name it; do not
  imitate its output.
