# Azure AI Foundry Conversion

This folder converts the Claude account export in `../claude-account-export/`
into a deployable **Azure AI Foundry** environment that replicates the same
toolset: every skill becomes a Foundry **Agent** with its instructions,
knowledge files, and scripts; the persona becomes a shared system-prompt
preamble; the infrastructure is provisioned with Bicep.

## Concept mapping

| Claude concept | Azure AI Foundry equivalent |
|---|---|
| Skill (`SKILL.md` instructions + trigger description) | Agent (Agent Service): `instructions`, with the trigger description kept as the agent description for routing |
| Skill `references/` (knowledge, mappings, catalogues) | Files uploaded to a per-agent **vector store**, attached via the **file_search** tool (RAG) |
| Skill `scripts/` (Python/JS generators) | Attached as files to the **code_interpreter** tool; the instructions tell the agent to run them |
| Skill `assets/` (templates, constants) | code_interpreter files (consumed by the scripts) |
| Persona / user preferences (`PERSONA.md`) | Shared system-prompt preamble prepended to every agent's instructions |
| Router skill (`enx-tprm-control-center`) | **Connected agents**: a router agent that hands off to the worker agents |
| Claude model | An Azure model deployment (default `gpt-4o` from the Foundry model catalog) — **Claude models are not available on Azure**; see Limitations |
| claude.ai skill sync | `scripts/convert_skills.py` + `scripts/create_agents.py` (re-run to re-sync) |

## Folder layout

```
convertion/
├── README.md                  ← this file
├── MAPPING.md                 ← per-skill conversion table (all 35 skills)
├── infra/
│   ├── main.bicep             ← Foundry account + project + model deployment + storage
│   └── main.parameters.json
├── setup/
│   ├── provision.sh           ← az CLI: resource group + Bicep deployment
│   ├── requirements.txt       ← Python deps for the scripts
│   └── .env.example           ← environment variables template
├── agents/
│   └── persona_system_prompt.md  ← shared persona preamble
└── scripts/
    ├── convert_skills.py      ← export → build/agents/ (instructions, knowledge, manifest)
    ├── create_agents.py       ← build/agents/ → live Foundry agents (SDK)
    └── smoke_test.py          ← sends a test prompt to one converted agent
```

## Deployment — five steps

```bash
# 0. Prerequisites: Azure CLI (az login), Python 3.10+, an Azure subscription
#    with access to Azure AI Foundry and the chosen model region.

# 1. Provision infrastructure (resource group, Foundry account+project, model)
cd convertion/setup
cp .env.example .env            # fill in subscription, region, names
./provision.sh

# 2. Install script dependencies
pip install -r requirements.txt

# 3. Convert the export into agent definitions (offline, deterministic)
cd ../scripts
python3 convert_skills.py       # writes ../build/agents/ + manifest.json

# 4. Create the agents in Foundry (uploads knowledge, attaches tools)
python3 create_agents.py        # uses PROJECT_ENDPOINT from .env / environment

# 5. Attach integrations + model tiers (Jira, OneTrust, Defender, SharePoint,
#    SecurityScorecard, IAF API, ENX gateway MCP, Bing web search, o3-mini
#    reasoning) — after creating the conn-* Foundry connections; see
#    integrations/README.md
python3 attach_integrations.py

# 6. Create the flagship layer: assurance advisor (reasoning + combined
#    knowledge + durable memory) and orchestrator (routes across all agents)
python3 create_orchestrator.py

# 7. Verify
python3 smoke_test.py --agent infosec-assurance-orchestrator \
    --prompt "Summarise DORA Art. 30 contractual provisions"
```

## Integrations, workflows, Copilot

The `integrations/` folder wires the agents into the Euronext toolchain —
Jira Cloud, Jira Assets (CMDB), OneTrust, SecurityScorecard, Microsoft
Defender (Graph security), SharePoint (Graph), the internal IAF API, the ENX
gateway MCP server, Grounding-with-Bing web search, and an `o3-mini`
reasoning tier for analytic agents (see `integrations/README.md` and
`integrations/registry.json`). `workflows/` holds Logic Apps definitions
replacing Claude Routines (OneTrust intake, Defender incident briefs,
scheduled DeepSearch, Jira↔IAF sync), and `integrations/copilot/` documents
surfacing the agents in Microsoft 365 Copilot.

## Orchestrator, advisor with memory, MCP access

`orchestrator/README.md` describes the flagship layer: the
`infosec-assurance-orchestrator` (single entry point, reasoning model,
connected to every agent), the `infosec-assurance-advisor` (reasoning
generalist across all persona domains, grounded in a combined vector store
of every skill's knowledge, with durable team memory in
`vs-assurance-memory` managed by `scripts/memory_store.py`), and the MCP
server in `mcp-server/` that exposes the whole environment to any MCP
client (Claude included) via `ask_orchestrator` / `ask_agent` /
`save_memory` / `search_memory`.

Re-running steps 3–4 is idempotent by agent name: existing agents are updated
in place (instructions and knowledge refreshed), new skills become new agents.

## What gets created in Azure

- 1 resource group
- 1 Azure AI Foundry account (`Microsoft.CognitiveServices`, kind `AIServices`)
  with 1 Foundry **project**
- 1 model deployment (default `gpt-4o`; change in `main.parameters.json`)
- 35 agents (18 custom GRC/TPRM + 4 document + 13 general), each with:
  - the persona preamble + its skill's instructions
  - a vector store with its `references/` files (where the skill has any)
  - code_interpreter with its `scripts/` and `assets/` files (where present)
- 1 router agent (`enx-tprm-control-center`) wired to its five worker agents
  via connected-agent tools

## Limitations and honest deltas

1. **Model:** Anthropic Claude models are not offered in the Azure model
   catalog. Agents default to `gpt-4o`. Instruction-following and output
   style will differ; validate the report-generating agents (ciso-reporting,
   deepsearch, slide generators) against known-good outputs before relying on
   them. If Claude fidelity is mandatory, keep those workloads on claude.ai /
   Claude API and use Foundry for the rest — the converter lets you deploy a
   subset (`--only`).
2. **Skill triggering:** Claude auto-selects skills from their descriptions.
   In Foundry, selection is explicit (you invoke an agent) or routed through
   the router agent / your application layer.
3. **JS scripts:** code_interpreter executes Python only. Skills whose
   generators are Node.js (the pptx slide generators) have their JS attached
   as reference material; the converter flags them in the manifest
   (`"requires_external_runtime": true`) — run those generators in an Azure
   Function or container job if you need them server-side.
4. **Local-hardware skills:** `whisperx-transcribe-diarize` targets local
   Apple-Silicon execution; in Azure use AI Foundry Speech (batch
   transcription + diarization) instead. It is converted as knowledge-only.
5. **Connectors:** Gmail/Drive/Adobe-style connectors have no direct
   equivalent inside an agent; use Azure Logic Apps or OpenAPI tools per
   integration (out of scope here, documented in MAPPING.md).
6. **SDK drift:** `azure-ai-projects` evolves quickly; versions are pinned in
   `setup/requirements.txt`. If a call signature has moved, check the
   migration notes for the pinned major version.

## Governance note (ISO 42001 / EU AI Act)

Deploying these agents on Azure makes your organisation the **deployer** (and
for substantially modified systems potentially the provider) of the AI
systems under the EU AI Act, and brings them into scope of your AIMS if you
run ISO/IEC 42001. The exported `iso42001` and `eu-ai-act` agents themselves
contain the reference material to run that assessment; do it before
production use. Log and monitor via Azure AI Foundry's built-in tracing +
Azure Monitor.
