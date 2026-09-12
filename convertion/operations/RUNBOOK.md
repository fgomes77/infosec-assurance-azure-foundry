# Operations Runbook — Day-2 Operation of the InfoSec Assurance Foundry Platform

Day-2 procedures for the platform described in `../README.md` /
`../ARCHITECTURE.md`: health checks, failure modes per component with
diagnosis and fix, severities, and escalation to the accountable owner.
Who may do what is fixed by `../team/TEAM_MODEL.md` (§3 flow F7 incident,
§12.3 break-glass); this file only says *how*. Companion files:
`MONITORING.md` (signals and alert catalogue), `SUPPORT_MODEL.md` (intake
and SLOs), `CHANGE_MANAGEMENT.md` (every fix that changes configuration),
`access-governance/BREAK_GLASS.md` (owner unavailable).

Invariants that no runbook step may relax: agents stay read-only
(`../governance/DATA_PROTECTION_GUARDRAILS.md` §2), no write reaches
SharePoint or a system of record without verifier PASS + human approval
(`../governance/HUMAN_APPROVAL.md`), identities are Entra users and managed
identities (no keys), EU region, no Euronext data to the web. A fix that
needs an exception to any of these is a Tier C change, never a runbook
action. Placeholders in `{braces}`.

## 1. Roles in operation

| Role | Who | Standing access used | Escalation target |
|---|---|---|---|
| Reporter / L1 | any of the five (`sg-infosec-foundry-users`) | own Entra user: playground, Copilot, MCP, Teams Approvals | peer in `{teams:infosec-assurance-platform}` |
| Operator / L2 | owner `{upn:francisco.gomes}` | standing `Reader` RG + `Log Analytics Reader` (§5 L6 of the team model); PIM `-admin-pim` for any change | landing-zone `{group:azure-platform}`, custodians, Microsoft |
| Continuity | deputy `{upn:deputy-approver}` | `-breakglass` PIM (disable-only, `BREAK_GLASS.md`) | owner on return |
| Custodians | `{group:jira-admins}`, `{group:onetrust-admins}`, `{group:enx-gateway}`, `{upn:iaf-owner}`, `{group:spo-admins}`, `{group:iam-admins}` | their own systems | — |
| SOC | `{group:soc-oncall}` | receives severity-1 alerts (`alerts.bicep`) | — |

Control: ISO 27001:2022 A.5.2, A.5.24; DORA Art. 5(2), 17(1); NIS2 Art. 20.

## 2. Health checks

All checks are read-only and run with the owner's standing roles (no PIM).
Evidence goes to `Governance/Operations/{yyyy}-{mm}/` on the SharePoint site.

### Daily (owner, ~10 min; automated where an alert exists)

| # | Check | How | Healthy when | Alert (`MONITORING.md` §4) |
|---|---|---|---|---|
| H1 | Alert inbox | Azure Monitor alerts, last 24 h | no unacknowledged severity 1–2 | all |
| H2 | Pipeline runs | Logic Apps `{baseName}-la` run history, or `LogicAppWorkflowRuntime` (`kql/verifier-fail-rate.kql`, `kql/approval-sla.kql`) | no `Failed`/`TimedOut` runs; no gate pending > 48 h | `pipeline-run-failed`, `approval-sla` |
| H3 | Verifier verdicts | `kql/verifier-fail-rate.kql` without the final `where` | FAIL rate ≤ 30 % per pipeline | `verifier-fail-rate` |
| H4 | Egress | `kql/egress-detection.kql` | zero rows | `egress-internal-marker` |
| H5 | Model capacity | Foundry account metrics `AzureOpenAIRequests` by `StatusCode` | 429 < 1 % of requests | `model-throttling-429` |
| H6 | Delivery Function | `AppRequests` for `{baseName}-fn-delivery` | 5xx = 0; p95 `render` < 60 s | `delivery-function-5xx` |
| H7 | Privileged activity | `breakglass_window_write`, `agent_modified_by_non_deploy_identity`, `keyvault-human-secret-read` | zero rows, or every row matches a PIM activation with a ticket | those three |

### After every deployment or SDK bump (owner, within 1 business day)

| # | Check | How | Healthy when |
|---|---|---|---|
| H8 | Drift baseline | `build/manifest.json` of the run vs the stored baseline (`CHANGE_MANAGEMENT.md` §7) | only the agents named in the change differ |
| H9 | Telemetry schema | run each `kql/*.kql` without its final `where`, and the inline queries of `alerts.bicep`, against the last hour | every query returns columns (no "unknown column"); `gen_ai.*` attribute names and `LogicAppWorkflowRuntime` / `AzureDiagnostics` column names still match — otherwise fix the query (Low-risk change) before trusting the alerts |

### Weekly (owner)

| # | Check | How | Healthy when |
|---|---|---|---|
| W1 | Smoke test | `python3 ../scripts/smoke_test.py --agent infosec-assurance-orchestrator --prompt "One-line health check: name three DORA Art. 30(2) baseline contractual provisions."` (same prompt as `../deploy.sh` step 7) | answer cites Art. 30(2), in English, within 60 s |
| W2 | Read-only tool surface | `python3 ../scripts/attach_integrations.py --dry-run` | `[read-only]` on every OpenAPI tool; `write_connections` absent for every agent in `../integrations/registry.json` |
| W3 | Approval-gate presence | `grep -rn "APPROVAL GATE" ../build/agents/*/instructions.md \| wc -l` = agent count | equal |
| W4 | Connections | Foundry portal → Connections: every `conn-*`, `bing-grounding`, `enx-gateway-mcp`, `app-insights` present, no auth error | all green |
| W5 | Memory store | `python3 ../scripts/memory_store.py list` | lists without error; no note older than the retention set in `../team/TEAM_MODEL.md` §13 |
| W6 | Credential ages | `../team/access-review.sh --quick` (Key Vault secret *names* and dates only) | none past its rotation date in `../team/ACCESS_REGISTER.md` |
| W7 | Cost | Cost Management, RG `rg-infosec-foundry`, week-over-week | within ±25 % of the monthly forecast unless a known campaign explains it |

### Monthly (owner; users consulted) — the ISMS operating rhythm

| # | Activity | Input | Output |
|---|---|---|---|
| M1 | Evaluation review (`../ARCHITECTURE.md` "Evaluation and success metrics") | `kql/verifier-fail-rate.kql`, approval rework counts from `{list:ApprovalDecisions}`, grounding-rate sample | findings in `Governance/Operations/{yyyy}-{mm}/evaluation.md`; drift → `CHANGE_MANAGEMENT.md` re-sync |
| M2 | Cost and tier review (`../governance/MODEL_ROUTING.md` rule 7) | `kql/latency-and-tokens.kql` (full table) | tier moves proposed as Tier C changes; advisory agents never move down |
| M3 | Known-issue list refresh | `SUPPORT_MODEL.md` §6 | updated list posted in the Teams channel |
| M4 | PIM activation report | Entra PIM audit | sent to `{upn:line-manager}` (team model §12.2) |

Quarterly and annual items (access review, DR test, template inventory
review) are in `access-governance/QUARTERLY_ACCESS_REVIEW.md` and
`CHANGE_MANAGEMENT.md` §9.

## 3. Severity model

| Sev | Definition | Examples | Response (owner or deputy) | Resolution target | Notify |
|---|---|---|---|---|---|
| P1 | Confidentiality or integrity event, or platform unusable for all five | confirmed internal identifier in a Bing query; credential exposure; report stored under the wrong supplier; ARM write outside a PIM window; Foundry account down | 1 h, 24×7 best effort (business hours contractual) | 1 business day to contain; fix per `CHANGE_MANAGEMENT.md` §8 | owner, deputy, `{upn:line-manager}`, SOC; DPO if personal data involved |
| P2 | One requirement a–j unavailable, or a control degraded | all pipelines failing; verifier FAIL rate > 30 %; approval flow not delivering cards; delivery Function 5xx | 4 business hours | 2 business days | owner, deputy, channel |
| P3 | Degradation with workaround | 429 throttling; slow reasoning runs; one connection failing (agent still answers without it); Copilot surface stale | 1 business day | 5 business days | channel |
| P4 | Cosmetic / request | template wording, new watchlist supplier, question | 2 business days | next monthly cycle | — |

Rules: any user may raise any severity; the owner confirms the level
within the response time; a P1 with the owner unavailable > 2 business
days invokes `BREAK_GLASS.md`; every P1/P2 gets a post-incident note
(§6). Control: ISO 27001:2022 A.5.24–A.5.27; DORA Art. 17–19 (classify
ICT incidents; report major ones through the Euronext DORA process — this
platform is an internal ICT service, so the DORA major-incident criteria
apply through the group process, not from here); NIS2 Art. 23.

## 4. Failure modes per component

Each row: symptom → diagnosis (read-only) → fix (with the access it needs
and the change tier). "Disable" actions are allowed under PIM/break-glass
without approval; "change" actions follow `CHANGE_MANAGEMENT.md`.

### 4.1 Foundry account, project, model deployments (`{baseName}-aif`, `{baseName}-proj`)

| Id | Symptom | Diagnosis | Fix | Access / tier |
|---|---|---|---|---|
| FM-01 | Every agent call fails with 401/403 | `az account show`; role of the caller on the project (`Azure AI User`); `disableLocalAuth: true` means key auth is refused by design | user not in `sg-infosec-foundry-users` → `access-governance/ACCESS_LIFECYCLE.md`; MI missing role → `../team/rbac.bicep` redeploy | owner PIM `Azure AI Developer` only if a connection is involved; RBAC = Tier C PR |
| FM-02 | Agent answers but a tool is missing (no web results, no Jira data) | Foundry portal → agent → tools; `attach_integrations.py --dry-run --only <agent>`; connection status | re-run `attach_integrations.py --only <agent>` (idempotent) | owner PIM `Azure AI Developer` (§5 L1) |
| FM-03 | `egress-internal-marker` alert | open the trace (`OperationId`) in App Insights; read the query text; confirm true positive | true positive: P1 — record in ticket `{jira:INFOSEC-PLAT}-nnn`, add the marker to the instruction-layer rule in `attach_integrations.py` **and** `kql/egress-detection.kql` (Tier C PR); never disable Bing wholesale unless the leak repeats | disable connection = PIM; fix = Tier C |
| FM-04 | Content-filter block on legitimate security text | trace shows `content_filter` finish reason | adjust the custom RAI policy severity for that category (Tier C); never disable filtering (`DATA_PROTECTION_GUARDRAILS.md` §3) | Tier C |
| FM-05 | `model-throttling-429` | metrics by `ModelDeploymentName` | short term: retries already in `_azure_helpers.py`/workflow `Until` loops; sustained: raise `modelCapacity` in `../infra/main.parameters.json` | Tier C (infra) |
| FM-06 | p95 latency > 5 min on an agent | `kql/latency-and-tokens.kql`; check whether the run loops on tool errors | fix the failing tool (FM-02/FM-13); if the loop is behavioural, instruction change | Tier C |
| FM-07 | Token budget exceeded | same query; identify agent/model | confirm legitimate load; else move a non-advisory agent down a tier at M2 (`MODEL_ROUTING.md` rule 7) | Tier C |

### 4.2 Agents, vector stores, memory

| Id | Symptom | Diagnosis | Fix | Access / tier |
|---|---|---|---|---|
| FM-08 | Verifier FAIL rate rising on one pipeline | `kql/verifier-fail-rate.kql`; compare a FAIL draft with the verifier findings; `python3 ../scripts/verify_conversion.py` | drift in knowledge/instructions → re-sync from a fresh export (`CHANGE_MANAGEMENT.md` §5 type "re-sync"); tier too low → M2 | Tier C |
| FM-09 | Agent run stuck `queued`/`in_progress` > 15 min | Foundry portal → threads; App Insights trace for the run | cancel the run (portal); re-run; if repeated, FM-05 or a hung tool (FM-13) | user (own run) / owner |
| FM-15 | Vector store missing files, `file_search` returns nothing | `create_agents.py --dry-run`; compare `build/manifest.json` with the live agent | re-run `../deploy.sh` steps 3–4 for that agent (`create_agents.py --only <agent>`) | owner PIM `Azure AI Developer` |
| FM-16 | Memory note wrong or contains personal data beyond minimisation | `memory_store.py list`; identify author | author deletes; else `MEMORY_DELETE` Tier C via deputy (`TEAM_MODEL.md` §13) | user / Tier C |
| FM-17 | Prompt-injection suspected in a retrieved document | verifier finding (rule 7), or a user report | quarantine the source file (custodian), re-run; add the pattern to `../agents/verifier_instructions.md` if new | P1 if a write was attempted; Tier C |

### 4.3 Logic Apps pipelines and the approval flow (`{baseName}-la`)

| Id | Symptom | Diagnosis | Fix | Access / tier |
|---|---|---|---|---|
| FM-10 | `approval-sla` alert — gate pending > 48 h or expired | run history → `Human_approval_gate` inputs: `requestedBy`, `kind`, `reportType`; `{list:ApprovalDecisions}` | pending: remind the tier group; Tier B > 2 business days → fallback per `../team/approval-policy.json`; expired = rejection, requester re-triggers | approvers |
| FM-18 | Cards not reaching Teams | approval flow (Power Automate/Function behind `approvalWebhookUrl`) run history; webhook secret expiry | rotate the webhook (§5 L3 KV); resubmit the suspended run from run history (`Logic App Standard Operator`) | owner PIM |
| FM-19 | Run failed at `Run_producing_agent` / `Get_agent_output` | HTTP status in the action output: 401 → Logic App MI lost `Azure AI User`; 404 → agent id parameter stale after re-create | RBAC via `rbac.bicep`; update the `agentId` app setting from `build/manifest.json` | Tier C |
| FM-20 | Approver == requester accepted, or approver outside the tier group | approval flow logs; `{list:ApprovalDecisions}` row | P1 control failure: disable the workflow (PIM), fix the flow, re-approve the affected items with a valid approver | disable = PIM; fix = Tier C |
| FM-21 | Scheduled workflow (`scheduled-deepsearch`, `onetrust-assessment-intake`) not firing | trigger history; app stopped; storage account for the runtime unreachable | start the app; check the runtime storage identity-based connection | owner PIM `Logic App Standard Operator` |

### 4.4 Delivery Function and SharePoint (`{baseName}-fn-delivery`, `{sharepoint:infosec-assurance}`)

| Id | Symptom | Diagnosis | Fix | Access / tier |
|---|---|---|---|---|
| FM-11 | `render` 5xx | `AppRequests`/`AppTraces` for the Function; Node runtime missing for `pptx`; renderer not staged | `python3 ../scripts/stage_renderers.py` + `func azure functionapp publish` (`../functions/delivery/README.md`) | owner PIM `Website Contributor` (§5 L5) |
| FM-12 | `ensure_folder` 403/404 | Function MI `Sites.Selected` write grant missing or site id changed (`SHAREPOINT_SITE_ID`) | re-grant per `../functions/delivery/README.md`; never widen to `Sites.ReadWrite.All` | custodian `{group:spo-admins}` + owner; Tier C |
| FM-22 | Duplicate supplier folder or report under the wrong supplier | folder rule in `../sharepoint/README.md` (normalisation, case-insensitive); check the trigger payload | P1 if a report landed under another supplier: move the file (site owner), record in the ticket; if the normalisation missed a case, fix `normalise()` (Tier C) | owner (site owner) |
| FM-23 | Share link anonymous or wrong scope | `Upload_and_share` output: `scope` must be `organization` (`users` for `Reports/DPO/`) | remove the link (site owner); fix the pipeline parameter | P1; Tier C |
| FM-24 | Upload succeeds, Teams notification fails | `Notify_team` action output | notification-only step, not gated: fix the `teamsWebhookUrl` app setting | owner PIM |

### 4.5 Connections, Key Vault, credentials

| Id | Symptom | Diagnosis | Fix | Access / tier |
|---|---|---|---|---|
| FM-13 | One integration returns 401/403 (Jira, OneTrust, SSC, IAF, Confluence, ENX gateway) | trace of the tool call; secret age in `access-review.sh --quick`; custodian status page | rotate with the custodian (`TEAM_MODEL.md` §3 F8): new KV secret version, connection re-pointed; agents keep answering without that tool meanwhile (non-blocking principle) | owner PIM `Key Vault Secrets Officer` 2 h (§5 L3) |
| FM-25 | Credential exposure suspected | `keyvault-human-secret-read` alert; custodian audit log | P1: disable the secret version (PIM), custodian revokes the token, issue new, `ACCESS_REGISTER.md` entry, post-incident note | PIM; ticket |
| FM-26 | Bing Grounding key invalid | `bing-grounding` connection error | rotate the Bing key (`Contributor` 2 h on `{baseName}-bing`) — the single API key on the platform | owner PIM |
| FM-27 | ENX gateway MCP tool list changed / write tool appeared | `enx-gateway.json` vs gateway response | request the read-only toolset from `{group:enx-gateway}`; detach until confirmed | PIM (detach); Tier C |

### 4.6 MCP server, Copilot, GitHub deploy pipeline

| Id | Symptom | Diagnosis | Fix | Access / tier |
|---|---|---|---|---|
| FM-28 | Local MCP server fails auth | user's `az login` expired; user not in `-users` | user re-authenticates; else lifecycle runbook | user |
| FM-29 | Hosted MCP rejects a team member | Easy Auth allowed group; Container App MI role | group membership (lifecycle); MI role via `rbac.bicep` | Tier C |
| FM-30 | Copilot agent answers with stale behaviour | Copilot Studio publication date vs last `deploy.sh` | republish to `sg-infosec-foundry-users` only (`../integrations/copilot/README.md`) | owner (Environment Maker) |
| FM-31 | `deploy.sh` fails at step 2 (`verify_conversion.py`) | its output lists the discrepancy (fidelity/coverage/rules/freshness) | never bypass: fix the export or the converter, re-run; the gate is what keeps outputs identical to claude.ai | Tier C |
| FM-32 | `deploy.sh` fails at steps 3–6 in the pipeline | GitHub Actions log; OIDC federated credential; deploy SP roles | re-run after fixing; hotfix by hand only under `CHANGE_MANAGEMENT.md` §8 | deploy SP / owner PIM |

## 5. Escalation

| Step | Who | Channel | When |
|---|---|---|---|
| 1 | Reporter | `{teams:infosec-assurance-platform}` post using the intake template (`SUPPORT_MODEL.md` §3) | immediately |
| 2 | Peer (L1) | same thread | within 4 business hours; resolves self-service items (§4 rows marked "user") |
| 3 | Owner (L2) | ticket `{jira:INFOSEC-PLAT}-nnn` opened by the owner for every P1–P3 | within the §3 response time |
| 4 | Deputy | `BREAK_GLASS.md` | owner unreachable for a P1/P2, or > 2 business days with a pending Tier C item |
| 5 | L3 | landing-zone `{group:azure-platform}` (network, subscription, policy), custodians (target systems), Microsoft support via the landing-zone team's plan (Foundry, Logic Apps, Function service issues) | when the cause is outside the platform |
| 6 | Line manager / CISO delegate | `{upn:line-manager}` | every P1; every break-glass activation |

Never escalate by sharing screenshots of report content, secrets or thread
contents in the channel; reference thread ids, run ids and ticket numbers.

## 6. Incident record and post-incident note

Filed under `Governance/Incidents/{yyyy}/{ticket}.md` within 5 business
days of closing a P1/P2: timeline (UTC), detection source (alert id or
reporter), impact (which requirement a–j, which suppliers' reports), root
cause, actions taken with the identity used (PIM activation id or
break-glass ticket), what was disabled and when it was re-enabled, the
change record that fixed it (`CHANGE_MANAGEMENT.md` §7), evidence links
(run ids, `OperationId`s, `{list:ApprovalDecisions}` rows), and the
prevention item (alert, instruction, runbook or template change). Control:
ISO 27001:2022 A.5.27 (learning from incidents), A.5.28 (evidence); DORA
Art. 13(2), 17(3); ISO 42001 A.6.2.8 (AI incident handling), A.8.4.

## 7. Compliance mapping

| Control / article | Implemented by |
|---|---|
| ISO 27001:2022 A.5.24–A.5.28 | severities §3, escalation §5, incident record §6 |
| A.5.29, A.5.30 | deputy continuity + break-glass path (§1, §5 step 4) |
| A.5.36, A.8.8 | weekly W2/W3 checks prove the read-only and approval-gate controls are still deployed |
| A.8.6 | H5, FM-05, FM-07 capacity handling |
| A.8.15, A.8.16 | daily checks over App Insights / Log Analytics evidence; evidence folders |
| A.8.32 | every "change" cell routes to `CHANGE_MANAGEMENT.md` |
| DORA Art. 9(2), 10, 11, 17 | detection and response procedures; continuity through the deputy; incident classification |
| NIS2 Art. 21(2)(b)–(c), 23 | incident handling, business continuity, reporting path |
| ISO 42001 A.6.2.6, A.6.2.8, A.8.4 | monthly evaluation M1–M2; AI incident handling FM-03/FM-17; performance monitoring |
| EU AI Act Art. 14, 26(5) | approval SLA (FM-10) and verifier monitoring keep human oversight effective |
