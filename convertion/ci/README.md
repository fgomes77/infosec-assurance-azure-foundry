# CI/CD — gates on every PR, gated deploy on `main`

Nothing reaches the tenant that has not first proved itself on a clean
runner. The pipelines here run the **same scripts** the team runs by hand
(`deploy.sh` steps 1–2, `infra/validate.sh`, `operations/evaluation/run_evals.py`),
so a green pipeline and a green desk are the same statement.

| File | What it is |
|---|---|
| `../../.github/workflows/ci.yml` | GitHub Actions: jobs `gates`, `secret-scan` (every PR and every push to `main`) and `deploy` (push to `main`, `production` environment approval, OIDC) |
| `azure-pipelines.yml` | Azure DevOps equivalent — same steps, same order; register as *existing YAML file* `/convertion/ci/azure-pipelines.yml` |
| `syntax_check.sh` | The syntax gate both pipelines call: python, json, yaml, javascript, bicep, shell. Runnable by hand before a PR |
| `deploy_logicapps.sh` | Packages `build/logicapps/` (from `scripts/build_logicapps.py`) and deploys it with `az logicapp deployment source config-zip`; called by `deploy.sh --workflows` |
| `../../.github/gitleaks.toml` | Secret-scan configuration: default rules + allow-list of the kit's documented placeholders |
| `../../.github/dependabot.yml` | Weekly grouped dependency PRs (patch class — `operations/LIFECYCLE.md`) |
| `../../.devcontainer/` | The same toolchain locally: Python 3.12, Node 22, Azure CLI, Bicep 0.47.16, Functions Core Tools v4, gitleaks 8.18.4 |

## 1. The PR gate, in order

| # | Step | Command | Fails when |
|---|---|---|---|
| 1 | Convert | `python3 convertion/scripts/convert_skills.py` | the export cannot be converted |
| 2 | Fidelity | `python3 convertion/scripts/verify_conversion.py` | a knowledge file, code-tree file or zip member no longer matches its source SHA-256, an instruction lost its rules/persona/approval gate, or a skill is neither converted nor decided |
| 3 | Kit consistency | `python3 convertion/scripts/verify_kit.py` | a secret, tenant hostname or e-mail address appears under `convertion/`, a JSON/YAML/shell file is unparsable, or a cross-reference is broken |
| 4 | Syntax | `convertion/ci/syntax_check.sh` | any `.py .json .yaml .js .bicep .sh` in the kit fails to compile/parse |
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

The `deploy` job/stage runs only on a push to `main`, only after the gates
and the secret scan are green, and only after the **`production`
environment** approval — the accountable owner is the approver
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

## 3. Secret scan

```bash
gitleaks detect --no-git --source . --config .github/gitleaks.toml --redact   # working tree
gitleaks detect           --source . --config .github/gitleaks.toml --redact   # full history
```

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
convertion/ci/syntax_check.sh          # SKIP_BICEP=1 if you have no bicep CLI
cd convertion && ./deploy.sh --dry-run
```

The container holds no credential: `az login` uses your own Entra identity,
and every script authenticates with `DefaultAzureCredential`.
