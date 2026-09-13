#!/usr/bin/env python3
"""Create/update the delivery-layer agents (requirements d, d2, e, f, j
and the TPRM lifecycle systems k-t):

  ciso-global-report, tpa-evidence-analyzer, soc-report-analyzer,
  pentest-report-analyzer, template-manager,
  supplier-intake-triage (k), contract-security-review (l),
  dora-register-builder (m), concentration-risk-analyzer (n),
  continuous-monitoring-radar (o), supplier-incident-assessor (p),
  exit-offboarding-assurance (q), findings-remediation-register (r),
  isms-audit-pack (s), regulatory-change-watch (t)

Run AFTER create_agents.py and BEFORE attach_integrations.py (their tools
and model tiers come from integrations/registry.json) and
create_orchestrator.py (so the orchestrator connects to them too).

The first five are options 6-10 of the control-center menu
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
  k-t lifecycle systems   -> the framework knowledge each one reasons from
                             (DORA/NIS2 converted stores, advisor packs
                             gdpr-art28, cloud-ict, iso22301, iso27005,
                             iso27002, cis, csa-ccm, tpa-evidence-playbook)
                             plus governance/RISK_THRESHOLDS.md wherever the
                             system assigns a severity or a tier, so no
                             threshold is re-invented per agent. They render
                             through the EXISTING generic renderers
                             (docx-generic / xlsx-generic) or emit HTML
                             directly - no new renderer, no new approval path.

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
from inference_profiles import params_for  # noqa: E402

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
            # the output contract this agent must emit, in its own store
            "templates/ciso_global_deck.schema.json",
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
    # ---- TPRM lifecycle systems (requirements k-t) -------------------
    # Same governed path as the five above: charter + persona + approval
    # gate, a knowledge store of the verified methodology packs, the
    # read-only enterprise toolset from integrations/registry.json, and a
    # pipeline in workflows/pipelines.json rendering through an EXISTING
    # renderer (docx-generic / xlsx-generic / direct HTML) - no new
    # renderer, so the verifier + approval + SharePoint path is unchanged.
    "supplier-intake-triage": {
        "model": REASONING_MODEL,
        "description": "Lifecycle gate 1: supplier/service intake triage and "
                       "tiering - supplier type, DORA critical-or-important-"
                       "function test, inherent risk profile, the assurance "
                       "depth and evidence set that follow, and the "
                       "obligations triggered.",
        "knowledge": [_ADV + "tpsrca-supplier-types.md",
                      _ADV + "cloud-ict-service-assurance.md",
                      _ADV + "gdpr-art28-sccs.md",
                      _ADV + "iso27005-risk-management.md",
                      "build/agents/tpsrca-assessment-engine/knowledge/*",
                      "governance/RISK_THRESHOLDS.md"] + _PACKS,
        "overlay": True,
    },
    "contract-security-review": {
        "model": REASONING_MODEL,
        "description": "Contract, DPA and schedule review clause by clause "
                       "against DORA Art. 30(2)/(3) and Art. 29, GDPR "
                       "Art. 28(3) + SCCs, NIS2 Art. 21(2)(d), ENX security "
                       "minimums, incident clocks, resilience and exit - with "
                       "proposed wording for Legal.",
        "knowledge": [_ADV + "gdpr-art28-sccs.md",
                      _ADV + "cloud-ict-service-assurance.md",
                      _ADV + "iso22301-business-continuity.md",
                      "build/agents/dora/knowledge/*",
                      "build/agents/nis2/knowledge/*"] + _PACKS,
        "overlay": True,
    },
    "dora-register-builder": {
        "model": REASONING_MODEL,
        "description": "DORA Art. 28(3) Register of Information: builds the "
                       "ITS tables (entities, arrangements, providers, "
                       "services, functions, subcontracting chain, data "
                       "locations, exit) and validates every rule breach "
                       "before the owner submits it.",
        "knowledge": ["build/agents/dora/knowledge/*",
                      _ADV + "cloud-ict-service-assurance.md",
                      _ADV + "tpsrca-supplier-types.md"] + _PACKS,
        "overlay": True,
    },
    "concentration-risk-analyzer": {
        "model": REASONING_MODEL,
        "description": "DORA Art. 29 concentration and fourth-party chain "
                       "analysis: provider / fourth-party / geography / "
                       "technology / entity exposure, impact of failure "
                       "against ENX recovery objectives, substitutability "
                       "and treatment options.",
        "knowledge": ["build/agents/dora/knowledge/*",
                      _ADV + "iso22301-business-continuity.md",
                      _ADV + "cloud-ict-service-assurance.md",
                      _ADV + "iso27005-risk-management.md",
                      "governance/RISK_THRESHOLDS.md"] + _PACKS,
        "overlay": True,
    },
    "continuous-monitoring-radar": {
        "model": REASONING_MODEL,
        "description": "Third-Party Assurance Radar (HTML): evidence expiry, "
                       "assessments due, external rating drift, overdue "
                       "findings, expiring risk acceptances and "
                       "undispositioned watch items, recomputed against an "
                       "as-at date.",
        "knowledge": [_ADV + "tpa-evidence-review-playbook.md",
                      _ADV + "soc-isae-assurance-reports.md",
                      _ADV + "csa-ccm-caiq-star.md",
                      _ADV + "iso27002-control-attributes.md",
                      "agents/knowledge-packs/enx-html-design-guide.md",
                      "governance/RISK_THRESHOLDS.md"] + _PACKS,
        "overlay": True,
    },
    "supplier-incident-assessor": {
        "model": REASONING_MODEL,
        "description": "Supplier incident impact on Euronext plus the "
                       "notification-duty assessment with deadlines computed "
                       "from the evidenced awareness timestamp (DORA "
                       "Art. 18/19, NIS2 Art. 23, GDPR Art. 33/34) - "
                       "assessment only, it never notifies.",
        "knowledge": ["build/agents/dora/knowledge/*",
                      "build/agents/nis2/knowledge/*",
                      _ADV + "gdpr-art28-sccs.md",
                      _ADV + "iso22301-business-continuity.md",
                      _ADV + "nist-csf-2-0.md",
                      "governance/RISK_THRESHOLDS.md"] + _PACKS,
        "overlay": True,
    },
    "exit-offboarding-assurance": {
        "model": REASONING_MODEL,
        "description": "DORA Art. 28(8) exit strategy (triggers, options, "
                       "transition plan, data exit, continuity, test record, "
                       "readiness verdict) and the evidenced offboarding "
                       "checklist at termination.",
        "knowledge": ["build/agents/dora/knowledge/*",
                      _ADV + "iso22301-business-continuity.md",
                      _ADV + "cloud-ict-service-assurance.md",
                      _ADV + "gdpr-art28-sccs.md"] + _PACKS,
        "overlay": True,
    },
    "findings-remediation-register": {
        "model": REASONING_MODEL,
        "description": "Consolidated findings, remediation and risk-"
                       "acceptance register: every finding normalised with "
                       "severity, control reference, owner, due date, status "
                       "and closure evidence; every acceptance with an "
                       "expiry that reverts it to OPEN.",
        "knowledge": [_ADV + "iso27005-risk-management.md",
                      _ADV + "iso27002-control-attributes.md",
                      _ADV + "cis-controls-v8-1.md",
                      _ADV + "pentest-standards-owasp-ptes-cvss.md",
                      "governance/RISK_THRESHOLDS.md"] + _PACKS,
        "overlay": True,
    },
    "isms-audit-pack": {
        "model": REASONING_MODEL,
        "description": "ISO/IEC 27001:2022 governance packs for the third-"
                       "party scope: SoA extract, internal audit plan and "
                       "report (cl. 9.2), management review input pack "
                       "(cl. 9.3), and the audit evidence index.",
        "knowledge": [_ADV + "iso27002-control-attributes.md",
                      _ADV + "governance-frameworks-compendium.md",
                      _ADV + "iso27005-risk-management.md",
                      _ADV + "iso20000-service-management.md",
                      "build/agents/iso27001/knowledge/*"] + _PACKS,
        "overlay": True,
    },
    "regulatory-change-watch": {
        "model": REASONING_MODEL,
        "description": "Regulatory and standards horizon scanning with, per "
                       "change, the ENX applicability, the named platform "
                       "artefacts that must change, the gap assessment and "
                       "an action plan worked backwards from the application "
                       "date.",
        "knowledge": [_ADV + "governance-frameworks-compendium.md",
                      _ADV + "nist-csf-2-0.md",
                      "build/agents/eu-ai-act/knowledge/*",
                      "build/agents/dora/knowledge/*",
                      "build/agents/nis2/knowledge/*"] + _PACKS,
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
                                inference=params_for(name, spec["model"]),
                                existing=live.get(name))
        record_version(agent)
        print(f"{'updated' if name in live else 'created'}  {agent.ref} "
              f"({agent.id})")
    print("\nnext: `python3 create_agents.py --rewire` so the control-center "
          "ROUTE table covers these agents (deploy.sh step [4b])")
    return 0


if __name__ == "__main__":
    sys.exit(main())
