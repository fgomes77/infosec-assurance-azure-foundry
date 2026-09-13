# CI/CD — gates on every PR, gated deploy on `main`

Nothing reaches the tenant that has not first proved itself on a clean
runner. The pipelines here run the **same scripts** the team runs by hand
(`deploy.sh` steps 1–2, `infra/validate.sh`, `operations/evaluation/run_evals.py`),
so a green pipeline and a green desk are the same statement.

| File | What it is |
|---|---|
| `../../.github/workflows/ci.yml` | GitHub Actions **gates**: jobs `gates` and `secret-scan`, on every PR and every push to `main`. Entirely offline — it never touches Azure |
| `../../.github/workflows/deploy.yml` | The **only** path in the repository that talks to Azure: `workflow_run` after CI succeeds on `main` → `production` environment approval → OIDC federated login → EU-residency assertion → `deploy.sh` |
| `../../.github/workflows/nightly-drift.yml` | Nightly detective control: `verify_deployment.py` (live vs verified build) + `team/access-review.sh` (access snapshot), read-only OIDC identity, no approval |
| `azure-pipelines.yml` | Azure DevOps equivalent of ci.yml **and** deploy.yml — same steps, same order, one file (ADO expresses the dependency as `dependsOn`); register as *existing YAML file* `/convertion/ci/azure-pipelines.yml` |
| `syntax_check.sh` | The syntax gate every pipeline calls: python, json, yaml, toml, javascript, bicep, shell (`bash -n` **and** `shellcheck --severity=warning`). Runnable by hand before a PR; both pipelines install shellcheck and run the gate with `REQUIRE_SHELLCHECK=1`, so the lint can never skip on a runner |
| `tests/test_residency.py` | The EU-residency gate: region allow-lists, parameter files, inference SKUs, the runner's target region, and (`--live`) the regions of the resources that exist. Runs under pytest **and** standalone, so the deploy job can assert residency without pytest installed |
| `deploy_logicapps.sh` | Packages `build/logicapps/` (from `scripts/build_logicapps.py`) and deploys it with `az logicapp deployment source config-zip`; called by `deploy.sh --workflows` |
| `../../.github/gitleaks.toml` | Secret-scan configuration: default rules + allow-list of the kit's documented placeholders. **The single source of rules** |
| `../../.gitleaks.toml` | Root shim: `[extend] path` to the file above, so an invocation without `--config` (pre-commit, `gitleaks protect`) gets the same rules instead of the bare defaults |
| `../../.pre-commit-config.yaml` | Local mirror of the gates — hygiene hooks, gitleaks, and `language: system` hooks calling `syntax_check.sh`, `test_residency.py`, `verify_kit.py` and (pre-push) `deploy.sh --dry-run` |
| `../../.github/PULL_REQUEST_TEMPLATE.md` | The review checklist of `operations/CHANGE_MANAGEMENT.md` §3–§4 as the PR body |
| `../../.github/CODEOWNERS` | Required reviewers: the accountable owner everywhere under `convertion/`, owner **+** deputy on anything that changes privilege, policy or what "green" means |
| `../../.github/dependabot.yml` | Weekly grouped dependency PRs (patch class — `operations/LIFECYCLE.md`) |
| `../../.devcontainer/` | The same toolchain locally: Python 3.12, Node 22, Azure CLI, Bicep 0.47.16, Functions Core Tools v4, gitleaks 8.18.4 |

## 1. The PR gate, in order

| # | Step | Command | Fails when |
|---|---|---|---|
| 1 | Convert | `python3 convertion/scripts/convert_skills.py` | the export cannot be converted |
| 2 | Fidelity | `python3 convertion/scripts/verify_conversion.py` | a knowledge file, code-tree file or zip member no longer matches its source SHA-256, a packaged `.py` fails to compile **or imports at module level something that is neither stdlib, a pin in a Function `requirements.txt`, nor part of the package**, a `require(path.join(__dirname, …))` does not resolve, an instruction lost its rules/persona/approval gate, or a skill is neither converted nor decided. The import check is static resolution, not an import smoke (nothing is executed, and lazy imports behind a CLI fallback are out of scope) — the executing proof is the delivery image build's final `python3 -c "import …"` layer |
| 3 | Kit consistency | `python3 convertion/scripts/verify_kit.py` | a secret, tenant hostname or e-mail address appears under `convertion/`, a JSON/YAML/shell file is unparsable, or a cross-reference is broken |
| 4 | Syntax | `convertion/ci/syntax_check.sh` (`REQUIRE_SHELLCHECK=1`) | any `.py .json .yaml .toml .js .bicep .sh` in the kit fails to compile/parse, **or** shellcheck reports an error/warning in a kit shell script (info/style are advisory; a deliberate exception is an inline `# shellcheck disable=SCxxxx` with a reason, never a lowered severity). Locally the lint degrades to a note when shellcheck is absent — `sudo apt-get install shellcheck` |
| 4b | EU residency | `python3 convertion/ci/tests/test_residency.py` | a Bicep `@allowed` location list, an Azure Policy `allowedLocations` array, a parameter file's `location`, a `deploymentSku`, or the runner's own `AZURE_LOCATION`/endpoint names a region outside the EU/EEA |
| 4c | Self-knowledge pack | `python3 convertion/scripts/build_self_knowledge.py --check` | `agents/knowledge-packs/platform-self-knowledge.md` is stale — an agent, pipeline, template or approval kind changed and the pack that answers "what can this platform do" was not regenerated. Fix by running the script without `--check` and committing the result; the `deploy.sh --dry-run` chain of step 8 deliberately only *reports* staleness, so CI never writes into `agents/` |
| 4d | Function test suites | `python3 -m pytest convertion/functions/delivery/tests convertion/functions/office-tools/tests convertion/scripts/tests -q` | a delivery-Function gate, renderer contract, office-tools handler or the memory privacy filter regresses. Fully offline — `azure.functions` and `azure.identity` are stubbed by the suites and no Azure SDK is needed; the office-tools suite loads its module under a unique name so both Function suites run in one invocation |
| 5 | Infrastructure policy | `convertion/infra/validate.sh` | a module fails `bicep build`, or the parameters break EU residency / pinned model versions / standard agent setup / VNet injection / CMK (findings C5, C6, C11, C12, C22) |
| 6 | Evaluation G0 + plans | `run_evals.py --dry-run` and `--emit-plans` | the golden set is invalid, a fixture fails its own checks, or a metric is below its floor (`operations/evaluation/EVALUATION.md` §5) |
| 7 | Platform currency | `check_model_lifecycle.py --dry-run --horizon 180`, `learning_loop.py --dry-run` | a tier has no pinned model version, a deployed version retires inside the ticket window, or a tier model cannot call the tools its agents are given (finding C4) |
| 8 | Offline dry-run chain | `cd convertion && ./deploy.sh --dry-run` | any step of the real deployment would fail before it touches Azure |
| — | Secret scan (parallel job) | `gitleaks detect` over the working tree **and** the git history | a credential-shaped string that is not an allow-listed placeholder appears anywhere in the repository |

Every artefact the gates produce (`build/manifest.json`,
`build/lifecycle-report.json`, `build/evals/**`, the redacted gitleaks SARIF)
is uploaded as the change record for `operations/CHANGE_MANAGEMENT.md` §6
step 6 — `build/` is git-ignored, so the pipeline artefact is the evidence.

**Known red gates.** The pipeline is deliberately honest: step 7 fails today
because the `reasoning` tier is pinned to a model that supports none of the
OpenAPI / MCP / AI Search / Web Search tools its agents are given (finding
C4, re-selection is a Tier C change), and step 3 fails while the template
assets listed in `templates/registry.json` are missing. Neither is worked
around here — fix the cause, do not weaken the gate.

## 2. Deploy on `main`

Deployment is its own workflow (`.github/workflows/deploy.yml`), not a job in
`ci.yml`. The split is the point: `ci.yml` can then be read as what it is — a
gate that never authenticates to anything — and the two files are separately
listed in `CODEOWNERS`, so a change to the deployment path shows up as such in
the review request. GitHub chains them with `workflow_run` (deploy fires only
for a **completed, successful** CI run on `main`, and checks out
`workflow_run.head_sha` so it deploys the commit CI actually verified). Azure
DevOps keeps both in one pipeline, where `dependsOn: gates` says the same
thing.

The `deploy` job/stage runs only on a push to `main`, only after the gates
and the secret scan are green, only after the EU-residency assertion passes
both offline and `--live` against the resource group, and only after the
**`production` environment** approval — the accountable owner is the approver
(`team/TEAM_MODEL.md` F5, ledger L11). It then runs `deploy.sh` unchanged
with `STRICT_RUNTIME=1`, so a runner still pinned to the retiring classic
threads/runs SDK fails instead of silently deploying on it (finding C1).
Afterwards it publishes `build/agent-versions.json` — the promoted
`<agent>:<version>` of every agent that release created, which pipelines pin
and the nightly `verify_deployment.py` compares against (finding C19).

### Credential: OIDC federated credential, no secret

The repository stores **no secret**. The deploy identity is the app
registration `{app:infosec-foundry-deployer}` with a federated credential
bound to this repository's `production` environment:

```bash
# once, by an Entra admin (team/least-privilege/IDENTITY_RBAC.md)
az ad app federated-credential create --id {app-object-id} --parameters '{
  "name": "github-production",
  "issuer": "https://token.actions.githubusercontent.com",
  "subject": "repo:{github:org/repo}:environment:production",
  "audiences": ["api://AzureADTokenExchange"]
}'
```

The workflow's `permissions: id-token: write` lets the runner request that
token; `azure/login@v2` exchanges it. Nothing else in the job may use it —
the environment approval is what stands between a merge and the tenant.

Azure DevOps uses the same mechanism through an **ARM service connection
with workload identity federation** (`azureSubscription:
$(azureServiceConnection)`); the subject is issued by ADO, and the approval
lives on the ADO Environment `production`.

### Variables, not secrets

Every value the deploy needs is a repository/environment **variable**
(`vars.*` / pipeline variables): resource group, project endpoint, account
and workspace names, the alert mailbox, the action-group id, the delivery
Function app name, `FOUNDRY_API_VERSION`, `MEMORY_BACKEND`,
`KNOWLEDGE_SOURCE`. None is confidential, and keeping them out of the
`secrets` store keeps "this repository holds no secret" literally true.
Anything that *is* confidential stays a `@Microsoft.KeyVault(...)` reference
resolved by the workload's managed identity at run time.

## 2b. Nightly drift (`.github/workflows/nightly-drift.yml`)

Preventive gates only catch what goes through the pipeline. Nightly at 03:17
UTC the detective half asks the tenant two questions, both read-only:

| | Check | Fails when |
|---|---|---|
| A | `scripts/verify_deployment.py` | a live agent's instructions hash, tool set, model tier or promoted VERSION no longer matches the verified build; an agent exists in Foundry that the kit does not know (portal-created); an OpenAPI tool exposes a non-GET operation; a registry agent gained `write_connections` (C2, C19) |
| B | `team/access-review.sh` | — it is a snapshot, not an assertion: role assignments, Entra group membership, Foundry connection auth types, Key Vault secret ages, managed identities (`team/TEAM_MODEL.md` §15) |

It authenticates with a **read-only** federated identity
(`vars.AZURE_READONLY_CLIENT_ID`, Reader + Directory read) and carries no
`environment:` — gating a detective control behind a human approval means it
quietly stops running. A red night is an operational finding: follow
`operations/RUNBOOK.md`.

The access snapshot contains real user principal names. The workflow masks the
local part of every address before the artefact is uploaded; the unredacted
quarterly evidence belongs in SharePoint `Governance/AccessReviews/`, never in
a build artefact.

## 3. Secret scan

```bash
gitleaks detect --no-git --source . --config .github/gitleaks.toml --redact   # working tree
gitleaks detect           --source . --config .github/gitleaks.toml --redact   # full history
gitleaks detect --no-git --source .                                            # via the root shim

python3 convertion/scripts/scan_secrets.py                         # the kit's own pattern scan
python3 convertion/scripts/scan_secrets.py --json build/secret-scan.json   # CI evidence artefact
python3 convertion/scripts/scan_secrets.py --gitleaks               # both passes in one command
```

`scripts/scan_secrets.py` is a thin CLI over `verify_kit.scan_secrets` — the
same patterns, the same allow-list, the same `SECRETS  <file>:<line>: <label>`
output, deliberately **not** a second implementation. It exits 1 on any
finding, so it can be a gate on its own; `--gitleaks` adds the gitleaks pass
when the binary is on PATH (and says so when it is not, rather than passing
silently), reading the root `.gitleaks.toml` by default.

`.gitleaks.toml` at the repository root does nothing but `[extend] path` to
`.github/gitleaks.toml`, so the two commands above and the pre-commit hook all
enforce one allow-list. `extend.path` resolves against the **working
directory**, and gitleaks permits an extend chain of depth 2 — root → `.github`
→ defaults is exactly two links. Add rules in `.github/gitleaks.toml` only.

`--redact` keeps the finding out of the log. The allow-list covers only
documented placeholder syntax (`{upn:...}`, `<tenant>`, `${VAR}`, `@{...}`),
Key Vault references, public Azure built-in role definition GUIDs and
generated output under `build/`. Widening it to silence a finding is
forbidden: remove the value, rotate it, and open the incident
(`operations/RUNBOOK.md`). A same-id `[[rules]]` block would *replace* a
default rule and silently disable it — relax only through the allow-list.

## 4. Local mirror

Open the repository in the dev container (`.devcontainer/`) — it installs
the same Python, Node, Azure CLI, Bicep, Functions Core Tools and gitleaks
versions the pipelines use, plus the renderer `npm` dependencies. Then:

```bash
pre-commit install                     # hooks: hygiene, gitleaks, the kit gates
pre-commit install --hook-type pre-push  # also rehearse the release on push
pre-commit run --all-files             # everything the hooks cover, now

convertion/ci/syntax_check.sh          # SKIP_BICEP=1 if you have no bicep CLI
python3 convertion/ci/tests/test_residency.py
python3 -m pytest convertion/ci/tests -q
cd convertion && ./deploy.sh --dry-run
```

A hook can be skipped (`SKIP=kit-dry-run`, `--no-verify`) and a workflow
cannot, so `.pre-commit-config.yaml` is a convenience, never the control. It
deliberately carries **no ruff hook** yet: `ruff check convertion/` reports 17
findings today, nearly all `E402` from the `try: import azure… except
ImportError` shim every Foundry script opens with. A hook that is red on
arrival teaches people to bypass hooks — add ruff in the same PR that adds a
root `ruff.toml` selecting the rules the kit actually wants.

The container holds no credential: `az login` uses your own Entra identity,
and every script authenticates with `DefaultAzureCredential`.
