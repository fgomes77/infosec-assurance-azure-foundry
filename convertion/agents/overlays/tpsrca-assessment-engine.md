# tpsrca-assessment-engine — Foundry overlay

(Appended after the SKILL.md body; environment mapping only.)

- **Phase 1 — supplier tier:** the classifier skill is not in the export.
  Use `advisor-knowledge/tpsrca-supplier-types.md` (A.01–D.05 catalogue +
  scope matrix) from your knowledge store; if the type is ambiguous ask the
  user, and record the chosen type and rationale in the output JSON.
- **Phase 2 — OSINT collection:** `tpsrca-osint-agents` are not in the
  export. Hand off (A2A) to the published agent `deepsearch_protocol` (same 7
  collection streams); pass only public terms (supplier name, domain,
  products). Take its returned section data as `osint_data`.
- **Phases 3–5 — calculation:** run `calculation_engine.py` from your
  `code_interpreter` files on the collected data; it is the SINGLE
  deterministic scorer (inherent/residual, composite, rating). Never
  estimate scores in prose.
- **12 agents:** they are roles inside this agent unless the deployment ran
  the optional split, which is implemented by
  `scripts/create_tpsrca_subagents.py`. The published agent names are
  hyphenated: **`tpsrca-calc`** (roles 4–8; owns `calculation_engine.py` and
  is the only agent that produces a number), **`tpsrca-analysis`** (roles 2,
  3 and 9–11), **`tpsrca-report`** (role 12). This agent keeps **role 1** as
  the coordinator and reaches them with `ROUTE: <agent-name>` hand-offs.
  Either way each phase's output names the role that produced it for
  traceability, and the numbers always come from the calculation engine.
- Storage/format: outputs go through the orchestrator to the matching
  pipeline (`ciso-global-pptx` consumes your JSON when the user wants the
  CISO deck). Intake: Supplier + Service names.
