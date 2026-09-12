# Model Routing — Best Model per Task, Lowest Tokens per Result

Requirement j: use the most adequate LLM for each task, minimising token
consumption while keeping accuracy and result quality. Three deployment
tiers (names configurable in `setup/.env`; swap the concrete models as the
Azure catalogue evolves — the TIER structure is the contract):

| Tier | Default deployment | Cost profile | Assigned to |
|---|---|---|---|
| `light` | `gpt-4o-mini` | ~15–30× cheaper than reasoning | Deterministic transformation against fixed templates and schemas, routing, bookkeeping: `docx`, `pdf`, `pptx`, `xlsx`, `enx-tprm-control-center` (router, no tools), `morning` |
| `chat` | `gpt-4o` | mid | Standard report generation where the template + verified extraction rules carry the quality: `dpia`, `ciso-reporting`, `ciso-executive-summary`, `tprm-slide-generator`, `pptx-executive-summary-ciso`, `onetrust-form-b`, `template-manager`, `whisperx-transcribe-diarize`, `doc-coauthoring`, `internal-comms`, `learn` |
| `reasoning` | `o4-mini` (tool-capable reasoning model — finding C4; **never `o3-mini`**, which supports none of the OpenAPI, MCP, Azure AI Search, SharePoint or Web Search tools that every reasoning agent carries) | high per token, but fewer iterations on analytic work | Judgement-heavy analysis: `deepsearch-protocol`, `ai-deepsearch-osint-gathering-report`, `cyber-forum`, `ciso-global-report`, `tpa-evidence-analyzer`, `soc-report-analyzer`, `pentest-report-analyzer`, `pdf-full-coverage-analyzer`, `tpsrca-assessment-engine`, `mcp-builder`, framework advisors (`iso27001`, `iso42001`, `dora`, `nis2`, `eu-ai-act`), `infosec-assurance-advisor`, orchestrator, `output-verifier` |

**Tool compatibility is part of the routing rule (finding C4).** An agent may
only be pinned to a tier whose model supports *every* tool type it carries. The
matrix of record — per model, per tool type, with the Microsoft tool-support
table as source — is `../integrations/registry.json` →
`model_tiers._tool_compatibility`, and the deployment per tier is
`model_tiers._deployment_of_record`. `attach_integrations.py` fails the run for
any agent whose tier model is marked `no` for a tool type it carries. Re-check
the matrix at every model change and at the standing platform-currency review
(`../enterprise/UPDATE_AND_UPGRADE_REVIEW_POLICY.md`).

Assignment of record: the `model_tier` field per agent in
`integrations/registry.json`, applied by `attach_integrations.py`. The
table above was regenerated from the registry (2026-09-12); a
`verify_kit`/`verify_conversion` drift check comparing this table with
the registry is a shared delta — until it exists, edit both together.

### Tool compatibility (tier name ≠ tool support)

Tool support is a property of the MODEL, not of the tier label. `o3-mini`
supports **no** OpenAPI, MCP, AI Search / `file_search`, SharePoint or Web
Search tools, yet every advisory, analyzer and research agent above is
pinned to `reasoning` AND carries the 11-tool read-only surface
(`advisory_read_only_toolset` in `integrations/registry.json`). The
`reasoning` deployment is therefore a tool-capable reasoning model
(`o4-mini` of record; validate candidates on the dev comparison set before
promotion). Pinning the tier back to `o3-mini` would leave those agents
unable to call a single enterprise tool, and
`scripts/attach_integrations.py` now refuses the run if that is attempted.

| Tool class | `light` (`gpt-4o-mini`) | `chat` (`gpt-4o`) | `reasoning` (`o3-mini`) | `reasoning` (`o4-mini`, of record) |
|---|---|---|---|---|
| `code_interpreter` | yes | yes | yes | yes |
| `file_search` / AI Search | yes | yes | **no** | yes |
| OpenAPI (Confluence, Jira, CMDB, Graph, OneTrust, SecurityScorecard, IAF, osint-proxy) | yes | yes | **no** | yes |
| MCP (ENX gateway) | yes | yes | **no** | yes |
| SharePoint grounding (preview, OBO) | yes | yes | **no** | verify on the day |
| Bing grounding / Web Search | yes | yes | **no** | yes |
| Image input | yes | yes | **no** | per model — verify |

Source: Microsoft Foundry — tool support by region and model,
https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/limits-quotas-regions#tool-support-by-region-and-model (GA, 2026-09-07).

Routing consequence (already written into the agent charters): an agent on a
model that cannot carry a tool never guesses the result — the read is routed
to `enterprise-explorer` (light) and the retrieved material is handed to the
reasoning agent as text.

The `reasoning` row of the tier table above names the re-selected model, and
`integrations/registry.json` `model_tiers._comment` /
`model_tiers._deployment_of_record` carry the same value; the three move in one
change.

### Vision / image inputs

`o3-mini` accepts no image input; `gpt-4o` / `gpt-4o-mini` do. The image-input
column of the newly selected reasoning model (`o4-mini`) must be re-verified on
the day of deployment and the row above updated before any pipeline relies on
it; until then the platform keeps the conservative rule below. Requirement d2 lists images and scanned PDFs as evidence, so the rule
is: **image inputs never reach a reasoning agent directly.** A pre-step
transcribes them to text — scanned PDFs via Document Intelligence
(`/api/extract_pdf` in the delivery Function), images via a
`/api/describe_image` endpoint that runs the `chat` deployment with a
fixed, non-generative "transcribe exactly; do not interpret" prompt
(shared delta in `report-delivery-pipeline.json` / `function_app.py`) —
and the reasoning agent consumes the resulting text, which is stored with
the audit artefacts (`DATA_PROTECTION_GUARDRAILS.md` §4). Accuracy floor:
transcription output is verbatim evidence, so it is subject to the
verifier's grounding rule like any other source.

| Tier | Vision input | Use for images |
|---|---|---|
| `light` | yes | cheap OCR-style transcription of simple scans |
| `chat` | yes | `describe_image` transcription of complex evidence (certificates, dashboards) |
| `reasoning` | no (assumed until the selected model's row is verified) | consumes transcribed text only |

**Advisory pin (requirements g/h/i):** every information-providing system
— the framework advisors (iso27001, iso42001, dora, nis2, eu-ai-act),
cyber-forum, tpsrca-assessment-engine and infosec-assurance-advisor —
is PINNED to the `reasoning` tier (the registry's
`advisory_read_only_toolset` lists them; `enx-tprm-control-center` is
deliberately NOT in the list — it is a `light` router with no tools). These agents answer
users directly, so quality of reasoning is the product; the monthly
tier-tuning review below may move other agents down, never these. They
also carry code_interpreter for Word/Excel/PowerPoint/HTML file
generation (`scripts/apply_advisory_profile.py`), and file rendering
stays deterministic code — token economy for advisory systems comes from
RAG retrieval and structured output contracts, not from a cheaper model.

## Token-economy rules (already engineered into the platform)

1. **Deterministic code over generation** — everything renderable is
   rendered by scripts (code_interpreter or the delivery Function), never
   token-generated: PPTX/DOCX/XLSX bytes cost zero completion tokens and
   are byte-consistent with the previous environment.
2. **RAG over context stuffing** — knowledge lives in vector stores;
   file_search retrieves only relevant chunks instead of carrying whole
   catalogues in every prompt.
3. **Verifier before human** — the cheap deterministic-rules pass catches
   rework before an expensive regeneration round-trip with the approver.
4. **Single-pass output contracts** — agents emit one structured JSON
   block per deliverable (no conversational padding), sized to the
   renderer's schema.
5. **Orchestrator restraint** — the orchestrator answers directly only
   when no specialist adds value, and hands off otherwise; hand-offs go
   to the cheapest tier that can do the task.
6. **Chunked PDF analysis** — the full-coverage method processes long
   reports in bounded chunks with per-chunk extraction, avoiding repeated
   full-document context.
7. **Monitor and tune** — App Insights tracks tokens per deliverable per
   agent (ARCHITECTURE.md metrics). Review monthly using
   `../operations/kql/latency-and-tokens.kql` and `verifier-fail-rate.kql`
   (`../operations/RUNBOOK.md` M2); a tier move is a change under
   `../operations/CHANGE_MANAGEMENT.md` §1. An agent whose
   quality holds on a cheaper tier moves down; one that loops or fails
   verification moves up. Change = edit `model_tier` in the registry +
   re-run `attach_integrations.py --only <agent>`.
   Procedure: `../operations/TOKEN_ECONOMY_PLAYBOOK.md`; accuracy-floor
   evidence: `../operations/evaluation/run_evals.py` against
   `../operations/evaluation/golden-set.*.json` (gate G1); cost figures:
   `../operations/FINOPS.md` §2. Tier proposals from the monthly review are
   backlog items delivered in the quarterly improvement cycle
   (`../operations/CONTINUOUS_IMPROVEMENT.md` §4.1 "FinOps").

   **Tool-support rule (R4 of `../enterprise/UPDATE_AND_UPGRADE_REVIEW_POLICY.md`):**
   a tier model must support every tool in the tier's toolset per the
   [tool-support table](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/limits-quotas-regions#tool-support-by-region-and-model)
   (2026-09-07, GA) **on the day of the change**. `o3-mini` fails this for the
   advisory toolset, which is why the reasoning tier is `o4-mini`;
   `python3 ../enterprise/upgrade/check_model_lifecycle.py --dry-run` reports any
   violation, and `attach_integrations.py` refuses the run.

## Accuracy floor

Economy never overrides fidelity: report-producing agents were validated
against known-good claude.ai outputs on their assigned tier. Any tier
downgrade for those agents requires re-running the comparison set
(`scripts/smoke_test.py` prompts + a known assessment) and a template-
manager-style approval before it takes effect.
