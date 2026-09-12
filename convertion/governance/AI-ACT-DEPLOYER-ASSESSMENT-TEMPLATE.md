# EU AI Act Deployer Assessment + ISO/IEC 42001 checklist — template

Fill once per environment (test, prod) before go-live (IMPLEMENTATION
SERIES gate) and at every material change (`operations/CHANGE_MANAGEMENT.md`
§5 "high"). Pre-filled with the platform controls; `{…}` are to complete.

| Field | Value |
|---|---|
| AI system | InfoSec Assurance agent platform on Microsoft Foundry (formerly Azure AI Foundry) — agents a–j, orchestrator, verifier, delivery pipelines, Teams / M365 Copilot channel |
| Deployer | Euronext — `{legal-entity}`; accountable owner `{upn:owner}` (Francisco Gustavo Gomes) |
| Providers | Microsoft (Azure OpenAI / Foundry catalogue models); Anthropic (skill instruction sets, see `THIRD_PARTY_IP.md`) |
| Assessment date / version | `{date}` / kit release `{release}` (`operations/LIFECYCLE.md` §2) |

## 1. Risk classification (Art. 6, Annex III)

| Question | Position | Evidence |
|---|---|---|
| Prohibited practice (Art. 5)? | No — supplier/document analysis, no biometric, social scoring, emotion recognition | this table |
| Annex III high-risk area? | **To confirm by `{group:legal}`**: outputs concern suppliers (legal persons), not natural persons' access to services/employment; evidence analysis of pentests/SOC reports is not a listed area. Working position: NOT high-risk; limited-risk transparency (Art. 50) applies to generated content | `{decision-ref}` |
| GPAI models used (Art. 51–55)? | Yes (provider obligations rest with Microsoft/OpenAI/Anthropic); deployer relies on provider documentation | provider docs `{link}` |

## 2. Deployer duties (Art. 26) → platform control

| Duty | Control | Evidence |
|---|---|---|
| Use per provider instructions (26(1)) | pinned model versions, default RAI content filters | `infra/main.bicep`, `MODEL_ROUTING.md` |
| Human oversight by competent persons (26(2), Art. 14) | verifier PASS + human approval before any write; approver ≠ requester | `HUMAN_APPROVAL.md`, `team/approval-policy.json`, Logic Apps run history |
| Input data relevant and representative (26(4)) | evidence taken from the assessment record / supplier files only; sources cited; "TO CONFIRM" for unknowns | persona principles 1, 5; verifier rule 3 |
| Monitoring and provider/authority reporting (26(5)) | App Insights alerts (`infra/monitoring.bicep`, `infra/kql/`), incident procedure `operations/RUNBOOK.md` | alert history |
| Log retention ≥ 6 months (26(6)) | Log Analytics retention 365 days (`logRetentionDays`), Foundry tracing | Bicep parameter |
| Inform workers / affected persons (26(7)) | team onboarding (`team/ONBOARDING.md`); outputs carry agent + verifier traceability (verifier rule 6) | onboarding record |
| Transparency of AI-generated content (Art. 50(2)) | deliverables state the producing agent; Copilot channel disclosure text | verifier rule 6, `enterprise/ENTERPRISE_BLUEPRINT.md` (Copilot surface) |
| DPIA where required (26(9)) | personal data limited to what the source assessment contains; memory store policy | `MEMORY_POLICY.md`, `DATA_PROTECTION_GUARDRAILS.md` §3 |

## 3. ISO/IEC 42001 Annex A checklist (deployer scope)

| Control | Implemented by | Status |
|---|---|---|
| A.2 policies for AI | this file + `HUMAN_APPROVAL.md` + `DATA_PROTECTION_GUARDRAILS.md` | `{ok/gap}` |
| A.3 roles / accountability | `team/RACI.md`, `team/TEAM_MODEL.md` | `{ }` |
| A.4 resources (data, tooling, competence) | vector-store inventory (`operations/BACKUP_DR.md` §1), onboarding | `{ }` |
| A.5 impact assessment | §1–2 above; supplier impact = assessments remain human-approved | `{ }` |
| A.6 AI system life cycle | `operations/LIFECYCLE.md`, `CHANGE_MANAGEMENT.md`, comparison set vs claude.ai | `{ }` |
| A.7 data for AI systems | residency EU, minimisation, memory policy, `THIRD_PARTY_IP.md` | `{ }` |
| A.8 information for interested parties | `team/USER_QUICKSTART.md`, transparency text | `{ }` |
| A.9 use of AI systems | approval gates, read-only posture, egress rules; second channel (Copilot) in scope | `{ }` |
| A.10 third-party relationships | Microsoft/Anthropic terms, `THIRD_PARTY_IP.md`, DORA Art. 28/30 evidence under `Reports/<Supplier>/<Service>/` | `{ }` |

## 4. Automated processing inventory (add rows on change)

| Processing | Inputs | Agent / component | Human gate |
|---|---|---|---|
| OSINT supplier assessment | public web (sanitised), assessment record | deepsearch agents | verifier + approval before SharePoint |
| Evidence-tree scanning (certificates, SOC, pentest, PCI) | supplier files in `GRC/TPA/Active` | tpa/soc/pentest analyzers | same |
| Assessment → CISO/DPO reports | OneTrust PDF | ciso-*, dpia | same |
| Template propagation | template review package | template-manager + `template-update-approval.json` | owner approval (P7D) |
| Team memory | human notes | `memory_store.py` | human is the writer |

Sign-off: owner `{upn:owner}` `{date}` · DPO `{upn:dpo}` `{date}` · Legal `{upn:legal}` `{date}`
