# Platform Skills — Inclusion / Exclusion Decision (41 skills + harness skills)

`MAPPING.md` said the non-synced platform skills are "not deployed by
default; convert on demand the same way". That is not literally possible
(they are not account-synced and most describe consumer Claude
features), so this file records a per-skill decision. Encode it in
`scripts/convert_skills.py` as `PLATFORM_INCLUDE` (name → mode) and
`PLATFORM_EXCLUDED` (name → rationale) and let `verify_conversion.py`
assert every platform skill appears in exactly one set (shared delta).

Modes: **AGENT** (converted to a Foundry agent), **KNOWLEDGE-PACK**
(rules folded into an ENX-authored pack under `agents/knowledge-packs/`),
**SUPERSEDED** (function provided by a platform component), **EXCLUDED**
(no Foundry meaning or consumer-only).

## 1. `platform-skills/public/` (8)

| Skill | Account-synced | Decision | ENX rationale | Target component |
|---|---|---|---|---|
| docx | yes | AGENT (`light`) | Word deliverables; licence gate per `THIRD_PARTY_IP.md` | `build/agents/docx` |
| pdf | yes | AGENT (`light`) | PDF assembly/extraction; licence gate | `build/agents/pdf` |
| pptx | yes | AGENT (`light`) | slide decks; Node generators run in the delivery Function | `build/agents/pptx` |
| xlsx | yes | AGENT (`light`) | Form B round-trip xlsx, registers | `build/agents/xlsx` |
| file-reading | no | KNOWLEDGE-PACK | Foundry file intake differs (file_search / code_interpreter / Function extract) | `agents/knowledge-packs/file-intake-foundry.md` |
| pdf-reading | no | KNOWLEDGE-PACK | rasterise-and-read → Document Intelligence / `/api/extract_pdf` (`MODEL_ROUTING.md` §Vision) | `agents/knowledge-packs/pdf-reading-foundry.md` |
| frontend-design | no | KNOWLEDGE-PACK | HTML dashboards are template-governed; only the accessible-colour/layout rules are kept | `agents/knowledge-packs/enx-html-design-guide.md` |
| product-self-knowledge | no | KNOWLEDGE-PACK | rewritten as platform self-knowledge for Foundry/Copilot users | `agents/knowledge-packs/platform-self-knowledge.md` |

## 2. `platform-skills/examples/` (33)

| Skill | Account-synced | Decision | ENX rationale | Target component |
|---|---|---|---|---|
| doc-coauthoring | yes | AGENT (`chat`) | structured doc drafting for policies/specs | `build/agents/doc-coauthoring` |
| internal-comms | yes | AGENT (`chat`) | status/leadership updates, incident notes | `build/agents/internal-comms` |
| learn | yes | AGENT (`chat`) | team learning on regulation/frameworks | `build/agents/learn` |
| mcp-builder | yes | AGENT (`reasoning`) | building ENX gateway MCP tooling | `build/agents/mcp-builder` |
| morning | yes | SUPERSEDED | daily brief = Logic App `workflows/morning-brief.json` (agent shell kept `light`) | `workflows/morning-brief.json` |
| algorithmic-art | yes | EXCLUDED | p5.js generative art — no assurance use | — |
| brand-guidelines | yes | EXCLUDED | Anthropic brand; ENX house style lives in `enx-writing-style.md` / `enx-html-design-guide.md` | — |
| canvas-design | yes | EXCLUDED | consumer artwork generation | — |
| import-memory | yes | SUPERSEDED | durable memory = `scripts/memory_store.py` + `MEMORY_POLICY.md` | `scripts/memory_store.py` |
| skill-creator | yes | EXCLUDED | Claude-skill authoring/evals; Foundry agents are created by `scripts/create_agents.py` | — |
| slack-gif-creator | yes | EXCLUDED | Slack not an ENX channel | — |
| theme-factory | yes | EXCLUDED | artefact theming; templates are registry-governed | — |
| web-artifacts-builder | yes | EXCLUDED | claude.ai Artifacts; HTML delivered to SharePoint / Static Web App | — |
| benepass-reimbursement | no | EXCLUDED | consumer finance task | — |
| built-in-browser | no | EXCLUDED | Claude browser tool; web = Bing grounding + osint-proxy only | — |
| call-to-book | no | EXCLUDED | consumer phone-booking | — |
| cancel-unsubscribe | no | EXCLUDED | consumer task | — |
| chrome-browser | no | EXCLUDED | browser automation — egress policy forbids generic browsing | — |
| computer-use | no | EXCLUDED | desktop control — out of scope, no approved write path | — |
| deep-research | no | SUPERSEDED | research pattern folded into `agents/overlays/research-pattern.md` for deepsearch/cyber-forum | overlays |
| docs | no | EXCLUDED | Google Docs connector — M365 tenant only | — |
| event-planning | no | EXCLUDED | consumer task | — |
| file-expenses | no | EXCLUDED | consumer task | — |
| file-form | no | EXCLUDED | generic form filling; OneTrust Form B has its own agent | — |
| financial-calculator | no | EXCLUDED | consumer finance | — |
| google-workspace | no | EXCLUDED | Google Workspace — M365 tenant only | — |
| grocery-shopping | no | EXCLUDED | consumer task | — |
| hire-help | no | EXCLUDED | consumer task | — |
| meal-delivery | no | EXCLUDED | consumer task | — |
| paint | no | EXCLUDED | consumer creative | — |
| prescription-refill | no | EXCLUDED | consumer health task | — |
| return-refund | no | EXCLUDED | consumer task | — |
| setup-writing-style | no | SUPERSEDED | ENX writing style is fixed in `agents/knowledge-packs/enx-writing-style.md` | knowledge pack |

## 3. Harness skills (Claude Code environment, listed in `CAPABILITIES.md`)

| Harness skill | Decision | Rationale / where covered |
|---|---|---|
| dataviz | KNOWLEDGE-PACK | accessible-colour, legend, axis and stat-tile rules folded into `enx-html-design-guide.md` (spider graph, gauges, exposure map) — templates still govern look |
| loop, workflow-authoring | SUPERSEDED | recurring runs and multi-agent pipelines = Logic Apps (`workflows/README.md`, `agent-fanout.json`, `scheduled-*.json`) |
| artifact-design, artifact-diagramming, artifact-capabilities | SUPERSEDED | published HTML = SharePoint org-scoped links + template review page (`static-web-app.bicep`) |
| session-start-hook, code-review, security-review, simplify, update-config, keybindings-help, fewer-permission-prompts, run, init, claude-api, design | EXCLUDED | development-environment tooling, not runtime capability of the platform |

No code change is implied by §3.

## 4. Verification

```bash
ls ../../claude-account-export/platform-skills/public ../../claude-account-export/platform-skills/examples | grep -v '\.skill$' | wc -l   # 41 folders
python3 ../scripts/verify_conversion.py   # after the shared delta: asserts every platform skill is in exactly one decision set
```
