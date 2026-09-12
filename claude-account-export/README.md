# Claude Account Export — Complete Skill & Capability Backup

**Exported:** 2026-09-11
**Account:** gustavo.paulos@icloud.com (fgomes77)
**Source:** Claude Code remote session (claude.ai/code) — account-synced skill bucket

This directory is a faithful copy of the skills synced to the Claude account
(custom-developed and Anthropic-provided), the configured persona/preferences,
and the session capability surface (MCP connectors, agents, built-in skills).
See **Known gaps** below for skills whose source uploads are incomplete, and for
one skill deliberately excluded from this export for data-protection reasons.

---

## Contents

| Path | What it is |
|---|---|
| `skills/` | File copy of 35 account-synced skills, exactly as deployed (SKILL.md, references, scripts, assets, fonts, templates) |
| `skills/manifest.json` | The account's skill manifest — skill IDs, sources, descriptions, last-updated timestamps (redacted: the excluded skill's entry removed) |
| `local-skills/session-start-hook/` | Environment-local skill provisioned in the remote container |
| `advisor-knowledge/` | Authored knowledge pack grounding the persona domains the skill uploads did not cover (ISO/IEC 27005, NIST CSF 2.0, CIS v8.1, GDPR Art. 28/SCCs 2021/914, management-frameworks compendium) plus the persona-coverage traceability matrix — authored 2026-09-11, not exported claude.ai content (each file carries a provenance header) |
| `platform-skills/` | Complete copy of `/mnt/skills` from the session container — Anthropic's 8 public and 32 example built-in skills, each as an unpacked folder plus its packaged `.skill` bundle (canonical upstream: <https://github.com/anthropics/skills>) |
| `environment/ENVIRONMENT.md` | Manifest of the session container: root filesystem layout, what is and isn't exportable, OS and toolchain versions |
| `PERSONA.md` | The configured user persona / response preferences (system-level profile) |
| `CAPABILITIES.md` | MCP servers, connectors, agent types, and built-in platform skills available to the account's sessions |

## Skill inventory (35 skills)

### Custom-developed skills (18) — your own IP

| Skill | Purpose | Last updated |
|---|---|---|
| `ai-deepsearch-osint-gathering-report` | OSINT third-party security assessment → HTML dashboard | 2026-03-24 |
| `ciso-executive-summary` | CISO-grade TPRM executive summary HTML report from OneTrust PDFs | 2026-04-07 |
| `ciso-reporting` | Euronext Group CISO governance deliverables (HTML dashboard, A3 PDF, 8-slide PPTX) | 2026-05-26 |
| `cyber-forum` | ENX Information Security Assurance Q&A / threat-intelligence briefs | 2026-05-26 |
| `deepsearch-protocol` | Supplier Security DeepSearch Protocol V17.02.11 (OSINT TPRM dashboard) | 2026-03-24 |
| `dora` | DORA (EU 2022/2554) compliance advisor — ICT risk, incidents, TLPT, TPRM, RoI | 2026-05-19 |
| `dpia` | OneTrust assessment PDF → InfoSec TPA Report (DOCX) for DPO review | 2026-01-27 |
| `enx-tprm-control-center` | Entry-point menu / router for the ENX TPRM toolset | 2026-05-26 |
| `eu-ai-act` | EU AI Act (2024/1689) compliance advisor — risk tiers, GPAI, conformity | 2026-05-19 |
| `iso27001` | ISO/IEC 27001:2022 ISMS compliance assistant — SoA, Annex A, gap analysis | 2026-05-19 |
| `iso42001` | ISO/IEC 42001:2023 AI Management System (AIMS) advisor | 2026-05-19 |
| `nis2` | NIS2 (EU 2022/2555) compliance advisor — Art. 21 measures, Art. 23 reporting | 2026-05-19 |
| `onetrust-form-b` | OneTrust Non-Critical Form B questionnaire assistant with human sign-off gate | 2026-05-26 |
| `pdf-full-coverage-analyzer` | Exhaustive chunked PDF analysis with coverage verification | 2026-05-21 |
| `pptx-executive-summary-ciso` | TPRM executive summary slide generator (OneTrust PDF → board slide) | 2026-03-06 |
| `tprm-slide-generator` | TPRM executive summary slide generator (brand-consistent workflow) | 2026-02-26 |
| `tpsrca-assessment-engine` | TPSRCA assessment engine — 12 agents for risk scoring, gap analysis, evidence validation | 2025-12-11 |
| `whisperx-transcribe-diarize` | Local WhisperX transcription + speaker diarization (macOS Apple Silicon) | 2026-04-16 |

### Anthropic document skills (4) — enabled on the account

`docx`, `pdf`, `pptx`, `xlsx` — Office/PDF document creation and manipulation toolkits.

### Anthropic example skills (13) — enabled on the account

`algorithmic-art`, `brand-guidelines`, `canvas-design`, `doc-coauthoring`,
`import-memory`, `internal-comms`, `learn`, `mcp-builder`, `morning`,
`skill-creator`, `slack-gif-creator`, `theme-factory`, `web-artifacts-builder`.

Anthropic skills are also published at <https://github.com/anthropics/skills>;
the copies here are the exact versions synced to this account.

## How to restore / reuse

- **Claude Code (any machine):** copy a skill folder into `~/.claude/skills/` (personal)
  or `<repo>/.claude/skills/` (project) — it becomes invocable as `/<skill-name>`.
- **Claude.ai:** re-upload a skill folder (zipped) under Settings → Capabilities → Skills.
- **Claude API / Agent SDK:** pass the skill directory via the skills configuration.

Each skill is self-contained: `SKILL.md` (YAML frontmatter with the trigger
description + instructions) plus optional `references/`, `scripts/`, `assets/`.

## Known gaps

- **One skill excluded for data protection.** A custom forensic-analysis persona
  skill contains identifiable personal data of private individuals connected to
  an active criminal case, so it is deliberately **not** included in this export
  (and its entry was removed from `manifest.json`). It remains available on the
  Claude account; keep any copy of it out of shared or public repositories.
- **Eight skills were uploaded to claude.ai without supporting files their own
  SKILL.md instructions reference — regenerated here (2026-09-11).** The gap is
  in the source uploads (this export mirrors the account sync byte-for-byte),
  so the missing files were reconstructed and added to this backup, each marked
  in its header as a dated reconstruction:
  - `dora` — four references (64-article guide, RTS/ITS guide, incident
    classification per CDR 2024/1772, third-party risk Arts. 28-44) rebuilt
    from SKILL.md and the official texts.
  - `eu-ai-act` — three references (risk classification, high-risk
    obligations, GPAI governance) rebuilt likewise.
  - `iso27001` — Annex A 2022 (93 controls) and 2013 (114 controls)
    catalogues plus the 2013-to-2022 mapping; summaries in original wording,
    not verbatim standard text.
  - `iso42001` — clause 4-10 requirements, the 38-control Annex A catalogue,
    and the AI risk / impact assessment methodology.
  - `nis2` — the Art. 21(2)(a)-(j) measures guide and the ISO 27001:2022
    mapping.
  - `ciso-executive-summary` — `assets/template.html` rebuilt from the
    surviving `references/html-template-spec.md` (tokenized placeholders
    replace the lost original's baseline data).
  - `tprm-slide-generator`, `pptx-executive-summary-ciso` —
    `references/data_schema.md` and `references/template_layout.md` derived
    directly from the skills' own scripts and template constants.

  The reconstructions are faithful to each SKILL.md's citations but are not
  the original files: verify regulatory citations against EUR-Lex / official
  ISO publications before relying on them, and consider re-uploading the
  completed skill folders to claude.ai so account sync and backup converge.
  Corrected upstream error: `dora/SKILL.md` as deployed inverted DORA
  Art. 30(2)/30(3) (the regulation has 30(2) as the all-services baseline and
  30(3) as the critical/important-function additions). The copy in this export
  is corrected (Art. 30 section, gap-analysis table, common-errors table) —
  the deployed skill on claude.ai carries the error until re-uploaded from
  here.

## Known limitations of this export

- **Claude.ai Project knowledge files and chat history are not reachable from a
  Claude Code session container** — this export covers everything synced to the
  session environment (skills, manifest, persona, capabilities). Project knowledge
  documents must be exported from claude.ai (Settings → Privacy → Export data, or
  per-project download).
- Connector credentials (Gmail, Google Drive, GitHub, Adobe, Canva, etc.) are
  OAuth grants held by Anthropic and are intentionally **not** exportable; only
  the connector roster is documented in `CAPABILITIES.md`.
- A secret and PII scan was run over every exported file before commit; the only
  secret-pattern match is a documentation placeholder (`hf_xxxx…` in the WhisperX
  install guide), and the one skill containing personal data was excluded (see
  **Known gaps**).
