# Persona Coverage Matrix

Traceability from every element of the persona description
(`../agents/persona_system_prompt.md`, sourced from
`../../claude-account-export/PERSONA.md`) to where it is implemented in this
project — both as behaviour (instructions) and as grounded knowledge
(retrievable sources). Verified with the commands at the end.

## 1. Identity, role, experience, tone, language

| Persona element | Where implemented |
|---|---|
| Senior InfoSec Assurance & TPRM Leader; Principal Security Assurance Consultant & TPRM Lead | Persona preamble prepended to ALL agents (converter + orchestrator/advisor/verifier creators) |
| >20 years across financial services and critical ICT | Same preamble; reflected in evidence-led working style of advisor/verifier charters |
| Language policy: always answer in English | Preamble line on every agent |
| Tone: professional, precise, evidence-led, solution-oriented | Preamble + advisor charter ("reason from evidence", "firm recommendation with rationale") + verifier grounding rule |
| Cybersecurity architect & project manager (PMBOK-certified) | Preamble + grounded in `advisor-knowledge/governance-frameworks-compendium.md` (PMBOK 7 section) + the dossier's implementation plan applies the discipline |

## 2. Regulatory / framework domains → knowledge grounding

| Domain | Behavioural (agent) | Knowledge (retrievable source in the combined store) |
|---|---|---|
| ISO/IEC 27001:2022 | iso27001 agent | iso27001 references: Annex A 2022 (93 controls), Annex A 2013, 2013→2022 mapping |
| ISO/IEC 27002:2022 | iso27001 agent | Covered by the Annex A 2022 catalogue (the 27002 control set) + control-mapping notes |
| ISO/IEC 27005:2022 | advisor (+ iso27001 agent for ISMS context) | `advisor-knowledge/iso27005-risk-management.md` |
| NIST CSF 2.0 | advisor | `advisor-knowledge/nist-csf-2-0.md` (6 Functions, categories, ISO mapping, GV.SC for TPRM) |
| CIS v8.1 | advisor | `advisor-knowledge/cis-controls-v8-1.md` (18 controls, IG1-3, Annex A mapping) |
| GDPR Art. 28 / SCCs 2021/914 | dpia + onetrust-form-b agents (process), advisor (advisory) | `advisor-knowledge/gdpr-art28-sccs.md` (Art. 28(3) clauses, SCC modules, TIA, checklist) |
| DORA | dora agent | dora references: 64 articles, RTS/ITS, incident classification, third-party risk |
| NIS2 | nis2 agent | nis2 references: Art. 21 measures, ISO 27001 mapping |
| EU AI Act | eu-ai-act agent | eu-ai-act references: risk classification, high-risk obligations, GPAI governance |
| ISO/IEC 42001 | iso42001 agent | iso42001 references: clauses, Annex A controls, AI risk methodology |
| ISO 22301 business continuity | advisor | `advisor-knowledge/iso22301-business-continuity.md` |
| SOC 1/2/3 (SSAE 18 / ISAE 3402 / ISAE 3000) reliance | soc-report-analyzer, tpa-evidence-analyzer, advisor | `advisor-knowledge/soc-isae-assurance-reports.md`, `tpa-evidence-review-playbook.md` |
| CSA CCM / CAIQ / STAR | advisor, tpsrca-assessment-engine | `advisor-knowledge/csa-ccm-caiq-star.md` |
| ISO/IEC 27701 privacy management | dpia agent (process), advisor | section "ISO/IEC 27701" in `advisor-knowledge/gdpr-art28-sccs.md` |
| PCI DSS v4 (supplier scope) | tpa-evidence-analyzer (AOC/ROC/SAQ/ASV), advisor | `advisor-knowledge/pci-dss-v4-supplier-assurance.md` |
| Cloud service models, shared responsibility, ICT service assurance | advisor, tpsrca | `advisor-knowledge/cloud-ict-service-assurance.md`, `tpsrca-supplier-types.md` |
| Security architecture | advisor | `advisor-knowledge/security-architecture-reference.md` |
| Penetration-test standards (OWASP, PTES, CVSS) | pentest-report-analyzer, advisor | `advisor-knowledge/pentest-standards-owasp-ptes-cvss.md` |
| ISO/IEC 20000-1 service management | advisor | `advisor-knowledge/iso20000-service-management.md` |
| ISO/IEC 27002 control attributes | iso27001 agent, advisor | `advisor-knowledge/iso27002-control-attributes.md` |

## 3. Management-framework expertise → knowledge grounding

| Expertise claimed | Grounding |
|---|---|
| ITIL (4), COBIT (2019), COSO, TOGAF (10), agile, Lean IT, ISO 20000-1, PMBOK 7, cloud & ICT service assurance | `advisor-knowledge/governance-frameworks-compendium.md` — practitioner sections + cross-walk table of what the assurance team uses each framework for |

## 4. Functional coverage (TPRM · ISMS · GRC · ICT GRC)

| Function | Agents delivering it |
|---|---|
| TPRM | deepsearch-protocol, ai-deepsearch-osint, tpsrca-assessment-engine, dpia, onetrust-form-b, ciso-reporting, ciso-executive-summary, slide generators, enx-tprm-control-center |
| TPRM — evidence review (certificates, SOC reports, pentests, questionnaires) | tpa-evidence-analyzer (req. d2), soc-report-analyzer, pentest-report-analyzer (req. e/f), pdf-full-coverage-analyzer |
| CISO reporting line | ciso-global-report (req. d), ciso-reporting, ciso-executive-summary, pptx-executive-summary-ciso |
| Methodology / template control (req. j) | template-manager + `workflows/template-update-approval.json` |
| Quality gate | output-verifier (`agents/verifier_instructions.md`) — no approval gate (`HUMAN_APPROVAL.md` Layer 2 exception) |
| Entry point / routing | orchestrator (`create_orchestrator.py`), enx-tprm-control-center router, infosec-assurance-advisor |
| Enterprise reconnaissance (find the facts before the analysis) | enterprise-explorer (`agents/enterprise-explorer_instructions.md`, light tier, `advisory_read_only_toolset`, no web search) — the read-only fact-finder across Confluence, Jira, Jira Assets CMDB, SharePoint, OneTrust, Defender, Entra ID, SecurityScorecard, IAF and the ENX gateway MCP |
| Deep research with citations (threat/regulatory/supplier questions no single agent holds) | research-coordinator → research-worker (×N) → research-writer (`agents/research-*_instructions.md` + `agents/overlays/research-pattern.md`); adapted from the claude.ai `deep-research` skill — sub-agents become A2A hand-offs, WebFetch becomes Bing grounding + `osint-proxy`, filesystem notes become replies |
| ISMS | iso27001, iso42001, advisor (27005 risk methodology, SoA/treatment support) |
| GRC / ICT GRC | dora, nis2, eu-ai-act, cyber-forum, advisor cross-framework mapping; CMDB integration for DORA RoI |

Delivery agents, orchestrator, advisor and verifier receive the persona
from `create_delivery_agents.py` / `create_orchestrator.py`, not from the
converter — the `build/agents` grep below therefore counts converted
skills only; check live agent instructions for the rest.

## 4a. Environment knowledge packs (ENX-authored) → persona elements

The advisor pack of §2–§3 grounds what the persona *knows*. A second,
smaller set grounds how the persona *works in this environment* — the
claude.ai platform skills that had no Foundry meaning as written and were
re-authored as packs (`PLATFORM_SKILLS_DECISION.md` §1, decision
KNOWLEDGE-PACK). They are attached as `pack__<file>` to the agents listed,
by `convert_skills.py` (`KNOWLEDGE_PACKS`) and
`create_delivery_agents.py` (`_PACKS`), and all five also enter the
advisor's combined store through `create_orchestrator.py`.

| Pack (`agents/knowledge-packs/`) | Persona element it grounds | Replaces (claude.ai) | Attached to |
|---|---|---|---|
| `file-intake-foundry.md` | "evidence-led" — start from the evidence file, never from an assumption about it | `file-reading` | dpia, onetrust-form-b, ciso-reporting, ciso-executive-summary, pdf-full-coverage-analyzer, the two slide generators, tpsrca, whisperx + docx/pdf/pptx/xlsx + the four delivery analyzers |
| `pdf-reading-foundry.md` | Same, for the format most supplier evidence arrives in (inventory before reading; no rasterise-and-look CLI in the sandbox) | `pdf-reading` (+ its REFERENCE.md) | the file agents above minus whisperx, plus `pdf` and the delivery analyzers |
| `enx-writing-style.md` | Tone: professional, precise, evidence-led, decisive; English only | `setup-writing-style` **mechanism EXCLUDED** (mailbox/Drive harvesting is personal-data processing without a basis — `agents/README.md`); only the house style transfers | the file agents, deepsearch ×2, cyber-forum, internal-comms, doc-coauthoring, and every delivery agent |
| `enx-html-design-guide.md` | "Consistent thresholds / template governance" (principle 3, requirement j) — quality floor for free HTML, and Rule 0: a registered template is never restyled | `frontend-design` (palette/typography replaced by Euronext tokens) | deepsearch ×2, cyber-forum, ciso-executive-summary, tpsrca, template-manager |
| `platform-self-knowledge.md` | "Never answer capability questions from memory" — what this platform is (Microsoft Foundry, conversations/responses, A2A) and what it is not | `product-self-knowledge` (Anthropic product content EXCLUDED) | every agent, via `scripts/build_self_knowledge.py`; carries the Claude-on-Foundry correction (`CLAUDE_ON_FOUNDRY.md`) |

Each pack carries an "Authored {date}" provenance header, so a pack is
never mistaken for exported claude.ai content — the same rule as the
advisor pack.

## 5. Platform data-protection rules → implementation

| Persona bullet | Behaviour (instructions) | Enforcement (tool / credential / detective) |
|---|---|---|
| Read-only posture | preamble bullet; APPROVAL GATE block | `attach_integrations.py` non-GET strip + empty `write_connections` + MCP `readOnlyHint` check; read-only app registrations / `Sites.Selected` read (`DATA_PROTECTION_GUARDRAILS.md` §2) |
| Web egress | preamble bullet (the only instruction-layer carrier) | Bing grounding + allow-listed osint-proxy only; `infra/kql/egress-internal-markers.kql` alert (`§1`) |
| Injection defence | preamble bullet | verifier rule 8 (injection resistance) |
| Minimisation | preamble bullet; advisor memory ban | verifier rule 5; `MEMORY_POLICY.md`; `scripts/memory_store.py` |
| Sanitise and proceed | preamble closing bullet | `DATA_PROTECTION_GUARDRAILS.md` §5 non-blocking table |
| Consistent thresholds (principle 3) | preamble principle 3 → must cite `RISK_THRESHOLDS.md` (shared delta) | verifier rule 2 scale-aware table |

## How the pack reaches the agents

`create_orchestrator.py` builds the advisor's combined vector store from
every converted skill's knowledge **plus** `agents/advisor-knowledge/*.md`,
so the advisor (and, via routing, the orchestrator) can retrieve and cite
all persona domains — not only answer from model memory. Skill-level agents
keep exactly their exported knowledge (fidelity to claude.ai is verified
separately); the pack is advisor-scope by design, and its files carry an
"authored" header so they are never mistaken for exported claude.ai content.

## Verifying coverage

```bash
# persona preamble + approval gate present in every built agent
grep -rl "Principal Security Assurance Consultant" build/agents/*/instructions.md | wc -l  # = converted agent count
grep -rL "APPROVAL GATE" build/agents/*/instructions.md   # empty (converted agents); live: every agent except output-verifier

# advisor pack present and included in the combined store (dry run prints the file count)
ls agents/advisor-knowledge/*.md
python3 scripts/create_orchestrator.py --dry-run   # combined knowledge files = skills' + advisor pack + knowledge packs

# every knowledge pack reaches at least one agent, and every row of §4a exists
ls agents/knowledge-packs/*.md
grep -n "KNOWLEDGE_PACKS" -A 20 scripts/convert_skills.py   # pack -> agent map
ls build/agents/*/pack__*.md | sed 's|.*/pack__||' | sort -u

# every Foundry-only charter is covered by a §4 row
for f in agents/*_instructions.md; do n=$(basename "$f" _instructions.md); \
  grep -q "$n" governance/PERSONA-COVERAGE.md || echo "UNCOVERED $n"; done
```
