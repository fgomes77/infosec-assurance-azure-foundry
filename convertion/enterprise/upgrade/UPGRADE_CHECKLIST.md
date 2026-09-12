# Upgrade / Update Checklist — One Form per Change

Fill one copy per change and paste it into the PR description (and
`Governance/Changes/{ticket}.md`). Binding policy:
`../UPDATE_AND_UPGRADE_REVIEW_POLICY.md` — **no implementation before the
owner's approval**; deputy review when the owner authored. Process detail:
`../../operations/CHANGE_MANAGEMENT.md` §3; objects and version ids:
`../../operations/LIFECYCLE.md`. Placeholders in `{braces}` only — no
secrets, hostnames, e-mails or object ids anywhere in this form.

```
=====================================================================
UPGRADE / UPDATE CHECKLIST                      ticket: {jira:INFOSEC-PLAT}-nnn
=====================================================================
Title:              <verb> <object>  (e.g. "Bump light tier gpt-4o-mini 2024-07-18 -> {version}")
Proposer:           {upn:name}                Date opened: {yyyy-mm-dd}
Author:             {upn:name}                Owner-authored?  yes | no
Reviewer:           {upn:deputy-approver} (owner-authored) | {upn:francisco.gomes}
Approver:           {upn:francisco.gomes}  (production environment approval)
Origin:             learning proposal {yyyy-mm} item n | platform currency review Q{n} |
                    retirement notice | incident {id} | user request | vendor change | other
Requirement(s):     a b c d d2 e f g h i j   (REQUIREMENTS.md)
Release bump:       major | minor | patch     (LIFECYCLE.md §2)

---------------------------------------------------------------------
1. CLASS (policy §1) — tick one primary, list secondary
---------------------------------------------------------------------
[ ] C1  model version / deployment        [ ] C8  workflows / pipelines
[ ] C2  API / SDK / runtime versions      [ ] C9  Function code / images
[ ] C3  platform feature (GA/preview)     [ ] C10 infrastructure
[ ] C4  instructions / persona / verifier [ ] C11 RBAC / groups / identities
[ ] C5  registry tools / tiers            [ ] C12 connections / secrets
[ ] C6  templates (j)                     [ ] C13 docs / runbooks only
[ ] C7  knowledge sources
Risk class (CHANGE_MANAGEMENT §5):  low | medium | high
Preview feature involved?  no | yes -> register row: {capability}, exit criterion: {…},
                           compensating control: {…}, on the approval path? MUST be "no"

---------------------------------------------------------------------
2. WHAT CHANGES (before -> after; files; live objects)
---------------------------------------------------------------------
Files:              {path} … 
Live objects:       agent {name}:{old version} -> {new version} | deployment {name} {old} -> {new} |
                    connection {conn-…} | workflow {name} | template {id} v{old} -> v{new} | …
Environments:       dev {baseName}-proj(dev)  ->  test (staged: {agent|pipeline|tier|candidate}) -> prod
Users informed:     {teams:infosec-assurance-platform} post on {date}

---------------------------------------------------------------------
3. INVARIANTS — every line must read "unchanged" (else: risk-acceptance, not a change)
---------------------------------------------------------------------
read-only agents ............... unchanged | WEAKENED (stop)
approval before any write ...... unchanged | WEAKENED (stop)
taxonomy / templates contract .. unchanged | WEAKENED (stop)
identities (Entra-only, PIM) ... unchanged | WEAKENED (stop)
EU residency (DataZone/EU) ..... unchanged | WEAKENED (stop)
no egress (DATA_PROTECTION §1) . unchanged | WEAKENED (stop)
Why (high risk only): …

---------------------------------------------------------------------
4. STANDING RULES (policy §3) — evidence per rule
---------------------------------------------------------------------
R1 pins:      versionUpgradeOption NoAutoUpgrade on all deployments  [ ]  explicit versions [ ]
              (`python3 enterprise/upgrade/check_model_lifecycle.py --dry-run` -> 0 ERROR, output attached)
R2 retire:    days to retirement of every model touched: {n} (ticket ≥ 120 days rule met? yes | n/a)
R3 method:    six phases documented (C1 only): Discover [ ] Assess [ ] Adapt [ ] Validate [ ] Roll out [ ] Retire [ ]
R4 tools:     tool-support row pasted (model, region, OpenAPI/MCP/AI Search/SharePoint/Web Search):
              {row}   -> all tools of the tier supported? yes | no (stop)
R5 versions:  new immutable agent version(s): {name}:{version}; active version set by the owner [ ];
              pipelines / Copilot reference updated [ ]
R6 one kind:  no model + SDK change in the same release [ ]
R7 preview:   none on the approval path [ ]
R8 EU:        deploymentSku {DataZoneStandard|Standard}; region {eu-region}; data location unchanged [ ]
R9 portal:    nothing set by hand in the portal [ ]

---------------------------------------------------------------------
5. EVIDENCE — mandatory per class (policy §1); "n/a" only where the class allows
---------------------------------------------------------------------
[ ] verify_conversion.py .............. PASS      log tail: …
[ ] <script> --dry-run ................ create_agents | create_delivery_agents | create_orchestrator |
                                        attach_integrations ([read-only] on every tool) | update_templates |
                                        deploy.sh | provision_identity.sh --plan   -> clean
[ ] py_compile / json.tool / yaml ..... clean
[ ] bicep build + infra/validate.sh ... clean       what-if delta (C1/C10): {n} create / {n} modify / {n} delete
[ ] Eval baseline vs candidate ........ run_evals.py --agent … --out build/evals/{ticket}-control
                                        run_evals.py … --model-override … --out build/evals/{ticket}-candidate
                                        gate candidate: PASS | FAIL ; metrics below floor: none | {list}
[ ] Comparison set (report agents) .... pipelines: {list}; verifier PASS first attempt: yes; structure/threshold/
                                        section drift: none; wording delta signed by: {upn:name}
[ ] Security review ................... invariants stated (§3); access-review.sh --quick clean; new scopes: none | {…}
[ ] Cost ............................. unit-cost delta (FINOPS.md): {+/-…} / month; budget impact: none | {…}
[ ] check_model_lifecycle.py .......... attached (C1, C2, quarterly)
[ ] Knowledge intake form ............. knowledge-refresh.md §3 rows 1-9 (C7)
[ ] Template approval run ............. template-update-approval run id {run-id} (C6)
[ ] Access snapshot before/after ...... (C11) attached
[ ] Custodian confirmation ............ (C12) read-only scope confirmed by {upn:custodian}

---------------------------------------------------------------------
6. ROLLOUT PLAN
---------------------------------------------------------------------
dev:    deployed {date}; gates green [ ]
test:   staged object {…}; observation {start}-{end} (≥ 1 week for tiers/models);
        checks: Q1 not below previous week [ ]  no new verifier FAIL category [ ]  no alert [ ]
prod:   deploy command: deploy.sh | attach_integrations.py --only … | update_templates.py … | rbac.bicep | pipeline
        window: {date}; owner approval of the production environment [ ]
post:   RUNBOOK W1-W4 by {date}; drift baseline build/baseline-{date}.json [ ]; Copilot republish [ ] n/a [ ]

---------------------------------------------------------------------
7. ROLLBACK (tested once in dev before prod for C1 / C10)
---------------------------------------------------------------------
Command / action:   switch active version back to {name}:{old} | attach_integrations.py --only … (old tier) |
                    checkout platform/v{old} && ./deploy.sh | update_templates.py (backup + new approval) |
                    what-if of previous commit + redeploy | previous secret version
Previous object kept until: {date}  (models: 7 days after zero requests; secrets: next rotation)
Rollback tested in dev on: {date}  by {upn:name}

---------------------------------------------------------------------
8. EMERGENCY (only if an open P1/P2 — policy §5; CHANGE_MANAGEMENT §8)
---------------------------------------------------------------------
Incident:           {id}      Minimum change: disable {object} | other: …
PIM activation:     {date-time}, justification = ticket id      Deputy review within 2 h: {date-time}
Retrospective PR:   {pr} within 1 business day     Secret rotated if read: yes | n/a

---------------------------------------------------------------------
9. RECORDS (policy §6)
---------------------------------------------------------------------
Decision:           approved | rejected | deferred (revisit {date})  by {upn:francisco.gomes} on {date}
Deputy review:      {upn:deputy-approver} on {date}   (owner-authored only)
Release tag:        platform/v{…}     ARM deployment: {release}-{yyyymmdd}
Evidence links:     PR {…}; Actions run {…}; eval reports {…}; Governance/Changes/{ticket}.md
Control refs:       ISO 27001:2022 A.8.32, A.8.9, A.8.29, A.8.31; ISO 42001 A.6.2.4-A.6.2.5;
                    DORA Art. 9(4)(e), Art. 10; EU AI Act Art. 9, Art. 14, Art. 26
=====================================================================
```

## Quick reference — which evidence for which class

| Class | Dry-run | Eval baseline vs candidate | Comparison set | Security review | Cost | Extra |
|---|---|---|---|---|---|---|
| C1 model version / deployment | `infra/validate.sh` + `what-if` | required (`--model-override`) | every affected pipeline | required | required | `check_model_lifecycle.py`; tool-support row; staged 1 week |
| C2 API / SDK / runtime | every script `--dry-run`; `py_compile`; Function local run | affected agents | report agents if behaviour changed | required (CVEs) | optional | changelog cited; never with C1 |
| C3 platform feature | as the feature's IaC/script | affected agents | if output path changes | required | required | preview register row; DPA/terms; RoPA if data flow changes |
| C4 instructions / verifier | `create_*.py --dry-run`; `verify_conversion.py` | required | report agents | verifier rules = high | — | new agent version |
| C5 registry | `attach_integrations.py --dry-run` `[read-only]` | tier changes | tier changes on report agents | required; `write_connections` = line manager | tier changes | tool-support row |
| C6 templates | `update_templates.py --dry-run` | affected consumers | required | — | — | approval run id |
| C7 knowledge | `create_*.py --dry-run` | required | advisors g/h/i | intake form rows 2, 3, 6 | — | provenance in file header |
| C8 workflows | JSON parse; `package_workflows.py` | — | one run to the verifier in test | required if approval step changes | — | `HUMAN_APPROVAL.md` table |
| C9 Function / images | `py_compile`; `func` local | — | `/render` smoke via comparison set | required | — | image scan |
| C10 infrastructure | `infra/validate.sh` + `what-if` | — | — | required | required | rollback tested in dev |
| C11 RBAC / identities | `provision_identity.sh --plan`; `what-if` | — | — | required; line manager for privileged | — | snapshot before/after |
| C12 connections / secrets | connection smoke test | — | — | custodian | — | register row |
| C13 docs | markdown renders; links | — | — | — | — | — |

Sources for the platform rules referenced in the form: see
`../UPDATE_AND_UPGRADE_REVIEW_POLICY.md` §7 (retirement schedule 2026-09-02,
`versionUpgradeOption` 2026-06-05, tool-support table 2026-09-07, model
migration 2026-08-26, agent versioning 2026-08-27 — all GA as of 2026-09-12).
