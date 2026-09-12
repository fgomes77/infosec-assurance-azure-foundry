# Project Dossier

Narrative documentation of the InfoSec Assurance Agent Platform, **derived
from the conversion kit in `../convertion/`**. The kit is the source of
truth; this dossier is a rendering of it.

- **Project-Dossier-InfoSec-Assurance-Agent-Platform.docx** — the professional project document: objectives, requirements, goals, solution structure, workflows, interconnections, security & governance, and the implementation plan, with the embedded infographics.
- **infographics/** — the diagrams (PNG) and `generate.py`, their reproducible generator.
- **build_dossier.js** — rebuilds the .docx from source (requires the `docx` npm package): `node build_dossier.js`.

## Regeneration

The `.docx` and the infographics are **regenerated from the current kit** —
they are build outputs, never hand-edited binaries. After any change under
`../convertion/` that the dossier describes (agent inventory, architecture,
workflows, governance, implementation plan), update `build_dossier.js` /
`infographics/generate.py` to match the kit and re-run:

```bash
python3 infographics/generate.py && node build_dossier.js
```

Both binaries in this folder were produced by an earlier run of those
generators and therefore lag the kit until the command above is re-run;
the kit documents (`../convertion/README.md`, `MAPPING.md`,
`ARCHITECTURE.md`, `REQUIREMENTS.md`, `enterprise/`) are authoritative on
naming ("Microsoft Foundry", formerly Azure AI Foundry), runtime vocabulary
(conversations/responses), orchestration (A2A hand-offs / Agent Framework,
not Connected Agents), knowledge design (one vector store per agent; Azure
AI Search / Foundry IQ for shared knowledge and memory) and agent counts
wherever the two disagree.
