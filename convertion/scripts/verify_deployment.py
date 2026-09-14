#!/usr/bin/env python3
"""Live drift check: what is deployed in Azure AI Foundry vs the verified
build - the half of the old verify_sync.py that compared the LIVE state
with the repository. READ-ONLY (list agents, get agent, list vector-store
files; it never updates anything).

Per agent expected from build/manifest.json (+ delivery, advisor, verifier,
orchestrator) it reports, exactly like verify_sync.py did:

    IDENTICAL        instructions hash, tools, model, version all match
    DIFFERENT        one or more of: instructions (sha256 after stripping
                     the deploy-time FILE MAP / advisory addendum / ROUTING
                     TABLE blocks), tool set (file_search /
                     code_interpreter / openapi / mcp / bing /
                     azure_ai_search vs manifest+registry), model
                     deployment (tier -> deployment name), the live agent
                     VERSION vs the version this build promoted
                     (build/agent-versions.json — finding C19), an OpenAPI
                     tool that exposes a non-GET operation (write surface),
                     a registry agent with write_connections
    ONLY IN FOUNDRY  live agent the kit does not know (portal-created)
    ONLY IN BUILD    expected agent not deployed

Connected agents no longer exist on the Agent Service (finding C2), so
`connected_agent` is not an expected tool type anywhere; routers and the
orchestrator carry a deploy-time ROUTE table in their instructions
instead.

Exit 1 on any drift. Run as the last deploy step and nightly (the Routine
equivalent - operations/MONITORING.md).

Usage: python3 verify_deployment.py [--json out.json] [--only a,b]
                                    [--ignore-version]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
CONV = HERE.parent
BUILD = CONV / "build"
try:
    from dotenv import load_dotenv
    load_dotenv(CONV / "setup" / ".env")
except ImportError:
    pass

from _azure_helpers import strip_deploy_blocks, tool_type  # noqa: E402
from _foundry_runtime import (get_runtime, knowledge_source,  # noqa: E402
                              memory_backend, read_ledger)
from attach_integrations import REGISTRY, UNMANAGED_OK, model_for  # noqa: E402
from create_delivery_agents import AGENTS as DELIVERY  # noqa: E402
import create_orchestrator as co  # noqa: E402

CHAT_MODEL = os.environ.get("MODEL_DEPLOYMENT_NAME", "gpt-4o")
# finding C4: NOT o3-mini - it carries none of the OpenAPI/MCP/AI Search/
# SharePoint/Web Search tools the reasoning agents need
REASONING_MODEL = os.environ.get("REASONING_MODEL_DEPLOYMENT_NAME", "o4-mini")
INTEGRATION_TYPES = {"openapi": "openapi", "mcp": "mcp",
                     "bing_grounding": "bing_grounding",
                     "azure_ai_search": "azure_ai_search"}
KS = knowledge_source()
# tool the advisory profile / advisor add when combined knowledge or durable
# memory is served from Azure AI Search instead of a second vector store (C3)
ADVISORY_SEARCH = {"azure_ai_search"} if KS["mode"] == "ai-search" else set()
ADVISOR_SEARCH = ({"azure_ai_search"}
                  if memory_backend() == "search-index" else set())


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def expected_agents() -> dict[str, dict]:
    """name -> {instructions_sha, tools (set of type names), model}"""
    mf = json.loads((BUILD / "manifest.json").read_text())
    out = {}
    for a in mf["agents"]:
        if a.get("alias_of"):
            continue
        text = (BUILD / a["instructions_file"]).read_text(encoding="utf-8")
        # routers carry a ROUTE table in their instructions, not a tool (C2)
        out[a["name"]] = {"sha": sha(strip_deploy_blocks(text)),
                          "tools": set(a["tools"]),
                          "model": CHAT_MODEL}
    for name, spec in DELIVERY.items():
        out[name] = {"sha": sha(strip_deploy_blocks(
            __import__("create_delivery_agents").build_instructions(name))),
            "tools": ({"file_search"} if spec.get("knowledge") else set())
            | ({"code_interpreter"} if spec.get("code") else set()),
            "model": spec["model"]}
    out[co.ADVISOR] = {"sha": sha(strip_deploy_blocks(co.advisor_instructions())),
                       "tools": {"file_search", "bing_grounding"} | ADVISOR_SEARCH,
                       "model": REASONING_MODEL}
    out[co.VERIFIER] = {"sha": sha(strip_deploy_blocks(co.verifier_instructions())),
                        "tools": set(), "model": REASONING_MODEL}
    out[co.ORCHESTRATOR] = {"sha": sha(strip_deploy_blocks(co.orchestrator_instructions())),
                            "tools": {"bing_grounding"},
                            "model": REASONING_MODEL}
    # registry: model tier + integration tools + advisory profile additions
    for name, cfg in REGISTRY["agents"].items():
        if name in out:
            out[name]["model"] = model_for(cfg)
            for t in cfg["tools"]:
                out[name]["tools"].add(
                    INTEGRATION_TYPES[REGISTRY["connections"][t]["type"]])
    for name in REGISTRY.get("advisory_read_only_toolset", {}).get("agents", []):
        if name in out:
            out[name]["tools"] |= {"code_interpreter", "file_search"} | ADVISORY_SEARCH
    # versions promoted by the last deploy (finding C19)
    for name, entry in read_ledger().get("agents", {}).items():
        if name in out:
            out[name]["version"] = entry.get("version")
    return out


def openapi_writes(agent) -> list[str]:
    """Names of OpenAPI tools on the live agent exposing a non-GET verb."""
    bad = []
    for t in agent.tools or []:
        if tool_type(t) != "openapi":
            continue
        spec = getattr(t, "openapi", None)
        d = spec.as_dict() if hasattr(spec, "as_dict") else (spec or {})
        paths = (d.get("spec") or {}).get("paths", {})
        for ops in paths.values():
            if any(v.lower() not in ("get", "parameters") for v in ops):
                bad.append(d.get("name", "?"))
                break
    return bad


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    ap.add_argument("--json", help="write the report here")
    ap.add_argument("--ignore-version", action="store_true",
                    help="skip the agent-version comparison (C19)")
    args = ap.parse_args()

    rt = get_runtime(os.environ.get("PROJECT_ENDPOINT"))
    expected = expected_agents()
    live = rt.list_agents()
    ledger = read_ledger()
    keep = set(args.only.split(",")) if args.only else None
    report: dict[str, dict] = {}
    drift = 0

    for name in sorted(set(expected) | set(live)):
        if keep and name not in keep:
            continue
        if name not in live:
            report[name] = {"state": "ONLY IN BUILD"}
            drift += 1
            continue
        if name not in expected:
            state = "ONLY IN FOUNDRY" if name not in UNMANAGED_OK else "IDENTICAL"
            report[name] = {"state": state, "note": "unmanaged live agent"}
            drift += state != "IDENTICAL"
            continue
        agent, exp = live[name], expected[name]
        reasons = []
        if sha(strip_deploy_blocks(agent.instructions or "")) != exp["sha"]:
            reasons.append("instructions")
        live_tools = {tool_type(t) for t in (agent.tools or [])}
        if live_tools != exp["tools"]:
            reasons.append(f"tools live={sorted(live_tools)} expected={sorted(exp['tools'])}")
        if (agent.model or "") != exp["model"]:
            reasons.append(f"model live={agent.model} expected={exp['model']}")
        want_version = exp.get("version")
        if not args.ignore_version and want_version:
            if agent.version is None:
                reasons.append(f"version live=not versioned by this runtime "
                               f"expected={want_version} (classic fallback "
                               f"runtime — finding C1)")
            elif str(agent.version) != str(want_version):
                reasons.append(f"version live={agent.name}:{agent.version} "
                               f"expected={agent.name}:{want_version} "
                               f"(build/agent-versions.json; a portal edit or "
                               f"an unpromoted version is serving traffic)")
        writes = openapi_writes(agent)
        if writes:
            reasons.append(f"WRITE OPERATIONS exposed by {writes}")
        if REGISTRY["agents"].get(name, {}).get("write_connections"):
            reasons.append("registry write_connections not empty")
        report[name] = {"state": "DIFFERENT" if reasons else "IDENTICAL",
                        "reasons": reasons}
        drift += bool(reasons)

    for name, r in report.items():
        print(f"{r['state']:16} {name}"
              + (f"  <- {'; '.join(r['reasons'])}" if r.get("reasons") else "")
              + (f"  ({r['note']})" if r.get("note") else ""))
    if args.json:
        # agent names stay top-level (unchanged shape); the deploy context
        # is added under reserved "_" keys.
        Path(args.json).write_text(json.dumps(
            {**report,
             "_promoted": ledger.get("agents", {}),
             "_kit_release": ledger.get("_kit_release"),
             "_api_version": ledger.get("_api_version")},
            indent=1), encoding="utf-8")
    if not ledger.get("agents"):
        print("\nnote: build/agent-versions.json is empty — version comparison "
              "skipped. build/ is git-ignored, so restore the ledger the "
              "release pipeline published with the deploy, or re-run "
              "deploy.sh to record the promoted versions (finding C19)")
    print(f"\n{len(report)} agents compared, {drift} drifted")
    print("RESULT: " + ("IDENTICAL - live environment matches the verified build"
                        if not drift else
                        "DRIFT - re-run deploy.sh for the agents listed, or "
                        "investigate portal changes (operations/CHANGE_MANAGEMENT.md)"))
    return 1 if drift else 0


if __name__ == "__main__":
    sys.exit(main())
