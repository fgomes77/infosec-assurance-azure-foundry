# Approval Routing — Who Approves What, Segregation of Duties, Break-Glass

Extends `../../governance/HUMAN_APPROVAL.md` (which says *that* every
submission of record needs a human) with *who* that human is. The
approval flow behind `approvalWebhookUrl` (Power Automate or the approval
Function) reads `approvals/routing.json` and resolves the approver set at
run time; the Logic Apps gates stay unchanged.

## 1. Approval tiers

| Tier | What | Minimum approver | Rule | Why this tier |
|---|---|---|---|---|
| **1 — Four-eyes peer** | Reports that leave the team or bind a stakeholder: **b** DPO report, **c** Cyber Forum deck, **d** Global CISO deck; every Jira issue creation and IAF submission (`defender-incident-brief`, `scheduled-deepsearch` ticket branch, `jira-finding-sync`); scheduled runs with no human requester (`onetrust-assessment-intake`, `scheduled-deepsearch` upload) | One member of `sg-infosec-foundry-report-approvers` **who is not the requester** | Approver ≠ requester enforced by the flow (requester UPN from `requestedBy`); the owner's reports are approved by a peer like anyone else's | External audience or record of record: an author cannot be the sole check on a document a CISO or the DPO will act on (EU AI Act Art. 14; ISO 27001 A.5.3) |
| **2 — Author sign-off** | Internal working papers stored under `Reports/<Supplier>/<Service>/`: **a** DeepSearch, **d2** evidence analysis, **e** SOC summary, **f** pentest summary | The requesting assurance user (a natural person reviewing the verifier-passed draft) | Requester approves own run; **escalates to tier 1** when the report is attached to a supplier risk decision, shared outside the team, or the requester marks `stakeholderFacing: true` at trigger time; peer sampling of 10 % per quarter (`../../operations/access-governance/`) | Minimum that still satisfies "human approval before any write"; these reports are inputs to the analyst's own work, and a second approver on every SOC summary would slow the team without changing the risk. Sampling catches drift |
| **3 — Owner only** | Template changes (`template-update-approval`, kind `TEMPLATE_UPDATE`); platform changes: Bicep, `integrations/registry.json` (tools, `model_tier`, `write_connections`), OpenAPI specs, workflow definitions, `agents/*_instructions.md`, `persona_system_prompt.md`, knowledge packs, Graph permission consents, Key Vault secret scope, group membership of privileged groups; memory **deletions** not by the author | `{upn:francisco.gomes}` | If the requester is the owner → `{upn:deputy-approver}` approves (SoD). Platform changes additionally need a GitHub PR review (owner reviews users' and deputy's PRs; deputy reviews the owner's) | Configuration of record affects every user's outputs; one accountable approver, with an independent reviewer for his own changes (A.5.3, DORA Art. 9(4)(e)) |
| **Never auto-approved** | Anything above | — | Break-glass grants *access*, never approval; expiry (P3D reports, P7D templates) rejects | `../../governance/HUMAN_APPROVAL.md` Layer 3 |

Threshold or scoring changes inside a template (moving the TPRM red band)
remain tier 3 **plus** the explicit methodology confirmation the
template-manager charter already requires.

## 2. Routing matrix (as implemented in `approvals/routing.json`)

| `kind` (from the gate's subscribe body) | Approver set | Exclusions | Timeout | Fallback when set is empty |
|---|---|---|---|---|
| `REPORT_DELIVERY` with `reportType` in {InfoSecTPA-DPO, CyberForum, CISOGlobal} | `sg-infosec-foundry-report-approvers` | requester | P3D | escalate to `{upn:francisco.gomes}`; if requester = owner, escalate to `{upn:deputy-approver}` |
| `REPORT_DELIVERY` with `reportType` in {DeepSearch, EvidenceAnalysis, SOCSummary, PentestSummary} and `stakeholderFacing` ≠ true | the requester | — | P3D | if no requester (scheduled) → tier 1 set |
| `REPORT_DELIVERY` with `stakeholderFacing` = true | tier 1 set | requester | P3D | as tier 1 |
| `JIRA_CREATE`, `IAF_SUBMIT` | `sg-infosec-foundry-report-approvers` | requester | P3D | as tier 1 |
| `TEMPLATE_UPDATE` | `{upn:francisco.gomes}` | — | P7D | requester = owner → `{upn:deputy-approver}` |
| `PLATFORM_CHANGE` (GitHub PR + deployment environment `prod`) | CODEOWNERS (`{upn:francisco.gomes}`) | PR author | none (PR stays open) | author = owner → `{upn:deputy-approver}` |
| `MEMORY_DELETE` (not by author) | `{upn:francisco.gomes}` | — | P7D | — |

Every decision callback carries `{"decision", "approver", "correlationId",
"tier", "timestamp"}`; the Logic Apps run history plus the flow's own log
are the evidence (DORA Art. 28 retention ≥ 1 year via Log Analytics).

## 3. Segregation of duties for the owner

| Situation | Who approves | Mechanism |
|---|---|---|
| Owner requests a report (any tier 1 report) | A peer from `sg-infosec-foundry-report-approvers` | Requester exclusion in routing |
| Owner proposes a template change | `{upn:deputy-approver}` | `TEMPLATE_UPDATE` fallback rule |
| Owner opens a platform PR | `{upn:deputy-approver}` reviews; owner still merges (accountable) | Branch protection: required review, author cannot self-approve; deputy has `Write` |
| Owner rotates a credential | Owner executes; deputy verifies the rotation ticket closes with the Key Vault version id | Quarterly review sample |
| Owner deletes another user's memory note | Owner executes after a `MEMORY_DELETE` approval by the note author or, if unavailable, the deputy | `memory_store.py delete` recorded with file id + reason |
| Owner activates PIM | Self-activation with justification; no approver required (would block daily maintenance) | Activation alerts to `{upn:line-manager}`; monthly PIM report reviewed by line manager |

The owner never approves his own change; the deputy never approves a
change he authored; neither can add members to `sg-infosec-foundry-platform-approvers`
or `-platform-admins` (Entra IAM team owns those groups).

## 4. Break-glass

| Element | Rule |
|---|---|
| Trigger | Owner unavailable > 2 business days with a pending tier-3 approval or a platform incident (P1/P2), or an incident requiring immediate disabling of a workflow/connection |
| Who | `{upn:deputy-approver}` activates eligible membership of `sg-infosec-foundry-breakglass` (grants the platform-admin role set) |
| Approval | PIM activation approved by `{upn:line-manager}` (or `{upn:ciso-delegate}`), justification = ticket id |
| Duration | 8 h max, single activation per incident, MFA required |
| What it does **not** do | It does not approve anything: tier-1/3 approvals still need a human in the routing table; the deputy may *disable* (a workflow, a connection, an agent) without approval, but may *change* only with the owner's retrospective approval |
| After | Owner reviews the Activity Log and Foundry tracing of the window within 5 business days; a break-glass report goes to `Governance/AccessReviews/` |
| Runbook | `../../operations/access-governance/BREAK_GLASS.md` |

## 5. Approval evidence (what an auditor sees)

| Evidence | Where |
|---|---|
| Decision, approver UPN, timestamp, correlation id | Logic Apps run history (`Wait_for_approval_*` outputs) + Log Analytics export |
| The draft that was approved | Foundry thread (messages + verifier verdict), report version in SharePoint |
| Routing rule in force at the time | `approvals/routing.json` git history |
| Who could have approved | `sg-infosec-foundry-*` membership snapshot from the quarterly review |
| Segregation exceptions (break-glass) | PIM activation history + break-glass report |
