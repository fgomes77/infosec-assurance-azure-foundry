# Owner Workbench — one place to run, develop and change the platform

For the accountable owner (`TEAM_MODEL.md` §1: `{upn:francisco.gomes}`), and
for whoever deputises. The five assurance users have `USER_QUICKSTART.md`,
which covers *using* the ten systems; this file covers *developing and
operating* them — and it is deliberately the only page you should need open.

Everything here points at something executable. If a command in this file does
not work, that is a defect in this file.

## 1. Open the console first

```bash
python3 scripts/build_console.py          # build/console/enx-console.html + catalog.json
```

The **ENX Assurance Console** is a single self-contained page holding the whole
platform: the ten systems, every agent with its tier, profile class, tools and
charter, every pipeline and workflow, every connection and what it may read,
every template, every dashboard query, and every runbook with its own first
line. It has a filter box — type `evidence`, `dora`, `cache` and the page
narrows to what matters.

It is **generated, never authored**: it cannot describe an agent the platform
does not have, and a new agent appears the moment it is registered. The same
inventory is `build/console/catalog.json`, which the MCP `catalog` tool serves
— so the page, the chat clients and Copilot all read one source.

| Where | How |
|---|---|
| Locally | `python3 scripts/build_console.py && open build/console/enx-console.html` |
| From any MCP client | tool `catalog` (optionally `area=agents`, `area=develop`, …) |
| For the team | store the page in SharePoint `Governance/Console/` after each platform release (`operations/LIFECYCLE.md`) |
| In CI | `python3 scripts/build_console.py --check` fails the build when an agent, connection, workflow or query has no description |

That last row is the point of the check: an item nobody described is an item
nobody can safely use, so the console treats a missing description as a defect
rather than rendering a blank cell.

## 2. The change map

Every change class, what to edit, what to run **before**, how to apply it, and
the gate it must pass. `Tier A` self-service · `Tier B` peer-approved ·
`Tier C` owner-only (`TEAM_MODEL.md` §12.1).

| Change | Edit | Check before | Apply | Tier |
|---|---|---|---|---|
| Agent charter | `agents/<name>_instructions.md`, or the export for a converted skill | `convert_skills.py && verify_conversion.py` | `create_agents.py --only <name>` | B |
| Tools on an agent | `integrations/registry.json` + the spec | `attach_integrations.py --dry-run` | `attach_integrations.py --only <name>` | B |
| How an agent runs | `integrations/inference-profiles.json` | `inference_profiles.py --show <name>` | `attach_integrations.py --only <name>` | B |
| Report template | `templates/` + `templates/registry.json` | `update_templates.py … --dry-run` | the `template-update-approval` workflow | C |
| Workflow / pipeline | `workflows/*.json` | `ci/tests/test_workflow_efficiency.py` | `ci/deploy_logicapps.sh` | B |
| Infrastructure | `infra/*.bicep`, parameters | `infra/validate.sh` + `ci/tests/test_residency.py` | `az deployment group create` (series 01–02) | C |
| Model tier | registry `model_tiers` + infra params | `enterprise/upgrade/check_model_lifecycle.py --dry-run` | six-phase migration (policy R3) | C |
| Durable knowledge | `agents/advisor-knowledge/` or a memory note | `memory_store.py --list` | `memory_store.py --add …` | A |

Two rules hold across all of them. **Never edit `build/` or
`claude-account-export/`** — one is generated, the other is the byte-verified
source. And **run the gates locally before you push**: they are offline and
take seconds, and CI runs exactly the same scripts.

## 3. The full gate set, in the order CI runs it

```bash
python3 scripts/convert_skills.py && python3 scripts/verify_conversion.py
python3 scripts/verify_kit.py
convertion/ci/syntax_check.sh
python3 ci/tests/test_residency.py
python3 ci/tests/test_workflow_efficiency.py
python3 scripts/build_self_knowledge.py --check
python3 scripts/build_console.py --check
python3 scripts/inference_profiles.py --check
python3 -m pytest functions/delivery/tests functions/office-tools/tests scripts/tests -q
infra/validate.sh
python3 scripts/scan_secrets.py
```

`pre-commit run --all-files` runs the same set on commit and push.

## 4. Develop a new system end to end

The shortest honest path from "the team wants X" to "X is a system", with the
gate that stops each step going wrong:

1. **Write the charter.** `agents/<name>_instructions.md` — persona is
   prepended automatically; state the extraction rules, the thresholds, the
   output contract and what the agent must never do. Gate: `verify_conversion`.
2. **Define the output contract.** `templates/<name>.schema.json` plus a sample
   under `templates/samples/`. Gate: `evaluation/run_regression.py`.
3. **Build the renderer** (if it produces a file) under
   `functions/delivery/renderers-src/<name>/`. Gate:
   `scripts/stage_renderers.py --strict`.
4. **Register the agent**: tier, tools, guardrail policy in
   `integrations/registry.json`; class in `integrations/inference-profiles.json`.
   Gate: `inference_profiles.py --check`, `attach_integrations.py --dry-run`.
5. **Add the pipeline** in `workflows/pipelines.json` (requirement id, agent,
   render format, template, approval kind). Gate:
   `test_workflow_efficiency.py`.
6. **Document it** in `REQUIREMENTS.md` and `USER_QUICKSTART.md`. Gate:
   `verify_kit.py` (cross-references) and `build_console.py --check`
   (description present).
7. **Prove it**: run it end to end in dev, verify the deliverable against a
   known-good, then promote. Gate: the golden set.

## 5. Operate

| Question | Where to look |
|---|---|
| What is it costing, and which agent? | `operations/kql/latency-and-tokens.kql`, `FINOPS.md` |
| Are the caches working? | `operations/kql/prompt-cache-hit-rate.kql` (target ≥ 0.6) |
| Is quality holding? | `operations/kql/verifier-fail-rate.kql`, the weekly evaluation run |
| Is anything waiting on a person? | `operations/kql/approval-sla.kql` |
| Did anything leave that should not have? | `operations/kql/egress-detection.kql` |
| Is the live platform still what the kit says? | `scripts/verify_deployment.py`, nightly drift workflow |
| What changed and who approved it? | `operations/CHANGE_MANAGEMENT.md`, the version ledger |
| What is still open to improve? | `operations/FOUNDRY_OPTIMIZATION_REGISTER.md` §3 |

## 6. Rhythm

- **Daily (hypercare):** pipeline failures, verifier fails, approval queue, egress alerts.
- **Weekly:** evaluation + red-team run; backlog triage.
- **Monthly:** tier tuning on real telemetry; cost review; access review.
- **Quarterly:** platform currency review (model retirements, preview→GA, region
  availability, the Claude residency re-check), policy compliance export, DR test.
  Rebuild the console and file it with the quarter's evidence pack.

## 7. When something is wrong

| Symptom | First move |
|---|---|
| A pipeline fails at the agent step | Check the agent version pinned in `pipelines.json` against `build/agent-versions.json` |
| The verifier fails repeatedly on one report type | Read the FAIL reasons; the fix is usually the charter's extraction rules, not the model |
| A deliverable looks different from last quarter | Check the template version and the model version — both are pinned, so a change had an approval |
| An agent cannot call a tool | `attach_integrations.py --dry-run`: tier model vs tool compatibility is enforced there |
| Cost jumped | Cache hit rate first, then tokens per agent — a broken prefix looks like a price rise |
| Anything involving a tenant change | `operations/RUNBOOK.md`, and it is Tier C |
