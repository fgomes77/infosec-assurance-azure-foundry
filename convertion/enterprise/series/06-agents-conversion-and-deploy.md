# Step 06 — Agents: runtime migration, conversion, deploy

**Objective.** Migrate the kit's scripts and MCP server from the classic
threads/runs runtime to the GA Responses-API service **first** (D1), then
run the gated chain `convert → verify → create → attach → delivery agents →
orchestrator → advisory profile → smoke test` (`deploy.sh`) per
environment, with the advisor's stores merged (D5) and multi-agent routing
re-implemented without connected agents (D2). Result fidelity is proven by
`scripts/verify_conversion.py` (byte checks of instructions, templates,
thresholds and scripts) and the comparison set.

**Owner / effort.** `{upn:francisco.gomes}`; 6 days (2 for §A in `dev`,
then 1–2 per environment). No countersign; UAT by the four users in
`test`. **Depends on** 02, 04.

## 1. Platform facts

| Fact | Status / source |
|---|---|
| Classic Agent Service (threads/runs; `azure-ai-agents` `AgentsClient`) retires **2027-03-31**; Assistants API retired 2026-08-26; new service = agents / conversations / responses; `azure-ai-projects` 2.x (2.6.0, 2026-09-04) drops the `azure-ai-agents` dependency; REST `api-version=v1` for agents/conversations/responses | [GA] https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/migrate (2026-08-05); https://github.com/Azure/azure-sdk-for-python/blob/main/sdk/ai/azure-ai-projects/CHANGELOG.md (2026-09-04); https://learn.microsoft.com/en-us/azure/foundry/reference/foundry-project-rest-preview |
| Two agent types: **prompt agents** (config only) and **hosted agents** (container/.zip, Agent Framework, LangGraph, custom; GA); every save is an immutable **version** `<name>:<version>`, traffic pinned by version selector; up to 1,000 versions per agent | [GA] https://learn.microsoft.com/en-us/azure/foundry/agents/overview (2026-08-19); https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/development-lifecycle (2026-08-27) |
| Connected agents **not available**; A2A tool (preview) or Agent Framework orchestration instead | [GA/preview] https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/agent-to-agent (2026-09-04) |
| File search GA (not in Italy North); **1 vector store per agent**, 10,000 files per vector store, 512 MB per file, 2,000,000 tokens per file (limits page; the file-search page says 5,000,000); 128 tools per agent; 100,000 messages per conversation — not increasable | [GA] https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/file-search (2026-08-05); …/limits-quotas-regions (2026-09-07) |
| Code Interpreter GA: Python-only sandbox (ACA dynamic sessions, no outbound network, 1 h active / 30 min idle, billed separately, project region) | [GA] https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/code-interpreter (2026-08-05) |
| Memory (preview) — not enabled on report agents; see `enterprise/memory-learning/` | [preview] https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/what-is-memory (2026-06-04) |
| Agent Optimizer (preview) proposes; only a human *Promote* creates a new version | [preview] https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/agent-optimizer-overview (2026-08-19) |

## A. Runtime migration of the kit (once, in `dev`, before any agent exists)

| # | File | Change (shared delta) | Verify |
|---|---|---|---|
| A1 | `setup/requirements.txt`, `mcp-server/requirements.txt` | **S-06**: `azure-ai-projects>=2.3.0,<3` (2.6.0 current), remove `azure-ai-agents==1.1.0`, keep `azure-identity`, `python-dotenv`, `PyYAML`, `mcp` | `pip install -r`; `python3 -c "import azure.ai.projects as p; print(p.__version__)"` |
| A2 | `scripts/create_agents.py`, `scripts/create_delivery_agents.py`, `scripts/create_orchestrator.py`, `scripts/apply_advisory_profile.py`, `scripts/attach_integrations.py` | replace `azure.ai.agents.models` imports and `agents_client.create_agent(...)`/`update_agent` with `project.agents.create_version(agent_name, definition=PromptAgentDefinition(model, instructions, tools))`; "idempotent by name" becomes "new immutable version per run, previous versions kept" | every script `--dry-run` unchanged in output; `verify_conversion.py` untouched (it checks build bytes, not the runtime) |
| A3 | `scripts/smoke_test.py`, `mcp-server/server.py` | **Applied in `mcp-server/server.py`**: the server calls `scripts/_foundry_runtime.py` (`conversations` + `responses`, `agent_reference` with the promoted version); the MCP parameter is `conversation_id` and `thread_id` is still accepted and returned as a deprecated alias for one release. Original shape: threads → `conversations.create()`; runs → `responses.create(conversation=…, input=…, extra_body={"agent_reference": {"name": …, "type": "agent_reference"}})`; MCP `thread_id` parameter renamed `conversation_id` (old name accepted for one release) | `smoke_test.py --agent dora --prompt …` returns text |
| A4 | `scripts/_azure_helpers.py` | file uploads through `project.get_openai_client().files.create(purpose="assistants")` and vector stores through the same client (`vector_stores.create`, `vector_stores.files.create`) — the upload cache (sha256 → file id) is unchanged | cache hit rate in the log |
| A5 | `scripts/memory_store.py` | same client; store is `vs-assurance-memory` (staging) or the Search index `MEMORY_INDEX_NAME`, per `MEMORY_BACKEND` (§C) | `memory_store.py list` |
| A6 | `deploy.sh` | **Applied as step `[0b/8]`** (`STRICT_RUNTIME=1` makes it blocking). Original **S-10**: step `[0/7] runtime pre-flight` — `python3 -c "import azure.ai.projects as p, sys; sys.exit(0 if p.__version__.split('.')[0]=='2' else 1)"` | dry run |

Reference shape (validated with `py_compile`; confirm parameter names
against the 2.x samples of the migrate page on the execution day):

```python
# series-06-runtime-shape.py — new-runtime calls used by the migrated scripts
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition
from azure.identity import DefaultAzureCredential


def create_or_version(project: AIProjectClient, name: str, model: str, instructions: str, tools: list):
    """Every call creates a new immutable version <name>:<n>; the previous versions stay."""
    return project.agents.create_version(
        agent_name=name,
        definition=PromptAgentDefinition(model=model, instructions=instructions, tools=tools),
    )


def ask(project: AIProjectClient, name: str, prompt: str, conversation_id: str | None = None):
    client = project.get_openai_client()
    conv_id = conversation_id or client.conversations.create().id
    resp = client.responses.create(
        conversation=conv_id,
        input=prompt,
        extra_body={"agent_reference": {"name": name, "type": "agent_reference"}},
    )
    return conv_id, resp.output_text, resp.status


if __name__ == "__main__":
    import os
    p = AIProjectClient(endpoint=os.environ["PROJECT_ENDPOINT"], credential=DefaultAzureCredential())
    print(ask(p, "dora", "Name three DORA Art. 30(2) baseline contractual provisions.")[1])
```

## B. Conversion and deployment chain (per environment)

| # | Command (from `convertion/`) | What it proves |
|---|---|---|
| B1 | `python3 scripts/convert_skills.py` | export → `build/agents/*` + `build/manifest.json` (offline, deterministic) |
| B2 | `python3 scripts/verify_conversion.py` | templates, thresholds, scripts byte-identical to the claude.ai originals; secret grep; coverage |
| B3 | `python3 scripts/create_agents.py --dry-run` then live | 35 agents: persona preamble + instructions + APPROVAL GATE block; per-agent vector store `vs-<agent>`; code_interpreter files |
| B4 | `python3 scripts/attach_integrations.py --dry-run` then live | read-only tools + model tiers from `integrations/registry.json` (connections of step 04) |
| B5 | `python3 scripts/create_delivery_agents.py` then `attach_integrations.py` again | `ciso-global-report`, `tpa-evidence-analyzer`, `soc-report-analyzer`, `pentest-report-analyzer`, `template-manager` |
| B6 | `python3 scripts/create_orchestrator.py` | advisor + orchestrator (§D) + memory notes store |
| B7 | `python3 scripts/apply_advisory_profile.py` | advisory addendum + code_interpreter on the g/h/i agents; `reasoning` tier pin |
| B8 | `python3 scripts/stage_renderers.py` | renderers for step 05's Function |
| B9 | `python3 scripts/smoke_test.py --agent infosec-assurance-orchestrator --prompt "One-line health check: name three DORA Art. 30(2) baseline contractual provisions."` | end-to-end answer (same prompt as `deploy.sh` step 7 and `operations/RUNBOOK.md` W1) |

`./deploy.sh` runs B1–B9 in order and stops at the first failure
(`--dry-run` for the offline rehearsal). In `test`/`prod` it runs from the
deploy pipeline under `{app:infosec-foundry-deployer}`, never from a
workstation (`operations/CHANGE_MANAGEMENT.md` §2).

## C. Advisor stores (D5)

> **Implemented differently from the first draft — this is the shape of record.**
> `scripts/create_orchestrator.py` attaches exactly ONE `file_search` store to
> the advisor and it keeps its existing name **`vs-assurance-combined`** (all
> skill knowledge + advisor knowledge packs). It is NOT renamed to
> `vs-assurance-advisor`, and memory notes do **not** live inside it as
> `MEMORY-*` files.

One vector store per agent is a fixed service limit (limits page, 2026-09-07,
GA), so durable memory cannot be a second `file_search` store. Two switches in
`setup/.env` decide where each thing comes from:

| Switch | Values | Effect |
|---|---|---|
| `KNOWLEDGE_SOURCE` | `vector-store` (default) / `ai-search` / `none` | combined knowledge from `vs-assurance-combined`, or from the Azure AI Search / Foundry IQ index `KNOWLEDGE_INDEX_NAME` (default `kb-assurance`), or not grounded |
| `MEMORY_BACKEND` | `vector-store` (transition default) / `search-index` | durable memory in `vs-assurance-memory` as a **staging store managed by `scripts/memory_store.py` and no longer attached to the advisor**, or as documents in the Azure AI Search index `MEMORY_INDEX_NAME` (default `kb-assurance-memory`) read through the GA Azure AI Search tool |

`scripts/memory_store.py` implements `add` / `list` / `delete` / `import` /
`purge` identically on both backends with the same privacy filter, the same
special-category rejection and the same `--approved-by` gate
(`governance/MEMORY_POLICY.md` §2a). Deletion stays per note, so GDPR
minimisation is unchanged. Moving `MEMORY_BACKEND` from `vector-store` to
`search-index` is a Tier C change: export first
(`operations/BACKUP_DR.md` §3), then re-import.

The Foundry IQ knowledge-base route is evaluated in `test` and adopted as a
Tier C change if retrieval quality on the comparison set is equal or better.

## D. Multi-agent routing without connected agents (D2)

| Component today | v1 implementation | Later |
|---|---|---|
| `infosec-assurance-orchestrator` (connected to every agent) | prompt agent that **answers directly** from the advisor knowledge and, when a specialist is needed, returns a structured `ROUTE: <agent-name>` line; callers (MCP `ask_orchestrator`, Copilot wrapper, `workflows/agent-fanout.json`) perform the hand-off as a second `responses.create` on the named agent — deterministic, traceable, read-only | A2A tool (preview) piloted in `test`; Agent Framework 1.0 hosted orchestrator as the GA candidate (Q1 2027 Tier C change) |
| `enx-tprm-control-center` router | same pattern (menu → `ROUTE:`); stays `light` tier, no tools | as above |
| `workflows/agent-fanout.json` | unchanged semantics (parallel specialist responses + orchestrator synthesis) on the new endpoints (step 07) | — |

`create_orchestrator.py` therefore stops emitting `ConnectedAgentTool`
definitions and instead injects the live agent list (name + description)
into the orchestrator's instructions as the routing table — re-run it after
adding agents, exactly as today.

## E. Click-path

**Foundry portal.** *Build* → **Agents** → the list shows every agent
created by the scripts with its versions; open `dora` → *Instructions*
(persona preamble + APPROVAL GATE visible), *Tools* (file search store,
code interpreter, the read-only OpenAPI/MCP tools), *Model* (tier
deployment) → *Try in playground* (upload a public PDF, ask a question) →
*Versions* → set **active version** = the one `deploy.sh` created (never
"always use latest" in `prod`). *Build* → **Tracing** shows the run. No
agent is edited in the portal: a portal edit creates a version the
`agent_modified_by_non_deploy_identity` alert flags (`operations/MONITORING.md` §4).

## F. Values captured into `setup/.env`

The kit does **not** use `ADVISOR_VECTOR_STORE_ID` — the advisor's store is
resolved by NAME. The implemented keys are:

| Variable | Value |
|---|---|
| `FOUNDRY_API_VERSION` | `v1` |
| `ORCHESTRATOR_AGENT_NAME`, `VERIFIER_AGENT_NAME` | `infosec-assurance-orchestrator`, `output-verifier` (names, not ids — the new API addresses agents by `name:version`; `workflows/pipelines.json` `agent` keys already use names) |
| `KNOWLEDGE_SOURCE` | `vector-store` \| `ai-search` \| `none` (§C) |
| `MEMORY_BACKEND` | `vector-store` \| `search-index` (§C) |
| `SEARCH_SERVICE_ENDPOINT` | endpoint of the Azure AI Search service (empty until `ai-search` / `search-index` is selected) |
| `SEARCH_CONNECTION_NAME` | `ai-search` — the project connection of category `CognitiveSearch`; `infra/main.bicep` `searchConnectionName` must match |
| `KNOWLEDGE_INDEX_NAME` | `kb-assurance` (alias accepted: `KNOWLEDGE_BASE_NAME`) |
| `MEMORY_INDEX_NAME` | `kb-assurance-memory` |
| `ENABLE_A2A_TOOL` | `false` — attach the A2A tool (preview) alongside the ROUTE table |

## G. Verification

| # | Check | Pass when |
|---|---|---|
| V1 | `deploy.sh --dry-run` | completes; `[0/7]` pre-flight passes (SDK major 2) |
| V2 | `verify_conversion.py` | exit 0; secret grep clean |
| V3 | `grep -rn "APPROVAL GATE" build/agents/*/instructions.md \| wc -l` | = number of agents (`governance/HUMAN_APPROVAL.md` "Verifying the control") |
| V4 | `attach_integrations.py --dry-run` | `[read-only]` on every OpenAPI tool; no `write_connections` |
| V5 | Comparison set (`operations/CHANGE_MANAGEMENT.md` §4): the known assessments through `dpia`, `ciso-reporting`, `ciso-global-report`, `deepsearch-protocol`, `soc-report-analyzer`, `pentest-report-analyzer` | rendered files byte-identical (deterministic renderers) and JSON contracts equal on scores/thresholds |
| V6 | Verifier: a draft with a missing section | first line `VERDICT: FAIL` |
| V7 | Routing: `smoke_test.py --agent infosec-assurance-orchestrator --prompt "Assess the security of {public-supplier-domain}"` | reply contains `ROUTE: deepsearch-protocol` |
| V8 | Portal: each agent has exactly one active version equal to the deploy log | screenshot |
| V9 | UAT (`test`): the four users each run one advisory question and one pipeline (step 07) and sign `Governance/Implementation/test/06/uat-{upn}.md` | four sign-offs |
| V10 | Tool-support: every advisory agent's model shows the OpenAPI/MCP/Web Search tools attached without error (D3) | portal *Tools* tab; one live tool call in tracing |

**Rollback.** Set the active version back to the previous number (portal
*Versions*, or the version selector via SDK) — no redeploy needed; for a
whole release, `deploy.sh` from the previous tag creates new versions with
the old content. **ISMS evidence.** deploy log, `verify_conversion.py`
output, V5 comparison table, UAT sign-offs — ISO 42001 A.6.2.4–A.6.2.6
(deployment, operation, monitoring), A.8.4; EU AI Act Art. 9, Art. 26;
ISO 27001:2022 A.8.32; DORA Art. 9(2).

## Sources
- [GA] Migration guide — https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/migrate (2026-08-05)
- [GA] SDK overview / changelog — https://learn.microsoft.com/en-us/azure/foundry/how-to/develop/sdk-overview (2026-08-26); https://github.com/Azure/azure-sdk-for-python/blob/main/sdk/ai/azure-ai-projects/CHANGELOG.md (2026-09-04)
- [GA] Agent overview, lifecycle, versioning — https://learn.microsoft.com/en-us/azure/foundry/agents/overview (2026-08-19); https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/development-lifecycle (2026-08-27)
- [preview] A2A tool — https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/agent-to-agent (2026-09-04)
- [GA] Agent Framework 1.0 — https://devblogs.microsoft.com/agent-framework/microsoft-agent-framework-version-1-0/ (2026-04-03)
- [GA] File search / limits — https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/file-search (2026-08-05); https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/limits-quotas-regions (2026-09-07)
- [GA] Code Interpreter — https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/code-interpreter (2026-08-05)
- [preview] Memory; Agent Optimizer — https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/what-is-memory (2026-06-04); https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/agent-optimizer-overview (2026-08-19)
