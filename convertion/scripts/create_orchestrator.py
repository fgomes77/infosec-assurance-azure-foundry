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
VERIFIER = "output-verifier"
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
   (pdf_full_coverage_analyzer), TPRM scoring (tpsrca_assessment_engine),
   SOC 1/2/3 report summaries (soc_report_analyzer), penetration-test
   summaries (pentest_report_analyzer), SharePoint TPA evidence-tree
   analysis (tpa_evidence_analyzer), the Global CISO 9-slide deck
   (ciso_global_report), board slide (tprm_slide_generator), template
   changes (template_manager), transcript post-processing
   (whisperx_transcribe_diarize), read-only enterprise look-ups
   (enterprise_explorer). NIST CSF 2.0, CIS v8.1, ISO 27005, ISO 27002
   attributes, GDPR Art. 28/SCCs, ITIL/COBIT/COSO/TOGAF/PMBOK/ISO 20000,
   cloud and SOC/pentest evidence methodology -> infosec_assurance_advisor.
3. Multi-part requests -> decompose, call several agents, and synthesise
   one coherent answer; state which agent produced which part.
4. Only answer directly when no specialist adds value; use web search for
   anything time-sensitive and cite sources.
5. Any deliverable or submission-of-record draft (report, executive
   summary, finding, ticket, Form B answer set) -> pass it through
   output_verifier BEFORE presenting it for human approval. On FAIL, send
   the findings back to the producing agent, get a corrected draft, and
   re-verify (at most twice; then surface the FAIL to the user).

Never fabricate a specialist's output; if a handoff fails, say so and give
your best direct answer, clearly labelled as such.
"""

# Same mandatory gate the converter appends to every specialist agent.
sys.path.insert(0, str(HERE))
from convert_skills import APPROVAL_GATE, ALIASES  # noqa: E402
from _azure_helpers import (integration_tools, kit_metadata,  # noqa: E402
                            reconcile_store)


def persona() -> str:
    text = (CONV / "agents" / "persona_system_prompt.md").read_text(encoding="utf-8")
    return text.split("---", 2)[-1].strip()


def _charter(name: str) -> str:
    return (CONV / "agents" / name).read_text(encoding="utf-8").strip()


def advisor_instructions() -> str:
    return (persona() + "\n\n---\n\n" + _charter("advisor_instructions.md")
            + "\n\n---\n\n" + _charter("overlays/research-pattern.md")
            + APPROVAL_GATE)


def verifier_instructions() -> str:
    return persona() + "\n\n---\n\n" + _charter("verifier_instructions.md")


def orchestrator_instructions() -> str:
    # built-in routing + the routing charter (pipelines, intake, menu rules)
    return (persona() + "\n\n---\n\n" + ORCHESTRATOR_INSTRUCTIONS
            + "\n\n---\n\n" + _charter("orchestrator_instructions.md")
            + APPROVAL_GATE)


def connectable(manifest: dict) -> set[str]:
    """Agents the orchestrator may connect to: everything live EXCEPT
    platform-specific example agents and alias twins (routing noise and
    injection surface - integrations/registry.json example_agents)."""
    return {n for n, a in manifest.items()
            if not a.get("platform_specific") and not a.get("alias_of")}


def load_manifest() -> dict:
    try:
        return {a["name"]: a for a in json.loads(
            (BUILD / "manifest.json").read_text())["agents"]}
    except (OSError, json.JSONDecodeError):
        return {}


def gather_knowledge_files() -> list[Path]:
    # every converted skill's knowledge + the advisor knowledge pack, which
    # grounds the persona domains the skill export does not cover (ISO 27005,
    # NIST CSF 2.0, CIS v8.1, GDPR Art. 28/SCCs, management frameworks) +
    # the environment knowledge packs (platform self-knowledge, file intake)
    files = sorted(BUILD.glob("agents/*/knowledge/*")) + \
        sorted((CONV / "agents" / "advisor-knowledge").glob("*.md")) + \
        sorted((CONV / "agents" / "knowledge-packs").glob("*.md"))
    # de-duplicate identical content (slide-generator twins, shared__/pack__
    # copies of the SSOT and knowledge packs) by digest
    import hashlib
    seen, out = set(), []
    for f in files:
        key = hashlib.sha256(f.read_bytes()).hexdigest()
        if key not in seen:
            seen.add(key)
            out.append(f)
    return out


def ensure_store(agents_client, name: str, file_ids: list[str]):
    """Store called `name` holding exactly file_ids (re-runs refresh it, so
    an approved template propagates - requirement j)."""
    return reconcile_store(agents_client, name, file_ids)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    knowledge = gather_knowledge_files()
    advisor_text = advisor_instructions()
    manifest = load_manifest()
    allow = connectable(manifest)
    excluded = sorted(set(manifest) - allow)

    if args.dry_run:
        print(f"[dry-run] {ADVISOR}: model={REASONING_MODEL}, "
              f"combined knowledge files={len(knowledge)}, "
              f"stores=[{KNOWLEDGE_STORE}, {MEMORY_STORE}], web-search + "
              f"instructions {len(advisor_text)} chars (integration tools "
              f"preserved on update)")
        print(f"[dry-run] {VERIFIER}: model={REASONING_MODEL}, "
              f"deterministic PASS/FAIL rules, no tools, generates nothing")
        print(f"[dry-run] {ORCHESTRATOR}: model={REASONING_MODEL}, "
              f"web-search, connected to {len(allow)} manifest agents + "
              f"delivery agents + {ADVISOR} + {VERIFIER}; NOT connected: "
              f"{excluded or 'none'}; aliases: {ALIASES}")
        assert not any(manifest[n].get("platform_specific") for n in allow), \
            "platform-specific agent would be connected"
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
    from _azure_helpers import UploadCache, upload_files
    kids = upload_files(agents_client, knowledge,
                        UploadCache(BUILD / "upload-cache.json"),
                        label="combined knowledge")
    kstore = ensure_store(agents_client, KNOWLEDGE_STORE, kids)
    mstore = ensure_store(agents_client, MEMORY_STORE, [])

    tools, resources = [], {}
    fs = FileSearchTool(vector_store_ids=[kstore.id, mstore.id])
    tools += fs.definitions
    resources.update(fs.resources)
    if ADVISOR in live:
        # keep what attach_integrations.py attached (OpenAPI/MCP/Bing)
        tools += integration_tools(live[ADVISOR])
    if not any(getattr(t, "type", "") == "bing_grounding" for t in tools):
        try:
            tools += BingGroundingTool(connection_id=BING_CONNECTION).definitions
        except Exception:
            print("note: Bing grounding not attached (connection missing?)")

    kwargs = dict(model=REASONING_MODEL, name=ADVISOR,
                  description="Senior reasoning advisor across all InfoSec "
                              "Assurance domains, grounded in the combined "
                              "knowledge base with durable team memory.",
                  instructions=advisor_text,
                  tools=tools, tool_resources=resources,
                  metadata=kit_metadata())
    advisor = (agents_client.update_agent(live[ADVISOR].id, **kwargs)
               if ADVISOR in live else agents_client.create_agent(**kwargs))
    print(f"{'updated' if ADVISOR in live else 'created'}  {ADVISOR} ({advisor.id})")
    live[ADVISOR] = advisor

    # ---- output-verifier (verifier-gated pattern) ---------------------
    vkwargs = dict(model=REASONING_MODEL, name=VERIFIER,
                   metadata=kit_metadata(),
                   description="Independent verification layer: checks every "
                               "deliverable draft against deterministic rules "
                               "(completeness, threshold consistency, "
                               "grounding, no placeholders, data "
                               "minimisation) and returns PASS/FAIL before "
                               "human approval. Generates nothing.",
                   instructions=verifier_instructions())
    verifier = (agents_client.update_agent(live[VERIFIER].id, **vkwargs)
                if VERIFIER in live else agents_client.create_agent(**vkwargs))
    print(f"{'updated' if VERIFIER in live else 'created'}  {VERIFIER} ({verifier.id})")
    live[VERIFIER] = verifier

    # ---- orchestrator ------------------------------------------------
    otools = []
    try:
        otools += BingGroundingTool(connection_id=BING_CONNECTION).definitions
    except Exception:
        pass
    alias_notes: dict[str, list[str]] = {}
    for alias, target in ALIASES.items():
        alias_notes.setdefault(target, []).append(alias)
    connected = []
    for name, agent in sorted(live.items()):
        if name == ORCHESTRATOR or (name in manifest and name not in allow):
            continue                      # platform-specific / alias twins
        desc = (agent.description or f"Specialist agent {name}")
        for alias in alias_notes.get(name, []):
            desc += f" Also answers requests phrased for '{alias}'."
        otools += ConnectedAgentTool(
            id=agent.id, name=name.replace("-", "_"),
            description=desc[:512],
        ).definitions
        connected.append(name)

    okwargs = dict(model=REASONING_MODEL, name=ORCHESTRATOR,
                   description="Entry point: routes and decomposes InfoSec "
                               "Assurance requests across all agents.",
                   instructions=orchestrator_instructions(),
                   tools=otools, metadata=kit_metadata())
    if ORCHESTRATOR in live:
        agents_client.update_agent(live[ORCHESTRATOR].id, **okwargs)
        print(f"updated  {ORCHESTRATOR} -> {len(connected)} connected agents")
    else:
        agents_client.create_agent(**okwargs)
        print(f"created  {ORCHESTRATOR} -> {len(connected)} connected agents")
    return 0


if __name__ == "__main__":
    sys.exit(main())
