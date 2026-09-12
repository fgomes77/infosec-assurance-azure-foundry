#!/usr/bin/env python3
"""Create/update the delivery-layer agents (requirements d, d2, e, f, j):

  ciso-global-report, tpa-evidence-analyzer, soc-report-analyzer,
  pentest-report-analyzer, template-manager

Run AFTER create_agents.py and BEFORE attach_integrations.py (their tools
and model tiers come from integrations/registry.json) and
create_orchestrator.py (so the orchestrator connects to them too).

Each agent = persona preamble + agents/<name>_instructions.md + the
approval gate, plus a knowledge vector store seeded with the methodology
files it must share with the base agents (so thresholds/templates stay
byte-consistent with the previous environment):

  ciso-global-report      -> ciso-reporting + pptx-executive-summary-ciso +
                             tpsrca knowledge, templates/registry.json
  tpa-evidence-analyzer   -> pdf-full-coverage-analyzer knowledge
  soc-report-analyzer     -> pdf-full-coverage-analyzer knowledge
  pentest-report-analyzer -> pdf-full-coverage-analyzer knowledge
  template-manager        -> templates/registry.json + every template asset
                             (also attached to code_interpreter for preview
                             rendering)

Idempotent by name. --dry-run needs no Azure SDK.
"""

from __future__ import annotations

import argparse
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

import os
ENDPOINT = os.environ.get("PROJECT_ENDPOINT")
CHAT_MODEL = os.environ.get("MODEL_DEPLOYMENT_NAME", "gpt-4o")
REASONING_MODEL = os.environ.get("REASONING_MODEL_DEPLOYMENT_NAME", "o3-mini")

from create_orchestrator import persona  # noqa: E402
from convert_skills import APPROVAL_GATE  # noqa: E402

# name -> (model, knowledge sources [globs relative to repo], code files)
AGENTS: dict[str, dict] = {
    "ciso-global-report": {
        "model": REASONING_MODEL,
        "description": "Global CISO 9-slide PPTX briefing on one supplier/"
                       "service assessment: contract owner, impacted ENX "
                       "entities, service+supplier description, risk & "
                       "controls resume, internal/external exposure diagram, "
                       "ICT inherent+residual scores, ENX actions to the "
                       "Contract Owner.",
        "knowledge": [
            "build/agents/ciso-reporting/knowledge/*",
            "build/agents/pptx-executive-summary-ciso/knowledge/*",
            "build/agents/tpsrca-assessment-engine/knowledge/*",
            "templates/registry.json",
        ],
    },
    "tpa-evidence-analyzer": {
        "model": REASONING_MODEL,
        "description": "Analyses the SharePoint TPA/Active evidence tree for "
                       "a supplier/service: per-file content id, scope, "
                       "emission date, validity period, findings; "
                       "consolidated evidence analysis report.",
        "knowledge": ["build/agents/pdf-full-coverage-analyzer/knowledge/*"],
    },
    "soc-report-analyzer": {
        "model": REASONING_MODEL,
        "description": "SOC 1/2/3 (Type 1/2) report analysis: opinion, "
                       "scope, period, every exception, CUEC mapping, "
                       "subservice carve-outs, reliance verdict.",
        "knowledge": ["build/agents/pdf-full-coverage-analyzer/knowledge/*"],
    },
    "pentest-report-analyzer": {
        "model": REASONING_MODEL,
        "description": "Penetration test report analysis: full normalised "
                       "findings register, scope/currency adequacy, "
                       "Euronext relevance, reliance verdict.",
        "knowledge": ["build/agents/pdf-full-coverage-analyzer/knowledge/*"],
    },
    "template-manager": {
        "model": CHAT_MODEL,
        "description": "Controlled template change process: inventory, "
                       "analyse, edit, visual before/after review, "
                       "approval-gated propagation. Never applies a change "
                       "without recorded human approval.",
        "knowledge": ["templates/registry.json"],
        "code": ["build/agents/*/code/*template*", "templates/registry.json"],
    },
}


def gather(globs: list[str]) -> list[Path]:
    out: list[Path] = []
    for g in globs:
        out += sorted(CONV.glob(g))
    seen, uniq = set(), []
    for f in out:
        key = (f.name, f.stat().st_size)
        if f.is_file() and key not in seen:
            seen.add(key)
            uniq.append(f)
    return uniq


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", help="single agent name")
    args = ap.parse_args()

    todo = {k: v for k, v in AGENTS.items()
            if not args.only or k == args.only}
    if not todo:
        sys.exit(f"unknown agent {args.only!r}")

    pre = persona()
    plans = {}
    for name, spec in todo.items():
        instr_file = CONV / "agents" / f"{name}_instructions.md"
        if not instr_file.exists():
            sys.exit(f"missing {instr_file}")
        instructions = (pre + "\n\n---\n\n" +
                        instr_file.read_text(encoding="utf-8") + APPROVAL_GATE)
        plans[name] = (spec, instructions,
                       gather(spec.get("knowledge", [])),
                       gather(spec.get("code", [])))

    if args.dry_run:
        for name, (spec, instructions, know, code) in plans.items():
            print(f"[dry-run] {name}: model={spec['model']}, "
                  f"knowledge files={len(know)}, code files={len(code)}, "
                  f"instructions {len(instructions)} chars")
        return 0

    if not ENDPOINT:
        sys.exit("Set PROJECT_ENDPOINT (setup/.env)")
    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential
    from azure.ai.agents.models import CodeInterpreterTool, FileSearchTool
    from _azure_helpers import UploadCache, upload_files
    from create_orchestrator import ensure_store

    agents_client = AIProjectClient(
        endpoint=ENDPOINT, credential=DefaultAzureCredential()).agents
    live = {a.name: a for a in agents_client.list_agents()}
    cache = UploadCache(BUILD / "upload-cache.json")

    for name, (spec, instructions, know, code) in plans.items():
        tools, resources = [], {}
        if know:
            kids = upload_files(agents_client, know, cache,
                                label=f"{name} knowledge")
            store = ensure_store(agents_client, f"vs-{name}", kids)
            fs = FileSearchTool(vector_store_ids=[store.id])
            tools += fs.definitions
            resources.update(fs.resources)
        if code:
            cids = upload_files(agents_client, code, cache,
                                label=f"{name} code")
            ci = CodeInterpreterTool(file_ids=cids)
            tools += ci.definitions
            resources.update(ci.resources)

        kwargs = dict(model=spec["model"], name=name,
                      description=spec["description"][:512],
                      instructions=instructions,
                      tools=tools or None, tool_resources=resources or None)
        agent = (agents_client.update_agent(live[name].id, **kwargs)
                 if name in live else agents_client.create_agent(**kwargs))
        print(f"{'updated' if name in live else 'created'}  {name} ({agent.id})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
