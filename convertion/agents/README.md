# convertion/agents — index and decisions

This directory holds everything that shapes agent behaviour WITHOUT
touching the byte-verified skill bodies from `claude-account-export/`
(fidelity is enforced by `scripts/verify_conversion.py`). Adaptation
happens through prepended persona text, appended overlays/addenda,
authored knowledge, and charters for agents that exist only here.

| Path | Purpose | Consumed by |
|---|---|---|
| `persona_system_prompt.md` | Persona preamble + platform data-protection rules (prepended to every agent) | convert_skills, create_orchestrator, create_delivery_agents |
| `advisory_addendum.md` | File-generation + read-only enterprise access for information-providing agents | apply_advisory_profile |
| `document_agents_addendum.md` | Runtime map and delivery binding for docx/pdf/pptx/xlsx | convert_skills (append for the four document skills) |
| `overlays/_foundry-environment.md` | Generic claude.ai → Foundry translation, appended to EVERY converted agent after the body | convert_skills |
| `overlays/<skill>.md` | Skill-specific environment mapping (deepsearch-protocol, ai-deepsearch-osint-gathering-report, ciso-reporting, ciso-executive-summary, cyber-forum, enx-tprm-control-center menu v2, tpsrca-assessment-engine, doc-coauthoring, learn) | convert_skills |
| `overlays/research-pattern.md` | Source tiers + citation discipline for cyber-forum, framework advisors, advisor, research agents | convert_skills / create_orchestrator / create_delivery_agents |
| `knowledge-packs/*.md` | Environment know-how packs: file intake, PDF reading, HTML design guide, writing style, platform self-knowledge | vector stores of the relevant agents |
| `advisor-knowledge/*.md` | Authored domain knowledge (persona domains not covered by the export) | combined store (create_orchestrator) + per-agent knowledge globs |
| `*_instructions.md` | Charters of agents that exist only in Foundry (advisor, verifier, orchestrator routing, ciso-global-report, analyzers, template-manager, enterprise-explorer, research-coordinator/worker/writer) | create_orchestrator / create_delivery_agents |

## Decisions recorded here (platform / example skills)

| Source | Decision | Rationale |
|---|---|---|
| `product-self-knowledge` (Anthropic product docs) | **EXCLUDED**; principle kept in `knowledge-packs/platform-self-knowledge.md` | No Claude models/products on Azure; only the "never answer capability questions from memory" rule transfers (MCP client note stays in mcp-server/README.md) |
| `setup-writing-style` (mailbox/Slack/Drive harvesting, per-user skill store) | **EXCLUDED** mechanism; **INCLUDED** house style `knowledge-packs/enx-writing-style.md` and the "paste samples in the thread" mode | Reading users' sent mail is a personal-data processing activity without a documented basis; Foundry has no per-user skill store; shared memory bans PII |
| `frontend-design` | **INCLUDED as constrained pack** `knowledge-packs/enx-html-design-guide.md` | Quality floor kept; distinctive palettes conflict with template governance (requirement j) and ENX brand |
| `file-reading`, `pdf-reading` | **INCLUDED, rewritten** as `knowledge-packs/file-intake-foundry.md`, `pdf-reading-foundry.md` | Their CLIs/paths do not exist in code_interpreter |
| `deep-research` | **INCLUDED, adapted** as research-coordinator/worker/writer charters + `overlays/research-pattern.md` | Method kept; sub-agents → connected agents; WebFetch → grounding; notes → reply |
| `doc-coauthoring`, `learn` | **DEPLOYED (adapted)** via overlays | Valuable for procedures/onboarding; Claude-only mechanics mapped |
| alphaXiv / personal paper library | **REPLACED** by the `MEMORY:` block tagged `citation` in `vs-assurance-memory` | No per-user libraries on the platform |
| Per-framework advisory systems (NIST CSF, CIS, 27005, 27002 attributes, GDPR Art. 28/27701, ITIL, COBIT, COSO, TOGAF, PMBOK, ISO 20000, agile/Lean, cloud) | `infosec-assurance-advisor` **IS** the advisory system for these frameworks, grounded by `advisor-knowledge/` and routed by keyword in `orchestrator_instructions.md` | One reasoning-tier advisor with the combined store beats eleven thin agents for cost and consistency; may be split later with the create_delivery_agents pattern |
| `tpsrca-assessment-engine` 12 agents | Kept as roles in one agent; Phase 1 via `advisor-knowledge/tpsrca-supplier-types.md`, Phase 2 delegated to `deepsearch_protocol`; optional split documented in the overlay | Single deterministic scorer (`calculation_engine.py`) preserved |
| `ai-deepsearch-osint-gathering-report` | Kept as a separate agent with the identical toolset and its own pipeline; companion reference shared both ways | Both skills are byte-verified exports; merging would alter fidelity |

## Model tiers of the agents charted here

light: enterprise-explorer, docx/pdf/pptx/xlsx · chat: research-worker,
research-writer, template-manager, learn, doc-coauthoring · reasoning:
advisor, verifier, orchestrator, research-coordinator, ciso-global-report,
analyzers (governance/MODEL_ROUTING.md is authoritative).

## Placeholders

Use `{braces}` for any tenant-specific value; no hostnames, secrets or
e-mail addresses in this directory.
