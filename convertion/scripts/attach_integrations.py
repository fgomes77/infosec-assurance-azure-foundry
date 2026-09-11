#!/usr/bin/env python3
"""Attach integrations (OpenAPI tools, MCP, Bing grounding) and model tiers
to already-created Foundry agents, per integrations/registry.json.

Run AFTER create_agents.py. Existing tools on each agent (file_search,
code_interpreter, connected agents) are preserved; integration tools are
appended. Re-running replaces previously attached integration tools of the
same name.

Auth material: each OpenAPI connection's credentials live in a Foundry
project connection (created in the portal or via Bicep) named in the
registry's "foundry_connection" — this script only references them.

Usage:
    python3 attach_integrations.py               # all agents in registry
    python3 attach_integrations.py --only cyber-forum
    python3 attach_integrations.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONV = HERE.parent
try:
    from dotenv import load_dotenv
    load_dotenv(CONV / "setup" / ".env")
except ImportError:
    pass

ENDPOINT = os.environ.get("PROJECT_ENDPOINT")
CHAT_MODEL = os.environ.get("MODEL_DEPLOYMENT_NAME", "gpt-4o")
REASONING_MODEL = os.environ.get("REASONING_MODEL_DEPLOYMENT_NAME", "o3-mini")

REGISTRY = json.loads((CONV / "integrations" / "registry.json").read_text())


def load_openapi_spec(rel: str) -> dict:
    import yaml
    return yaml.safe_load((CONV / rel).read_text(encoding="utf-8"))


def build_tools(agent_tools: list[str], dry: bool) -> list:
    """Return Foundry tool definitions for the named registry connections."""
    if dry:
        return []
    from azure.ai.agents.models import (
        BingGroundingTool, OpenApiTool, OpenApiConnectionAuthDetails,
        OpenApiConnectionSecurityScheme,
    )
    defs = []
    for key in agent_tools:
        conn = REGISTRY["connections"][key]
        if conn["type"] == "openapi":
            auth = OpenApiConnectionAuthDetails(
                security_scheme=OpenApiConnectionSecurityScheme(
                    connection_id=conn["foundry_connection"]))
            defs += OpenApiTool(
                name=key.replace("-", "_"),
                description=f"{key} integration (see {conn['spec']})",
                spec=load_openapi_spec(conn["spec"]),
                auth=auth,
            ).definitions
        elif conn["type"] == "bing_grounding":
            defs += BingGroundingTool(
                connection_id=conn["foundry_connection"]).definitions
        elif conn["type"] == "mcp":
            mcp = json.loads((CONV / conn["config"]).read_text())
            mcp.pop("_comment", None)
            defs.append(mcp)  # MCP tool definitions pass through as dicts
    return defs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="comma-separated agent names")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    wanted = REGISTRY["agents"]
    if args.only:
        keep = set(args.only.split(","))
        wanted = {k: v for k, v in wanted.items() if k in keep}

    if args.dry_run:
        for name, cfg in wanted.items():
            model = REASONING_MODEL if cfg["model_tier"] == "reasoning" else CHAT_MODEL
            print(f"[dry-run] {name}: +{cfg['tools'] or ['(none)']} model={model}")
        print(f"\n{len(wanted)} agents would be updated")
        return 0

    if not ENDPOINT:
        sys.exit("Set PROJECT_ENDPOINT (setup/.env)")
    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential
    agents_client = AIProjectClient(
        endpoint=ENDPOINT, credential=DefaultAzureCredential()).agents

    live = {a.name: a for a in agents_client.list_agents()}
    integration_names = {k.replace("-", "_") for k in REGISTRY["connections"]}

    for name, cfg in wanted.items():
        agent = live.get(name)
        if agent is None:
            print(f"skip     {name}: not deployed (run create_agents.py)")
            continue
        # keep non-integration tools; drop previously attached integrations
        kept = [t for t in (agent.tools or [])
                if getattr(t, "type", t.get("type") if isinstance(t, dict) else "")
                not in ("openapi", "bing_grounding", "mcp")
                or (getattr(t, "name", "") or (t.get("server_label", "")
                    if isinstance(t, dict) else "")) not in integration_names]
        model = REASONING_MODEL if cfg["model_tier"] == "reasoning" else CHAT_MODEL
        agents_client.update_agent(
            agent.id, model=model, tools=kept + build_tools(cfg["tools"], False))
        print(f"updated  {name}: +{cfg['tools']} model={model}")

    print(f"\ndone: {len(wanted)} agents processed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
