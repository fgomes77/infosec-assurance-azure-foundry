#!/usr/bin/env bash
# Offline syntax gate for the kit: python, json, yaml, javascript, bicep,
# shell. Shared by .github/workflows/ci.yml and ci/azure-pipelines.yml so the
# two pipelines can never diverge, and runnable by hand before a PR:
#
#   convertion/ci/syntax_check.sh              # everything it can check
#   SKIP_BICEP=1 convertion/ci/syntax_check.sh # no bicep CLI on this machine
#
# Read-only: it compiles/parses, never writes (py_compile caches go to a temp
# dir, bicep builds to stdout). Scope is convertion/ plus the pipeline YAML —
# claude-account-export/ is verified byte-for-byte by verify_conversion.py and
# is never linted here, and build/ is generated output. The pipeline YAML
# (.github/) and the dev container (.devcontainer/) are parsed too, so a typo
# in a gate definition fails the gate that defines it.
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
  done < <(files yaml; files yml; ls "$ROOT"/.github/*.yml "$ROOT"/.github/workflows/*.yml 2>/dev/null)
  note "$n file(s)"
else
  note "PyYAML not installed — YAML parse SKIPPED (pip install PyYAML)"
fi

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
