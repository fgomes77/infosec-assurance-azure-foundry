# Agent Architecture — Design Patterns, MCP/RAG/Skills, Guardrails

How this environment maps to the standard agent design patterns
(single-shot, iterative ReAct, planner-executor, reflexive, verifier-gated)
and the three context architectures (MCP, RAG, Skills), and where each
guardrail lives. Nothing here changes agent outputs — it documents and
enforces how those outputs are produced, checked, and released.

## The three context architectures in this stack

| Architecture | Where it lives here |
|---|---|
| **MCP** (connect to external systems) | `mcp-server/` exposes the environment to MCP clients; `integrations/mcp/enx-gateway.json` consumes the internal ENX gateway; OpenAPI tools cover the non-MCP systems (Jira, OneTrust, Graph, SecurityScorecard, IAF) |
| **RAG** (ground answers in your data) | Per-agent vector stores (`vs-<agent>`) + the advisor's combined store (`vs-assurance-combined`) + durable memory (`vs-assurance-memory`) via file_search |
| **Skills** (packaged actions + logic) | The converted SKILL.md instruction sets + code_interpreter scripts/assets — the claude.ai skills preserved as agent capabilities |

## Design pattern per agent

| Pattern | Agents | Why |
|---|---|---|
| **1. Single-shot** | docx, pdf, pptx, xlsx (per document task) | Deterministic transformation; low latency/cost |
| **2. Iterative ReAct** | cyber-forum, deepsearch-protocol, ai-deepsearch-osint (research loops over web search + APIs) | Tool use, observe, adapt until evidence suffices |
| **3. Planner-executor** | infosec-assurance-orchestrator (plans, delegates to connected specialists, aggregates); enx-tprm-control-center (TPRM sub-router) | Decomposition across independent executors |
| **4. Reflexive** | Report generators: ciso-reporting, ciso-executive-summary, tprm-slide-generator, pptx-executive-summary-ciso, dpia, onetrust-form-b — a mandatory SELF-CHECK pass before presenting (injected by the converter) | Quality on high-stakes deliverables |
| **5. Verifier-gated** | `output-verifier` agent independently checks every submission-of-record draft against deterministic rules BEFORE the human approval gate | Independent layer; self-critique is not independent |

Combined release path for anything leaving the environment (unchanged
results, more assurance):

```
specialist agent → (reflexive self-check) → output-verifier (rules) →
HUMAN APPROVAL (governance/HUMAN_APPROVAL.md) → gated workflow submits
```

## The output-verifier (pattern 5)

Created by `scripts/create_orchestrator.py` alongside the advisor. It never
generates content; it returns a strict PASS/FAIL verdict with findings.
Rules (in `agents/verifier_instructions.md`): schema/required-field
completeness per deliverable type, score-threshold consistency (e.g. TPRM
red ≥7.0 / amber ≥4.0 vs the slide colour bands), citation presence for
regulatory claims, no unresolved placeholders ({{TOKEN}}, TBD), no personal
data beyond what the source assessment contains, and approval-gate text
present on any draft submission. FAIL → back to the producing agent;
PASS → to the human approver. The orchestrator routes drafts through it;
the Logic Apps gates mean nothing skips the human even if the verifier is
bypassed.

## Guardrails and observability (production panel)

| Guardrail | Implementation |
|---|---|
| Timeouts | Workflow HttpWebhook gates expire P3D; HTTP actions carry Logic Apps defaults |
| Retries + error handling | `scripts/_azure_helpers.py` backoff on every upload/store call; per-agent failure isolation in create_agents.py; workflow runAfter failure paths |
| Safety filters | Azure AI Foundry default content filtering (RAI policy) applies to both model deployments; stricter custom policies attachable per deployment |
| Deterministic constraints | Read-only OpenAPI tools (writes stripped); output-verifier rules; verify_conversion.py byte-fidelity gate in deploy.sh |
| Memory/state | Foundry threads (session) + vs-assurance-memory (durable, auditable, deletable) |
| Observability | Application Insights wired to the Foundry project (Bicep): traces, tokens, latency per run; Logic Apps run history evidences approvals |
| Human oversight | Three-layer approval control — see governance/HUMAN_APPROVAL.md |

## Delivery pipelines (release path made executable)

The combined release path above is implemented end-to-end by
`workflows/report-delivery-pipeline.json` (one Logic App per entry in
`workflows/pipelines.json`): producing agent → output-verifier →
HttpWebhook human approval (P3D) → delivery Function renders the file →
`ensure_folder` (idempotent `Reports/<Supplier>/<Service>/`) → upload +
organisation-scoped share link → Teams notification. Template changes run
the same shape through `workflows/template-update-approval.json` with a
visual before/after review page and `scripts/update_templates.py`
propagation. The only SharePoint writer is the delivery Function's
managed identity; agents stay read-only
(`governance/DATA_PROTECTION_GUARDRAILS.md`), and model tiers per agent
are governed by `governance/MODEL_ROUTING.md`.

## Evaluation and success metrics

Track per agent in App Insights / Foundry tracing: task success (verifier
PASS rate on first attempt), human approval rate vs rework, latency and
token cost per deliverable, and grounding rate (answers citing a knowledge
source). Review monthly in the ISMS operating rhythm; a falling first-pass
rate on a report agent means its knowledge or instructions drifted — re-run
`deploy.sh` from a fresh export and re-verify.

## Function fit — TPRM / ISMS / GRC / ICT GRC

- **TPRM:** deepsearch + tpsrca (ReAct evidence gathering) → verifier-gated
  reports → human-approved Jira/IAF submissions; CMDB grounding for DORA RoI.
- **ISMS:** iso27001/iso42001 advisors (RAG over the catalogues) support
  SoA, risk treatment, audit prep; memory keeps positions consistent.
- **GRC / ICT GRC:** dora/nis2/eu-ai-act advisors with web grounding for
  regulatory currency; the advisor cross-maps frameworks; every output is
  evidence-led, verified, and human-released — the audit trail is the
  workflow run history plus the memory store.
