#!/usr/bin/env python3
"""Report drift between the account-synced skills (claude-account-export/
skills/<name>/ - the deployed source of truth, what convert_skills.py
converts) and the platform copies of the same skills
(platform-skills/public|examples/<name>/).

Precedence rule (governance/PLATFORM_SKILLS_DECISION.md): the account
copy wins; the platform copy is informational. A DIFFERENT result means
Anthropic shipped a newer built-in than the one synced to the account -
review, then re-sync the export; never convert the platform copy over
the account one. SHA-256 per file, like verify_sync.py did.

Usage: python3 diff_platform_copies.py        (exit 0 always; informational)
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from convert_skills import EXPORT, PLATFORM_ROOTS  # noqa: E402


def _tree(root: Path) -> dict[str, str]:
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob("*") if p.is_file() and "__pycache__" not in p.parts}


def report() -> list[str]:
    lines = []
    for tree, root in PLATFORM_ROOTS.items():
        if not root.is_dir():
            continue
        for plat in sorted(root.iterdir()):
            acct = EXPORT / plat.name
            if not plat.is_dir() or not (plat / "SKILL.md").is_file() \
                    or not (acct / "SKILL.md").is_file():
                continue
            a, b = _tree(acct), _tree(plat)
            if a == b:
                lines.append(f"IDENTICAL       {plat.name} ({tree})")
                continue
            only_a = sorted(set(a) - set(b))
            only_b = sorted(set(b) - set(a))
            changed = sorted(f for f in set(a) & set(b) if a[f] != b[f])
            lines.append(f"DIFFERENT       {plat.name} ({tree}): "
                         f"{len(changed)} changed, {len(only_a)} only in account, "
                         f"{len(only_b)} only in platform"
                         + (f" - {', '.join((changed + only_b)[:4])}" if changed or only_b else ""))
    return lines


if __name__ == "__main__":
    for line in report():
        print(line)
    sys.exit(0)
