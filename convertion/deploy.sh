#!/usr/bin/env bash
# One-command, gated deployment of the whole environment.
# Each step must succeed (and the conversion must VERIFY against the
# claude.ai export) before the next runs — accuracy gates the speed.
#
#   ./deploy.sh                runtime pre-flight -> model lifecycle ->
#                              convert -> self-knowledge pack -> verify
#                              -> agents -> delivery agents -> router rewire
#                              -> advisor/orchestrator -> integrations
#                              -> advisory profile -> renderers -> checks
#                              -> smoke test -> live drift check
#
# Not run here (optional, one-off): scripts/create_tpsrca_subagents.py splits
# the TPSRCA 12-role methodology into tpsrca-calc / tpsrca-analysis /
# tpsrca-report. It needs registry entries first and changes the routable
# agent set, so it is an owner decision, not a deploy step.
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
#   ALLOW_CLASSIC_RUNTIME=1
#                   allow the deploy to proceed on the retiring classic
#                   threads/runs SDK (azure-ai-projects 1.x). Default: the
#                   pre-flight only warns; set STRICT_RUNTIME=1 to fail.
#   STRICT_RUNTIME=1  fail the deploy unless azure-ai-projects is 2.x
#   LIFECYCLE_HORIZON  days for the model-retirement warning (default 180)
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

# [0a] Runtime pre-flight (finding C1, shared delta S-10). The classic
# threads/runs Agent Service retires 2027-03-31; scripts/_foundry_runtime.py
# prefers the GA Responses API and falls back to the classic runtime, which
# this gate makes visible instead of silent.
echo "==> [0b/8] Runtime pre-flight (Foundry data-plane SDK + api-version)"
python3 - <<'PYPRE' || { echo "runtime pre-flight failed"; exit 1; }
import os, sys
sys.path.insert(0, ".")          # deploy.sh runs from convertion/scripts
from _foundry_runtime import API_VERSION, runtime_banner, runtime_mode, sdk_version
print(runtime_banner())
if runtime_mode() == "classic":
    msg = ("classic threads/runs runtime in use (azure-ai-projects "
           f"{sdk_version() or 'missing'}); upgrade setup/requirements.txt to "
           "azure-ai-projects>=2.3.0,<3 — enterprise/series/06 §A")
    if os.environ.get("STRICT_RUNTIME") == "1":
        sys.exit("ERROR: " + msg)
    print("WARNING: " + msg)
elif API_VERSION != "v1":
    print(f"WARNING: FOUNDRY_API_VERSION={API_VERSION} is not the GA 'v1' "
          f"surface — setup/.env")
PYPRE

# [0c] Model lifecycle / platform currency (findings C6, C25). Offline; it
# fails only when a deployed model version is inside the ticket window or a
# tier has no pinned version — the reviewed compensating control for
# NoAutoUpgrade (enterprise/UPDATE_AND_UPGRADE_REVIEW_POLICY.md R1, R2).
echo "==> [0c/8] Model lifecycle + pinned-version check (offline)"
if [ -f ../enterprise/upgrade/check_model_lifecycle.py ]; then
  # Advisory by default (it reports pinned-version, retirement and
  # tool-support findings that need an OWNER decision, not a failed build);
  # LIFECYCLE_STRICT=1 makes it blocking — that is what the release pipeline
  # sets (ci/README.md, finding C25).
  if ! python3 ../enterprise/upgrade/check_model_lifecycle.py --dry-run \
      --horizon "${LIFECYCLE_HORIZON:-180}" \
      --json ../build/lifecycle-report.json; then
    echo "!! model lifecycle findings are open: a pinned model version is empty, a deployment retires within the ticket window, or a tier model cannot carry its tools (finding C4). Open the change ticket (enterprise/UPDATE_AND_UPGRADE_REVIEW_POLICY.md §4) or re-run with an updated retirement table."
    [ -n "${LIFECYCLE_STRICT:-}" ] && exit 1
  fi
else
  echo "note: enterprise/upgrade/check_model_lifecycle.py not present - platform-currency check skipped"
fi

if [ -z "$DRY" ]; then
  echo "==> [0/8] Pre-deploy export of vs-assurance-memory + vector-store inventory (read-only)"
  python3 ../operations/backup_vector_stores.py --stores vs-assurance-memory \
    --out "../operations/backups/$(date -u +%Y-%m-%d)" \
    || { echo "backup failed — aborting (operations/BACKUP_DR.md §3)"; exit 1; }
fi

echo "==> [1/8] Converting skills from the claude.ai export ${CONVERT_FLAGS}"
# shellcheck disable=SC2086
python3 convert_skills.py $CONVERT_FLAGS

# [1b] The platform self-knowledge pack (what agents retrieve when asked what
# THIS platform can do) is generated from the kit: manifest, registry,
# pipelines, templates, approval policy. It needs the fresh manifest, so it
# runs after the conversion; when it changes anything the conversion re-runs
# so every knowledge store ships the new version.
echo "==> [1b/8] Regenerating the platform self-knowledge pack"
if [ -n "$DRY" ]; then
  # a rehearsal must not write into agents/ (the pack is a committed file):
  # report only. Add `build_self_knowledge.py --check` to the pipeline once
  # the regenerated pack is in git, to fail on a stale one.
  python3 build_self_knowledge.py --dry-run | tail -1
else
  set +e
  python3 build_self_knowledge.py --changed-exit 9
  sk_rc=$?
  set -e
  case "$sk_rc" in
    0) ;;
    9) echo "    pack changed - re-converting so every knowledge store gets it"
       # shellcheck disable=SC2086
       python3 convert_skills.py $CONVERT_FLAGS ;;
    *) echo "self-knowledge pack generation failed"; exit "$sk_rc" ;;
  esac
fi

echo "==> [2/8] Verifying conversion fidelity (templates, rules, gates) + kit consistency"
python3 verify_conversion.py
python3 verify_kit.py

if [ -z "$DRY" ] && [ -z "${ALLOW_BASIC_AGENT_SETUP:-}" ]; then
  echo "==> Pre-flight: capability host (standard agent setup, finding C5)"
  # The capability host binds the project to the BYO Cosmos DB / AI Search /
  # Storage and is IMMUTABLE once the first agent exists. Set
  # ALLOW_BASIC_AGENT_SETUP=1 only for a dev project deliberately running the
  # basic (Microsoft-managed) setup.
  if [ -z "${PROJECT_RESOURCE_ID:-}" ]; then
    echo "note: PROJECT_RESOURCE_ID not set (setup/.env) - capability-host check skipped"
  elif ! az rest --method get \
      --url "https://management.azure.com${PROJECT_RESOURCE_ID}/capabilityHosts?api-version=2025-06-01" \
      --query "value[0].name" -o tsv 2>/dev/null | grep -q .; then
    echo "!! No capability host on the project. Deploy infra/main.bicep with enableStandardAgentSetup=true FIRST - it cannot be added after the first agent exists."
    exit 1
  fi
fi

echo "==> [3/8] Creating/updating agents (router wiring deferred) $DRY"
python3 create_agents.py --skip-routers $DRY

echo "==> [4/8] Creating delivery-layer agents (ciso-global-report, analyzers, template-manager) $DRY"
python3 create_delivery_agents.py $DRY

# The control-center ROUTE table covers the delivery agents (menu options
# 6-10, agents/overlays/enx-tprm-control-center.md), so it can only be wired
# once step [4] has created them - wiring it inside step [3] would fail on
# targets that do not exist yet.
echo "==> [4b/8] Wiring the control-center ROUTE table over the full agent set $DRY"
python3 create_agents.py --rewire $DRY

echo "==> [5/8] Creating advisor + verifier + orchestrator (+ memory store) $DRY"
python3 create_orchestrator.py $DRY

# Integrations run ONCE, after every agent exists (advisor included) —
# earlier runs would skip the advisor as "not deployed".
echo "==> [5b/8] Attaching integrations and model tiers to every agent $DRY"
python3 attach_integrations.py $DRY

echo "==> [6/8] Applying advisory profile (file generation + read-only enterprise charter + combined store) $DRY"
python3 apply_advisory_profile.py $DRY

echo "==> [6a/8] Re-wiring the orchestrator to the final agent set $DRY"
python3 create_orchestrator.py $DRY

echo "==> [6c/8] Staging delivery-function renderers"
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
  echo "==> [6d/8] Identity model check (read-only)"
  ../team/least-privilege/scripts/provision_identity.sh --verify && ../team/access-review.sh --quick \
    || echo "note: identity drift detected - see team/TEAM_MODEL.md §15"

  echo "==> [6e/8] Monitoring rules (what-if only; apply from the pipeline)"
  az deployment group what-if -g "$AZURE_RESOURCE_GROUP" -f ../operations/alerts.bicep \
    -p logAnalyticsName="${LOG_ANALYTICS_WORKSPACE_NAME:-infosecfoundry-logs}" \
       foundryAccountName="${FOUNDRY_ACCOUNT_NAME:-infosecfoundry-aif}" \
       ownerAlertEmail="${OWNER_ALERT_EMAIL:?set OWNER_ALERT_EMAIL in setup/.env}" \
    || echo "note: alert what-if skipped (no az session or RG) - see operations/MONITORING.md §4"

  echo "==> [6f/8] Component budgets (what-if only; apply from the pipeline)"
  az deployment group what-if -g "$AZURE_RESOURCE_GROUP" -f ../operations/cost-budget.bicep \
    -p baseName="${BASE_NAME:-infosecfoundry}" foundryAccountName="${FOUNDRY_ACCOUNT_NAME:-infosecfoundry-aif}" \
       logAnalyticsName="${LOG_ANALYTICS_WORKSPACE_NAME:-infosecfoundry-logs}" \
       appInsightsName="${APP_INSIGHTS_NAME:-infosecfoundry-appi}" \
       startDate="${BUDGET_START_DATE:-{yyyy-MM-01}}" actionGroupId="${ACTION_GROUP_ID:-}" \
    || echo "note: budget what-if skipped (no az session or RG) - see operations/FINOPS.md §4"

  echo "==> [7/8] Smoke test via the orchestrator"
  python3 smoke_test.py --agent infosec-assurance-orchestrator \
    --prompt "One-line health check: name three DORA Art. 30(2) baseline contractual provisions."

  echo "==> [7b/8] Live drift check (deployed state vs verified build, read-only)"
  python3 verify_deployment.py
else
  echo "==> [7/8] Smoke test + live drift check skipped (dry run)"
fi

echo "==> Deployment pipeline completed (release ${KIT_RELEASE})."
