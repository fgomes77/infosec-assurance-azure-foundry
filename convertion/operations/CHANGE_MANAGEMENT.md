# Change Management — Owner's PR-Based Process for Every Platform Change

How a change to the platform is proposed, verified, approved, rolled out
and rolled back. Scope = everything `../team/TEAM_MODEL.md` §12 calls a
*platform change* (Tier C) plus the two changes that have their own
approval-gated workflow (template updates, memory deletion). The
accountable owner `{upn:francisco.gomes}` runs the process; peers propose;
the deputy `{upn:deputy-approver}` reviews the owner's own changes. Nothing
here alters what agents produce — the fidelity gate
(`../scripts/verify_conversion.py`) exists precisely so that a change
either keeps outputs byte-identical to the claude.ai originals or is
visibly a new version.

Principles: one path (PR → CI gates → review → `production` environment
approval → `../deploy.sh` → post-checks); no hand edits in the portal
(detected by `agent_modified_by_non_deploy_identity`,
`breakglass_window_write` — `MONITORING.md` §4); prefer *disable* to
*change* during incidents; every change leaves a record (§7). Control:
ISO 27001:2022 A.8.32 (change management), A.8.9 (configuration
management), A.8.31 (separation of dev/test/prod), A.8.29 (security
testing), A.5.3 (SoD); ISO 42001 A.6.2.4–A.6.2.5 (verification,
validation, deployment), A.6.2.7 (operation and monitoring); DORA Art.
9(4)(e), 8(2)–(3); EU AI Act Art. 9 (risk management through the life
cycle, as deployer of a substantially modified system), Art. 26.

## 1. Change types and gates

| Type | Files (examples) | Tier / approver | Mandatory gates before merge | Rollout | Rollback |
|---|---|---|---|---|---|
| **Prompt / instructions / persona** | `../agents/*_instructions.md`, `../agents/persona_system_prompt.md`, advisor knowledge packs, `../agents/verifier_instructions.md` | C — owner (deputy when the owner authored) | `verify_conversion.py`; `create_agents.py --dry-run` / `create_delivery_agents.py --dry-run` / `create_orchestrator.py --dry-run`; comparison set (§4) for report-producing agents; W2/W3 checks pass on the built output | `deploy.sh` (steps 1–6b); Copilot republish if published | revert PR → `deploy.sh` (idempotent by agent name) |
| **Registry — tools, tiers, `write_connections`** | `../integrations/registry.json`, `../integrations/openapi/*.yaml`, `../integrations/mcp/enx-gateway.json` | C — owner; any non-empty `write_connections` additionally needs the line manager and a `HUMAN_APPROVAL.md` update (default stays none) | `attach_integrations.py --dry-run` shows `[read-only]` on every tool; JSON/YAML parse; tier change for report agents needs the comparison set (`MODEL_ROUTING.md` "Accuracy floor"); advisory agents never leave `reasoning` | `attach_integrations.py --only <agent>` or full `deploy.sh` step 4/5b | revert → re-attach |
| **Template (j)** | source template in the export + `../templates/registry.json` | C via `../workflows/template-update-approval.json` (visual before/after review; owner approves; deputy if the proposer is the owner) | `update_templates.py --dry-run`; `verify_conversion.py` re-run inside the script; renderer re-staged | `update_templates.py --template <id> --file … --approved-by … --approval-run <run>` (atomic, rolls back on failure) | previous version is the backup the script keeps; re-apply it with a new approval run |
| **Integration credential / connection** | Key Vault secret version, Foundry `conn-*` target | owner + custodian (F8) — no PR for the secret value, PR for any scope/spec change | custodian confirms read-only scope; `ACCESS_REGISTER.md` row updated | new secret version → connection re-pointed → smoke test of the tool | re-point to the previous version (kept until the next rotation) |
| **Infrastructure** | `../infra/main.bicep`, `main.parameters.json`, `../team/rbac.bicep`, `alerts.bicep`, Logic Apps definitions `../workflows/*.json`, `../functions/delivery/*` | C — owner; RBAC/consent changes also line manager (`TEAM_MODEL.md` §6) | `bicep build` + `az deployment group what-if`; JSON parse of workflow definitions; `func` local run for the Function; `access-review.sh --quick` after deploy shows no unexpected assignment | pipeline with the deploy SP (OIDC, `production` environment) | `what-if` of the previous commit, redeploy; Logic Apps keep run history across versions |
| **Model tier / capacity** | `model_tier` in the registry; `modelCapacity`, model versions in Bicep | C — owner; downgrade of a report agent requires the comparison set; `enterprise/upgrade/check_model_lifecycle.py` clean; the tool-support row for the tier model pasted into the checklist | as Registry + Infrastructure | staged: one agent first, observe 1 week (`kql/latency-and-tokens.kql`, `kql/verifier-fail-rate.kql`) | revert the tier |
| **Re-sync from a fresh claude.ai export** (F6) | `../../claude-account-export/` refresh | C — owner | `convert_skills.py` → `verify_conversion.py` must pass; diff of `build/manifest.json` vs baseline reviewed; comparison set for changed report agents | full `deploy.sh`; template registry versions bumped where sources changed | previous export tag → `deploy.sh` |
| **Access** (groups, roles, Sites.Selected, CA, PIM) | `../team/rbac.bicep`, `../team/least-privilege/entra/groups.json`, access packages | line manager for privileged groups; owner for user groups | `provision_identity.sh --plan`; `what-if` | `provision_identity.sh --apply` / `rbac.bicep` | previous assignment set; `access_snapshot.sh` before/after |
| **Memory deletion of another's note** | `vs-assurance-memory` | C `MEMORY_DELETE` — author, else owner; deputy when the owner requests | `memory_store.py list` shows the note id | `memory_store.py delete <file_id>` | none (deletion is the point) — record the note text hash in the ticket |
| **Runbooks / docs only** | `operations/*.md`, `team/*.md`, READMEs | owner; peer review | markdown renders; links resolve | merge | revert |

Out of scope for this process (no change record needed): a user's own
threads, running a pipeline, approving a report (Tier A/B), saving a
memory note, rotating one's own `az login`.

## 2. Roles

| Role | Who | Responsibility |
|---|---|---|
| Proposer | any of the five (PR, or `template-manager` proposal, or a ticket the owner converts to a PR) | describes the intent and the requirement (a–j) affected |
| Author | owner (or proposer with GitHub Write for a docs/prompt PR) | implements on a branch; never on `main` |
| Reviewer | deputy for owner-authored PRs (CODEOWNERS); owner for everyone else's | checks §4 evidence is attached, least privilege unchanged, placeholders only |
| Approver | owner approves the `production` environment deployment as accountable; deputy approves Tier C items the owner authored (`TEAM_MODEL.md` §12.2) | recorded by GitHub environment approval / the approval workflow |
| Executor | deploy SP `{app:infosec-foundry-deployer}` via GitHub OIDC; owner under PIM only for §8 | runs `deploy.sh` |

Self-approval is impossible by construction: branch protection requires a
review from someone other than the author, and the owner cannot add
himself to the groups that approve his privileged changes (`TEAM_MODEL.md`
§6). Control: ISO 27001:2022 A.5.3; DORA Art. 9(4)(e).

## 3. Standard flow

| # | Step | Evidence |
|---|---|---|
| 1 | Ticket `{jira:INFOSEC-PLAT}-nnn`: intent, type (§1), requirement a–j, risk (§5), rollback plan | ticket |
| 2 | Branch `change/{ticket}`; edit; **placeholders only** (`{braces}`); no secrets, UPNs, object ids or hostnames (`verify_conversion.py` greps for leaked secrets) | commit |
| 3 | Local gates: `python3 scripts/convert_skills.py && python3 scripts/verify_conversion.py`; `./deploy.sh --dry-run`; `bicep build` for any `.bicep`; `python3 -m json.tool` for every JSON; `python3 -m py_compile` for every script | paste the tail of each into the PR |
| 4 | Comparison set (§4) when a report-producing agent, its template, tier or verifier rules changed | comparison report attached |
| 5 | PR with the template in §6; reviewer per §2 | PR review |
| 6 | CI (`.github/workflows/ci.yml`; exact gate list in `../ci/README.md` §1): the same gates as step 3 on a clean runner + `access-review.sh --quick` in verify-only mode; must be green | checks |
| 7 | Merge to `main`; the `production` environment holds the deployment until the owner approves (deputy cannot approve a deployment — accountability stays with the owner; the deputy's review was the SoD control) | environment approval |
| 8 | `deploy.sh` runs under the deploy SP; steps 1–7 must all pass; smoke test prompt answered | Actions log |
| 9 | Post-checks within 1 business day: RUNBOOK W1–W4; `kql/verifier-fail-rate.kql` next day; template `last_approved` bumped; Copilot republished if instructions changed | ticket comment with evidence links |
| 10 | Close the ticket; `ACCESS_REGISTER.md` change-log row when access, connections or credentials changed | register |

Lead time target: 5 business days from PR to production for standard
changes (SLO in `SUPPORT_MODEL.md` §2 for templates).

## 4. Comparison set (result-fidelity regression)

`REQUIREMENTS.md` fixes the principle: the same inputs produce the same
reports as on claude.ai. The comparison set makes that testable after a
change:

| Item | Content | Location |
|---|---|---|
| Inputs | one anonymised OneTrust PDF (b, c, d), one synthetic TPA evidence folder (d2), one SOC and one pentest report (e, f), one public supplier domain (a), the `smoke_test.py` prompts for g/h/i | `Governance/ComparisonSet/inputs/` (site) — synthetic or public data only |
| Known-good outputs | the last approved output per pipeline, hashed | `Governance/ComparisonSet/baseline/{pipeline}/` |
| Procedure | run each affected pipeline to the verifier (do **not** approve the gate — let it expire or reject it, so nothing is stored under a real supplier); download the verified JSON/HTML from the run; diff against baseline: structure, scores, thresholds, section count identical; wording differences on `chat`/`reasoning` tiers reviewed by the proposer and reviewer — executable as `python3 operations/evaluation/run_evals.py --golden operations/evaluation/golden-set.example.json` (`evaluation/EVALUATION.md` gate G1); the JSON + markdown report is the artefact attached to the PR | diff attached to the PR |
| Pass criterion | verifier PASS on first attempt for every affected pipeline; no schema/threshold/section drift; reviewer signs the wording delta | PR comment |

Control: ISO 42001 A.6.2.4 (verification and validation), A.8.4; ISO
27001:2022 A.8.29; EU AI Act Art. 9(6)–(8) (testing against defined
metrics before deployment).

## 5. Risk classification of a change

| Class | Criteria | Extra requirements |
|---|---|---|
| Low | docs, runbooks, alert thresholds, watchlist additions, new supplier on the DeepSearch list | standard flow, single reviewer |
| Medium | prompt/knowledge change, template change, tier change, new read-only OpenAPI spec, capacity | comparison set; staged rollout for tiers |
| High | anything touching write paths, identities, consents, `write_connections`, Sites.Selected, CA/PIM, RAI policy, egress rules, verifier rules | line-manager awareness; explicit statement in the PR of which invariant (`RUNBOOK.md` preamble) is affected and why it is not weakened; post-deploy `access-review.sh` full run; `HUMAN_APPROVAL.md` / `DATA_PROTECTION_GUARDRAILS.md` updated in the same PR |

A High change that *weakens* an invariant is refused by design; the
correct path is a risk-acceptance record in the ISMS signed by the CISO
delegate before any PR is opened (ISO 27001:2022 cl. 6.1.3, 8.3; DORA
Art. 6(8)).

## 6. PR template

```
Ticket:            {jira:INFOSEC-PLAT}-nnn
Type (§1):         prompt | registry | template | credential | infra | tier | re-sync | access | memory-delete | docs
Requirement(s):    a–j affected
Risk class (§5):   low | medium | high
Invariants:        read-only agents / approval before write / taxonomy / identities / EU / no-egress — unchanged (state why for high)
Gates:             verify_conversion ✔  deploy.sh --dry-run ✔  bicep build ✔  json ✔  py_compile ✔
Comparison set:    n/a | attached (pipelines: …; eval reports: build/evals/{ticket}-control, -candidate — EVALUATION.md G1)
Checklist:         enterprise/upgrade/UPGRADE_CHECKLIST.md filled and pasted below
Rollout:           deploy.sh | attach_integrations --only | update_templates | rbac.bicep
Rollback:          …
Post-checks:       RUNBOOK W1–W4 planned on {date}
Reviewer:          deputy (owner-authored) | owner
```

## 7. Records

| Record | Where | Retention |
|---|---|---|
| Ticket, PR, review, CI logs, environment approval, Actions deployment log | GitHub `{github:org/repo}` + Jira | ≥ 1 year (DORA Art. 28 evidence); repo history indefinitely |
| Template approvals | `template-update-approval` run history + `{list:ApprovalDecisions}` + `../templates/registry.json` audit line | ≥ 1 year |
| Drift baseline | `build/manifest.json` at each successful deploy, committed as `build/baseline-{date}.json` (or stored under `Governance/Operations/baselines/`) | until superseded + 1 year |
| Access changes | `../team/ACCESS_REGISTER.md` change log; `access_snapshot.sh` before/after | per quarterly review |
| Emergency changes (§8) | ticket + retrospective PR + post-incident note (`RUNBOOK.md` §6) | ≥ 1 year |

Control: ISO 27001:2022 A.5.33, A.8.15; ISO 42001 A.6.2.3 (documentation),
A.6.2.7; EU AI Act Art. 12, 26(6).

## 8. Emergency change

Used only during an open P1/P2 (`RUNBOOK.md` §3) when waiting for the
standard flow would prolong the impact.

| # | Step | Who | Control |
|---|---|---|---|
| 1 | Ticket states the incident and the *minimum* change; prefer disable (workflow, connection, tool, secret version) — disabling needs no approval | owner (deputy under break-glass may only disable) | `TEAM_MODEL.md` §12.3 |
| 2 | Activate PIM with the ticket id as justification (`Contributor` needs the line manager) | owner | PIM record; `breakglass_window_write` will fire — expected |
| 3 | Apply the change by hand only if the pipeline cannot run; otherwise push a hotfix branch and deploy through the pipeline with an expedited review (deputy, ≤ 2 h) | owner | Actions log |
| 4 | Within 1 business day: retrospective PR that makes the repo equal to what is deployed (`verify_conversion.py` must pass; `deploy.sh --dry-run` clean); reviewer per §2 | owner | PR |
| 5 | Deactivate PIM; rotate any secret whose value was read (`keyvault-human-secret-read`) | owner + custodian | KV version |
| 6 | Post-incident note lists the emergency change and the retrospective PR | owner | `Governance/Incidents/` |

An emergency change never grants `write_connections`, never widens Graph
permissions, never disables content filtering or the verifier, and never
approves a pending report (those remain Tier A/B/C decisions). Control:
ISO 27001:2022 A.8.32 (emergency changes recorded and reviewed), A.8.2;
DORA Art. 9(4)(e), 17(2).

## 9. Calendar

| Cadence | Activity | Owner |
|---|---|---|
| Per change | flow §3 | owner |
| Weekly | post-checks of the week's changes (RUNBOOK W1–W4) | owner |
| Monthly | tier/cost review → tier changes (RUNBOOK M2); known-issue list | owner |
| Quarterly | template inventory review (`../templates/registry.json` consumers and `last_approved`), alert threshold review (`alerts.bicep` / `../infra/monitoring.bicep` params), comparison-set refresh with the latest approved outputs; improvement cycle review/plan/verify/report (`CONTINUOUS_IMPROVEMENT.md` §4) | owner + one peer |
| Quarterly | platform currency review (`../enterprise/UPDATE_AND_UPGRADE_REVIEW_POLICY.md` §4): model retirement schedule, SDK changelog, API lifecycle, GA/preview page, preview-feature register; `python3 ../enterprise/upgrade/check_model_lifecycle.py --dry-run --params ../infra/main.parameters.prod.json` output filed under `Governance/Operations/{yyyy}-Qn/platform-currency.md` | owner + deputy |
| Semi-annual | re-sync from a fresh claude.ai export when the source skills changed (F6); restore test per `BACKUP_DR.md` §6 (agents and knowledge stores rebuild from the export; `vs-assurance-memory` restores from the `backup_vector_stores.py` export) | owner |
| Annual | full review of this process and of `HUMAN_APPROVAL.md` / `DATA_PROTECTION_GUARDRAILS.md`; ISO 42001 AI-system impact assessment refresh for the deployer role | owner + ISMS |

## 10. Shared deltas needed by this process (not applied here)

| Id | Target | Literal text |
|---|---|---|
| D-OPS-G1 | `.github/workflows/ci.yml` (repo root) | **Applied** — `.github/workflows/ci.yml` (job `gates`: convert_skills → verify_conversion → verify_kit → `convertion/ci/syntax_check.sh` → `convertion/infra/validate.sh` → `run_evals.py --dry-run` + `--emit-plans` → `check_model_lifecycle.py` + `learning_loop.py` → `./deploy.sh --dry-run`; job `secret-scan`: gitleaks over tree and history; job `deploy` on push to `main`, `environment: production`, `permissions: id-token: write`, `azure/login@v2` with the federated credential of `{app:infosec-foundry-deployer}`, `STRICT_RUNTIME=1`, `LIFECYCLE_STRICT=1`, publishes `build/agent-versions.json`). Azure DevOps equivalent: `convertion/ci/azure-pipelines.yml`. Documentation: `convertion/ci/README.md`. |
| D-OPS-G2 | `CODEOWNERS` (repo root, new) | `convertion/ @{github:francisco-gomes}` and `convertion/team/ convertion/operations/ convertion/governance/ @{github:francisco-gomes} @{github:deputy-approver}` with branch protection "require review from Code Owners, dismiss stale reviews, no self-approval" |
