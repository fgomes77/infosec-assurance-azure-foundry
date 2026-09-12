#!/usr/bin/env python3
"""Retention housekeeping for the Foundry project: conversations/threads,
unreferenced files, orphaned vector stores and expired durable-memory notes.

Every horizon comes from `setup/.env` (never from a constant in this file)
so the schedule in `enterprise/MEMORY_AND_LEARNING.md` §1 and
`governance/MEMORY_POLICY.md` §3 is the single source of truth:

    RETENTION_CONVERSATION_APPROVED_DAYS   90   M1, after the deliverable is approved
    RETENTION_CONVERSATION_IDLE_DAYS      180   M1, inactivity
    RETENTION_ORPHAN_FILE_DAYS             30   grace before an unreferenced file goes
    RETENTION_ORPHAN_STORE_DAYS            30   grace before an orphan vs-* store goes
    RETENTION_MEMORY_MONTHS                24   M2, `retain_until` cap

What is NEVER deleted by this script (memory policy, finding C3):
  * `vs-assurance-memory` and `vs-assurance-combined` - the durable memory
    staging store and the advisor's combined knowledge store;
  * any vector store or file a LIVE agent references;
  * a memory NOTE whose `retain_until` has not passed - and no note at all
    without `--approved-by`, the same human act `memory_store.py import`
    requires (`governance/MEMORY_POLICY.md` §2).

Modes:
    python3 cleanup_foundry.py --dry-run            OFFLINE rehearsal: resolves
                                                    the policy from .env, prints
                                                    what each scope would examine,
                                                    makes no Azure call
    python3 cleanup_foundry.py --stores --files     live, READ-ONLY listing
    python3 cleanup_foundry.py --threads            conversations/threads past the
                                                    idle horizon (listing)
    python3 cleanup_foundry.py --memory --approved-by "{upn:francisco.gomes}"
    python3 cleanup_foundry.py --all --apply        actually delete

Run monthly after an approval (`operations/RUNBOOK.md`); the read-only run
prints exactly what it would remove, so the list is filed as the evidence
of the retention control (ISO 27001:2022 A.5.34, A.8.10; GDPR Art. 5(1)(e)).
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import sys
from pathlib import Path

CONV = Path(__file__).resolve().parent.parent
try:
    from dotenv import load_dotenv
    load_dotenv(CONV / "setup" / ".env")
except ImportError:
    pass

# Never removed, whatever the referencing state (memory policy).
PROTECTED_STORES = {"vs-assurance-memory", "vs-assurance-combined"}
MEMORY_STORE = "vs-assurance-memory"
# memory_store.py writes notes as memory-<stamp>.txt; the stamp IS the note's
# date of record, so retention needs no content read (data minimisation).
NOTE_NAME = re.compile(r"^memory-(\d{8})T\d{6}\d*Z\.txt$")

RETENTION_DEFAULTS = {
    "conversation_approved_days": ("RETENTION_CONVERSATION_APPROVED_DAYS", 90),
    "conversation_idle_days": ("RETENTION_CONVERSATION_IDLE_DAYS", 180),
    "orphan_file_days": ("RETENTION_ORPHAN_FILE_DAYS", 30),
    "orphan_store_days": ("RETENTION_ORPHAN_STORE_DAYS", 30),
    "memory_months": ("RETENTION_MEMORY_MONTHS", 24),
}

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _foundry_runtime import get_runtime, memory_backend  # noqa: E402


def retention() -> dict[str, int]:
    """Horizons from setup/.env, with the documented policy defaults."""
    out: dict[str, int] = {}
    for key, (env, default) in RETENTION_DEFAULTS.items():
        # tolerate the inline comments the .env.example ships with
        raw = (os.environ.get(env) or "").split("#", 1)[0].strip()
        if not raw:
            out[key] = default
            continue
        try:
            value = int(raw)
        except ValueError:
            sys.exit(f"{env}={raw!r} in setup/.env is not a whole number of "
                     f"{'months' if key.endswith('months') else 'days'}")
        if value <= 0:
            sys.exit(f"{env} must be positive (got {value}); a zero horizon "
                     f"would delete live data - governance/MEMORY_POLICY.md §3")
        out[key] = value
    return out


def print_policy(pol: dict[str, int]) -> None:
    print("retention policy (setup/.env -> governance/MEMORY_POLICY.md §3, "
          "enterprise/MEMORY_AND_LEARNING.md §1):")
    for key, (env, default) in RETENTION_DEFAULTS.items():
        unit = "months" if key.endswith("months") else "days"
        source = "env" if os.environ.get(env, "").strip() else "default"
        print(f"  {env:<38} {pol[key]:>4} {unit}   ({source}; policy default {default})")
    print(f"  protected stores                       "
          f"{', '.join(sorted(PROTECTED_STORES))}")
    print(f"  memory backend                         {memory_backend()}")


# ------------------------------------------------------------------ helpers
def _created(obj) -> dt.datetime | None:
    """created_at as an aware datetime (epoch seconds or datetime)."""
    raw = getattr(obj, "created_at", None)
    if raw is None:
        return None
    if isinstance(raw, dt.datetime):
        return raw if raw.tzinfo else raw.replace(tzinfo=dt.timezone.utc)
    try:
        return dt.datetime.fromtimestamp(float(raw), dt.timezone.utc)
    except (TypeError, ValueError, OSError):
        return None


def _older_than(obj, cutoff: dt.datetime) -> bool:
    created = _created(obj)
    return created is not None and created < cutoff


def _res(agent) -> dict:
    r = getattr(agent, "tool_resources", None)
    if r is None:
        return {}
    return r.as_dict() if hasattr(r, "as_dict") else dict(r)


def referenced(rt) -> tuple[set[str], set[str]]:
    """(vector store ids, file ids) referenced by live agents."""
    stores: set[str] = set()
    files: set[str] = set()
    for agent in rt.list_agents().values():
        res = _res(agent)
        stores |= set((res.get("file_search") or {}).get("vector_store_ids") or [])
        files |= set((res.get("code_interpreter") or {}).get("file_ids") or [])
    return stores, files


def _iter(listing):
    """Both runtimes answer either a list or a paged object with .data."""
    return getattr(listing, "data", None) or listing


# -------------------------------------------------------------------- scopes
def sweep_stores(rt, pol, used: set[str], mode: str, apply: bool,
                 all_stores: list) -> int:
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(
        days=pol["orphan_store_days"])
    removed = 0
    for vs in all_stores:
        if vs.id in used or vs.name in PROTECTED_STORES:
            continue
        if not _older_than(vs, cutoff):
            print(f"keep  store {vs.id} {vs.name!r}: orphaned but inside the "
                  f"{pol['orphan_store_days']}-day grace period")
            continue
        print(f"{mode} store {vs.id} {vs.name!r}")
        removed += 1
        if apply:
            rt.vector_stores.delete(vs.id)
    return removed


def sweep_files(rt, pol, used: set[str], mode: str, apply: bool) -> int:
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(
        days=pol["orphan_file_days"])
    removed = 0
    for f in _iter(rt.files.list()):
        if f.id in used or getattr(f, "purpose", "") != "assistants":
            continue
        if not _older_than(f, cutoff):
            continue
        print(f"{mode} file {f.id} {getattr(f, 'filename', '')!r}")
        removed += 1
        if apply:
            rt.files.delete(f.id)
    return removed


def sweep_threads(rt, pol, older_than: int | None, mode: str, apply: bool) -> int:
    days = older_than or pol["conversation_idle_days"]
    if rt.mode == "responses":
        print(f"note: --threads is a no-op on the GA runtime — classic threads "
              f"are replaced by conversations (finding C1). Conversation "
              f"retention ({days} days idle, "
              f"{pol['conversation_approved_days']} days after approval) is a "
              f"project/Cosmos DB TTL setting, not a delete loop: set it on the "
              f"standard-agent-setup Cosmos account "
              f"(governance/DATA_PROTECTION_GUARDRAILS.md, "
              f"enterprise/MEMORY_AND_LEARNING.md §1 M1)")
        return 0
    ac = rt.project.agents
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)
    removed = 0
    for th in _iter(ac.threads.list()):
        if not _older_than(th, cutoff):
            continue
        created = _created(th)
        print(f"{mode} thread {th.id} (created {created:%Y-%m-%d}, "
              f"idle horizon {days}d)")
        removed += 1
        if apply:
            ac.threads.delete(th.id)
    return removed


def sweep_memory(rt, pol, mode: str, apply: bool, approved_by: str) -> int:
    """Expired durable-memory notes ONLY (retain_until passed), and only with
    a recorded human approval - the memory policy's write gate."""
    if apply and not approved_by:
        sys.exit("--memory --apply needs --approved-by \"{upn}\": deleting a "
                 "team note is a write of record (governance/MEMORY_POLICY.md §2)")
    today = dt.date.today()
    horizon = dt.timedelta(days=30 * pol["memory_months"])
    removed = 0

    if memory_backend() == "search-index":
        from memory_store import SearchBackend
        backend = SearchBackend()
        expired = [d for d in backend.client.search(
            search_text="*", select="id,stamp,subject,retain_until", top=1000)
            if (d.get("retain_until") or "9999-12-31") < today.isoformat()]
        for doc in expired:
            print(f"{mode} memory note {doc['id']} "
                  f"(retain_until {doc.get('retain_until')})")
            removed += 1
            if apply:
                backend.delete(doc["id"])
        return removed

    store = next((vs for vs in rt.vector_stores.list()
                  if vs.name == MEMORY_STORE), None)
    if store is None:
        print(f"note: {MEMORY_STORE} not found — nothing to purge "
              f"(run create_orchestrator.py first)")
        return 0
    names = {f.id: getattr(f, "filename", "") for f in _iter(rt.files.list())}
    for vf in rt.vector_store_files.list(vector_store_id=store.id):
        name = names.get(vf.id, "")
        m = NOTE_NAME.match(name)
        if not m:
            print(f"keep  memory file {vf.id} {name!r}: not a "
                  f"memory_store.py note — left for manual review")
            continue
        stamped = dt.datetime.strptime(m.group(1), "%Y%m%d").date()
        retain_until = stamped + horizon
        if retain_until >= today:
            continue
        print(f"{mode} memory note {vf.id} {name!r} "
              f"(retain_until {retain_until.isoformat()})")
        removed += 1
        if apply:
            rt.vector_store_files.delete(vector_store_id=store.id, file_id=vf.id)
            rt.files.delete(vf.id)
    if removed and apply:
        print(f"  purge approved by {approved_by} "
              f"(file this run with the monthly evidence)")
    return removed


# ---------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stores", action="store_true",
                    help="vs-* stores no live agent references")
    ap.add_argument("--files", action="store_true",
                    help="assistants files in no store and on no agent")
    ap.add_argument("--threads", action="store_true",
                    help="classic threads past the idle horizon")
    ap.add_argument("--memory", action="store_true",
                    help="durable-memory notes past retain_until")
    ap.add_argument("--all", action="store_true",
                    help="every scope above")
    ap.add_argument("--older-than", type=int, metavar="DAYS",
                    help="override RETENTION_CONVERSATION_IDLE_DAYS for --threads")
    ap.add_argument("--approved-by", default="",
                    help="UPN of the human approving a --memory purge")
    ap.add_argument("--apply", action="store_true", help="really delete")
    ap.add_argument("--dry-run", action="store_true",
                    help="offline rehearsal: resolve the policy and print the "
                         "plan; no Azure call, no credentials needed")
    args = ap.parse_args()

    if args.apply and args.dry_run:
        ap.error("--apply and --dry-run are mutually exclusive")
    scopes = {"stores": args.stores or args.all, "files": args.files or args.all,
              "threads": args.threads or args.all, "memory": args.memory or args.all}
    if not any(scopes.values()):
        if args.dry_run:
            scopes = dict.fromkeys(scopes, True)      # rehearse everything
        else:
            ap.error("choose --stores, --files, --threads, --memory or --all")

    pol = retention()
    print_policy(pol)
    print()

    if args.dry_run:
        idle = args.older_than or pol["conversation_idle_days"]
        print("[dry-run] OFFLINE — no Azure call. This run would examine:")
        if scopes["stores"]:
            print(f"[dry-run] stores : every vector store, deleting those no live "
                  f"agent references and older than {pol['orphan_store_days']} days; "
                  f"never {', '.join(sorted(PROTECTED_STORES))}")
        if scopes["files"]:
            print(f"[dry-run] files  : every purpose='assistants' file, deleting those "
                  f"in no surviving store / on no agent and older than "
                  f"{pol['orphan_file_days']} days")
        if scopes["threads"]:
            print(f"[dry-run] threads: classic threads older than {idle} days "
                  f"(no-op on the GA runtime — conversation TTL is a Cosmos DB "
                  f"setting; approved-deliverable horizon "
                  f"{pol['conversation_approved_days']} days)")
        if scopes["memory"]:
            print(f"[dry-run] memory : notes in {MEMORY_STORE} "
                  f"(backend {memory_backend()}) whose retain_until "
                  f"(stamp + {pol['memory_months']} months) has passed; "
                  f"--apply additionally requires --approved-by")
        print("\nnothing was read or deleted (dry run; drop --dry-run for a "
              "read-only live listing, add --apply to delete)")
        return 0

    rt = get_runtime(os.environ.get("PROJECT_ENDPOINT"))
    mode = "DELETE" if args.apply else "would delete"
    removed = 0

    all_stores: list = []
    used_stores, used_files = set(), set()
    if scopes["stores"] or scopes["files"]:
        used_stores, used_files = referenced(rt)
        all_stores = list(rt.vector_stores.list())
        for vs in all_stores:
            if vs.name in PROTECTED_STORES:
                used_stores.add(vs.id)
        # a file inside a store that SURVIVES this run is still referenced
        for vs in all_stores:
            if vs.id in used_stores or not scopes["stores"]:
                for vf in rt.vector_store_files.list(vector_store_id=vs.id):
                    used_files.add(vf.id)

    if scopes["stores"]:
        removed += sweep_stores(rt, pol, used_stores, mode, args.apply, all_stores)
    if scopes["files"]:
        removed += sweep_files(rt, pol, used_files, mode, args.apply)
    if scopes["threads"]:
        removed += sweep_threads(rt, pol, args.older_than, mode, args.apply)
    if scopes["memory"]:
        removed += sweep_memory(rt, pol, mode, args.apply, args.approved_by)

    print(f"\n{removed} objects "
          f"{'deleted' if args.apply else 'listed (read-only; add --apply)'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
