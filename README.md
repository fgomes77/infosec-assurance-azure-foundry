# infosec-assurance-azure-foundry

**Microsoft Foundry (formerly Azure AI Foundry)** deployment of the InfoSec
Assurance agent platform — the conversion of the Claude skill toolset into
Foundry agents.

## Contents

| Path | What it is |
|---|---|
| `convertion/` | The conversion kit — Bicep infrastructure (`infra/`, `enterprise/`), provisioning, agent charters and verifier rules, MCP server, 15 read-only OpenAPI integrations (`integrations/openapi/`: OneTrust, SecurityScorecard, Defender Graph, Entra IAM Graph, Jira Cloud, Jira Assets CMDB, SharePoint Graph, Confluence, Exchange/Teams/M365 Graph, Azure DevOps, OSINT proxy, passive recon, IAF), 17 Logic Apps workflows + `pipelines.json`, orchestrator and advisor, human-approval governance, team model and operations — plus the delivery layer (`convertion/REQUIREMENTS.md`): supplier/service SharePoint storage pipelines, Global CISO deck, evidence/SOC/pentest analyzers, read-only enterprise access, egress guardrails, model routing, template change control |
| `claude-account-export/` | The conversion source — 35 account-synced skills (18 custom GRC/TPRM), 41 Anthropic platform skills (8 public, 33 examples), the advisor knowledge pack, `PERSONA.md`, `CAPABILITIES.md`, `environment/` |
| `project-dossier/` | Project dossier for the InfoSec Assurance Agent Platform — `.docx` and infographics, both **regenerated from the current kit** by the generators in that folder |

Platform currency: Foundry changes faster than this kit. Every change is
owner-approved before implementation and re-checked quarterly against the
service — the binding rule is
`convertion/enterprise/UPDATE_AND_UPGRADE_REVIEW_POLICY.md` and the current
platform decisions with their sources are in
`convertion/enterprise/ENTERPRISE_BLUEPRINT.md`.

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
