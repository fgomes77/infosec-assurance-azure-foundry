#!/usr/bin/env bash
# One-command, gated deployment of the whole environment.
# Each step must succeed (and the conversion must VERIFY against the
# claude.ai export) before the next runs — accuracy gates the speed.
#
#   ./deploy.sh            convert -> verify -> agents -> integrations
#                          -> orchestrator -> smoke test
#   ./deploy.sh --dry-run  full offline rehearsal (no Azure calls)
set -euo pipefail
cd "$(dirname "$0")/scripts"

DRY=""
[ "${1:-}" = "--dry-run" ] && DRY="--dry-run"

echo "==> [1/7] Converting skills from the claude.ai export"
python3 convert_skills.py

echo "==> [2/7] Verifying conversion fidelity (templates, rules, gates)"
python3 verify_conversion.py

echo "==> [3/7] Creating/updating agents $DRY"
python3 create_agents.py $DRY

echo "==> [4/7] Attaching integrations and model tiers $DRY"
python3 attach_integrations.py $DRY

echo "==> [5/7] Creating delivery-layer agents (ciso-global-report, analyzers, template-manager) $DRY"
python3 create_delivery_agents.py $DRY

echo "==> [5b/7] Re-attaching integrations to delivery agents $DRY"
python3 attach_integrations.py $DRY

echo "==> [6/7] Creating advisor + orchestrator (+ memory store) $DRY"
python3 create_orchestrator.py $DRY

echo "==> [6b/7] Staging delivery-function renderers"
python3 stage_renderers.py || echo "note: stage renderers after convert (see functions/delivery/README.md)"

if [ -z "$DRY" ]; then
  echo "==> [7/7] Smoke test via the orchestrator"
  python3 smoke_test.py --agent infosec-assurance-orchestrator \
    --prompt "One-line health check: name three DORA Art. 30(2) baseline contractual provisions."
else
  echo "==> [7/7] Smoke test skipped (dry run)"
fi

echo "==> Deployment pipeline completed."
