"""Shared helpers for the deployment scripts: retry with backoff, parallel
file uploads, and a content-hash upload cache.

The cache (build/upload-cache.json) maps sha256 -> Foundry file id so a file
already uploaded this deployment cycle (including byte-identical twins
across agents, e.g. the duplicated slide-generator references) is reused
instead of re-uploaded — faster, cheaper, and consistent.
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Lock

MAX_ATTEMPTS = 4
UPLOAD_WORKERS = 8


def retry(fn, *args, what: str = "call", **kwargs):
    """Run fn with exponential backoff (1s, 2s, 4s + jitter); re-raise on
    the final failure so errors stay visible, never swallowed."""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            return fn(*args, **kwargs)
        except Exception as e:  # noqa: BLE001 - transport/service errors vary
            if attempt == MAX_ATTEMPTS:
                raise
            delay = 2 ** (attempt - 1) + random.uniform(0, 0.5)
            print(f"  retry {attempt}/{MAX_ATTEMPTS - 1} for {what} "
                  f"after error: {e} (waiting {delay:.1f}s)")
            time.sleep(delay)


FILE_MAP_MARKER = "## FILE MAP (code_interpreter attachments)"
ADVISORY_MARKER = "# Advisory-system addendum"
# Routing table injected at deploy time by create_orchestrator.py /
# create_agents.py in place of the retired ConnectedAgentTool (finding C2,
# enterprise/series/06-agents-conversion-and-deploy.md §D). Stripped before
# hashing so the offline charter hash stays stable.
ROUTING_MARKER = "## ROUTING TABLE (live agents, injected at deploy time)"


def kit_metadata() -> dict:
    """Metadata stamped on every agent create/update (operations/LIFECYCLE.md
    §1 V4): the platform release tag exported by deploy.sh."""
    return {"kit_release": os.environ.get("KIT_RELEASE", "unversioned"),
            "managed_by": "convertion-kit"}


def file_map_block(pairs: list[tuple[str, str]]) -> str:
    """Instructions block mapping original file names to Foundry file ids
    (code_interpreter mounts files as /mnt/data/<file-id>, names are lost).
    Appended at deploy time; verify_deployment.py strips it before hashing."""
    if not pairs:
        return ""
    rows = "\n".join(f"| `{n}` | `/mnt/data/{i}` |" for n, i in pairs)
    return (f"\n\n{FILE_MAP_MARKER}\n\n| original file | path in the sandbox |"
            f"\n|---|---|\n{rows}\n")


def strip_deploy_blocks(instructions: str) -> str:
    """Remove the deploy-time additions (FILE MAP, advisory addendum,
    routing table) so a live agent's instructions can be compared with
    build/agents/*/instructions.md."""
    for marker in (FILE_MAP_MARKER, ADVISORY_MARKER, ROUTING_MARKER):
        i = instructions.find(marker)
        if i >= 0:
            instructions = instructions[:i].rstrip().removesuffix("---").rstrip()
    return instructions.rstrip() + "\n"


def endpoint_key() -> str:
    return hashlib.sha256(
        os.environ.get("PROJECT_ENDPOINT", "").encode()).hexdigest()[:16]


class UploadCache:
    """sha256 -> file id, valid for ONE Foundry project: the cache records
    the endpoint hash and is ignored (rebuilt) when it differs, so a cache
    restored in CI or copied between projects never reuses foreign ids."""

    def __init__(self, path: Path):
        self.path = path
        self.lock = Lock()
        self.map: dict[str, str] = {}
        self.key = endpoint_key()
        if path.is_file():
            try:
                data = json.loads(path.read_text())
                if data.get("_endpoint") == self.key:
                    self.map = {k: v for k, v in data.items()
                                if not k.startswith("_")}
                else:
                    print("  upload cache ignored: different PROJECT_ENDPOINT")
            except (json.JSONDecodeError, AttributeError):
                self.map = {}

    @staticmethod
    def digest(p: Path) -> str:
        return hashlib.sha256(p.read_bytes()).hexdigest()

    def get(self, digest: str) -> str | None:
        with self.lock:
            return self.map.get(digest)

    def put(self, digest: str, file_id: str) -> None:
        with self.lock:
            self.map[digest] = file_id
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps({"_endpoint": self.key, **self.map},
                                            indent=1))


def upload_files(agents_client, paths: list[Path], cache: UploadCache,
                 label: str = "") -> list[str]:
    """Upload files in parallel with retry + dedupe; returns file ids in the
    same order as `paths`. Any single failure fails the whole batch loudly
    (a partially-provisioned knowledge base is worse than a clean retry)."""
    def one(p: Path) -> str:
        d = cache.digest(p)
        cached = cache.get(d)
        if cached:
            return cached
        up = retry(agents_client.files.upload_and_poll,
                   file_path=str(p), purpose="assistants",
                   what=f"upload {p.name}")
        cache.put(d, up.id)
        return up.id

    with ThreadPoolExecutor(max_workers=UPLOAD_WORKERS) as ex:
        ids = list(ex.map(one, paths))
    if label:
        reused = sum(1 for p in paths if cache.get(cache.digest(p)))
        print(f"  {label}: {len(ids)} files ready "
              f"({len(ids)} total, cache hits included)")
    return ids


def reconcile_store(agents_client, name: str, file_ids: list[str]):
    """Return the vector store called `name` holding EXACTLY `file_ids`:
    reuse the newest store of that name, add missing files, detach stale
    ones, and delete older duplicates of the same name (each re-run used to
    leave orphans). Creates the store when absent."""
    same = [vs for vs in agents_client.vector_stores.list() if vs.name == name]
    if not same:
        return retry(agents_client.vector_stores.create_and_poll,
                     name=name, file_ids=file_ids or None,
                     what=f"vector store {name}")
    same.sort(key=lambda v: getattr(v, "created_at", 0) or 0, reverse=True)
    store, older = same[0], same[1:]
    have = {vf.id for vf in agents_client.vector_store_files.list(
        vector_store_id=store.id)}
    for fid in [f for f in file_ids if f not in have]:
        retry(agents_client.vector_store_files.create_and_poll,
              vector_store_id=store.id, file_id=fid, what=f"attach {fid}")
    for fid in have - set(file_ids):
        retry(agents_client.vector_store_files.delete,
              vector_store_id=store.id, file_id=fid, what=f"detach {fid}")
    for vs in older:
        retry(agents_client.vector_stores.delete, vs.id,
              what=f"delete duplicate store {vs.id}")
    if file_ids and (have != set(file_ids) or older):
        print(f"  {name}: reconciled (+{len(set(file_ids) - have)} "
              f"-{len(have - set(file_ids))}, {len(older)} duplicates removed)")
    return store


def tool_type(t) -> str:
    return getattr(t, "type", None) or (t.get("type", "") if isinstance(t, dict) else "")


def routing_table_block(rows: list[tuple[str, str]]) -> str:
    """Deploy-time routing table replacing ConnectedAgentTool (C2): the
    orchestrator answers with `ROUTE: <agent-name>` and the caller performs
    the hand-off as a second responses.create on that agent."""
    if not rows:
        return ""
    body = "\n".join(f"| `{n}` | {(d or '').replace('|', '/')[:300]} |"
                      for n, d in rows)
    return (f"\n\n{ROUTING_MARKER}\n\nWhen a specialist is needed, reply "
            f"with a single line `ROUTE: <agent-name>` chosen from this "
            f"table (the caller performs the hand-off), then stop.\n\n"
            f"| agent-name | handles |\n|---|---|\n{body}\n")


def integration_tools(agent) -> list:
    """OpenAPI / MCP / Bing / AI Search tools currently on a live agent -
    preserved by the create scripts so a re-run never wipes
    attach_integrations.py or apply_advisory_profile.py work."""
    return [t for t in (agent.tools or [])
            if tool_type(t) in ("openapi", "bing_grounding", "mcp",
                                "azure_ai_search")]
