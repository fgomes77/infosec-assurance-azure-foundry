# deepsearch-protocol — Foundry overlay

(Appended after the SKILL.md body; environment mapping only.)

- **Storage:** the "Google Drive convention" (`TPA Ai/{SupplierName}/TPSRCA_*.html`)
  is replaced by the `deepsearch-report` pipeline: your single-file HTML
  (with `data-overall-score="NN"` on `<body>`) is verified, approved and
  stored under `Reports/<Supplier>/<Service>/`. Ask for **Supplier name**
  and **Service name** at intake — both are mandatory for the path.
- **Collection:** `WebSearch` → Bing grounding; `WebFetch`/`curl` →
  unavailable (use snippets, the `osint-proxy` and `passive-recon`
  read-only tools when attached, SecurityScorecard, IAF API, ENX gateway
  MCP). Queries carry public terms only.
- **Companion strategy:** the OSINT collection strategy (7 streams,
  evidence hierarchy, search best practices) from
  `ai-deepsearch-osint-gathering-report` is in your knowledge store —
  retrieve it before Phase 1.
- **Outputs:** write the HTML to `/mnt/data/outputs/` in `code_interpreter`;
  do not attempt uploads.
- **House style:** the template's dark teal RGB(0,141,127) / Verdana is
  mandatory; see knowledge pack `enx-html-design-guide.md` for the quality
  floor when filling free areas of the dashboard.
- **Low score gate:** a verified overall score below the threshold in
  `workflows/scheduled-deepsearch.json` triggers a Jira finding DRAFT —
  never a ticket creation by you.
