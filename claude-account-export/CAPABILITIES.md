# Session Capabilities — Connectors, MCP Servers, Agents, Built-in Skills

Snapshot of the capability surface available to this account's Claude sessions
(claude.ai / Claude Code remote), recorded 2026-09-11. Connector credentials are
OAuth grants held by Anthropic and cannot be exported — reconnect each service
under claude.ai Settings → Connectors to restore.

## Connected MCP servers / connectors

| Connector | Capability summary |
|---|---|
| **GitHub** | Repos, PRs, issues, reviews, Actions, code search (scoped to authorised repositories) |
| **Gmail** | Read/search/send mail, drafts, labels, threads |
| **Google Drive** | Search, read, create, share, update files |
| **Adobe for Creativity** | Express document import/export, image editing (Firefly), fonts, PDF/InDesign conversion, video tools, asset storage |
| **Canva** | Design generation, editing, export, brand templates, folders |
| **Gamma** | AI presentations, documents, webpages; analytics; export |
| **Whimsical** | Flowcharts, mind maps, sequence diagrams, wireframes, docs, boards |
| **draw.io** | Diagram creation, shape search |
| **Mermaid Chart** | Mermaid diagram validation and rendering |
| **tldraw** | Canvas drawing via Editor API scripting |
| **Firecrawl** | Web search, developer-docs search, research-paper search and reading |
| **alphaXiv** | arXiv paper database (2.5M+ papers), researcher lookup, personal paper library |
| **AgentMail** | Programmatic inboxes, threads, drafts, provider connections |
| **IFTTT** | Applets, triggers/actions across consumer services |
| **Mobbin** | Mobile/web design pattern search (screens, flows) |
| **PDF Viewer** | Display and list PDFs |
| **Three.js 3D Viewer** | 3D scene display and learning resources |
| **Trimble SketchUp** | 3D model building and saving |
| **Claude Code Remote** | Session orchestration: spawn/manage sibling sessions, Routines (scheduled triggers), PR activity subscriptions, webhooks |

## Claude Code platform capabilities

- **Artifacts** — publish HTML pages to claude.ai (private by default), with runtime
  capabilities: shared database, per-user state, viewer identity, file storage,
  Claude queries from the page, comment threads, watches/wakes.
- **Agents / subagents** — `general-purpose`, `Explore` (read-only search), `Plan`
  (architecture), `claude-code-guide` (product docs), plus workflow orchestration
  (multi-agent pipelines) and background tasks.
- **Scheduling** — Routines (cron / one-shot), `send_later` self-reminders,
  dynamic loops, PR babysitting/steward workflows.
- **Web** — WebSearch, WebFetch (through session network policy).
- **Files & documents** — full filesystem tooling, Office/PDF generation via the
  document skills, Playwright-driven Chromium for rendering/screenshots.

## Built-in platform skills present in every session container (`/mnt/skills`)

These ship with the Claude Code environment (in addition to the account-synced
skills exported in `skills/`):

- **Public:** `docx`, `pdf`, `pptx`, `xlsx`, `file-reading`, `pdf-reading`,
  `frontend-design`, `product-self-knowledge`
- **Examples:** `algorithmic-art`, `benepass-reimbursement`, `brand-guidelines`,
  `built-in-browser`, `call-to-book`, `cancel-unsubscribe`, `canvas-design`,
  `chrome-browser`, `computer-use`, `deep-research`, `doc-coauthoring`, `docs`,
  `event-planning`, `file-expenses`, `file-form`, `financial-calculator`,
  `google-workspace`, `grocery-shopping`, `hire-help`, `import-memory`,
  `internal-comms`, `learn`, `mcp-builder`, `meal-delivery`, `morning`, `paint`,
  `prescription-refill`, `return-refund`, `setup-writing-style`, `skill-creator`,
  `slack-gif-creator`, `theme-factory`, `web-artifacts-builder`

Canonical upstream source: <https://github.com/anthropics/skills>. A complete
copy of this tree (unpacked folders and packaged `.skill` bundles) is included
in this export under `platform-skills/`.

## Harness / session skills (environment-provided)

`session-start-hook` (exported under `local-skills/`), `design`, `dataviz`,
`artifact-design`, `artifact-diagramming`, `artifact-capabilities`,
`update-config`, `keybindings-help`, `code-review`, `simplify`,
`fewer-permission-prompts`, `loop`, `claude-api`, `workflow-authoring`, `run`,
`init`, `security-review` — these are provided by the Claude Code harness itself
and are not user-owned files; they are listed here for completeness of the
capability inventory.
