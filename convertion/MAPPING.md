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
when you run `scripts/convert_skills.py`. Knowledge files are flattened for the
vector store; scripts/ and assets/ are packaged as
`build/agents/<name>/code/<name>-scripts.zip` with the original layout kept
alongside in `build/agents/<name>/code-tree/`. Shared SSOT copies appear as
`shared__*` and environment knowledge packs as `pack__*`.

**Default build = 22 agents** (the 18 custom GRC/TPRM + 4 document skills).
The 13 Anthropic example skills below convert only with
`--include-examples`, which takes the build to the full 35. Eight further
agents exist only in Foundry and are converted from no skill: the
orchestrator, the advisor, the output-verifier and the five delivery-layer
agents (last section); `agents/README.md` also charters `enterprise-explorer`
and the three research agents.

**Machine form of this document:** `templates/skill-decisions.json` carries
one enforced decision row per skill — all 35 exported plus the 41 Anthropic
built-ins under `claude-account-export/platform-skills/` (76 enforced
entries; the 17 harness skills are recorded but not enforced). Each row has
`decision` (AGENT · ALIAS · KNOWLEDGE-PACK · SUPERSEDED · EXCLUDED), the
agent and tier it became, `deployed`, `requires_flag`, `target`, the
rationale in ENX terms, the owner and the date. This file and
`governance/PLATFORM_SKILLS_DECISION.md` stay the prose record; the JSON is
what `scripts/verify_conversion.py` enforces (checks C1–C10 in its
`enforcement` block), so a skill can never be silently dropped or silently
deployed. Changing a decision is a Tier-B change and needs the approval
recorded in `governance/HUMAN_APPROVAL.md` — never a hand edit.

Platform currency: naming, runtime vocabulary (conversations/responses,
not threads/runs), hand-off mechanics and tool availability change with the
service — the binding review rule and the quarterly currency check are
`enterprise/UPDATE_AND_UPGRADE_REVIEW_POLICY.md`. The models the tiers run
on are a currency item too: Claude models **are** offered on Foundry and are
excluded here by the EU residency rule, not by availability
(`governance/CLAUDE_ON_FOUNDRY.md`).

## Custom GRC / TPRM skills (18) — one dedicated agent each

| Agent | Source skill | Tools | Conversion notes |
|---|---|---|---|
| `deepsearch-protocol` | deepsearch-protocol | FS | OSINT assessment protocol; web research requires grounding (Bing) or your own search tool — flag in manifest. Bing grounding is a **global** service outside the Azure compliance boundary (the DPA does not apply): sanitised public queries only, accepted residual risk — `governance/DATA_PROTECTION_GUARDRAILS.md` §1 |
| `ai-deepsearch-osint` | ai-deepsearch-osint-gathering-report | FS | Same family as above |
| `ciso-executive-summary` | ciso-executive-summary | FS + CI | references/ specs + regenerated template.html; Python renderers run in CI |
| `ciso-reporting` | ciso-reporting | FS + CI | Deterministic pipeline: orchestrator script runs in CI; JS pptx generator flagged external-runtime |
| `cyber-forum` | cyber-forum | FS | Q&A/threat-intel; grounding recommended for live CVE data (same egress caveat as `deepsearch-protocol`) |
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
| `pptx-executive-summary-ciso` | pptx-executive-summary-ciso | FS + CI | Alias of `tprm-slide-generator` (`convert_skills.ALIASES`): built and byte-verified, **not** published as a second agent; the orchestrator registers the alias as a second trigger description on `tprm-slide-generator` |
| `tpsrca-assessment-engine` | tpsrca-assessment-engine | FS + CI | 12-agent methodology encoded in instructions; optionally split into separate published agents with A2A hand-offs later |
| `whisperx-transcribe-diarize` | whisperx-transcribe-diarize | FS + CI (post-processors) | Local-GPU skill: transcription moves to Azure AI Speech batch transcription + diarization (`workflows/speech-transcription.json`). `format_transcript.py`, `relabel_speakers.py`, `normalize_pt_br.py` and the HTML template run unchanged in `code_interpreter` via `scripts/adapters/speech_to_whisperx.py`, shipped inside the agent package |

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

`learn` and `doc-coauthoring` are **deployed (adapted)** rather than excluded:
the adaptation lives in the overlay layer, not in the converted body.
`agents/overlays/_foundry-environment.md` is appended to every agent after
its instructions, per-skill overlays in `agents/overlays/<skill>.md` carry
the ENX-specific rules, and `agents/document_agents_addendum.md` carries the
shared docx/pdf/pptx/xlsx delivery contract. Three further adaptation
decisions are recorded here so they are not re-litigated:

- `ai-deepsearch-osint-gathering-report` stays a **separate agent** with an
  identical toolset and shared companion references — not folded into
  `deepsearch-protocol`.
- `tpsrca-assessment-engine` Phase 1 (supplier classification) is served from
  `agents/advisor-knowledge/tpsrca-supplier-types.md`; Phase 2 (OSINT) is
  delegated to `deepsearch-protocol` through the ROUTER entry rather than
  duplicated.
- `enx-tprm-control-center` carries the menu v2 options 6–13 (the delivery
  and advisory pipelines) on top of the five original worker skills.

New agents with no source skill: `enterprise-explorer`,
`research-coordinator`, `research-worker`, `research-writer`
(`agents/README.md`). New pipelines with no source skill:
`generic-docx-deliverable`, `generic-pptx-deliverable`, `research-brief`
(`workflows/pipelines.json`).

## Non-skill components

**Superseded row.** The `platform-skills/` row of the table below used to
read "Not deployed by default; convert on demand the same way". That wording
is superseded by `templates/skill-decisions.json` plus
`governance/PLATFORM_SKILLS_DECISION.md`: each of the 41 built-ins carries an
explicit decision, and `scripts/verify_conversion.py` enforces it.


| Export component | Foundry equivalent |
|---|---|
| `PERSONA.md` | `agents/persona_system_prompt.md` — prepended to every agent's instructions by the converter |
| `CAPABILITIES.md` connectors (Gmail, Drive, GitHub, Adobe, …) | Per-connector decision (replaced · absorbed · excluded) in `integrations/CONNECTOR_DECISIONS.md`: Google Drive → `sharepoint-graph`, Gmail → `exchange-graph` + the gated mail send, Slack/Calendar → `teams-graph` + `m365-personal-graph` (delegated, OBO), GitHub → `azure-devops` (read-only; no PR/push tools by design), Firecrawl/WebFetch → Bing grounding + `osint-proxy`, Copilot → `integrations/copilot/` |
| `platform-skills/` (Anthropic built-ins beyond the enabled set) | Not convertible "on demand the same way" — most describe consumer Claude features. Each of the 41 carries an explicit decision (AGENT · KNOWLEDGE-PACK · SUPERSEDED · EXCLUDED) in `governance/PLATFORM_SKILLS_DECISION.md`, enforced from `templates/skill-decisions.json` |
| Harness skills (`CAPABILITIES.md`, 17 entries) | Recorded in `templates/skill-decisions.json` (origin `harness`, not enforced) and described in `governance/PLATFORM_SKILLS_DECISION.md` §3 |
| Routines / scheduled triggers | Azure Logic Apps (16 definitions in `workflows/` + `pipelines.json`) or Functions timer triggers calling the agent API (`conversations` / `responses`) |
| Artifacts (published HTML) | Self-contained single-file HTML stored in SharePoint (served as a download; no CDN scripts) — the default. Optional Entra-protected Azure Static Web App (`infra/static-web-app.bicep`, `enableStaticWebApp`) when rendered pages are wanted. Artifact **runtime capabilities** (shared database, per-viewer state, comments, republish watches, ask-Claude) have no equivalent and are out of scope |
| `web-artifacts-builder` (React/Vite bundling) | Not deployed — `code_interpreter` has no Node and no network; ENX dashboards are self-contained HTML templates in `templates/assets/` |
| Local binary toolchain the document skills assume (LibreOffice/`soffice`, pandoc, poppler/`pdftoppm`, qpdf, tesseract, ImageMagick) | **Not in `code_interpreter` and not in the delivery image.** The `functions/office-tools/` container (`{baseName}-office`) exposes it as `/api/convert`, `/api/recalc` (the xlsx skill's mandatory formula gate, running `recalc.py` verbatim), `/api/accept_changes`, `/api/thumbnail`, `/api/validate`. It is never an agent tool: it holds no Azure credential and makes no outbound call, and the delivery Function or the pipeline calls it (`agents/document_agents_addendum.md`, `agents/overlays/_foundry-environment.md`) |
| `verify_sync.py` | `scripts/verify_conversion.py` (offline: export vs `build/`, byte-level plus overlays and charters hashed) + `scripts/verify_kit.py` (kit consistency, secret scan) + `scripts/verify_deployment.py` (live: deployed agents vs the verified build — IDENTICAL · DIFFERENT · ONLY IN FOUNDRY · ONLY IN BUILD, exit 1 on drift; the last deploy step and the nightly drift job) |

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
