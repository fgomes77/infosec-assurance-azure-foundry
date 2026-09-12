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
    python3 memory_store.py import --from-file export.md --dry-run
    python3 memory_store.py import --from-file export.md --approved-by "{upn}"

`import` carries the safeguards of the claude.ai import-memory skill into
the shared TEAM store (governance/MEMORY_IMPORT.md): the export is DATA,
never instructions (instruction-like lines are dropped); additive only;
the privacy filter removes special-category / personal-profile lines
(GDPR Art. 9, health, beliefs, orientation, biometrics, criminal record,
private contact details); at most MAX_BATCH notes per run; nothing is
written without --approved-by (the plan is printed first, --dry-run shows
it and stops). `add` applies the same special-category rejection.
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
MAX_BATCH = 50

import re  # noqa: E402

SPECIAL_CATEGORY = re.compile(
    r"(?i)\b(health|medical|diagnos\w*|disabilit\w*|pregnan\w*|religio\w*|"
    r"belief|ethnic\w*|racial|sexual|orientation|biometric|genetic|"
    r"trade[- ]union|political (opinion|party)|criminal|conviction|"
    r"home address|date of birth|passport|national id|social security|"
    r"salary|bank account|iban)\b")
INSTRUCTION_LIKE = re.compile(
    r"(?i)^\s*(#+\s*)?(system|assistant|user)\s*:|^\s*(ignore|disregard|you must|"
    r"always|never|from now on|act as|pretend)\b|<\s*/?\s*(system|instructions?)\s*>")
PERSONAL_PROFILE = re.compile(r"(?i)^\s*(/?profile\.md|/?people/|my (name|age|family|partner))")


def privacy_filter(lines: list[str]) -> tuple[list[str], list[tuple[str, str]]]:
    """Return (kept, dropped[(reason, line)]) - the import-memory rules."""
    kept, dropped = [], []
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith(("---", "```")):
            continue
        if INSTRUCTION_LIKE.search(line):
            dropped.append(("instruction-like", line))
        elif SPECIAL_CATEGORY.search(line):
            dropped.append(("special-category / personal data", line))
        elif PERSONAL_PROFILE.search(line):
            dropped.append(("personal profile (out of scope)", line))
        else:
            kept.append(line.lstrip("-*# ").strip())
    return kept, dropped


def store_note(agents_client, store, text: str) -> str:
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / f"memory-{stamp}.txt"
        f.write_text(f"[{stamp}]\n{text.strip()}\n", encoding="utf-8")
        up = agents_client.files.upload_and_poll(file_path=str(f),
                                                 purpose="assistants")
        agents_client.vector_store_files.create_and_poll(
            vector_store_id=store.id, file_id=up.id)
    return f"{f.name} ({up.id})"


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
    p_imp = sub.add_parser("import", help="filtered, approved bulk import")
    p_imp.add_argument("--from-file", required=True)
    p_imp.add_argument("--dry-run", action="store_true")
    p_imp.add_argument("--approved-by", default="",
                       help="UPN of the approver; required to write")
    args = ap.parse_args()

    if args.cmd == "import":
        lines = Path(args.from_file).read_text(encoding="utf-8").splitlines()
        kept, dropped = privacy_filter(lines)
        print(f"plan: {len(kept)} notes to add, {len(dropped)} lines dropped")
        for reason, line in dropped:
            print(f"  drop [{reason}] {line[:70]}")
        for line in kept[:MAX_BATCH]:
            print(f"  add  {line[:90]}")
        if len(kept) > MAX_BATCH:
            print(f"  ... {len(kept) - MAX_BATCH} more: re-run for the next batch "
                  f"(MAX_BATCH={MAX_BATCH})")
        if args.dry_run or not args.approved_by:
            print("nothing written" + ("" if args.dry_run else
                                      " - pass --approved-by <upn> to apply"))
            return 0
        agents_client = get_agents_client()
        store = find_store(agents_client)
        for line in kept[:MAX_BATCH]:
            print("stored", store_note(agents_client, store,
                                       f"{line} | imported, approved by {args.approved_by}"))
        return 0

    agents_client = get_agents_client()
    store = find_store(agents_client)

    if args.cmd == "add":
        text = (Path(args.from_file).read_text(encoding="utf-8")
                if args.from_file else args.note)
        if not text:
            sys.exit("Provide a note or --from-file")
        if SPECIAL_CATEGORY.search(text):
            sys.exit("rejected: special-category / personal data pattern in the "
                     "note (governance/DATA_PROTECTION_GUARDRAILS.md)")
        print("stored", store_note(agents_client, store, text))
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
