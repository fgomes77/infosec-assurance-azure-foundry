#!/usr/bin/env python3
"""Create/update Azure AI Foundry agents from build/manifest.json.

Run convert_skills.py first. Auth: DefaultAzureCredential (az login).
Requires PROJECT_ENDPOINT and MODEL_DEPLOYMENT_NAME (env or setup/.env).

Idempotent by agent name: an existing agent with the same name is updated
(instructions, tools, fresh vector store); others are created. Router agents
(connected agents) are wired last, once their targets exist.

Usage:
    python3 create_agents.py                # everything in the manifest
    python3 create_agents.py --only dora
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


def get_client():
    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential
    return AIProjectClient(endpoint=ENDPOINT,
                           credential=DefaultAzureCredential())


from _azure_helpers import UploadCache, retry, upload_files as _upload

_CACHE = UploadCache(BUILD / "upload-cache.json")


def upload_files(agents_client, agent_dir: Path, names: list[str],
                 subdir: str) -> list[str]:
    return _upload(agents_client, [agent_dir / subdir / n for n in names],
                   _CACHE)


def ensure_agent(agents_client, spec: dict, existing: dict, dry: bool):
    agent_dir = BUILD / "agents" / spec["name"]
    instructions = (BUILD / spec["instructions_file"]).read_text(encoding="utf-8")

    if dry:
        print(f"[dry-run] {spec['name']}: tools={spec['tools']} "
              f"knowledge={len(spec['knowledge_files'])} "
              f"code={len(spec['code_files'])}")
        return None

    from azure.ai.agents.models import CodeInterpreterTool, FileSearchTool

    tools, tool_resources = [], {}
    if spec["knowledge_files"]:
        kids = upload_files(agents_client, agent_dir,
                            spec["knowledge_files"], "knowledge")
        vs = retry(agents_client.vector_stores.create_and_poll,
                   file_ids=kids, name=f"vs-{spec['name']}",
                   what=f"vector store vs-{spec['name']}")
        fs = FileSearchTool(vector_store_ids=[vs.id])
        tools += fs.definitions
        tool_resources.update(fs.resources)
    if spec["code_files"]:
        cids = upload_files(agents_client, agent_dir,
                            spec["code_files"], "code")
        ci = CodeInterpreterTool(file_ids=cids)
        tools += ci.definitions
        tool_resources.update(ci.resources)

    kwargs = dict(model=MODEL, name=spec["name"],
                  description=spec["description"] or None,
                  instructions=instructions,
                  tools=tools or None,
                  tool_resources=tool_resources or None)
    if spec["name"] in existing:
        agent = agents_client.update_agent(existing[spec["name"]], **kwargs)
        print(f"updated  {spec['name']} ({agent.id})")
    else:
        agent = agents_client.create_agent(**kwargs)
        print(f"created  {spec['name']} ({agent.id})")
    return agent


def wire_router(agents_client, spec: dict, ids: dict, dry: bool):
    targets = ([t for t in spec["router_targets"] if t in ids] if not dry
               else spec["router_targets"])
    if not targets:
        return
    if dry:
        print(f"[dry-run] router {spec['name']} -> {targets}")
        return
    from azure.ai.agents.models import ConnectedAgentTool
    tools = []
    for t in targets:
        tools += ConnectedAgentTool(
            id=ids[t].id, name=t.replace("-", "_"),
            description=ids[t].description or f"Delegate {t} tasks",
        ).definitions
    agents_client.update_agent(ids[spec["name"]].id, tools=tools)
    print(f"wired    {spec['name']} -> {', '.join(targets)}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="comma-separated agent names")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    manifest = json.loads((BUILD / "manifest.json").read_text())["agents"]
    if args.only:
        keep = set(args.only.split(","))
        manifest = [a for a in manifest if a["name"] in keep]
    if not args.dry_run and not ENDPOINT:
        sys.exit("Set PROJECT_ENDPOINT (setup/.env) — printed by provision.sh")

    agents_client = None
    existing: dict = {}
    if not args.dry_run:
        client = get_client()
        agents_client = client.agents
        existing = {a.name: a.id for a in agents_client.list_agents()}

    created: dict = {}
    failures: list[str] = []
    routers = [a for a in manifest if a["router_targets"]]
    for spec in manifest:
        try:
            agent = ensure_agent(agents_client, spec, existing, args.dry_run)
        except Exception as e:  # noqa: BLE001 - isolate per-agent failures
            failures.append(spec["name"])
            print(f"FAILED   {spec['name']}: {e}")
            continue
        if agent is not None:
            created[spec["name"]] = agent
    for spec in routers:
        try:
            wire_router(agents_client, spec, created, args.dry_run)
        except Exception as e:  # noqa: BLE001
            failures.append(f"{spec['name']} (router wiring)")
            print(f"FAILED   {spec['name']} router wiring: {e}")

    print(f"\ndone: {len(manifest)} agents processed, "
          f"{len(failures)} failed" + (f": {failures}" if failures else ""))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
