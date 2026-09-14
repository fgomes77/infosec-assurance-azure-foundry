#!/usr/bin/env python3
"""EU-residency assertion for the kit (governance/DATA_PROTECTION_GUARDRAILS.md
§3 "Residency": *the deploy job alone talks to Azure (EU endpoints) and must
fail on any non-EU location*).

`infra/validate.sh` already checks that `infra/main.parameters*.json` name a
region inside `main.bicep`'s own `@allowed` list. That is a *self*-consistency
check: widen the `@allowed` list to `eastus` and it still passes. This module
is the check that cannot be widened from inside the kit — it holds an explicit
EU/EEA region set and asserts every place a region is chosen against it:

    1. infra/main.bicep                      @allowed([...]) param location
    2. enterprise/landing-zone.bicep         @allowed([...]) param location
    3. enterprise/azure-policy-assignments.bicep  allowedLocations array
    4. every *.parameters*.json              location value
    5. deploymentSku                         Global* routes inference out of the EU
    6. AZURE_LOCATION / DEPLOY_LOCATION      the region the runner would deploy to
    7. PROJECT_ENDPOINT / any *.azure.com    no non-EU region token in an endpoint
    8. --live                                the regions of the resources that
                                             actually exist in the resource group

Two ways to run it — both used:

    python3 -m pytest convertion/ci/tests -q        # PR gate (job `gates`)
    python3 convertion/ci/tests/test_residency.py   # deploy gate, no pytest needed
    python3 convertion/ci/tests/test_residency.py --live   # + `az resource list`

The standalone mode exists so `.github/workflows/deploy.yml` can assert
residency *before* `azure/login` on a runner that only carries the data-plane
requirements, and again after login with `--live`.

READ-ONLY: parses files, reads environment variables, and in `--live` mode
issues `az ... list`/`show` calls only.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONV = HERE.parent.parent                 # convertion/
ROOT = CONV.parent                        # repository root

# Azure regions inside the EU/EEA. Euronext evidence, vector stores and model
# inference may sit in these and nowhere else (README §Residency; GDPR Art. 44
# — no transfer outside the EEA; DORA Art. 28 register). Switzerland and
# Norway are EEA/adequacy-decision geographies and are listed because
# infra/main.bicep offers them; the UK (uksouth/ukwest) is NOT in this set.
#
# Adding a region here is a Tier C platform change: it widens the data
# boundary. It is reviewed by the accountable owner + deputy (CODEOWNERS
# covers convertion/ci/ and convertion/infra/).
EU_EEA_REGIONS = frozenset({
    "austriaeast",
    "francecentral", "francesouth",
    "germanynorth", "germanywestcentral",
    "italynorth",
    "northeurope",          # Ireland
    "norwayeast", "norwaywest",
    "polandcentral",
    "spaincentral",
    "swedencentral", "swedensouth",
    "switzerlandnorth", "switzerlandwest",
    "westeurope",           # Netherlands
})

# Regions that must never appear: a short, explicit deny list so a typo that
# happens to look like a region is caught even if it is absent from the set
# above for another reason.
FORBIDDEN_REGIONS = frozenset({
    "eastus", "eastus2", "westus", "westus2", "westus3", "centralus",
    "northcentralus", "southcentralus", "westcentralus",
    "uksouth", "ukwest",
    "canadacentral", "canadaeast", "brazilsouth",
    "eastasia", "southeastasia", "japaneast", "japanwest",
    "australiaeast", "australiasoutheast", "centralindia", "southindia",
    "koreacentral", "uaenorth", "southafricanorth", "israelcentral",
})

# `global` is not a region: private DNS zones, Bing grounding and policy
# assignments are region-less resources and Azure reports their location as
# `global`. The allowed-locations policy must list it or those resources cannot
# be created at all (enterprise/azure-policy-assignments.bicep, README
# §Residency). It carries no data at rest, so it is not a residency exception.
REGIONLESS = frozenset({"global"})

# Inference routing. A `Global*` SKU may serve the request from any Microsoft
# region on the planet; `DataZoneStandard` keeps it inside the EU Data Zone and
# `Standard` inside the account's own region (infra/validate.sh agrees).
EU_SAFE_SKUS = frozenset({"DataZoneStandard", "Standard", "ProvisionedManaged"})

BICEP_LOCATION_SOURCES = (
    "infra/main.bicep",
    "enterprise/landing-zone.bicep",
)


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def _read(rel: str) -> str:
    return (CONV / rel).read_text(encoding="utf-8")


def allowed_locations(rel: str) -> set[str]:
    """The `@allowed([...])` list attached to `param location` in a Bicep file."""
    text = _read(rel)
    m = re.search(r"@allowed\(\[(.*?)\]\)\s*(?:@\w+[^\n]*\s*)*param\s+location\b",
                  text, re.S)
    assert m, f"{rel}: no @allowed([...]) list on `param location` — the region " \
              f"is unconstrained, which is exactly what this gate forbids"
    return set(re.findall(r"'([a-z0-9]+)'", m.group(1)))


def policy_allowed_locations() -> set[str]:
    """The `allowedLocations` array of the preventive Azure Policy assignment."""
    text = _read("enterprise/azure-policy-assignments.bicep")
    m = re.search(r"param\s+allowedLocations\s+array\s*=\s*\[(.*?)\]", text, re.S)
    assert m, "azure-policy-assignments.bicep: no allowedLocations array"
    return set(re.findall(r"'([a-z0-9]+)'", m.group(1)))


def parameter_files() -> list[Path]:
    out: list[Path] = []
    for pattern in ("infra/*.parameters*.json", "enterprise/*.parameters*.json"):
        out.extend(sorted(CONV.glob(pattern)))
    assert out, "no ARM parameter files found — the glob or the layout changed"
    return out


def param_value(path: Path, name: str):
    doc = json.loads(path.read_text(encoding="utf-8"))
    return doc.get("parameters", {}).get(name, {}).get("value")


def is_placeholder(value: str) -> bool:
    """`{brace}`, `<angle>` and `${VAR}` forms are documented placeholders, not
    values (governance/DATA_PROTECTION_GUARDRAILS.md; .gitleaks.toml §1)."""
    return bool(re.search(r"[{<]|\$\{", value or ""))


# --------------------------------------------------------------------------
# 1-3. the region allow-lists the platform is built from
# --------------------------------------------------------------------------
def test_bicep_location_allowlists_are_eu_only() -> None:
    for rel in BICEP_LOCATION_SOURCES:
        allowed = allowed_locations(rel)
        assert allowed, f"{rel}: empty @allowed list"
        outside = sorted(allowed - EU_EEA_REGIONS)
        assert not outside, (
            f"{rel}: region(s) outside the EU/EEA in the location allow-list: "
            f"{outside}. Euronext evidence may not be stored or processed there "
            f"(governance/DATA_PROTECTION_GUARDRAILS.md §3)")
        forbidden = sorted(allowed & FORBIDDEN_REGIONS)
        assert not forbidden, f"{rel}: explicitly forbidden region(s): {forbidden}"


def test_policy_assignment_pins_eu_locations() -> None:
    """C11: the preventive Azure Policy is the control that stops a resource
    being created outside the EU even by someone bypassing this repository."""
    allowed = policy_allowed_locations()
    assert allowed, "azure-policy-assignments.bicep: empty allowedLocations"
    outside = sorted(allowed - EU_EEA_REGIONS - REGIONLESS)
    assert not outside, (
        f"azure-policy-assignments.bicep: allowedLocations lets resources be "
        f"created outside the EU/EEA: {outside}")


def test_policy_allowlist_is_not_wider_than_the_template() -> None:
    """The preventive policy must not permit a region the template refuses —
    that would let a portal-created resource sit where the kit never would."""
    extra = sorted(policy_allowed_locations()
                   - allowed_locations("infra/main.bicep") - REGIONLESS)
    assert not extra, (
        f"azure-policy-assignments.bicep allows region(s) infra/main.bicep does "
        f"not: {extra}. Keep the policy at or inside the template's allow-list")


# --------------------------------------------------------------------------
# 4-5. the regions and SKUs actually selected
# --------------------------------------------------------------------------
def test_parameter_files_select_an_eu_region() -> None:
    for path in parameter_files():
        loc = param_value(path, "location")
        if loc is None or is_placeholder(str(loc)):
            continue
        rel = path.relative_to(ROOT)
        assert loc in EU_EEA_REGIONS, (
            f"{rel}: location {loc!r} is outside the EU/EEA")
        assert loc not in FORBIDDEN_REGIONS, f"{rel}: forbidden location {loc!r}"


def test_parameter_files_do_not_route_inference_outside_the_eu() -> None:
    for path in parameter_files():
        sku = param_value(path, "deploymentSku")
        if sku is None or is_placeholder(str(sku)):
            continue
        rel = path.relative_to(ROOT)
        assert sku in EU_SAFE_SKUS, (
            f"{rel}: deploymentSku {sku!r} may serve inference from outside the "
            f"EU Data Zone — use one of {sorted(EU_SAFE_SKUS)} (finding C5/C6)")


# --------------------------------------------------------------------------
# 6-7. what THIS runner would deploy to — the deploy-time assertion
# --------------------------------------------------------------------------
def test_environment_location_is_eu() -> None:
    """Fails the deploy job when the runner's environment names a non-EU region.
    Skipped (vacuously true) on a PR runner, which sets none of these."""
    for var in ("AZURE_LOCATION", "DEPLOY_LOCATION", "LOCATION", "AZURE_REGION"):
        value = (os.environ.get(var) or "").strip().lower().replace(" ", "")
        if not value or is_placeholder(value):
            continue
        assert value in EU_EEA_REGIONS, (
            f"{var}={value!r} is outside the EU/EEA — this deployment is refused "
            f"(governance/DATA_PROTECTION_GUARDRAILS.md §3)")


def test_endpoints_name_no_non_eu_region() -> None:
    """Foundry/Function endpoints carry their region in the hostname. A
    `*.eastus.*` endpoint in the environment means the deploy would target a
    non-EU account even if AZURE_LOCATION looks right."""
    for var in ("PROJECT_ENDPOINT", "FOUNDRY_ENDPOINT", "AZURE_OPENAI_ENDPOINT",
                "DELIVERY_FUNCTION_URL", "SEARCH_ENDPOINT"):
        value = (os.environ.get(var) or "").strip().lower()
        if not value or is_placeholder(value):
            continue
        hit = sorted(r for r in FORBIDDEN_REGIONS if re.search(rf"\b{r}\b|[.\-]{r}[.\-]", value))
        assert not hit, f"{var} points at a non-EU region {hit}: {value[:60]}…"


# --------------------------------------------------------------------------
# 8. --live: the regions of the resources that exist right now
# --------------------------------------------------------------------------
def live_resource_locations(resource_group: str) -> list[tuple[str, str]]:
    """READ-ONLY `az resource list`. Returns [(name, location), ...]."""
    if not shutil.which("az"):
        raise RuntimeError("az CLI not found — cannot run the live residency check")
    proc = subprocess.run(
        ["az", "resource", "list", "--resource-group", resource_group,
         "--query", "[].{name:name,location:location}", "-o", "json"],
        capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"az resource list failed: {proc.stderr.strip()[:300]}")
    return [(r.get("name", "?"), (r.get("location") or "").lower())
            for r in json.loads(proc.stdout or "[]")]


def check_live(resource_group: str) -> list[str]:
    problems = []
    resources = live_resource_locations(resource_group)
    for name, loc in resources:
        if loc in ("global", ""):      # Front Door, DNS zones, policy: no region
            continue
        if loc not in EU_EEA_REGIONS:
            problems.append(f"{name}: {loc}")
    print(f"   {len(resources)} resource(s) in {resource_group}, "
          f"{len(problems)} outside the EU/EEA")
    return problems


# --------------------------------------------------------------------------
# standalone runner (no pytest on the deploy runner)
# --------------------------------------------------------------------------
def main(argv: list[str]) -> int:
    live = "--live" in argv
    checks = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failures = 0
    print(f">> EU residency gate — {len(checks)} offline check(s)"
          f"{' + live resource-group scan' if live else ''}")
    for fn in checks:
        try:
            fn()
            print(f"   ok   {fn.__name__}")
        except AssertionError as exc:
            print(f"   FAIL {fn.__name__}: {exc}")
            failures += 1
    if live:
        rg = os.environ.get("AZURE_RESOURCE_GROUP", "").strip()
        if not rg or is_placeholder(rg):
            print("   FAIL live: AZURE_RESOURCE_GROUP is not set to a real "
                  "resource group — cannot assert live residency")
            failures += 1
        else:
            try:
                problems = check_live(rg)
            except RuntimeError as exc:
                print(f"   FAIL live: {exc}")
                failures += 1
            else:
                for p in problems:
                    print(f"   FAIL live resource outside the EU/EEA — {p}")
                failures += len(problems)
                if not problems:
                    print("   ok   live resources are all EU/EEA-resident")
    print("residency gate OK" if not failures else
          f"residency gate FAILED ({failures} finding(s))")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
