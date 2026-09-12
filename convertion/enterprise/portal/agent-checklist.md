# Per-Agent Portal Checklist

Run for every agent after `../../deploy.sh` and before a version is
promoted (Build > Agents > *agent* > Versions > Promote). The checklist is
evidence for the owner's review (`../../operations/CHANGE_MANAGEMENT.md`)
and for the quarterly access review. Agents v2 facts: every save is an
immutable version referenced as `<agent>:<version>`; the served version is
chosen explicitly (`version_selector`), so a promotion is a human act
([Development lifecycle](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/development-lifecycle),
GA, 2026-08-27; [Publish — active version](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/publish-copilot#select-an-active-agent-version),
GA, 2026-08-26). Fixed limits: 128 tools per agent, 1 vector store per
agent, 512 MB per file, 10,000 files per vector store
([Limits](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/limits-quotas-regions), GA, 2026-09-07).

## A. Identity and model

| # | Check | Expected | Where |
|---|---|---|---|
| A1 | Name matches the export skill name / registry key | e.g. `dora`, `tpa-evidence-analyzer` | Build > Agents |
| A2 | Description = the skill's trigger description (routing text) | non-empty, unchanged from `build/agents/<agent>/manifest` | agent header |
| A3 | Model deployment = the registry `model_tier` | light `gpt-4o-mini` / chat `gpt-4o` / reasoning `o3-mini` (or the MDL-4 successor for tool-bearing agents) | Setup > Model |
| A4 | Tool-bearing reasoning agent is NOT on a model without OpenAPI/MCP support | o3-mini: OpenAPI/MCP/SharePoint/Web Search unsupported → must be on the successor deployment | [Tool support](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/limits-quotas-regions#tool-support-by-region-and-model) |
| A5 | Version promoted = `build/manifest.json` version; older versions kept for rollback | pinned, not "always latest", for pipeline agents | Versions |

## B. Instructions

| # | Check | Expected |
|---|---|---|
| B1 | Persona preamble present at the top (`../../agents/persona_system_prompt.md`) | yes |
| B2 | `APPROVAL GATE` block present | yes — Layer 2 of HUMAN_APPROVAL |
| B3 | Egress rule present when `web-search` is attached | yes (appended by `attach_integrations.py`) |
| B4 | Advisory addendum + read-only charter on the eight advisory agents | yes (`apply_advisory_profile.py`) |
| B5 | SHA-256 of instructions = manifest hash | equal; else drift (PORTAL_CONFIGURATION §4) |

## C. Tools (read-only by construction)

| # | Check | Expected |
|---|---|---|
| C1 | `file_search` bound to `vs-<agent>` (advisor: `vs-assurance-combined` + `vs-assurance-memory`) | one store per agent (platform limit) |
| C2 | `code_interpreter` files = the skill's `scripts/` + `assets/` (and the advisory agents) | present; Python-only sandbox, no outbound network ([Code Interpreter](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/code-interpreter), GA, 2026-08-05) |
| C3 | OpenAPI tools: only GET + `x-enx-read-only` operations; connection = `conn-*` | `attach_integrations.py --dry-run --only <agent>` prints `[read-only]` on each |
| C4 | MCP tool `enx_gateway`: `allowed_tools` non-empty, all `readOnlyHint=true`; `require_approval` `never` only for the allow-listed reads; auth via project connection (agent identity / MI), no header token | [MCP tool](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/model-context-protocol) (GA, 2026-08-26) |
| C5 | Web search only on agents listed with `web-search` in the registry | others: none |
| C6 | No Connected Agents tool (not available in Agents v2); orchestrator/control-center use A2A tools to **published** specialists | [Migrate](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/migrate#agent-tool-availability) (GA, 2026-08-05); [A2A](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/agent-to-agent) (preview) |
| C7 | SharePoint grounding tool (preview) only on interactive advisors, never on pipeline or Teams-published agents | SP-1 |
| C8 | Tool count ≤ 128; orchestrator groups TPRM specialists behind `enx-tprm-control-center` | limit |
| C9 | `write_connections` absent for this agent in the registry | absent (any grant = Tier C PR) |

## D. Guardrails, tracing, evaluation

| # | Check | Expected |
|---|---|---|
| D1 | Agent-level guardrail = registry `guardrail_policy` (`infosec-security-analysis` for report agents; `infosec-web-facing` for web/SharePoint/OpenAPI agents) | set; agent guardrail overrides the deployment's ([Guardrails](https://learn.microsoft.com/en-us/azure/foundry/guardrails/how-to-create-guardrails), GA, 2026-07-30) |
| D2 | Tracing visible in Operate > Tracing for a smoke-test run (`scripts/smoke_test.py --agent <agent>`) | spans with tool calls and tokens |
| D3 | Continuous evaluation rule attached (see `guardrails-tracing-evaluations.md`) | yes for pipeline + advisory agents |
| D4 | Golden-set evaluation run recorded before promotion (`../../operations/evaluation/golden-set.schema.json`) | run id in the change record |

## E. Publishing (only the six Copilot-fit agents)

| # | Check | Expected |
|---|---|---|
| E1 | Published agent has its own Entra Agent ID; data-plane read roles **re-assigned** to it | recorded in `ACCESS_REGISTER.md` ([Agent identity](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/agent-identity), GA, 2026-08-25) |
| E2 | Audience = `sg-infosec-foundry-users` only | Teams admin center app permission policy |
| E3 | No file upload / SharePoint tool expectation in Copilot | documented limitation |

## F. Sign-off

| Field | Value |
|---|---|
| Agent / version | `{agent}:{version}` |
| Reviewed by | `{upn:francisco.gomes}` (deputy `{upn:deputy-approver}` when the owner authored) |
| Change record | `{jira:INFOSEC-PLAT}-nnn` / PR `#{n}` |
| Evidence | manifest hash, dry-run output, eval run id, screenshot of Versions pane |

## Agent groups (from `../../integrations/registry.json`)

| Group | Agents | Tier | Tools |
|---|---|---|---|
| Advisory (read-only toolset pinned) | iso27001, iso42001, dora, nis2, eu-ai-act, cyber-forum, tpsrca-assessment-engine, infosec-assurance-advisor | reasoning | full read surface + web-search + osint-proxy |
| OSINT / research | deepsearch-protocol, ai-deepsearch-osint-gathering-report | reasoning | web-search, securityscorecard, osint-proxy (+ iaf, cmdb, defender, gateway for deepsearch) |
| Report generation | dpia, onetrust-form-b, ciso-reporting, ciso-executive-summary, tprm-slide-generator, pptx-executive-summary-ciso, template-manager | chat | onetrust, sharepoint-graph (+ jira for ciso-reporting) |
| Delivery / analysis | ciso-global-report, tpa-evidence-analyzer, soc-report-analyzer, pentest-report-analyzer, pdf-full-coverage-analyzer | reasoning | sharepoint-graph (read), per registry |
| Document transformation | docx, pdf, pptx, xlsx | light | code_interpreter only |
| Router | enx-tprm-control-center | light | none (A2A hand-offs only) |
| Examples (opt-in) | doc-coauthoring, internal-comms, learn, mcp-builder, morning | per registry | per registry |
| Verifier | output-verifier | reasoning | none (rules only) |
