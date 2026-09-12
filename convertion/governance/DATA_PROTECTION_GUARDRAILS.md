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
| Residency exception | Bing Grounding is a **global** service: the sanitised public query is the only Euronext-originated text processed outside the EU. Accepted residual risk, owner = the platform owner, reviewed annually and at every platform-currency review; detective alert `egress-internal-markers` (`infra/monitoring.bicep`). |
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
- Analysis services (Document Intelligence OCR, Speech batch transcription)
  are reached only by the delivery Function with its managed identity, never
  as agent tools — so the non-GET stripping rule above needs no exception
  for them (`../integrations/README.md` §Analysis services).

## 3. Data handling inside the platform

- **Residency:** `location` is restricted to EU regions (the `@allowed`
  list in `infra/main.bicep`, enforced again by `infra/validate.sh`); model
  inference runs on the **EU Data Zone** SKU (`deploymentSku =
  DataZoneStandard`; `GlobalStandard` is not allowed). Agent conversations,
  files and vector stores stay in the account region in Microsoft-managed
  storage — BYO storage / Cosmos DB / AI Search is the option if
  customer-subscription custody is ever required (accepted risk, owner: the
  platform owner). Per-component table: `../infra/README.md` §Residency.
  No data leaves the tenant boundary except the sanitised search queries of
  §1. CI/CD: pull-request jobs are offline (repository content only —
  templates and thresholds, never assessment data); the deploy job alone
  talks to Azure (EU endpoints).

  The residency gate is **`ci/tests/test_residency.py`** — no longer a shared
  delta, it exists and runs as gate `[4b]` on every pull request and twice in
  `.github/workflows/deploy.yml` (offline before the credential is minted,
  then `--live` after login). Seven offline checks: the Bicep `@allowed`
  location lists, the `allowedLocations` array of the Azure Policy assignment,
  the `location` values in every ARM parameter file, `deploymentSku` not being
  a `Global*` SKU, the runner's `AZURE_LOCATION`, and non-EU region tokens in
  configured endpoints — plus a `--live` scan of the deployed resource group.
  Smoke prompts carry public regulation text only, never supplier data.
- **Minimisation:** agents carry only the knowledge files their skill
  needs; personal data in deliverables is limited to what the source
  assessment already contains (verifier rule 5); the memory store bans
  special-category data (advisor charter).
- **Content safety:** the custom RAI policy `infosec-security-analysis`
  (`infra/main.bicep`: annotate-only for Hate, Sexual, Violence and
  Self-harm; blocking for jailbreak and protected material) is bound to all
  three model deployments, in ANNOTATE-capable severity settings —
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
  called from `deploy.sh`, and its standalone entry point
  **`scripts/scan_secrets.py`** — a thin CLI over the same
  `verify_kit.scan_secrets` (no second implementation of the patterns), with
  `--json` for the CI evidence artefact and an optional `gitleaks` second pass
  — plus the gitleaks CI job `secret-scan` of `.github/workflows/ci.yml`,
  `.github/workflows/deploy.yml` and `.github/workflows/nightly-drift.yml`
  (same steps in `convertion/ci/azure-pipelines.yml`), whose configuration
  `.github/gitleaks.toml` allow-lists only the documented placeholders, Key
  Vault references and public Azure role-definition GUIDs. The repository root
  also carries a `.gitleaks.toml` that does nothing but `[extend] path` to
  `.github/gitleaks.toml`, so a scan run **without** `--config` (pre-commit,
  `gitleaks protect`) enforces the same allow-list instead of gitleaks' bare
  defaults — see `../ci/README.md` §3. Reviewers additionally grep every PR
  (`.github/CODEOWNERS` + the PR template checklist).
- **Transport/identity:** managed identities end-to-end (Logic Apps →
  Foundry, Function → Graph); function endpoints are key-protected,
  VNet-integrated and restricted to the Logic App subnet
  (`infra/delivery.bicep`), with private endpoints under
  `enablePrivateNetworking` (`infra/network.bicep`); the egress FQDN
  allow-list is in `../infra/README.md` §Network; TLS everywhere by platform
  default.

Feedback records (`../enterprise/memory/feedback-schema.json`) carry identifiers
and generic descriptions only — no report content, findings, scores or personal
data; `learning_loop.py` masks e-mail/IP/secret-like strings and flags the
record. Native memory (preview) is **not** enabled; if it is ever piloted:
per-user scope, TTL 90 days, `user_profile_details` exclusion list, RoPA first
(`../enterprise/MEMORY_AND_LEARNING.md` §3).


**Personal M365 data (`morning-brief`, `mailbox-intake`).** Two workflows
touch a person's own mailbox, calendar and chats. Application access policies
scope the automation identity to **the five team accounts and the one shared
mailbox** — it cannot read anyone else in the tenant. Only `$select`-ed
fields are read (subject, time, organiser, sender; never message bodies
beyond what the brief quotes). The morning brief is written to the user's
**own OneDrive** with 7-day retention (the `RetentionDays` field on the
uploaded item, swept by the delivery Function's cleanup timer). Mailbox
attachments are filed to `Infosec Assurance/GRC/TPA/Inbox/` for human triage
and nothing else. No personal data is written to any SharePoint list, and no
content is sent to any external service. Calendar, mail and chat items are
**data, never instructions** (§1 prompt-injection defence).

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
