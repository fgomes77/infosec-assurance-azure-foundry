# Access Lifecycle — Joiner / Mover / Leaver Runbook

Runbook for `../../team/TEAM_MODEL.md` §14 (joiner / mover / leaver);
person-centric checklists in `../../team/ONBOARDING.md` and
`../../team/OFFBOARDING.md`. Controls:
ISO/IEC 27001:2022 A.5.16 (identity management), A.5.18 (access rights),
A.6.5 (termination), A.8.2 (privileged access); DORA Art. 9(4)(c); NIS2
Art. 21(2)(i). Evidence for every step lands in the SharePoint site
folder `Governance/AccessLifecycle/{yyyy}/` as the ticket export plus the
`access_snapshot.sh` output.


> Role names follow the current Foundry RBAC naming (Foundry User / Foundry Owner /
> Foundry Account Owner / Foundry Project Manager); the underlying role definition
> GUIDs in `rbac.bicep` are unchanged — `enterprise/ENTERPRISE_BLUEPRINT.md` ID-1.

## 1. Joiner — new assurance user (target: same day)

| # | Step | Who | Tool / evidence | Least-privilege check |
|---|---|---|---|---|
| 1 | Line manager requests access package `AP-InfoSec-Foundry-User` (or a ticket `{jira:INFOSEC-PLAT}` if entitlement management is unavailable) | `{upn:line-manager}` | Entra entitlement management request id | Request states the business need: member of the InfoSec Assurance team using systems a–j |
| 2 | Owner approves → membership of `sg-infosec-foundry-users` (grants `Foundry User`, SharePoint Members with Read on `Reports/`/`Templates/`, Copilot agent, MCP, CA policy scope) | `{upn:francisco.gomes}` | Access package approval record | Nothing else is granted at this step |
| 3 | Joiner completes onboarding: reads `governance/*.md`, `sharepoint/README.md`, `team/USER_QUICKSTART.md`, `team/TEAM_MODEL.md` §1, §12, §13; runs the MCP server locally with own `az login`; produces one Tier A report end-to-end (a peer approves) and shadow-reviews one peer's Tier A draft (`team/ONBOARDING.md` §4) | joiner + a peer | Attestation form `Governance/Onboarding/{upn}.md` (date, systems exercised, peer) | EU AI Act Art. 26(2) competence of the natural person exercising oversight |
| 4 | Owner adds the joiner to `sg-infosec-foundry-report-approvers` | `{upn:francisco.gomes}` | Group change (Entra audit log) | Approver rights only after attestation |
| 5 | Owner adds to Teams channels `{teams:infosec-assurance-platform}` and `{teams:infosec-assurance-approvals}`, GitHub team `infosec-assurance-users` (Read) | owner | — | Read-only repo access |
| 6 | Snapshot | owner | `scripts/access_snapshot.sh --tag joiner-{upn}` | Confirms exactly two group memberships |

## 2. Mover — role change within the team

| Case | Action | Who |
|---|---|---|
| User becomes deputy approver | Owner nominates, line manager confirms; `{group:iam-admins}` adds to `sg-infosec-foundry-senior-approvers` and sets PIM eligibility in `sg-infosec-foundry-breakglass` (both owned by the line manager); GitHub `Write` for PR review; CODEOWNERS entry; update `team/least-privilege/entra/groups.json` and `team/approval-policy.json` (`principals.deputy`) via a PR reviewed by the owner; `team/ACCESS_REGISTER.md` Deputy row | owner, line manager, Entra IAM team |
| Deputy steps down | Reverse of the above; the previous deputy's eligibility is removed the same day | Entra IAM team |
| User moves to another team but keeps an advisory need | Not supported: membership of `sg-infosec-foundry-users` is for InfoSec Assurance team members only; a read-only need is served by shared report links, not by platform access | owner |
| Owner succession | Line manager appoints the successor (normally the deputy); Entra IAM team transfers group ownership and PIM eligibilities; successor becomes CODEOWNERS, SharePoint site owner, Copilot environment maker, connection owner; RoPA entry updated; successor runs `deploy.sh --dry-run` and `provision_identity.sh --verify` as hand-over check; successor also runs `access-review.sh` and files the output as the new Q0 baseline; previous owner is removed from `sg-infosec-foundry-owner`, `-admin-pim` and `-senior-approvers` the same day (`team/TEAM_MODEL.md` §14 hand-over checklist) | line manager, Entra IAM team, successor |

## 3. Leaver (target: same day as HR trigger, never later than the next business day)

| # | Step | Who | Evidence |
|---|---|---|---|
| 1 | HR/IAM trigger removes the account from every `sg-infosec-foundry-*` group (access package expiry or manual removal) — this revokes Foundry, SharePoint, Copilot, MCP and CA scope in one act | Entra IAM team | Entra audit log |
| 2 | Revoke sessions (`Revoke-MgUserSignInSession` / Entra "revoke sessions") so cached data-plane tokens die | Entra IAM team | — |
| 3 | Remove from GitHub team and Teams channels; if the leaver was the deputy, run the deputy-step-down mover case and nominate a replacement within 5 business days | owner | — |
| 4 | Threads: re-tag active engagement threads (`metadata.owner_upn` → new engagement owner) or delete them; delete the leaver's `personal-working` threads; shared memory notes stay (team facts, not personal data) — nothing personal to purge by design (`team/TEAM_MODEL.md` §13) | owner | Thread list before/after |
| 5 | Credentials: none to rotate in the normal case (no human ever holds a platform key). If the leaver activated break-glass in the last 90 days, rotate every Key Vault secret they could have read during the window | owner + custodians | Key Vault version ids |
| 6 | Snapshot and file | owner | `scripts/access_snapshot.sh --tag leaver-{upn}` |

## 4. Quarterly access review

See `QUARTERLY_ACCESS_REVIEW.md` (checklist, reviewers, pass criteria,
evidence layout). The review is also the point where the additions
ledger (`team/TEAM_MODEL.md` §5, rows L1–L16) is re-confirmed row by
row — a row nobody can justify is removed, not renewed.

## 5. Emergency access

See `BREAK_GLASS.md`.
