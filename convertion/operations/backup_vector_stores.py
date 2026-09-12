#!/usr/bin/env python3
"""Export the platform's vector-store inventory and the shared memory notes
to a dated folder (operations/BACKUP_DR.md §3 B1), and restore memory notes
from such a folder (§4 R2).

Read-only by default: listing vector stores and downloading the memory
notes needs only the Azure AI User data-plane role every team member holds
(no PIM). The only write path is --restore, which re-adds memory notes to
vs-assurance-memory and refuses to run without --ticket and --confirm
(recorded Tier C act — team/TEAM_MODEL.md §12.1 / §13).

Output layout (--out, default operations/backups/<yyyy-mm-dd>):

    manifest.json     every vs-* store: id, name, status, file counts, files
                      [{id, filename, bytes, status, sha256?}], plus run info
    memory/<file>.txt the notes of vs-assurance-memory (content downloaded)
    README.txt        how to restore

Usage:
    python3 backup_vector_stores.py                         # all vs-* stores
    python3 backup_vector_stores.py --stores vs-assurance-memory
    python3 backup_vector_stores.py --dry-run               # offline plan
    python3 backup_vector_stores.py --restore <folder> --ticket {jira}-nnn --confirm
    python3 backup_vector_stores.py --upload-account {baseName}sa --upload-container backups
                                                            # EU blob copy (Container Apps Job)

--dry-run needs no Azure SDK and makes no network call: it prints the plan
and, when build/manifest.json exists, the stores deploy.sh would have
created. Never prints or stores a secret; PROJECT_ENDPOINT is not one.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONV = HERE.parent
BUILD = CONV / "build"
try:
    from dotenv import load_dotenv
    load_dotenv(CONV / "setup" / ".env")
except ImportError:
    pass

MEMORY_STORE = "vs-assurance-memory"
STORE_PREFIX = "vs-"
README = """Restore instructions (operations/BACKUP_DR.md §4)

R1  Agents and knowledge stores (vs-<agent>, vs-assurance-combined) are NOT
    restored from this folder: rebuild them from git + the claude.ai export
    with ../deploy.sh (or scripts/create_agents.py --only <agent>). The
    manifest here is drift evidence: compare file names/counts with the
    live stores after the rebuild.

R2  Memory store (vs-assurance-memory):
      python3 operations/backup_vector_stores.py --restore <this folder> \\
          --ticket {jira:INFOSEC-PLAT}-nnn --confirm
    Re-adds every note in memory/ whose SHA-256 is absent from the live
    store (idempotent). Record the restored count in the ticket.

Classification: internal. File under Governance/Backups/<date>/ on the
InfoSec Assurance site or the EU 'backups' blob container only.
"""


def utc_stamp() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def note_body(data: bytes) -> bytes:
    """memory_store.py writes '[<stamp>]\\n<text>\\n'. Hash the text only so a
    restored note (new stamp) is recognised as the same note."""
    lines = data.split(b"\n", 1)
    if lines and lines[0].startswith(b"[") and lines[0].endswith(b"]"):
        return lines[1] if len(lines) > 1 else b""
    return data


# ----------------------------------------------------------------- Azure

def get_agents_client():
    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential
    endpoint = os.environ.get("PROJECT_ENDPOINT")
    if not endpoint:
        sys.exit("Set PROJECT_ENDPOINT (setup/.env)")
    return AIProjectClient(endpoint=endpoint,
                           credential=DefaultAzureCredential()).agents


def download_file(agents_client, file_id: str) -> bytes | None:
    """Best effort across azure-ai-agents minors: get_content() streams bytes;
    fall back to None (metadata only) when content download is unsupported."""
    try:
        chunks = agents_client.files.get_content(file_id)
        return b"".join(chunks) if not isinstance(chunks, (bytes, bytearray)) \
            else bytes(chunks)
    except Exception as e:  # noqa: BLE001 - SDK surface varies by version
        print(f"  content download unavailable for {file_id}: {e}")
        return None


def list_stores(agents_client, wanted: set[str] | None):
    for vs in agents_client.vector_stores.list():
        name = getattr(vs, "name", "") or ""
        if not name.startswith(STORE_PREFIX):
            continue
        if wanted and name not in wanted:
            continue
        yield vs


def file_meta(agents_client, file_id: str) -> dict:
    try:
        f = agents_client.files.get(file_id)
        return {"filename": getattr(f, "filename", None),
                "bytes": getattr(f, "bytes", None),
                "created_at": str(getattr(f, "created_at", ""))}
    except Exception:  # noqa: BLE001
        return {"filename": None, "bytes": None, "created_at": ""}


# ----------------------------------------------------------------- export

def export(out: Path, wanted: set[str] | None, with_content: bool) -> int:
    agents_client = get_agents_client()
    out.mkdir(parents=True, exist_ok=True)
    mem_dir = out / "memory"
    manifest = {"exported_at": utc_stamp(), "kit_release":
                os.environ.get("KIT_RELEASE", "unversioned"),
                "endpoint_host": _host(os.environ.get("PROJECT_ENDPOINT", "")),
                "stores": []}
    stores = list(list_stores(agents_client, wanted))
    if not stores:
        print("no vs-* vector store found (run create_orchestrator.py first?)")
    for vs in stores:
        entry = {"id": vs.id, "name": vs.name, "status": str(getattr(vs, "status", "")),
                 "file_counts": _counts(vs), "files": []}
        is_memory = vs.name == MEMORY_STORE
        for vf in agents_client.vector_store_files.list(vector_store_id=vs.id):
            row = {"id": vf.id, "status": str(getattr(vf, "status", ""))}
            row.update(file_meta(agents_client, vf.id))
            if is_memory and with_content:
                data = download_file(agents_client, vf.id)
                if data is not None:
                    mem_dir.mkdir(exist_ok=True)
                    fname = row["filename"] or f"{vf.id}.txt"
                    (mem_dir / Path(fname).name).write_bytes(data)
                    row["sha256"] = sha256_bytes(note_body(data))
                    row["backup_path"] = f"memory/{Path(fname).name}"
            entry["files"].append(row)
        manifest["stores"].append(entry)
        print(f"{vs.name}: {len(entry['files'])} file(s)")
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2),
                                       encoding="utf-8")
    (out / "README.txt").write_text(README, encoding="utf-8")
    mem = next((s for s in manifest["stores"] if s["name"] == MEMORY_STORE), None)
    print(f"wrote {out / 'manifest.json'}"
          + (f" — memory notes exported: {len(mem['files'])}" if mem else
             f" — WARNING: {MEMORY_STORE} not found"))
    # A missing memory store is a warning, not a failure: on the first
    # deployment it does not exist yet (deploy.sh step 0 must not abort).
    return 0


def _counts(vs) -> dict:
    fc = getattr(vs, "file_counts", None)
    if fc is None:
        return {}
    return {k: getattr(fc, k) for k in ("total", "completed", "failed",
                                        "in_progress", "cancelled")
            if hasattr(fc, k)}


def _host(endpoint: str) -> str:
    return endpoint.split("//", 1)[-1].split("/", 1)[0] if endpoint else ""


# ---------------------------------------------------------------- restore

def restore(folder: Path, ticket: str) -> int:
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    mem = next((s for s in manifest["stores"] if s["name"] == MEMORY_STORE), None)
    if not mem:
        sys.exit(f"{folder} holds no {MEMORY_STORE} export")
    agents_client = get_agents_client()
    store = next((vs for vs in agents_client.vector_stores.list()
                  if vs.name == MEMORY_STORE), None)
    if store is None:
        sys.exit(f"{MEMORY_STORE} not found — run create_orchestrator.py first")

    live_hashes: set[str] = set()
    for vf in agents_client.vector_store_files.list(vector_store_id=store.id):
        data = download_file(agents_client, vf.id)
        if data is not None:
            live_hashes.add(sha256_bytes(note_body(data)))

    restored = skipped = 0
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    for row in mem["files"]:
        path = row.get("backup_path")
        if not path:
            continue
        data = (folder / path).read_bytes()
        h = sha256_bytes(note_body(data))
        if h in live_hashes:
            skipped += 1
            continue
        with tempfile.TemporaryDirectory() as td:
            f = Path(td) / f"memory-{stamp}-restored-{h[:8]}.txt"
            text = note_body(data).decode("utf-8", errors="replace").rstrip()
            f.write_text(f"[{stamp}] restored from {folder.name} under {ticket}\n"
                         f"{text}\n", encoding="utf-8")
            up = agents_client.files.upload_and_poll(file_path=str(f),
                                                     purpose="assistants")
            agents_client.vector_store_files.create_and_poll(
                vector_store_id=store.id, file_id=up.id)
        live_hashes.add(h)
        restored += 1
    print(f"restored {restored} note(s), skipped {skipped} already present "
          f"(ticket {ticket})")
    return 0


# ----------------------------------------------------------------- upload

def upload(out: Path, account: str, container: str) -> int:
    """Copy the export folder to <container>/<folder-name>/ in the platform's
    EU storage account with the caller's identity (managed identity in the
    Container Apps Job, az login for the owner). Needs azure-storage-blob
    (optional dependency; operations/BACKUP_DR.md §3)."""
    try:
        from azure.identity import DefaultAzureCredential
        from azure.storage.blob import BlobServiceClient
    except ImportError:
        sys.exit("upload needs azure-storage-blob (pip install azure-storage-blob)")
    svc = BlobServiceClient(f"https://{account}.blob.core.windows.net",
                            credential=DefaultAzureCredential())
    cc = svc.get_container_client(container)
    n = 0
    for f in sorted(out.rglob("*")):
        if f.is_file():
            with f.open("rb") as fh:
                cc.upload_blob(f"{out.name}/{f.relative_to(out).as_posix()}",
                               fh, overwrite=True)
            n += 1
    print(f"uploaded {n} file(s) to {container}/{out.name}/")
    return 0


# ---------------------------------------------------------------- dry run

def dry_run(out: Path, wanted: set[str] | None) -> int:
    print("DRY RUN — no Azure call, nothing written")
    print(f"  endpoint host : {_host(os.environ.get('PROJECT_ENDPOINT', '')) or '(unset)'}")
    print(f"  output folder : {out}")
    print(f"  stores filter : {sorted(wanted) if wanted else 'all vs-*'}")
    expected = [MEMORY_STORE, "vs-assurance-combined"]
    manifest = BUILD / "manifest.json"
    if manifest.exists():
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
            agents = data.get("agents", data if isinstance(data, list) else [])
            for a in agents:
                name = a.get("name") if isinstance(a, dict) else None
                if name and (a.get("knowledge") or a.get("knowledge_files")
                             or a.get("tools", {}) and "file_search" in str(a.get("tools"))):
                    expected.append(f"vs-{name}")
        except Exception as e:  # noqa: BLE001
            print(f"  (could not read build/manifest.json: {e})")
    else:
        print("  build/manifest.json absent — run scripts/convert_skills.py to "
              "list per-agent stores; memory + combined stores assumed")
    for name in sorted(set(expected)):
        if wanted and name not in wanted:
            continue
        flag = "  [content exported]" if name == MEMORY_STORE else ""
        print(f"  would inventory {name}{flag}")
    print("  would write manifest.json, README.txt"
          + (", memory/*.txt" if not wanted or MEMORY_STORE in wanted else ""))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", default=None,
                    help="output folder (default operations/backups/<yyyy-mm-dd>)")
    ap.add_argument("--stores", default=None,
                    help="comma-separated store names (default: every vs-*)")
    ap.add_argument("--no-content", action="store_true",
                    help="inventory only; do not download memory notes")
    ap.add_argument("--dry-run", action="store_true", help="offline plan")
    ap.add_argument("--restore", metavar="FOLDER",
                    help="re-add memory notes from an export folder")
    ap.add_argument("--ticket", default=None, help="change/incident ticket id "
                    "(required with --restore)")
    ap.add_argument("--confirm", action="store_true",
                    help="acknowledge that --restore writes to the shared store")
    ap.add_argument("--upload-account", default=os.environ.get("BACKUP_STORAGE_ACCOUNT"),
                    help="storage account name for an EU blob copy of the export")
    ap.add_argument("--upload-container", default=os.environ.get("BACKUP_CONTAINER", "backups"))
    args = ap.parse_args()

    if args.restore:
        if not (args.ticket and args.confirm):
            sys.exit("--restore requires --ticket <id> and --confirm "
                     "(operations/BACKUP_DR.md §4 R2)")
        if args.dry_run:
            print(f"DRY RUN — would restore memory notes from {args.restore} "
                  f"under ticket {args.ticket}")
            return 0
        return restore(Path(args.restore).resolve(), args.ticket)

    out = Path(args.out).resolve() if args.out else (
        Path(os.environ.get("BACKUP_OUT_DIR", HERE / "backups")).resolve()
        / dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d"))
    wanted = {s.strip() for s in args.stores.split(",") if s.strip()} \
        if args.stores else None
    if args.dry_run:
        rc = dry_run(out, wanted)
        if args.upload_account:
            print(f"  would upload to {args.upload_account}/{args.upload_container}/{out.name}/")
        return rc
    rc = export(out, wanted, with_content=not args.no_content)
    if rc == 0 and args.upload_account:
        rc = upload(out, args.upload_account, args.upload_container)
    return rc


if __name__ == "__main__":
    sys.exit(main())
