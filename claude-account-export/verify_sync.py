#!/usr/bin/env python3
"""Verify that the Claude account's synced skills match this GitHub backup.

Run from a fresh Claude Code (web) session after re-uploading skills on
claude.ai, so the session container carries the updated sync:

    python3 claude-account-export/verify_sync.py

It locates the account's synced skill bucket (~/.claude/skills/synced/<id>/),
compares every file against claude-account-export/skills/, and reports:
  - IDENTICAL files (content match)
  - DIFFERENT files (present in both, content differs)
  - ONLY IN SYNC   (on the account but not in this backup)
  - ONLY IN BACKUP (in this backup but not on the account)

Expected steady-state result after re-uploading the completed skill folders:
everything identical except the deliberately excluded forensic-persona skill
(ONLY IN SYNC) and this script/README/PERSONA/CAPABILITIES docs (backup-only,
outside skills/ so not compared). Bytecode caches are ignored.
"""

import hashlib
import sys
from pathlib import Path

IGNORE_PARTS = {"__pycache__", ".DS_Store"}
# manifest.json always differs: the backup copy is deliberately redacted and
# the synced copy carries fresh sync timestamps on every session.
IGNORE_FILES = {"manifest.json"}


def file_map(root: Path) -> dict:
    out = {}
    for p in root.rglob("*"):
        if (p.is_file() and not (set(p.parts) & IGNORE_PARTS)
                and p.relative_to(root).as_posix() not in IGNORE_FILES):
            out[p.relative_to(root).as_posix()] = hashlib.sha256(
                p.read_bytes()
            ).hexdigest()
    return out


def find_sync_bucket() -> Path:
    base = Path.home() / ".claude" / "skills" / "synced"
    buckets = [d for d in base.iterdir() if d.is_dir()] if base.is_dir() else []
    if not buckets:
        sys.exit(f"No synced skill bucket found under {base} — run this from a "
                 "Claude Code session with account skill sync enabled.")
    return max(buckets, key=lambda d: d.stat().st_mtime)


def main() -> int:
    backup = Path(__file__).resolve().parent / "skills"
    sync = find_sync_bucket()
    print(f"Sync bucket : {sync}\nBackup      : {backup}\n")

    a, b = file_map(sync), file_map(backup)
    same = sorted(k for k in a.keys() & b.keys() if a[k] == b[k])
    diff = sorted(k for k in a.keys() & b.keys() if a[k] != b[k])
    only_sync = sorted(a.keys() - b.keys())
    only_backup = sorted(b.keys() - a.keys())

    print(f"IDENTICAL      : {len(same)} files")
    for title, items in (("DIFFERENT", diff), ("ONLY IN SYNC", only_sync),
                         ("ONLY IN BACKUP", only_backup)):
        print(f"{title:15}: {len(items)} files")
        for k in items:
            print(f"    {k}")

    if not diff and not only_backup:
        print("\nRESULT: converged — every backup file matches the account "
              "sync (sync-only extras listed above are expected exclusions).")
        return 0
    print("\nRESULT: not yet converged — re-upload the skills listed under "
          "DIFFERENT / ONLY IN BACKUP on claude.ai, then re-run from a fresh "
          "session.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
