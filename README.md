# infosec-assurance-azure-foundry

Azure AI Foundry deployment of the InfoSec Assurance agent platform — the
conversion of the Claude skill toolset into Foundry agents.

## Contents

| Path | What it is |
|---|---|
| `convertion/` | The conversion kit — Bicep infrastructure, provisioning, agent and verifier instructions, MCP server, seven OpenAPI integrations (OneTrust, SecurityScorecard, Defender Graph, Jira Cloud, Jira Assets CMDB, SharePoint Graph, IAF), four workflows, orchestrator, human-approval governance |
| `claude-account-export/` | The conversion source — 35 account-synced skills (18 custom GRC/TPRM), 41 Anthropic platform skills (8 public, 33 examples), the advisor knowledge pack, `PERSONA.md`, `CAPABILITIES.md`, `environment/` |
| `project-dossier/` | Project dossier for the InfoSec Assurance Agent Platform — `.docx`, infographics and their generators |

`convertion/` reads `claude-account-export/` as a sibling directory
(`convert_skills.py`, `verify_conversion.py`), so the export is required here,
not optional.

## Relationship to `Infosec-assurance-grc-tprm-soecialidt`

This repository and
[`fgomes77/Infosec-assurance-grc-tprm-soecialidt`](https://github.com/fgomes77/Infosec-assurance-grc-tprm-soecialidt)
were maintained as mirrors up to 2026-09-12 and still share the content above.

**They are no longer synchronised.** From 2026-09-12 each repository evolves
independently: changes made here do not propagate there, and changes made there
do not propagate here. Any future alignment is a deliberate, manual act.
