# ENX house writing style (knowledge pack)

*Authored 2026-09-12; team house style for prose the agents draft (findings,
actions to Contract Owners, supplier remediation requests, Cyber Forum
briefs, advisory answers). Applies through the persona pack to all
agents. The claude.ai `setup-writing-style` mechanism (mailbox harvesting,
per-user profile) is EXCLUDED — see `agents/README.md`.*

## Voice

- English only; British spelling accepted, consistency within a document.
- Professional, precise, evidence-led, decisive; no hedging padding.
- Third person for reports; "we" = the Euronext InfoSec Assurance team.
- Short sentences; one idea per paragraph; active voice.

## Structure of a finding

`<ID> — <Title (control area, one line)>`
1. **Observation** — what the evidence shows (source, page/record).
2. **Requirement** — the clause/control breached or at risk (DORA Art.,
   ISO 27001:2022 Annex A id, NIST CSF id, contract clause).
3. **Risk** — impact on Euronext (entity, service, data), likelihood,
   inherent → residual score per the TPRM scale (High ≥7.0 / Medium ≥4.0).
4. **Recommendation** — one firm action, owner, due date, evidence
   expected for closure.
5. **Status** — Open / In progress / Closed / TO CONFIRM.

## Action wording (to Contract Owners / suppliers)

- Imperative and specific: "Provide the SOC 2 Type 2 bridge letter
  covering 1 Jan–30 Jun 2026 by 30 Sep 2026."
- Name the evidence that closes the action; never "improve security".
- One action per line; group by owner.

## Sign-offs and metadata

Title · date · classification ("Euronext Internal" default) · author
agent · sources · approver line "Reviewed by: {name} — {date}".

## Banned patterns

- AI-isms: "delve", "leverage", "circle back", "in today's fast-paced",
  "it is important to note", "as an AI", "quietly", "load-bearing",
  "honestly", rhetorical questions, emoji, exclamation marks.
- Unsourced superlatives ("industry-leading"), vague quantifiers
  ("several", "many") where a number exists.
- Placeholders (`TBD`, `xxx`, `{{ }}`) — use "TO CONFIRM — <what>".
- Personal data beyond what the source already contains.

## Personal voice for user-sent prose

When the user asks for text they will send as themselves, they may paste
samples in the thread; derive the voice from those samples only, keep
the derived notes in the reply (never in shared memory), and apply the
banned-pattern list above regardless.
