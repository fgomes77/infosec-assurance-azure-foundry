# Third-Party IP Register — Anthropic-licensed skills in the export

Fourteen exported skills carry `LICENSE.txt` ("© 2025 Anthropic, PBC …
use governed by your agreement with Anthropic … Additional Restrictions").
The export README and `MAPPING.md` treat them as convertible; no legal
decision was recorded. This register records the position so the ENX
ISO/IEC 42001 AIMS (A.10 third-party relationships) and the EU AI Act
deployer assessment (`AI-ACT-DEPLOYER-ASSESSMENT-TEMPLATE.md`) can cite
it. Nothing in `claude-account-export/` or `build/` is altered.

## 1. Licensed material and how the kit uses it

| Skill | Role in the platform | Use in Foundry | Exposure |
|---|---|---|---|
| `docx`, `pdf`, `pptx`, `xlsx` | Office-document generation agents (`light` tier) and the scripts the delivery Function / code_interpreter run | instructions + scripts + schemas redeployed; persona / approval-gate preambles prepended (a derived instruction set) | HIGH — copies retained outside the Services, derivative works |
| `algorithmic-art`, `brand-guidelines`, `canvas-design`, `slack-gif-creator`, `theme-factory`, `web-artifacts-builder`, `skill-creator` | not deployed (`PLATFORM_SPECIFIC` / EXCLUDED in `PLATFORM_SKILLS_DECISION.md`) | retained in the repository as export fidelity evidence only | LOW — no redeployment |
| `internal-comms`, `learn`, `mcp-builder` | converted as agents (`chat` / `reasoning`) | instructions redeployed with preambles | MEDIUM |

Restriction summary (verbatim terms in each `LICENSE.txt`): no
extraction from the Services, no copies outside the Services, no
derivative works, no distribution.

## 2. Decision of record

| Field | Value |
|---|---|
| Decision | **PENDING — option A preferred.** A: obtain written permission from Anthropic under the Commercial Terms for the seven redeployed skills ({confirm which Agreement applies — Commercial Terms expected}; the request cites this file). B: replace `docx`/`pdf`/`pptx`/`xlsx` with ENX-authored instruction sets over the same open-source libraries (python-docx, pypdf, python-pptx, openpyxl) plus the delivery Function renderers, and drop `internal-comms`/`learn`/`mcp-builder` (no mission dependency). |
| Accountable owner | `{upn:owner}` (Francisco Gustavo Gomes) |
| Consulted | `{group:legal}`, `{group:dpo}` |
| Target date | `{date}` — before production go-live (IMPLEMENTATION_SERIES gate) |
| Interim control | The seven redeployed skills are conversion-gated: `convert_skills.py` must require `--accept-anthropic-license` for the `LICENSE_RESTRICTED` set and exclude `LICENSE.txt` from vector stores (shared delta). Until the flag is implemented, the owner records acceptance here: `accepted-by: {upn} on {date}` |
| Result-fidelity note | Option B changes byte-level outputs of the four office agents; the comparison set (`operations/CHANGE_MANAGEMENT.md` §4) must be re-baselined if B is chosen. |

## 3. Other third-party content

| Component | Licence | Position |
|---|---|---|
| ENX-authored skills (deepsearch, ciso-*, dpia, onetrust-form-b, tpsrca, cyber-forum, control-center, framework advisors, pdf-full-coverage-analyzer, whisperx) | Euronext internal — no `LICENSE.txt` | Internal IP; classification Euronext Internal |
| Regulatory texts in references (DORA, NIS2, EU AI Act, GDPR) | EU public documents (reuse permitted with source) | Retained; cite EUR-Lex |
| ISO standards summaries in references | ISO copyright — summaries/mappings only | Keep to control ids + paraphrase; never store full standard text in vector stores |
| Open-source libraries pinned by renderers/Function | per `functions/delivery/requirements.txt` / `package.json` | SBOM in the CI job (shared delta, `ci/`) |

Review: annually and on every re-sync from a fresh export
(`operations/LIFECYCLE.md` §3).
