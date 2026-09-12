# Microsoft Foundry Conversion

This folder converts the Claude account export in `../claude-account-export/`
into a deployable **Microsoft Foundry (formerly Azure AI Foundry)**
environment that replicates the same toolset: every skill becomes a Foundry
**Agent** with its instructions, knowledge files, and scripts; the persona
becomes a shared system-prompt preamble; the infrastructure is provisioned
with Bicep. The rest of this file says "Foundry" for short; the Azure
resource provider is still `Microsoft.CognitiveServices`.

Runtime vocabulary follows the current Agent Service: a session is a
**conversation** and a model call is a **response** (classic threads/runs
retire 2027-03-31 — `enterprise/ENTERPRISE_BLUEPRINT.md` PRJ-2).

## Concept mapping

| Claude concept | Microsoft Foundry equivalent |
|---|---|
| Skill (`SKILL.md` instructions + trigger description) | Agent (Agent Service): `instructions`, with the trigger description kept as the agent description for routing |
| Skill `references/` (knowledge, mappings, catalogues) | Files uploaded to the agent's **vector store**, attached via the **file_search** tool (RAG). The service allows **one vector store per agent**, so shared/combined knowledge and durable memory move to an Azure AI Search index / Foundry IQ knowledge base — `enterprise/MEMORY_AND_LEARNING.md` §2 |
| Skill `scripts/` (Python/JS generators) | Attached as files to the **code_interpreter** tool; the instructions tell the agent to run them |
| Skill `assets/` (templates, constants) | code_interpreter files (consumed by the scripts) |
| Persona / user preferences (`PERSONA.md`) | Shared system-prompt preamble prepended to every agent's instructions |
| Router skill (`enx-tprm-control-center`) | **A2A hand-offs**: a router agent that hands off to the published worker agents. Connected Agents do not exist on the current Agent Service; the production path is Microsoft Agent Framework orchestration with the verifier and the approval gate as explicit steps (`enterprise/ENTERPRISE_BLUEPRINT.md` ORC-1) |
| Claude chat session / thread | Foundry **conversation** (+ `responses`); classic threads/runs retire 2027-03-31 |
| Claude model | An Azure model deployment (default `gpt-4o` from the Foundry model catalog). Claude models **are** offered on Microsoft Foundry; they are excluded here by the **EU residency rule**, not by availability — correction of record, `*ModelFormat` parameters and the tier-switch procedure in `governance/CLAUDE_ON_FOUNDRY.md` (summarised in Limitation 1) |
| claude.ai skill sync | `scripts/convert_skills.py` + `scripts/create_agents.py` (re-run to re-sync) |

## Folder layout

```
convertion/
├── README.md · MAPPING.md · ARCHITECTURE.md · REQUIREMENTS.md   ← kit docs
├── deploy.sh                  ← convert → verify → create → integrate → smoke
├── infra/                     ← main.bicep (+ agent-stores, network, delivery,
│                                monitoring, guard, cost, defender-ai, logicapp,
│                                mcp-server, static-web-app, private-endpoint,
│                                workload-rbac), main.parameters*.json,
│                                validate.sh, kql/
├── enterprise/                ← ENTERPRISE_BLUEPRINT, PORTAL_CONFIGURATION,
│                                MEMORY_AND_LEARNING, UPDATE_AND_UPGRADE_REVIEW_POLICY,
│                                IMPLEMENTATION_SERIES, landing-zone.bicep,
│                                azure-policy-assignments.bicep, portal/, series/,
│                                memory/, memory-learning/, upgrade/
├── setup/                     ← provision.sh, requirements.txt, .env.example
├── agents/                    ← persona_system_prompt.md, addenda, overlays/,
│                                knowledge-packs/, advisor-knowledge/,
│                                12 charters (`*_instructions.md`)
├── scripts/                   ← 22 Python tools (convert, create, attach, verify,
│                                update_templates, memory_store, …) + adapters/
├── build/                     ← generated: agents/ (22), manifest.json,
│                                instruction-hashes.json, learning/
├── integrations/              ← registry.json, 15 OpenAPI specs (openapi/),
│                                mcp/, connections/, copilot/, CONNECTOR_DECISIONS.md
├── workflows/                 ← 17 Logic App definitions + pipelines.json
├── ci/                        ← CI/CD: the gate script syntax_check.sh shared by
│                                both pipelines, the Azure DevOps pipeline
│                                azure-pipelines.yml, deploy_logicapps.sh, and
│                                README.md explaining the PR gates, the OIDC
│                                deploy and the secret scan
├── functions/
│   ├── delivery/              ← renderer + SharePoint storage Function (holds the
│   │                            managed identity: Graph, Foundry, Document Intelligence)
│   └── office-tools/          ← the binary document toolchain as a SECOND container
│                                (LibreOffice/soffice, pandoc, poppler, qpdf, tesseract,
│                                ImageMagick): /api/convert, /api/recalc (the xlsx formula
│                                gate), /api/accept_changes, /api/thumbnail, /api/validate.
│                                No Azure credential, no outbound call, key-protected, and
│                                never an agent tool — the pipeline calls it
├── mcp-server/                ← MCP exposure of the platform (+ evals/)
├── templates/                 ← registry.json, 11 deliverable schemas, skill-decisions.json
│                                (the machine form of MAPPING.md + governance/
│                                PLATFORM_SKILLS_DECISION.md), themes/, assets/, samples/
├── governance/                ← 11 governance docs + index README
├── operations/                ← day-2 operation of the delivered systems
│   ├── RUNBOOK.md, SUPPORT_MODEL.md, CHANGE_MANAGEMENT.md, MONITORING.md
│   ├── FINOPS.md, TOKEN_ECONOMY_PLAYBOOK.md, cost-budget.bicep
│   ├── LIFECYCLE.md, BACKUP_DR.md, backup_vector_stores.py, backup-job.bicep
│   ├── RETENTION_AND_CLEANUP.md   ← monthly housekeeping: orphan stores/files, idle
│   │                            conversations, memory notes past retain_until
│   ├── ROLLOUT_PLAN.md, KPIS.md, CONTINUOUS_IMPROVEMENT.md
│   ├── evaluation/            ← golden set, EVALUATION.md, run_evals.py (gates)
│   ├── access-governance/     ← lifecycle, quarterly review, break-glass
│   ├── kql/                   ← egress, verifier fail rate, latency+tokens, SLA
│   └── alerts.bicep           ← extended alert catalogue (see MONITORING.md §4)
├── team/                      ← team model, RACI, RBAC, access register, onboarding
│   ├── USER_QUICKSTART.md     ← per-user guide to systems a–j (inputs, path, tier)
│   ├── entra-groups.md, sharepoint-permissions.md ← executable identity /
│   │                            site-permission setup
│   └── least-privilege/       ← historical design variant (see its README)
├── evaluation/                ← golden/ and smoke/ sets
├── orchestrator/              ← orchestrator + advisor + MCP layer README
└── sharepoint/                ← `Reports/<Supplier>/<Service>/` storage rules

(repo root, outside this folder)
├── .github/                   ← workflows/ci.yml (offline gates on every PR),
│                                workflows/deploy.yml (the ONLY path that talks
│                                to Azure: workflow_run after a green CI on
│                                `main`, `environment: production` approval,
│                                OIDC), workflows/nightly-drift.yml (nightly
│                                drift + access snapshot, read-only identity);
│                                CODEOWNERS, PULL_REQUEST_TEMPLATE.md,
│                                gitleaks.toml, dependabot.yml
├── .gitleaks.toml             ← root shim: `[extend] path` → .github/gitleaks.toml
│                                so a scan run without --config uses the same
│                                allow-list (pre-commit, `gitleaks protect`)
├── .pre-commit-config.yaml    ← local, non-authoritative mirror of the CI gates
└── .devcontainer/             ← dev container mirroring the CI toolchain
```

## Deployment — step by step (`deploy.sh` runs the same sequence)

```bash
# 0. Prerequisites: Azure CLI (az login), Python 3.10+, an Azure subscription
#    with access to Microsoft Foundry and the chosen model region.

# 1. Provision infrastructure (resource group, Foundry account+project, model)
cd convertion/setup
cp .env.example .env            # fill in subscription, region, names
#    Runtime keys to review before the first deploy (all documented in
#    .env.example): FOUNDRY_API_VERSION=v1, KNOWLEDGE_SOURCE, MEMORY_BACKEND,
#    SEARCH_SERVICE_ENDPOINT, SEARCH_CONNECTION_NAME, KNOWLEDGE_INDEX_NAME,
#    MEMORY_INDEX_NAME, ENABLE_A2A_TOOL, REASONING_MODEL_DEPLOYMENT_NAME
#    (o4-mini — never o3-mini, finding C4).
./provision.sh

# 2. Install script dependencies
pip install -r requirements.txt

# 3. Convert the export into agent definitions (offline, deterministic)
cd ../scripts
python3 convert_skills.py       # writes ../build/agents/ + manifest.json

# 4. Create the agents in Foundry (uploads knowledge, attaches tools)
python3 create_agents.py        # uses PROJECT_ENDPOINT from .env / environment

# 5. Attach integrations + model tiers (Jira, OneTrust, Defender, SharePoint,
#    SecurityScorecard, IAF API, ENX gateway MCP, web search, and the
#    tool-capable reasoning tier — governance/MODEL_ROUTING.md holds the
The full governance index is `governance/README.md` — including `RISK_THRESHOLDS.md`
(which scale belongs to which deliverable), `PLATFORM_SKILLS_DECISION.md`,
`CLAUDE_ON_FOUNDRY.md`, `MEMORY_POLICY.md`, `MEMORY_IMPORT.md`,
`M365_DOCUMENT_EDITING.md` and `THIRD_PARTY_IP.md` (the Anthropic-licensed skills —
the IP decision is still open and the conversion of those seven agents is gated on it).
#    tool-compatibility matrix) — after creating the conn-* Foundry
#    connections; see integrations/README.md
python3 attach_integrations.py

# 6. Create the flagship layer: assurance advisor (reasoning tier + the
#    combined knowledge store; durable memory served from the
#    kb-assurance-memory Azure AI Search index — one vector store per agent)
#    and orchestrator (A2A hand-offs across all agents)
python3 create_orchestrator.py

# 7. Verify
python3 smoke_test.py --agent infosec-assurance-orchestrator \
    --prompt "Summarise DORA Art. 30 contractual provisions"
```

## Delivery layer (requirements a–j)

`REQUIREMENTS.md` traces the full business-requirement set to its
components. In one paragraph: twelve **report-delivery pipelines**
(`workflows/report-delivery-pipeline.json` + `workflows/pipelines.json`)
take a supplier name + service name, run the producing agent, pass the
draft through the output-verifier and the human approval gate, render the
file (HTML/DOCX/PPTX/XLSX) in the **delivery Function**
(`functions/delivery/`) — which calls the second container,
`functions/office-tools/`, for anything needing the binary toolchain
(LibreOffice/pandoc/poppler conversion, the mandatory xlsx `/api/recalc`
formula gate, tracked-change flattening, slide thumbnails, OOXML
validation) — and store it in SharePoint under
`Reports/<Supplier>/<Service>/` with the idempotent folder rule (reuse
the supplier folder when it exists, create the service folder only when
missing — `sharepoint/README.md`). Five **new agents** extend the
converted set:
`ciso-global-report` (Global CISO 9-slide deck), `tpa-evidence-analyzer`
(TPA/Active evidence tree analysis), `soc-report-analyzer`,
`pentest-report-analyzer`, and `template-manager` (approval-gated template
change control with visual before/after review —
`workflows/template-update-approval.json`, `templates/registry.json`,
`scripts/update_templates.py`). Read-only Confluence access joins the
integration set for the advisor (requirement i), egress and data
protection are specified in `governance/DATA_PROTECTION_GUARDRAILS.md`,
and token-economy model routing in `governance/MODEL_ROUTING.md`.

## Integrations, workflows, Copilot

The `integrations/` folder wires the agents into the Euronext toolchain —
Jira Cloud, Jira Assets (CMDB), OneTrust, SecurityScorecard, Microsoft
Defender (Graph security), SharePoint (Graph), the internal IAF API, the ENX
gateway MCP server, web search, and a reasoning tier for analytic agents
(15 OpenAPI specs in `integrations/openapi/`; tiers, tools and connections
in `integrations/registry.json`; the tool-compatibility matrix that decides
which reasoning model may carry those tools is
`governance/MODEL_ROUTING.md`). `workflows/` holds 17 Logic Apps
definitions plus `pipelines.json`, replacing Claude Routines (OneTrust
intake, Defender incident briefs, scheduled DeepSearch, Jira↔IAF sync,
scheduled evaluation/red-team, approval and delivery pipelines), and
`integrations/copilot/` documents the **native publish to Microsoft Teams
and Microsoft 365 Copilot** (`enterprise/ENTERPRISE_BLUEPRINT.md` CP-1).

**Web egress, stated plainly.** Grounding with Bing Search and the
allow-listed `osint-proxy` page fetch are the *only* routes out to the web;
no generic HTTP or browser tool exists on any agent. Bing grounding is a
**global** service: the sanitised query leaves the Azure compliance
boundary and **the Azure Data Protection Addendum does not apply to it**, so
EU residency is not guaranteed for the query text. Queries may therefore
carry public facts only — supplier and product names, CVE ids, regulation
references — never internal identifiers, scores, findings or quoted
internal text. This is an **accepted residual risk** owned by the
accountable owner, recorded on the `web-search` connection in
`integrations/registry.json`, in the RoPA and in the DORA Art. 28 register,
and re-reviewed each quarter; the compensating controls are the persona
egress rule, the `egress-internal-markers` KQL alert, and page reads going
through `osint-proxy` instead. Full text:
`governance/DATA_PROTECTION_GUARDRAILS.md` §1.

## Orchestrator, advisor with memory, MCP access

`orchestrator/README.md` describes the flagship layer: the
`infosec-assurance-orchestrator` (single entry point, reasoning tier, A2A
hand-offs to every published agent), the `infosec-assurance-advisor`
(reasoning generalist across all persona domains, grounded in the combined
knowledge store — its single file_search store — with durable team memory
served from the `kb-assurance-memory` Azure AI Search index, still written
and deleted through `scripts/memory_store.py`; `vs-assurance-memory` is the
transition backend, `enterprise/MEMORY_AND_LEARNING.md` §2), and the MCP
server in `mcp-server/` that exposes the whole environment to any MCP
client (Claude included) via `ask_orchestrator` / `ask_agent` /
`save_memory` / `search_memory`.

Step **[1b]** regenerates the platform self-knowledge pack
(`scripts/build_self_knowledge.py`) from the manifest that step [1] just
wrote; when the pack changed, step [1] is re-run so the new tables reach the
agents' knowledge stores. Step **[4b]** is the router rewire
(`create_agents.py --rewire`): step [3] runs with `--skip-routers` because
the delivery agents a ROUTE table points at are only created in step [4].

Re-running steps 3–4 is idempotent by agent name: existing agents are updated
in place (instructions and knowledge refreshed), new skills become new agents.
[1b] and [4b] are idempotent too — [1b] rewrites only the marked blocks and
reports "up to date" when nothing moved, and [4b] rewrites only ROUTE tables.

## What gets created in Azure

- 1 resource group
- 1 Microsoft Foundry account (`Microsoft.CognitiveServices`, kind `AIServices`)
  with 1 Foundry **project**
- 3 model deployments — chat (default `gpt-4o`), reasoning and light tiers;
  names, pinned versions and capacity in `main.parameters.json`
  (`governance/MODEL_ROUTING.md` decides which agent runs on which tier)
- 22 converted agents by default (18 custom GRC/TPRM + 4 document skills);
  the 13 Anthropic example skills convert only with `--include-examples`,
  which takes the export's 35 skills to 35 agents. Each agent gets:
  - the persona preamble + its skill's instructions (+ overlay/addendum)
  - its vector store with the `references/` files (where the skill has any)
  - code_interpreter with its `scripts/` and `assets/` files (where present)
- 8 agents that exist only here: `infosec-assurance-orchestrator`,
  `infosec-assurance-advisor`, `output-verifier`, and the delivery layer
  (`ciso-global-report`, `tpa-evidence-analyzer`, `soc-report-analyzer`,
  `pentest-report-analyzer`, `template-manager`) — `agents/README.md` also
  charters `enterprise-explorer` and the three research agents
- 1 router agent (`enx-tprm-control-center`) handing off to its five worker
  agents through the A2A tool
- 2 container-based Function apps — `{baseName}-delivery` (renderers,
  SharePoint storage, Document Intelligence; holds the managed identity) and
  `{baseName}-office` (`functions/office-tools/`: LibreOffice, pandoc,
  poppler, qpdf, tesseract, ImageMagick; **no credential and no outbound
  call**, key-protected, called only by the delivery Function and the
  pipelines, never attached to an agent). Images are tagged with the release
  tag (`operations/LIFECYCLE.md` V10)

## Limitations and honest deltas

1. **Model:** Anthropic Claude models **are** offered on Microsoft Foundry;
   they are excluded from this deployment by the **EU residency rule** (no EU
   Data Zone for them at the time of writing), not by availability. An earlier
   statement in this kit that they are "not available on Azure" is
   **withdrawn** — the correction of record, its sources and the per-tier
   switch procedure are `governance/CLAUDE_ON_FOUNDRY.md`. Re-check the model
   region-availability page at the quarterly platform-currency review; the
   three publisher-format parameters in `infra/main.bicep` —
   `lightModelFormat`, `chatModelFormat`, `reasoningModelFormat`, each
   `@allowed(['OpenAI', 'Anthropic'])` and feeding the `format` field of the
   three model deployments — already accept `Anthropic` (Haiku → light,
   Sonnet → chat, Opus → reasoning) for the day the residency position
   changes. Switching is never a one-parameter edit: a deployment is named
   after its model, so the tier's `*ModelName` / `*ModelVersion` parameters,
   the matching `*_DEPLOYMENT_NAME` in `setup/.env` and
   `_deployment_of_record` in `integrations/registry.json` move with it,
   `deploymentSku` stays `DataZoneStandard`, and the candidate must pass the
   tool-compatibility matrix (`governance/MODEL_ROUTING.md`, finding C4)
   before it can carry a reasoning agent's tools. Agents therefore
   default to `gpt-4o`: instruction-following and output style differ from
   claude.ai, so validate the report-generating agents (ciso-reporting,
   deepsearch, slide generators) against known-good outputs before relying on
   them. If Claude fidelity is mandatory, keep those workloads on claude.ai /
   Claude API and use Foundry for the rest — the converter lets you deploy a
   subset (`--only`).
2. **Skill triggering:** Claude auto-selects skills from their descriptions.
   In Foundry, selection is explicit (you invoke an agent) or routed through
   the orchestrator / router agent (A2A hand-offs) or your application layer.
3. **JS scripts:** code_interpreter executes Python only. Skills whose
   generators are Node.js (the pptx slide generators) have their JS attached
   as reference material; the converter flags them in the manifest
   (`"requires_external_runtime": true`) — run those generators in an Azure
   Function or container job if you need them server-side.
4. **Local-hardware skills:** `whisperx-transcribe-diarize` targets local
   Apple-Silicon execution; in Azure use Foundry Speech batch transcription
   + diarization instead (`workflows/speech-transcription.json`). It is
   converted as knowledge-only.
5. **Connectors:** Gmail/Drive/Adobe-style connectors have no direct
   equivalent inside an agent; use Azure Logic Apps or OpenAPI tools per
   integration (out of scope here, documented in MAPPING.md).
6. **SDK drift:** `azure-ai-projects` evolves quickly; versions are pinned in
   `setup/requirements.txt`, today `azure-ai-projects>=2.3.0,<3` (GA agents /
   conversations / responses, `api-version=v1`). The classic threads/runs pins
   (`azure-ai-projects==1.0.0`, `azure-ai-agents==1.1.0`) remain only as a
   documented fallback that `scripts/_foundry_runtime.py` detects automatically
   and `deploy.sh` step `[0b/8]` warns about (`STRICT_RUNTIME=1` makes it fail). If a call signature has moved, check the
   migration notes for the pinned major version. The runtime moves too: the
   classic threads/runs data plane retires 2027-03-31, so scripts and
   workflows target conversations/responses (`enterprise/ENTERPRISE_BLUEPRINT.md`
   PRJ-2) — an SDK or API-version bump is a reviewed change, never a
   convenience upgrade.

## Platform currency

Microsoft Foundry moves faster than this kit. Every change to the platform
— model version, API/SDK version, preview→GA feature, instructions,
registry, workflows, infrastructure, RBAC — is reviewed and approved by the
accountable owner **before** it is implemented, and a **quarterly
platform-currency review** re-checks API lifecycle, SDK cadence, portal GA
status, preview exits, model retirements and region availability (including
the Claude-on-Foundry residency position above). The binding rule, the
per-change evidence table and the quarterly checklist are in
`enterprise/UPDATE_AND_UPGRADE_REVIEW_POLICY.md`; the current platform
decisions and their sources are in `enterprise/ENTERPRISE_BLUEPRINT.md`.
Read both before changing anything here.

## Cost (FinOps)

Spend is governed, not incidental: `operations/FINOPS.md` holds the cost
model per component, the cost per deliverable by tier, capacity sizing,
budgets and anomaly alerts, and the monthly owner review;
`operations/TOKEN_ECONOMY_PLAYBOOK.md` is the tuning procedure and
`governance/MODEL_ROUTING.md` the tier rules. Two current planning points:
deployments run in the **EU Data Zone**, which carries a premium over
Global pricing from 2026-09-01, and the quota tier plus per-deployment
capacity are re-checked quarterly with the platform-currency review (raise
capacity on sustained 429s; move a tier to provisioned capacity only after
three months above the break-even point).

## Governance note (ISO 42001 / EU AI Act)

Deploying these agents on Azure makes your organisation the **deployer** (and
for substantially modified systems potentially the provider) of the AI
systems under the EU AI Act, and brings them into scope of your AIMS if you
run ISO/IEC 42001. The exported `iso42001` and `eu-ai-act` agents themselves
contain the reference material to run that assessment; do it before
production use. Log and monitor via Microsoft Foundry's built-in tracing +
Azure Monitor. Day-2 operation (health checks, failure modes, severities),
support tiers and SLOs, PR-based change control and the alert catalogue are in
`operations/` (`RUNBOOK.md`, `SUPPORT_MODEL.md`, `CHANGE_MANAGEMENT.md`,
`MONITORING.md`); the ownership and access model is `team/TEAM_MODEL.md`.
