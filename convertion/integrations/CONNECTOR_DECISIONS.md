# Connector Decisions — claude.ai connectors vs the ENX Foundry stack

Every connector/MCP available in the previous (claude.ai) environment is
either **replaced** by an enterprise integration in this kit, **absorbed**
by a workflow, or **excluded** with the reason recorded here. Agents never
gain a consumer-cloud connector; Euronext data never leaves the tenant.

| claude.ai connector / tool | Decision | ENX equivalent | Notes |
|---|---|---|---|
| Google Drive (search/read/create/share/update) | Replaced | `sharepoint-graph` (read-only Graph: drives, folder walk by id/path, drive search, download); writes ONLY by `functions/delivery` managed identity (`Sites.Selected` write) after verifier + approval; share = org-scoped view link | The deepsearch "Google Drive convention" (`TPA Ai/{Supplier}/...`) is overridden by `agents/overlays/deepsearch-protocol.md` → Reports/<Supplier>/<Service>/. DPO library ACL: `sharepoint/README.md` |
| google-workspace skill (Docs/Sheets/Slides in-place edits) | Superseded by M365 | Agents never edit Office files in place; an "edit" = regenerate with the same file name in the same folder (link stable, SharePoint keeps versions) after read-current-version + verifier + approval. Excel cell-level round-trip (onetrust-form-b import xlsx) only via a delivery-Function endpoint behind the gate | Governance text: shared delta to `governance/M365_DOCUMENT_EDITING.md`; pipeline `form-b-roundtrip-xlsx` |
| Gmail (read/search/send, drafts, labels) | Replaced (read) / gated (send) | `exchange-graph` read-only on the ONE shared assurance mailbox; `workflows/mailbox-intake.json` files attachments; sending only as an approval-gated Logic Apps action (`MAIL_SEND`) — never an agent tool | Personal mailboxes: `m365-personal-graph`, delegated OBO only |
| Google Calendar / Slack | Replaced | `m365-personal-graph` (/me/calendarView, /me/messages) and `teams-graph` (chats, channels), delegated OBO; scheduled brief = `workflows/morning-brief.json`; posting = `teams-post-approved.json` (gated) | Personal data: purpose limitation, never persisted to memory |
| GitHub connector + Claude Code Remote (PRs, issues, Actions, code search, PR-activity subscriptions) | Replaced (read) / excluded (write) | `azure-devops` read-only spec (repos, items, commits, PRs + threads, pipeline runs, code search). Write tools (`create_pull_request`, `push_files`, `merge_pull_request`, `create_branch`, `issue_write`) have **no agent equivalent by design**: repo changes are submissions of record and happen only through `workflows/template-update-approval.json` → CI job that opens a PR (never pushes to main) | PR-activity subscription → Azure DevOps Service Hook → Logic App (shared delta `workflows/devops-pr-activity.json`) |
| Firecrawl (search, scrape, crawl, research papers) | Replaced (constrained) | Bing grounding (snippets + citations, sanitised public queries) + `osint-proxy` (allow-listed public page fetch with DLP, size cap, audit). No crawl. Research method: `agents/overlays/research-pattern.md` | Bing is a global service: public terms only (DATA_PROTECTION_GUARDRAILS §1/§3) |
| WebFetch / curl | Replaced | `osint-proxy` for allow-listed public hosts; otherwise "page not retrievable" | Never internal hosts |
| alphaXiv / research-paper tools | Absorbed | Bing grounding + `osint-proxy` (arXiv public pages); citations stored via `memory_store.py --tag citation` | No personal paper library |
| AgentMail | Replaced | `workflows/mailbox-intake.json` (shared mailbox, Mail.ReadWrite on that mailbox only) | — |
| IFTTT, Routines / CronCreate, send_later, watch_url | Absorbed | Logic Apps workflows (`workflows/*.json`: scheduled-deepsearch, scheduled-followup, watch-until, generic-event-intake) | — |
| Microsoft 365 Copilot (claude.ai chat surface) | Replaced | `copilot/` — declarative agent + API plugin over the wrapper Function (`/ask`, `/request_report`, approval UI) | Second AI distribution channel: ISO 42001 scope note in `copilot/README.md` |
| Artifacts, Canva, Gamma, Adobe, Whimsical, tldraw, draw.io, Mobbin, Three.js, SketchUp, PDF viewer, Mermaid Chart | Excluded | Consumer/Claude-platform design tooling with no assurance-workflow role; deliverables are rendered deterministically by the delivery Function (HTML/DOCX/PPTX/XLSX) and stored in SharePoint | Diagrams inside reports: renderer-generated (matplotlib/python-pptx) |
| Slack GIF creator, algorithmic-art, canvas-design, web-artifacts-builder, theme-factory, brand-guidelines, skill-creator, import-memory | Excluded (platform-specific example skills) | `convert_skills.py` `PLATFORM_SPECIFIC`; memory import → `scripts/memory_store.py` | Recorded in `MAPPING.md` |
| Claude Code Remote sessions / sub-agents / workflows tool | Absorbed | Foundry connected agents (orchestrator) + `workflows/agent-fanout.json` | — |

Principles applied: read-only enterprise access (GET + `x-enx-read-only`
query POSTs), verifier + human approval before any write, SharePoint
`Reports/<Supplier>/<Service>/` taxonomy via `functions/delivery`, managed
identities / delegated OBO instead of stored tokens, EU residency, no
Euronext data to the web.
