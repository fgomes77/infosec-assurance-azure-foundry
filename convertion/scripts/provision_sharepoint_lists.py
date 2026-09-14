#!/usr/bin/env python3
"""Create (idempotently) the SharePoint lists the delivery Function writes to —
and keep their columns in step with the code that writes them.

Four lists carry the platform's state of record: the TPRM portfolio, the TPSRCA
score history, the TPA evidence cache and the supplier research ledger. Until
now they were provisioned by hand from a click-path, and their columns were
described in prose. Prose drifts: the documented column names for the portfolio
and history lists were NOT the names functions/delivery/function_app.py writes,
so a site built to the documentation would have taken a Graph 400 on every
portfolio_update and history_append — a failure that only shows up in
production, on the write that matters.

So the spec below is the source of truth, and `--check` proves it matches the
code by reading the `_list_upsert(...)` call sites out of function_app.py.

    python3 provision_sharepoint_lists.py --check     # CI gate, offline
    python3 provision_sharepoint_lists.py --dry-run   # print the plan
    python3 provision_sharepoint_lists.py --site-id <id>   # create/repair

Live mode needs Sites.Manage on the site for the signed-in principal
(enterprise/series/05-sharepoint-and-delivery-function.md §2) and is safe to
re-run: an existing list is reused, only missing columns are added, and nothing
is ever deleted or renamed.
"""

from __future__ import annotations

import argparse
import ast
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONV = HERE.parent
FUNCTION_APP = CONV / "functions" / "delivery" / "function_app.py"
GRAPH = "https://graph.microsoft.com/v1.0"

# kind -> the Graph columnDefinition facet. 'note' is multi-line text: the
# evidence cache and the research ledger store extracted JSON, which does not
# fit a single-line text column.
KINDS = {
    "text": {"text": {}},
    "note": {"text": {"allowMultipleLines": True, "textType": "plain"}},
    "datetime": {"dateTime": {"format": "dateTime"}},
    "number": {"number": {"decimalPlaces": "automatic"}},
    "bool": {"boolean": {}},
}

# const in function_app.py -> the list it names.
#   env        the app setting that can rename it per deployment
#   default    the display name the kit assumes
#   key        the column(s) an upsert matches on — must be indexed, because
#              these lists pass the 5 000-item view threshold within a year
#   columns    (name, kind, indexed)
LISTS: dict[str, dict] = {
    "PORTFOLIO_LIST": {
        "env": "PORTFOLIO_LIST_NAME",
        "default": "TPRM Portfolio",
        "purpose": "Current assurance state per supplier/service — written by "
                   "POST /api/portfolio_update after approval.",
        "key": ["Supplier", "Service"],
        "columns": [
            ("Supplier", "text", True), ("Service", "text", True),
            ("TPAStatus", "text", False),        # Ongoing | Complete
            ("LastReportType", "text", False), ("LastReportUrl", "text", False),
            ("LastRunId", "text", False), ("ApprovedBy", "text", False),
            ("UpdatedAt", "datetime", False),
        ],
    },
    "HISTORY_LIST": {
        "env": "HISTORY_LIST_NAME",
        "default": "TPSRCA History",
        "purpose": "Append-only score history — POST /api/history_append. "
                   "Never upserted: each assessment is its own row, so a "
                   "trend cannot be rewritten.",
        "key": [],
        "columns": [
            ("Supplier", "text", True), ("Service", "text", True),
            ("AssessmentDate", "datetime", False), ("Composite", "number", False),
            ("ReportType", "text", False), ("ReportUrl", "text", False),
            ("RunId", "text", False),
        ],
    },
    "EVIDENCE_CACHE_LIST": {
        "env": "EVIDENCE_CACHE_LIST_NAME",
        "default": "TPA Evidence Cache",
        "purpose": "Delta re-analysis of the TPA evidence tree (requirement "
                   "d2): facts extracted from a file, keyed on its Graph eTag.",
        "key": ["CacheKey"],
        "columns": [
            ("CacheKey", "text", True),          # <driveId>|<itemId>
            ("DriveId", "text", False), ("ItemId", "text", False),
            ("ETag", "text", False), ("FileName", "text", False),
            ("Facts", "note", False), ("ExtractorRef", "text", False),
            ("RunId", "text", False), ("StoredAt", "datetime", False),
        ],
    },
    "RESEARCH_LEDGER_LIST": {
        "env": "RESEARCH_LEDGER_LIST_NAME",
        "default": "Supplier Research Ledger",
        "purpose": "Every search, page read and authority lookup per supplier, "
                   "with its date, citation and originating action — read "
                   "before searching again (GET /api/research_ledger).",
        "key": ["RecordKey"],
        "columns": [
            ("RecordKey", "text", True),         # hash(supplier|service|source|query)
            ("Supplier", "text", True), ("Service", "text", False),
            ("SourceId", "text", True), ("Tool", "text", False),
            ("Tier", "text", False), ("Query", "note", False),
            ("Topic", "text", False), ("Url", "note", False),
            ("Title", "text", False), ("Citation", "note", False),
            ("Facts", "note", False), ("ObservedAt", "datetime", True),
            ("OriginatingAction", "text", False), ("RunId", "text", False),
        ],
    },
}

# Read-only to the Function; the watchlist is maintained by the team and only
# READ by workflows/scheduled-deepsearch.json. Provisioned here so one command
# builds every list the platform expects, and so its name stops being written
# two different ways in two different documents.
READ_ONLY_LISTS: dict[str, dict] = {
    "SUPPLIER_WATCHLIST": {
        "env": "SUPPLIER_WATCHLIST_NAME",
        "default": "Supplier Watchlist",
        "purpose": "Suppliers the weekly scheduled DeepSearch covers — read by "
                   "workflows/scheduled-deepsearch.json, written by the team.",
        "key": [],
        "columns": [
            ("SupplierName", "text", True), ("ServiceName", "text", False),
            ("SupplierDomain", "text", False), ("Active", "bool", False),
        ],
    },
}

ALL_LISTS = {**LISTS, **READ_ONLY_LISTS}


def _literal_keys(node: ast.AST) -> set[str] | None:
    """Keys of a dict literal, or None when the argument is not a literal."""
    if not isinstance(node, ast.Dict):
        return None
    out = set()
    for k in node.keys:
        if isinstance(k, ast.Constant) and isinstance(k.value, str):
            out.add(k.value)
        else:
            return None            # computed key: cannot be checked statically
    return out


def written_fields() -> dict[str, set[str]]:
    """{const name: every field name written there} from the _list_upsert call
    sites in function_app.py. Static, so the gate needs no Azure SDK."""
    tree = ast.parse(FUNCTION_APP.read_text(encoding="utf-8"))
    found: dict[str, set[str]] = {}
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "_list_upsert"):
            continue
        if not node.args or not isinstance(node.args[0], ast.Name):
            continue               # list name computed: out of scope
        const = node.args[0].id
        keys: set[str] = set()
        for arg in node.args[1:3]:
            got = _literal_keys(arg)
            if got is None:
                continue
            keys |= got
        found.setdefault(const, set()).update(keys)
    return found


def check() -> list[str]:
    problems: list[str] = []
    written = written_fields()
    if not written:
        problems.append("no _list_upsert call site found in "
                        "functions/delivery/function_app.py — this gate is "
                        "checking nothing; fix the parser before trusting it")
    for const, fields in sorted(written.items()):
        spec = LISTS.get(const)
        if not spec:
            problems.append(f"{const}: written by the Function but has no "
                            f"definition in provision_sharepoint_lists.py — "
                            f"the list would have to be created by hand")
            continue
        have = {c[0] for c in spec["columns"]}
        for missing in sorted(fields - have):
            problems.append(f"{spec['default']}: the Function writes column "
                            f"{missing!r} that the provisioning spec does not "
                            f"create — Graph rejects the write with 400")
    # the match columns must be indexed, or the $filter lookup fails once the
    # list passes the view threshold — silently, as a cache/ledger miss
    for const, spec in LISTS.items():
        indexed = {c[0] for c in spec["columns"] if c[2]}
        for key in spec["key"]:
            if key not in indexed:
                problems.append(f"{spec['default']}: upsert matches on {key!r} "
                                f"but that column is not indexed")
    # every list constant in the Function has a spec (including read-only ones)
    src = FUNCTION_APP.read_text(encoding="utf-8")
    for const, spec in ALL_LISTS.items():
        if const in LISTS and f"{const} = os.environ.get(" not in src:
            problems.append(f"{const} is specified here but no longer read by "
                            f"function_app.py — remove it or fix the name")
        if const in LISTS and f'os.environ.get("{spec["env"]}"' not in src:
            problems.append(f"{const}: function_app.py does not read the env "
                            f"var {spec['env']} this spec names")
    return problems


def plan() -> list[str]:
    lines = []
    for const, spec in ALL_LISTS.items():
        name = os.environ.get(spec["env"], spec["default"])
        lines.append(f"list {name!r} ({len(spec['columns'])} columns"
                     + (f", key {'+'.join(spec['key'])}" if spec["key"] else
                        ", append-only") + ")")
        for col, kind, indexed in spec["columns"]:
            lines.append(f"    {col:<18} {kind:<9}{' indexed' if indexed else ''}")
    return lines


def provision(site_id: str, dry: bool) -> int:
    import requests                                   # noqa: PLC0415
    from azure.identity import DefaultAzureCredential  # noqa: PLC0415

    token = DefaultAzureCredential().get_token(
        "https://graph.microsoft.com/.default").token
    head = {"Authorization": f"Bearer {token}"}
    created = repaired = 0
    for const, spec in ALL_LISTS.items():
        name = os.environ.get(spec["env"], spec["default"])
        got = requests.get(f"{GRAPH}/sites/{site_id}/lists",
                           params={"$filter": f"displayName eq '{name}'",
                                   "$expand": "columns"},
                           headers=head, timeout=30)
        got.raise_for_status()
        existing = (got.json().get("value") or [None])[0]
        if not existing:
            body = {"displayName": name,
                    "description": spec["purpose"][:255],
                    "list": {"template": "genericList"},
                    "columns": [{"name": c, "indexed": idx, **KINDS[k]}
                                for c, k, idx in spec["columns"]]}
            if dry:
                print(f"[dry-run] CREATE {name} "
                      f"({len(spec['columns'])} columns)")
            else:
                r = requests.post(f"{GRAPH}/sites/{site_id}/lists",
                                  json=body, headers=head, timeout=60)
                r.raise_for_status()
                print(f"created {name}")
            created += 1
            continue
        have = {c["name"] for c in existing.get("columns", [])}
        for col, kind, idx in spec["columns"]:
            if col in have:
                continue
            if dry:
                print(f"[dry-run] ADD COLUMN {name}.{col} ({kind})")
            else:
                r = requests.post(
                    f"{GRAPH}/sites/{site_id}/lists/{existing['id']}/columns",
                    json={"name": col, "indexed": idx, **KINDS[kind]},
                    headers=head, timeout=30)
                r.raise_for_status()
                print(f"added {name}.{col}")
            repaired += 1
    print(f"{'would create' if dry else 'created'} {created} list(s), "
          f"{'would add' if dry else 'added'} {repaired} column(s)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true",
                    help="offline gate: the spec matches the code that writes")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the plan; with --site-id, the exact changes")
    ap.add_argument("--site-id", default=os.environ.get("SHAREPOINT_SITE_ID", ""),
                    help="Graph site id (default: $SHAREPOINT_SITE_ID)")
    args = ap.parse_args()

    if args.check:
        problems = check()
        print(f">> SharePoint list provisioning — {len(ALL_LISTS)} list(s)")
        for p in problems:
            print(f"   FAIL {p}", file=sys.stderr)
        if problems:
            print(f"list gate FAILED — {len(problems)} finding(s)",
                  file=sys.stderr)
            return 1
        print("list gate OK — every column the Function writes is provisioned, "
              "every upsert key is indexed")
        return 0

    if args.dry_run and not args.site_id:
        print("\n".join(plan()))
        return 0
    if not args.site_id:
        sys.exit("--site-id or SHAREPOINT_SITE_ID is required "
                 "(or use --dry-run alone to print the plan)")
    return provision(args.site_id, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
