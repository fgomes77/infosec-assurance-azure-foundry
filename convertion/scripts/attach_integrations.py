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
# finding C4: o3-mini supports NO OpenAPI/MCP/AI Search/SharePoint/Web Search
# tool - see integrations/registry.json model_tiers._tool_compatibility
REASONING_MODEL = os.environ.get("REASONING_MODEL_DEPLOYMENT_NAME", "o4-mini")
LIGHT_MODEL = os.environ.get("LIGHT_MODEL_DEPLOYMENT_NAME", "gpt-4o-mini")
TIER_MODEL = {"light": LIGHT_MODEL, "chat": CHAT_MODEL, "reasoning": REASONING_MODEL}

sys.path.insert(0, str(HERE))
from _azure_helpers import dedupe_tools, tool_type  # noqa: E402

REGISTRY = json.loads((CONV / "integrations" / "registry.json").read_text())

# Foundry tool definitions bind a project connection by its ID, never by the
# name used in integrations/registry.json. The resolver turns one into the
# other once per name and says so when a connection is missing, instead of
# attaching a tool that silently never calls anything.
_PROJECT = None
_CONN_IDS: dict[str, str] = {}


def resolve_connection(name: str) -> str:
    """Project connection name -> connection id (unchanged when it already is
    an id, when there is no client, or when the lookup fails - with a note)."""
    if not name or name.startswith("/"):
        return name
    if name in _CONN_IDS:
        return _CONN_IDS[name]
    resolved = name
    if _PROJECT is not None:
        try:
            from azure.core.exceptions import AzureError
        except ImportError:               # SDK not installed (dry runs)
            AzureError = Exception        # noqa: N806
        try:
            resolved = _PROJECT.connections.get(name=name).id or name
        except (AzureError, AttributeError, TypeError, ValueError) as e:
            print(f"note: project connection {name!r} did not resolve to an id "
                  f"({type(e).__name__}: {e}) - passing the name through; "
                  f"create it with integrations/connections/ if the tool fails")
    _CONN_IDS[name] = resolved
    return resolved
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


def check_tool_compatibility(name: str, cfg: dict) -> list[str]:
    """Finding C4: an agent may only be pinned to a tier whose model supports
    every tool it carries (integrations/registry.json
    model_tiers._tool_compatibility). This is the enforcement point the
    registry's _tool_compatibility._comment names."""
    tiers = REGISTRY.get("model_tiers", {})
    matrix = tiers.get("_tool_compatibility", {}).get("models", {})
    model = model_for(cfg)
    row = matrix.get(model)
    if not row:
        return [f"{name}: model {model!r} has no row in "
                f"model_tiers._tool_compatibility.models - add it before deploying"]
    bad = []
    for t in cfg.get("tools", []):
        conn = REGISTRY["connections"].get(t)
        if conn is None:
            bad.append(f"{name}: unknown connection {t!r} (integrations/registry.json)")
            continue
        if row.get(conn["type"]) == "no":
            bad.append(f"{name}: model {model!r} does not support tool type "
                       f"{conn['type']!r} required by connection {t!r} (finding C4)")
    return bad


# The one documented exception to "GET only" (integrations/README.md "Read-only
# rule of record", governance/HUMAN_APPROVAL.md Layer 1): five search APIs
# express a QUERY as a POST because the query does not fit in a URL. They read
# and never mutate. The flag `x-enx-read-only: true` on the operation is what
# keeps it, and it is honoured ONLY for these operationIds — a spec author
# cannot widen the rule by adding the flag to a write.
READ_ONLY_POST_OPS = {
    "searchIssuesJql",      # Jira Cloud - JQL search
    "aqlSearchObjects",     # Jira Assets CMDB - AQL, the only query surface
    "runHuntingQuery",      # Defender - KQL advanced hunting
    "searchContent",        # SharePoint / Graph search
    "codeSearch",           # Azure DevOps - code search
}
# Filled by load_openapi_spec, printed by --dry-run and audited by
# verify_conversion.py: the standing evidence of what non-GET survived.
KEPT_POSTS: list[str] = []


def load_openapi_spec(rel: str, read_only: bool) -> dict:
    """Load a spec; unless write access was explicitly granted, strip every
    non-GET operation so the agent is technically incapable of submitting
    (see governance/HUMAN_APPROVAL.md, Layer 1).

    The exception is a non-GET operation carrying `x-enx-read-only: true`
    whose operationId is in READ_ONLY_POST_OPS. A flag on any other operation
    is REFUSED loudly rather than honoured — silently trusting a flag in a
    spec file would make the Layer-1 control editable by whoever edits the
    spec, which is the opposite of a structural control.
    """
    import yaml
    spec = yaml.safe_load((CONV / rel).read_text(encoding="utf-8"))
    if read_only:
        for path, ops in list(spec.get("paths", {}).items()):
            for verb in list(ops):
                if verb.lower() in ("get", "parameters"):
                    continue
                op = ops[verb]
                if isinstance(op, dict) and op.get("x-enx-read-only") is True:
                    op_id = op.get("operationId")
                    if op_id in READ_ONLY_POST_OPS:
                        KEPT_POSTS.append(
                            f"{rel}: {verb.upper()} {path} ({op_id})")
                        continue
                    sys.exit(
                        f"{rel}: {verb.upper()} {path} carries "
                        f"x-enx-read-only but operationId {op_id!r} is not in "
                        f"the allow-set {sorted(READ_ONLY_POST_OPS)} "
                        f"(integrations/README.md 'Read-only rule of record')")
                del ops[verb]
            if not any(v.lower() != "parameters" for v in ops):
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
        if not conn.get("enabled", True):
            sys.exit(f"connection {key!r} is disabled in the registry "
                     f"(enabled=false) but is listed on an agent")
        if conn["type"] == "openapi":
            read_only = key not in write_connections
            auth = OpenApiConnectionAuthDetails(
                security_scheme=OpenApiConnectionSecurityScheme(
                    connection_id=resolve_connection(conn["foundry_connection"])))
            defs += OpenApiTool(
                name=key.replace("-", "_"),
                description=(f"{key} integration"
                             + (" [read-only]" if read_only else "")
                             + f" (see {conn['spec']})"),
                spec=load_openapi_spec(conn["spec"], read_only),
                auth=auth,
            ).definitions
        elif conn["type"] == "bing_grounding":
            # finding C13 keeps the residual-risk acceptance for web grounding;
            # this only makes the wiring real - the tool needs the connection ID
            cid = resolve_connection(conn["foundry_connection"])
            if cid == conn["foundry_connection"] and _PROJECT is not None:
                print(f"note: web grounding for {key!r} is attached with an "
                      f"unresolved connection reference - verify it in the "
                      f"portal (enterprise/portal/agent-checklist.md)")
            defs += BingGroundingTool(connection_id=cid).definitions
        elif conn["type"] == "mcp":
            mcp = json.loads((CONV / conn["config"]).read_text())
            # every key starting with '_' is documentation, not tool definition
            mcp = {k: v for k, v in mcp.items() if not k.startswith("_")}
            approval = mcp.get("require_approval")
            if isinstance(approval, dict):
                waived = approval.get("never", {}).get("tool_names", [])
                if sorted(waived) != sorted(mcp.get("allowed_tools", [])):
                    sys.exit(f"{conn['config']}: require_approval.never.tool_names "
                             f"must equal allowed_tools (finding C10)")
            elif approval != "always":
                sys.exit(f"{conn['config']}: require_approval must be 'always' or "
                         f"the per-tool waiver object (finding C10)")
            cname = mcp.pop("project_connection", None)
            if cname or conn.get("foundry_connection"):
                # finding C10: auth is the project connection, never a run-time
                # bearer header injected into the tool definition
                mcp["connection_id"] = resolve_connection(
                    cname or conn["foundry_connection"])
            defs.append(mcp)  # MCP tool definitions pass through as dicts
        else:
            sys.exit(f"connection {key!r}: unsupported type {conn['type']!r} - "
                     f"attach_integrations.py has no handler (finding C9: "
                     f"'sharepoint_grounding' needs one before it can be attached)")
    return defs


def list_mcp_tools(dry: bool) -> int:
    """Finding C10 / gap G-04. Print, per MCP connection: the resolved project
    connection, the require_approval waiver set and every allow-listed tool
    with its readOnlyHint. FAIL when a waived tool is not read-only, when the
    waiver set differs from allowed_tools, or when the project connection
    cannot be resolved. `integrations/mcp/enx-gateway.json` `_verification`
    states exactly this behaviour."""
    findings: list[str] = []
    for key, conn in REGISTRY["connections"].items():
        if conn.get("type") != "mcp":
            continue
        cfg = json.loads((CONV / conn["config"]).read_text(encoding="utf-8"))
        allowed = cfg.get("allowed_tools") or []
        approval = cfg.get("require_approval")
        waived = (approval.get("never", {}).get("tool_names", [])
                  if isinstance(approval, dict) else
                  (allowed if approval == "never" else []))
        connection = cfg.get("project_connection") or conn.get("foundry_connection")
        print(f"\nMCP connection {key}  ({conn['config']})")
        print(f"  server_label       : {cfg.get('server_label', '-')}")
        print(f"  project connection : {connection or '(UNRESOLVED)'}")
        print(f"  require_approval   : "
              f"{'per-tool waiver' if isinstance(approval, dict) else approval!r}")
        print(f"  waiver set         : {sorted(waived)}")
        if not connection:
            findings.append(f"{key}: no project_connection / foundry_connection "
                            f"(finding C10 - auth must come from the connection)")
        if sorted(waived) != sorted(allowed):
            findings.append(f"{key}: require_approval waiver set != allowed_tools "
                            f"(finding C10)")
        hints = cfg.get("_tool_read_only_hints") or cfg.get("tool_read_only_hints") or {}
        for tool in allowed:
            placeholder = tool.startswith("{") and tool.endswith("}")
            hint = hints.get(tool)
            if hint is None and not dry and not placeholder:
                hint = _probe_read_only_hint(cfg, tool)
            mark = "readOnlyHint=true" if hint is True else (
                "readOnlyHint=UNKNOWN" if hint is None else "readOnlyHint=false")
            if placeholder:
                mark += "  (template placeholder - fill with the tenant tool name)"
            print(f"    - {tool:<48} {mark}")
            if placeholder:
                # a shipped template cannot be probed; the tenant fills the
                # allow-list at step D9 and re-runs this check before attaching
                continue
            if hint is not True:
                findings.append(f"{key}: allow-listed tool {tool!r} is not proven "
                                f"read-only ({mark}) - refuse to attach (finding C10)")
    for f in findings:
        print(f"FAIL: {f}")
    return 1 if findings else 0


def _probe_read_only_hint(cfg: dict, tool: str):
    """Live tools/list probe against the gateway. Returns None when the
    gateway cannot be reached (read-only access, no credentials in the kit)."""
    import urllib.error
    import urllib.request
    try:
        req = urllib.request.Request(
            cfg["server_url"], method="POST",
            data=json.dumps({"jsonrpc": "2.0", "id": 1,
                             "method": "tools/list"}).encode(),
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as r:
            body = json.loads(r.read().decode())
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError,
            OSError, ValueError, json.JSONDecodeError) as e:
        # the gateway is unreachable from here (read-only access, no
        # credentials in the kit) - UNKNOWN, and the caller then refuses to
        # attach the tool (finding C10). Never silently "not read-only".
        print(f"    probe {tool!r}: {type(e).__name__}: {e}")
        return None
    except KeyError:
        print(f"    probe {tool!r}: the MCP config has no 'server_url'")
        return None
    for t in body.get("result", {}).get("tools", []):
        if t.get("name") == tool:
            return bool(t.get("annotations", {}).get("readOnlyHint"))
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="comma-separated agent names")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--list-mcp-tools", action="store_true",
                    help="print each MCP connection's project connection, "
                         "require_approval waiver set and per-tool readOnlyHint "
                         "(finding C10); exits 1 on any violation")
    args = ap.parse_args()

    if args.list_mcp_tools:
        return list_mcp_tools(args.dry_run)

    wanted = REGISTRY["agents"]
    if args.only:
        keep = set(args.only.split(","))
        wanted = {k: v for k, v in wanted.items() if k in keep}

    incompatible: list[str] = []
    for name, cfg in wanted.items():
        incompatible += check_tool_compatibility(name, cfg)
    if incompatible:
        for msg in incompatible:
            print(f"FAIL: {msg}")
        print("\nRe-select the tier model or move the agent to a tier whose "
              "model carries the tool (governance/MODEL_ROUTING.md).")
        return 1

    if args.dry_run:
        for name, cfg in wanted.items():
            model = model_for(cfg)
            writes = cfg.get("write_connections", [])
            labelled = [t + ("" if t in writes
                             or REGISTRY["connections"][t]["type"] != "openapi"
                             else " [read-only]") for t in cfg["tools"]]
            guard = cfg.get("guardrail_policy", "infosec-security-analysis")
            print(f"[dry-run] {name}: +{labelled or ['(none)']} model={model} "
                  f"rai={guard}")
        # Load every attached spec once so the read-only audit is populated
        # even in --dry-run, where build_tools() returns early.
        KEPT_POSTS.clear()
        for key, conn in REGISTRY["connections"].items():
            if conn.get("type") == "openapi" and conn.get("spec"):
                load_openapi_spec(conn["spec"], read_only=True)
        print("\n[dry-run] kept read-only POST operations:")
        for line in sorted(set(KEPT_POSTS)) or ["  (none)"]:
            print(f"  {line}")
        print(f"\n{len(wanted)} agents would be updated "
              f"(writes granted: "
              f"{sum(bool(c.get('write_connections')) for c in wanted.values())})")
        return 0

    if not ENDPOINT:
        sys.exit("Set PROJECT_ENDPOINT (setup/.env)")
    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential
    global _PROJECT
    _PROJECT = AIProjectClient(endpoint=ENDPOINT,
                               credential=DefaultAzureCredential())
    agents_client = _PROJECT.agents

    live = {a.name: a for a in agents_client.list_agents()}
    integration_names = {k.replace("-", "_") for k in REGISTRY["connections"]}

    for name, cfg in wanted.items():
        agent = live.get(name)
        if agent is None:
            print(f"skip     {name}: not deployed (run create_agents.py)")
            continue
        # keep non-integration tools; drop previously attached integrations
        def _is_integration(t) -> bool:
            ttype = tool_type(t)
            if ttype not in ("openapi", "bing_grounding", "mcp"):
                return False
            if ttype == "bing_grounding":
                # a Bing tool carries no name, so it can only be recognised by
                # its type - and web grounding is owned by the registry. Keeping
                # the old one would leave TWO grounding tools on the agent (one
                # bound to a connection NAME, one to the resolved id).
                return True
            name = (getattr(t, "name", "")
                    or (t.get("server_label", "") if isinstance(t, dict) else ""))
            return name in integration_names

        kept = [t for t in (agent.tools or []) if not _is_integration(t)]
        model = model_for(cfg)
        # `kept` and the freshly built definitions can overlap (a tool renamed
        # in the registry, an agent updated twice in one deploy): one tool of
        # each identity, first occurrence wins.
        tools = dedupe_tools(kept + build_tools(cfg["tools"],
                                                cfg.get("write_connections", []),
                                                False), label=name)
        agents_client.update_agent(agent.id, model=model, tools=tools)
        guard = cfg.get("guardrail_policy", "infosec-security-analysis")
        # The pinned SDK does not expose the agent-level RAI assignment on
        # update_agent; it is set at creation / in the portal and verified by
        # enterprise/portal/agent-checklist.md (finding C14 / D-EB7).
        print(f"updated  {name}: +{cfg['tools']} model={model} "
              f"rai={guard} (assignment verified in the portal checklist)")

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
