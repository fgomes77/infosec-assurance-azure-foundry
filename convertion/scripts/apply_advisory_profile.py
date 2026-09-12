#!/usr/bin/env python3
"""Apply the advisory-system profile (requirements g/h/i) to every
information-providing agent listed in the registry's
advisory_read_only_toolset:

  1. Append agents/advisory_addendum.md to the agent's instructions
     (idempotent via marker) — the Word/Excel/PowerPoint/HTML
     file-generation contract and the enterprise read-source charter.
  2. Ensure the code_interpreter tool is attached (python-docx, openpyxl,
     python-pptx run there), preserving all existing tools.
  2b. Attach the combined knowledge store (vs-assurance-combined: every
     skill's references + advisor-knowledge/ packs) as a SECOND
     file_search store, so a framework advisor answering a cross-framework
     question (DORA vs ISO 27005, NIS2 vs NIST CSF) is grounded in the
     packs the export does not contain (governance/PERSONA-COVERAGE.md).
  3. Report tier/toolset status (the tools themselves are attached by
     attach_integrations.py from the same registry — run it first).

Run AFTER create_agents.py + create_delivery_agents.py +
attach_integrations.py + create_orchestrator.py (the advisor must exist).
Idempotent. --dry-run needs no Azure SDK.
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

    if args.dry_run:
        for name in targets:
            tier = REGISTRY["agents"].get(name, {}).get("model_tier")
            tools = REGISTRY["agents"].get(name, {}).get("tools", [])
            print(f"[dry-run] {name}: tier={tier}, registry tools={len(tools)}, "
                  f"would append addendum ({len(ADDENDUM)} chars) + ensure "
                  f"code_interpreter")
        return 0

    if not ENDPOINT:
        sys.exit("Set PROJECT_ENDPOINT (setup/.env)")
    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential
    from azure.ai.agents.models import CodeInterpreterTool

    agents_client = AIProjectClient(
        endpoint=ENDPOINT, credential=DefaultAzureCredential()).agents
    live = {a.name: a for a in agents_client.list_agents()}
    combined = next((v.id for v in agents_client.vector_stores.list()
                     if v.name == COMBINED_STORE), None)
    if combined is None:
        print(f"note: {COMBINED_STORE} not found (run create_orchestrator.py) "
              f"- combined grounding not attached")

    for name in targets:
        agent = live.get(name)
        if agent is None:
            print(f"skip {name}: not deployed (run the create scripts first)")
            continue
        # second file_search store: the combined knowledge base
        resources = agent.tool_resources
        res = (resources.as_dict() if hasattr(resources, "as_dict")
               else dict(resources or {}))
        fsr = dict(res.get("file_search") or {})
        ids = list(fsr.get("vector_store_ids") or [])
        if combined and combined not in ids:
            ids.append(combined)
        stores_changed = combined is not None and ids != list(
            fsr.get("vector_store_ids") or [])
        if ids:
            fsr["vector_store_ids"] = ids
            res["file_search"] = fsr

        instructions = agent.instructions or ""
        if MARKER not in instructions:
            instructions = instructions.rstrip() + "\n\n---\n\n" + ADDENDUM
        # keep every existing tool; add code_interpreter if absent
        tools = list(agent.tools or [])
        has_ci = any(getattr(t, "type", None) == "code_interpreter"
                     or (isinstance(t, dict) and t.get("type") == "code_interpreter")
                     for t in tools)
        if not has_ci:
            tools += CodeInterpreterTool().definitions

        expect = REGISTRY["agents"].get(name, {})
        has_fs = any(getattr(t, "type", None) == "file_search"
                     or (isinstance(t, dict) and t.get("type") == "file_search")
                     for t in tools)
        if ids and not has_fs:
            from azure.ai.agents.models import FileSearchTool
            tools += FileSearchTool(vector_store_ids=ids).definitions
        agents_client.update_agent(agent.id, instructions=instructions,
                                   tools=tools, tool_resources=res or None)
        print(f"applied  {name}: addendum={'kept' if MARKER in (agent.instructions or '') else 'added'}, "
              f"code_interpreter={'kept' if has_ci else 'added'}, "
              f"combined store={'added' if stores_changed else 'kept'}, "
              f"registry tier={expect.get('model_tier')} "
              f"(tools attached by attach_integrations.py)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
