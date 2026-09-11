---
name: enx-tprm-control-center
description: >
  Entry point and router for the ENX TPRM toolset. Use ONLY when the user
  explicitly says "open ENX menu", "ENX control center", "ENX menu", "TPRM menu",
  "TPRM control center", or "start ENX". Presents a five-option menu — DPIA
  InfoSec Report, CISO Reporting, Cyber Forum, OneTrust Form B Questions,
  DeepSearch Report Dashboard — and routes the selection to the correct worker
  skill. This skill performs NO assessment, report generation, or analysis
  itself; it only displays the menu, collects the required input for the chosen
  project, and dispatches. Do NOT trigger this skill for direct, specific
  requests like "run DeepSearch on X" or "generate a DPIA from this PDF" — those
  invoke their worker skills directly.
---

# ENX TPRM Control Center

A thin router over the ENX Third-Party Risk Management toolset. It exists so one
phrase opens a single menu, and each selection loads **only** the worker it
needs — no project pays the token cost of the other four.

## Operating principle — read this first

This skill must stay cheap. Therefore:

- **Never inline worker content.** Do not paste a worker's instructions,
  templates, or parameters into this conversation. Read the worker's `SKILL.md`
  **only after** the user selects its menu number.
- **Never perform the work here.** This skill displays the menu, collects input,
  and dispatches. The selected worker does the assessment and produces the file.
- **Load parameters lazily.** Read `references/shared-parameters.md` only when a
  worker needs a cross-cutting constant (risk thresholds, approval bands, design
  tokens). Do not read it just to show the menu.

## Step 1 — Present the menu

On activation, print exactly this and then stop and wait for a number:

```
═══════════════════════════════════════════════
  ENX TPRM CONTROL CENTER
═══════════════════════════════════════════════
  1.  DPIA InfoSec Report      — DOCX TPA report for the DPO team
  2.  CISO Reporting           — canonical CISO HTML summary
  3.  Cyber Forum              — Q&A / threat-intel brief
  4.  OneTrust Form B          — assisted Form B question answering
  5.  DeepSearch Dashboard     — OSINT supplier security HTML dashboard
═══════════════════════════════════════════════
  Reply with a number (1–5) to begin.
```

## Step 2 — Dispatch on selection

When the user replies with a number, follow that row. The **Input mode** column
is the contract: `EXECUTE` means act immediately on what the user gives next;
`ASK` means request exactly the listed input, then run once it arrives — do not
ask open-ended "what do you want" questions.

| # | Project | Worker skill | Input mode | What to collect / do | Output |
|---|---------|--------------|-----------|----------------------|--------|
| 1 | DPIA InfoSec Report | `dpia` | **ASK** | Request the OneTrust third-party assessment **PDF**. On upload, read `dpia/SKILL.md` and follow it. | `.docx` TPA report |
| 2 | CISO Reporting | `ciso-reporting` | **ASK** | Request the verified assessment JSON, or a completed assessment (PDF / OneTrust export / prior TPSRCA) to extract one from. On receipt, read `ciso-reporting/SKILL.md` and follow it. | HTML + A3 PDF + 8-slide PPTX |
| 3 | Cyber Forum | `cyber-forum` | **EXECUTE** | Take the user's question as-is — no file needed. Read `cyber-forum/SKILL.md` and answer. | inline answer / short brief |
| 4 | OneTrust Form B | `onetrust-form-b` | **ASK** | Request the OneTrust Form B export (xlsx for the filled-file output; PDF too if available) and the supporting evidence. On receipt, read `onetrust-form-b/SKILL.md` and follow it. | filled import `.xlsx` + sign-off gate |
| 5 | DeepSearch Dashboard | `deepsearch-protocol` | **ASK** | Request the supplier **name or domain**. On receipt, read `deepsearch-protocol/SKILL.md` and follow it. | single-file `.html` dashboard |

If the user names a project in plain language instead of a number ("I need a
DPIA"), map it to the matching row and dispatch the same way.

## Step 3 — Hand off cleanly

Once dispatched, the worker skill owns the task end to end. Do not re-summarise
the menu, do not interleave other workers, and do not narrate the routing. After
the worker delivers its output file, you may offer to return to the menu
("Reply *ENX menu* to run another."), but do not force it.

## Worker registry

All five workers are live. Each dispatches and runs end to end.

| Worker skill | Status | Notes |
|--------------|--------|-------|
| `dpia` | ✅ Live | OneTrust PDF → DOCX TPA report. |
| `deepsearch-protocol` | ✅ Live | Supplier OSINT → HTML dashboard (V17.x). |
| `ciso-reporting` | ✅ Live | Verified JSON → HTML + A3 PDF + 8-slide PPTX (`generate_reports_v2.py`). |
| `cyber-forum` | ✅ Live | Security Q&A + threat-intel brief. Runs on default source list. |
| `onetrust-form-b` | ✅ Live | OneTrust Form B export → evidence-led answers → filled import xlsx. v5 question set bundled. |

## Single source of truth

All cross-cutting constants — the TPRM risk threshold override, TPSRCA approval
bands, OneTrust scale, and HTML design tokens — live in
`references/shared-parameters.md`. Workers reference that file so no parameter is
defined twice. If a worker's own `SKILL.md` ever conflicts with it, the SSOT
wins for thresholds and design tokens (per the standing TPRM Risk Threshold
Override). Do not copy the SSOT contents into a worker; point to the file.
