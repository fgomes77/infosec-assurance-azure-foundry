# Human Review & Approval Policy — Mandatory for All Agents

**Rule: no AI agent in this environment submits anything to a connected
platform without prior human review and explicit approval.** "Submit" means
any write of record to an external system: creating/transitioning/commenting
Jira issues, submitting findings to the IAF API, writing back to OneTrust,
uploading deliverables to SharePoint, posting to the ENX gateway, sending
mail/messages, and writing durable memory on someone's behalf. Read
operations (queries, searches, downloads) are not gated.

Enforced as defense in depth at three layers:

## Layer 1 — Technical: agents hold read-only tools

`scripts/attach_integrations.py` strips every non-GET operation from the
OpenAPI specs before attaching them, so agents **cannot** call write
endpoints directly, whatever their instructions or a prompt-injection
attempt says.

**Exception of record — five query POSTs.** Some search APIs express a
*query* as a POST because it does not fit in a URL. Those operations are
kept: `searchIssuesJql` (Jira JQL), `aqlSearchObjects` (Jira Assets AQL),
`runHuntingQuery` (Defender advanced hunting), `searchContent` (SharePoint /
Graph search) and `codeSearch` (Azure DevOps). Two conditions must both hold
— the operation carries `x-enx-read-only: true` in the spec **and** its
`operationId` is in `attach_integrations.READ_ONLY_POST_OPS`. The second
condition is the control: without it, anyone who can edit a spec file could
widen the read-only rule by adding a flag, which would make a structural
control editable by its own subject. A flag on any other operation is a hard
failure at attach time and in `verify_conversion.py`'s read-only audit, which
re-derives the kept list from the specs and prints it
(`attach_integrations.py --dry-run` prints the same list). These five read;
none of them mutates.

Mail send (`MAIL_SEND`) and repository changes (`TEMPLATE_UPDATE`, where CI
opens a pull request rather than pushing) exist only as Layer-3 gated
actions — never as an agent tool. Write operations exist only inside the approval-gated
workflows (Layer 3). A specific write may be granted to a specific agent
only by listing the connection in that agent's `"write_connections"` in
`integrations/registry.json` — the default for every agent is none, and any
grant is a deliberate, reviewable diff to this repository.

MCP tools follow the same rule: an `allowed_tools` list may name READ
tools only — `attach_integrations.py` calls the gateway's `tools/list` and
refuses any tool whose annotations lack `readOnlyHint=true` unless the
connection is in `write_connections` (`integrations/mcp/enx-gateway.json`).
Write-capable Euronext operations that remain in OpenAPI specs at source
(e.g. Jira transitions, IAF submit) are stripped at attach time AND are
reachable only from Layer 3 workflows. Identity layer: the ONLY SharePoint
writer is the delivery Function's managed identity (`Sites.Selected` write
on the one site); agents' Graph app and the Foundry project MI hold
`Sites.Selected` read; the Logic App MI's direct-upload write is a
time-boxed exception (L12x) recorded in `../team/TEAM_MODEL.md` §8 and
`../team/ACCESS_REGISTER.md`. Reviewable-diff dependency: changes to
`write_connections`, this folder, `workflows/`, `infra/` and `agents/`
require CODEOWNER review and passing checks on `main` (branch protection
per the CI delta; see `DATA_PROTECTION_GUARDRAILS.md` §3).

## Layer 2 — Behavioural: a draft-then-approve protocol in every agent

`convert_skills.py` and `create_orchestrator.py` append the APPROVAL GATE
block to every agent's instructions: prepare the complete draft (ticket,
finding, report, answer set), present it to the human with a clear
"awaiting your approval" marker, and proceed only on an explicit approval in
the conversation; a rejection or edit request restarts the cycle. This keeps
behaviour correct even for channels Layer 1 cannot see (e.g. text the human
might paste onward), and preserves the mandatory sign-off gate the
onetrust-form-b skill already carried. Delivery agents and the
orchestrator/advisor get the same block from `create_delivery_agents.py` /
`create_orchestrator.py`. **Documented exception:** `output-verifier`
carries no gate — it generates nothing and returns PASS/FAIL only; the
count in "Verifying the control" is therefore agents − 1.

## Layer 3 — Process: approval steps inside the workflows

Every Logic Apps workflow suspends before its submission-of-record actions
on an `HttpWebhook` approval gate: the draft is sent to the approver
(Teams adaptive card / Power App), the workflow waits for a human
`approved`/`rejected` callback, and expiry auto-rejects without
submitting. Notifications-only steps (Teams summaries) are not gated.
Approver ≠ requester and tiered approver groups are enforced by the
approval flow per `../team/approval-policy.json`. See `../workflows/README.md`.

Reference implementation of the approval side:
`../integrations/copilot/function/function_app.py` —
`POST /api/approval/subscribe` (the `approvalWebhookUrl` target) stores the
draft and posts the review link to Teams, `GET /api/approval/{id}` renders it,
and `POST /api/approval/{id}/decide` verifies the approver against
`../team/approval-policy.json` (Graph `checkMemberGroups`, no self-approval)
before calling back `{decision, approver}`.

| Gated workflow | Submission of record | Expiry |
|---|---|---|
| `report-delivery-pipeline.json` (the twelve deliverable pipelines in `workflows/pipelines.json`: deepsearch-report, ai-deepsearch-report, dpia-dpo-report, cyber-forum-pptx, cyber-forum-brief, ciso-global-pptx, ciso-exec-summary, tpa-evidence-analysis, soc-report-summary, pentest-report-summary, advisory-file-delivery, transcript-summary) | SharePoint upload to `Reports/<Supplier>/<Service>/` via the delivery Function (`functions/delivery`) — the only technical write path — after `output-verifier` PASS | P3D → auto-reject |
| `defender-incident-brief.json`, `onetrust-assessment-intake.json`, `scheduled-deepsearch.json`, `jira-finding-sync.json` | report upload / Jira create / IAF submit (Jira and IAF writes exist ONLY here — Layer-3 exceptions, never in agents) | P3D |
| **Promote agent version** (including Agent Optimizer candidates) | Activating a new immutable agent version so it serves traffic. Approver: platform owner `{upn:francisco.gomes}` (deputy review when owner-authored). Evidence: the eval run report URL, the instruction/tool diff, and the `<agent>:<version>` recorded in `build/agent-versions.json` by the deploy (finding C19). Agents are **never updated in place** on the GA runtime — every deploy saves a new immutable version, and rollback is re-activating the previous version number. | n/a (PR-based, `operations/CHANGE_MANAGEMENT.md` Tier C) |
| `template-update-approval.json` | `scripts/update_templates.py` writes the template back, bumps `templates/registry.json` (logged in `templates/audit.log`) and re-runs convert → verify → create | **P7D** (template change = methodology change; owner-tier approval) |

Documented exceptions inside Layer 3: (a) the template workflow uploads the
before/after **review page** to the review location BEFORE approval — review
material, not a deliverable of record; (b) approval alone does not propagate
a template. **Implemented:** after the approval callback,
`template-update-approval.json` renders the template's registry `sample`
(`templates/samples/<id>.json`) with the *proposed* template through the
delivery Function `/render` — so a schema mismatch (400) or a failed quality
gate (422) stops the run — and then runs `output-verifier` on that rendered
sample; `Apply_template_update_*` executes only on `VERDICT: PASS`, and a
FAIL notifies Teams and changes nothing. The theme tokens (`enx-theme`,
format `json`, no renderer) take the parallel branch and are verified as
source text. `scripts/update_templates.py` **refuses to run without
`--approval-run`** (the approval workflow's run id, which it also writes to
`templates/audit.log`), so an apply outside the approved run is not possible
— `--dry-run`, which writes nothing, is exempt.

## Scope notes

- **MCP server:** `ask_*` tools inherit Layers 1–2 (the agents they reach
  hold read-only tools and the draft protocol). `save_memory` is itself the
  human approval act — a person (or their client, on their instruction)
  persists a note; agents cannot call it.
- **Scheduling a follow-up is not a submission.** The MCP tool
  `schedule_followup` (and the `scheduled-followup` Logic App behind it,
  contract `../integrations/openapi/followup-scheduler.yaml`) re-opens an
  existing conversation at a future time: the agent answers in that
  conversation and the requester is notified on Teams. Nothing is stored in
  SharePoint, Jira, OneTrust or any other system of record, so no Layer-3
  gate applies — anything the follow-up produces becomes a deliverable only
  through the delivery pipeline, with `output-verifier` PASS and approval as
  usual. An agent cannot schedule: the spec's only operation is a POST, the
  Layer-1 rule strips non-GET operations, and the registry entry is
  `enabled: false` so attaching it fails the deploy. The caller is a named
  human and `requestedBy` comes from their identity.
- **Copilot surface:** the same agents answer in Copilot, so Layers 1–2
  apply unchanged; Copilot adds no write path.
- **Continuous evaluation, red-team scans and `learning_loop.py` proposals**
  are INPUTS to a human decision. None of them may promote a version, change
  a deployment or edit a template on its own.
- **Orchestrator/advisor:** carry the same gate; a hand-off cannot launder a
  write, because the specialist it hands off to (by `ROUTE:` table, A2A tool
  or Agent Framework step) is read-only too.

## Compliance mapping

- **EU AI Act Art. 14 (human oversight):** approval gates are the oversight
  measure — outputs take effect only after natural-person review.
- **ISO/IEC 42001 Annex A** (A.6 AI system life cycle, A.9 use of AI
  systems): this policy is the documented control; audit evidence = the
  registry's empty `write_connections`, the gate block in deployed agent
  instructions, and workflow run history showing approval callbacks.
- **DORA/NIS2 context:** submissions of record into risk registers and
  ticketing remain human-accountable acts.
- **DORA Art. 28(2)/(3) evidence retention:** Log Analytics / App Insights
  retention is `logRetentionDays = 365` in `../infra/main.bicep`; Logic
  Apps run history and the approval flow's persisted decision record
  ({kind, correlationId, requestedBy, approver, decision, timestamp}) are
  the approval evidence; `operations/BACKUP_DR.md` archives them.
- **DORA Art. 30 contractual evidence:** stored with the assessment under
  `Reports/<Supplier>/<Service>/` (SharePoint versioning on).
- **Copilot second channel:** in AIMS scope; same agents, same Layers 1–2,
  no write path. Deployer assessment: `AI-ACT-DEPLOYER-ASSESSMENT-TEMPLATE.md`.
- Additional audit evidence: `templates/audit.log`, SharePoint version
  history, `team/ACCESS_REGISTER.md` (write-capable identities).

## Verifying the control

```bash
python3 ../scripts/attach_integrations.py --dry-run   # shows [read-only] on every OpenAPI tool
grep -rn "APPROVAL GATE" ../build/agents/*/instructions.md | wc -l   # = converted agents (delivery/orchestrator agents are assembled at create time — check the live agent instructions)
python3 ../scripts/attach_integrations.py --dry-run --list-mcp-tools           # every MCP tool shows readOnlyHint
# live check: every agent except output-verifier carries the gate
```

Operational evidence that the gates are exercised:
`../operations/kql/approval-sla.kql` (pending / expired gates) and the
`approval-sla` alert in `../operations/alerts.bicep` (or `approval-expiry` in
`../infra/monitoring.bicep` — `../operations/MONITORING.md` §4 says which
catalogue is deployed); `../operations/RUNBOOK.md` FM-10 and FM-20 (gate
integrity failures are P1). Guardrail register, observability wiring and the
evaluation baseline procedure:
`../enterprise/series/08-guardrails-observability-evaluation.md`. Promotion of a
new agent version (including Agent Optimizer candidates) is a Tier C change
approved by the platform owner.

Related: `RISK_THRESHOLDS.md` (threshold changes are methodology changes),
`MEMORY_POLICY.md`, `../team/TEAM_MODEL.md` (identities and groups).
