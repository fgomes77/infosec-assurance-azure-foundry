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
LIGHT_MODEL = os.environ.get("LIGHT_MODEL_DEPLOYMENT_NAME", "gpt-4o-mini")
TIER_MODEL = {"light": LIGHT_MODEL, "chat": CHAT_MODEL, "reasoning": REASONING_MODEL}

REGISTRY = json.loads((CONV / "integrations" / "registry.json").read_text())
# Live agents that may legitimately lack a registry entry: the verifier
# (registry example_agents.unmanaged_ok) and the orchestrator, whose tools
# are owned by create_orchestrator.py. Any other unmanaged live agent FAILS
# the run (registry _comment) - an unknown agent is an ungoverned tool surface.
UNMANAGED_OK = set(REGISTRY.get("example_agents", {}).get("unmanaged_ok", [])) | {
    "infosec-assurance-orchestrator"}


def model_for(cfg: dict) -> str:
    tier = cfg.get("model_tier", "chat")
    if tier not in TIER_MODEL:
        sys.exit(f"unknown model_tier {tier!r} (governance/MODEL_ROUTING.md)")
    return TIER_MODEL[tier]


def load_openapi_spec(rel: str, read_only: bool) -> dict:
    """Load a spec; unless write access was explicitly granted, strip every
    non-GET operation so the agent is technically incapable of submitting
    (see governance/HUMAN_APPROVAL.md, Layer 1)."""
    import yaml
    spec = yaml.safe_load((CONV / rel).read_text(encoding="utf-8"))
    if read_only:
        for path, ops in list(spec.get("paths", {}).items()):
            for verb in list(ops):
                if verb.lower() not in ("get", "parameters"):
                    del ops[verb]
            if not any(v.lower() == "get" for v in ops):
                del spec["paths"][path]
    return spec


def build_tools(agent_tools: list[str], write_connections: list[str],
                dry: bool) -> list:
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
            read_only = key not in write_connections
            auth = OpenApiConnectionAuthDetails(
                security_scheme=OpenApiConnectionSecurityScheme(
                    connection_id=conn["foundry_connection"]))
            defs += OpenApiTool(
                name=key.replace("-", "_"),
                description=(f"{key} integration"
                             + (" [read-only]" if read_only else "")
                             + f" (see {conn['spec']})"),
                spec=load_openapi_spec(conn["spec"], read_only),
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
            model = model_for(cfg)
            writes = cfg.get("write_connections", [])
            labelled = [t + ("" if t in writes
                             or REGISTRY["connections"][t]["type"] != "openapi"
                             else " [read-only]") for t in cfg["tools"]]
            print(f"[dry-run] {name}: +{labelled or ['(none)']} model={model}")
        print(f"\n{len(wanted)} agents would be updated "
              f"(writes granted: "
              f"{sum(bool(c.get('write_connections')) for c in wanted.values())})")
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
        model = model_for(cfg)
        agents_client.update_agent(
            agent.id, model=model,
            tools=kept + build_tools(cfg["tools"],
                                     cfg.get("write_connections", []), False))
        print(f"updated  {name}: +{cfg['tools']} model={model}")

    print(f"\ndone: {len(wanted)} agents processed")
    if not args.only:
        unmanaged = sorted(set(live) - set(REGISTRY["agents"]) - UNMANAGED_OK)
        if unmanaged:
            print(f"FAIL: live agents without a registry entry (add them to "
                  f"integrations/registry.json or example_agents.unmanaged_ok): "
                  f"{unmanaged}")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
