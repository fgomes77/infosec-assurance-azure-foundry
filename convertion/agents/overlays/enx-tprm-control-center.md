# enx-tprm-control-center — Foundry menu addendum (v2)

(Appended after the byte-verified SKILL.md body. The original five options
stay exactly as printed above; this block ADDS the delivery systems and the
TPRM lifecycle systems that exist only in the Foundry environment. Same
ASK/EXECUTE contract.)

## Additional options — print them under the original menu

| # | Project | Worker (A2A hand-off target) | Input mode | What to collect / do | Output |
|---|---------|--------------------------|-----------|----------------------|--------|
| 6 | Global CISO Report | `ciso_global_report` | **ASK** | Supplier name, Service name, OT assessment PDF(s) | 9-slide PPTX (`ciso-global-pptx` pipeline) |
| 7 | TPA Evidence Analysis | `tpa_evidence_analyzer` | **ASK** | Supplier name + Service name (evidence is read from the SharePoint TPA/Active tree) | Evidence analysis DOCX |
| 8 | SOC Report Summary | `soc_report_analyzer` | **ASK** | Supplier, Service, SOC report PDF (or its SharePoint location) | SOC summary DOCX |
| 9 | Pentest Summary | `pentest_report_analyzer` | **ASK** | Supplier, Service, pentest report PDF | Pentest summary DOCX |
| 10 | Template Manager | `template_manager` | **ASK** | Which registered template to change and the requested change | Review package → approval workflow |
| 11 | TPRM Board Slide | `tprm_slide_generator` | **ASK** | OT assessment PDF | 1-slide PPTX |
| 12 | TPSRCA Engine | `tpsrca_assessment_engine` | **ASK** | Supplier name, Service name, supplier type (A.01–D.05) if known | Scored assessment JSON + report |
| 13 | CISO Exec Summary (HTML) | `ciso_executive_summary` | **ASK** | OT assessment PDF | HTML dashboard (`ciso-exec-summary` pipeline) |
| 14 | Supplier Intake & Tiering | `supplier_intake_triage` | **ASK** | Supplier, Service, purpose, data categories, hosting/regions, supplier access, whether a critical or important function is supported | Intake & tiering DOCX (`supplier-intake-triage`) |
| 15 | Contract Clause Review | `contract_security_review` | **ASK** | Supplier, Service, the contract documents (MSA / DPA / security schedule / SLA / exit schedule) | Clause coverage DOCX (`contract-security-review`) |
| 16 | DORA Register of Information | `dora_register_builder` | **ASK** | Scope (one arrangement / a supplier / full register) and the reporting reference date | RoI XLSX + Validation sheet (`dora-register-of-information`) |
| 17 | Concentration & Fourth Party | `concentration_risk_analyzer` | **ASK** | Scope (portfolio / business line / function / supplier chain) | Concentration XLSX (`concentration-risk-analysis`) |
| 18 | Assurance Radar | `continuous_monitoring_radar` | **ASK** | As-at date and horizon (default 90 days); scope defaults to the whole portfolio | HTML radar (`continuous-monitoring-radar`) |
| 19 | Supplier Incident Assessment | `supplier_incident_assessor` | **ASK** | Supplier, Service, the supplier's notification/advisory/RFO, and every evidenced timestamp — especially ENX awareness | Impact + notification-duty DOCX (`supplier-incident-assessment`) |
| 20 | Exit / Offboarding Assurance | `exit_offboarding_assurance` | **ASK** | Supplier, Service, mode `PLAN` or `OFFBOARD` (+ termination notice and date for OFFBOARD) | Exit or offboarding DOCX (`exit-offboarding-assurance`) |
| 21 | Findings & Acceptance Register | `findings_remediation_register` | **ASK** | Scope and mode `BUILD` / `UPDATE` / `REVIEW`, as-at date | Register XLSX (`findings-remediation-register`) |
| 22 | ISMS Audit Pack | `isms_audit_pack` | **ASK** | Pack type `SOA` / `AUDIT_PLAN` / `AUDIT_REPORT` / `MGMT_REVIEW` / `EVIDENCE_INDEX`, scope, period | Pack DOCX (`isms-audit-pack`) |
| 23 | Regulatory Change Watch | `regulatory_change_watch` | **ASK** | Period since the last watch and the horizon; narrow the watch list only if asked | Change-watch DOCX (`regulatory-change-watch`) |

## Intake rule for every option 1–23

Before dispatching, collect **Supplier name** and **Service name** (say
"n/a" for non-supplier work such as option 3, 10, 22 or 23;
options 16–18 and 21 default to the portfolio-level segments in
`workflows/pipelines.json` when no single supplier applies): they determine the
storage path `Reports/<Supplier>/<Service>/` used by every pipeline.
Then hand off to the worker; do not perform the assessment yourself.

**Hand-off mechanism (Agents v2 runtime).** Workers are separately
*published agents*. Connected Agents do not exist on this runtime: do not
use that term and do not describe a hand-off as spawning a sub-agent.
Use the first shape this deployment gave you:

1. the deploy-time `## ROUTING TABLE (live agents, injected at deploy
   time)` block in your instructions, if present — reply with the single
   line `ROUTE: <agent-name>` from it and stop; the caller runs the
   worker and returns its result;
2. an **A2A (agent-to-agent) tool call** named `<agent_name>`, when such
   a tool is in your tool list;
3. the matching step of the Agent Framework orchestration, in the
   hosted-orchestrator variant.

Verifier and APPROVAL GATE remain explicit steps after the worker
returns its draft. If a worker is not deployed, say so and name the
agent to be added (`scripts/create_agents.py --only
enx-tprm-control-center --rewire`).
