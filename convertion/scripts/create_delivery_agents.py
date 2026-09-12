#!/usr/bin/env python3
"""Create/update the delivery-layer agents (requirements d, d2, e, f, j):

  ciso-global-report, tpa-evidence-analyzer, soc-report-analyzer,
  pentest-report-analyzer, template-manager

Run AFTER create_agents.py and BEFORE attach_integrations.py (their tools
and model tiers come from integrations/registry.json) and
create_orchestrator.py (so the orchestrator connects to them too).

These five agents are options 6-10 of the control-center menu
(agents/overlays/enx-tprm-control-center.md), so they are ROUTE targets of
`enx-tprm-control-center`. Because they only exist once this script has
run, the router is wired in a later pass: `create_agents.py --rewire`
(deploy.sh step [4b]). Running this script without that pass leaves the
control-center routing only to the agents that existed before it.

Each agent = persona preamble + agents/<name>_instructions.md + the
approval gate, plus a knowledge vector store seeded with the methodology
files it must share with the base agents (so thresholds/templates stay
byte-consistent with the previous environment):

  ciso-global-report      -> ciso-reporting + pptx-executive-summary-ciso +
                             tpsrca knowledge, templates/registry.json,
                             advisor pack iso27005 (residual-risk wording)
  tpa-evidence-analyzer   -> pdf-full-coverage-analyzer knowledge + advisor
                             packs soc-isae, pentest-standards, csa-ccm,
                             iso22301, pci-dss, cloud-ict, tpa-evidence-
                             review-playbook, gdpr-art28 (citable sources)
  soc-report-analyzer     -> pdf-full-coverage-analyzer + soc-isae +
                             governance compendium (COSO)
  pentest-report-analyzer -> pdf-full-coverage-analyzer + pentest-standards
                             + cis-controls (Control 18)
  template-manager        -> templates/registry.json + every template asset
                             (also attached to code_interpreter for preview
                             rendering)
  all analyzers           -> knowledge packs file-intake / pdf-reading /
                             enx-writing-style; research-pattern overlay

Idempotent by name: on the GA runtime each run saves a new immutable
version `<name>:<n>` recorded in build/agent-versions.json (finding C19);
on the classic fallback runtime the agent is updated in place.
--dry-run needs no Azure SDK.
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
# finding C4: NOT o3-mini - it carries none of the OpenAPI/MCP/AI Search/
# SharePoint/Web Search tools the reasoning agents need
REASONING_MODEL = os.environ.get("REASONING_MODEL_DEPLOYMENT_NAME", "o4-mini")

sys.path.insert(0, str(HERE))
from create_orchestrator import persona  # noqa: E402
from convert_skills import APPROVAL_GATE  # noqa: E402
from _azure_helpers import file_map_block, kit_metadata  # noqa: E402
from _foundry_runtime import get_runtime, record_version  # noqa: E402

_PACKS = ["agents/knowledge-packs/file-intake-foundry.md",
          "agents/knowledge-packs/pdf-reading-foundry.md",
          "agents/knowledge-packs/enx-writing-style.md"]
_ADV = "agents/advisor-knowledge/"

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
            _ADV + "iso27005-risk-management.md",
            _ADV + "tpsrca-supplier-types.md",
        ] + _PACKS,
        "overlay": True,
    },
    "tpa-evidence-analyzer": {
        "model": REASONING_MODEL,
        "description": "Analyses the SharePoint TPA/Active evidence tree for "
                       "a supplier/service: per-file content id, scope, "
                       "emission date, validity period, findings; "
                       "consolidated evidence analysis report.",
        "knowledge": ["build/agents/pdf-full-coverage-analyzer/knowledge/*",
                      _ADV + "soc-isae-assurance-reports.md",
                      _ADV + "pentest-standards-owasp-ptes-cvss.md",
                      _ADV + "csa-ccm-caiq-star.md",
                      _ADV + "iso22301-business-continuity.md",
                      _ADV + "pci-dss-v4-supplier-assurance.md",
                      _ADV + "cloud-ict-service-assurance.md",
                      _ADV + "tpa-evidence-review-playbook.md",
                      _ADV + "gdpr-art28-sccs.md"] + _PACKS,
        "overlay": True,
    },
    "soc-report-analyzer": {
        "model": REASONING_MODEL,
        "description": "SOC 1/2/3 (Type 1/2) report analysis: opinion, "
                       "scope, period, every exception, CUEC mapping, "
                       "subservice carve-outs, reliance verdict.",
        "knowledge": ["build/agents/pdf-full-coverage-analyzer/knowledge/*",
                      _ADV + "soc-isae-assurance-reports.md",
                      _ADV + "governance-frameworks-compendium.md"] + _PACKS,
        "overlay": True,
    },
    "pentest-report-analyzer": {
        "model": REASONING_MODEL,
        "description": "Penetration test report analysis: full normalised "
                       "findings register, scope/currency adequacy, "
                       "Euronext relevance, reliance verdict.",
        "knowledge": ["build/agents/pdf-full-coverage-analyzer/knowledge/*",
                      _ADV + "pentest-standards-owasp-ptes-cvss.md",
                      _ADV + "cis-controls-v8-1.md"] + _PACKS,
        "overlay": True,
    },
    "template-manager": {
        "model": CHAT_MODEL,
        "description": "Controlled template change process: inventory, "
                       "analyse, edit, visual before/after review, "
                       "approval-gated propagation. Never applies a change "
                       "without recorded human approval.",
        "knowledge": ["templates/registry.json",
                      "agents/knowledge-packs/enx-html-design-guide.md"],
        # template assets from the byte-verified code-tree (original layout)
        "code": ["build/agents/*/code-tree/assets/*template*",
                 "build/agents/*/code-tree/assets/*.pptx",
                 "templates/registry.json"],
    },
}


def build_instructions(name: str) -> str:
    """persona + charter (+ research overlay) + gate - importable so
    verify_conversion.py can freeze the hash offline."""
    spec = AGENTS[name]
    instr_file = CONV / "agents" / f"{name}_instructions.md"
    if not instr_file.exists():
        sys.exit(f"missing {instr_file}")
    text = persona() + "\n\n---\n\n" + instr_file.read_text(encoding="utf-8")
    if spec.get("overlay"):
        text += ("\n\n---\n\n" + (CONV / "agents" / "overlays" /
                                  "research-pattern.md").read_text(encoding="utf-8"))
    return text + APPROVAL_GATE


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

    plans = {}
    for name, spec in todo.items():
        instructions = build_instructions(name)
        plans[name] = (spec, instructions,
                       gather(spec.get("knowledge", [])),
                       gather(spec.get("code", [])))

    if args.dry_run:
        for name, (spec, instructions, know, code) in plans.items():
            print(f"[dry-run] {name}: model={spec['model']}, "
                  f"knowledge files={len(know)}, code files={len(code)}, "
                  f"instructions {len(instructions)} chars")
        print("[dry-run] control-center ROUTE table over these agents is "
              "wired by `create_agents.py --rewire` (deploy.sh step [4b])")
        return 0

    if not ENDPOINT:
        sys.exit("Set PROJECT_ENDPOINT (setup/.env)")
    from azure.ai.agents.models import CodeInterpreterTool, FileSearchTool
    from _azure_helpers import UploadCache, upload_files
    from create_orchestrator import ensure_store

    rt = get_runtime(ENDPOINT)
    live = rt.list_agents()
    cache = UploadCache(BUILD / "upload-cache.json")

    for name, (spec, instructions, know, code) in plans.items():
        tools, resources = [], {}
        if know:
            kids = upload_files(rt, know, cache,
                                label=f"{name} knowledge")
            store = ensure_store(rt, f"vs-{name}", kids)
            fs = FileSearchTool(vector_store_ids=[store.id])
            tools += fs.definitions
            resources.update(fs.resources)
        if code:
            cids = upload_files(rt, code, cache,
                                label=f"{name} code")
            ci = CodeInterpreterTool(file_ids=cids)
            tools += ci.definitions
            resources.update(ci.resources)
            instructions += file_map_block(list(zip([c.name for c in code], cids)))
        if name in live:
            from _azure_helpers import integration_tools
            tools += integration_tools(live[name])   # keep attach_integrations work

        agent = rt.upsert_agent(name=name, model=spec["model"],
                                description=spec["description"][:512],
                                instructions=instructions,
                                tools=tools, tool_resources=resources,
                                metadata=kit_metadata(),
                                existing=live.get(name))
        record_version(agent)
        print(f"{'updated' if name in live else 'created'}  {agent.ref} "
              f"({agent.id})")
    print("\nnext: `python3 create_agents.py --rewire` so the control-center "
          "ROUTE table covers these agents (deploy.sh step [4b])")
    return 0


if __name__ == "__main__":
    sys.exit(main())
