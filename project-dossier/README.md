# Project Dossier

Narrative documentation of the InfoSec Assurance Agent Platform, **derived
from the conversion kit in `../convertion/`**. The kit is the source of
truth; this dossier is a rendering of it.

- **Project-Dossier-InfoSec-Assurance-Agent-Platform.docx** — the project
  document, in two parts so it serves both audiences without splitting into
  two files that drift apart:
  - **Part I — For stakeholders**: executive summary, context, objectives and
    scope, the ten systems (requirements a–j), what changes for the team,
    governance and compliance, benefits and cost, risks, and the phased plan.
  - **Part II — For implementers**: the Microsoft Foundry target architecture
    and resource inventory, model tiers and inference profiles, the agent
    inventory and conversion pipeline, all 20 connections, the 17 workflows
    and 12 delivery pipelines, storage and the evidence cache, the security
    controls in implementation terms, identity and RBAC, deployment, the CI
    gate set, and operations.
  - Appendices: requirement traceability, repository map, glossary, references.
- **infographics/** — the six diagrams (PNG) and `generate.py`, their
  reproducible generator.
- **build_dossier.js** — rebuilds the .docx from source.

## Regeneration

The `.docx` and the infographics are **build outputs, never hand-edited
binaries**. After any change under `../convertion/` that the dossier
describes (agent inventory, architecture, workflows, governance, plan,
connections), update `build_dossier.js` / `infographics/generate.py` to match
the kit and re-run:

```bash
npm install docx            # once, in this folder
python3 infographics/generate.py && node build_dossier.js
```

Where the dossier and the kit disagree, **the kit wins**: `../convertion/`
(`README.md`, `MAPPING.md`, `ARCHITECTURE.md`, `REQUIREMENTS.md`,
`enterprise/`, `governance/`) is authoritative on naming ("Microsoft
Foundry", formerly Azure AI Foundry), runtime vocabulary
(conversations/responses on the Responses API), orchestration (A2A hand-offs
/ Agent Framework, not Connected Agents), knowledge design (one vector store
per agent; Azure AI Search / Foundry IQ for shared knowledge and memory), and
every count of agents, workflows, connections and templates.

`node_modules/` is a local build dependency and is not committed.
