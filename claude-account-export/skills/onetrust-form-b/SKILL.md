---
name: onetrust-form-b
description: >
  Assists with completing the OneTrust Non-Critical Form B supplier assessment
  questionnaire — drafts evidence-led responses for each question, validates
  them against the allowed answer options, routes them through a mandatory
  human sign-off gate, and writes the approved answers back into the OneTrust
  round-trip import xlsx. Use when the user asks to "answer Form B", "complete
  the OneTrust Form B", "fill the Form B", "draft Form B responses", or uploads
  a OneTrust Form B export (PDF and/or xlsx) and asks for help responding.
  Bounded-agency workflow: the skill gathers evidence and proposes answers but
  never finalises them without explicit user approval.
---

# OneTrust Form B — Assisted Completion

Completes the **Non-Critical Form B – Sept2025 (template v5)** — the OneTrust
supplier-assessment questionnaire ENX issues to third parties. 35 questions
across 9 sections; the canonical structure is bundled in `references/`.

## The two-input rule

A OneTrust Form B is exported as **two files** and the skill is most accurate
with both:

- **The PDF export** — question text, section grouping, the respondent split,
  and the conditional follow-up guidance ("If 3, 4 or 5, please provide…").
- **The XLSX export** — the OneTrust round-trip import template. Its
  `Assessment Responses - v2` sheet is what gets re-imported; its
  `Assessment Response Options` sheet holds the exact answer ladders.

If the user provides **only the xlsx**, the skill can still run — the bundled
`references/form_b_catalogue.json` carries the question text and the option
ladders for the standard v5 template. If the user provides **only the PDF**,
the skill can draft answers but **cannot produce the filled import file** — ask
for the xlsx export to deliver that. Always tell the user which case applies.

## Why this is bounded-agency, not full-auto

Form B answers are a **compliance output** sent to a supplier and re-imported
into OneTrust. The skill is permitted judgement in **retrieving evidence and
matching it to a response option**, but the **answer set is never final until a
human approves it**. No exceptions, no "approve to save time" shortcut. This
mirrors the verified-JSON gate in `ciso-reporting`: the human checkpoint is the
control, not friction.

## Inputs

| Input | Required | Notes |
|-------|----------|-------|
| Form B xlsx export | For the filled-file output | The OneTrust round-trip template. |
| Form B PDF export | Recommended | Adds conditional guidance not in the xlsx. |
| Evidence | Yes | Vendor docs, certifications, prior assessments, SecurityScorecard, policies — uploaded by the user. |
| Respondent context | Recommended | Which questions the user can answer (Supplier vs. C.O. split). |

## Reference files (bundled — read when needed)

- `references/form_b_structure.md` — section map, question types, the
  conditional-evidence rule. Read this first.
- `references/form_b_catalogue.json` — 35 questions with id, text, guidance,
  OneTrust UID, question type.
- `references/form_b_options.json` — exact allowed answer strings per question.

## The question-type rule

Each question's `question_type` dictates how it is answered — see
`form_b_structure.md`. Critically:

- `Statement` → no response (section header). Leave blank.
- `MultiChoice - single select` → exactly one string copied **verbatim** from
  `form_b_options.json`. A paraphrase will fail the OneTrust import.
- `Yes-No` → `Yes` / `No` / sometimes `NotApplicable`.
- `Inventory`, `Engagement`, `Contract`, `Controls`, `Personal Data` → **not
  importable via the sheet**. The skill flags these and tells the user they
  must be set directly in the OneTrust UI; it does not fabricate them.

## The conditional-evidence rule

Many questions carry a follow-up keyed to the answer (e.g. 3.2 — "For 1,2,3
answers please provide the relevant certifications"). When the chosen answer
triggers a follow-up, the skill records the evidence requirement in the
**Justification** column and flags it to the user. The attachment itself is
uploaded in the OneTrust UI — the skill cannot attach files, only state what is
required.

## Workflow

1. **Identify inputs.** Determine whether the user has the xlsx, the PDF, or
   both. State which output is achievable (see the two-input rule).
2. **Load the question set.** From the uploaded xlsx, or fall back to the
   bundled catalogue for the standard v5 template.
3. **Map evidence to questions.** For each question the user has evidence for,
   match the evidence to the correct answer option. Respect the respondent
   split — do not answer a Supplier question from C.O.-side assumptions.
4. **Draft the answer set.** Per question: `response` (verbatim option or free
   text) · `justification` · `confidence` (🟢/🟠/🔴 per SSOT §3) · `status`
   (`Answered` | `EVIDENCE GAP` | `UI-ONLY`). Never invent evidence — a
   question with no support is `EVIDENCE GAP`, not a guess.
5. **Present for review.** Show the full draft as a table grouped by section,
   with confidence and any evidence gaps explicit.
6. **Mandatory sign-off gate.** Do not write any file until the user explicitly
   approves. Approval may be all-at-once or question-by-question; corrections
   loop back to step 5.
7. **Write the import file.** On approval, save the approved answers to
   `<vendor>_form_b_answers.json` and run:
   ```bash
   python onetrust-form-b/scripts/fill_form_b.py \
     --xlsx <onetrust_export.xlsx> \
     --answers <vendor>_form_b_answers.json \
     --out /mnt/user-data/outputs/<vendor>_Form_B_filled.xlsx
   ```
   The script edits only the Response and Justification columns and validates
   single-select answers against the option ladder — read its output for any
   `VALIDATION WARNING` and fix before delivering.
8. **Deliver** the filled xlsx with `present_files`, plus a summary listing
   answered counts, evidence gaps, and UI-only questions still outstanding.

## Answer-file format (`<vendor>_form_b_answers.json`)

```json
{
  "3.1": {"response": "1 - ISMS in place and documented with continuous monitoring",
          "justification": "ISO 27001 certificate attached (valid to 2027)."},
  "5.2": {"response": "2 - Security ScoreCard B",
          "justification": "SecurityScorecard rating B, retrieved 05/2026."}
}
```

Keys are question ids; `response` must be a verbatim option string for
single-select questions. `justification` is optional but expected wherever a
conditional follow-up applies.

## Parameters

Confidence bands and in-scope frameworks come from the SSOT —
`../enx-tprm-control-center/references/shared-parameters.md` (§3, §7).

## Output

`<vendor>_Form_B_filled.xlsx` — the OneTrust import file with verified
responses (produced only after sign-off) — plus an inline summary of evidence
gaps and any UI-only questions that must be completed directly in OneTrust.
