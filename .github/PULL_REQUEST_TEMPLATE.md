<!--
Review checklist for the InfoSec Assurance Foundry kit
(convertion/operations/CHANGE_MANAGEMENT.md §3 "PR" and §4 "Evidence";
delta D-OPS-G2). The reviewer is the deputy for owner-authored PRs and the
accountable owner for everyone else's (.github/CODEOWNERS, RACI R20).

Delete nothing. An item that does not apply is ticked `[n/a]` with the reason
on the same line — a blank box reads as "not checked", not as "not relevant".
-->

## What changes, and why

<!-- One paragraph. What a reader of the repository in a year needs to know. -->

**Change class** (convertion/operations/LIFECYCLE.md):
`patch` / `minor` / `major` — <!-- pick one -->

**Tier** (convertion/team/TEAM_MODEL.md §12.1):
`A — self-service` / `B — peer-approved` / `C — owner-only` — <!-- pick one -->

**Findings / deltas addressed:** <!-- e.g. C4, C19, D-OPS-G1 — or `none` -->

---

## Gates

CI runs all of these; tick them because you looked at the result, not because
the check mark was green.

- [ ] `gates` job green — convert → verify_conversion → verify_kit → syntax →
      residency → infra policy → evaluation → platform currency → `deploy.sh --dry-run`
- [ ] `secret-scan` job green — gitleaks over the working tree **and** the history
- [ ] Ran locally what CI cannot: `pre-commit run --all-files`, or the specific
      gate this change touches

## Data protection and residency

- [ ] No secret, token, connection string, real hostname, UPN or e-mail address
      is added anywhere. Everything identifying is a documented placeholder
      (`{upn:...}`, `<tenant>`, `${VAR}`) or a `@Microsoft.KeyVault(...)` reference
- [ ] No allow-list in `.github/gitleaks.toml` was widened. (If it was: say which
      entry and why the value is provably not a secret)
- [ ] Every region this change can select is EU/EEA —
      `python3 convertion/ci/tests/test_residency.py` passes, and any new region
      added to an `@allowed` list is justified below
- [ ] No Euronext or supplier data is sent to a web-facing service; any new
      outbound call is sanitised and documented in
      `convertion/governance/DATA_PROTECTION_GUARDRAILS.md` §1

## Least privilege and approval

- [ ] Enterprise access stays **read-only**: no new tool without
      `readOnlyHint=true`, no OpenAPI operation beyond GET, no
      `write_connections` grant
- [ ] Every write still goes through the verifier **and** a human approval gate
      (`convertion/governance/HUMAN_APPROVAL.md`); no gate was bypassed or relaxed
- [ ] Identities are managed identities / OIDC federated credentials — no client
      secret, no stored credential, no key in a workflow
- [ ] Delivery still writes only to SharePoint `Reports/<Supplier>/<Service>/`
      via the delivery Function
- [ ] RBAC, group membership and approval routing are unchanged — or the change
      is reflected in `convertion/team/ACCESS_REGISTER.md`,
      `least-privilege/entra/groups.json` and `approval-policy.json`, and the
      deputy is on this review

## Platform currency (2026)

- [ ] Responses API only — no classic threads/runs, no Connected Agents, one
      vector store per agent, reasoning tier stays tool-capable
- [ ] No retired pattern reintroduced (`convertion/enterprise/` is the reference)
- [ ] Model deployments stay version-pinned with `NoAutoUpgrade`; a tier change
      is a Tier C change and names its lifecycle evidence

## Consistency

- [ ] Documentation updated in the same commit — the README/table/checklist that
      describes what changed, not a follow-up PR
- [ ] GitHub Actions and `convertion/ci/azure-pipelines.yml` still run the same
      steps in the same order (they call the same scripts on purpose)
- [ ] `convertion/claude-account-export/` and `convertion/build/` untouched
      (byte-verified fidelity / generated output)
- [ ] Cross-references resolve — `verify_kit.py` covers the kit; check any link
      you added to a path outside it by hand

## Evidence attached

<!--
CHANGE_MANAGEMENT.md §4: the artefacts that make this reviewable. Paste the
run URL, or the relevant lines of output — not a screenshot of a green tick.
-->

- CI run:
- Dry-run / gate output that matters:
- For a Tier C change — approval record:

## Rollback

<!-- How this is undone, in one line. "Revert the commit" is a valid answer
     only when nothing was applied to the tenant. -->
