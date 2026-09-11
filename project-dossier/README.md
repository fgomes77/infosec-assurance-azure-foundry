# Project Dossier

- **Project-Dossier-InfoSec-Assurance-Agent-Platform.docx** — the professional project document: objectives, requirements, goals, solution structure, workflows, interconnections, security & governance, and the implementation plan, with five embedded infographics.
- **infographics/** — the five diagrams (PNG) and `generate.py`, their reproducible generator.
- **build_dossier.js** — rebuilds the .docx from source (requires the `docx` npm package): `node build_dossier.js`.

Regenerate after changes: `python3 infographics/generate.py && node build_dossier.js`.
