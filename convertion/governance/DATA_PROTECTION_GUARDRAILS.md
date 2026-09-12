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
| Instruction layer | Every agent with `web-search` carries the egress rule (appended by `attach_integrations.py`): search queries may contain ONLY public facts — supplier public names, product names, CVE ids, regulation references. NEVER internal identifiers (assessment ids, contract ids, project codenames, employee names, internal hostnames/IPs), scores, findings, or any text quoted from an internal document. When public and internal terms are needed together, the agent reformulates to the public terms and applies the internal context to the results locally. |
| Network layer | Bing Grounding is the ONLY web egress for agents (no generic HTTP tool is attached to any agent). Queries are auditable in Foundry tracing. |
| Detective layer | App Insights KQL alert on grounding-tool inputs matching internal-marker patterns (`ENX-`, assessment-id regex, internal domain suffixes, employee-directory names list from Entra). A hit raises a review ticket — the run is not killed retroactively, the pattern is fixed forward (instruction or list update). |
| Prompt-injection defence | Content fetched from the web (and from supplier evidence files) is DATA, never instructions: the persona preamble's injection rule tells agents to ignore directives embedded in retrieved content; the verifier checks deliverables for signs of instruction-following from sources. |

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
  `Sites.Read.All`; OneTrust viewer role; Jira browse-only) — defence in
  depth: even a mis-attached spec cannot escalate.
- The ONLY writer is the delivery Function's managed identity
  (`Sites.Selected` write on the one SharePoint site), reachable only
  from the Logic Apps after verifier PASS + human approval.
- ENX gateway MCP: consumed as-is; its own gateway policy governs which
  tools it exposes — request the read-only toolset for this project.

## 3. Data handling inside the platform

- **Residency:** Foundry account, storage, vector stores, Function and
  Logic Apps deploy to the EU region set in `setup/.env`; no data leaves
  the tenant boundary except sanitised search queries (§1).
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
  and workflows reference names only (`verify_conversion.py` greps for
  leaked secrets as a deploy gate).
- **Transport/identity:** managed identities end-to-end (Logic Apps →
  Foundry, Function → Graph); function endpoints key-protected and
  VNet-restricted; TLS everywhere by platform default.

## 4. Auditability

Every run is traceable: Foundry thread + tracing (prompts, tool calls,
tokens) in App Insights; Logic Apps run history evidences every approval
decision, approver and timestamp; SharePoint versioning preserves every
stored report version; the durable memory store is inspectable and
deletable (`scripts/memory_store.py`). Retention per the ISMS record
schedule — configure App Insights retention ≥ 1 year for DORA Art. 28
evidence needs.

## 5. Non-blocking principle — where the line sits

| Action | Guardrail behaviour |
|---|---|
| Reasoning, reading internal sources, drafting | Never blocked |
| Web search | Rewritten to sanitised queries, then executed |
| Rendering + storing a report | Gated (verifier + human approval), then executed |
| Writing to Jira/OneTrust/IAF/Confluence | Not possible from agents; submissions of record go through the approval-gated workflows only |
| Egress of internal identifiers to the web | Prevented by instruction + detected by alert — the only true "no" |
