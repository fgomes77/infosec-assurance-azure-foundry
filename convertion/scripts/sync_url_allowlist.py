#!/usr/bin/env python3
"""Regenerate the delivery Function's outbound allow-list from the
authoritative source registry.

The allow-list decides what the platform can reach on the public web. It was
a hand-kept Python list in functions/delivery/urlpolicy.py, while the reasons
for each entry lived in integrations/knowledge-sources.json — two files that
could disagree without anyone noticing, in the one place where disagreement
means either a source that cannot be read or a host that should not be
reachable.

This script makes the registry the single source: it rewrites the generated
block in urlpolicy.py (and the identical copy under functions/web-render/,
when it exists) from the registry's `domains`.

    python3 sync_url_allowlist.py            # rewrite
    python3 sync_url_allowlist.py --check    # CI gate: fail if out of date

Per-call supplier domains are NOT in the list: they are passed as
supplierDomain and allow-listed for that call only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONV = HERE.parent
REGISTRY = CONV / "integrations" / "knowledge-sources.json"
TARGETS = [CONV / "functions" / "delivery" / "urlpolicy.py",
           CONV / "functions" / "web-render" / "urlpolicy.py"]

BEGIN = "# BEGIN generated allow-list (scripts/sync_url_allowlist.py)"
END = "# END generated allow-list"


def domains() -> list[str]:
    """Every standing public domain in the registry, deduplicated.

    A '*' entry documents a per-call supplier domain (passed as
    supplierDomain) and is deliberately NOT a standing allow-list entry.
    """
    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    out: set[str] = set()
    for src in reg["sources"]:
        for d in src["domains"]:
            d = d.strip().lower()
            if d.startswith("*") or " " in d:
                continue
            out.add(d[4:] if d.startswith("www.") else d)
    return sorted(out)


def block() -> str:
    names = domains()
    lines = [BEGIN,
             "# Generated from integrations/knowledge-sources.json — do not",
             "# edit by hand: add the source there (with its tier, citation",
             "# rule and reason) and re-run the script. Adding a domain here",
             "# widens what the platform can reach: Tier-B change.",
             "DEFAULT_ALLOWLIST = ["]
    row = "   "
    for n in names:
        piece = f' "{n}",'
        if len(row) + len(piece) > 74:
            lines.append(row)
            row = "   "
        row += piece
    if row.strip():
        lines.append(row)
    lines += ["]", END]
    return "\n".join(lines)


def apply(target: Path, want: str) -> bool:
    """Return True when the file already matched."""
    text = target.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(BEGIN) + r".*?" + re.escape(END), re.S)
    if pattern.search(text):
        new = pattern.sub(lambda _: want, text)
    else:  # first run: replace the legacy hand-kept literal
        legacy = re.compile(
            r"# Curated public OSINT registries.*?^\]\n", re.S | re.M)
        if not legacy.search(text):
            sys.exit(f"{target}: neither the generated block nor the legacy "
                     f"DEFAULT_ALLOWLIST literal was found — refusing to guess")
        new = legacy.sub(want + "\n", text)
    if new == text:
        return True
    target.write_text(new, encoding="utf-8")
    return False


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true",
                    help="fail when a target is out of date (CI gate)")
    args = ap.parse_args()

    want = block()
    stale: list[str] = []
    for target in TARGETS:
        if not target.is_file():
            continue
        if args.check:
            text = target.read_text(encoding="utf-8")
            if want not in text:
                stale.append(str(target.relative_to(CONV)))
        else:
            matched = apply(target, want)
            print(f"{target.relative_to(CONV)}: "
                  f"{'unchanged' if matched else 'regenerated'} — "
                  f"{len(domains())} domains")
    if stale:
        print("STALE — the outbound allow-list does not match "
              "integrations/knowledge-sources.json:", file=sys.stderr)
        for s in stale:
            print(f"   {s}", file=sys.stderr)
        print("Run: python3 scripts/sync_url_allowlist.py", file=sys.stderr)
        return 1
    if args.check:
        print(f"allow-list in step with the source registry — "
              f"{len(domains())} domains")
    return 0


if __name__ == "__main__":
    sys.exit(main())
