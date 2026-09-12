# Step 07 — Workflows: Logic Apps Standard, pipelines, approval flow

**Objective.** Deploy Logic Apps Standard (`infra/logicapp.bicep`) with
the 12 `report-delivery-pipeline` instances of `workflows/pipelines.json`
and the standalone workflows of `workflows/`, rewritten from the classic
threads/runs REST to the GA **conversations / responses** endpoints (D1);
wire the human-approval side (`approvalWebhookUrl`) to the routing policy;
bind every secret as a Key Vault app setting; prove one pipeline end to
end into the test SharePoint site.

**Owner / effort.** `{upn:francisco.gomes}`; 4 days. **Depends on** 05, 06.

## 1. Platform facts

| Fact | Status / source |
|---|---|
| Foundry project data plane: `api-version=v1` (GA) for agents / conversations / responses; hosted-agent and agent-application operations use `2025-11-15-preview` | [GA] https://learn.microsoft.com/en-us/azure/foundry/reference/foundry-project-rest-preview |
| Azure OpenAI **v1 GA API**: base path `…/openai/v1/`, `api-version` no longer required for GA features; preview features opt in per feature | [GA] https://learn.microsoft.com/en-us/azure/foundry/openai/api-version-lifecycle (2026-06-05) |
| Logic Apps Standard **Agent action** (preview): call/create Foundry agents from a workflow, run autonomously from triggers, expose connector actions or entire Request-triggered workflows as agent tools (built-in actions run in-process with VNet integration) | [preview] https://learn.microsoft.com/en-us/azure/logic-apps/automate-foundry-agents-with-workflows (2026-08-13) |
| Classic "Logic Apps as agent tool" (Consumption only, same RG) retires with classic agents 2027-03-31; the new service has no native Logic Apps tool | [GA] https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/migrate#agent-tool-availability (2026-08-05) |
| Foundry portal *workflows* (visual designer) retire 2026-12-01 — not used | [preview] retirement page ms.date 2026-07-31 (index D12) |

## 2. Rewrite of the agent-invocation actions (shared delta S-07)

Every workflow that calls an agent today does *create thread → post
message → create run → poll → read messages* with `apiVersion 2025-05-01`.
The new sequence is two HTTP actions plus (for long runs) a poll on the
response id. Literal replacement for `Run_producing_agent` and its
`Until_agent_run_completes` / `Get_agent_output` in
`workflows/report-delivery-pipeline.json` (same pattern for the verifier
actions and for `defender-incident-brief`, `scheduled-followup`,
`agent-fanout`, `generic-event-intake`, `teams-post-approved`,
`morning-brief`, `mailbox-intake`, `watch-until`):

```json
{
  "Create_conversation": {
    "type": "Http",
    "inputs": {
      "method": "POST",
      "uri": "@{parameters('foundryEndpoint')}/openai/v1/conversations?api-version=@{parameters('apiVersion')}",
      "headers": { "Content-Type": "application/json" },
      "body": { "metadata": { "owner": "@{triggerBody()?['requestedBy']}", "runId": "@{workflow().run.name}" } },
      "authentication": { "type": "ManagedServiceIdentity", "audience": "https://ai.azure.com" }
    },
    "runAfter": { "Select_attachments": [ "Succeeded" ] }
  },
  "Run_producing_agent": {
    "type": "Http",
    "inputs": {
      "method": "POST",
      "uri": "@{parameters('foundryEndpoint')}/openai/v1/responses?api-version=@{parameters('apiVersion')}",
      "headers": { "Content-Type": "application/json" },
      "body": {
        "conversation": "@{body('Create_conversation')?['id']}",
        "agent_reference": { "name": "@{parameters('agentName')}", "type": "agent_reference" },
        "input": "@{variables('promptText')}",
        "background": true
      },
      "authentication": { "type": "ManagedServiceIdentity", "audience": "https://ai.azure.com" }
    },
    "runAfter": { "Create_conversation": [ "Succeeded" ] }
  },
  "Until_agent_run_completes": {
    "type": "Until",
    "expression": "@contains(createArray('completed','failed','incomplete','cancelled'), body('Get_response')?['status'])",
    "limit": { "count": 240, "timeout": "PT2H" },
    "actions": {
      "Delay_30s": { "type": "Wait", "inputs": { "interval": { "count": 30, "unit": "Second" } } },
      "Get_response": {
        "type": "Http",
        "inputs": {
          "method": "GET",
          "uri": "@{parameters('foundryEndpoint')}/openai/v1/responses/@{body('Run_producing_agent')?['id']}?api-version=@{parameters('apiVersion')}",
          "authentication": { "type": "ManagedServiceIdentity", "audience": "https://ai.azure.com" }
        },
        "runAfter": { "Delay_30s": [ "Succeeded" ] }
      }
    },
    "runAfter": { "Run_producing_agent": [ "Succeeded" ] }
  }
}
```

Conventions kept from `workflows/README.md`: terminal-state expression
(never `!= 'in_progress'`), `apiVersion` bound to the
`FOUNDRY_API_VERSION` app setting (now `v1`), managed identity with
audience `https://ai.azure.com`, `agentName` replaces `agentId`
(`pipelines.json` already keys on names). The `Agent_draft_text` action
reads `body('Get_response')?['output_text']` (fallback: the last
`output[].content[].text`). Field names follow the `azure-ai-projects` 2.x
Responses samples (`agent_reference`, `conversation`, `background`);
confirm against the REST reference on the execution day and record the
verified shape in the sign-off.

## 3. Instances, parameters, secrets

| Item | Kit source | Action |
|---|---|---|
| Logic Apps Standard app `{baseName}-la` | `infra/logicapp.bicep` (WS plan, runtime storage, VNet integration `snet-apps`, Key Vault app settings) | deployed by `main.bicep` (`enableLogicApps=true`) |
| 12 pipeline instances | `workflows/pipelines.json` × `workflows/report-delivery-pipeline.json` | **Gap G-07**: `scripts/build_logicapps.py` and `ci/deploy_logicapps.sh` are referenced by `workflows/README.md` but do not exist. Until they do, generate `build/logicapps/<name>/workflow.json` by substituting each `pipelines.json` entry into the template parameters (`agent`→`agentName`, `render`→`renderFormat`, `approvalKind`, `libraryRoot`→`libraryRootItemId`, fallbacks, flags) and deploy with `az logicapp deployment source config-zip -g {rg} -n {baseName}-la --src build/logicapps.zip` (shared delta S-12: add the script; the integration pass owns it) |
| Standalone workflows | `onetrust-assessment-intake`, `scheduled-deepsearch`, `defender-incident-brief`, `jira-finding-sync`, `morning-brief` (×5 users), `mailbox-intake`, `watch-until`, `scheduled-followup`, `agent-fanout`, `generic-event-intake`, `teams-post-approved`, `speech-transcription`, `report-status`, `template-update-approval` | same zip |
| Secrets as app settings | `infra/logicapp.bicep` `secretNames`: `kv-delivery-function-key`, `kv-approval-webhook-url`, `kv-teams-webhook-url`, `kv-jira-api-token`, `kv-onetrust-api-token`, `kv-iaf-client-secret` | create the six secrets in `{baseName}-kv` (owner under PIM); app settings are `@Microsoft.KeyVault(VaultName=…;SecretName=…)` references; Logic Apps MI holds `Key Vault Secrets User` (`infra/workload-rbac.bicep`) |
| Identity | Logic Apps MI → **Foundry User** on the project; no Graph roles (SharePoint I/O only through the Function) | `infra/workload-rbac.bicep` `logicAppAiUser`; `team/least-privilege/SHARED_DELTAS.md` row for `workflows/README.md` |
| Approval side | `approvalWebhookUrl` → Power Automate flow or Function that renders the draft as a Teams Approval, resolves approvers from `team/least-privilege/approvals/routing.json` (or `team/approval-policy.json`) minus the requester, verifies the approver's token UPN, and POSTs `{decision, approver, comment, correlationId}` to the `callbackUrl`; expiry `P3D` (`P7D` for template updates) | built by the owner in the Power Platform environment `{pp-env:infosec-assurance}`; DLP policy must allow HTTP to the Logic Apps callback host only |

Rule for the **Agent action (preview)** — recorded here and mirrored into
`workflows/README.md` by the integration pass (shared delta S-13): the
Logic Apps Agent action may orchestrate **read** steps only; **no write
connector (Jira create, SharePoint upload, IAF submit, Teams post, mail)
is ever exposed as an agent tool** — writes remain deterministic actions
that run after the `HttpWebhook` approval gate. "Workflow as tool" is
piloted for `ensure_folder`/`render` read-side helpers only once the
feature is GA.

## 4. Click-path

**Azure portal.** Logic App `{baseName}-la` → *Workflows* → *Add* → paste
each `definition` (or the zip deploy) → *Parameters* → check the
`{placeholders}` are replaced by app settings → *Identity* → system-assigned
→ *Configuration* → the six `@Microsoft.KeyVault(...)` settings show a
green check → *Networking* → VNet integration `snet-apps`; inbound
private endpoint (`infra/main.bicep` `peLogicApp`). Run history → a run
suspended at `Human_approval_gate` shows *Waiting* until the callback.
**Foundry portal.** *Build* → *Tracing* → the run created by the Logic App
appears with `metadata.runId` = the Logic Apps run name.

## 5. CLI / kit scripts

```bash
az logicapp show -g {rg} -n {baseName}-la --query "identity.principalId" -o tsv
az role assignment list --assignee {la-principal-id} --scope {project-id} -o table        # Foundry User
# trigger one pipeline (owner token; the trigger accepts authenticated team callers only)
curl -s -X POST "https://{baseName}-la.azurewebsites.net/api/deepsearch-report/triggers/manual/invoke?api-version=2022-05-01&sp=…&sv=1.0&sig=…" \
  -H "Content-Type: application/json" -d '{"pipeline":"deepsearch-report","supplierName":"Acme Test","serviceName":"Managed SOC","requestedBy":"{upn:francisco.gomes}"}'
# → 202 {runId, status: ACCEPTED}; then
curl -s "https://{baseName}-la.azurewebsites.net/api/report-status/triggers/manual/invoke?runId={runId}&…"
```

## 6. Values captured into `setup/.env`

| Variable | Value |
|---|---|
| `FOUNDRY_API_VERSION` | `v1` (app setting of the same name in `logicapp.bicep` `foundryApiVersion` — default changes from `2025-05-01`, S-07) |
| `LOGIC_APP_NAME` | Bicep output `logicAppName` |
| `APPROVAL_WEBHOOK_URL`, `TEAMS_WEBHOOK_URL` | **not** in `.env` — Key Vault only (`kv-approval-webhook-url`, `kv-teams-webhook-url`) |

## 7. Verification

| # | Check | Pass when |
|---|---|---|
| V1 | `python3 -c "import json,glob; [json.load(open(f)) for f in glob.glob('workflows/*.json')]"` and the built instances | all parse; no `threads/` string remains (`grep -rn "threads" workflows/ build/logicapps/` → 0 hits) |
| V2 | `dev`: `deepsearch-report` instance run with a public supplier | reaches `Run_output_verifier`, verdict read; run stops at the gate (no approval side in dev) and expires after `P3D` without any write |
| V3 | `test`: same run, approved by a **different** user in Teams | file appears at `Reports/Acme Test/Managed SOC/DeepSearch_AcmeTest_ManagedSOC_{date}.html` on the test site; `webUrl` + org share link returned; Teams notice posted |
| V4 | `test`: approver = requester | approval flow rejects; run records `DECIDED_NOT_STORED` |
| V5 | `test`: verifier FAIL (draft with a removed section) | no gate raised, Teams notice `brief_failed_verification`-style, nothing written |
| V6 | `report-status` for V2–V5 run ids | `AWAITING_APPROVAL` / `STORED` / `DECIDED_NOT_STORED` as expected |
| V7 | Key Vault references: Logic App *Configuration* | all six resolved (green); `keyvault-human-secret-read` alert shows only the owner's PIM window |
| V8 | Routines: `onetrust-assessment-intake`, `scheduled-deepsearch`, `jira-finding-sync` in **disabled** state in `test` until UAT; enabled one at a time with their gates observed | run history per routine |
| V9 | `operations/kql/approval-sla.kql`, `pipeline-failures.kql` return rows for the test runs | telemetry schema confirmed (RUNBOOK H9) |

**Rollback.** Disable the workflow instance (Logic Apps Standard Operator);
redeploy the previous zip; run history is preserved across versions.
**ISMS evidence.** run-history exports with approval callbacks (approver
UPN, timestamp, correlationId), V1–V9 outputs — EU AI Act Art. 14 (human
oversight) and Art. 12; ISO 42001 A.6.2.7, A.9.3; ISO 27001:2022 A.5.36,
A.8.32; DORA Art. 10(1).

## Sources
- [GA] Foundry project REST (v1 / preview) — https://learn.microsoft.com/en-us/azure/foundry/reference/foundry-project-rest-preview
- [GA] Azure OpenAI v1 API lifecycle — https://learn.microsoft.com/en-us/azure/foundry/openai/api-version-lifecycle (2026-06-05)
- [preview] Logic Apps Agent action — https://learn.microsoft.com/en-us/azure/logic-apps/automate-foundry-agents-with-workflows (2026-08-13)
- [GA] Tool availability (Logic Apps classic tool retirement) — https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/migrate#agent-tool-availability (2026-08-05)
- [GA] Migration guide (Responses API) — https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/migrate (2026-08-05)
- Kit: `workflows/README.md`, `workflows/pipelines.json`, `infra/logicapp.bicep`, `team/least-privilege/approvals/routing.json`
