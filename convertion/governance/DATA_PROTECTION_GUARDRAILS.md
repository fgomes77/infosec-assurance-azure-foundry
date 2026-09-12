# Data-Protection Guardrails — Euronext Data Never Leaves, Work Never Stops

Design goal (requirement i, verbatim intent): *full web-search capability,
but no Euronext information goes to the web; enforce every security
policy/guardrail to protect Euronext data — without blocking task
execution and reasoning.*

The pattern throughout is **sanitise-and-proceed, not deny**: guardrails
transform what crosses a boundary instead of refusing the task. Blocking
is reserved for the two actions that are irreversible (external egress of
confidential data, and writes to systems of record).

## 1. Web-search egress control

| Layer | Control |
|---|---|
| Instruction layer | Every agent carries the egress rule through the persona preamble (`agents/persona_system_prompt.md`, prepended by `convert_skills.py`, `create_delivery_agents.py`, `create_orchestrator.py`; `attach_integrations.py` attaches tools and models only and appends no text): search queries may contain ONLY public facts — supplier public names, product names, CVE ids, regulation references. NEVER internal identifiers (assessment ids, contract ids, project codenames, employee names, internal hostnames/IPs), scores, findings, or any text quoted from an internal document. When public and internal terms are needed together, the agent reformulates to the public terms and applies the internal context to the results locally. |
| Network layer | Bing Grounding (search) and the allow-listed `osint-proxy` OpenAPI tool (page-level public OSINT fetch, read-only) are the ONLY web egress for agents; no generic HTTP/browser tool exists (WebFetch/browser skills EXCLUDED in `PLATFORM_SKILLS_DECISION.md`). Bing Grounding is a **global** service: only the sanitised public query crosses the EU boundary (`infra/main.bicep` residency comment). Queries are auditable in Foundry tracing. |
| Detective layer | Scheduled-query alert (`infra/monitoring.bicep`, query `infra/kql/egress-internal-markers.kql`) on grounding-tool inputs matching internal-marker patterns (`ENX-`, assessment-id regex, internal domain suffixes, employee-directory names list from Entra), routed to the owner action group. A hit raises a review ticket — the run is not killed retroactively, the pattern is fixed forward (instruction or list update). Implemented by `operations/kql/egress-detection.kql` and the `egress-internal-marker` rule in `operations/alerts.bicep` (severity 1, owner + SOC) where that catalogue is deployed; response: `operations/RUNBOOK.md` FM-03. |
| Prompt-injection defence | Content fetched from the web (and from supplier evidence files) is DATA, never instructions: the persona preamble's injection rule tells agents to ignore directives embedded in retrieved content; the verifier checks deliverables for signs of instruction-following from sources. |

**Compliance boundary (accepted residual risk).** Grounding with Bing Search /
the Web Search tool sends the query to a global Microsoft service **outside the
Azure compliance boundary**; the Azure Data Protection Addendum does **not**
apply to it and EU residency is not guaranteed for the query text
([Bing tools](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/bing-tools),
GA 2026-08-27). The risk is accepted by Francisco Gustavo Gomes (accountable
owner) on the basis of the sanitisation rule above, the detective KQL egress
alert, and page reads going through `osint-proxy` instead. It is recorded in
the RoPA and in the DORA Art. 28 register and re-reviewed at every standing
platform-currency review (`../enterprise/UPDATE_AND_UPGRADE_REVIEW_POLICY.md`
§4). A domain-restricted alternative (Bing Custom Search / Web Search with a
domain allow-list, preview) is evaluated in `test` before any GA adoption. The
same text is carried on the `web-search` connection in
`../integrations/registry.json` (finding C13).

Continuous evaluation samples 10 % of production interactions into
Application Insights (`../enterprise/series/08-guardrails-observability-evaluation.md`
§4); those samples are subject to the same retention and the same RoPA entry.

## 2. Read-only enterprise access (structural, not behavioural)

- `attach_integrations.py` **strips every non-GET operation** from each
  OpenAPI spec at attach time unless the connection is named in that
  agent's `write_connections` — which no agent has. Confluence, Jira,
  Jira Assets, SharePoint, OneTrust, Defender (security monitoring),
  Entra ID IAM, SecurityScorecard (risk monitoring), IAF
  (governance/compliance/AET findings): agents physically cannot write,
  whatever they are asked. Additional Euronext tooling (vulnerability
  management, GRC platforms, AET) reaches agents only through the ENX
  gateway MCP server or a new OpenAPI spec added under the same
  read-only-by-construction pattern.
- The registry's `advisory_read_only_toolset` applies this full read
  surface uniformly to EVERY information-providing system (framework
  advisors, cyber-forum, tpsrca, control-center, advisor), and the
  persona preamble carries the read-only + egress rules into every agent
  on the platform — the rules exist in the instructions layer, the tool
  layer, and the credential layer at once.
- The service accounts / app registrations behind the Foundry connections
  are themselves provisioned read-only (Confluence read scopes; Graph
  `Sites.Selected` **read** on the one site — no identity holds
  `Sites.Read.All` / `Sites.ReadWrite.All`, see `../team/TEAM_MODEL.md`
  §8; OneTrust viewer role; Jira browse-only) — defence in depth: even a
  mis-attached spec cannot escalate.
- The ONLY writer is the delivery Function's managed identity
  (`Sites.Selected` write on the one SharePoint site), reachable only
  from the Logic Apps after verifier PASS + human approval. Logic Apps
  hold no Graph write except the time-boxed L12x exception
  (`../team/ACCESS_REGISTER.md`).
- ENX gateway MCP: `allowed_tools` read-only; `attach_integrations.py`
  refuses tools without `readOnlyHint=true` (`HUMAN_APPROVAL.md` Layer 1).

## 3. Data handling inside the platform

- **Residency:** Foundry account, storage, vector stores (which hold
  Euronext evidence), Function and Logic Apps deploy to the EU region set
  in `setup/.env`; `infra/main.bicep` restricts `location` to EU regions;
  no data leaves the tenant boundary except sanitised search queries
  (§1). CI/CD: pull-request jobs are offline (repository content only —
  templates and thresholds, never assessment data) and may run on
  non-EU hosted runners only if ENX policy accepts that; the deploy job
  alone talks to Azure (EU endpoints) and must fail on any non-EU
  location (`ci/tests/test_residency.py`, shared delta); smoke prompts
  carry public regulation text only, never supplier data.
- **Minimisation:** agents carry only the knowledge files their skill
  needs; personal data in deliverables is limited to what the source
  assessment already contains (verifier rule 5); the memory store bans
  special-category data (advisor charter).
- **Content safety:** the default Azure AI content-filter (RAI) policy
  stays on both model deployments in ANNOTATE-capable severity settings —
  tuned so GRC/security vocabulary (vulnerabilities, exploits, attack
  paths) is not falsely blocked: this is professional security analysis,
  and a filter that blocks the domain blocks the mission. If a legitimate
  run is filtered, adjust the custom RAI policy severity for that
  category rather than disabling filtering.
- **Secrets:** all credentials in Key Vault / Foundry connections; specs
  and workflows reference names only. Scanning status: a manual
  secret/PII scan was run once at export time (export README); the
  repeating control is
  `scripts/verify_kit.py` §1 (secret, tenant-hostname and e-mail scan)
  called from `deploy.sh`, plus the gitleaks CI job `secret-scan` of
  `.github/workflows/ci.yml` (same steps in `convertion/ci/azure-pipelines.yml`)
  whose configuration `.github/gitleaks.toml` allow-lists only the documented
  placeholders, Key Vault references and public Azure role-definition GUIDs —
  see `../ci/README.md` §3. (There is no `scripts/scan_secrets.py` in the kit;
  `verify_kit.py` is what performs that scan.) Reviewers additionally grep every
  PR (`CODEOWNERS` + PR template checklist).
- **Transport/identity:** managed identities end-to-end (Logic Apps →
  Foundry, Function → Graph); function endpoints key-protected and
  VNet-restricted; TLS everywhere by platform default.

Feedback records (`../enterprise/memory/feedback-schema.json`) carry identifiers
and generic descriptions only — no report content, findings, scores or personal
data; `learning_loop.py` masks e-mail/IP/secret-like strings and flags the
record. Native memory (preview) is **not** enabled; if it is ever piloted:
per-user scope, TTL 90 days, `user_profile_details` exclusion list, RoPA first
(`../enterprise/MEMORY_AND_LEARNING.md` §3).

## 4. Auditability

Every run is traceable: the Foundry conversation + tracing (prompts, tool calls,
tokens) in App Insights; Logic Apps run history evidences every approval
decision, approver and timestamp; SharePoint versioning preserves every
stored report version; the durable memory store is inspectable and
deletable (`scripts/memory_store.py`, policy in `MEMORY_POLICY.md`).
Retention per the ISMS record schedule — `logRetentionDays = 365` in
`infra/main.bicep` (DORA Art. 28 evidence); the tables and the evidence layout
are in `operations/MONITORING.md` §1–§2, §6. Backups of the shared memory store
are dated read-only exports produced by an EU-resident managed-identity job and
filed in the EU storage container `backups/` and/or `Governance/Backups/`,
protected like the source and retained per the note retention —
`operations/BACKUP_DR.md` §1. Template changes are logged
in `templates/audit.log`. Full-coverage PDF analysis
(`pdf-full-coverage-analyzer`) must ship its audit artefacts (chunk
inventory, per-chunk extraction JSON, coverage statement, verdict) with
the report: the evidence-summary contract carries an `auditArtifacts`
array and the pipeline uploads them to
`Reports/<Supplier>/<Service>/audit/<date>/` (shared delta); the verifier
requires the coverage statement + verdict COMPLETE (or PARTIAL with
explicit user acceptance).

## 5. Non-blocking principle — where the line sits

| Action | Guardrail behaviour |
|---|---|
| Reasoning, reading internal sources, drafting | Never blocked |
| Web search | Rewritten to sanitised queries, then executed |
| Rendering + storing a report | Gated (verifier + human approval), then executed |
| Writing to Jira/OneTrust/IAF/Confluence | Not possible from agents; submissions of record go through the approval-gated workflows only |
| Egress of internal identifiers to the web | Prevented by instruction + detected by alert — the only true "no" |
