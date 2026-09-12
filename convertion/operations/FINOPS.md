# FinOps — Cost Model, Token Economics, Capacity, Budgets and the Monthly Review

What the platform costs, where every euro goes, how much a deliverable
costs in tokens per tier, how much throughput the model deployments must
carry, which budgets and anomaly alerts fence the spend, and the monthly
review the owner runs. Extends `RUNBOOK.md` W7 / M2, `MONITORING.md` §4
(`daily-token-budget`, `latency-and-token-budget`, `model-throttling-429`)
and `../governance/MODEL_ROUTING.md` rule 7; the tier-tuning procedure
itself is `TOKEN_ECONOMY_PLAYBOOK.md`, the quality floor that bounds every
economy decision is `evaluation/EVALUATION.md`.

Ownership: the accountable owner `{upn:francisco.gomes}` runs FinOps under
his standing `Reader` + `Log Analytics Reader` (`../team/TEAM_MODEL.md` §5
L6) and Cost Management *reader* on the RG — no write role is needed for
any activity here; users hold no monitoring or cost role (flow F9). A tier,
capacity or budget change is a platform change (Tier C, deputy review when
the owner authored it — `CHANGE_MANAGEMENT.md` §1 "Model tier / capacity").

Control (whole document): ISO 27001:2022 A.8.6 (capacity management), A.5.9
(inventory of assets and their owners), A.8.16 (monitoring); DORA Art. 9(2)
(ICT capacity and performance), Art. 6(8)/(9) (resources for the ICT risk
framework, proportionality); ISO 42001 A.4.2–A.4.4 (resources for AI
systems), A.6.2.6 (operation and monitoring); EU AI Act Art. 26(5)
(deployer monitoring). All figures are **planning placeholders** in EUR at
list price — replace with Cost analysis actuals at the first M2 review and
keep the KQL price map (`kql/latency-and-tokens.kql`) aligned.

## 1. Cost model per component

Resource names are those `../infra/main.bicep` creates (`{baseName}` =
`infosecfoundry` by default). "Driver" is the unit Azure bills; "lever" is
what the owner can change without weakening an invariant.

| # | Component | Resource | Billing driver | Planning baseline / month (dev → prod) | Lever | Bicep switch |
|---|---|---|---|---|---|---|
| C1 | Model tiers `light` / `chat` / `reasoning` | `{baseName}-aif` deployments (`DataZoneStandard`, EU Data Zone) | tokens in/out per model | €50 → €150 (see §2; volume-driven) | tier tuning, RAG sizing, caching, batching (playbook) | `modelCapacity`, `reasoningModelCapacity`, `lightModelCapacity` |
| C2 | Grounding with Bing (sanitised public queries only) | `bing-grounding` connection | per 1 000 transactions | €10 → €25 | query dedupe in DeepSearch, watchlist size | `enableWebSearch` |
| C3 | Vector stores + files (35 agent stores, combined advisory store, `vs-assurance-memory`) | Foundry file storage | GB × days beyond the free tier | €5 → €10 | memory retention (`TEAM_MODEL.md` §13), upload cache (`_azure_helpers.UploadCache`) | — |
| C4 | code_interpreter sessions (advisory file generation, DOCX/XLSX in-thread) | Foundry | per session | €10 → €20 | render in the delivery Function instead for pipelines (already the design) | — |
| C5 | Document Intelligence (OCR for scanned PDFs) | `{baseName}-docint` | per page | €2 → €10 | OCR only when text extraction is empty | `enableDocumentIntelligence` |
| C6 | Log Analytics + App Insights (workspace-based) | `{baseName}-logs`, `{baseName}-appi` | GB ingested/day; retention 365 d (`MONITORING.md` §2) | €120 → €250 | sampling of `AppTraces` (never of `AppDependencies` — the egress detector needs them); Basic-logs tier for `FunctionAppLogs` | `logRetentionDays` |
| C7 | Logic Apps Standard (12 pipeline instances + 14 workflow definitions) | `{baseName}-la` (WS1) | plan hours + storage | €160 → €180 | one plan for all workflows (already); stop `mailbox-intake` / `morning-brief` if unused | `enableLogicApps` |
| C8 | Delivery Function (Flex Consumption) | `{baseName}-fn-delivery` | executions + GB-s | €10 → €30 | — | `enableDelivery` |
| C9 | Container Registry (renderer image) | `{baseName}acr` (Basic) | per day | €5 | — | with C8 |
| C10 | Storage (deliverables, Function/Logic Apps state, ZRS) | `{baseName}st…` | GB + transactions | €5 → €10 | lifecycle rule to cool tier after 90 d | `storageSku` |
| C11 | Key Vault | `{baseName}-kv` | operations | €1 | — | — |
| C12 | Hosted MCP server (optional) | Container Apps (`mcp-server.bicep`) | vCPU-s + memory | €0 → €40 | keep local MCP (own `az login`) unless Copilot/hosted access is needed | `enableMcpHosting` |
| C13 | Private networking (prod profile) | VNet, ~8 private endpoints, private DNS | per endpoint-hour + data | €0 → €70 | prod only (`main.parameters.prod.json`) | `enablePrivateNetworking` |
| C14 | Speech (WhisperX replacement) | `{baseName}-speech` | audio hours | €0 (off) | on-demand only | `enableSpeech` |
| C15 | Static Web App (report viewer, optional) | `static-web-app.bicep` | Standard plan | €0 → €9 | — | `enableStaticWebApp` |
| C16 | Alerts, budgets, action groups | `alerts.bicep`, `cost.bicep`, this folder | per rule-month, e-mail free | €5 | — | `enableMonitoring`, `enableBudget` |
| | **Total (planning)** | | | **≈ €380 dev → ≈ €830 prod** | budget `monthlyBudget` = 1500 in `main.bicep` leaves ~45 % headroom for campaigns (bulk DeepSearch of a supplier portfolio) | |

Reading: the **fixed platform (C6–C13) is 3–5× the token spend** at the
five-user volume of §2. Token economy (`MODEL_ROUTING.md`) matters for
scale and for latency under the TPM caps, but the euro levers for this team
are ingestion volume (C6), the Logic Apps plan (C7) and the optional
components (C12–C15). Never trade an invariant for cost: content recording
in tracing, 365-day retention, the verifier pass and EU Data Zone SKUs are
not levers (`DATA_PROTECTION_GUARDRAILS.md` §4; DORA Art. 28).

## 2. Token cost per deliverable, by tier

Price placeholders (EUR per 1 M tokens, same map as
`kql/latency-and-tokens.kql`): `gpt-4o-mini` 0.15 in / 0.60 out; `gpt-4o`
2.50 / 10.00; `o3-mini` 1.10 / 4.40 (reasoning tokens bill as output).
Every pipeline deliverable = producer run + `output-verifier` pass
(reasoning tier, `../scripts/create_orchestrator.py`) + orchestrator hop
when invoked conversationally. Volumes are the five-user planning
assumption; the actual counts come from `{list:ApprovalDecisions}` and
`kql/latency-and-tokens.kql` at M2.

| Req | Pipeline / system | Agent (tier of record, `../integrations/registry.json`) | Producer tokens in / out | Verifier in / out | € per deliverable | Volume / month | € / month |
|---|---|---|---|---|---|---|---|
| a | `deepsearch-report`, `ai-deepsearch-report`, `scheduled-deepsearch` | `deepsearch-protocol` (reasoning) — multi-tool OSINT, iterative | 120 k / 60 k | 25 k / 2 k | ≈ 0.45 | 20 | 9.0 |
| b | `dpia-dpo-report` | `dpia` (chat) — chunked OT PDF → fixed DOCX contract | 40 k / 8 k | 15 k / 1 k | ≈ 0.20 | 10 | 2.0 |
| c | `cyber-forum-pptx` + `cyber-forum-brief` | `ciso-reporting` (chat) + `cyber-forum` (reasoning) | 45 k / 6 k + 30 k / 8 k | 2 × 15 k / 1 k | ≈ 0.30 | 10 | 3.0 |
| d | `ciso-global-pptx`, `ciso-exec-summary` | `ciso-global-report` (reasoning; CMDB grounding) / `ciso-executive-summary` (chat) | 60 k / 20 k | 15 k / 1 k | ≈ 0.20 | 10 | 2.0 |
| d2 | `tpa-evidence-analysis` | `tpa-evidence-analyzer` (reasoning) — per-file chunked extraction | 250 k / 40 k (≈ 10 files) | 20 k / 2 k | ≈ 0.50 (+ ≈ 0.04 per extra file) | 8 | 4.0 |
| e | `soc-report-summary` | `soc-report-analyzer` (reasoning) — long report, bounded chunks | 120 k / 20 k | 15 k / 1 k | ≈ 0.27 | 10 | 2.7 |
| f | `pentest-report-summary` | `pentest-report-analyzer` (reasoning) | 100 k / 20 k | 15 k / 1 k | ≈ 0.25 | 6 | 1.5 |
| g | framework advisors (`iso27001`, `iso42001`, `dora`, `nis2`, `eu-ai-act`) — per turn | reasoning (pinned) — RAG chunks + persona + memory | 12 k / 4 k | none (in-thread) | ≈ 0.03 | 400 turns | 12.0 |
| h | `infosec-assurance-advisor`, `tpsrca-assessment-engine`, `enx-tprm-control-center` — per turn | reasoning (pinned) | 15 k / 5 k | none | ≈ 0.04 | 200 turns | 8.0 |
| i | `infosec-assurance-orchestrator` hop (route + hand-off) | reasoning | 6 k / 1 k | none | ≈ 0.01 | 400 hops | 4.0 |
| j | `template-manager` proposal (analyse / preview) | chat | 20 k / 5 k | 15 k / 1 k (template-update-approval) | ≈ 0.10 | 4 | 0.4 |
| — | light-tier bookkeeping (`xlsx`, routing hand-offs, folder/file steps) | `gpt-4o-mini` | 5 k / 1 k | none | < 0.01 | 300 | 0.6 |
| | **Tokens, planning total** | | | | | | **≈ €49** |

Unit-cost rules the owner applies at M2: (1) a deliverable that costs more
than 2× its row above for two consecutive months is a `FM-07` finding
(`RUNBOOK.md`) — check for tool loops, oversized RAG results or
unchunked inputs before touching the tier; (2) the advisory rows g/h/i are
**never** moved down a tier (`MODEL_ROUTING.md` advisory pin) — their
economy comes from RAG sizing and single-pass contracts only; (3) a report
agent is a downgrade candidate only after the accuracy-floor test
(`TOKEN_ECONOMY_PLAYBOOK.md` §7, `evaluation/EVALUATION.md` gate G1).

## 3. Capacity and throughput (TPM)

Deployments are `DataZoneStandard` pay-as-you-go with a TPM cap set in
`main.bicep`; RPM is derived by the platform (≈ 6 RPM per 1 k TPM for the
`gpt-4o` family, ≈ 1 RPM per 1 k TPM for `o`-series — verify in the
portal for the deployed versions). Provisioned throughput (PTU) is not
justified at this volume; revisit above ~50 pipeline runs/day.

| Tier | Deployment (`main.bicep` param) | Default cap | Peak consumer | Peak need | Verdict |
|---|---|---|---|---|---|
| `light` | `lightModelCapacity` | 100 k TPM | bookkeeping / routing hand-offs, ≤ 10 concurrent | < 20 k TPM | oversized; keep (no cost when idle) |
| `chat` | `modelCapacity` | 50 k TPM | b/c/d report generation, 2–3 concurrent runs of ~45 k tokens over ~3 min | ≈ 45 k TPM | adequate; 429s appear only when a user batches OT PDFs — queue them |
| `reasoning` | `reasoningModelCapacity` | 30 k TPM | DeepSearch (120 k tokens over ~5 min ≈ 24 k TPM) **plus** the verifier **plus** advisory turns of five users | ≈ 55 k TPM at campaign peak | **raise to 60 k in prod** (`main.parameters.prod.json`); until then serialise DeepSearch runs and keep `scheduled-deepsearch` on its Monday off-peak slot (`../workflows/scheduled-deepsearch.json`) |

Throttling is handled, not hidden: the Logic Apps HTTP actions carry a
`retryPolicy` (exponential, `../workflows/*.json`), scripts use
`_azure_helpers.retry`, and `model-throttling-429` (`alerts.bicep`,
severity 3, > 20 per 15 min) tells the owner when the cap — not a bug — is
the bottleneck (`RUNBOOK.md` FM-05). Quota is regional: a capacity increase
is a `what-if` + PR on `main.bicep` (Tier C, Medium risk) and may need a
quota request through `{group:azure-platform}`. Control: ISO 27001:2022
A.8.6; DORA Art. 9(2), 11(1) (continuity under load).

## 4. Budgets and anomaly alerts

Layered fences — each fires to the owner action group
`infosec-foundry-ag-owner` (`MONITORING.md` §4); none of them stops a
running pipeline or changes any resource (alerting is read-only; a
*response* is a human decision, `RUNBOOK.md` FM-06/FM-07).

| Fence | Where | Scope / filter | Thresholds | Notifies | Response |
|---|---|---|---|---|---|
| RG budget | `../infra/cost.bicep` (module `budget` in `main.bicep`, `monthlyBudget` = 1500) | whole RG | 50 % / 80 % actual, 100 % forecast | owner group + action group | W7 explanation; freeze optional components |
| Token-spend budget | `cost-budget.bicep` → `{baseName}-budget-models` | `ResourceId` = `{baseName}-aif` | 80 % actual, 100 % actual, 100 % forecast of `modelBudgetAmount` (default 300) | owner | M2 out of cycle; playbook §1 loop |
| Observability budget | `cost-budget.bicep` → `{baseName}-budget-observability` | `ResourceId` ∈ {`{baseName}-logs`, `{baseName}-appi`} | 80 % / 100 % actual of `observabilityBudgetAmount` (default 300) | owner | check ingestion by table (`Usage` table); sample `AppTraces`; never cut retention |
| Daily token volume | `alerts.bicep` `daily-token-budget` (`dailyTokenBudget` 20 M) | `TokenTransaction` on `{baseName}-aif` | > 20 M / day | owner | FM-07 |
| Per-agent token / latency | `alerts.bicep` `latency-and-token-budget` (`kql/latency-and-tokens.kql`: 5 M tokens / agent / day, p95 5 min) | per agent/model | rows > 0 | owner | FM-06 / FM-07 |
| Throttling | `alerts.bicep` `model-throttling-429` | `{baseName}-aif` | > 20 per 15 min | owner | FM-05; §3 |
| Cost anomaly (ML-based) | Cost Management anomaly alert — **subscription scope only**; requested from `{group:azure-platform}` (§6 delta D-FIN-S1) | subscription, filtered on the RG | Azure's anomaly model, daily | owner mailbox `{email:sg-infosec-foundry-owner}` | W7 |
| Weekly cost digest | `cost-budget.bicep` `{baseName}-cost-weekly` (scheduled action, optional `enableWeeklyReport`) | RG, daily-costs view | every Monday 07:00 UTC | owner group | W7 input |

Deploy `cost-budget.bicep` after `main.bicep` (needs the action group id
from `monitoring.bicep` and the resource names), as a module (delta
D-FIN-B1) or standalone; `az deployment group what-if` first
(`CHANGE_MANAGEMENT.md` §3 step 3). Control: ISO 27001:2022 A.8.6, A.8.16;
DORA Art. 9(2), 10(1) (detection of anomalous activity); ISO 42001 A.6.2.6.

## 5. Cost allocation and tagging

Every resource in `rg-infosec-foundry` carries the tags below (delta
D-FIN-B2 adds them to `main.bicep`); Cost analysis groups by `costCenter`
and `requirement`, and the token spend is attributed per agent by
`kql/latency-and-tokens.kql` (agents are not Azure resources, so the KQL
estimate is the per-agent view).

| Tag | Value | Used for |
|---|---|---|
| `owner` | `{email:sg-infosec-foundry-owner}` (group mailbox, never a person) | budget contacts; A.5.9 asset ownership |
| `costCenter` | `{costcenter:infosec-assurance}` | chargeback / showback |
| `workload` | `infosec-foundry` | Cost analysis filter |
| `environment` | `dev` / `prod` (`environmentName`) | dev vs prod split |
| `dataClassification` | `confidential` | pairs with `DATA_PROTECTION_GUARDRAILS.md` |
| `requirement` | `a-j` | traceability to `../REQUIREMENTS.md` |

## 6. Monthly owner review (RUNBOOK M2, expanded)

Run in the first week of the month with M1 (`evaluation/EVALUATION.md`
§6) — quality and cost are reviewed together so that a saving never lands
without its accuracy evidence. Output: `Governance/Operations/{yyyy}-{mm}/finops.md`
(template below) filed next to `evaluation.md`; decisions become Tier C
tickets, never portal edits.

| # | Step | Input | Decision / output |
|---|---|---|---|
| 1 | Actuals vs plan | Cost analysis (RG, by tag, by resource) vs §1 table | update §1 baselines when actuals differ > 20 % two months running |
| 2 | Token spend per agent / per deliverable | `kql/latency-and-tokens.kql` (full table), `kql/tokens-per-agent.kql` (`../infra/kql/`), decisions count from `{list:ApprovalDecisions}` | € per deliverable vs §2; agents > 2× → FM-07 investigation |
| 3 | Throughput | 429 count (`model-throttling-429` history), p95 latency | capacity change proposal (§3) |
| 4 | Tier candidates | `kql/verifier-fail-rate.kql` (first-pass PASS rate) + step 2 | down-candidates (non-advisory, PASS ≥ 95 %, cost material) → playbook §1; up-candidates (loops, FAIL spikes) |
| 5 | Ingestion | `Usage` table by data type; retention unchanged | sampling proposal for `AppTraces` / `FunctionAppLogs` only |
| 6 | Optional components | C12–C15 usage (MCP requests, Static Web App hits, Speech hours) | switch off unused (`enable*` params, Low risk) |
| 7 | Budget check | §4 fences, forecast month-end | budget amount change (Tier C, Low risk) |
| 8 | Evidence | this table filled, KQL exports attached | `finops.md` filed; tickets opened; W7 baseline refreshed |

`finops.md` template:

```
# FinOps review {yyyy}-{mm} — owner {upn:francisco.gomes}
Actuals: € {n} (plan € {n}); by component: …; by tag: …
Tokens: {n} M in / {n} M out; € per deliverable: a {n} b {n} … ; outliers: …
Capacity: 429s {n}; p95 {n} s; change proposed: none | {ticket}
Tier candidates: down {agent} (PASS {n} %, saving € {n}/month, eval gate G1 planned {date}) | up {agent} (reason)
Ingestion: {n} GB/day; sampling: none | proposal {ticket}
Optional components switched: …
Budget: forecast € {n} / 1500; fences fired: …
Actions: {ticket list}; next review {date}
```

KPIs reported quarterly with the access review
(`access-governance/QUARTERLY_ACCESS_REVIEW.md`): € per approved
deliverable per pipeline (trend), token cost share of total (< 30 %
expected), 429s per 1 000 runs (< 5), budget fences fired (0 unexplained),
tier changes made vs rolled back.

## 7. Controls implemented here

| Control | Evidence |
|---|---|
| ISO 27001:2022 A.8.6 capacity management | §3 sizing, `model-throttling-429`, capacity change path |
| ISO 27001:2022 A.5.9, A.5.2 asset inventory and ownership | §1 component table, §5 `owner` tag, `TEAM_MODEL.md` §2 |
| ISO 27001:2022 A.8.16 monitoring; A.8.15 logging retained | §4 fences; retention not a lever (§1) |
| ISO 27001:2022 A.8.32 change management | every lever change is a Tier C PR (`CHANGE_MANAGEMENT.md`) |
| DORA Art. 9(2) capacity/performance; Art. 6(8) resources; Art. 10(1) anomaly detection | §3; §1; §4 anomaly alert |
| ISO 42001 A.4.2–A.4.4 resources; A.6.2.6 operation and monitoring; A.6.2.4 verification before change | §1–§3; §6; accuracy floor via `evaluation/EVALUATION.md` |
| EU AI Act Art. 26(5) deployer monitoring; Art. 9 lifecycle risk management | M1 + M2 joint review |

## 8. Shared deltas needed by this layer (not applied here)

| Id | Target | Location | Literal text |
|---|---|---|---|
| D-FIN-B1 | `infra/main.bicep` | after the `budget` module | `@description('Deploy the component budgets and weekly cost digest (operations/cost-budget.bicep)') param deployComponentBudgets bool = false` / `module componentBudgets '../operations/cost-budget.bicep' = if (deployComponentBudgets && enableMonitoring) { name: 'component-budgets' params: { baseName: baseName foundryAccountName: foundry.name logAnalyticsName: logAnalytics.name appInsightsName: appInsights.name startDate: budgetStartDate actionGroupId: monitoring!.outputs.actionGroupId contactEmails: [ownerEmail] } }` |
| D-FIN-B2 | `infra/main.bicep` | after the `environmentName` param | `@description('Cost-allocation tags applied to every resource (operations/FINOPS.md §5)') param resourceTags object = { owner: '{email:sg-infosec-foundry-owner}', costCenter: '{costcenter:infosec-assurance}', workload: 'infosec-foundry', environment: environmentName, dataClassification: 'confidential', requirement: 'a-j' }` and `tags: resourceTags` on every top-level resource and passed as `tags` to each module |
| D-FIN-B3 | `infra/main.parameters.prod.json` | parameters | `"reasoningModelCapacity": { "value": 60 }, "deployComponentBudgets": { "value": true }` |
| D-FIN-B4 | `infra/main.parameters.json` | parameters | `"deployComponentBudgets": { "value": false }` |
| D-FIN-E1 | `setup/.env.example` | after `DAILY_TOKEN_BUDGET` (delta D-OPS-E1) | `# --- FinOps (operations/FINOPS.md) ---` / `MODEL_BUDGET_EUR=300` / `OBSERVABILITY_BUDGET_EUR=300` / `PRICE_EUR_PER_1M_IN=gpt-4o-mini:0.15,gpt-4o:2.50,o3-mini:1.10   # placeholders, align with the price list` / `PRICE_EUR_PER_1M_OUT=gpt-4o-mini:0.60,gpt-4o:10.00,o3-mini:4.40` |
| D-FIN-D1 | `deploy.sh` | after step `[6e/7]` (delta D-OPS-D1) | `echo "==> [6f/7] Component budgets (what-if only; apply from the pipeline)"` / `az deployment group what-if -g "$AZURE_RESOURCE_GROUP" -f ../operations/cost-budget.bicep -p baseName="${BASE_NAME:-infosecfoundry}" foundryAccountName="${FOUNDRY_ACCOUNT_NAME:-infosecfoundry-aif}" logAnalyticsName="${LOG_ANALYTICS_WORKSPACE_NAME:-infosecfoundry-logs}" appInsightsName="${APP_INSIGHTS_NAME:-infosecfoundry-appi}" startDate="${BUDGET_START_DATE:-{yyyy-MM-01}}" actionGroupId="${ACTION_GROUP_ID:-}" \|\| echo "note: budget what-if skipped (no az session or RG) - see operations/FINOPS.md §4"` |
| D-FIN-R1 | `README.md` | folder layout tree, under `operations/` (after delta D-OPS-R1) | `│   ├── FINOPS.md, TOKEN_ECONOMY_PLAYBOOK.md, cost-budget.bicep   ← cost model, tier-tuning loop, component budgets` / `│   └── evaluation/            ← golden set, EVALUATION.md, run_evals.py (gates before any model/tier/prompt/template change)` |
| D-FIN-Q1 | `REQUIREMENTS.md` | after delta D-OPS-Q1 | `Token economy is operated, not only designed: operations/FINOPS.md (cost per component and per deliverable, capacity, budgets), operations/TOKEN_ECONOMY_PLAYBOOK.md (tier-tuning loop with an accuracy floor) and operations/evaluation/ (golden set + run_evals.py gates before any model, tier, prompt or template change).` |
| D-FIN-M1 | `governance/MODEL_ROUTING.md` | rule 7, end (after delta D-M1) | `Procedure: operations/TOKEN_ECONOMY_PLAYBOOK.md; accuracy floor evidence: operations/evaluation/run_evals.py against operations/evaluation/golden-set.*.json (gate G1); cost figures: operations/FINOPS.md §2.` |
| D-FIN-M2 | `operations/RUNBOOK.md` | row M2, Input column | append `; operations/FINOPS.md §6 checklist; evaluation/run_evals.py report of the month` |
| D-FIN-M3 | `operations/CHANGE_MANAGEMENT.md` | §4 comparison set, Procedure row | append `— executable as python3 operations/evaluation/run_evals.py --golden operations/evaluation/golden-set.example.json (EVALUATION.md gate G1); the JSON + markdown report is the artefact attached to the PR` |
| D-FIN-S1 | `{group:azure-platform}` request (no repo file) | subscription | `az costmanagement alert` / portal: anomaly alert scoped to subscription `{subscription-id}`, filter resource group `rg-infosec-foundry`, recipient `{email:sg-infosec-foundry-owner}` — recorded in `team/ACCESS_REGISTER.md` change log |
