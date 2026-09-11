# OneTrust Form B — Canonical Structure Reference

Derived from the **Non-Critical Form B – Sept2025, template version 5** (the
OneTrust assessment-questionnaire ENX issues to suppliers). This file plus the
two JSON companions are the canonical question set for `onetrust-form-b`.

## Companion files

- `form_b_catalogue.json` — 35 questions: `id`, `question`, `guidance`,
  `uid` (OneTrust Unique Identifier), `question_type`, `option_count`.
- `form_b_options.json` — for each question with a fixed scale, the exact
  allowed response strings (copy verbatim into the import sheet).

## Why two source files are needed

A Form B is split across two artefacts and the skill needs both:

1. **The PDF export** — gives question text, section grouping, the
   respondent split, and the conditional follow-up guidance
   ("If 3, 4 or 5, please provide…").
2. **The XLSX export** — the OneTrust round-trip import/export template. Its
   `Assessment Responses - v2` sheet is what gets re-imported; its
   `Assessment Response Options` sheet holds the exact answer ladders.

The PDF alone is not enough — it does not print the selectable options. The
XLSX alone is not enough — it does not carry the conditional guidance. The
skill uses the catalogue/options JSON (built from the XLSX) and the guidance
(from the PDF) together.

## Section map (9 sections, 35 questions)

| § | Section | Qs | Respondent |
|---|---------|----|------------|
| 1 | General Information (Supplier + Service) | 19 | C.O. (Lea Sevestre) |
| 2 | Supplier — Compliance & Legal Risk Criticality | 1 | Supplier (External) |
| 3 | Supplier — Security Risk Mitigation | 2 | Supplier (External) |
| 4 | Supplier — Operational Risk (Likelihood) | 1 | Supplier (External) |
| 5 | Supplier — Security Risks (Likelihood) | 2 | Supplier (External) |
| 6 | Supplier — Compliance & Legal Risks (Likelihood) | 1 | Supplier (External) |
| 7 | C.O. — Operational Risk Criticality | 5 | C.O. |
| 8 | C.O. — Security Risk Criticality | 3 | C.O. |
| 9 | C.O. — Security Risk Mitigation | 1 | C.O. |

**Respondent split** — "Supplier (External)" questions are answered by the
vendor contact; "C.O." (Contract Owner) questions by the internal Euronext
owner. The skill keeps this split visible so each answer is attributed to the
party who can actually evidence it.

## Question types (drives how a response is written)

| Type | How to answer |
|------|---------------|
| `Statement` | No response — section header only. Leave blank. |
| `MultiChoice - single select` | One exact string from `form_b_options.json`. |
| `Attribute - multiple select` / `MultiChoice - multiple` | Comma-space delimited list of exact option strings. |
| `Yes-No` | `Yes` / `No` (some allow `NotApplicable`). |
| `Text` | Free text. |
| `Attribute` / `Attribute - numerical text` | Free text / number. |
| `Inventory`, `Engagement`, `Contract`, `Controls`, `Personal Data` | **Not importable via the sheet** — must be set in the OneTrust UI. The skill flags these, does not attempt them. |

## Scoring scale

Risk-bearing multiple-choice questions use a **1–5 likelihood/criticality
scale** embedded in the option string ("1 - …" best, "5 - …" worst; some use
1/3/5 only). The conditional guidance is keyed to these numbers. The skill does
not compute a residual score here — Form B is a *questionnaire*; scoring happens
later in OneTrust. The skill's job is accurate, evidence-backed responses.

## The conditional-evidence rule

Many questions carry a follow-up: e.g. 3.2 — "For 1,2,3 answers please provide
the relevant certifications." When the chosen answer triggers a follow-up, the
skill must surface the evidence requirement to the user (the response is not
complete without the attachment/justification). Attachments themselves go in
the OneTrust UI; the skill records what is required in the Justification column.
