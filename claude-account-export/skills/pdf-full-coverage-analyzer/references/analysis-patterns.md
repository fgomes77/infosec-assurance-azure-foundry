# Per-Chunk Analysis Patterns

This file is the practical guide for **Stage 4** — what to actually do
when reading each chunk. The schema is in `output-schema.md`; this file
explains *how* to fill it out faithfully for any topic.

## The two-axis principle

Every chunk gets analysed along two axes simultaneously:

- **CONTEXT** — what the chunk is about, where it sits in the document's structure, how it relates to other chunks. *Inferred from the text, but kept honest about being inference.*
- **DETAILS** — what the chunk actually says. *Specific, page-anchored, faithful to the source.*

Neither replaces the other. A summary without details loses nuance. Details without context lose meaning.

## Universal walkthrough

For each chunk file, do these six steps in order. Don't shortcut.

### Step 1 — Read the chunk completely, once, without producing output

Read every `[page N]` block. Notice but don't yet write down:
- What this chunk is about as a whole
- Where it sits structurally (section header? continuation? new topic?)
- What it references (forward to later chunks, backward to earlier ones)
- Anything strange (OCR noise, layout issues, ambiguity)

### Step 2 — Write the `context` block

A few sentences each:
- **`what_this_section_is_about`** — one to three sentences in plain language.
- **`document_role`** — pick one tag (see schema). If unsure, pick `other` and explain in `what_this_section_is_about`.
- **`structural_position`** — be specific: *"continuation of Section 4.3, beginning"*, *"start of Chapter 7"*, *"table of contents pages"*, *"appendix B mid-section"*.
- **`key_entities_introduced`** — people, organisations, products, concepts, terms first defined here.
- **`key_entities_referenced`** — entities mentioned but assumed already known.
- **`relation_to_prior_chunks`** — does it continue, contradict, refine, or stand alone? If the chunk is chunk 1 of the document, say `independent`.
- **`open_threads_for_later_chunks`** — anything the chunk promises but does not deliver ("we will explore this in Section 5").

This is the navigation layer. A reader who reads only your context blocks should understand the document's shape.

### Step 3 — Write the `details` array

Go page by page through the chunk. For each page, ask:

- What **facts** are stated? (events, observations, descriptions)
- What **claims** are made? (assertions that could be questioned)
- What **definitions** are given? (terms, concepts, scope)
- What **numbers** appear? (figures, rates, counts, amounts — capture units!)
- What **names** appear? (people, places, organisations, products, statutes, standards)
- What **dates** appear? (events, deadlines, durations)
- What **conditions / requirements / exceptions** are stated?
- What **citations / references** are given? (sources, cases, prior works)
- What **examples / instructions** appear?

Each detail becomes one entry in the `details` array. **Anchor every entry to a page number**, even when the chunk spans many pages.

### Step 4 — Decide where to quote verbatim

Most details should be paraphrased faithfully — paraphrasing demonstrates comprehension and avoids copyright issues. But for some details, the *exact wording* is the point:

- Legal contract clauses
- Statutory language
- Definitions that are themselves subject to interpretation
- Numerical thresholds expressed with specific units or conditions
- Direct quotations the document itself is making
- Names of standards, statutes, articles, sections

For those cases, fill `exact_quote_if_critical` with a verbatim quote **≤ 15 words**. Otherwise leave it empty. Quoting longer than 15 words violates copyright handling rules — if a detail truly cannot be captured in 15 words, paraphrase and explain that the source is more elaborate.

### Step 5 — Note open questions and quality

- **`open_questions`** — what does this chunk leave unresolved? *(Not the same as `open_threads_for_later_chunks` — open questions may never be resolved anywhere in the document.)*
- **`user_query_relevance`** — given the user's specific question, how relevant is this chunk? High / medium / low / none. Never let "none" be a reason to skip recording details — it just guides synthesis prioritisation later.
- **`extraction_quality_notes`** — OCR noise? Mid-sentence breaks? Tables that didn't extract cleanly? Be specific so the synthesis stage knows where to apply skepticism.

### Step 6 — Sanity check before moving on

Before going to the next chunk:

- Do the `details` cover every page in the chunk? Yes/no per page.
- Is anything important still in the text that didn't make it into `details`? If yes, add it.
- Does the `context` make sense given the `details`? They should align.
- Are there any claims in `context` that aren't supported by `details`? Remove them — `context` is inference, but it must be inference grounded in what's actually there.

---

## Topic-specific adaptations

The same two-axis structure works everywhere, but emphasis shifts by document type. Use these as starting prompts for the `details` array; the schema doesn't change.

### Legal / contractual documents

Emphasize:
- Parties, defined terms, effective dates, termination conditions
- Obligations (who must do what, by when, on what condition)
- Rights and remedies
- Liability limits, indemnities, warranties
- Governing law, jurisdiction, dispute resolution
- Cross-references (Section X, Schedule Y, Annex Z)
- **Use verbatim quotes generously** for clause text — wording matters legally.

### Regulatory / compliance documents

Emphasize:
- Scope (who/what is regulated, effective territory)
- Definitions
- Obligations and prohibitions
- Thresholds (timeframes, quantities, classifications)
- Sanctions, penalties, enforcement mechanisms
- Cross-references to other regulations and articles
- Effective dates and transition periods
- **Quote verbatim** for article text, definitions, and thresholds.

### Scientific / academic papers

Emphasize:
- Hypotheses, claims, conclusions
- Methodology details (population, instruments, statistical methods)
- Numerical results with units and uncertainty
- Cited prior work
- Limitations stated by the authors
- Funding, conflicts of interest
- Tables and figures — describe what they show, page-anchored

### Medical records / case reports

Emphasize:
- Patient demographics (de-identify in the output if appropriate)
- Diagnoses, codes (ICD, SNOMED), and dates
- Medications (drug, dose, route, frequency, dates)
- Procedures, results, vitals — with units
- Allergies, contraindications, alerts
- Clinical decisions and reasoning
- Quote verbatim for ambiguous clinical wording.

### Financial filings / reports

Emphasize:
- Reporting period, currency, accounting basis
- Numerical figures with units and time periods (Q3 2025, FY 2024)
- Year-over-year and quarter-over-quarter comparisons stated by the document
- Forward-looking statements and assumptions
- Risk factors
- Footnotes — they often carry the substantive detail
- Named entities (subsidiaries, counterparties, auditors)

### Technical specifications / standards

Emphasize:
- Defined terms and acronyms
- Normative requirements ("shall", "must", "should", "may") with explicit identifiers
- Numerical limits, tolerances, conditions
- Test methods and acceptance criteria
- Referenced standards and versions
- Diagrams — describe what they show
- **Quote verbatim** for normative requirement language.

### Narrative documents (reports, essays, articles, books)

Emphasize:
- Arguments and their supporting evidence
- Key claims and their qualifications
- Named people, places, events, dates
- Quotations (with their original speakers attributed)
- Structure (where does the argument turn?)
- Conclusions and their reasoning

### Transcripts (depositions, interviews, hearings)

Emphasize:
- Speaker turns: who said what (anchor to page and line if line numbers are present)
- Direct quotes for substantive statements (≤ 15 words at a time; many short quotes are fine)
- Topic shifts
- Objections, rulings, off-record moments
- Times, dates, attendance, exhibits referenced
- Use `exact_quote_if_critical` generously — the wording of testimony often matters.

### Tabular / data-heavy documents

Emphasize:
- What each table represents (caption + column headers)
- Notable individual values
- Totals, averages, outliers stated in narrative around the table
- Units, time periods, scope
- Footnotes to tables
- If the table didn't extract cleanly, flag it in `extraction_quality_notes` and consider rasterising the page for visual inspection.

### When the user has not specified a topic-specific focus

Default to:

- **Context** — complete document structure: what kind of document, who wrote it, when, purpose, organisation.
- **Details** — comprehensive: every named entity, every numerical figure, every claim, every definition, every conclusion.
- **Output** — a structured outline of the document plus the complete details inventory, with page citations throughout.

---

## Cross-chunk synthesis (after Stage 5 returns COMPLETE)

With the per-chunk JSONs in hand, build the user's actual answer:

### If the user asked "extract every X"
- Walk every chunk's `details`, pick entries where `type` or `content` matches X.
- Deduplicate carefully — the same entity may appear in multiple chunks with different qualifiers; preserve the qualifiers.
- Cite the page for each entry.
- Produce a structured list (table or array).

### If the user asked "summarise"
- Walk every chunk's `context`, weave them into a structural summary that reflects the document's actual arc.
- Pull in details only where they exemplify or anchor the summary points.
- Cite pages for the anchoring details.
- Resist the temptation to compress out nuance — the value of this skill is that nuance survives.

### If the user asked a specific question
- Pull `details` from chunks with `user_query_relevance` of high or medium.
- Pull `context` from neighbouring chunks to give the relevant details their proper meaning.
- If the document does not answer the question, say so explicitly with the pages searched.

### Always
- Flag contradictions found between chunks (page X says A, page Y says B).
- Flag silence — when the user's question implies the document should address something it doesn't.
- Carry forward any `extraction_quality_notes` that materially affect confidence in the final answer.

---

## What this skill refuses to do

- Summarise the document without verifying coverage first.
- Cite pages it has not actually read.
- Hallucinate detail that wasn't in the source.
- Skim long documents and pretend they were read thoroughly.
- Use confidence theatre to paper over OCR noise or genuine ambiguity.

If you find yourself wanting to do any of these because the document is long and the user is waiting, that is exactly when you should *not* shortcut. The skill is the shortcut — use it.
