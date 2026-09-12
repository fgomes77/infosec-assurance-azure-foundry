# Monitoring — Signals, Tables, Dashboards and the Alert Catalogue

What the platform emits, where it lands, which queries the owner runs, and
which alerts page whom. Implements the observability row of
`../ARCHITECTURE.md` ("Guardrails and observability"), the detective layer
of `../governance/DATA_PROTECTION_GUARDRAILS.md` §1 and §4, the metrics of
`../governance/MODEL_ROUTING.md` rule 7, and the detective controls named
in `access-governance/BREAK_GLASS.md` §4. Alerts are deployed by
`alerts.bicep`; queries live in `kql/`; responses are in `RUNBOOK.md`.

Monitoring is read-only: the owner's standing `Log Analytics Reader`
(`../team/TEAM_MODEL.md` §5 L6) is enough for every query here, and no
alert rule holds a write permission anywhere. Users need no monitoring
role — they report, the owner triages (§3 flow F9). Control: ISO
27001:2022 A.8.15 (logging), A.8.16 (monitoring activities), A.8.2; DORA
Art. 9(3), 10(1)–(2), 12(1) (logging), 28 (evidence retention); NIS2 Art.
21(2)(b); ISO 42001 A.6.2.6, A.6.2.7; EU AI Act Art. 12 (record-keeping),
26(5) (deployer monitoring).

## 1. Sources → sink

All logs converge on the Log Analytics workspace `{baseName}-logs` created
by `../infra/main.bicep`; App Insights `{baseName}-appi` is
workspace-based, so its tables are queryable in the workspace next to the
platform logs (one scope for every alert rule).

| Source | What it carries | Table(s) in `{baseName}-logs` | How it gets there |
|---|---|---|---|
| Foundry tracing (`app-insights` connection in `main.bicep`) | every agent run: spans per thread/run/tool call, `gen_ai.*` attributes (agent, model, tokens, tool name, inputs when content recording is on) | `AppDependencies`, `AppTraces`, `AppExceptions` | connection created by Bicep; tracing enabled on the project |
| Foundry account metrics | `AzureOpenAIRequests` (by `ModelDeploymentName`, `StatusCode`), `TokenTransaction`, `ProcessedPromptTokens`, `GeneratedTokens` | Azure Monitor metrics (not a table) | platform |
| Foundry account diagnostics | data-plane audit / request-response (agent, connection, vector-store CRUD; caller identity) | `AzureDiagnostics` (`MICROSOFT.COGNITIVESERVICES`) | diagnostic setting — delta D-OPS-B2 |
| Logic Apps Standard `{baseName}-la` | run/trigger/action lifecycle for every pipeline: `Human_approval_gate`, `Notify_verifier_fail`, `Render_report_file`, `Upload_and_share`… | `LogicAppWorkflowRuntime` (category `WorkflowRuntime`); App Insights of the app (`AppRequests`) | diagnostic setting — D-OPS-B2; App Insights connection string app setting |
| Delivery Function `{baseName}-fn-delivery` | `render`, `ensure_folder`, `upload` requests, exceptions, Graph status codes | `AppRequests`, `AppTraces`, `FunctionAppLogs` | App Insights connection string; diagnostic setting |
| Key Vault `{baseName}-kv` | `SecretGet` / `SecretList` with caller identity | `AzureDiagnostics` (`AuditEvent`) | diagnostic setting — D-OPS-B2 |
| Azure Activity Log | every ARM write in `rg-infosec-foundry` with caller | `AzureActivity` | subscription diagnostic setting (landing-zone team) |
| Entra ID sign-in and PIM audit | PIM activations, CA outcomes for the `sg-infosec-foundry-*` groups | `SigninLogs`, `AuditLogs` (tenant workspace, read via `{group:iam-admins}` report) | tenant diagnostic setting — not this RG |
| Microsoft Graph / SharePoint audit | file created/moved/shared under `Reports/`, `Templates/`, `Governance/`; sharing-link scope | Purview audit (`OfficeActivity` if the Sentinel M365 connector is attached) | M365 admin / `{group:spo-admins}`; monthly export to `Governance/Operations/` when no connector exists |
| Approval flow (Power Automate / Function behind `approvalWebhookUrl`) | `kind, reportType, tier, ruleId, correlationId, requestedBy, approver, decision, timestamp` | SharePoint list `{list:ApprovalDecisions}` (`../team/approval-policy.json` `record`) | the flow writes before the callback |
| Cost Management | daily cost by resource | Cost analysis (export to the storage account optional) | subscription |

Column mapping when a query is opened in the App Insights blade instead
of the workspace: `AppDependencies.Properties` = `dependencies.customDimensions`,
`DurationMs` = `duration`, `TimeGenerated` = `timestamp`, `Name` = `name`.

## 2. Retention and residency

| Store | Setting | Value | Why |
|---|---|---|---|
| `{baseName}-logs` | `retentionInDays` | `main.bicep` ships 90; **set 365** (delta D-OPS-B3) | DORA Art. 28 evidence ≥ 1 year (`DATA_PROTECTION_GUARDRAILS.md` §4); approval and egress evidence |
| `AppDependencies` etc. | inherit workspace | 365 | same |
| `{list:ApprovalDecisions}` | SharePoint retention label | ≥ 1 year, ISMS record schedule | `TEAM_MODEL.md` §12.1 |
| Logic Apps run history | platform (90 days, Standard) | plus `LogicAppWorkflowRuntime` in the workspace for the long tail | — |
| Region | all monitoring resources | same EU region as the platform (`AZURE_LOCATION`) | residency §3 of the guardrails |

Trace content: tool inputs and message text are recorded only when content
recording is enabled on the tracing exporter. It is **on** for this
platform because the egress detector needs the Bing query text; the traces
therefore contain assessment excerpts and are classified Confidential —
readers are the owner and `sg-infosec-foundry-readers` only (ISO 27001:2022
A.8.15 "logs protected"; A.5.34 privacy; GDPR Art. 5(1)(c)).

## 3. Standard queries (`kql/`)

| File | Question | Scope table | Used by |
|---|---|---|---|
| `egress-detection.kql` | Did any Bing query carry an internal marker, assessment id or employee name? | `AppDependencies` | alert `egress-internal-marker`; RUNBOOK H4, FM-03 |
| `verifier-fail-rate.kql` | FAIL/PASS split per pipeline over 24 h (from `Notify_verifier_fail` vs `Human_approval_gate` action completions) | `LogicAppWorkflowRuntime` | alert `verifier-fail-rate`; RUNBOOK H3, M1; MODEL_ROUTING rule 7 |
| `latency-and-tokens.kql` | Runs, p50/p95 latency, tokens and estimated cost per agent/model | `AppDependencies` | alert `latency-and-token-budget`; RUNBOOK H5, M2 |
| `approval-sla.kql` | Gates pending > 48 h or expired (`TimedOut`) | `LogicAppWorkflowRuntime` | alert `approval-sla`; RUNBOOK FM-10; SUPPORT_MODEL SLO |
| `../infra/kql/agent-drift.kql` | (1) an agent definition changed by an identity other than the deploy SP; (2) **`agent_version_not_in_manifest`** — a run whose `gen_ai.agent.version` is not the version the last deploy promoted | `AzureDiagnostics`, `AppDependencies` + `AppEvents` | alerts `agent-drift`, `agent_version_not_in_manifest` (`../infra/monitoring.bicep`); RUNBOOK FM-19 |

**Version-drift baseline (finding C19).** `agent_version_not_in_manifest`
compares the serving version against `build/agent-versions.json` — the ledger
`scripts/_foundry_runtime.py` writes on every deploy — **not** against
`build/manifest.json`, which holds no versions. `deploy.sh` publishes the
ledger to App Insights as the custom event `deploy_manifest`. Nightly drift
Routine: **restore the release pipeline's `build/agent-versions.json` before
running `python3 scripts/verify_deployment.py`** — `build/` is git-ignored, so
without the restored ledger the version comparison is silently skipped and the
drift check degrades to a name-only check.

Each file ends with a `where` that keeps only breaching rows (so the alert
fires on *rows > 0*); remove that line for the dashboard view. Thresholds
are `let` constants at the top of each file and mirrored as
`alerts.bicep` parameters where a metric alert exists; changing one is a
Low-risk change (`CHANGE_MANAGEMENT.md` §5).

## 4. Alert catalogue (`alerts.bicep`)

Action groups: `infosec-foundry-ag-owner` (e-mail to
`{email:sg-infosec-foundry-owner}` + optional Teams webhook of
`{teams:infosec-assurance-platform}`); `infosec-foundry-ag-soc` (optional
webhook to `{group:soc-oncall}`, severity 1 only). Severity 1 = RUNBOOK P1
handling; 2 = P2; 3 = P3.

| Rule name | Signal | Query / metric | Eval / window | Threshold | Sev | Notifies | Runbook | Control |
|---|---|---|---|---|---|---|---|---|
| `egress-internal-marker` | internal marker in a Bing query | `kql/egress-detection.kql` | 15 min / 1 h | rows > 0 | 1 | owner + SOC | FM-03 | A.8.12, A.8.16; DORA 9(3)(b); ISO 42001 A.6.2.6 |
| `verifier-fail-rate` | FAIL rate > 30 % with ≥ 5 verdicts | `kql/verifier-fail-rate.kql` | 1 h / 24 h | rows > 0 | 2 | owner | FM-08 | ISO 42001 A.6.2.6, A.8.4; EU AI Act 26(5) |
| `latency-and-token-budget` | p95 > 5 min or agent > 5 M tokens/day | `kql/latency-and-tokens.kql` | 1 h / 24 h | rows > 0 | 3 | owner | FM-06, FM-07 | A.8.6; DORA 9(2) |
| `approval-sla` | gate pending > 48 h or expired | `kql/approval-sla.kql` | 1 h / 7 d | rows > 0 | 3 | owner | FM-10 | EU AI Act 14; A.5.36 |
| `pipeline-run-failed` | Logic Apps run `Failed`/`TimedOut`/`Cancelled` | inline (`LogicAppWorkflowRuntime`) | 15 min / 1 h | rows > 0 | 2 | owner | FM-19, FM-21 | A.8.16; DORA 10(1) |
| `delivery-function-5xx` | `render`/`ensure_folder`/`upload` 5xx | inline (`AppRequests`) | 15 min / 1 h | rows > 0 | 2 | owner | FM-11, FM-12 | A.8.16 |
| `breakglass_window_write` | ARM write in the RG by a caller other than the deploy SP | inline (`AzureActivity`) | 15 min / 1 h | rows > 0 | 1 | owner + SOC | BREAK_GLASS §2 step 6; CHANGE_MANAGEMENT §8 | A.8.2, A.8.15; DORA 9(4)(c) |
| `agent_modified_by_non_deploy_identity` | agent / connection / vector-store write on the Foundry data plane by a non-deploy identity | inline (`AzureDiagnostics`, Cognitive Services audit) | 15 min / 1 h | rows > 0 | 1 | owner + SOC | BREAK_GLASS §4; CHANGE_MANAGEMENT §1 | A.8.9, A.8.32 |
| `keyvault-human-secret-read` | `SecretGet`/`SecretList` with a UPN claim | inline (`AzureDiagnostics` `AuditEvent`) | 15 min / 1 h | rows > 0 | 2 | owner | BREAK_GLASS §2 step 7; FM-25 | A.5.17, A.8.2 |
| `model-throttling-429` | `AzureOpenAIRequests` with `StatusCode=429` | metric on `{baseName}-aif` | 15 min / 1 h | total > 20 | 3 | owner | FM-05 | A.8.6 |
| `daily-token-budget` | `TokenTransaction` over 24 h | metric on `{baseName}-aif` | 1 h / 1 d | total > `dailyTokenBudget` (20 M) | 3 | owner | FM-07, M2 | MODEL_ROUTING rule 7 |

Expected-noise rules: `breakglass_window_write` also fires on every
legitimate PIM window of the owner — that is intended; the alert is
reconciled against PIM activations (RUNBOOK H7) so that an ARM write
*without* a matching activation is the finding. `skipQueryValidation` is
set because `LogicAppWorkflowRuntime` and the Cognitive Services audit
columns exist only after the diagnostic settings of D-OPS-B2 have shipped
data; the owner validates each inline query at first deployment (RUNBOOK
H9) and after each SDK bump and records the verified column
names in the ticket.

Not alerted, reviewed instead: cost trend (weekly W7), memory-store
contents (W5), Copilot publication age (FM-30), SharePoint sharing scope
(monthly Purview export, `FM-23` if a non-organisation link appears).

## 5. Dashboard (Azure Workbook `{baseName}-ops`, owner-maintained)

| Section | Tiles | Query |
|---|---|---|
| Health | runs/day per agent; success rate; 429 share; Function p95 | `latency-and-tokens.kql` (no final `where`), account metrics, `AppRequests` |
| Quality | verifier PASS rate per pipeline (7-day trend); approvals per tier; rework count | `verifier-fail-rate.kql`; `{list:ApprovalDecisions}` export |
| Oversight | pending gates with age; expired gates; approver ≠ requester check (count of rows where equal must be 0) | `approval-sla.kql`; decisions list |
| Data protection | egress hits (should be flat zero); content-filter blocks; tool calls per connection | `egress-detection.kql`; `AppDependencies` by `gen_ai.tool.name` |
| Privileged access | ARM writes by caller; PIM activations (from the IAM report); KV human reads | `AzureActivity`; `AzureDiagnostics` |
| Cost | tokens and estimated EUR per agent, per tier; month-to-date vs forecast | `latency-and-tokens.kql`; Cost Management |

The workbook is version-controlled like everything else (A.8.9):
`operations/workbook.json` is the importable Azure Workbook definition
(one section per row above, each tile bound to the same `kql/*.kql` text
as the alert rules; workspace resource id supplied as the `Workspace`
parameter at import). Re-export it into the repo on each change (Low-risk
change, `CHANGE_MANAGEMENT.md` §1).

## 6. Evidence produced for audits

| Evidence | Produced by | Filed under |
|---|---|---|
| Daily health-check log | RUNBOOK H1–H7 (manual or the workbook's daily snapshot) | `Governance/Operations/{yyyy}-{mm}/` |
| Egress detector results (zero-row proof) | `egress-detection.kql` weekly export | same |
| Verifier and approval statistics | M1 evaluation | same |
| Alert history | Azure Monitor alert export, quarterly | `Governance/AccessReviews/{yyyy}-Q{n}/` (with the access review) |
| Break-glass reconciliations | RUNBOOK H7 + BREAK_GLASS §2 step 6 | `Governance/AccessReviews/breakglass-{ticket}.md` |

## 7. Shared deltas needed by this layer (not applied here)

| Id | Target | Location | Literal text |
|---|---|---|---|
| D-OPS-B1 | `infra/main.bicep` | after the `teamRbac` module (delta D-B3 of `team/TEAM_MODEL.md`) | `@description('Deploy the operations alert rules (operations/alerts.bicep)') param deployAlerts bool = false` / `@description('Owner group distribution address for alerts') param ownerAlertEmail string = '{email:sg-infosec-foundry-owner}'` / `module opsAlerts '../operations/alerts.bicep' = if (deployAlerts) { name: 'ops-alerts' params: { logAnalyticsName: logAnalytics.name foundryAccountName: foundry.name location: location ownerAlertEmail: ownerAlertEmail deployerPrincipalId: deployerPrincipalId } }` |
| D-OPS-B2 | `infra/main.bicep` | before outputs | `resource foundryDiag 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = { name: 'to-log-analytics' scope: foundry properties: { workspaceId: logAnalytics.id logs: [ { categoryGroup: 'audit', enabled: true } { categoryGroup: 'allLogs', enabled: true } ] metrics: [ { category: 'AllMetrics', enabled: true } ] } }` and the same `diagnosticSettings` block scoped to `keyVault` (D-B2), to the Logic Apps Standard app `{baseName}-la` (`logs: [ { category: 'WorkflowRuntime', enabled: true } ]`) and to the delivery Function `{baseName}-fn-delivery` (`logs: [ { category: 'FunctionAppLogs', enabled: true } ]`) once those resources are declared in Bicep |
| D-OPS-B3 | `infra/main.bicep` | `logAnalytics.properties` | `retentionInDays: 365 // DORA Art. 28 evidence; DATA_PROTECTION_GUARDRAILS.md §4` |
| D-OPS-B4 | `infra/main.parameters.json` | parameters | `"deployAlerts": { "value": false }, "ownerAlertEmail": { "value": "{email:sg-infosec-foundry-owner}" }` |
| D-OPS-E1 | `setup/.env.example` | end | `# --- Operations (operations/MONITORING.md) ---` / `LOG_ANALYTICS_WORKSPACE_NAME=<baseName>-logs` / `FOUNDRY_ACCOUNT_NAME=<baseName>-aif` / `OWNER_ALERT_EMAIL={email:sg-infosec-foundry-owner}` / `TEAMS_PLATFORM_CHANNEL_WEBHOOK_SECRET_NAME=teams-platform-webhook   # Key Vault secret NAME only` / `SOC_ONCALL_WEBHOOK_SECRET_NAME=soc-oncall-webhook             # Key Vault secret NAME only` / `DAILY_TOKEN_BUDGET=20000000` |
| D-OPS-D1 | `deploy.sh` | after step `[6d/7]` (delta D-D1 of the team model) | `echo "==> [6e/7] Monitoring rules (what-if only; apply from the pipeline)"` / `az deployment group what-if -g "$AZURE_RESOURCE_GROUP" -f ../operations/alerts.bicep -p logAnalyticsName="${LOG_ANALYTICS_WORKSPACE_NAME:-infosecfoundry-logs}" foundryAccountName="${FOUNDRY_ACCOUNT_NAME:-infosecfoundry-aif}" ownerAlertEmail="${OWNER_ALERT_EMAIL:?set OWNER_ALERT_EMAIL in setup/.env}" \|\| echo "note: alert what-if skipped (no az session or RG) - see operations/MONITORING.md §4"` |
| D-OPS-R1 | `README.md` | folder layout tree, under `operations/` | `│   ├── RUNBOOK.md, SUPPORT_MODEL.md, CHANGE_MANAGEMENT.md, MONITORING.md   ← day-2 operation` / `│   ├── kql/                   ← egress, verifier fail rate, latency+tokens, approval SLA` / `│   └── alerts.bicep           ← scheduled-query + metric alerts to the owner group` |
| D-OPS-R2 | `README.md` | "Governance note" paragraph, end | `Day-2 operation (health checks, failure modes, severities), support tiers and SLOs, PR-based change control and the alert catalogue are in operations/ (RUNBOOK.md, SUPPORT_MODEL.md, CHANGE_MANAGEMENT.md, MONITORING.md).` |
| D-OPS-Q1 | `REQUIREMENTS.md` | after delta D-Q1 of the team model | `Operating the delivered systems — health checks, failure modes per pipeline, support tiers and SLOs, change control for prompts/registry/templates/tiers/infra, alerts (egress, verifier FAIL rate, latency/tokens, approval SLA): operations/RUNBOOK.md, SUPPORT_MODEL.md, CHANGE_MANAGEMENT.md, MONITORING.md.` |
| D-OPS-A1 | `ARCHITECTURE.md` | "Guardrails and observability" table, Observability row | append ` — alert catalogue and queries: operations/MONITORING.md; failure handling: operations/RUNBOOK.md` |
| D-OPS-P1 | `governance/DATA_PROTECTION_GUARDRAILS.md` | §1 Detective layer cell | append ` Implemented by operations/kql/egress-detection.kql and the \`egress-internal-marker\` rule in operations/alerts.bicep (severity 1, owner + SOC); response: operations/RUNBOOK.md FM-03.` |
| D-OPS-P2 | `governance/DATA_PROTECTION_GUARDRAILS.md` | §4 Auditability, after "≥ 1 year" | ` (delta D-OPS-B3 sets \`retentionInDays: 365\`; tables and evidence layout in operations/MONITORING.md §1–§2, §6).` |
| D-OPS-M1 | `governance/MODEL_ROUTING.md` | rule 7, after "Review monthly" | ` using operations/kql/latency-and-tokens.kql and verifier-fail-rate.kql (RUNBOOK.md M2); a tier move is a change under operations/CHANGE_MANAGEMENT.md §1.` |
| D-OPS-H1 | `governance/HUMAN_APPROVAL.md` | end of "Verifying the control" | `Operational evidence that the gates are exercised: operations/kql/approval-sla.kql (pending/expired gates) and the \`approval-sla\` alert in operations/alerts.bicep; RUNBOOK.md FM-10 and FM-20 (gate integrity failures are P1).` |
| D-OPS-W1 | `workflows/README.md` | end of "Deployment" | `4. Enable diagnostic settings (category \`WorkflowRuntime\`) to the platform Log Analytics workspace: the operations alerts (operations/MONITORING.md §4) read \`LogicAppWorkflowRuntime\` and key on the action names \`Human_approval_gate\`, \`Wait_for_approval_*\` and \`Notify_verifier_fail\` — keep those names when editing definitions.` |
| D-OPS-F1 | `functions/delivery/README.md` | end | `Monitoring: connect the app to \`{baseName}-appi\`; the \`delivery-function-5xx\` alert (operations/alerts.bicep) keys on \`AppRoleName\` containing \`fn-delivery\` — keep the app name \`{baseName}-fn-delivery\`.` |
| D-OPS-T1 | `team/TEAM_MODEL.md` | §3 F7, F9, F12 "Derived requirement" cells | **applied** (same folder set): `→ operations/RUNBOOK.md` (F7), `→ operations/MONITORING.md §5, RUNBOOK.md M1–M2` (F9), `→ operations/SUPPORT_MODEL.md` (F12) |
| D-OPS-BG1 | `operations/access-governance/BREAK_GLASS.md` | §4 table | **applied**: `(operations/alerts.bicep; operations/MONITORING.md §4)`; group names per delta D-OP1 of the team model (also applied) |
