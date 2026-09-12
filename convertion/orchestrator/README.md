# Orchestrator, Assurance Advisor, and MCP Access

The layer the InfoSec Assurance team actually talks to. Three components on
top of the 22 converted agents:

```
 team member ──► MCP server (mcp-server/) ─────────┐
 Teams/Copilot ──► Copilot connector ──────────────┤
 Logic Apps workflows ─────────────────────────────┤
                                                   ▼
                        ┌──────────────────────────────────┐
                        │  infosec-assurance-orchestrator  │  reasoning model
                        │  (A2A hand-offs: ALL below)      │  + web search
                        └───────┬──────────────────────────┘
                ┌───────────────┼──────────────────────────┐
                ▼               ▼                          ▼
   infosec-assurance-advisor   22 specialist agents   enx-tprm-control-center
   (reasoning + memory +       (dora, dpia, deepsearch,   (TPRM sub-router)
    combined knowledge)         ciso-reporting, ...)
```

## 1. `infosec-assurance-orchestrator`

Single entry point. Runs on the **reasoning deployment** (`o3-mini` by
default; must be a tool-capable reasoning model — `../governance/MODEL_ROUTING.md`)
with **web search** and **A2A hand-offs to every published agent** (Connected
Agents do not exist on the current Agent Service; Microsoft Agent Framework
orchestration is the production path — `../enterprise/ENTERPRISE_BLUEPRINT.md`
ORC-1), so it can answer directly, decompose a request across specialists,
or hand off wholesale (a OneTrust PDF → `dpia`; a supplier domain →
`deepsearch-protocol`). Created by `scripts/create_orchestrator.py`, which
discovers the live agents at run time — re-run it after adding agents and
the wiring refreshes.

**Routing contract.** Connected agents do not exist on the Agent Service
(finding C2). `create_orchestrator.py` injects a deploy-time **ROUTING TABLE**
(name + one-line description of every live agent) into the orchestrator's
instructions; the orchestrator answers `ROUTE: <agent-name>` and the CALLER
performs the hand-off as a second `responses.create` on that agent, in the
same conversation. The three callers that implement it are
`../mcp-server/server.py` (`ask_orchestrator`),
`../integrations/copilot/function/function_app.py` (`/api/ask`) and
`../workflows/agent-fanout.json`. The A2A tool (preview) is attached *in
addition* when `ENABLE_A2A_TOOL=true` and the pinned SDK exposes it.

## 2. `infosec-assurance-advisor` — the reasoning generalist

The agent that "answers all themes of the persona": ISO/IEC 27001/27002/
27005, NIST CSF 2.0, CIS v8.1, GDPR Art. 28/SCCs, DORA, NIS2, EU AI Act,
ISO 42001, ITIL/COBIT/COSO/TOGAF/PMBOK, cloud and ICT service assurance.

- **Model:** the reasoning deployment.
- **Knowledge:** ONE combined vector store built from every skill's
  knowledge files (all references, catalogues, mappings across the 22
  agents) — the advisor cites which source document grounds each answer.
- **Web search:** Bing grounding for current threats/regulatory news —
  a **global** service outside the Azure compliance boundary (the Azure
  DPA does not apply to it), so sanitised public queries only, never
  internal identifiers, scores or quoted internal text. Accepted
  residual risk with the persona egress rule and the KQL
  internal-marker alert as controls
  (`../governance/DATA_PROTECTION_GUARDRAILS.md` §1).
- **Memory:**
  - *Session memory* — one Foundry **conversation** per (person, supplier,
    service, engagement) (`../team/TEAM_MODEL.md` §13); the current Agent
    Service runtime uses conversations and responses, and classic
    threads/runs retire 2027-03-31.
  - *Durable memory* — the Azure AI Search index `kb-assurance-memory`,
    reached through the AI Search tool beside the single `file_search`
    knowledge store (the service allows one vector store per agent — limits
    page, 2026-09-07; `vs-assurance-memory` is the transition backend,
    `../enterprise/MEMORY_AND_LEARNING.md` §2). The advisor's instructions tell
    it to consult memory first and to end substantive sessions by emitting a
    fenced `MEMORY:` block (decisions, supplier facts, positions taken);
    `scripts/memory_store.py add` writes those notes into the store (run
    manually, from a Logic App step, or from the MCP server's `save_memory`
    tool). Notes are timestamped files — auditable and deletable, which
    matters for GDPR minimisation.

    The service allows one vector store per agent, so `vs-assurance-memory` is
    no longer attached to the advisor: with `MEMORY_BACKEND=vector-store` it is
    a staging store managed by `scripts/memory_store.py`, and with
    `MEMORY_BACKEND=search-index` memory is served from the Azure AI Search
    index `MEMORY_INDEX_NAME` (default `kb-assurance-memory`) through the GA
    Azure AI Search tool (finding C3).

Charter lives in `../agents/advisor_instructions.md` (persona preamble is
prepended automatically, as for every agent).

## 3. MCP server (`../mcp-server/`)

Exposes the environment to any MCP client — Claude Desktop/Code, the ENX
gateway, or internal tooling: `ask_orchestrator`, `ask_agent`,
`list_agents`, `save_memory`, `search_memory`. Runs locally (stdio) for a
team member, or on Azure Container Apps behind Entra auth for shared use.
This is the reverse bridge: the Claude side keeps its skills, and can now
also drive the Foundry deployment through one MCP connection.

## Deploy order

```bash
python3 ../scripts/convert_skills.py            # [1]  export -> build/
python3 ../scripts/build_self_knowledge.py      # [1b] regenerate the self-knowledge pack
                                                #      (re-run [1] when it changed)
python3 ../scripts/verify_conversion.py         # [2]  fidelity, decisions, read-only audit
python3 ../scripts/verify_kit.py                #      kit consistency + secret scan
python3 ../scripts/create_agents.py --skip-routers   # [3] agents, ROUTE tables left empty
python3 ../scripts/create_delivery_agents.py    # [4]  the five delivery agents
python3 ../scripts/create_agents.py --rewire    # [4b] ROUTE tables, now that the targets exist
python3 ../scripts/create_orchestrator.py       # [5]  advisor + orchestrator + memory store
python3 ../scripts/apply_advisory_profile.py    #      advisory addendum + combined knowledge
python3 ../scripts/attach_integrations.py       # [6]  ONCE, after every agent exists
python3 ../scripts/stage_renderers.py --strict  #      renderers for the delivery Function
python3 ../scripts/memory_store.py list         #      verify the memory store
```

Order matters in two places, and both are the same mistake in different
clothes: **`attach_integrations.py` runs once, after every agent exists** (it
refuses live agents with no registry entry, so running it early reports agents
that simply have not been created yet), and **the ROUTE tables are wired in
[4b], not [3]** — a router built before `create_delivery_agents.py` would point
at agents that do not exist. `../deploy.sh` runs exactly this sequence.

## Governance

The advisor's durable memory is a personal-data-adjacent store (it may hold
names, supplier facts, internal positions): include it in RoPA/retention
schedules, restrict who can run `memory_store.py`, and review its contents
periodically. Both new agents inherit the ISO 42001 / EU AI Act deployer
obligations noted in the main README.
