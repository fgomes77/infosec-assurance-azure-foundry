#!/usr/bin/env bash
# Offline + optional online gate for infra/: bicep build + lint of every
# module, parameter-file coherence, EU-residency policy check, and (with
# --what-if) a read-only `az deployment group what-if`. CI runs this on every
# PR (see README §CI); setup/provision.sh runs it before deploying.
#
# The policy block also gates the decisions that bind at account/project
# creation: standard agent setup (C5), agent VNet injection (C12), CMK (C22),
# pinned model versions + NoAutoUpgrade (C6) and preventive Azure Policy (C11).
#
#   ./validate.sh                      # build + lint + policy (no Azure calls)
#   ./validate.sh --what-if <rg>       # + what-if with main.parameters.json
#   PARAMS=main.parameters.prod.json ./validate.sh --what-if <rg>
set -euo pipefail
cd "$(dirname "$0")"
PARAMS="${PARAMS:-main.parameters.json}"
BICEP_VERSION="${BICEP_VERSION:-0.47.16}"   # pinned: main.bicep uses the `!` non-null assertion syntax
BICEP="${BICEP:-}"
if [ -z "$BICEP" ]; then
  if command -v bicep >/dev/null 2>&1; then BICEP=bicep
  elif command -v az >/dev/null 2>&1; then az bicep install --version "v$BICEP_VERSION" >/dev/null 2>&1 || true; BICEP="az bicep"
  else echo "bicep CLI not found (install Bicep $BICEP_VERSION or az CLI)"; exit 1; fi
fi
echo ">> Bicep: $($BICEP --version 2>/dev/null || $BICEP version)"

fail=0
for f in *.bicep; do
  # standalone CLI: `bicep build <file>`; az extension: `az bicep build --file <file>`
  case "$BICEP" in az*) ARGS="build --file $f --stdout" ;; *) ARGS="build $f --stdout" ;; esac
  if ! $BICEP $ARGS >/dev/null 2>"/tmp/bicep-$f.log"; then
    echo "!! build failed: $f"; grep -v BCP081 "/tmp/bicep-$f.log"; fail=1
  fi
  if grep -q "Warning" "/tmp/bicep-$f.log"; then
    grep "Warning" "/tmp/bicep-$f.log" | grep -v BCP081 || true   # Bing has no published types; expected
  fi
done
[ $fail -eq 0 ] && echo ">> build + lint OK for $(ls *.bicep | wc -l) modules"

echo ">> Parameter/policy check ($PARAMS)"
python3 - "$PARAMS" <<'PY'
import json, re, sys
params_file = sys.argv[1]
tpl = open('main.bicep').read()
declared = set(re.findall(r'^param (\w+)', tpl, re.M))
allowed_eu = re.search(r"@allowed\(\[(.*?)\]\)\s*param location", tpl, re.S).group(1)
eu = set(re.findall(r"'([a-z]+)'", allowed_eu))
p = json.load(open(params_file))['parameters']
bad = 0
for k in p:
    if k not in declared:
        print(f"!! unknown parameter {k}"); bad = 1
loc = p.get('location', {}).get('value', 'swedencentral')
if loc not in eu:
    print(f"!! location {loc} is not in the EU allow-list {sorted(eu)}"); bad = 1
sku = p.get('deploymentSku', {}).get('value', 'DataZoneStandard')
if sku not in ('DataZoneStandard', 'Standard'):
    print(f"!! deploymentSku {sku} would route inference outside the EU"); bad = 1
if p.get('publicNetworkAccess', {}).get('value') == 'Disabled' and not p.get('enablePrivateNetworking', {}).get('value'):
    print("!! publicNetworkAccess=Disabled requires enablePrivateNetworking=true"); bad = 1
if int(p.get('logRetentionDays', {}).get('value', 365)) < 365:
    print("!! logRetentionDays < 365 (DORA Art. 28 evidence retention)"); bad = 1
# Finding C6 — every tier must be pinned; an unpinned deployment follows the
# provider default and silently changes validated deliverables.
for tier in ('modelVersion', 'reasoningModelVersion', 'lightModelVersion'):
    if not str(p.get(tier, {}).get('value', '')).strip():
        print(f"!! {tier} is not pinned (finding C6: pin the version on every tier)"); bad = 1
upgrade = p.get('modelVersionUpgradeOption', {}).get('value', 'NoAutoUpgrade')
if upgrade not in ('NoAutoUpgrade', 'OnceNewDefaultVersionAvailable', 'OnceCurrentVersionExpired'):
    print(f"!! modelVersionUpgradeOption {upgrade} is not a valid option"); bad = 1
# Finding C12 — injection needs a subnet; the account cannot be injected later.
if p.get('enableAgentVnetInjection', {}).get('value') and not (
        p.get('enablePrivateNetworking', {}).get('value') or str(p.get('agentSubnetId', {}).get('value', '')).strip()):
    print("!! enableAgentVnetInjection=true requires enablePrivateNetworking=true or an explicit agentSubnetId"); bad = 1
# Finding C22 — a key URI without a key name falls back to platform keys.
cmk_uri = str(p.get('cmkKeyUri', {}).get('value', '')).strip()
if cmk_uri and '/keys/' not in cmk_uri:
    print("!! cmkKeyUri must be a Key Vault key URI (https://<vault>/keys/<name>)"); bad = 1
# prod profile: the decisions that cannot be taken after the first agent exists
if p.get('environmentName', {}).get('value') == 'prod':
    if not p.get('enableStandardAgentSetup', {}).get('value'):
        print("!! prod requires enableStandardAgentSetup=true (finding C5 — the capability host is immutable once an agent exists)"); bad = 1
    if not p.get('enableAgentVnetInjection', {}).get('value'):
        print("!! prod requires enableAgentVnetInjection=true (finding C12 — private endpoints do not cover agent tool egress)"); bad = 1
    if upgrade != 'NoAutoUpgrade':
        print("!! prod requires modelVersionUpgradeOption=NoAutoUpgrade (finding C6)"); bad = 1
    if not p.get('enablePolicyAssignments', {}).get('value') or p.get('policyEffectMode', {}).get('value') != 'Deny':
        print("!! prod requires enablePolicyAssignments=true with policyEffectMode=Deny (finding C11 — validate.sh is a client-side check, not a control)"); bad = 1
    if int(p.get('conversationRetentionDays', {}).get('value', 90)) > 90:
        print("!! conversationRetentionDays > 90 (governance/THREADS_MEMORY.md retention)"); bad = 1
    if not cmk_uri:
        print("NOTE prod cmkKeyUri is empty — pass 1 creates the platform, then enterprise/landing-zone.bicep creates the CMK key and grants the encryption-user roles, then re-run this deployment with cmkKeyUri set (finding C22)")
text = open(params_file).read()
if re.search(r'@[A-Za-z0-9._%+-]+\.[A-Za-z]{2,}', text.replace('{owner-mailbox}', '')):
    print("!! e-mail address found in parameters file — use {placeholders}"); bad = 1
if re.search(r'(?i)(secret|password|token)"?\s*:\s*"[^{"][^"]{8,}"', text):
    print("!! literal secret-like value in parameters file"); bad = 1
print("policy OK" if not bad else "policy FAILED"); sys.exit(bad)
PY

if [ "${1:-}" = "--what-if" ]; then
  RG="${2:?resource group required}"
  echo ">> what-if against $RG (read-only)"
  az deployment group what-if --resource-group "$RG" \
    --template-file main.bicep --parameters "$PARAMS" --result-format FullResourcePayloads
fi
