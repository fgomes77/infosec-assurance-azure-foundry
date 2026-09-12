#!/usr/bin/env python3
"""Housekeeping for the Foundry project: orphaned vector stores, unreferenced
files and old threads (cost, quota and data-retention footprint -
governance/DATA_PROTECTION_GUARDRAILS.md). DRY-RUN by default; pass
--apply to delete. Never touches vs-assurance-memory or anything a live
agent references.

    python3 cleanup_foundry.py --stores              # vs-* stores no agent uses
    python3 cleanup_foundry.py --files               # files not in any store / agent
    python3 cleanup_foundry.py --threads --older-than 30
    python3 cleanup_foundry.py --stores --files --apply

Run monthly (operations/RUNBOOK.md) after an approval; the run prints
exactly what it would remove so the list can be filed as evidence.
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import sys
from pathlib import Path

CONV = Path(__file__).resolve().parent.parent
try:
    from dotenv import load_dotenv
    load_dotenv(CONV / "setup" / ".env")
except ImportError:
    pass

PROTECTED_STORES = {"vs-assurance-memory"}


def client():
    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential
    endpoint = os.environ.get("PROJECT_ENDPOINT")
    if not endpoint:
        sys.exit("Set PROJECT_ENDPOINT (setup/.env)")
    return AIProjectClient(endpoint=endpoint, credential=DefaultAzureCredential()).agents


def _res(agent) -> dict:
    r = agent.tool_resources
    return r.as_dict() if hasattr(r, "as_dict") else dict(r or {})


def referenced(ac) -> tuple[set[str], set[str]]:
    """(vector store ids, file ids) referenced by live agents."""
    stores, files = set(), set()
    for a in ac.list_agents():
        res = _res(a)
        stores |= set((res.get("file_search") or {}).get("vector_store_ids") or [])
        files |= set((res.get("code_interpreter") or {}).get("file_ids") or [])
    return stores, files


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stores", action="store_true")
    ap.add_argument("--files", action="store_true")
    ap.add_argument("--threads", action="store_true")
    ap.add_argument("--older-than", type=int, default=30, metavar="DAYS")
    ap.add_argument("--apply", action="store_true", help="really delete")
    args = ap.parse_args()
    if not (args.stores or args.files or args.threads):
        ap.error("choose --stores, --files and/or --threads")

    ac = client()
    used_stores, used_files = referenced(ac)
    mode = "DELETE" if args.apply else "would delete"
    removed = 0

    if args.stores or args.files:
        all_stores = list(ac.vector_stores.list())
        for vs in all_stores:
            if vs.name in PROTECTED_STORES:
                used_stores.add(vs.id)
        # files inside every store that stays count as referenced
        for vs in all_stores:
            if vs.id in used_stores or not args.stores:
                for vf in ac.vector_store_files.list(vector_store_id=vs.id):
                    used_files.add(vf.id)

    if args.stores:
        for vs in all_stores:
            if vs.id in used_stores:
                continue
            print(f"{mode} store {vs.id} {vs.name!r}")
            removed += 1
            if args.apply:
                ac.vector_stores.delete(vs.id)

    if args.files:
        for f in ac.files.list().data if hasattr(ac.files.list(), "data") else ac.files.list():
            if f.id in used_files or getattr(f, "purpose", "") != "assistants":
                continue
            print(f"{mode} file {f.id} {getattr(f, 'filename', '')!r}")
            removed += 1
            if args.apply:
                ac.files.delete(f.id)

    if args.threads:
        cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=args.older_than)
        for th in ac.threads.list():
            created = getattr(th, "created_at", None)
            if created is None or created > cutoff:
                continue
            print(f"{mode} thread {th.id} (created {created:%Y-%m-%d})")
            removed += 1
            if args.apply:
                ac.threads.delete(th.id)

    print(f"\n{removed} objects {'deleted' if args.apply else 'listed (dry run; add --apply)'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
