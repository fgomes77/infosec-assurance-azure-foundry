#!/usr/bin/env python3
"""Create/update the flagship layer: infosec-assurance-advisor and
infosec-assurance-orchestrator (plus the durable memory vector store).

Run AFTER create_agents.py (and ideally attach_integrations.py).

- advisor: reasoning model + combined knowledge vector store built from
  EVERY converted agent's knowledge files (build/agents/*/knowledge/*) +
  the persistent memory vector store + Bing web search (if configured).
- orchestrator: reasoning model + web search + connected-agent tools to
  every live agent (advisor included), so one entry point can route any
  assurance request.

Idempotent by name. --dry-run needs no Azure SDK.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONV = HERE.parent
BUILD = CONV / "build"
try:
    from dotenv import load_dotenv
    load_dotenv(CONV / "setup" / ".env")
except ImportError:
    pass

ENDPOINT = os.environ.get("PROJECT_ENDPOINT")
REASONING_MODEL = os.environ.get("REASONING_MODEL_DEPLOYMENT_NAME", "o3-mini")
BING_CONNECTION = os.environ.get("BING_CONNECTION_NAME", "bing-grounding")

ADVISOR = "infosec-assurance-advisor"
ORCHESTRATOR = "infosec-assurance-orchestrator"
MEMORY_STORE = "vs-assurance-memory"
KNOWLEDGE_STORE = "vs-assurance-combined"

ORCHESTRATOR_INSTRUCTIONS = """\
You are the single entry point for the InfoSec Assurance team's agent
environment. For each request, decide and act:

1. Broad or cross-framework advisory questions -> hand off to
   infosec_assurance_advisor (it holds the combined knowledge base and the
   team's durable memory).
2. Specialist pipeline work -> hand off to the matching specialist agent:
   OneTrust assessment analysis (dpia), Form B responses (onetrust_form_b),
   CISO deliverables (ciso_reporting / ciso_executive_summary), supplier
   OSINT assessments (deepsearch_protocol), threat questions (cyber_forum),
   regulation-specific depth (dora, nis2, eu_ai_act, iso27001, iso42001),
   document production (docx, pdf, pptx, xlsx), exhaustive PDF review
   (pdf_full_coverage_analyzer), TPRM scoring (tpsrca_assessment_engine).
3. Multi-part requests -> decompose, call several agents, and synthesise
   one coherent answer; state which agent produced which part.
4. Only answer directly when no specialist adds value; use web search for
   anything time-sensitive and cite sources.

Never fabricate a specialist's output; if a handoff fails, say so and give
your best direct answer, clearly labelled as such.
"""

# Same mandatory gate the converter appends to every specialist agent.
from convert_skills import APPROVAL_GATE  # noqa: E402


def persona() -> str:
    text = (CONV / "agents" / "persona_system_prompt.md").read_text(encoding="utf-8")
    return text.split("---", 2)[-1].strip()


def gather_knowledge_files() -> list[Path]:
    files = sorted(BUILD.glob("agents/*/knowledge/*"))
    # de-duplicate identical twins (e.g. the two slide-generator skills)
    seen, out = set(), []
    for f in files:
        key = (f.name, f.stat().st_size)
        if key not in seen:
            seen.add(key)
            out.append(f)
    return out


def ensure_store(agents_client, name: str, file_ids: list[str]):
    for vs in agents_client.vector_stores.list():
        if vs.name == name:
            return vs
    return agents_client.vector_stores.create_and_poll(
        name=name, file_ids=file_ids or None)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    knowledge = gather_knowledge_files()
    advisor_instructions = (persona() + "\n\n---\n\n" +
                            (CONV / "agents" / "advisor_instructions.md")
                            .read_text(encoding="utf-8") + APPROVAL_GATE)

    if args.dry_run:
        print(f"[dry-run] {ADVISOR}: model={REASONING_MODEL}, "
              f"combined knowledge files={len(knowledge)}, "
              f"stores=[{KNOWLEDGE_STORE}, {MEMORY_STORE}], web-search + "
              f"instructions {len(advisor_instructions)} chars")
        print(f"[dry-run] {ORCHESTRATOR}: model={REASONING_MODEL}, "
              f"web-search, connected to all live agents + {ADVISOR}")
        return 0

    if not ENDPOINT:
        sys.exit("Set PROJECT_ENDPOINT (setup/.env)")
    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential
    from azure.ai.agents.models import (BingGroundingTool, ConnectedAgentTool,
                                        FileSearchTool)
    agents_client = AIProjectClient(
        endpoint=ENDPOINT, credential=DefaultAzureCredential()).agents
    live = {a.name: a for a in agents_client.list_agents()}

    # ---- advisor -----------------------------------------------------
    kids = [agents_client.files.upload_and_poll(file_path=str(f),
                                                purpose="assistants").id
            for f in knowledge]
    kstore = ensure_store(agents_client, KNOWLEDGE_STORE, kids)
    mstore = ensure_store(agents_client, MEMORY_STORE, [])

    tools, resources = [], {}
    fs = FileSearchTool(vector_store_ids=[kstore.id, mstore.id])
    tools += fs.definitions
    resources.update(fs.resources)
    try:
        tools += BingGroundingTool(connection_id=BING_CONNECTION).definitions
    except Exception:
        print("note: Bing grounding not attached (connection missing?)")

    kwargs = dict(model=REASONING_MODEL, name=ADVISOR,
                  description="Senior reasoning advisor across all InfoSec "
                              "Assurance domains, grounded in the combined "
                              "knowledge base with durable team memory.",
                  instructions=advisor_instructions,
                  tools=tools, tool_resources=resources)
    advisor = (agents_client.update_agent(live[ADVISOR].id, **kwargs)
               if ADVISOR in live else agents_client.create_agent(**kwargs))
    print(f"{'updated' if ADVISOR in live else 'created'}  {ADVISOR} ({advisor.id})")
    live[ADVISOR] = advisor

    # ---- orchestrator ------------------------------------------------
    otools = []
    try:
        otools += BingGroundingTool(connection_id=BING_CONNECTION).definitions
    except Exception:
        pass
    for name, agent in sorted(live.items()):
        if name == ORCHESTRATOR:
            continue
        otools += ConnectedAgentTool(
            id=agent.id, name=name.replace("-", "_"),
            description=(agent.description or f"Specialist agent {name}")[:512],
        ).definitions

    okwargs = dict(model=REASONING_MODEL, name=ORCHESTRATOR,
                   description="Entry point: routes and decomposes InfoSec "
                               "Assurance requests across all agents.",
                   instructions=(persona() + "\n\n---\n\n"
                                 + ORCHESTRATOR_INSTRUCTIONS + APPROVAL_GATE),
                   tools=otools)
    if ORCHESTRATOR in live:
        agents_client.update_agent(live[ORCHESTRATOR].id, **okwargs)
        print(f"updated  {ORCHESTRATOR} -> {len(live) - 1} connected agents")
    else:
        agents_client.create_agent(**okwargs)
        print(f"created  {ORCHESTRATOR} -> {len(live)} connected agents")
    return 0


if __name__ == "__main__":
    sys.exit(main())
