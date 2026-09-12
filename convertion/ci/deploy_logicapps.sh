#!/usr/bin/env bash
# Ship the derived Logic App (Standard) definitions.
#
# `scripts/build_logicapps.py` writes build/logicapps/<name>/workflow.json —
# one instance per workflows/pipelines.json entry plus every standalone
# workflow (workflows/README.md "Deployment note"). This script packages that
# folder in the layout a Logic App Standard site expects (each workflow in its
# own directory at the zip root, next to host.json) and deploys it with
# `az logicapp deployment source config-zip`. Called by deploy.sh --workflows;
# safe to run on its own.
#
#   ci/deploy_logicapps.sh                 # deploy build/logicapps -> $LOGIC_APP_NAME
#   ci/deploy_logicapps.sh --dry-run       # build the zip, print the command, deploy nothing
#   LOGIC_APP_NAME=... AZURE_RESOURCE_GROUP=... ci/deploy_logicapps.sh
#
# Identity: the caller's `az login` — in CI the federated deploy identity of
# the `production` environment (team/TEAM_MODEL.md L11). No secret is read or
# written here: connection strings and tokens stay `@Microsoft.KeyVault(...)`
# app settings on the site, set once by setup/provision.sh.
#
# Rollback: Logic Apps keeps the previous deployment package —
# `az logicapp deployment list` then re-deploy the prior zip, or re-run this
# script from the previous commit (operations/CHANGE_MANAGEMENT.md §3).
set -euo pipefail
cd "$(dirname "$0")/.."

DRY=""
[ "${1:-}" = "--dry-run" ] && DRY=1

SRC="${LOGICAPPS_DIR:-build/logicapps}"
RG="${AZURE_RESOURCE_GROUP:-}"
APP="${LOGIC_APP_NAME:-${BASE_NAME:-infosecfoundry}-la}"
ZIP="${LOGICAPPS_ZIP:-build/logicapps.zip}"

[ -f setup/.env ] && set -a && . setup/.env && set +a
RG="${AZURE_RESOURCE_GROUP:-$RG}"
APP="${LOGIC_APP_NAME:-$APP}"

if [ ! -d "$SRC" ]; then
  echo "no $SRC — run: python3 scripts/build_logicapps.py" >&2
  exit 1
fi
count=$(find "$SRC" -name workflow.json | wc -l | tr -d ' ')
if [ "$count" -eq 0 ]; then
  echo "$SRC holds no workflow.json — run scripts/build_logicapps.py" >&2
  exit 1
fi

# host.json belongs at the zip root; build_logicapps.py does not emit one, so
# a minimal Workflow-runtime host file is generated when it is absent.
if [ ! -f "$SRC/host.json" ]; then
  cat > "$SRC/host.json" <<'JSON'
{
  "version": "2.0",
  "extensionBundle": {
    "id": "Microsoft.Azure.Functions.ExtensionBundle.Workflows",
    "version": "[1.*, 2.0.0)"
  }
}
JSON
fi

rm -f "$ZIP"
(cd "$SRC" && zip -q -r "$OLDPWD/$ZIP" . -x '*.DS_Store')
echo ">> packaged $count workflow(s) from $SRC -> $ZIP"
python3 - "$SRC" <<'PY'
import json, sys
from pathlib import Path
# Fail before deploying rather than after: every definition must parse and
# must not carry an unresolved ${ENV} placeholder (build_logicapps.py reports
# them; deploying one would create a workflow that fails at run time).
bad = 0
for f in sorted(Path(sys.argv[1]).rglob("workflow.json")):
    try:
        text = f.read_text(encoding="utf-8")
        json.loads(text)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"!! {f}: {exc}"); bad = 1; continue
    if "${" in text:
        print(f"!! {f}: unresolved ${{ENV}} placeholder — set it in setup/.env "
              f"and re-run scripts/build_logicapps.py"); bad = 1
print("definitions OK" if not bad else "definitions FAILED")
sys.exit(bad)
PY

if [ -n "$DRY" ]; then
  echo ">> dry run — would deploy:"
  echo "   az logicapp deployment source config-zip -g ${RG:-<AZURE_RESOURCE_GROUP>} -n $APP --src $ZIP"
  exit 0
fi

: "${RG:?set AZURE_RESOURCE_GROUP (setup/.env)}"
echo ">> deploying $ZIP to logic app $APP (resource group $RG)"
az logicapp deployment source config-zip -g "$RG" -n "$APP" --src "$ZIP"
echo ">> deployed. Verify: az logicapp show -g $RG -n $APP --query state -o tsv"
echo "   Run history and the enable/disable state of each workflow are in the"
echo "   portal (workflows/README.md); this script never enables a workflow."
