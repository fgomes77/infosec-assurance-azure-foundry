# Memory and Learning — How the Platform Remembers and Improves Without Modifying Itself

Scope: the memory tiers of the InfoSec Assurance agents (session,
durable team memory, knowledge, native agent memory) and the learning
loop that turns feedback, evaluation results and verifier outcomes into
owner-reviewed change proposals. Nothing in this file lets an agent alter
its own instructions, tools, model, memory policy or knowledge: every
change goes through `UPDATE_AND_UPGRADE_REVIEW_POLICY.md` and
`../operations/CHANGE_MANAGEMENT.md`. Companion files:
`memory/knowledge-refresh.md` (scheduled refresh of knowledge sources),
`memory/feedback-schema.json` (the feedback record), `memory/learning_loop.py`
(offline monthly aggregation into a proposal for the owner).

Owner: Francisco Gustavo Gomes (`{upn:francisco.gomes}`) — accountable
for creation, planning, maintenance, optimisation and updates. Users:
`{upn:francisco.gomes}`, `{upn:jose.mogollon}`, `{upn:pedro.santos}`,
`{upn:jose.meireles}`, `{upn:tania.morais}` (`../team/TEAM_MODEL.md`).
Platform status is as of 2026-09-12; GA/preview labels come from the
Microsoft Learn pages cited in §7. Supersedes the memory tiers sketch in
`memory-learning/MEMORY_LEARNING_RESEARCH.md` §2 where the two differ.

Control: ISO 27001:2022 A.5.12, A.5.34, A.8.10, A.8.32; ISO 42001
A.6.2.6, A.7.2–A.7.4, A.8.3, cl. 10.1–10.2; GDPR Art. 5(1)(c), (e), Art.
30; EU AI Act Art. 9, Art. 14, Art. 26(5)–(7); DORA Art. 9(4)(e), Art. 13.

## 1. Memory tiers

| # | Tier | Object on the platform | Written by | Read by | Retention / deletion | Status (source in §7) |
|---|---|---|---|---|---|---|
| M1 | **Session memory** — one conversation per (person, supplier, service, engagement) | Foundry **conversation** (the new Agent Service runtime replaced threads with conversations/responses; classic threads retire 2027-03-31) — the kit's `create_*.py` still say "thread"; the convention in `../team/TEAM_MODEL.md` §13 applies unchanged | the runtime, from the user's own turns | the user and team members who take over an engagement (team-visible data plane) | deleted 90 days after the deliverable is approved and stored, 180 days of inactivity otherwise (TEAM_MODEL §13); with **Standard agent setup** the conversation state lives in the customer's Cosmos DB for NoSQL in the EU region | GA — new runtime; Standard setup GA |
| M2 | **Durable team memory** (reviewed, auditable) | `vs-assurance-memory` vector store, managed by `../scripts/memory_store.py` (`add` / `list` / `delete`) and the MCP tools `save_memory` / `search_memory` (`../mcp-server/server.py`); note format and banned content in TEAM_MODEL §13 and `../governance/MEMORY_POLICY.md` | **humans only**, under their own identity — the human act is the approval (`../governance/HUMAN_APPROVAL.md` scope notes); agents cannot call `save_memory` | `infosec-assurance-advisor` and the orchestrator through file_search | `retain_until` ≤ 24 months by default; `memory_store.py delete <file_id>`; weekly export (`../operations/BACKUP_DR.md` §3) | GA (file_search) — see the one-store-per-agent constraint in §2 |
| M3 | **Per-agent knowledge** | `vs-<agent>` vector store per converted skill, rebuilt from `build/agents/<name>/knowledge/` by `create_agents.py`; templates enter through `update_templates.py` only | `deploy.sh` under the deploy service principal | the agent that owns it | rebuilt on every deploy; source of truth is the export + `../agents/` | GA |
| M4 | **Combined knowledge** (advisor) | `vs-assurance-combined` — every agent's knowledge files + `../agents/advisor-knowledge/*.md` + `knowledge-packs/*.md`, built by `create_orchestrator.py` | `deploy.sh` | advisor, orchestrator | rebuilt on every deploy | GA; successor candidate = a Foundry IQ knowledge base over a Blob mirror (§2) |
| M5 | **Native agent memory** (Memory in Foundry Agent Service) | memory store `ms-assurance-user` — **not enabled by this kit**; pilot conditions in §3 | the runtime (LLM extraction from conversations) | the agent it is attached to | store-level `default_ttl_seconds`, item-level CRUD, remember/forget | **Preview** |

What is *not* a memory tier: web grounding (Bing / Web Search) is a
per-request lookup and stores nothing; App Insights traces are an audit
record, never retrieved by agents; SharePoint reports are the deliverable
of record and are read only through the read-only Graph tool.

## 2. Design constraints the tiers must respect

| Constraint | Effect on the kit | Source |
|---|---|---|
| **One vector store per agent and one per conversation** (fixed service limit, not increasable) | `create_orchestrator.py` attaches both `vs-assurance-combined` and `vs-assurance-memory` to the advisor — this cannot hold on the new runtime. Target: keep **one** file_search store on the advisor (the combined knowledge) and move durable memory to an **Azure AI Search index** `kb-assurance-memory` reached through the GA Azure AI Search tool, or to a Foundry IQ knowledge base via the `knowledge_base_retrieve` MCP tool. `memory_store.py` keeps its commands (`add` / `list` / `delete` become index-document CRUD with the same note header, author and `retain_until` fields); the MCP server keeps `save_memory` / `search_memory`. Shared delta in §8 | limits page, 2026-09-07 (GA) |
| 10,000 files per vector store; 512 MB per file; 300 GB total uploads | `vs-assurance-combined` has headroom, but the memory tier grows one file per note — another reason to move M2 to an index | limits page (GA) |
| File search is **unavailable in Italy North** | `main.bicep` allows `italynorth`; a deployment there loses M2–M4 — remove it from the allow-list or document the gap (delta in §8) | file-search page, 2026-08-05 (GA) |
| Native memory: VNet integration **not supported**; per-user scope; quotas 100 scopes/store, 10k memories/scope; LLM-extracted content | M5 stays disabled while the platform is network-isolated; if piloted, per-user preferences only (§3) | what-is-memory / memory-usage, 2026-06 / 2026-08 (preview) |
| Foundry IQ: `azureBlob` / `searchIndex` sources GA in Search REST `2026-04-01`; **SharePoint indexed source preview** (`2026-08-01-preview`, no SLA); document ACLs honoured only where the source supports and syncs them; remote SharePoint source needs an M365 Copilot licence per caller | Knowledge base `kb-assurance` may replace M4 over a **Blob mirror** of the knowledge files (GA path); the SharePoint Reports library stays on the read-only Graph tool until the indexed source is GA | what-is-foundry-iq 2026-07-31; sharepoint-indexed 2026-09-02 (preview); foundry-iq-faq 2026-06-05 |
| Standard agent setup keeps conversations (Cosmos DB), files (Storage) and vector stores (AI Search) in customer EU resources; the capability host cannot be changed after creation | M1 residency evidence for DORA / GDPR; choose Standard setup at project creation (enterprise blueprint) | standard-agent-setup, 2026-07-09 (GA) |
| Agent versions are immutable (`<name>:<version>`, 1,000 versions per agent); traffic follows the active version | learning never edits a live agent: a change produces a **new version**, promoted by the owner | development-lifecycle 2026-08-27 (GA); limits page |

## 3. Native memory (M5) — conditions for a pilot, and what it must never hold

Not enabled by this kit. A pilot is a Tier C change under
`UPDATE_AND_UPGRADE_REVIEW_POLICY.md` class **platform feature (preview)**
and needs all of the following before `default_ttl_seconds` is set:

| Condition | Setting / evidence |
|---|---|
| Scope | advisor only; `scope="{{$userId}}"` (per user, never team-wide); `user_profile_enabled=true`, `chat_summary_enabled=true`, **`procedural_memory_enabled=false`** on every agent — procedural memory is an LLM-inferred instruction channel that bypasses review |
| Content boundary | `user_profile_details` exclusion list: only working preferences (language, report format, framework focus); never supplier names, findings, scores, personal data of third parties, credentials, internal hostnames |
| Retention | `default_ttl_seconds=7776000` (90 days); quarterly item-level listing and purge; RoPA entry updated before enablement (`../governance/MEMORY_POLICY.md` §4) |
| Security | memory content is untrusted input: prompt-injection detection on retrieval (Prompt Shields, `../infra/main.bicep` RAI policy); Microsoft's own page lists prompt injection and memory corruption as threats |
| Exit criteria | VNet isolation becomes mandatory (unsupported), preview terms conflict with the DPA review, or the feature is retired/changed at a platform currency review |

## 4. The learning loop — signals to proposals to controlled updates

The loop is **closed by people, not by agents**. Agents produce signals;
the owner (deputy for the owner's own changes) decides; the pipeline
deploys a new version; evaluation confirms.

```
 signals (continuous)                     monthly aggregation (offline)            decision + controlled change
 ───────────────────────────────          ────────────────────────────────         ───────────────────────────────
 F  user feedback records                 learning_loop.py --dry-run               owner reviews proposal.md
    (memory/feedback-schema.json)     ─►  clusters by agent × category  ─►         (deputy when the owner authored)
 E  eval-report.json (run_evals G0–G4;    scores value × (6 − risk) ÷ effort             │
    continuous evaluation, human eval)    → build/learning/{yyyy-mm}/proposal.md     accept ─► ticket {jira:INFOSEC-PLAT}-nnn
 V  verifier FAIL reasons                 (never writes to agents, registry,               ─► UPGRADE_CHECKLIST.md
    (kql/verifier-fail-rate.kql export)    templates or memory)                            ─► CHANGE_MANAGEMENT §3 (PR, gates,
 A  approval rework / rejections                                                              G1 control vs candidate)
    ({list:ApprovalDecisions} export)                                                      ─► new agent version / template version
                                                                                          ─► re-evaluation G2, then G3 monthly
                                                                                     defer / decline ─► recorded with reason
```

| Step | What happens | Who | Evidence |
|---|---|---|---|
| 1 Collect | F: any user files a feedback record (portal, MCP, Copilot, Teams form) — run/conversation ids only, no report content, no personal data. E: `../operations/evaluation/run_evals.py` reports; continuous-evaluation results in App Insights; human-evaluation template answers (preview) exported. V: verifier FAIL findings. A: approval decisions with rework comments | users; runtime; owner exports | `build/learning/inbox/` (feedback JSONL, exports) |
| 2 Aggregate | `python3 enterprise/memory/learning_loop.py --dry-run --month {yyyy-mm}` groups signals by agent × category, computes recurrence, maps each cluster to a change path (`CHANGE_MANAGEMENT.md` §1 type) and drafts one backlog item per cluster in the `CONTINUOUS_IMPROVEMENT.md` §2 format | owner (RUNBOOK M1) | `build/learning/{yyyy-mm}/proposal.md` + `.json` |
| 3 Decide | the owner accepts, defers or declines each item; AI concerns (S15) and corrective actions are mandatory items; anything that would weaken an invariant is refused (risk-acceptance path instead) | owner; deputy reviews owner-authored items | Jira issue per accepted item |
| 4 Change | `UPGRADE_CHECKLIST.md` filled; PR with gates (`verify_conversion.py`, `--dry-run` of the affected script, G1 control vs candidate eval); comparison set when a report agent changes | author + reviewer per policy | PR + eval reports |
| 5 Deploy | new immutable agent version / template version via `deploy.sh` or `update_templates.py`; the previous version stays for rollback | deploy SP after the owner's `production` approval | Actions log, `build/manifest.json` |
| 6 Re-evaluate | G2 after staged rollout; G3 monthly trend; the next month's proposal reports whether the cluster disappeared | owner | `Governance/Operations/{yyyy}-{mm}/evaluation.md` |

Optional platform accelerators (all preview, none on the approval path):
**Agent Optimizer** proposes instruction/tool-description/model candidates
from an evaluation dataset and only creates a new version on an explicit
human *Promote* — treat its candidates as step-2 input; **continuous
evaluation** samples live traffic at a set percentage into the same
evaluators (GA core, some evaluators preview); **human evaluation
templates** collect reviewer ratings in the agent's Preview app (preview).
Never wire the optimizer to auto-promote; never let continuous-evaluation
results trigger a deployment.

## 5. What is never learned

| Never | Why | Enforced by |
|---|---|---|
| Autonomous self-modification: an agent editing its own or another agent's instructions, tools, model, guardrails, memory policy, templates or knowledge | reviewability (EU AI Act Art. 14; ISO 42001 A.6.2.5) | agents hold no write path (`HUMAN_APPROVAL.md` Layer 1); `agent_modified_by_non_deploy_identity` alert; immutable versions promoted by humans |
| Procedural memory on any report-producing or advisory agent | unreviewed instruction channel | `procedural_memory_enabled=false`; M5 disabled |
| Fine-tuning on assessment data | corpus changes with templates and regulations; answers must cite sources; Microsoft's own guidance reserves fine-tuning for stable style/format needs with curated data | no fine-tuning resources in `../infra/`; a request is a class *model* change with DPO review |
| Supplier confidential documents, personal data beyond role/company, special-category data, credentials, hostnames, verbatim contract text | GDPR minimisation; TEAM_MODEL §13 | note format + W5 review (`R13`); `verify_conversion.py` secret grep |
| Content of rejected or unapproved drafts as knowledge | only approved outputs may become golden-set baselines | `EVALUATION.md` §2; `knowledge-refresh.md` §3 |
| Individual user behaviour or performance profiles | `owner_upn` is for cost/capacity attribution only | TEAM_MODEL §13; no per-user store |
| Anything from a source not reviewed under `knowledge-refresh.md` (web pages, e-mail, chat transcripts) | provenance and IP (`../governance/THIRD_PARTY_IP.md`) | knowledge enters only via the export or `../agents/` through a PR |

## 6. GDPR minimisation and records

| Item | Rule |
|---|---|
| Feedback records | no report content, findings, scores, supplier confidential text or personal data; identifiers = run id, conversation id, agent, pipeline; submitter as `{upn:name}`; retained 24 months then purged from `build/learning/inbox/` and the SharePoint list `{list:PlatformFeedback}` (shared delta §8) |
| Durable memory | `MEMORY_POLICY.md` §1–§3; deletion on request by subject tag; RoPA entry owned by the owner |
| Evaluation artefacts | synthetic or public inputs only (`EVALUATION.md` §2); reports stored ≥ 1 year as change evidence |
| Native memory (if piloted) | per-user scope, 90-day TTL, exclusion list, RoPA before enablement, item-level deletion on leaver (`TEAM_MODEL.md` §14) |
| Learning proposals | contain aggregates and ids only; kept with the month's evaluation note |

## 7. Sources (status as of 2026-09-12)

| Claim | Source | Date | Status |
|---|---|---|---|
| One vector store per agent and per conversation; 10,000 files per store; 512 MB; 1,000 versions per agent | https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/limits-quotas-regions#default-service-limits | 2026-09-07 | GA |
| File search GA; unavailable in Italy North; Standard setup keeps files/index in customer Storage + AI Search | https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/file-search | 2026-08-05 | GA |
| Conversations replace threads; classic Agent Service retires 2027-03-31 | https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/migrate | 2026-08-05 | GA |
| Standard agent setup: Cosmos DB / Storage / AI Search in customer tenant; capability host immutable | https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/standard-agent-setup | 2026-07-09 | GA |
| Memory: user profile, chat summary, procedural; per-user scope; VNet unsupported; injection/corruption threats | https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/what-is-memory | 2026-06-02 | Preview |
| Memory store configuration (`*_enabled`, `default_ttl_seconds`, `update_delay`) | https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/memory-usage | 2026-08-05 | Preview |
| Foundry IQ knowledge bases: GA/preview split by Search REST version | https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/what-is-foundry-iq | 2026-07-31 | GA core / preview parts |
| Indexed SharePoint knowledge source | https://learn.microsoft.com/en-us/azure/search/agentic-knowledge-source-how-to-sharepoint-indexed | 2026-09-02 | Preview |
| Knowledge base connection via MCP `knowledge_base_retrieve` | https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/foundry-iq-connect | 2026-09-11 | Preview |
| Foundry IQ permissions and licensing | https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/foundry-iq-faq | 2026-06-05 | GA doc |
| Immutable agent versions, rollback by version switch | https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/development-lifecycle | 2026-08-27 | GA |
| Continuous evaluation of live traffic (sampling, max requests/hour) | https://learn.microsoft.com/en-us/azure/foundry/concepts/observability | 2026-07-31 | GA core; some evaluators preview |
| Human evaluation templates | https://learn.microsoft.com/en-us/azure/foundry/observability/how-to/human-evaluation | 2026-07-31 | Preview |
| Agent Optimizer: candidates, human Promote only | https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/agent-optimizer-overview | 2026-08-19 | Preview |
| AI Red Teaming Agent: agentic risk categories | https://learn.microsoft.com/en-us/azure/foundry/concepts/ai-red-teaming-agent | 2026-08-27 | Preview |
| When not to fine-tune | https://learn.microsoft.com/en-us/azure/foundry/openai/concepts/fine-tuning-considerations | 2026-06-05 | GA |
| Purview for Foundry interactions (audit, DSPM for AI, labels) | https://learn.microsoft.com/en-us/purview/ai-azure-foundry | 2026-05-01 | GA |

## 8. Shared deltas (literal text, not applied here)

| Id | Target | Text |
|---|---|---|
| D-ML-1 | `orchestrator/README.md` §"Memory" | replace "*Thread memory* — native: keep one Foundry thread per team member" with "*Session memory* — one Foundry **conversation** per (person, supplier, service, engagement) (`team/TEAM_MODEL.md` §13); the new Agent Service runtime uses conversations, classic threads retire 2027-03-31" and append to *Durable memory*: "The service allows one vector store per agent (limits page, 2026-09-07); target design keeps `vs-assurance-combined` on file_search and serves memory from the Azure AI Search index `kb-assurance-memory` (`enterprise/MEMORY_AND_LEARNING.md` §2)." |
| D-ML-2 | `scripts/create_orchestrator.py` (advisor tool wiring) | attach only `vs-assurance-combined` to file_search; add the Azure AI Search tool for index `kb-assurance-memory` when `SEARCH_SERVICE_ENDPOINT` is set; keep creating `vs-assurance-memory` only when `MEMORY_BACKEND=vector-store` (transition default) |
| D-ML-3 | `scripts/memory_store.py` / `mcp-server/server.py` | add `MEMORY_BACKEND` (`vector-store` \| `search-index`); for `search-index`, `add` = index document `{id, stamp, author, class, subject, retain_until, text}`, `list` = query with `$select` of the header fields, `delete` = delete by document id; `purge --older-than` per `governance/MEMORY_POLICY.md` §3 |
| D-ML-4 | `infra/main.bicep` | remove `'italynorth'` from the `location` allow-list (file search unavailable there) or add the comment `// italynorth: file_search not available — M2–M4 unusable`; add `param enableKnowledgeSearch bool = false` provisioning `Microsoft.Search/searchServices` (basic, EU region, `publicNetworkAccess` per `enablePrivateNetworking`) and a project connection of category `CognitiveSearch` |
| D-ML-5 | `setup/.env.example` | append `MEMORY_BACKEND=vector-store   # vector-store | search-index (enterprise/MEMORY_AND_LEARNING.md §2)` and `SEARCH_SERVICE_ENDPOINT=https://<search>.search.windows.net` and `MEMORY_INDEX_NAME=kb-assurance-memory` |
| D-ML-6 | `governance/MEMORY_POLICY.md` §4 | replace the paragraph with: "Preview feature; pilot conditions in `enterprise/MEMORY_AND_LEARNING.md` §3 (advisor only, per-user scope, procedural memory off, TTL 90 d, exclusion list, RoPA first). Not enabled by this kit." |
| D-ML-7 | `operations/CONTINUOUS_IMPROVEMENT.md` §1 | add row `\| S17 \| Feedback records (memory/feedback-schema.json) and the monthly learning proposal (enterprise/memory/learning_loop.py) \| build/learning/{yyyy-mm}/proposal.md \| monthly M1 \| every accepted item \| per proposal \|` |
| D-ML-8 | `sharepoint/README.md` | add list `{list:PlatformFeedback}` with the columns of `feedback-schema.json` (no report content, no personal data), read for `sg-infosec-foundry-users`, retention 24 months |
| D-ML-9 | `ARCHITECTURE.md` row "Memory/state" | `\| Memory/state \| Foundry conversations (session) + vs-assurance-memory → kb-assurance-memory (durable, auditable, deletable) + per-agent and combined knowledge stores; native Memory (preview) not enabled; learning loop = signals → owner-reviewed proposals → new agent version (enterprise/MEMORY_AND_LEARNING.md) \|` |
