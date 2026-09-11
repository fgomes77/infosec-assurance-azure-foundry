#!/usr/bin/env python3
"""Manage the advisor's durable memory vector store (vs-assurance-memory).

Memory notes are small timestamped text files uploaded into the store —
auditable, listable, and individually deletable (GDPR minimisation).

Usage:
    python3 memory_store.py add "2026-09-11 | Supplier X | Residual risk \
accepted by CISO for finding F-12; review 2027-Q1"
    python3 memory_store.py add --from-file notes.txt
    python3 memory_store.py list
    python3 memory_store.py delete <file_id>
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import sys
import tempfile
from pathlib import Path

CONV = Path(__file__).resolve().parent.parent
try:
    from dotenv import load_dotenv
    load_dotenv(CONV / "setup" / ".env")
except ImportError:
    pass

MEMORY_STORE = "vs-assurance-memory"


def get_agents_client():
    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential
    endpoint = os.environ.get("PROJECT_ENDPOINT")
    if not endpoint:
        sys.exit("Set PROJECT_ENDPOINT (setup/.env)")
    return AIProjectClient(endpoint=endpoint,
                           credential=DefaultAzureCredential()).agents


def find_store(agents_client):
    for vs in agents_client.vector_stores.list():
        if vs.name == MEMORY_STORE:
            return vs
    sys.exit(f"{MEMORY_STORE} not found — run create_orchestrator.py first")


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_add = sub.add_parser("add")
    p_add.add_argument("note", nargs="?")
    p_add.add_argument("--from-file")
    sub.add_parser("list")
    p_del = sub.add_parser("delete")
    p_del.add_argument("file_id")
    args = ap.parse_args()

    agents_client = get_agents_client()
    store = find_store(agents_client)

    if args.cmd == "add":
        text = (Path(args.from_file).read_text(encoding="utf-8")
                if args.from_file else args.note)
        if not text:
            sys.exit("Provide a note or --from-file")
        stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        with tempfile.TemporaryDirectory() as td:
            f = Path(td) / f"memory-{stamp}.txt"
            f.write_text(f"[{stamp}]\n{text.strip()}\n", encoding="utf-8")
            up = agents_client.files.upload_and_poll(file_path=str(f),
                                                     purpose="assistants")
            agents_client.vector_store_files.create_and_poll(
                vector_store_id=store.id, file_id=up.id)
        print(f"stored {f.name} ({up.id})")
    elif args.cmd == "list":
        for vf in agents_client.vector_store_files.list(vector_store_id=store.id):
            print(vf.id)
    elif args.cmd == "delete":
        agents_client.vector_store_files.delete(vector_store_id=store.id,
                                                file_id=args.file_id)
        agents_client.files.delete(args.file_id)
        print(f"deleted {args.file_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
