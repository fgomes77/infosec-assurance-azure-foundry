#!/usr/bin/env python3
"""Gate for the authoritative-source layer.

Web reach is the one capability where a quiet inconsistency is a control
failure rather than an inconvenience: a source the registry promises but the
allow-list refuses is research that silently cannot happen, and a host the
allow-list permits but the registry does not explain is reach nobody decided
to grant. This gate makes the two agree, and makes every source carry the
things a citation needs.

    python3 check_knowledge_sources.py            # report, exit 1 on a finding
    python3 check_knowledge_sources.py --list     # report everything, exit 0

Offline and deterministic: no network call, no credentials.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONV = HERE.parent
PACK = CONV / "agents" / "knowledge-packs" / "authoritative-sources.md"

REQUIRED = ("id", "name", "authority", "domains", "covers", "use_for",
            "citation", "access", "tier", "refresh")
PRIVATE = re.compile(r"(^|\.)(local|internal|corp|intranet|test)$", re.I)


def audit() -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []
    reg = json.loads((CONV / "integrations" / "knowledge-sources.json")
                     .read_text(encoding="utf-8"))
    conns = json.loads((CONV / "integrations" / "registry.json")
                       .read_text(encoding="utf-8"))["connections"]
    sources = reg["sources"]

    seen: set[str] = set()
    for src in sources:
        sid = src.get("id", "<no id>")
        for field in REQUIRED:
            if not src.get(field):
                findings.append(("fields", f"{sid} has no {field} — a source "
                                           f"without it cannot be cited or "
                                           f"reviewed"))
        if sid in seen:
            findings.append(("fields", f"{sid} is declared twice"))
        seen.add(sid)
        if src.get("tier") not in (1, 2, 3):
            findings.append(("tiers", f"{sid} has tier {src.get('tier')!r} — "
                                      f"1 (authority), 2 (official/standard) "
                                      f"or 3 (signal only)"))
        # 2. An 'api:' source names a connection that exists and is read-only.
        access = str(src.get("access", ""))
        if access.startswith("api:"):
            cname = access.split(":", 1)[1]
            conn = conns.get(cname)
            if not conn:
                findings.append(("access", f"{sid} declares access {access!r} "
                                           f"but no such connection is "
                                           f"registered"))
            elif conn.get("type") not in ("openapi", "mcp"):
                findings.append(("access", f"{sid} -> {cname}: connection type "
                                           f"{conn.get('type')!r} cannot serve "
                                           f"a source"))
        elif access not in ("page:osint-proxy", "search:web-search"):
            findings.append(("access", f"{sid} has unknown access mode "
                                       f"{access!r} (see _access_modes)"))
        # 3. No source may point anywhere internal.
        for dom in src.get("domains", []):
            d = dom.strip().lower()
            if d.startswith("*"):
                continue
            if PRIVATE.search(d) or "." not in d:
                findings.append(("domains", f"{sid}: {dom!r} is not a public "
                                            f"domain"))

    # 4. The allow-list of record is the registry — regenerated, not edited.
    sys.path.insert(0, str(HERE))
    import sync_url_allowlist as sync  # noqa: E402
    want = sync.block()
    for target in sync.TARGETS:
        if target.is_file() and want not in target.read_text(encoding="utf-8"):
            findings.append((
                "allow-list",
                f"{target.relative_to(CONV)} is out of step with the registry "
                f"— run scripts/sync_url_allowlist.py"))

    # 5. Every tier-1 source is teachable: the pack names it or its authority.
    pack = PACK.read_text(encoding="utf-8").lower() if PACK.is_file() else ""
    if not pack:
        findings.append(("pack", "agents/knowledge-packs/"
                                 "authoritative-sources.md is missing — the "
                                 "agents have reach with no citation rule"))
    else:
        for src in sources:
            if src.get("tier") != 1:
                continue
            names = [src["id"].replace("-", " "), src["id"],
                     src["name"].split("(")[0].strip().lower()]
            first_domain = next((d for d in src["domains"]
                                 if not d.startswith("*")), "")
            names.append(first_domain.lower())
            if not any(n and n.lower() in pack for n in names):
                findings.append(("pack", f"tier-1 source {src['id']} is not "
                                         f"mentioned in the citation pack"))
    return findings


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()

    reg = json.loads((CONV / "integrations" / "knowledge-sources.json")
                     .read_text(encoding="utf-8"))
    findings = audit()
    checks = ("fields", "tiers", "access", "domains", "allow-list", "pack")
    print(f">> authoritative sources — {len(reg['sources'])} source(s), "
          f"{len(checks)} check(s)")
    by: dict[str, list[str]] = {}
    for check, msg in findings:
        by.setdefault(check, []).append(msg)
    for check in checks:
        hits = by.get(check, [])
        print(f"   {'ok  ' if not hits else 'FAIL'} {check}"
              f"{'' if not hits else f' — {len(hits)}'}")
        for msg in hits:
            print(f"        - {msg}", file=sys.stderr)
    if findings and not args.list:
        print(f"knowledge-source gate FAILED — {len(findings)} finding(s)",
              file=sys.stderr)
        return 1
    tiers = {t: sum(1 for s in reg["sources"] if s["tier"] == t)
             for t in (1, 2, 3)}
    print(f"knowledge-source gate OK — tier 1: {tiers[1]}, tier 2: {tiers[2]}, "
          f"tier 3: {tiers[3]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
