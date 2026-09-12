# Quarterly Access Review — Checklist and Evidence

Cadence: first two weeks of each quarter. Reviewer of the user-facing
groups = the owner; reviewer of anything that grants the owner privilege
= `{upn:line-manager}` (ISO/IEC 27001:2022 A.5.18 "reviewed at planned
intervals", A.8.2 privileged rights, A.5.35 independent review; DORA
Art. 9(4)(c) periodic review of access rights; NIS2 Art. 21(2)(i)).
Evidence folder: SharePoint `Governance/AccessReviews/{yyyy}-Q{n}/`.
Model of record: `../../team/TEAM_MODEL.md` §15 (this checklist implements
its items 1–15); collectors `scripts/access_snapshot.sh` and
`../../team/access-review.sh` are read-only.

## Checklist

| # | Item | Source of truth | Collected by | Reviewer | Pass criterion | Action on fail |
|---|---|---|---|---|---|---|
| 1 | `sg-infosec-foundry-users`, `-report-approvers` membership | Entra access review + `scripts/access_snapshot.sh` (`groups-*.json`) | script | owner | Exactly the current team members; joiners attested; no leavers | Remove; file leaver runbook |
| 2 | `sg-infosec-foundry-owner`, `-senior-approvers`, `-admin-pim`, `-breakglass` membership and eligibilities | Entra access review (PIM for Groups) | `{group:iam-admins}` | line manager | Owner (+ deputy where designed) only; `-admin-pim` and `-breakglass` have no active members | Remove; incident if unexpected |
| 3 | Azure role assignments in `rg-infosec-foundry` | `access_snapshot.sh` (`role-assignments.json`) vs `team/rbac.bicep` | script | owner | No direct user assignments; no permanent privileged role on a group (unless `enablePim=false` exception recorded); every assignment maps to a ledger row | Redeploy `rbac.bicep`; investigate origin in Activity Log |
| 4 | PIM activation history (`-admin-pim`, `-breakglass`) | PIM audit log | `{group:iam-admins}` | line manager | Every activation has ticket + justification; break-glass activations have the owner's post-review | Follow-up with activator |
| 5 | SharePoint site permissions (site groups, unique permissions on `Reports/`, `Templates/`, `Governance/`) and `Sites.Selected` grants | Site permissions export; Graph `GET /sites/{siteId}/permissions` | owner | owner (line manager for the owner's own site role) | Matches `team/TEAM_MODEL.md` §9; exactly three `Sites.Selected` grants (Function MI write, project MI read, Logic App MI read — write only while ledger row L12x is open) | Remove extra grants |
| 6 | Graph application permissions on the Foundry project MI and the Logic App MI | Entra enterprise app → permissions | `{group:iam-admins}` | owner | Read-only set of `team/TEAM_MODEL.md` §8; no `*.ReadWrite.*`, no `Sites.Read.All` / `Sites.ReadWrite.All` on any identity | Revoke consent |
| 7 | Foundry connections and service accounts | Foundry Management center; Key Vault secret list (`kv-secrets.json`) | owner | deputy (independent check) | All secrets within rotation window; every connection has a custodian; `write_connections` empty in `integrations/registry.json` | Rotate; disable connection until rotated |
| 8 | Live agent definitions vs approved build | `scripts/verify_conversion.py` + live instruction hash compare | owner | deputy | No unexplained drift (instructions, tools, model tier) | Re-run `deploy.sh`; investigate |
| 9 | GitHub repository | Collaborators/teams, branch protection, environment protection, secret scanning | owner | line manager | Owner Maintain + CODEOWNERS; deputy Write; users Read; `prod` environment approval on; OIDC only | Fix settings |
| 10 | Copilot Studio agent sharing and DLP | Copilot Studio admin | owner | owner | Shared with `sg-infosec-foundry-users` only; delegated auth; DLP policy in place | Unshare |
| 11 | Shared memory store | `memory_store.py list` | owner | deputy | Notes conform to `team/TEAM_MODEL.md` §13; stale/superseded notes deleted; count reported to DPO | Delete (author, or owner via recorded `MEMORY_DELETE`) |
| 12 | Threads older than 90 days with approved deliverables | Thread list (`threads.json`) | owner | owner | Deleted or justified (open engagement / audit hold) | Delete |
| 13 | Approval sampling | `{list:ApprovalDecisions}` export: 10 % of Tier A decisions + 100 % of Tier B fallbacks (`ruleId=tierB-fallback-peer-after-2bd`) compared with the stored deliverable | deputy | owner (deputy for the owner's own approvals) | Every sampled decision matches the stored deliverable; no approver = requester row; fallbacks justified | Finding per decision; routing or training action; RUNBOOK FM-20 if the flow let approver = requester through |
| 14 | Additions ledger re-confirmation | `team/TEAM_MODEL.md` §5 (L1–L16) | owner | line manager | Every row still justified | Remove the grant |
| 15 | Conditional Access policy `CA-InfoSec-Foundry` | Entra CA | Entra IAM team | owner | Enabled, MFA + compliant device, scoped to the groups | Fix policy |

## Evidence layout

```
Governance/AccessReviews/{yyyy}-Q{n}/
├── snapshot/                  ← access_snapshot.sh output (json + table)
│   ├── groups-*.json
│   ├── role-assignments.json
│   ├── pim-eligibilities.json
│   ├── site-permissions.json
│   ├── kv-secrets.json        ← names + dates only, never values
│   ├── github-collaborators.json
│   └── threads.json
├── entra-access-review-{groups}.pdf
├── pim-activations-{yyyy}-Q{n}.csv
├── approval-sampling.md       ← item 13 results (Tier A sample, Tier B fallbacks)
├── ledger-confirmation.md     ← L1–L16 with reviewer initials and date
└── sign-off.md                ← owner + line manager, date, open actions
```

Retention: 5 years (ISMS record schedule; DORA Art. 28 evidence).

## Sign-off template (`sign-off.md`)

| Field | Value |
|---|---|
| Quarter | `{yyyy}-Q{n}` |
| Reviewer (user groups, items 1, 3, 5–12, 15) | `{upn:francisco.gomes}` — date |
| Reviewer (privileged groups, items 2, 4, 9, 14) | `{upn:line-manager}` — date |
| Independent checks (items 7, 8, 11, 13) | `{upn:deputy-approver}` — date |
| Findings | table: item, finding, action, owner, due date |
| Ledger rows removed / added | list |
| Next review | date |
