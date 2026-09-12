# Model Routing — Best Model per Task, Lowest Tokens per Result

Requirement j: use the most adequate LLM for each task, minimising token
consumption while keeping accuracy and result quality. Three deployment
tiers (names configurable in `setup/.env`; swap the concrete models as the
Azure catalogue evolves — the TIER structure is the contract):

| Tier | Default deployment | Cost profile | Assigned to |
|---|---|---|---|
| `light` | `gpt-4o-mini` | ~15–30× cheaper than reasoning | Deterministic transformation against fixed templates and schemas, routing, bookkeeping: `docx`, `pdf`, `pptx`, `xlsx`, `enx-tprm-control-center` (router, no tools), `morning` |
| `chat` | `gpt-4o` | mid | Standard report generation where the template + verified extraction rules carry the quality: `dpia`, `ciso-reporting`, `ciso-executive-summary`, `tprm-slide-generator`, `pptx-executive-summary-ciso`, `onetrust-form-b`, `template-manager`, `whisperx-transcribe-diarize`, `doc-coauthoring`, `internal-comms`, `learn` |
| `reasoning` | `o3-mini` | high per token, but fewer iterations on analytic work | Judgement-heavy analysis: `deepsearch-protocol`, `ai-deepsearch-osint-gathering-report`, `cyber-forum`, `ciso-global-report`, `tpa-evidence-analyzer`, `soc-report-analyzer`, `pentest-report-analyzer`, `pdf-full-coverage-analyzer`, `tpsrca-assessment-engine`, `mcp-builder`, framework advisors (`iso27001`, `iso42001`, `dora`, `nis2`, `eu-ai-act`), `infosec-assurance-advisor`, orchestrator, `output-verifier` |

Assignment of record: the `model_tier` field per agent in
`integrations/registry.json`, applied by `attach_integrations.py`. The
table above was regenerated from the registry (2026-09-12); a
`verify_kit`/`verify_conversion` drift check comparing this table with
the registry is a shared delta — until it exists, edit both together.

### Vision / image inputs

`o3-mini` (reasoning) accepts no image input; `gpt-4o` / `gpt-4o-mini`
do. Requirement d2 lists images and scanned PDFs as evidence, so the rule
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
| `reasoning` | no | consumes transcribed text only |

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
   agent (ARCHITECTURE.md metrics). Review monthly: an agent whose
   quality holds on a cheaper tier moves down; one that loops or fails
   verification moves up. Change = edit `model_tier` in the registry +
   re-run `attach_integrations.py --only <agent>`.

## Accuracy floor

Economy never overrides fidelity: report-producing agents were validated
against known-good claude.ai outputs on their assigned tier. Any tier
downgrade for those agents requires re-running the comparison set
(`scripts/smoke_test.py` prompts + a known assessment) and a template-
manager-style approval before it takes effect.
