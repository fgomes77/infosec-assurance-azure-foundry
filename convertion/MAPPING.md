# Per-Skill Conversion Map — Claude Export → Microsoft Foundry Agents

How each of the 35 exported skills converts to an agent on **Microsoft
Foundry (formerly Azure AI Foundry)**. **Tools:** FS = file_search (the
agent's single vector store, holding the skill's references/ — the service
allows one vector store per agent, so shared knowledge and durable memory
live in Azure AI Search / a Foundry IQ knowledge base instead,
`enterprise/MEMORY_AND_LEARNING.md` §2), CI = code_interpreter (with the
skill's scripts/ and assets/). The persona preamble is prepended to every
agent and the environment overlay appended after the body
(`agents/README.md`). Generated definitions land in `build/agents/<name>/`
when you run `scripts/convert_skills.py`.

**Default build = 22 agents** (the 18 custom GRC/TPRM + 4 document skills).
The 13 Anthropic example skills below convert only with
`--include-examples`, which takes the build to the full 35. Eight further
agents exist only in Foundry and are converted from no skill: the
orchestrator, the advisor, the output-verifier and the five delivery-layer
agents (last section); `agents/README.md` also charters `enterprise-explorer`
and the three research agents.

Platform currency: naming, runtime vocabulary (conversations/responses,
not threads/runs), hand-off mechanics and tool availability change with the
service — the binding review rule and the quarterly currency check are
`enterprise/UPDATE_AND_UPGRADE_REVIEW_POLICY.md`.

## Custom GRC / TPRM skills (18) — one dedicated agent each

| Agent | Source skill | Tools | Conversion notes |
|---|---|---|---|
| `deepsearch-protocol` | deepsearch-protocol | FS | OSINT assessment protocol; web research requires grounding (Bing) or your own search tool — flag in manifest |
| `ai-deepsearch-osint` | ai-deepsearch-osint-gathering-report | FS | Same family as above |
| `ciso-executive-summary` | ciso-executive-summary | FS + CI | references/ specs + regenerated template.html; Python renderers run in CI |
| `ciso-reporting` | ciso-reporting | FS + CI | Deterministic pipeline: orchestrator script runs in CI; JS pptx generator flagged external-runtime |
| `cyber-forum` | cyber-forum | FS | Q&A/threat-intel; grounding recommended for live CVE data |
| `dpia` | dpia | FS + CI | OneTrust PDF → DOCX report; python-docx runs in CI |
| `onetrust-form-b` | onetrust-form-b | FS + CI | Human sign-off gate preserved verbatim in instructions — the agent must not finalise answers |
| `enx-tprm-control-center` | enx-tprm-control-center | A2A hand-offs | Router → dpia, ciso-reporting, cyber-forum, onetrust-form-b, deepsearch-protocol. Connected Agents do not exist on the current Agent Service: the menu hands off through the A2A tool to the published worker agents (Agent Framework orchestration is the production path — `enterprise/ENTERPRISE_BLUEPRINT.md` ORC-1) |
| `dora` | dora | FS | 4 regenerated references as knowledge; Art. 30 correction included |
| `nis2` | nis2 | FS | 2 regenerated references |
| `eu-ai-act` | eu-ai-act | FS | 3 regenerated references |
| `iso27001` | iso27001 | FS | Annex A catalogues + 2013→2022 mapping as knowledge |
| `iso42001` | iso42001 | FS | Clauses, Annex A, AI risk methodology as knowledge |
| `pdf-full-coverage-analyzer` | pdf-full-coverage-analyzer | FS + CI | Chunked-coverage method; triage/cross-check scripts in CI |
| `tprm-slide-generator` | tprm-slide-generator | FS + CI | Regenerated schema/layout refs; JS slide generator flagged external-runtime |
| `pptx-executive-summary-ciso` | pptx-executive-summary-ciso | FS + CI | Byte-identical twin of the above — deploy one or both |
| `tpsrca-assessment-engine` | tpsrca-assessment-engine | FS + CI | 12-agent methodology encoded in instructions; optionally split into separate published agents with A2A hand-offs later |
| `whisperx-transcribe-diarize` | whisperx-transcribe-diarize | FS (knowledge only) | Local-hardware skill; use Foundry Speech batch transcription + diarization instead (`workflows/speech-transcription.json`) |

## Anthropic document skills (4) — one agent each, CI-centric

| Agent | Source skill | Tools | Notes |
|---|---|---|---|
| `docx` | docx | FS + CI | docx-js/python tooling runs in CI |
| `pdf` | pdf | FS + CI | pypdf et al. in CI |
| `pptx` | pptx | FS + CI | html2pptx flow; JS parts flagged |
| `xlsx` | xlsx | FS + CI | openpyxl flow |

## Anthropic example skills (13) — optional agents

`algorithmic-art`, `brand-guidelines`, `canvas-design`, `doc-coauthoring`,
`import-memory`, `internal-comms`, `learn`, `mcp-builder`, `morning`,
`skill-creator`, `slack-gif-creator`, `theme-factory`,
`web-artifacts-builder` — converted the same way (instructions + FS/CI as
present). Several are Claude-platform-specific (artifacts, Slack GIFs,
morning brief) and are marked `"platform_specific": true` in the manifest;
deploy with `--include-examples` only if you want them.

## Non-skill components

| Export component | Foundry equivalent |
|---|---|
| `PERSONA.md` | `agents/persona_system_prompt.md` — prepended to every agent's instructions by the converter |
| `CAPABILITIES.md` connectors (Gmail, Drive, GitHub, Adobe, …) | No in-agent equivalent; integrate per-connector via Logic Apps connectors or agent OpenAPI tools |
| `platform-skills/` (Anthropic built-ins beyond the enabled set) | Not deployed by default; convert on demand the same way |
| Routines / scheduled triggers | Azure Logic Apps (16 definitions in `workflows/` + `pipelines.json`) or Functions timer triggers calling the agent API (`conversations` / `responses`) |
| Artifacts (published HTML) | Azure Static Web Apps / Blob static hosting for generated HTML dashboards |
| `verify_sync.py` | Not applicable — in Foundry, re-running convert+create IS the sync (`deploy.sh`), and each run produces a new immutable agent version pipelines pin to |

## Delivery-layer agents (5) — new, not converted from a skill

Created by `scripts/create_delivery_agents.py`; instructions in
`agents/<name>_instructions.md`; tools/tiers in
`integrations/registry.json`; requirement mapping in `REQUIREMENTS.md`.

| Agent | Requirement | Tools | Knowledge reused (fidelity anchor) |
|---|---|---|---|
| `ciso-global-report` | d | OneTrust, Jira Assets CMDB, SharePoint (read) | ciso-reporting + pptx-executive-summary-ciso + tpsrca knowledge; output schema `templates/ciso_global_deck.schema.json` |
| `tpa-evidence-analyzer` | d2 | SharePoint Graph (read) | pdf-full-coverage-analyzer method |
| `soc-report-analyzer` | e | — (file upload) | pdf-full-coverage-analyzer method |
| `pentest-report-analyzer` | f | — (file upload) | pdf-full-coverage-analyzer method |
| `template-manager` | j | SharePoint (read) + code_interpreter over template assets | `templates/registry.json` inventory |

## Exclusions

The forensic-persona skill excluded from the export for data-protection
reasons is likewise absent here.
