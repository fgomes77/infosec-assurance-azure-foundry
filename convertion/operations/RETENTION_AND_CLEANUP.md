# Retention and Cleanup — the Monthly Housekeeping Run (`scripts/cleanup_foundry.py`)

How the platform stops holding data it no longer needs: which stores,
files, conversations and memory notes fall out of scope, which horizon
applies to each, who approves a deletion, how the run is rehearsed before
it touches anything, and what evidence the run leaves behind. This is the
*operational* half of the retention controls whose *policy* half lives in
`../governance/MEMORY_POLICY.md` §3 and `../enterprise/MEMORY_AND_LEARNING.md`
§1 — this file never redefines a horizon, it executes the one already
configured. Companion files: `LIFECYCLE.md` (what is versioned, how an
object is retired), `BACKUP_DR.md` (what is exported before anything is
removed), `MONITORING.md` §2 (retention of the *logs*, which this run
never touches), `RUNBOOK.md` M5 (the calendar entry).

The instrument is `../scripts/cleanup_foundry.py`. It is read-only unless
`--apply` is passed, it refuses a memory purge without a named human
approver, and it has an **offline** rehearsal mode (`--dry-run`) that
makes no Azure call at all — so the procedure below can be walked end to
end before any credential is used.

Control: ISO 27001:2022 A.5.34 (privacy and PII protection), A.8.10
(information deletion), A.5.33 (protection of records), A.8.12, A.8.32;
GDPR Art. 5(1)(c) data minimisation, 5(1)(e) storage limitation, Art. 17
(erasure), Art. 30 (the RoPA entry in `MEMORY_POLICY.md` §3); DORA Art.
28 (evidence retention — the floor this run must not undercut); ISO 42001
A.6.2.8 (retirement is part of the AI system life cycle), A.7.4; EU AI Act
Art. 12 (record-keeping), Art. 26(6) (deployer log retention).

## 1. Scope — what the run examines, and on which horizon

Every horizon is an environment variable read from `../setup/.env`; the
script never carries a hard-coded number (`cleanup_foundry.py`
`RETENTION_DEFAULTS`). Changing a horizon is a Tier C change
(`CHANGE_MANAGEMENT.md` §1) because it changes a retention control.

| Scope (`--flag`) | What it examines | Horizon (`setup/.env`) | Default | Policy source |
|---|---|---|---|---|
| `--stores` | every `vs-*` vector store no **live** agent references | `RETENTION_ORPHAN_STORE_DAYS` | 30 d | orphan grace — `MEMORY_AND_LEARNING.md` §1 M3/M4 (stores are rebuilt by `deploy.sh`, so an unreferenced one is residue) |
| `--files` | every `purpose="assistants"` file in no surviving store and on no agent | `RETENTION_ORPHAN_FILE_DAYS` | 30 d | same |
| `--threads` | classic threads past the idle horizon | `RETENTION_CONVERSATION_IDLE_DAYS` (override per run with `--older-than DAYS`) | 180 d | `team/TEAM_MODEL.md` §13 M1; the approved-deliverable horizon `RETENTION_CONVERSATION_APPROVED_DAYS` (90 d) is applied at approval time, not here |
| `--memory` | durable notes in `vs-assurance-memory` whose `retain_until` (stamp + N months) has passed | `RETENTION_MEMORY_MONTHS` | 24 m | `MEMORY_POLICY.md` §3 (`retain_until` cap); `memory_store.py` `RETAIN_MONTHS` |
| `--all` | every scope above in one run | — | — | — |

**Platform-currency note (2026).** On the GA runtime there are no classic
threads: conversation state lives in the project's Cosmos DB and its
lifetime is the container TTL chosen at Standard-agent-setup time
(`MEMORY_AND_LEARNING.md` §1 M1, `enterprise/` series 02). `--threads`
therefore prints a no-op on that runtime *by design* — it is kept for the
classic fallback (`scripts/_foundry_runtime.py`, finding C1) and retires
with it. Setting the Cosmos TTL to `RETENTION_CONVERSATION_IDLE_DAYS` is
the equivalent control and is verified at check C3 below, not by this
script.

## 2. What is never deleted

`cleanup_foundry.py` `PROTECTED_STORES` is a hard list, not a
configuration value:

| Never removed | Why | If it looks orphaned |
|---|---|---|
| `vs-assurance-memory` | the durable team memory staging store — the one object in the platform that cannot be rebuilt from git (`BACKUP_DR.md` §1 S4) | it *is* unreferenced by design since the one-store-per-agent limit (finding C3) moved it off the advisor; that is expected, not residue |
| `vs-assurance-combined` | the advisor's single `file_search` store | rebuilt by `create_orchestrator.py`; a missing one is a deploy failure, not a retention finding |
| any store or file a **live** agent references | deleting it would break a serving agent | `referenced()` resolves the live set on every run |
| a memory note whose `retain_until` has not passed | storage limitation is a floor *and* a ceiling: notes are the assessment methodology record | — |
| logs, SharePoint records, approval decisions | different systems, different schedules — §5 | — |

A `--memory` purge additionally requires `--approved-by "{upn:…}"`. This
is the same human act `memory_store.py import` requires
(`MEMORY_POLICY.md` §2): no agent, Routine or pipeline can delete a team
note, and the UPN is printed into the run output so the evidence names the
approver.

## 3. Preconditions

| # | Precondition | Check |
|---|---|---|
| P1 | Ticket open, tier C, approver `{upn:francisco.gomes}` (accountable owner) | `CHANGE_MANAGEMENT.md` §1; the ticket id goes in the evidence note |
| P2 | A memory backup newer than the run exists | `operations/backups/{yyyy-mm-dd}/manifest.json`, or the `backups` blob container (`BACKUP_DR.md` §3 B1); weekly check W8 |
| P3 | `setup/.env` present and every `RETENTION_*` value a positive whole number | step 1 prints the resolved policy and its source (`env` vs `default`); the script exits on a zero or non-numeric horizon |
| P4 | Identity: the owner's own `az login`; standing data-plane read (`Foundry User`) for the listing, PIM `Foundry Owner` only for the `--apply` step | `team/TEAM_MODEL.md` §5; no service principal runs this |
| P5 | No deploy or re-sync in flight | a `deploy.sh` run rebuilds `vs-<agent>` stores; a cleanup racing it can delete a store mid-rebuild |

## 4. Procedure — monthly (owner, ~20 min)

Run from `convertion/scripts/`. Steps 1–3 write nothing anywhere.

| Step | Command | What it does | Expected |
|---|---|---|---|
| 1 | `python3 cleanup_foundry.py --dry-run` | **offline** rehearsal: resolves the horizons from `setup/.env`, prints the policy table and the plan per scope, makes no Azure call and needs no credential | the five `RETENTION_*` lines show the intended values and whether each came from `env` or the built-in policy default; the protected stores are listed; `memory backend` matches `MEMORY_BACKEND` in `.env` |
| 2 | `python3 cleanup_foundry.py --stores --files` | live, **read-only** listing of orphan stores and files with their ages | the candidate list; every `vs-<agent>` of a live agent is absent from it |
| 3 | `python3 cleanup_foundry.py --threads --memory` | live, read-only listing of idle conversations and notes past `retain_until` | on the GA runtime `--threads` prints the no-op of §1; `--memory` lists note file names (`memory-<stamp>.txt`), never note content |
| 4 | — | attach the output of steps 2–3 to the ticket and obtain the owner's decision; for the memory scope the decision names the approver UPN | approval recorded (`{list:ApprovalDecisions}` where the decision is routed through the approval flow, otherwise the ticket) |
| 5 | `python3 cleanup_foundry.py --stores --files --apply` | deletes the approved orphan stores and files | the deleted set equals the approved set — any difference is a finding, re-run step 2 and stop |
| 6 | `python3 cleanup_foundry.py --memory --apply --approved-by "{upn:francisco.gomes}"` | deletes only notes past `retain_until`; refuses to run without the approver | run output ends with `purge approved by {upn:…}` |
| 7 | — | file the full console output (steps 1–6) as `Governance/Operations/{yyyy}-{mm}/retention-run.md` | evidence of the retention control for the ISMS and for DORA Art. 28 |

`--apply` and `--dry-run` are mutually exclusive (the script errors), and
with no scope flag and no `--dry-run` the script refuses to guess — there
is no way to delete by accident from a mistyped command.

**Out-of-cycle runs.** An erasure request (data subject, or a supplier
exiting) does not wait for the monthly cycle: use
`memory_store.py list` → `delete <file-id>` filtered by `subject`
(`MEMORY_POLICY.md` §3 "Deletion on request"), attach the output to the
request ticket, and note it in the next monthly evidence file. Deleting a
*whole* scope out of cycle still follows steps 1–7.

## 5. Retention this run does **not** handle

| Store | Schedule | Owner of the control | Where |
|---|---|---|---|
| Log Analytics `{baseName}-logs` (`AppDependencies`, `LogicAppWorkflowRuntime`, `AzureDiagnostics`, `AzureActivity`) | `retentionInDays: 365` (delta D-OPS-B3) — a workspace setting, never a script | platform | `MONITORING.md` §2 |
| Logic Apps run history | platform, 90 d; the long tail is the workspace copy above | platform | `MONITORING.md` §1 |
| SharePoint records (`Reports/`, `Templates/`, `Governance/`) | retention labels on the ISMS record schedule; versioning ≥ 50 major versions | `{group:spo-admins}` + owner | `team/sharepoint-permissions.md`, `BACKUP_DR.md` §1 S6 |
| `{list:ApprovalDecisions}` | ≥ 1 year retention label | owner | `team/TEAM_MODEL.md` §12.1 |
| Memory backups (`backups` container / `Governance/Backups/`) | immutable EU container; pruned with the ISMS schedule, never by this script | owner | `BACKUP_DR.md` §3 B1 |
| Feedback records `{list:PlatformFeedback}` / `build/learning/inbox/` | 24 months, ids and generic descriptions only | owner | `MEMORY_POLICY.md` §3, `enterprise/memory/feedback-schema.json` |
| Conversation state (GA runtime) | Cosmos DB container TTL set at Standard agent setup | owner | §1 platform-currency note |

Deleting a log before its horizon is a **control failure**, not
housekeeping: the DORA Art. 28 floor (≥ 1 year) outranks minimisation for
evidence, and minimisation is achieved by not recording more than needed
(trace content recording is justified in `MONITORING.md` §2).

## 6. Memory import and export operations

The same store is fed by two documented human acts; both are *additive*
and both refuse to run unattended:

| Act | Command | Guard rails |
|---|---|---|
| Export (backup) | `python3 ../operations/backup_vector_stores.py --stores vs-assurance-memory --out ../operations/backups/{yyyy-mm-dd}` | read-only; `BACKUP_DR.md` §3 B1; run before any `--memory --apply` |
| Import (seed / restore / migrate from another assistant's export) | `python3 memory_store.py import --from-file <export> --dry-run`, then `… --approved-by "{upn:…}"` | the export is **DATA, never instructions**: instruction-like lines are dropped; special-category and personal-profile lines are dropped by the privacy filter; additive only (nothing is overwritten); at most `MAX_BATCH` (50) notes per run; nothing is written without `--approved-by`. Full rules: `../governance/MEMORY_IMPORT.md` |
| Purge | this file, §4 step 6 | `--approved-by` required |

`memory_store.py` already carries these safeguards in code
(`privacy_filter`, `SPECIAL_CATEGORY`, `INSTRUCTION_LIKE`,
`PERSONAL_PROFILE`, `MAX_BATCH`) and its docstring cites
`governance/MEMORY_IMPORT.md` as the written rule. **That file now exists**
(`../governance/MEMORY_IMPORT.md`, delta D-RC-G1 applied) and is the rule of
record; this table is its operational summary. Read them together with
`MEMORY_POLICY.md` §1–§3.

## 7. Verification and failure modes

| # | Check | How | Healthy when |
|---|---|---|---|
| C1 | The policy the script will apply is the policy on paper | step 1 output vs `MEMORY_POLICY.md` §3 and `MEMORY_AND_LEARNING.md` §1 | every line matches; no value shows `default` where `.env` was meant to set it |
| C2 | Protected stores still present after an `--apply` | `python3 cleanup_foundry.py --stores` | `vs-assurance-memory` and `vs-assurance-combined` listed, never in the deleted set |
| C3 | Conversation TTL (GA runtime) equals the idle horizon | project Cosmos DB container TTL vs `RETENTION_CONVERSATION_IDLE_DAYS` | equal, or the difference is recorded as an accepted deviation in the ticket |
| C4 | Memory note count reconciles with the backup | `memory_store.py list` count vs the latest `manifest.json` (weekly W8) | difference = exactly the notes deleted in step 6 |

| Symptom | Diagnosis (read-only) | Fix |
|---|---|---|
| step 1 exits `… is not a whole number` / `must be positive` | a `RETENTION_*` value in `setup/.env` was edited by hand | correct `.env`; a zero horizon would delete live data and is refused by design |
| step 2 lists a store belonging to a live agent | the agent was renamed or a deploy is mid-flight (P5) | stop, re-run after the deploy; never `--apply` while the two disagree |
| step 6 refuses with a missing approver | `--approved-by` omitted | obtain the decision first — this is the control, not an obstacle |
| an unexpected store disappeared | compare with `build/manifest.json` / the last baseline (`CHANGE_MANAGEMENT.md` §7) | restore per `BACKUP_DR.md` §4 R1 (agents and knowledge stores rebuild from the export; `vs-assurance-memory` from the export in P2); raise P2 severity if it was the memory store |
| `--memory` lists nothing for months | `MEMORY_BACKEND=search-index` while the notes are still in the vector store, or the reverse | check step 1's `memory backend` line against `.env` (`MEMORY_POLICY.md` §2a) |

## 8. Evidence produced

| Evidence | Produced by | Filed under |
|---|---|---|
| Monthly retention run (policy resolved, candidates, approval, deletions) | §4 steps 1–7 | `Governance/Operations/{yyyy}-{mm}/retention-run.md` |
| Memory purge approval (UPN, note count) | §4 step 6 output | same file; decision also in the ticket / `{list:ApprovalDecisions}` |
| Erasure-request handling | out-of-cycle run + `memory_store.py` output | the request ticket, referenced from the monthly file |
| "No action" months | step 1–3 output with an empty candidate list | same file — a quiet month still produces the evidence |

## 9. Shared deltas raised by this file

`D-RC-G1`, `D-RC-G2`, `D-RC-G3`, `D-RC-R1` and
`D-RC-S1` are **applied**; `D-RC-W1` is applied as a reminder-only workflow.
The rows are kept as the record of what each change was.

| Id | Target | Location | Literal text | Status |
|---|---|---|---|---|
| D-RC-G1 | `governance/MEMORY_IMPORT.md` | **new file** (referenced already by `scripts/memory_store.py` docstring and by `governance/MEMORY_POLICY.md` §2) | see the full file body in the shared-delta payload of this run: the written rule behind `memory_store.py import` — export treated as DATA not instructions, additive-only, privacy filter (GDPR Art. 9 categories, personal-profile lines), `MAX_BATCH` 50, mandatory `--approved-by`, dry-run-first procedure, evidence filing, and the ISO/GDPR/EU AI Act control mapping | applied |
| D-RC-G2 | `governance/MEMORY_POLICY.md` | §3 "Retention / purge" row, end of the Mechanism cell | ` Operational procedure (rehearsal, approval, evidence): \`../operations/RETENTION_AND_CLEANUP.md\` §4, run monthly as RUNBOOK M5; the executing script is \`scripts/cleanup_foundry.py\` (\`--dry-run\` is offline).` | applied |
| D-RC-G3 | `governance/MEMORY_POLICY.md` | §3, new row after "Backup / restore" | `| Import of an external memory export | \`memory_store.py import --from-file <export> --dry-run\` then \`--approved-by "{upn:…}"\`; rules in \`MEMORY_IMPORT.md\` | \`{upn:owner}\` |` | applied |
| D-RC-S1 | `scripts/cleanup_foundry.py` | module docstring, the line `Run monthly after an approval (\`operations/RUNBOOK.md\`)` | replace with `Run monthly after an approval — the procedure, preconditions and evidence are in \`operations/RETENTION_AND_CLEANUP.md\` §4 (calendar entry: RUNBOOK.md M5);` | applied |
| D-RC-R1 | `README.md` | folder layout tree, under `operations/` (after delta D-LC-R1) | `│   ├── RETENTION_AND_CLEANUP.md   ← monthly housekeeping: orphan stores/files, idle conversations, memory notes past retain_until (scripts/cleanup_foundry.py)` | applied |
| D-RC-W1 | `workflows/memory-retention.json` | **new file** (named as a shared delta by `governance/MEMORY_POLICY.md` §3) | a monthly `Recurrence` workflow that only *reminds*: it posts the §4 checklist to `{teams:infosec-assurance-platform}` and opens the ticket. It must **not** call `cleanup_foundry.py --apply` — the deletion step needs a named human approver (§2), so an unattended workflow cannot hold it | applied (reminder-only) |
