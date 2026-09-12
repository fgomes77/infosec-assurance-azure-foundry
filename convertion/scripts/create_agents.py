#!/usr/bin/env python3
"""Create/update Azure AI Foundry agents from build/manifest.json.

Run convert_skills.py first. Auth: DefaultAzureCredential (az login).
Requires PROJECT_ENDPOINT and MODEL_DEPLOYMENT_NAME (env or setup/.env).

Idempotent by agent name: on the GA runtime every run saves a new
immutable version `<name>:<n>` of the same agent (previous versions stay
and can be re-activated); on the classic fallback runtime the agent is
updated in place. Either way the vector store is reconciled (no orphan
stores) and integration tools attached by attach_integrations.py are
preserved. Alias twins (manifest "alias_of") are NOT deployed - the
target agent answers for them. Routing is a deploy-time ROUTE table in the
instructions, not the retired ConnectedAgentTool (finding C2).

ROUTER WIRING ORDER. The control-center's ROUTE table covers the delivery
agents too (ciso-global-report, the three analyzers, template-manager),
and those are created by create_delivery_agents.py, which runs AFTER this
script. Routers are therefore wired in a SEPARATE pass:

    python3 create_agents.py --skip-routers      # step [3]: agents only
    python3 create_delivery_agents.py            # step [4]: delivery agents
    python3 create_agents.py --rewire            # step [4b]: ROUTE tables

A plain run still wires the routers at the end (standalone use), but when
a target is a delivery agent that is not live yet it DEFERS instead of
failing and prints the --rewire command. In --rewire mode a missing target
always fails loudly: by then everything must exist.

Every deployed version is recorded in build/agent-versions.json (C19),
which pipelines pin and verify_deployment.py compares against.

Usage:
    python3 create_agents.py                # everything in the manifest
    python3 create_agents.py --only dora
    python3 create_agents.py --skip-routers # agents only, leave ROUTE tables
    python3 create_agents.py --rewire       # ROUTE tables only (no agent save)
    python3 create_agents.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUILD = HERE.parent / "build"
try:
    from dotenv import load_dotenv
    load_dotenv(HERE.parent / "setup" / ".env")
except ImportError:
    pass  # plain environment variables still work

ENDPOINT = os.environ.get("PROJECT_ENDPOINT")
MODEL = os.environ.get("MODEL_DEPLOYMENT_NAME", "gpt-4o")


sys.path.insert(0, str(HERE))
from _azure_helpers import (UploadCache, file_map_block,  # noqa: E402
                            integration_tools, kit_metadata, reconcile_store,
                            routing_table_block, strip_deploy_blocks,
                            upload_files as _upload)
from _foundry_runtime import get_runtime, record_version  # noqa: E402

_CACHE = UploadCache(BUILD / "upload-cache.json")


def upload_files(agents_client, agent_dir: Path, names: list[str],
                 subdir: str) -> list[str]:
    return _upload(agents_client, [agent_dir / subdir / n for n in names],
                   _CACHE)


def ensure_agent(rt, spec: dict, existing: dict, dry: bool):
    agent_dir = BUILD / "agents" / spec["name"]
    instructions = (BUILD / spec["instructions_file"]).read_text(encoding="utf-8")

    if spec.get("alias_of"):
        print(f"alias    {spec['name']} -> served by {spec['alias_of']} "
              f"(not deployed)")
        return None
    if dry:
        print(f"[dry-run] {spec['name']}: tools={spec['tools']} "
              f"knowledge={len(spec['knowledge_files'])} "
              f"package={spec['code_files']} "
              f"({len(spec.get('code_tree_files', []))} files)"
              + (" PLATFORM-SPECIFIC (not connected)" if spec.get("platform_specific") else ""))
        return None

    from azure.ai.agents.models import CodeInterpreterTool, FileSearchTool

    tools, tool_resources = [], {}
    if spec["knowledge_files"]:
        kids = upload_files(rt, agent_dir,
                            spec["knowledge_files"], "knowledge")
        vs = reconcile_store(rt, f"vs-{spec['name']}", kids)
        fs = FileSearchTool(vector_store_ids=[vs.id])
        tools += fs.definitions
        tool_resources.update(fs.resources)
    if spec["code_files"]:
        cids = upload_files(rt, agent_dir,
                            spec["code_files"], "code")
        ci = CodeInterpreterTool(file_ids=cids)
        tools += ci.definitions
        tool_resources.update(ci.resources)
        # names are lost on upload: tell the agent which id is its package
        instructions += file_map_block(list(zip(spec["code_files"], cids)))
    if spec["name"] in existing:
        tools += integration_tools(existing[spec["name"]])  # keep attach_integrations work

    had = spec["name"] in existing
    agent = rt.upsert_agent(name=spec["name"], model=MODEL,
                            description=spec["description"] or "",
                            instructions=instructions,
                            tools=tools, tool_resources=tool_resources,
                            metadata=kit_metadata(),
                            existing=existing.get(spec["name"]))
    record_version(agent)
    print(f"{'updated' if had else 'created'}  {agent.ref} ({agent.id})")
    return agent


def delivery_agent_names() -> set[str]:
    """The agents create_delivery_agents.py owns - router targets that only
    exist after step [4] of deploy.sh."""
    try:
        from create_delivery_agents import AGENTS as DELIVERY
    except ImportError:                      # standalone copy of this script
        return set()
    return set(DELIVERY)


def wire_router(rt, spec: dict, ids: dict, dry: bool, *, required: bool = False):
    """Targets are resolved against the LIVE agents (merged with this run),
    so `--only <router>` wires too.

    A target that is not live yet fails loudly in --rewire mode (`required`);
    in a plain run it DEFERS when the missing targets are delivery agents,
    because those are created by the next step of deploy.sh.

    Connected agents do not exist on the new Agent Service (finding C2), so
    the router gets a deploy-time ROUTE table in its instructions instead:
    it answers `ROUTE: <agent-name>` and the caller (MCP server, Copilot
    wrapper, workflows/agent-fanout.json) performs the hand-off as a second
    responses.create. The block carries its own marker and is stripped
    before hashing, so the offline instruction hash is unaffected."""
    targets = spec["router_targets"]
    if not targets:
        return
    if dry:
        deferred = sorted(set(targets) & delivery_agent_names())
        print(f"[dry-run] router {spec['name']} -> ROUTE table over {targets} "
              f"(no ConnectedAgentTool — finding C2)"
              + (f"; {len(deferred)} target(s) come from "
                 f"create_delivery_agents.py, so the live wiring happens in "
                 f"the --rewire pass: {deferred}" if deferred else ""))
        return
    missing = [t for t in targets if t not in ids]
    if missing and not required and set(missing) <= delivery_agent_names():
        print(f"deferred {spec['name']}: {missing} not deployed yet "
              f"(create_delivery_agents.py) — wire with "
              f"`python3 create_agents.py --rewire` after step [4]")
        return
    if missing or spec["name"] not in ids:
        raise RuntimeError(f"router targets not deployed: {missing or spec['name']}")
    me = ids[spec["name"]]
    base = strip_deploy_blocks(me.instructions or "")
    rows = [(t, ids[t].description or f"{t} requests") for t in targets]
    agent = rt.upsert_agent(name=spec["name"], model=me.model or MODEL,
                            description=me.description,
                            instructions=base + routing_table_block(rows),
                            tools=me.tools, tool_resources=me.tool_resources,
                            metadata=kit_metadata(), existing=me)
    record_version(agent, note="router")
    print(f"wired    {agent.ref} -> ROUTE table: {', '.join(targets)}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="comma-separated agent names")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--rewire", action="store_true",
                    help="only (re)wire the router ROUTE tables against the "
                         "live agent set — run after create_delivery_agents.py")
    ap.add_argument("--skip-routers", action="store_true",
                    help="create/update agents but leave the ROUTE tables to "
                         "a later --rewire pass (deploy.sh step [3])")
    args = ap.parse_args()

    if args.rewire and args.skip_routers:
        ap.error("--rewire and --skip-routers are mutually exclusive")

    manifest = json.loads((BUILD / "manifest.json").read_text())["agents"]
    if args.only:
        keep = set(args.only.split(","))
        manifest = [a for a in manifest if a["name"] in keep]
    if not args.dry_run and not ENDPOINT:
        sys.exit("Set PROJECT_ENDPOINT (setup/.env) — printed by provision.sh")

    rt = None
    existing: dict = {}
    if not args.dry_run:
        rt = get_runtime(ENDPOINT)
        existing = rt.list_agents()

    created: dict = {}
    failures: list[str] = []
    routers = [a for a in manifest if a["router_targets"]]
    if not args.rewire:
        for spec in manifest:
            try:
                agent = ensure_agent(rt, spec, existing, args.dry_run)
            except Exception as e:  # noqa: BLE001 - isolate per-agent failures
                failures.append(spec["name"])
                print(f"FAILED   {spec['name']}: {e}")
                continue
            if agent is not None:
                created[spec["name"]] = agent
    live = {**existing, **created}
    if args.skip_routers:
        print(f"routers  {[r['name'] for r in routers]} not wired "
              f"(--skip-routers) — run `create_agents.py --rewire` after "
              f"create_delivery_agents.py")
    else:
        for spec in routers:
            try:
                wire_router(rt, spec, live, args.dry_run, required=args.rewire)
            except Exception as e:  # noqa: BLE001
                failures.append(f"{spec['name']} (router wiring)")
                print(f"FAILED   {spec['name']} router wiring: {e}")

    processed = 0 if args.rewire else len(manifest)
    print(f"\ndone: {processed} agents processed, "
          f"{len(routers) if not args.skip_routers else 0} router(s) wired, "
          f"{len(failures)} failed" + (f": {failures}" if failures else ""))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
