# Memory and learning options for the InfoSec Assurance agents (research note, 2026-09-12)

Scope: how the platform's agents should remember, ground, and improve — and how
they are kept from changing themselves without review. Evidence is from
Microsoft Learn / Foundry blog pages read on 2026-09-12; status is as of that date.
Nothing here edits shared files; deltas for README/ARCHITECTURE/main.bicep/
registry are listed at the end as literal text for the integration pass.

## 1. Current kit position vs. platform reality

| Kit today (orchestrator/README.md, ARCHITECTURE.md) | Platform as of 2026-09 | Consequence |
|---|---|---|
| "Thread memory — native: one Foundry thread per team member" | Agent Service runtime = agents / **conversations** / responses; conversations are durable objects reused across sessions; `store=false` opts out of server-side history | Rename "thread" to "conversation" in docs; keep the per-user conversation convention |
| Durable memory = `vs-assurance-memory` vector store + `memory_store.py` + `MEMORY:` block | Native **Memory (preview)**: user-profile, chat-summary and **procedural** memory; per-user `scope="{{$userId}}"`; item-level CRUD; store-level default TTL; remember/forget commands; regions include Sweden Central; VNet integration NOT supported; quotas 100 scopes/store, 10k memories/scope | Keep the vector-store memory as the **reviewed, auditable** tier; pilot native memory only for per-user preferences (not supplier facts/positions); do not enable procedural memory on any agent that writes reports |
| Per-agent vector stores via file_search | **Foundry IQ knowledge bases** on Azure AI Search: shared across agents, scheduled indexer refresh (5 min–24 h), ACL sync for supported sources; `searchIndex`/`azureBlob`/`indexedOneLake`/`web` GA in REST `2026-04-01`, SharePoint indexed source still preview | Candidate replacement for `vs-assurance-combined`: one KB over a Blob mirror of the knowledge files (GA path); SharePoint indexer stays preview -> use only for the Reports library read-side, behind a change ticket |
| ARCHITECTURE.md §"Evaluation and success metrics" (manual) | Evaluations/monitoring/tracing GA (Mar 2026); **continuous evaluation rules** (`EvaluationRule`, `max_hourly_runs`, default 100/h), scheduled evaluations, human evaluation templates (preview), end-user feedback events (preview), AI Red Teaming Agent (preview; cloud runs in Sweden Central; agentic risk categories: prohibited actions, sensitive-data leakage, task adherence, XPIA) | Adopt the continuous-evaluation loop below; it is the mechanism the "known-good outputs" KPI in task 2(B) needs |
| No fine-tuning | Fine-tuning docs: use when you have hundreds–thousands of curated pairs and need style/format/tool-use consistency; costs retraining on data/base-model change; imports from Blob need public network access | **Do not fine-tune.** The assurance corpus changes (templates, regs) and answers must cite sources — RAG + instructions + evaluation is the right loop |
| Instructions live in build/ + `update_templates.py` approval flow | Agent versions are immutable snapshots (`<name>:<version>`); publishing = agent application + deployment; **Agent Optimizer (preview)** proposes instruction/tool-description/model candidates and only creates a *new version* on explicit "Promote"; prompt flow retires 2027-04-20 | Versioning story is native; keep the human "Promote" as the only path to a new version; never wire the optimizer to auto-promote |

## 2. Recommended memory tiers

1. **Session** — one Foundry conversation per user per engagement (`conv-{upn:name}-{engagement}`); retention per ISMS record schedule; `store=false` for red-team/purple runs.
2. **Reviewed durable memory** — existing `vs-assurance-memory` (notes written only via `memory_store.py` / MCP `save_memory`, which is itself an approval-gated action per governance/HUMAN_APPROVAL.md). Holds supplier facts, positions taken, CISO decisions. Auditable, deletable, exportable.
3. **Native user memory (preview pilot, advisor only)** — memory store `ms-assurance-user` with `user_profile_enabled=true`, `chat_summary_enabled=true`, `procedural_memory_enabled=false`, `default_ttl_seconds=7776000` (90 d), `user_profile_details="Only working preferences: language, report format, framework focus. Never store supplier names, findings, personal data of third parties, credentials."`, tool `memory_search_preview` with `scope="{{$userId}}"` and `update_delay=5`. Exit the pilot if VNet isolation becomes a requirement (unsupported) or the preview terms conflict with the DPA review.
4. **Knowledge** — Foundry IQ knowledge base `kb-assurance` (GA `2026-04-01` shape: `azureBlob` source over `st-{env}-knowledge/knowledge-mirror`, indexer `PT6H`, `searchIndex` source for the templates registry). SharePoint indexed source (`2026-08-01-preview`) only after the preview-terms review; remote SharePoint source requires M365 Copilot licences for callers.

## 3. Evaluation-driven improvement loop (no self-modification)

```
production traffic ──► continuous EvaluationRule (groundedness, relevance,
   task_adherence, tool_call_accuracy, sensitive-data)  ─► App Insights
       │                                                       │
       ├─ human evaluation template (assurance-lead review)    ├─ alerts (preview):
       ├─ end-user thumbs (gen_ai.evaluation.result events)    │  score drop, latency, tokens
       ▼                                                       ▼
   golden dataset (build/eval/golden.jsonl, curated from  ◄── cluster analysis
   approved SharePoint reports; refreshed quarterly)
       │
       ▼
   Agent Optimizer run (preview) ──► candidates + diff ──► Francisco reviews
       │                                                        │
       └── "Promote candidate" = NEW immutable agent version ◄──┘
                     │
                     ▼
        change ticket + verify_conversion.py + smoke_test.py
        + scheduled AI red-team scan (purple env) before traffic switch
```

Rules
- Only a human clicks Promote / sets the active version; the optimizer's output is a proposal (its docs: "the new version doesn't receive traffic until you set it as the active version").
- `procedural_memory_enabled=false` on every report-producing agent: procedural learnings are LLM-as-a-judge inferred routines injected into context — an unreviewed instruction channel.
- Native memory writes are debounced by `update_delay`; treat the memory store as untrusted input: content-safety prompt-injection detection on retrieval, and a quarterly listing/purge (item-level CRUD).
- Foundry Control Plane (Operate pane) is where guardrail policies, red-team schedules and the fleet view live; agents get an Entra Agent ID at build time.

## 4. Shared deltas for the integration pass (literal text, not applied)

- README.md, "Concept mapping" table, row "claude.ai skill sync": append a row
  `| Memory / learning | Conversations (session) + vs-assurance-memory (reviewed) + optional Memory (preview) user profile; Foundry IQ knowledge base for shared knowledge; continuous evaluation -> Agent Optimizer proposals -> human Promote (see enterprise/memory-learning/) |`
- ARCHITECTURE.md line 57 "Memory/state": replace with
  `| Memory/state | Foundry conversations (session) + vs-assurance-memory (durable, auditable, deletable) + Memory (preview) user-profile pilot on the advisor only; procedural memory disabled |`
- ARCHITECTURE.md §"Evaluation and success metrics": add
  `Continuous evaluation rule per production agent (groundedness, relevance, task_adherence, tool_call_accuracy; max_hourly_runs=100) plus a weekly scheduled evaluation against build/eval/golden.jsonl; results in App Insights; Agent Optimizer candidates are promoted only by the platform owner.`
- infra/main.bicep: add `param enableKnowledgeBase bool = false` and, when true, `Microsoft.Search/searchServices` (basic, `semanticSearch: 'standard'`, `knowledgeRetrieval` consent) + a project connection of category `CognitiveSearch`; the project managed identity needs `Foundry User` on the project for continuous-evaluation rules.
- setup/.env.example: add
  `SEARCH_SERVICE_ENDPOINT=https://<search>.search.windows.net`
  `KNOWLEDGE_BASE_NAME=kb-assurance`
  `MEMORY_STORE_NAME=ms-assurance-user   # optional preview pilot`
- governance/HUMAN_APPROVAL.md: add gate "Promote agent version (incl. Agent Optimizer candidates) — approver: platform owner; evidence: eval run report URL + diff".
- governance/DATA_PROTECTION_GUARDRAILS.md: add "Native memory store: TTL 90 d, user_profile_details exclusion list, no VNet — document in RoPA; preview terms apply."
