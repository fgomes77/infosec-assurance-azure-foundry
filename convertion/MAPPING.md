# Per-Skill Conversion Map — Claude Export → Azure AI Foundry Agents

How each of the 35 exported skills converts. **Tools:** FS = file_search
(vector store with the skill's references/), CI = code_interpreter (with the
skill's scripts/ and assets/). The persona preamble is prepended to every
agent. Generated definitions land in `build/agents/<name>/` when you run
`scripts/convert_skills.py`.

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
| `enx-tprm-control-center` | enx-tprm-control-center | connected agents | Router → dpia, ciso-reporting, cyber-forum, onetrust-form-b, deepsearch-protocol |
| `dora` | dora | FS | 4 regenerated references as knowledge; Art. 30 correction included |
| `nis2` | nis2 | FS | 2 regenerated references |
| `eu-ai-act` | eu-ai-act | FS | 3 regenerated references |
| `iso27001` | iso27001 | FS | Annex A catalogues + 2013→2022 mapping as knowledge |
| `iso42001` | iso42001 | FS | Clauses, Annex A, AI risk methodology as knowledge |
| `pdf-full-coverage-analyzer` | pdf-full-coverage-analyzer | FS + CI | Chunked-coverage method; triage/cross-check scripts in CI |
| `tprm-slide-generator` | tprm-slide-generator | FS + CI | Regenerated schema/layout refs; JS slide generator flagged external-runtime |
| `pptx-executive-summary-ciso` | pptx-executive-summary-ciso | FS + CI | Byte-identical twin of the above — deploy one or both |
| `tpsrca-assessment-engine` | tpsrca-assessment-engine | FS + CI | 12-agent methodology encoded in instructions; optionally split into connected agents later |
| `whisperx-transcribe-diarize` | whisperx-transcribe-diarize | FS (knowledge only) | Local-hardware skill; use AI Foundry Speech batch transcription + diarization instead |

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
| Routines / scheduled triggers | Azure Logic Apps or Functions timer triggers invoking the agent API |
| Artifacts (published HTML) | Azure Static Web Apps / Blob static hosting for generated HTML dashboards |
| `verify_sync.py` | Not applicable — in Foundry, re-running convert+create IS the sync |

## Exclusions

The forensic-persona skill excluded from the export for data-protection
reasons is likewise absent here.
