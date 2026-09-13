#!/usr/bin/env bash
# Offline syntax gate for the kit: python, json, yaml, toml, javascript, bicep,
# shell (bash -n + shellcheck). Shared by .github/workflows/ci.yml and ci/azure-pipelines.yml so the
# two pipelines can never diverge, and runnable by hand before a PR:
#
#   convertion/ci/syntax_check.sh              # everything it can check
#   SKIP_BICEP=1 convertion/ci/syntax_check.sh # no bicep CLI on this machine
#   REQUIRE_SHELLCHECK=1 ...                   # fail instead of skipping the lint
#
# Read-only: it compiles/parses, never writes (py_compile caches go to a temp
# dir, bicep builds to stdout). Scope is convertion/ plus the pipeline YAML —
# claude-account-export/ is verified byte-for-byte by verify_conversion.py and
# is never linted here, and build/ is generated output. The pipeline YAML
# (.github/), the root .pre-commit-config.yaml, both gitleaks configs and the
# dev container (.devcontainer/) are parsed too, so a typo in a gate definition
# fails the gate that defines it.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
CONV="$ROOT/convertion"
PRUNE=( -path '*/build/*' -o -path '*/__pycache__/*' -o -path '*/node_modules/*'
        -o -path '*/renderers/*' -o -path '*/.ruff_cache/*' -o -path '*/.git/*' )
fail=0
note() { printf '   %s\n' "$1"; }
step() { printf '>> %s\n' "$1"; }

files() {  # files <ext> [more find args...]
  find "$CONV" \( "${PRUNE[@]}" \) -prune -o -name "*.$1" -type f -print | sort
}

export PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/kit-pycache"

step "python (py_compile)"
n=0
while IFS= read -r f; do
  n=$((n + 1))
  python3 -m py_compile "$f" || { note "!! $f"; fail=1; }
done < <(files py)
note "$n file(s)"

step "json (json.tool)"
n=0
while IFS= read -r f; do
  n=$((n + 1))
  python3 -m json.tool "$f" >/dev/null || { note "!! $f"; fail=1; }
done < <(files json; ls "$ROOT"/.devcontainer/*.json 2>/dev/null)
note "$n file(s)"

step "yaml (PyYAML)"
if python3 -c "import yaml" 2>/dev/null; then
  n=0
  while IFS= read -r f; do
    n=$((n + 1))
    python3 -c "import sys,yaml;list(yaml.safe_load_all(open(sys.argv[1],encoding='utf-8')))" "$f" \
      || { note "!! $f"; fail=1; }
  done < <(files yaml; files yml; ls "$ROOT"/.github/*.yml "$ROOT"/.github/workflows/*.yml \
                                    "$ROOT"/.pre-commit-config.yaml 2>/dev/null)
  note "$n file(s)"
else
  note "PyYAML not installed — YAML parse SKIPPED (pip install PyYAML)"
fi

step "toml (tomllib)"
# The gitleaks configs: an unparsable one makes the secret scan fail open on
# some versions and hard-fail on others — neither is noticed quickly.
n=0
while IFS= read -r f; do
  n=$((n + 1))
  python3 -c "import sys,tomllib;tomllib.load(open(sys.argv[1],'rb'))" "$f" \
    || { note "!! $f"; fail=1; }
done < <(files toml; ls "$ROOT"/.gitleaks.toml "$ROOT"/.github/gitleaks.toml 2>/dev/null)
note "$n file(s)"

step "javascript (node --check)"
if command -v node >/dev/null 2>&1; then
  n=0
  while IFS= read -r f; do
    n=$((n + 1))
    node --check "$f" || { note "!! $f"; fail=1; }
  done < <(files js)
  note "$n file(s)"
else
  note "node not installed — JS check SKIPPED"
fi

step "shell (bash -n)"
n=0
while IFS= read -r f; do
  n=$((n + 1))
  bash -n "$f" || { note "!! $f"; fail=1; }
done < <(files sh)
note "$n file(s)"

# bash -n only proves the file parses. shellcheck is the actual lint (unquoted
# expansions, lost exit codes, `set -e` traps) and is a HARD gate wherever it
# exists: both CI runners install it (.github/workflows/ci.yml toolchain step,
# ci/azure-pipelines.yml), so a PR cannot go green on a shellcheck finding by
# running somewhere without it. Locally it degrades to a note — install with
# `sudo apt-get install shellcheck` (0.9.0) or `brew install shellcheck`.
# Severity floor: warning (error+warning fail; info/style are advisory). A
# deliberate exception is an inline `# shellcheck disable=SCxxxx` with a reason,
# never a lowered severity here.
step "shell (shellcheck)"
if command -v shellcheck >/dev/null 2>&1; then
  n=0; sc=()
  while IFS= read -r f; do n=$((n + 1)); sc+=("$f"); done < <(files sh)
  shellcheck --severity=warning --external-sources "${sc[@]}" || { note "!! shellcheck findings above"; fail=1; }
  note "$n file(s)"
elif [ "${REQUIRE_SHELLCHECK:-}" = "1" ]; then
  note "shellcheck REQUIRED but not installed — gate FAILED"; fail=1
else
  note "shellcheck not installed — lint SKIPPED (bash -n only); CI installs it"
fi

step "bicep (build --stdout)"
if [ "${SKIP_BICEP:-}" = "1" ]; then
  note "SKIP_BICEP=1 — bicep build SKIPPED"
elif command -v bicep >/dev/null 2>&1 || command -v az >/dev/null 2>&1; then
  if command -v bicep >/dev/null 2>&1; then B=(bicep build); else B=(az bicep build --file); fi
  n=0
  while IFS= read -r f; do
    n=$((n + 1))
    # BCP081 = resource type has no published types (Bing, preview APIs) — expected.
    if ! "${B[@]}" "$f" --stdout >/dev/null 2>"${TMPDIR:-/tmp}/bicep.err"; then
      note "!! $f"; grep -v BCP081 "${TMPDIR:-/tmp}/bicep.err" | head -5; fail=1
    fi
  done < <(files bicep)
  note "$n file(s)"
else
  note "no bicep/az CLI — bicep build SKIPPED (install Bicep 0.47.16)"
fi

[ $fail -eq 0 ] && echo "syntax gate OK" || echo "syntax gate FAILED"
exit $fail
