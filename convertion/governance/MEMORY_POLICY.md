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

## 2. Note header (required — shared delta for `memory_store.py` / `server.py`)

```
[{stamp}] author={upn-from-token} class=Euronext Internal subject={supplier-or-topic-tag} retain_until={YYYY-MM-DD}
```

`retain_until` defaults to stamp + 24 months (assessment cycle × 2);
`subject` is free text but supplier notes use the SharePoint
`<Supplier>/<Service>` names so deletion-by-subject works.

## 3. Lifecycle

| Control | Mechanism | Owner |
|---|---|---|
| Retention / purge | `memory_store.py purge --older-than <date>` (shared delta) run by a monthly Logic App recurrence `workflows/memory-retention.json` (shared delta); notes past `retain_until` are deleted and the run summary posted to the owner | `{upn:owner}` |
| Deletion on request (data subject / supplier exit) | `memory_store.py list` → `delete <file-id>` by `subject`; evidence = run output attached to the request ticket | `{upn:owner}` / DPO channel |
| Backup / restore | `memory_store.py export` / `import` to the immutable EU blob container (`operations/BACKUP_DR.md` §3) — weekly | as in BACKUP_DR |
| Access | write: `{group:assurance-users}` via the MCP server / CLI with Entra token; read: advisor + orchestrator agents only; no Copilot direct read | `team/TEAM_MODEL.md` |
| Injection defence | notes are DATA (persona injection rule); prompt-injection detection on retrieval per `enterprise/memory-learning/` | platform |
| RoPA entry | "InfoSec Assurance team memory — purpose: continuity of assessment methodology; categories: business contact data of supplier staff (names/roles) where present in assessments; retention: `retain_until` ≤ 24 months; recipients: assurance team; location: EU region" | DPO channel |

## 4. Native Foundry memory (if enabled later)

Preview feature; TTL 90 days, exclusion list for `user_profile_details`,
document in the RoPA before enabling (`enterprise/memory-learning/
MEMORY_LEARNING_RESEARCH.md`). Not enabled by this kit.
