#!/usr/bin/env python3
"""Apply the advisory-system profile (requirements g/h/i) to every
information-providing agent listed in the registry's
advisory_read_only_toolset (today: the five framework advisors, cyber-forum,
tpsrca-assessment-engine and infosec-assurance-advisor).

`enx-tprm-control-center` is deliberately NOT in that set: it is a router —
light tier, no tools, no addendum — and giving it the advisory profile would
put the enterprise read surface and code_interpreter on an agent whose only
job is to say which worker should answer (integrations/registry.json).


  1. Append agents/advisory_addendum.md to the agent's instructions
     (idempotent via marker) — the Word/Excel/PowerPoint/HTML
     file-generation contract and the enterprise read-source charter.
  2. Ensure the code_interpreter tool is attached (python-docx, openpyxl,
     python-pptx run there), preserving all existing tools.
  2b. Wire the COMBINED knowledge (every skill's references +
     advisor-knowledge/ packs) so a framework advisor answering a
     cross-framework question (DORA vs ISO 27005, NIS2 vs NIST CSF) is
     grounded in the packs the export does not contain
     (governance/PERSONA-COVERAGE.md).

     The service allows exactly ONE vector store per agent (finding C3),
     so the previous design — the agent's own vs-<agent> PLUS
     vs-assurance-combined on the same file_search tool — is invalid and
     has been removed. The agent keeps its single per-agent store and the
     combined knowledge comes from KNOWLEDGE_SOURCE (setup/.env):

       ai-search     Azure AI Search / Foundry IQ knowledge base
                     KNOWLEDGE_INDEX_NAME over the project connection
                     SEARCH_CONNECTION_NAME, attached as the GA Azure AI
                     Search tool (the recommended target state)
       vector-store  default / transition: nothing extra is attached;
                     cross-framework questions are answered by ROUTE-ing
                     to infosec-assurance-advisor, which holds
                     vs-assurance-combined as its one store
       none          no combined grounding (isolated environments)
  3. Report tier/toolset status (the tools themselves are attached by
     attach_integrations.py from the same registry — run it first).

Run AFTER create_agents.py + create_delivery_agents.py +
attach_integrations.py + create_orchestrator.py (the advisor must exist).
Idempotent; on the GA runtime each run saves a new immutable agent version
recorded in build/agent-versions.json (finding C19). --dry-run needs no
Azure SDK.
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

HEREPATH = Path(__file__).resolve().parent
sys.path.insert(0, str(HEREPATH))
from _foundry_runtime import (ai_search_tool, get_runtime,  # noqa: E402
                              knowledge_source, record_version)
from _azure_helpers import (dedupe_tools, kit_metadata,  # noqa: E402
                            tool_type)

ENDPOINT = os.environ.get("PROJECT_ENDPOINT")
MARKER = "# Advisory-system addendum"
COMBINED_STORE = "vs-assurance-combined"

REGISTRY = json.loads((CONV / "integrations" / "registry.json")
                      .read_text(encoding="utf-8"))
PROFILE = REGISTRY["advisory_read_only_toolset"]
ADDENDUM = (CONV / "agents" / "advisory_addendum.md").read_text(encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", help="single agent name")
    args = ap.parse_args()

    targets = [a for a in PROFILE["agents"]
               if not args.only or a == args.only]
    if not targets:
        sys.exit(f"unknown advisory agent {args.only!r}")

    ks = knowledge_source()
    if args.dry_run:
        for name in targets:
            tier = REGISTRY["agents"].get(name, {}).get("model_tier")
            tools = REGISTRY["agents"].get(name, {}).get("tools", [])
            print(f"[dry-run] {name}: tier={tier}, registry tools={len(tools)}, "
                  f"would append addendum ({len(ADDENDUM)} chars) + ensure "
                  f"code_interpreter; combined knowledge via "
                  f"KNOWLEDGE_SOURCE={ks['mode']}"
                  + (f" (index {ks['index']} over connection "
                     f"{ks['connection']})" if ks["mode"] == "ai-search"
                     else " (ROUTE to the advisor)"
                     if ks["mode"] == "vector-store" else "")
                  + "; ONE vector store per agent — finding C3")
        return 0

    if not ENDPOINT:
        sys.exit("Set PROJECT_ENDPOINT (setup/.env)")
    from azure.ai.agents.models import CodeInterpreterTool

    rt = get_runtime(ENDPOINT)
    live = rt.list_agents()

    # Combined knowledge source (finding C3) - resolved once.
    search_defs: list = []
    if ks["mode"] == "ai-search":
        conn = rt.connection_id(ks["connection"])
        search_defs = ai_search_tool(conn, ks["index"]) if conn else []
        if not search_defs:
            print(f"note: KNOWLEDGE_SOURCE=ai-search but connection "
                  f"{ks['connection']!r} or the Azure AI Search tool is "
                  f"unavailable - combined knowledge not attached; "
                  f"cross-framework questions fall back to ROUTE-ing to "
                  f"infosec-assurance-advisor (enterprise/"
                  f"MEMORY_AND_LEARNING.md §2)")
    elif ks["mode"] == "vector-store":
        print(f"note: KNOWLEDGE_SOURCE=vector-store - the combined store "
              f"{COMBINED_STORE} stays on infosec-assurance-advisor only "
              f"(one vector store per agent, finding C3); advisory agents "
              f"reach it by ROUTE-ing to the advisor")

    for name in targets:
        agent = live.get(name)
        if agent is None:
            print(f"skip {name}: not deployed (run the create scripts first)")
            continue
        # ONE vector store per agent: keep the agent's own store exactly as
        # create_agents.py built it; never append a second one.
        resources = agent.tool_resources
        res = (resources.as_dict() if hasattr(resources, "as_dict")
               else dict(resources or {}))
        fsr = dict(res.get("file_search") or {})
        ids = list(fsr.get("vector_store_ids") or [])
        if len(ids) > 1:
            ids = ids[:1]          # repair an environment built before C3
            print(f"  {name}: trimmed {len(fsr['vector_store_ids'])} attached "
                  f"vector stores to 1 (service limit, finding C3)")
        if ids:
            fsr["vector_store_ids"] = ids
            res["file_search"] = fsr

        instructions = agent.instructions or ""
        if MARKER not in instructions:
            instructions = instructions.rstrip() + "\n\n---\n\n" + ADDENDUM
        # keep every existing tool; add code_interpreter if absent
        tools = list(agent.tools or [])
        has_ci = any(tool_type(t) == "code_interpreter" for t in tools)
        if not has_ci:
            tools += CodeInterpreterTool().definitions

        expect = REGISTRY["agents"].get(name, {})
        has_fs = any(tool_type(t) == "file_search" for t in tools)
        if ids and not has_fs:
            from azure.ai.agents.models import FileSearchTool
            tools += FileSearchTool(vector_store_ids=ids).definitions
        has_search = any(tool_type(t) == "azure_ai_search" for t in tools)
        if search_defs and not has_search:
            tools += search_defs

        # the live list can already carry a twin of something attached here
        # (a re-run, or attach_integrations.py in the same deploy)
        tools = dedupe_tools(tools, label=name)

        updated = rt.upsert_agent(
            name=name, model=agent.model, description=agent.description,
            instructions=instructions, tools=tools,
            tool_resources=res or None, metadata=kit_metadata(),
            existing=agent)
        record_version(updated, note="advisory profile")
        print(f"applied  {updated.ref}: "
              f"addendum={'kept' if MARKER in (agent.instructions or '') else 'added'}, "
              f"code_interpreter={'kept' if has_ci else 'added'}, "
              f"vector stores={len(ids)}, "
              f"combined knowledge={ks['mode']}"
              f"{' (attached)' if search_defs else ''}, "
              f"registry tier={expect.get('model_tier')} "
              f"(tools attached by attach_integrations.py)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
