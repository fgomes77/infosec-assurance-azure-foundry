#!/usr/bin/env bash
# One-command, gated deployment of the whole environment.
# Each step must succeed (and the conversion must VERIFY against the
# claude.ai export) before the next runs — accuracy gates the speed.
#
#   ./deploy.sh                convert -> verify -> agents -> delivery agents
#                              -> advisor/orchestrator -> integrations
#                              -> advisory profile -> renderers -> checks
#                              -> smoke test -> live drift check
#   ./deploy.sh --dry-run      full offline rehearsal (no Azure calls)
#   ./deploy.sh --infra        also run setup/provision.sh first
#   ./deploy.sh --functions    also publish functions/delivery (func CLI)
#   ./deploy.sh --workflows    also build + deploy the Logic App definitions
#
# Environment:
#   CONVERT_FLAGS   passed to steps 1-2, e.g. "--include-examples"
#                   or "--platform-skills docs" (deterministic CI builds)
#   CI=true         strict mode: renderer staging failures abort
#   KIT_RELEASE     release tag stamped on every agent (defaults to git describe)
set -euo pipefail
cd "$(dirname "$0")/scripts"

DRY=""; INFRA=""; FUNCTIONS=""; WORKFLOWS=""
for arg in "$@"; do
  case "$arg" in
    --dry-run)   DRY="--dry-run" ;;
    --infra)     INFRA=1 ;;
    --functions) FUNCTIONS=1 ;;
    --workflows) WORKFLOWS=1 ;;
    *) echo "unknown flag: $arg"; exit 2 ;;
  esac
done
CONVERT_FLAGS="${CONVERT_FLAGS:-}"
export KIT_RELEASE="${KIT_RELEASE:-$(git describe --tags --match 'platform/*' --always 2>/dev/null || echo unversioned)}"
[ -f ../setup/.env ] && set -a && . ../setup/.env && set +a

if [ -n "$INFRA" ] && [ -z "$DRY" ]; then
  echo "==> [0a] Provisioning infrastructure (setup/provision.sh)"
  ../setup/provision.sh
fi

if [ -z "$DRY" ]; then
  echo "==> [0/7] Pre-deploy export of vs-assurance-memory + vector-store inventory (read-only)"
  python3 ../operations/backup_vector_stores.py --stores vs-assurance-memory \
    --out "../operations/backups/$(date -u +%Y-%m-%d)" \
    || { echo "backup failed — aborting (operations/BACKUP_DR.md §3)"; exit 1; }
fi

echo "==> [1/7] Converting skills from the claude.ai export ${CONVERT_FLAGS}"
# shellcheck disable=SC2086
python3 convert_skills.py $CONVERT_FLAGS

echo "==> [2/7] Verifying conversion fidelity (templates, rules, gates) + kit consistency"
python3 verify_conversion.py
python3 verify_kit.py

echo "==> [3/7] Creating/updating agents $DRY"
python3 create_agents.py $DRY

echo "==> [4/7] Creating delivery-layer agents (ciso-global-report, analyzers, template-manager) $DRY"
python3 create_delivery_agents.py $DRY

echo "==> [5/7] Creating advisor + verifier + orchestrator (+ memory store) $DRY"
python3 create_orchestrator.py $DRY

# Integrations run ONCE, after every agent exists (advisor included) —
# earlier runs would skip the advisor as "not deployed".
echo "==> [5b/7] Attaching integrations and model tiers to every agent $DRY"
python3 attach_integrations.py $DRY

echo "==> [6/7] Applying advisory profile (file generation + read-only enterprise charter + combined store) $DRY"
python3 apply_advisory_profile.py $DRY

echo "==> [6a/7] Re-wiring the orchestrator to the final agent set $DRY"
python3 create_orchestrator.py $DRY

echo "==> [6c/7] Staging delivery-function renderers"
if [ "${CI:-}" = "true" ]; then
  python3 stage_renderers.py --strict
else
  python3 stage_renderers.py || echo "note: stage renderers after convert (see functions/delivery/README.md)"
fi

if [ -n "$FUNCTIONS" ] && [ -z "$DRY" ]; then
  echo "==> [6c2] Publishing the delivery Function App (${DELIVERY_FUNCTION_APP_NAME:?set DELIVERY_FUNCTION_APP_NAME in setup/.env})"
  (cd ../functions/delivery && func azure functionapp publish "$DELIVERY_FUNCTION_APP_NAME" --python)
fi

if [ -n "$WORKFLOWS" ]; then
  echo "==> [6c3] Building Logic App definitions (build/logicapps/) $DRY"
  python3 build_logicapps.py $DRY
  if [ -z "$DRY" ] && [ -x ../ci/deploy_logicapps.sh ]; then
    ../ci/deploy_logicapps.sh
  elif [ -z "$DRY" ]; then
    echo "note: ci/deploy_logicapps.sh not present — deploy build/logicapps/ with 'az logicapp deployment source config-zip' (workflows/README.md)"
  fi
fi

if [ -z "$DRY" ]; then
  echo "==> [6d/7] Identity model check (read-only)"
  ../team/least-privilege/scripts/provision_identity.sh --verify && ../team/access-review.sh --quick \
    || echo "note: identity drift detected - see team/TEAM_MODEL.md §15"

  echo "==> [6e/7] Monitoring rules (what-if only; apply from the pipeline)"
  az deployment group what-if -g "$AZURE_RESOURCE_GROUP" -f ../operations/alerts.bicep \
    -p logAnalyticsName="${LOG_ANALYTICS_WORKSPACE_NAME:-infosecfoundry-logs}" \
       foundryAccountName="${FOUNDRY_ACCOUNT_NAME:-infosecfoundry-aif}" \
       ownerAlertEmail="${OWNER_ALERT_EMAIL:?set OWNER_ALERT_EMAIL in setup/.env}" \
    || echo "note: alert what-if skipped (no az session or RG) - see operations/MONITORING.md §4"

  echo "==> [6f/7] Component budgets (what-if only; apply from the pipeline)"
  az deployment group what-if -g "$AZURE_RESOURCE_GROUP" -f ../operations/cost-budget.bicep \
    -p baseName="${BASE_NAME:-infosecfoundry}" foundryAccountName="${FOUNDRY_ACCOUNT_NAME:-infosecfoundry-aif}" \
       logAnalyticsName="${LOG_ANALYTICS_WORKSPACE_NAME:-infosecfoundry-logs}" \
       appInsightsName="${APP_INSIGHTS_NAME:-infosecfoundry-appi}" \
       startDate="${BUDGET_START_DATE:-{yyyy-MM-01}}" actionGroupId="${ACTION_GROUP_ID:-}" \
    || echo "note: budget what-if skipped (no az session or RG) - see operations/FINOPS.md §4"

  echo "==> [7/7] Smoke test via the orchestrator"
  python3 smoke_test.py --agent infosec-assurance-orchestrator \
    --prompt "One-line health check: name three DORA Art. 30(2) baseline contractual provisions."

  echo "==> [7b/7] Live drift check (deployed state vs verified build, read-only)"
  python3 verify_deployment.py
else
  echo "==> [7/7] Smoke test + live drift check skipped (dry run)"
fi

echo "==> Deployment pipeline completed (release ${KIT_RELEASE})."
