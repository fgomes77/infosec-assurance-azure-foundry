# Threads & Memory Conventions — Per-User Threads, Shared Team Memory, GDPR Minimisation

Two kinds of state exist (`../../ARCHITECTURE.md` "Memory/state"): Foundry
**threads** (session context) and the durable **`vs-assurance-memory`**
vector store (team knowledge). Neither is private storage; both are
in-scope for the RoPA entry `{ropa:infosec-foundry}` and the ISMS record
schedule.

## 1. Foundry threads

| Rule | Convention | Why |
|---|---|---|
| Visibility | Threads are **team-visible by design**: anyone with `Azure AI User` on the project can list and read them (verify per tenant; do not assume isolation). Treat every thread as a shared working paper | Foundry Agent Service applies project-level RBAC; per-thread ACLs are not part of the contract |
| One thread per engagement, not per day | Name/metadata: `{"owner":"{upn}","supplier":"<Supplier>","service":"<Service>","system":"a|b|c|d|d2|e|f|g|h|i|j","engagement":"<ticket-or-assessment-id>"}` set via thread `metadata` at creation (playground: first message states it; MCP/Copilot: the client sets it) | The advisor's context persists across sessions; deliverables and approvals can be traced back to one thread |
| Personal-data rule | No employee personal data beyond business role names already present in the source assessment; never paste HR, health, or private contact data; supplier contacts as role + company, not name, unless the report format needs the name | Persona minimisation rule; GDPR Art. 5(1)(c) |
| Uploads | Upload only the file the run needs (the OT PDF, the SOC report); delete thread files after the deliverable is approved when the source already lives in SharePoint | Minimisation; storage cost |
| Retention | Threads older than **90 days** with an approved deliverable are deleted by the owner's monthly job; threads for open engagements are kept; a thread referenced by an audit finding is exported to `Governance/Evidence/` first | Aligns with the 90-day Log Analytics retention in the Bicep; tracing keeps the audit trail |
| Identity in tracing | Local MCP and portal runs carry the user's own Entra identity in App Insights traces; hosted MCP and Copilot pass the user UPN as a message annotation (`x-requested-by`) | Per-user accountability without per-user credentials |
| Sensitive engagements | Incident-related or legally privileged work gets its own thread, metadata `"classification":"restricted"`, and is deleted on closure rather than at 90 days | A.5.12 classification |

## 2. Shared team memory (`vs-assurance-memory`)

| Rule | Convention |
|---|---|
| What goes in | Durable, professional facts only: decisions, agreed risk positions, supplier facts, template-cycle audit lines, open actions — exactly what the advisor's `MEMORY:` block emits |
| What never goes in | Special-category data; personal data about individuals beyond role/company; credentials, hostnames, internal IPs; anything copied verbatim from a supplier contract; personal reminders |
| Format | One note = one file: `YYYY-MM-DD | <Subject: supplier/topic> | <fact> | by {upn} | review <YYYY-Qn>` (`scripts/memory_store.py add`) |
| Who adds | Any assurance user, under their own identity (`memory_store.py` or MCP `save_memory`) — the human act is the approval (`../../governance/HUMAN_APPROVAL.md` scope notes) |
| Who deletes | The author at any time; the owner after a `MEMORY_DELETE` approval (`APPROVAL_ROUTING.md`); nobody else |
| Who reads | Every agent that has the store attached (advisor, orchestrator) and therefore every user — memory is shared context, not per-user |
| Review | Quarterly, with the access review: `memory_store.py list` → prune superseded/expired notes; DPO informed of the note count and categories |
| Retention | Supplier facts: until the supplier exits + 1 year; decisions/positions: 5 years (ISMS record schedule `{policy:records-retention}`); template audit lines: life of the template |

## 3. Personal notes

There is **no personal memory store**. A per-user vector store
(`vs-personal-{upn}`) was considered and rejected: it would add five
identities' worth of data to minimise and review, would be readable by any
agent it is attached to, and duplicates OneNote/Loop, which already sit
under the user's own M365 permissions. If a user needs a private scratch
context, they use a thread with `"classification":"personal-working"` and
delete it themselves; nothing from it is persisted to memory unless
promoted through the shared-memory rules above.

## 4. Per-user experience without per-user variation

The persona preamble is agent-side and identical for everyone. What varies
per user is only: their threads (metadata `owner`), their identity in
traces and approvals, their SharePoint permissions on evidence they already
manage, and what they choose to promote to shared memory. This is
deliberate: identical behaviour is what makes peer approval meaningful
(the approver knows exactly how the draft was produced).
