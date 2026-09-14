# Access governance — the ADMIN side of the team model

This folder holds the **operator runbooks**: what the platform owner and the
Entra IAM team execute, and the evidence each step files. It deliberately
contains **no model** — the team, roles, groups, RBAC and approval tiers are
defined once, in `../../team/`, and are only referenced here.

| Question | Here | Model of record |
|---|---|---|
| Who is on the team, which groups exist, which role goes where | — | `../../team/TEAM_MODEL.md` (§1 roles, §6 groups, §7 RBAC, §12 approvals) |
| Who does what across the lifecycle | — | `../../team/RACI.md` |
| What a **joiner / leaver** personally does and attests | — | `../../team/ONBOARDING.md`, `../../team/OFFBOARDING.md` |
| What the **admin** executes for a joiner / mover / leaver, with evidence | `ACCESS_LIFECYCLE.md` | (runs `../../team/TEAM_MODEL.md` §14) |
| How the quarterly review is run, item by item, with sign-off | `QUARTERLY_ACCESS_REVIEW.md` | (runs `../../team/TEAM_MODEL.md` §15) |
| Emergency access when the owner is unavailable | `BREAK_GLASS.md` | (group and PIM design: `../../team/TEAM_MODEL.md` §6, §5 L10) |
| Evidence commands (`access_snapshot.sh`) | `scripts/` | — |
| Group creation, PIM settings, CA policy, access packages, Entra access reviews | — | `../../team/entra-groups.md` |
| SharePoint site roles and the `Sites.Selected` grants | — | `../../team/sharepoint-permissions.md` |
| Group definitions as data + provisioning script | — | `../../team/least-privilege/entra/groups.json`, `.../scripts/provision_identity.sh` |
| Live identity inventory (people, groups, MIs, Entra Agent IDs, clients) | — | `../../team/ACCESS_REGISTER.md` |

**Rule against duplication:** if a fact about *who may do what* appears both
here and in `../../team/`, `../../team/` wins and the copy here must be
replaced by a link. Role display names follow the current Foundry RBAC naming
(Foundry User / Foundry Owner / Foundry Account Owner / Foundry Project
Manager); the role definition GUIDs in `../../team/rbac.bicep` are unchanged.

Note that `../../team/least-privilege/` is a **historical design variant** with
a different vocabulary (six groups, approval tiers 1/2/3) — never quote it in a
runbook; see its `README.md` for the name mapping.
