#!/usr/bin/env python3
"""Compare the platform's configured model deployments with a maintained model
retirement table and print upcoming retirements plus the review actions the
owner must take (enterprise/UPDATE_AND_UPGRADE_REVIEW_POLICY.md R1-R4).

Offline by design (--dry-run is the only mode; no Azure calls). Inputs:

    infra/main.bicep                  parameter defaults for the three tiers
    infra/main.parameters*.json       overrides (prod file wins when --params names it)
    enterprise/upgrade/model-deployment-policy.bicep   target pinned shape (informational)
    setup/.env (optional)             deployment names actually used by scripts
    retirement table                  --table <json>; default = the embedded table
                                      below, maintained by the owner at every
                                      quarterly platform currency review from
                                      https://learn.microsoft.com/en-us/azure/foundry/openai/concepts/model-retirement-schedule

Checks
  1. every tier has a NON-EMPTY explicit version (R1)            -> ERROR when empty
  2. main.bicep deployments carry versionUpgradeOption NoAutoUpgrade (R1) -> WARN if absent
  3. deploymentSku is DataZoneStandard or Standard (R8)           -> ERROR otherwise
  4. days until retirement per deployed model/version (R2)        -> ERROR < --ticket-days (120),
                                                                     WARN < --horizon (180)
  5. tool-support of the tier model vs the tier's toolset (R4)    -> ERROR when unsupported
  6. table freshness: 'reviewed' older than --max-table-age days  -> WARN

Usage
    python3 check_model_lifecycle.py --dry-run
    python3 check_model_lifecycle.py --dry-run --params infra/main.parameters.prod.json --horizon 180
    python3 check_model_lifecycle.py --dry-run --table Governance/Operations/model-retirement-table.json
    python3 check_model_lifecycle.py --write-table build/model-retirement-table.json   # export the embedded table for editing
    python3 check_model_lifecycle.py --dry-run --json build/lifecycle-report.json

Exit codes: 0 clean, 1 at least one ERROR (a review action is due), 3 input error.
Warnings never fail the run (CI uses the default; the monthly M3 run uses --strict
to fail on warnings as well).

Never changes anything. The decision on what to do with the output belongs to
Francisco Gustavo Gomes ({upn:francisco.gomes}); deputy review when he authors
the resulting change. Controls: ISO 27001:2022 A.8.32, A.8.9; ISO 42001 A.6.2.5;
DORA Art. 9(4)(e)-(f); EU AI Act Art. 9.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONV = HERE.parent.parent
MAIN_BICEP = CONV / "infra" / "main.bicep"
POLICY_BICEP = HERE / "model-deployment-policy.bicep"
ENV_FILE = CONV / "setup" / ".env"
REGISTRY = CONV / "integrations" / "registry.json"

# --------------------------------------------------------------------------- embedded retirement table
# Maintained by the owner. Source of every row: model retirement schedule
# (https://learn.microsoft.com/en-us/azure/foundry/openai/concepts/model-retirement-schedule,
# ms.date 2026-09-02) and the lifecycle policy (…/model-retirements, 2026-07-24).
# status: GA | Legacy | Deprecated | Retired | unknown. retirement_date: yyyy-mm-dd or null when
# the schedule lists the model but the date was not captured — a null date is itself a review action.
EMBEDDED_TABLE = {
    "reviewed": "2026-09-12",
    "source": "https://learn.microsoft.com/en-us/azure/foundry/openai/concepts/model-retirement-schedule",
    "source_date": "2026-09-02",
    "policy": {
        "ga_lifecycle_months": 18,
        "deprecated_at_months": 12,
        "min_notice_days_ga": 60,
        "replacement_declared_days_before": "90-120",
        "retired_http_status": 410,
    },
    "models": [
        {"name": "gpt-4o", "version": "2024-05-13", "status": "Deprecated", "retirement_date": "2026-10-01", "replacement": "gpt-5.1"},
        {"name": "gpt-4o", "version": "2024-08-06", "status": "Deprecated", "retirement_date": "2027-04-14", "replacement": "gpt-5.1"},
        {"name": "gpt-4o", "version": "2024-11-20", "status": "Legacy", "retirement_date": "2027-04-14", "replacement": "gpt-5.1"},
        {"name": "gpt-4o-mini", "version": "2024-07-18", "status": "Deprecated", "retirement_date": "2027-04-14", "replacement": "{owner-to-confirm}"},
        {"name": "o3-mini", "version": "2025-01-31", "status": "unknown", "retirement_date": None,
         "replacement": "o4-mini / gpt-5 family (tool-support table)",
         "note": "listed on the retirement schedule on 2026-09-02; date not captured — confirm at the next review"},
    ],
}

# Tool support by model — from the 'Tool support by region and model' table
# (https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/limits-quotas-regions#tool-support-by-region-and-model,
# ms.date 2026-09-07, GA). Refresh at every platform currency review. Models absent
# from this table are reported as 'not verified' (a warning), never assumed supported.
TOOL_SUPPORT = {
    "reviewed": "2026-09-12",
    "models": {
        "o3-mini":     {"openapi": False, "mcp": False, "azure_ai_search": False, "sharepoint": False, "web_search": False, "file_search": True, "code_interpreter": True, "bing_grounding": True},
        "gpt-4o":      {"openapi": True, "mcp": True, "azure_ai_search": True, "sharepoint": True, "web_search": True, "file_search": True, "code_interpreter": True, "bing_grounding": True},
        "gpt-4o-mini": {"openapi": True, "mcp": True, "azure_ai_search": False, "sharepoint": True, "web_search": True, "file_search": True, "code_interpreter": True, "bing_grounding": True},
    },
}
# registry tool name -> tool-support column
REGISTRY_TOOL_KIND = {
    "web-search": "web_search", "enx-gateway-mcp": "mcp",
    # every other registry tool is an OpenAPI spec (integrations/registry.json connections type openapi)
}


# --------------------------------------------------------------------------- readers
def read_bicep_params(path: Path) -> dict:
    """Extract `param <name> <type> = <default>` scalar defaults from a Bicep file."""
    text = path.read_text(encoding="utf-8")
    out: dict[str, str] = {}
    for m in re.finditer(r"^param\s+(\w+)\s+(string|int|bool)\s*=\s*(.+?)\s*$", text, re.M):
        name, _typ, raw = m.groups()
        raw = raw.split("//")[0].strip()
        out[name] = raw.strip("'") if raw.startswith("'") else raw
    out["_has_no_auto_upgrade"] = "NoAutoUpgrade" in text
    out["_deployment_count"] = len(re.findall(r"accounts/deployments@", text))
    return out


def read_params_file(path: Path | None) -> dict:
    if not path:
        return {}
    if not path.exists():
        sys.exit(f"parameters file not found: {path}")
    with open(path, encoding="utf-8") as fh:
        p = json.load(fh).get("parameters", {})
    return {k: v.get("value") for k, v in p.items()}


def read_env(path: Path) -> dict:
    env: dict[str, str] = {}
    if not path.exists():
        return env
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.split("#")[0].strip()
    return env


def read_registry_tiers(path: Path) -> dict[str, dict]:
    """tier -> {agent: [tool names]} from integrations/registry.json."""
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as fh:
        reg = json.load(fh)
    tiers: dict[str, dict] = {}
    for agent, spec in reg.get("agents", {}).items():
        if agent.startswith("_"):
            continue
        tiers.setdefault(spec.get("model_tier", "chat"), {})[agent] = list(spec.get("tools", []))
    return tiers


def load_table(path: Path | None) -> dict:
    if not path:
        return EMBEDDED_TABLE
    with open(path, encoding="utf-8") as fh:
        table = json.load(fh)
    for k in ("reviewed", "models"):
        if k not in table:
            sys.exit(f"retirement table {path} lacks '{k}'")
    return table


# --------------------------------------------------------------------------- checks
def days_until(date_str: str | None, today: dt.date) -> int | None:
    if not date_str:
        return None
    return (dt.date.fromisoformat(date_str) - today).days


def tier_rows(bicep: dict, params: dict, env: dict) -> list[dict]:
    def val(k: str) -> str:
        v = params.get(k, bicep.get(k, ""))
        return "" if v is None else str(v)
    rows = [
        {"tier": "chat", "name": val("modelName"), "version": val("modelVersion"),
         "format": val("chatModelFormat") or "OpenAI", "capacity": val("modelCapacity"),
         "env_deployment": env.get("MODEL_DEPLOYMENT_NAME")},
        {"tier": "reasoning", "name": val("reasoningModelName"), "version": val("reasoningModelVersion"),
         "format": val("reasoningModelFormat") or "OpenAI", "capacity": val("reasoningModelCapacity"),
         "env_deployment": env.get("REASONING_MODEL_DEPLOYMENT_NAME")},
        {"tier": "light", "name": val("lightModelName"), "version": val("lightModelVersion"),
         "format": val("lightModelFormat") or "OpenAI", "capacity": val("lightModelCapacity"),
         "env_deployment": env.get("LIGHT_MODEL_DEPLOYMENT_NAME")},
    ]
    return rows


def run_checks(rows: list[dict], bicep: dict, params: dict, table: dict, tiers: dict, args, today: dt.date) -> dict:
    findings: list[dict] = []

    def add(level: str, code: str, tier: str, msg: str, action: str) -> None:
        findings.append({"level": level, "code": code, "tier": tier, "message": msg, "action": action})

    # 6. table freshness
    reviewed = dt.date.fromisoformat(table["reviewed"])
    age = (today - reviewed).days
    if age > args.max_table_age:
        add("WARN", "TABLE-STALE", "-", f"retirement table reviewed {table['reviewed']} ({age} days ago)",
            "refresh the table from the retirement schedule at the platform currency review (policy §4 item 1)")

    # 3. SKU
    sku = str(params.get("deploymentSku", bicep.get("deploymentSku", "")))
    if sku not in ("DataZoneStandard", "Standard"):
        add("ERROR", "SKU-NOT-EU", "-", f"deploymentSku={sku!r}", "use DataZoneStandard (EU Data Zone) or Standard in an EU region (policy R8)")

    # 2. NoAutoUpgrade in main.bicep
    if not bicep.get("_has_no_auto_upgrade"):
        add("WARN", "NO-PIN-OPTION", "-", "infra/main.bicep deployments carry no versionUpgradeOption",
            "apply shared delta D-UP-1 (versionUpgradeOption: 'NoAutoUpgrade') or consume enterprise/upgrade/model-deployment-policy.bicep")

    by_key = {(m["name"], m["version"]): m for m in table["models"]}
    by_name: dict[str, list[dict]] = {}
    for m in table["models"]:
        by_name.setdefault(m["name"], []).append(m)

    for r in rows:
        tier, name, version = r["tier"], r["name"], r["version"]
        # 1. explicit version
        if not version:
            add("ERROR", "VERSION-EMPTY", tier, f"{name}: version is empty (provider default)",
                "set an explicit version in main.parameters*.json / main.bicep (policy R1); candidates: "
                + ", ".join(m["version"] for m in by_name.get(name, [])) or "see the retirement schedule")
        # 4. retirement
        entry = by_key.get((name, version))
        if entry is None and version and by_name.get(name):
            add("WARN", "VERSION-NOT-IN-TABLE", tier, f"{name} {version} not in the retirement table",
                "add the row from the retirement schedule; until then the retirement date is unknown")
        elif entry is None and not by_name.get(name):
            add("WARN", "MODEL-NOT-IN-TABLE", tier, f"{name} not in the retirement table",
                "add the model family to the table at the next review")
        if entry is not None:
            d = days_until(entry.get("retirement_date"), today)
            if d is None:
                add("WARN", "RETIREMENT-DATE-UNKNOWN", tier,
                    f"{name} {version} status={entry.get('status')} — retirement date not captured",
                    "confirm the date on the schedule page; if within the horizon open the change ticket (policy R2)")
            elif d < 0:
                add("ERROR", "RETIRED", tier, f"{name} {version} retired on {entry['retirement_date']} ({-d} days ago) — requests return HTTP 410",
                    f"emergency change: switch the tier to the reviewed replacement ({entry.get('replacement')}); policy §5")
            elif d < args.ticket_days:
                add("ERROR", "RETIREMENT-IMMINENT", tier,
                    f"{name} {version} ({entry.get('status')}) retires {entry['retirement_date']} in {d} days",
                    f"open {{jira:INFOSEC-PLAT}}-nnn now (≥ {args.ticket_days} days rule, policy R2); candidate = {entry.get('replacement')}; "
                    "run the six-phase migration (policy R3): freeze golden set → candidate deployment (model-deployment-policy.bicep enableCandidateDeployment) → run_evals.py --model-override → comparison set → staged switch")
            elif d < args.horizon:
                add("WARN", "RETIREMENT-UPCOMING", tier,
                    f"{name} {version} ({entry.get('status')}) retires {entry['retirement_date']} in {d} days",
                    f"plan the migration in the next platform currency review; candidate = {entry.get('replacement')}")
            elif entry.get("status") in ("Deprecated", "Legacy"):
                add("INFO", "DEPRECATED", tier,
                    f"{name} {version} is {entry['status']} (retires {entry['retirement_date']}, {d} days)",
                    "no action yet; new subscriptions cannot deploy Deprecated versions — keep the candidate plan current")
        # 5. tool support
        support = TOOL_SUPPORT["models"].get(name)
        agents = tiers.get(tier, {})
        needed: dict[str, set[str]] = {}
        for agent, tools in agents.items():
            for t in tools:
                kind = REGISTRY_TOOL_KIND.get(t, "openapi")
                needed.setdefault(kind, set()).add(agent)
        if support is None:
            if needed:
                add("WARN", "TOOL-SUPPORT-NOT-VERIFIED", tier, f"{name}: not in the embedded tool-support table",
                    "paste the row of the tool-support-by-region-and-model table into the checklist (policy R4)")
        else:
            for kind, ag in sorted(needed.items()):
                if not support.get(kind, False):
                    add("ERROR", "TOOL-UNSUPPORTED", tier,
                        f"{name} does not support '{kind}' but {len(ag)} agent(s) on this tier use it: {', '.join(sorted(ag))}",
                        "re-select the tier model (candidate with full tool support in the EU Data Zone) — policy R4 / MODEL_ROUTING.md; "
                        "attach_integrations.py must not attach tools the model cannot call")
        if r.get("env_deployment") and r["env_deployment"] != name:
            add("WARN", "ENV-MISMATCH", tier, f"setup/.env names deployment {r['env_deployment']!r} but Bicep deploys {name!r}",
                "align setup/.env with the Bicep parameters in the same change")

    level_rank = {"ERROR": 0, "WARN": 1, "INFO": 2}
    findings.sort(key=lambda f: (level_rank[f["level"]], f["tier"], f["code"]))
    errors = sum(1 for f in findings if f["level"] == "ERROR")
    warns = sum(1 for f in findings if f["level"] == "WARN")
    return {"findings": findings, "errors": errors, "warnings": warns}


# --------------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dry-run", action="store_true", help="offline check (the only mode; accepted for CI symmetry)")
    ap.add_argument("--params", type=Path, help="infra/main.parameters*.json to apply over the Bicep defaults")
    ap.add_argument("--table", type=Path, help="retirement table JSON (default: embedded table)")
    ap.add_argument("--write-table", type=Path, help="export the embedded retirement table to this path and exit")
    ap.add_argument("--horizon", type=int, default=180, help="days: retirements within this window are warnings")
    ap.add_argument("--ticket-days", type=int, default=120, help="days: retirements within this window are errors (ticket due)")
    ap.add_argument("--max-table-age", type=int, default=100, help="days before the table counts as stale")
    ap.add_argument("--today", help="yyyy-mm-dd (tests)")
    ap.add_argument("--json", type=Path, help="write the report here as JSON")
    ap.add_argument("--strict", action="store_true", help="warnings fail the run too")
    args = ap.parse_args()

    if args.write_table:
        args.write_table.parent.mkdir(parents=True, exist_ok=True)
        args.write_table.write_text(json.dumps(EMBEDDED_TABLE, indent=2), encoding="utf-8")
        print(f"embedded retirement table written to {args.write_table}")
        return 0

    today = dt.date.fromisoformat(args.today) if args.today else dt.date.today()
    if not MAIN_BICEP.exists():
        print(f"main.bicep not found at {MAIN_BICEP}")
        return 3
    bicep = read_bicep_params(MAIN_BICEP)
    params = read_params_file(args.params)
    env = read_env(ENV_FILE)
    table = load_table(args.table)
    tiers = read_registry_tiers(REGISTRY)
    rows = tier_rows(bicep, params, env)
    result = run_checks(rows, bicep, params, table, tiers, args, today)

    print(f"model lifecycle check — {today} — table reviewed {table['reviewed']} (source {table.get('source_date', '?')}); "
          f"params: {args.params or 'bicep defaults'}; policy module: {'present' if POLICY_BICEP.exists() else 'missing'}")
    print(f"{'tier':10} {'model':14} {'version':12} {'format':9} {'sku':17} {'agents':7}")
    sku = str(params.get("deploymentSku", bicep.get("deploymentSku", "")))
    for r in rows:
        print(f"{r['tier']:10} {r['name']:14} {(r['version'] or '(empty)'):12} {r['format']:9} {sku:17} {len(tiers.get(r['tier'], {})):7}")
    print()
    if not result["findings"]:
        print("no findings")
    for f in result["findings"]:
        print(f"[{f['level']}] {f['code']} ({f['tier']}): {f['message']}")
        print(f"        action: {f['action']}")
    print()
    print(f"errors {result['errors']}, warnings {result['warnings']} — decision and change ticket: owner {{upn:francisco.gomes}} "
          "(deputy review when owner-authored); this script changed nothing")

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        report = {"generated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "today": today.isoformat(),
                  "table_reviewed": table["reviewed"], "params": str(args.params) if args.params else None,
                  "deployments": rows, "sku": sku, **result}
        args.json.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"report: {args.json}")

    if result["errors"] or (args.strict and result["warnings"]):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
