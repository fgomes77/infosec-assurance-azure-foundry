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


class UploadCache:
    def __init__(self, path: Path):
        self.path = path
        self.lock = Lock()
        self.map: dict[str, str] = {}
        if path.is_file():
            try:
                self.map = json.loads(path.read_text())
            except json.JSONDecodeError:
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
            self.path.write_text(json.dumps(self.map, indent=1))


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
