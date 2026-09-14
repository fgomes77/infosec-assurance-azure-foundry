# Guardrails, Prompt Shields, Tracing and Evaluations — Settings of Record

What is configured, where, and the values the owner verifies in the portal
(Build > Models > deployment > Guardrails; Build > Agents > agent >
Guardrails; Operate > Tracing; Operate > Evaluations). Everything here is
observability or filtering — no setting changes what agents produce, and
the human approval gate stays the release control.

## 1. Guardrails (RAI policies)

A guardrail is an ARM `raiPolicy` assigned to a deployment
(`properties.raiPolicyName`) and, in Agents v2, also assignable per agent,
where "the agent's guardrail overrides the model deployment's"
([Create guardrails](https://learn.microsoft.com/en-us/azure/foundry/guardrails/how-to-create-guardrails), GA, 2026-07-30).
Base policy `Microsoft.DefaultV2` is not editable.

| Policy | Assigned to | Hate / Sexual / Violence / Self-harm | Jailbreak (Prompt Shields, direct) | Indirect attack (XPIA, documents/tool outputs) | Protected material text / code | Rationale |
|---|---|---|---|---|---|---|
| `infosec-security-analysis` (*kit*, `main.bicep`) | all three deployments; report/document agents | High, **annotate** (prompt + completion) | **block** | not enabled | text block / code annotate | GRC vocabulary (exploits, attack paths) must not be blocked — DATA_PROTECTION §3 |
| `infosec-web-facing` (D-EB7) | agents with `web-search`, `osint-proxy`, `sharepoint-graph`, `confluence-cloud`, `enx-gateway-mcp` (advisory, OSINT, analyzers) | same | block | **annotate first (pilot), then block** after 30 days without false positives on supplier questionnaires | same | retrieved content is data, never instructions (persona rule); XPIA makes it a platform control |

Portal checks: deployment guardrail name = policy; agent guardrail =
registry `guardrail_policy`; a legitimate block shows `content_filter`
finish reason in tracing → RUNBOOK FM-04 (adjust severity, never disable).
Annotations surface in App Insights (`gen_ai.*` / content-filter results) for
the injection dashboard (`../../operations/MONITORING.md`).

## 2. Defender for AI and Purview (Operate > Compliance)

| Control | Setting | Status / source |
|---|---|---|
| Defender for Cloud — AI threat protection | plan **AI Services** = Standard on `{sub:infosec-foundry}`; alert-processing rule: High → `{baseName}-ag` SOC receiver, Medium → owner | GA, commercial clouds, text tokens; [alert catalogue](https://learn.microsoft.com/en-us/azure/defender-for-cloud/alerts-ai-workloads) (2026-07-06) |
| Purview Data Security for Foundry | enabled in Control Plane; DSPM for AI; retention policy "Enterprise AI apps" per ISMS schedule; Insider Risk "Risky AI usage" → SOC; user security context passed by MCP server / Logic Apps / Copilot | GA; PAYG billing needed for policies; [Purview for Foundry](https://learn.microsoft.com/en-us/purview/ai-azure-foundry) (2026-05-01) |
| Control Plane guardrail policies | Operate > Compliance > Policies: require the RAI policy on every deployment; scope = RG; needs Owner / Resource Policy Contributor; up to 30 min to appear | [Compliance](https://learn.microsoft.com/en-us/azure/foundry/control-plane/how-to-manage-compliance-security) (2026-08-04; Operate partly preview) |

## 3. Tracing

| Setting | Value | Notes |
|---|---|---|
| Exporter | `app-insights` connection to `{baseName}-appi` (`main.bicep`) | GA for prompt and hosted agents; preview for workflow/external agents ([GA scope](https://learn.microsoft.com/en-us/azure/foundry/concepts/general-availability), 2026-09-09) |
| Content recording | **on** (needed by the egress detector — Bing query text) | traces contain assessment excerpts → Confidential; readers = owner + `sg-infosec-foundry-readers` (`MONITORING.md` §2) |
| Retention | 365 d workspace | DORA Art. 28 |
| Network isolation | traces are **not fully network-isolated** — accepted residual (NET-2) | [rollout pitfalls](https://learn.microsoft.com/en-us/azure/foundry/concepts/general-availability#common-rollout-pitfalls) |
| Diagnostic categories | Audit, RequestResponse, Trace, AzureOpenAIRequestUsage (+ AllMetrics) | [Diagnostic logging](https://learn.microsoft.com/en-us/azure/ai-services/diagnostic-logging) (GA, 2026-07-13) |
| Alerts | egress-internal-markers (sev 1), verifier-fail-rate, pipeline-failures, approval-expiry, agent-drift (`../../infra/monitoring.bicep`) | plus Defender AI alerts (§2) |

## 4. Evaluations

| Mechanism | Setting | Status / source |
|---|---|---|
| Golden-set (offline) | dataset per report agent from approved SharePoint reports (`../../operations/evaluation/golden-set.schema.json`); run before every promotion; evaluators: groundedness, relevance, task adherence, tool-call accuracy, plus the verifier rules as a custom evaluator | Evaluations GA (some evaluators preview) — [Observability](https://learn.microsoft.com/en-us/azure/foundry/concepts/observability) (2026-07-31) |
| Continuous evaluation (production sampling) | per pipeline + advisory agent: `samplingPercent` 10, `maxRequestRate` ≤ 100/h (system max 1000/h); results to App Insights; alert on score drop | announced/GA per observability page; classic how-to 2026-01-08 |
| Human evaluation templates | template `assurance-review`: thumbs, 1–5 accuracy, "citation correct?" multiple choice, free text; reviewers = `sg-infosec-foundry-report-approvers` via the agent Preview app | preview — [Human evaluation](https://learn.microsoft.com/en-us/azure/foundry/observability/how-to/human-evaluation) (2026-07-31) |
| AI Red Teaming Agent | quarterly run on `cyber-forum`, `deepsearch-protocol`, the advisor: content risks + prohibited actions (write attempts, egress of internal markers) with human-in-the-loop allowance rules; results filed with the ISMS review | preview — [Red teaming agent](https://learn.microsoft.com/en-us/azure/foundry/concepts/ai-red-teaming-agent) (2026-08-27) |
| Agent optimizer | may propose instruction candidates from evaluation runs; **only the owner promotes**; candidates diffed in the PR like any prompt change | preview — [Agent optimizer](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/agent-optimizer-overview) (2026-08-19) |
| Fine-tuning | not used (template-driven outputs; comparison set covers fidelity) | [When to fine-tune](https://learn.microsoft.com/en-us/azure/foundry/openai/concepts/fine-tuning-considerations) (2026-06-05) |

Owner cadence: monthly M1 review reads the evaluation dashboard, verifier
fail rate and Defender/Purview reports together (`../../operations/RUNBOOK.md`
§2 Monthly); any evaluator score drop on a report agent triggers the
re-sync / tier review of `MODEL_ROUTING.md` rule 7 — never an in-portal edit.
