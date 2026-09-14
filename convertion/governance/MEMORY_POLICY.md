# Durable Memory Policy — `vs-assurance-memory`

Scope: the team memory vector store written by `scripts/memory_store.py`
and by the MCP server's `save_memory` tool (`mcp-server/server.py`), read
by the advisor / orchestrator through file_search. It is a record of
processing (Euronext Internal) and must be operable under the ISMS record
schedule, GDPR Art. 30 RoPA and DORA Art. 28 evidence needs.

## 1. What may be stored

| Allowed | Forbidden |
|---|---|
| Team decisions, methodology positions, supplier facts already in the assessment record, follow-up reminders, template/threshold rationale | Special-category personal data; credentials/tokens; verbatim supplier confidential documents; anything an agent generated without a human choosing to persist it |

Writers: humans only (or their client acting on an explicit instruction).
Agents cannot call `save_memory` (`HUMAN_APPROVAL.md` scope notes).
The line-by-line filter contract behind `save_memory` and behind a bulk
`memory_store.py import` — what each pattern drops, the `--approved-by`
and `MAX_BATCH` guards, and the GDPR article mapping — is
`MEMORY_IMPORT.md`.

## 2. Note header (required — shared delta for `memory_store.py` / `server.py`)

```
[{stamp}] author={upn-from-token} class=Euronext Internal subject={supplier-or-topic-tag} retain_until={YYYY-MM-DD}
```

`retain_until` defaults to stamp + 24 months (assessment cycle × 2);
`subject` is free text but supplier notes use the SharePoint
`<Supplier>/<Service>` names so deletion-by-subject works.

## 2a. Durable-memory backends (`MEMORY_BACKEND`, finding C3)

Durable memory has two backends selected by `MEMORY_BACKEND` (`setup/.env`).
The policy above — privacy filter, special-category rejection, the note
header of §2, `--approved-by` gate, `retain_until` ≤ 24 months — is identical
on both; only the store differs.

| `MEMORY_BACKEND` | Store | Notes |
|---|---|---|
| `vector-store` (transition default) | Timestamped notes in the vector store `vs-assurance-memory` | **Staging only.** No longer attached to the advisor: the service allows exactly one vector store per agent (finding C3), and that slot holds `vs-assurance-combined`. Notes are written and read through `scripts/memory_store.py` / the MCP server, not by the agent's `file_search`. |
| `search-index` (target) | Documents `{id, stamp, author, class, subject, retain_until, text}` in the Azure AI Search index `MEMORY_INDEX_NAME` (default `kb-assurance-memory`) | Read by the advisor through the GA Azure AI Search tool beside its single `file_search` store, so memory is groundable again without spending the vector-store slot. |

`scripts/memory_store.py` implements `add` / `list` / `delete` / `import` /
`purge` identically on both backends, with the same privacy filter, the same
special-category rejection and the same `--approved-by` gate; `retain_until`
is set to 24 months in both. `mcp-server/server.py` `save_memory` /
`search_memory` follow the same switch. Moving between backends is a Tier C
change: export first (`operations/BACKUP_DR.md` §3), then re-import.

## 3. Lifecycle

| Control | Mechanism | Owner |
|---|---|---|
| Retention / purge | **`scripts/cleanup_foundry.py`** is the executing script. Every horizon comes from `setup/.env`: `RETENTION_CONVERSATION_APPROVED_DAYS` (90), `RETENTION_CONVERSATION_IDLE_DAYS` (180), `RETENTION_ORPHAN_FILE_DAYS` (30), `RETENTION_ORPHAN_STORE_DAYS` (30), `RETENTION_MEMORY_MONTHS` (24) — no horizon is hard-coded. The previously-deferred `memory_store.py purge --older-than` delta is **satisfied** by `cleanup_foundry.py --memory --apply --approved-by "{upn:…}"`: the same named-human gate, notes deleted only past their own `retain_until`, both backends (vector store and search index). Reminder-only monthly workflow: `../workflows/memory-retention.json` — it never runs `--apply`, because the purge needs a named approver an unattended workflow cannot hold. Procedure, rehearsal and evidence: `../operations/RETENTION_AND_CLEANUP.md` §4, run monthly as RUNBOOK M5; `--dry-run` is offline and makes no Azure call. | `{upn:owner}` |
| Deletion on request (data subject / supplier exit) | `memory_store.py list` → `delete <file-id>` by `subject`; evidence = run output attached to the request ticket | `{upn:owner}` / DPO channel |
| Backup / restore | `memory_store.py export` / `import` to the immutable EU blob container (`operations/BACKUP_DR.md` §3) — weekly | as in BACKUP_DR |
| Import of an external memory export | `memory_store.py import --from-file <export> --dry-run` then `--approved-by "{upn:…}"`; rules in `MEMORY_IMPORT.md` | `{upn:owner}` |
| Access | write: `{group:assurance-users}` via the MCP server / CLI with Entra token; read: advisor + orchestrator agents only; no Copilot direct read | `team/TEAM_MODEL.md` |
| Injection defence | notes are DATA (persona injection rule); prompt-injection detection on retrieval per `enterprise/memory-learning/` | platform |
| Feedback records | `{list:PlatformFeedback}` + `build/learning/inbox/` per `../enterprise/memory/feedback-schema.json` — ids and generic descriptions only, no report content, 24-month retention | `{upn:owner}` |
| RoPA entry | "InfoSec Assurance team memory — purpose: continuity of assessment methodology; categories: business contact data of supplier staff (names/roles) where present in assessments; retention: `retain_until` ≤ 24 months; recipients: assurance team; location: EU region" | DPO channel |

## 4. Native Foundry memory (if enabled later)

Preview feature (https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/what-is-memory,
2026-06-02). Pilot conditions in `../enterprise/MEMORY_AND_LEARNING.md` §3:
advisor only, per-user scope, procedural memory disabled on every agent, TTL
90 days, `user_profile_details` exclusion list, no VNet support, RoPA updated
before enablement. **Not enabled by this kit.**
