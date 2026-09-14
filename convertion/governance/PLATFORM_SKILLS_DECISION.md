# Platform Skills — Inclusion / Exclusion Decision (41 skills + harness skills)

**Machine-readable form: `../templates/skill-decisions.json`** (the entries
with origin `platform-skills/public` and `platform-skills/examples`);
`../scripts/verify_conversion.py` enforces it as checks C1–C10. Change both
together — this file is the prose record, the JSON is what CI checks.

`MAPPING.md` said the non-synced platform skills are "not deployed by
default; convert on demand the same way". That is not literally possible
(they are not account-synced and most describe consumer Claude
features), so this file records a per-skill decision.

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
| product-self-knowledge | no | KNOWLEDGE-PACK | Rewritten as platform self-knowledge for Foundry/Copilot users. **Rationale re-decided 2026-09-12:** the Anthropic product content is out of **scope** — a self-knowledge pack must describe the platform the user is on (Foundry, Agents v2, this kit's agents/pipelines/approval gates), and that holds whichever model a tier runs. The earlier "no Claude models on Azure" rationale is withdrawn as factually wrong (Claude models are offered on Foundry; unused here for EU residency, re-checked quarterly — `CLAUDE_ON_FOUNDRY.md`). Retained rule: never answer capability questions from memory | `agents/knowledge-packs/platform-self-knowledge.md` |

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
| setup-writing-style | no | SUPERSEDED | **Harvesting mechanism EXCLUDED, house style INCLUDED.** The skill learns a voice by reading the user's sent mail / Slack / Drive and storing a per-user style file; reading a team member's mailbox is a personal-data processing activity with no documented lawful basis, purpose or RoPA entry here (GDPR Art. 5(1)(a)/(b), 6, 30 — `DATA_PROTECTION_GUARDRAILS.md` §3), Foundry has no per-user skill store, and the shared memory bans PII (`MEMORY_POLICY.md`). ENX writing style is therefore **fixed, not learned**: `agents/knowledge-packs/enx-writing-style.md`, plus the skill's "paste samples in the conversation" mode, which processes only what the user chooses to paste. Same decision in prose: `../agents/README.md` §Decisions recorded here | knowledge pack |

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
python3 ../scripts/verify_conversion.py   # prints "skill decisions : 76 enforced"
```

`verify_conversion.py` asserts that **every** folder under
`platform-skills/public` and `platform-skills/examples` has exactly one row in
`../templates/skill-decisions.json`, and that no row lacks a folder (check C1)
— so a platform skill can be neither silently dropped nor silently deployed.

Earlier drafts of this file promised `PLATFORM_INCLUDE` and
`PLATFORM_EXCLUDED` constants in `scripts/convert_skills.py`. **Those
constants do not exist and are not wanted**: a second hand-maintained list
beside the decision table is exactly the drift this table was written to
prevent. The converter instead *derives* what it needs from the table
(`EXAMPLE_SKILLS`, `ALIASES`), and `verify_conversion.py` asserts the derived
sets still agree with it. The one literal set that remains,
`PLATFORM_SPECIFIC`, is a build flag rather than a decision — it marks skills
that only have meaning on the Claude platform, which is not the same statement
as "excluded" (`algorithmic-art` and `brand-guidelines` are excluded for having
no assurance use, not for needing a browser). The verifier enforces the
invariant that matters for it: every name in it has a decision row, and none of
those rows is `AGENT`.
