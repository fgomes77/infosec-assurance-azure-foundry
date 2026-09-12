# enx-tprm-control-center — Foundry menu addendum (v2)

(Appended after the byte-verified SKILL.md body. The original five options
stay exactly as printed above; this block ADDS the delivery systems that
exist only in the Foundry environment. Same ASK/EXECUTE contract.)

## Additional options — print them under the original menu

| # | Project | Worker (connected agent) | Input mode | What to collect / do | Output |
|---|---------|--------------------------|-----------|----------------------|--------|
| 6 | Global CISO Report | `ciso_global_report` | **ASK** | Supplier name, Service name, OT assessment PDF(s) | 9-slide PPTX (`ciso-global-pptx` pipeline) |
| 7 | TPA Evidence Analysis | `tpa_evidence_analyzer` | **ASK** | Supplier name + Service name (evidence is read from the SharePoint TPA/Active tree) | Evidence analysis DOCX |
| 8 | SOC Report Summary | `soc_report_analyzer` | **ASK** | Supplier, Service, SOC report PDF (or its SharePoint location) | SOC summary DOCX |
| 9 | Pentest Summary | `pentest_report_analyzer` | **ASK** | Supplier, Service, pentest report PDF | Pentest summary DOCX |
| 10 | Template Manager | `template_manager` | **ASK** | Which registered template to change and the requested change | Review package → approval workflow |
| 11 | TPRM Board Slide | `tprm_slide_generator` | **ASK** | OT assessment PDF | 1-slide PPTX |
| 12 | TPSRCA Engine | `tpsrca_assessment_engine` | **ASK** | Supplier name, Service name, supplier type (A.01–D.05) if known | Scored assessment JSON + report |
| 13 | CISO Exec Summary (HTML) | `ciso_executive_summary` | **ASK** | OT assessment PDF | HTML dashboard (`ciso-exec-summary` pipeline) |

## Intake rule for every option 1–13

Before dispatching, collect **Supplier name** and **Service name** (say
"n/a" for non-supplier work such as option 3 or 10): they determine the
storage path `Reports/<Supplier>/<Service>/` used by every pipeline.
Then hand off to the worker by its connected-agent tool; do not perform
the assessment yourself. If a worker tool is not attached, say so and
name the agent to be attached (`scripts/create_agents.py --only
enx-tprm-control-center --rewire`).
