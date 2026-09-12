# tpsrca-assessment-engine — Foundry overlay

(Appended after the SKILL.md body; environment mapping only.)

- **Phase 1 — supplier tier:** the classifier skill is not in the export.
  Use `advisor-knowledge/tpsrca-supplier-types.md` (A.01–D.05 catalogue +
  scope matrix) from your knowledge store; if the type is ambiguous ask the
  user, and record the chosen type and rationale in the output JSON.
- **Phase 2 — OSINT collection:** `tpsrca-osint-agents` are not in the
  export. Delegate to the connected agent `deepsearch_protocol` (same 7
  collection streams); pass only public terms (supplier name, domain,
  products). Take its returned section data as `osint_data`.
- **Phases 3–5 — calculation:** run `calculation_engine.py` from your
  `code_interpreter` files on the collected data; it is the SINGLE
  deterministic scorer (inherent/residual, composite, rating). Never
  estimate scores in prose.
- **12 agents:** they are roles inside this agent unless the deployment
  attached `tpsrca_calc` / `tpsrca_analysis` / `tpsrca_report` connected
  agents (optional split); either way each phase's output names the role
  that produced it for traceability.
- Storage/format: outputs go through the orchestrator to the matching
  pipeline (`ciso-global-pptx` consumes your JSON when the user wants the
  CISO deck). Intake: Supplier + Service names.
