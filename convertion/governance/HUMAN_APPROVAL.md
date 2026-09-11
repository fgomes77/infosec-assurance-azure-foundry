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
attempt says. Write operations exist only inside the approval-gated
workflows (Layer 3). A specific write may be granted to a specific agent
only by listing the connection in that agent's `"write_connections"` in
`integrations/registry.json` — the default for every agent is none, and any
grant is a deliberate, reviewable diff to this repository.

## Layer 2 — Behavioural: a draft-then-approve protocol in every agent

`convert_skills.py` and `create_orchestrator.py` append the APPROVAL GATE
block to every agent's instructions: prepare the complete draft (ticket,
finding, report, answer set), present it to the human with a clear
"awaiting your approval" marker, and proceed only on an explicit approval in
the conversation; a rejection or edit request restarts the cycle. This keeps
behaviour correct even for channels Layer 1 cannot see (e.g. text the human
might paste onward), and preserves the mandatory sign-off gate the
onetrust-form-b skill already carried.

## Layer 3 — Process: approval steps inside the workflows

Every Logic Apps workflow suspends before its submission-of-record actions
(Jira create, IAF submit, SharePoint deliverable upload) on an
`HttpWebhook` approval gate: the draft is sent to the approver (Teams), the
workflow waits for a human `approved`/`rejected` callback, expires after 3
days, and records rejections without submitting. Notifications-only steps
(Teams summaries) are not gated. See `../workflows/README.md`.

## Scope notes

- **MCP server:** `ask_*` tools inherit Layers 1–2 (the agents they reach
  hold read-only tools and the draft protocol). `save_memory` is itself the
  human approval act — a person (or their client, on their instruction)
  persists a note; agents cannot call it.
- **Copilot surface:** the same agents answer in Copilot, so Layers 1–2
  apply unchanged; Copilot adds no write path.
- **Orchestrator/advisor:** carry the same gate; a connected agent cannot
  launder a write, because the specialist it hands off to is read-only too.

## Compliance mapping

- **EU AI Act Art. 14 (human oversight):** approval gates are the oversight
  measure — outputs take effect only after natural-person review.
- **ISO/IEC 42001 Annex A** (A.6 AI system life cycle, A.9 use of AI
  systems): this policy is the documented control; audit evidence = the
  registry's empty `write_connections`, the gate block in deployed agent
  instructions, and workflow run history showing approval callbacks.
- **DORA/NIS2 context:** submissions of record into risk registers and
  ticketing remain human-accountable acts.

## Verifying the control

```bash
python3 ../scripts/attach_integrations.py --dry-run   # shows [read-only] on every OpenAPI tool
grep -rn "APPROVAL GATE" ../build/agents/*/instructions.md | wc -l   # = number of agents
```
