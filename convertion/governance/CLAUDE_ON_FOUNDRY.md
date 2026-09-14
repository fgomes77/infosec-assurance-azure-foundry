# Claude Models on Microsoft Foundry — correction of record and switch procedure

Earlier drafts of this kit said Claude models are **not available** on
Azure / "not offered in the Azure catalogue". **That statement is wrong and
is withdrawn.** Anthropic Claude models are offered in the Microsoft
Foundry model catalog. They are not used by this deployment for a
different reason: **EU data residency**. This file is the single record of
that correction, of what the infrastructure already supports for the day
the residency position changes, and of the procedure to switch a tier.

Decision of record for the platform: `../enterprise/ENTERPRISE_BLUEPRINT.md`
**MDL-3**; prerequisite entry `../enterprise/series/00-prerequisites.md`
**D10**; residency table `../infra/README.md` §Residency and §"Claude tiers
on Foundry".

## 1. The correction

| | Withdrawn statement | Position of record |
|---|---|---|
| Availability | "Claude models are not available on Azure" / "not offered in the Azure catalogue" | **Offered.** The Foundry model-retirement schedule carries an Anthropic section, which only exists for models in the catalog ([retirement schedule — Anthropic](https://learn.microsoft.com/en-us/azure/foundry/openai/concepts/model-retirement-schedule#anthropic), read 2026-09-02). |
| Why they are not used here | (implied) unavailable | **EU residency.** Reporting at the time of writing says the Anthropic models have no European data zone ([InfoQ](https://www.infoq.com/news/2026/07/claude-foundry-ga-europe/), 2026-07-05 — **community claim, not a Microsoft source**). Without an EU data zone a deployment cannot be created with `deploymentSku = DataZoneStandard`, which the residency rule requires and Azure Policy enforces (finding C11). |
| Status of the blocker | permanent | **Re-checked quarterly** at the platform-currency review (`../enterprise/UPDATE_AND_UPGRADE_REVIEW_POLICY.md` §4). Residency positions move; availability claims in this kit are never restated from memory. |

Why the distinction matters and is not pedantry: "unavailable" closes the
option and stops anyone looking again; "available but non-compliant for us"
keeps a dated, owned, re-checkable decision — which is what an ISO/IEC
42001 AIMS and an EU AI Act deployer file have to show. It also changes the
remediation: nothing Microsoft ships can fix "unavailable", whereas an EU
data zone announcement flips this decision in one quarterly review.

Where the stale text was corrected: `../README.md` (glossary row +
Limitation 1), `../MAPPING.md`, `../agents/README.md`,
`../agents/knowledge-packs/platform-self-knowledge.md`,
`../infra/README.md`, and `../../project-dossier/build_dossier.js` §4.2 /
§11.4. Agents answer capability questions from the knowledge pack, never
from model memory — that rule is the reason the wrong sentence could not be
left in one file "harmlessly".

## 2. What the infrastructure already supports

`../infra/main.bicep` does not hard-code an OpenAI-only world. Three
publisher-format parameters, each `@allowed(['OpenAI', 'Anthropic'])`, feed
the `format` field of the three `Microsoft.CognitiveServices/accounts/
deployments@2025-06-01` resources:

| Tier | Format parameter | Model-name parameter | Version parameter | Capacity parameter | Anthropic candidate |
|---|---|---|---|---|---|
| light | `lightModelFormat` | `lightModelName` | `lightModelVersion` | `lightModelCapacity` | Haiku |
| chat | `chatModelFormat` | `modelName` *(no `chat` prefix — the chat tier is the template's default model)* | `modelVersion` | `modelCapacity` | Sonnet |
| reasoning | `reasoningModelFormat` | `reasoningModelName` | `reasoningModelVersion` | `reasoningModelCapacity` | Opus |

Current values in all three parameter files (`main.parameters.json`,
`.test.json`, `.prod.json`): `OpenAI`, `OpenAI`, `OpenAI`.

Parameters that constrain any switch and are **not** relaxed for it:

| Parameter | Value | Why it still binds |
|---|---|---|
| `deploymentSku` | `DataZoneStandard` | Residency. `GlobalStandard` routes worldwide and is denied by Azure Policy, not only by the `@allowed` list (finding C11). This is the parameter an Anthropic deployment must satisfy — the format parameter is not the gate. |
| `modelVersionUpgradeOption` | `NoAutoUpgrade` | Report agents are validated against known-good outputs; an auto-upgrade would change deliverables without a change record (finding C6). Applies to all three deployments regardless of format. |
| `raiPolicyName` | the account RAI policy | Attached to every deployment by the template. Confirm on the day that the policy applies to the chosen Anthropic model — if content filtering is not enforced for that format, the compensating control is the verifier plus the approval gate, and the gap is recorded before the switch. |

Two structural consequences to plan for, both easy to miss:

1. **The deployment name is the model name.** Each deployment resource uses
   `name: modelName` / `reasoningModelName` / `lightModelName`. Changing a
   tier's model therefore changes its **deployment name**, so
   `MODEL_DEPLOYMENT_NAME`, `REASONING_MODEL_DEPLOYMENT_NAME` and
   `LIGHT_MODEL_DEPLOYMENT_NAME` in `../setup/.env` must move with it, and
   so must `_deployment_of_record` in `../integrations/registry.json`. A
   switch is never a one-parameter edit.
2. **Deployments are created serially** (`dependsOn` chains
   light → reasoning → chat). Switching one tier redeploys that resource;
   plan the window, not just the parameter.

## 3. Tool capability — the rule that decides the reasoning tier

Whatever the publisher, a tier may only carry a model that supports **every
tool type** its agents hold. The reasoning tier carries Bing grounding,
read-only OpenAPI tools, MCP, Azure AI Search and SharePoint; finding C4
rejected `o3-mini` for exactly this reason, and the same test applies to an
Anthropic candidate. The matrix of record is
`../integrations/registry.json` → `model_tiers._tool_compatibility`
(source: the Foundry tool-support table, read on the day); the rule and the
vision/token-economy rules are `MODEL_ROUTING.md`.

A model that cannot carry the tools is not a fidelity improvement — it is a
silent regression, because the agent answers without ever calling them.

What does **not** change with the publisher: tool use, MCP and A2A
hand-offs are provided by the Foundry Agents runtime, not by a model SDK.
Switching a tier to Anthropic adds **no** Anthropic SDK, no new egress path
and no new credential to this kit.

## 4. Switch procedure (per tier)

Treat a tier switch as a **Tier-C change** (`../operations/CHANGE_MANAGEMENT.md`):
model-of-record changes are pre-approved by the accountable owner, validated
against the comparison set, and promoted as a new agent version (finding
C19) before serving traffic.

1. **Confirm availability and residency, on the day.**
   `az cognitiveservices model list -l {location} -o table` — the model must
   appear with an EU Data Zone SKU. A news article is not evidence for this
   step; the CLI output is, and it is filed.
2. **Confirm tool support** for the candidate in the Foundry tool-support
   table; record the row in the step-02 sign-off
   (`../enterprise/series/02-foundry-account-project-models.md`).
3. **Record the decision** — owner approval, the two outputs above, and the
   RAI-policy position (§2) — before any parameter moves.
4. **Change the parameters together**: `<tier>ModelFormat = 'Anthropic'`,
   the tier's model-name and version parameters, the matching
   `*_DEPLOYMENT_NAME` in `../setup/.env`, and `_deployment_of_record` in
   `../integrations/registry.json`.
5. **Deploy to `test` first** with `main.parameters.test.json`.
6. **Run the comparison set**: `scripts/smoke_test.py` prompts plus one
   known assessment on both deployments; render both deliverables and diff
   them. The renderers are deterministic, so **only the verified JSON should
   differ** — a diff in layout or styling means something other than the
   model changed.
7. **Re-run the evaluation gates** (`../operations/evaluation/run_evals.py`)
   and the golden set; a tier change is exactly what those gates exist for.
8. **File the comparison with the template-manager approval** and promote.
9. **Update** this file's §5 decision row and
   `../enterprise/ENTERPRISE_BLUEPRINT.md` MDL-3.

Rollback: revert the parameter set and redeploy the tier; agent versions are
immutable, so pipelines pinned to the previous version keep running while
the new version is withdrawn.

## 5. Decision record

| Field | Value |
|---|---|
| Decision | **Do not deploy Anthropic-format tiers.** Availability is not the blocker; the absence of an EU data zone is. |
| Tiers affected | all three (light / chat / reasoning) — the kit runs OpenAI-format deployments |
| Accountable owner | `{upn:owner}` (Francisco Gustavo Gomes) |
| Recorded | 2026-09-12 |
| Re-check | quarterly platform-currency review — step: re-run §4 step 1 and record the result even when unchanged |
| Reverses when | an EU Data Zone SKU exists for the candidate model **and** §3 tool support is confirmed |
| Compensating controls while OpenAI-format | UAT against claude.ai baselines (ROLLOUT_PLAN Phase 4), per-agent self-check, `output-verifier`, and the human approval gate — the fidelity risk is `../README.md` Limitation 1 and the "Model substitution risk" row of the dossier |
| If Claude fidelity is mandatory for a workload | keep that workload on claude.ai / the Claude API and deploy a subset here (`convert_skills.py --only`); do **not** relax `deploymentSku` to obtain it |

## 6. Verification

| # | Check | How | Healthy when |
|---|---|---|---|
| V1 | No "not available" claim survives as an assertion | `grep -rni "claude.*not available\|not offered in the azure catalogue" --include=*.md --include=*.js --exclude=CLAUDE_ON_FOUNDRY.md --exclude-dir=build --exclude-dir=claude-account-export .` | exactly two hits, both **quotations inside a correction**: `enterprise/ENTERPRISE_BLUEPRINT.md` MDL-3 (its decision record, D-EB1 applied) and `project-dossier/build_dossier.js` (the risk row that states the correction and quotes the withdrawn wording). This file is excluded by name because quoting the withdrawn wording is its whole purpose. Any hit that is not a quotation inside a correction is a live wrong claim and is fixed |
| V2 | The format parameters still accept Anthropic | `grep -n "ModelFormat" ../infra/main.bicep` | three parameters, each `@allowed(['OpenAI', 'Anthropic'])` |
| V3 | Residency SKU unchanged | `grep -n "deploymentSku" ../infra/main.parameters*.json` | `DataZoneStandard` in every file |
| V4 | The quarterly re-check happened | the platform-currency review record | a dated §5 "Re-check" entry for the current quarter, pass or no-change |

Review: quarterly with the platform-currency review, and immediately on any
Microsoft announcement of Anthropic model residency in the EU.
