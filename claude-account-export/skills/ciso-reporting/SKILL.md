---
name: ciso-reporting
description: >
  Generates the three Euronext Group CISO Governance Meeting deliverables from a
  verified OneTrust Infosec Form (v14) assessment — an interactive HTML
  dashboard, an A3 landscape PDF, and an 8-slide PPTX deck. Use when the user
  asks for a "CISO report", "CISO reporting", "CISO ExecSummary", "TPRM
  governance deck", "executive risk summary", or a management-level write-up of
  a completed supplier assessment. The pipeline is deterministic: the
  orchestrator script does classification, threshold scoring, perimeter
  analysis, and rendering. Claude's only judgement task is producing the
  verified assessment JSON the script consumes.
---

# CISO Reporting — Group CISO Governance Meeting Deliverables

Turns one verified assessment into the three canonical Group CISO deliverables
via the orchestrator `scripts/generate_reports_v2.py` (v2 pipeline):

1. `{Vendor}_CISO_ExecSummary.html` — interactive dashboard
2. `{Vendor}_CISO_ExecSummary.pdf` — A3 landscape (Playwright)
3. `{Vendor}_CISO_TPRM_Governance.pptx` — 8-slide deck (token render)

## The one rule that governs this skill

**The script is the source of truth for every number, colour, and threshold.**
Claude does not compute domain scores, classify risk bands, write the spider
graph, or hand-render HTML. Claude's *only* job is to produce an accurate
**verified assessment JSON**; the orchestrator does phases 2–9 deterministically.
This separation is deliberate — it is why the output is reproducible and
audit-defensible. Do not bypass the script.

## Input contract — the verified JSON

The orchestrator consumes a **verified assessment JSON**, never a raw PDF.
OneTrust v14 exports are OCR-noisy and vendor-tunable, so PDF→JSON extraction is
intentionally *out of scope here* and a human verifies the JSON before render
(the data-accuracy lesson from the 3/3-vs-2/3 KPI miss).

`assets/assessment_schema_example.json` is the canonical shape. Required
top-level fields: `vendor`, `assessment_id`, `organisation`, `template_name`,
`date_created`, `date_completed`, `analyst`, `analyst_decision`, `manager`,
`manager_decision`, `dora_in_scope` (bool), `critical_supplier` (bool),
`service_criticality`, `supplier_type`, `certifications`, `cert_valid` (bool),
`approval_status`, `risks[]`, `findings[]`, `perimeter{}`, `crit_findings[]`,
`dora_actions[]`.

Each `risks[]` item: `rid`, `desc`, `category` ("Security"|"Operational"),
`domain` (one of the 5 below), `inherent`, `residual` (0 / null when Under
Review), `target`, `stage` ("Treated"|"In Treatment"|"Open"), `controls[]`
(each `{id, status}` — Euronext-owned controls have an id starting "Euronext").

The **5 domains** are fixed: `Cybersecurity`, `Data Management`, `IT`,
`Business Continuity`, `Third-Parties`. Every risk's `domain` must be one of
these or it is excluded from domain scoring.

## How to obtain the JSON

Ask the user which they have, then act:

- **They already have a verified JSON** → use it directly. Go to Workflow.
- **They have a completed assessment (PDF / OneTrust export / prior TPSRCA)** →
  extract the fields into the schema shape, then **present the JSON back for
  human verification before rendering**. State plainly that the script trusts
  this JSON verbatim, so any extraction error propagates into the deck.
- **They have only a supplier name** → no assessment exists yet; recommend
  running a DeepSearch (control-center menu option 5) first.

Never invent risk scores, control statuses, or findings to fill the schema. If
a field is genuinely unknown, surface the gap to the user rather than guessing.

## Workflow

1. Obtain and (if extracted) verify the assessment JSON. Save it to
   `/home/claude/<vendor>.json`.
2. Run the orchestrator:
   ```bash
   cd /home/claude
   python ciso-reporting/scripts/generate_reports_v2.py \
     --assessment <vendor>.json \
     --template ciso-reporting/assets/Group_CISO_Report_Template_v3_1.pptx \
     --outdir /mnt/user-data/outputs
   ```
3. Read the script's QA line. **`PASS - zero unsubstituted tokens`** is the
   pass criterion. If it reports `FAIL`, the JSON is missing fields the template
   expects — fix the JSON and re-run; do not hand-edit the PPTX.
4. Deliver all three files with `present_files`. State the overall risk band,
   whether proxy mode was applied, and any conditional-approval gating inline.

To smoke-test the pipeline without an assessment, run with `--demo` instead of
`--assessment` — it renders a synthetic `DEMO_VENDOR` set.

## Key behaviours the script enforces (for Claude's awareness)

Claude does not re-implement these — they are listed so Claude can explain the
output and spot a bad JSON.

- **Thresholds** (OneTrust 1–25 scale): `>12` HIGH `#DC2626` · `>4..≤12` MEDIUM
  `#D97706` · `≤4` LOW `#007D71`. These match SSOT §1 (HIGH/MED/LOW); the script
  hexes are the CISO light-theme variants.
- **Domain score** = MAX working residual across risks mapped to that domain.
- **Proxy mode** — if no risk has a positive residual (all Under Review), the
  script uses Inherent scores as working residuals and prints a PROXY
  DISCLOSURE. Expect this when the assessment is mid-flight.
- **Perimeter** — a control id starting "Euronext" → Internal; else External.
  All-internal residual exposure triggers a dedicated callout.
- **DORA in-scope** → adds the Art. 28–30 action block and red banner.

## Parameters

Cross-cutting constants are in the SSOT —
`../enx-tprm-control-center/references/shared-parameters.md` (§1 thresholds,
§2 result bands, §5b CISO design tokens). The script embeds its own copies for
deterministic rendering; if they ever diverge, the SSOT wins and the script
constants should be corrected to match.

## Dependencies

`python-pptx` and `playwright` (with Chromium) — both present in this
environment. If Playwright is unavailable, the script degrades gracefully:
it skips the spider PNG and PDF and still produces the HTML and PPTX.

## Output

Three files in `/mnt/user-data/outputs/`:
`{Vendor}_CISO_ExecSummary.html`, `{Vendor}_CISO_ExecSummary.pdf`,
`{Vendor}_CISO_TPRM_Governance.pptx`.
