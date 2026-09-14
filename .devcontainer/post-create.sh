#!/usr/bin/env bash
# Mirror of the CI toolchain (.github/workflows/ci.yml, convertion/ci/azure-pipelines.yml):
# same Python, Node, Azure CLI, Bicep, Functions Core Tools and gitleaks
# versions, so "green locally" and "green in CI" mean the same thing.
#
# Nothing here contacts Azure or the tenant: the container is a build and
# review environment. Sign in yourself with `az login` when you want to run a
# live script; every script then uses your own Entra identity
# (DefaultAzureCredential — no keys anywhere in this repository).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BICEP_VERSION="${BICEP_VERSION:-0.47.16}"
GITLEAKS_VERSION="${GITLEAKS_VERSION:-8.18.4}"
FUNC_CORE_TOOLS_VERSION="${FUNC_CORE_TOOLS_VERSION:-4}"

echo ">> Python packages (kit runtime + offline gates)"
python3 -m pip install --disable-pip-version-check --quiet --upgrade pip
python3 -m pip install --disable-pip-version-check --quiet \
  -r "$ROOT/convertion/setup/requirements.txt" \
  PyYAML==6.0.2 jsonschema==4.23.0 ruff==0.15.8
# The delivery Function and the MCP server carry their own pins; install them
# so `func start` and `python3 mcp-server/server.py` work out of the box.
python3 -m pip install --disable-pip-version-check --quiet \
  -r "$ROOT/convertion/functions/delivery/requirements.txt" || \
  echo "   note: delivery Function requirements skipped (see functions/delivery/README.md)"
python3 -m pip install --disable-pip-version-check --quiet \
  -r "$ROOT/convertion/mcp-server/requirements.txt" || \
  echo "   note: MCP server requirements skipped (see mcp-server/README.md)"

echo ">> Azure Functions Core Tools v${FUNC_CORE_TOOLS_VERSION} (delivery Function)"
npm install -g --silent "azure-functions-core-tools@${FUNC_CORE_TOOLS_VERSION}" --unsafe-perm true \
  || echo "   note: func install failed — install it manually before using deploy.sh --functions"

echo ">> Bicep ${BICEP_VERSION} (pinned: infra/main.bicep uses \`!\` non-null assertions)"
az bicep install --version "v${BICEP_VERSION}" >/dev/null 2>&1 \
  || az bicep upgrade >/dev/null 2>&1 || true

echo ">> gitleaks ${GITLEAKS_VERSION} (same version and config as CI)"
if ! command -v gitleaks >/dev/null 2>&1; then
  curl -sSLf "https://github.com/gitleaks/gitleaks/releases/download/v${GITLEAKS_VERSION}/gitleaks_${GITLEAKS_VERSION}_linux_x64.tar.gz" \
    | sudo tar -xz -C /usr/local/bin gitleaks \
    || echo "   note: gitleaks install failed — the CI job still scans every PR"
fi

echo ">> shellcheck (the shell lint of convertion/ci/syntax_check.sh, as in CI)"
if ! command -v shellcheck >/dev/null 2>&1; then
  sudo apt-get update -qq && sudo apt-get install -y -qq shellcheck \
    || echo "   note: shellcheck install failed — the syntax gate then runs bash -n only; CI still lints"
fi

echo ">> pre-commit hooks (local mirror of the CI gates)"
python3 -m pip install --quiet pre-commit \
  && (cd "$ROOT" && pre-commit install && pre-commit install --hook-type pre-push) \
  || echo "   note: pre-commit install failed — run it by hand (convertion/ci/README.md §4)"

echo ">> Node renderer dependencies (delivery Function renderers)"
for pkg in "$ROOT"/convertion/functions/delivery/renderers-src/*/package.json; do
  [ -f "$pkg" ] || continue
  (cd "$(dirname "$pkg")" && npm install --silent --no-audit --no-fund) \
    || echo "   note: npm install failed in $(dirname "$pkg")"
done

cat <<'NOTE'

Toolchain ready. The gates CI runs on every PR, in order:

  python3 convertion/scripts/convert_skills.py
  python3 convertion/scripts/verify_conversion.py
  python3 convertion/scripts/verify_kit.py
  convertion/ci/syntax_check.sh
  convertion/infra/validate.sh
  python3 convertion/operations/evaluation/run_evals.py --dry-run
  cd convertion && ./deploy.sh --dry-run

  python3 convertion/ci/tests/test_residency.py
  python3 convertion/scripts/build_self_knowledge.py --check
  python3 -m pytest convertion/functions/delivery/tests \
    convertion/functions/office-tools/tests convertion/scripts/tests -q

  gitleaks detect --no-git --source . --config .github/gitleaks.toml --redact
  python3 convertion/scripts/scan_secrets.py

The pre-commit hooks are installed (commit and pre-push), so the hygiene
checks, gitleaks and the syntax/residency/kit gates run locally before a
push. They are a convenience mirror, not the authority — CI is
(`convertion/ci/README.md` §4). All of them are offline. Nothing in this container holds a credential:
`az login` uses your own identity, and no secret is ever committed
(convertion/governance/DATA_PROTECTION_GUARDRAILS.md §3).
NOTE
