# Model Routing — Best Model per Task, Lowest Tokens per Result

Requirement j: use the most adequate LLM for each task, minimising token
consumption while keeping accuracy and result quality. Three deployment
tiers (names configurable in `setup/.env`; swap the concrete models as the
Azure catalogue evolves — the TIER structure is the contract):

| Tier | Default deployment | Cost profile | Assigned to |
|---|---|---|---|
| `light` | `gpt-4o-mini` | ~15–30× cheaper than reasoning | Deterministic transformation against fixed templates and schemas: `docx`, `pdf`, `pptx`, `xlsx` document agents, routing hand-offs, folder/file bookkeeping |
| `chat` | `gpt-4o` | mid | Standard report generation where the template + verified extraction rules carry the quality: `dpia`, `ciso-reporting`, `ciso-executive-summary`, `tprm-slide-generator`, `onetrust-form-b`, `template-manager`, `enx-tprm-control-center` |
| `reasoning` | `o3-mini` | high per token, but fewer iterations on analytic work | Judgement-heavy analysis: `deepsearch-protocol`, `cyber-forum`, `ciso-global-report`, `tpa-evidence-analyzer`, `soc-report-analyzer`, `pentest-report-analyzer`, `tpsrca-assessment-engine`, framework advisors, `infosec-assurance-advisor`, orchestrator |

Assignment of record: the `model_tier` field per agent in
`integrations/registry.json`, applied by `attach_integrations.py`.

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
