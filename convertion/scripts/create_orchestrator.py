#!/usr/bin/env python3
"""Create/update the flagship layer: infosec-assurance-advisor and
infosec-assurance-orchestrator (plus the durable memory vector store).

Run AFTER create_agents.py (and ideally attach_integrations.py).

- advisor: reasoning model + ONE combined knowledge vector store built
  from EVERY converted agent's knowledge files (build/agents/*/knowledge/*)
  + Bing web search (if configured). The service allows one vector store
  per agent (finding C3), so durable memory is NOT a second store: with
  MEMORY_BACKEND=search-index it is served from the Azure AI Search index
  MEMORY_INDEX_NAME through the GA Azure AI Search tool; with the
  transition default MEMORY_BACKEND=vector-store the notes store
  vs-assurance-memory is still created and managed by memory_store.py but
  is NOT attached to the advisor's file_search tool.
- orchestrator: reasoning model + web search + a deploy-time ROUTE table
  over every live agent. Connected agents do not exist on the new Agent
  Service (finding C2): the orchestrator answers `ROUTE: <agent-name>` and
  the caller (mcp-server, integrations/copilot, workflows/agent-fanout.json)
  performs the hand-off as a second responses.create on that agent. When
  ENABLE_A2A_TOOL=true and the pinned SDK exposes the A2A tool, the A2A
  tools are attached as well; otherwise the ROUTE table alone is used and
  the fallback is printed (documented in
  enterprise/series/06-agents-conversion-and-deploy.md §D).

Idempotent by name; on the GA runtime every run saves a new immutable
version recorded in build/agent-versions.json (finding C19).
--dry-run needs no Azure SDK.
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
# finding C4: NOT o3-mini - it carries none of the OpenAPI/MCP/AI Search/
# SharePoint/Web Search tools the reasoning agents need
REASONING_MODEL = os.environ.get("REASONING_MODEL_DEPLOYMENT_NAME", "o4-mini")
BING_CONNECTION = os.environ.get("BING_CONNECTION_NAME", "bing-grounding")
ENABLE_A2A = os.environ.get("ENABLE_A2A_TOOL", "false").strip().lower() == "true"

ADVISOR = "infosec-assurance-advisor"
ORCHESTRATOR = "infosec-assurance-orchestrator"
VERIFIER = "output-verifier"
MEMORY_STORE = "vs-assurance-memory"
KNOWLEDGE_STORE = "vs-assurance-combined"

ORCHESTRATOR_INSTRUCTIONS = """\
You are the single entry point for the InfoSec Assurance team's agent
environment. For each request, decide and act:

Hand-off protocol: you do not call other agents yourself. When a
specialist is needed, reply with the single line `ROUTE: <agent-name>`
(names exactly as in the ROUTING TABLE appended to these instructions) and
stop; the caller runs that agent and brings the answer back to you.

1. Broad or cross-framework advisory questions -> ROUTE:
   infosec-assurance-advisor (it holds the combined knowledge base and the
   team's durable memory).
2. Specialist pipeline work -> ROUTE to the matching specialist agent:
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
3. Multi-part requests -> decompose and emit one `ROUTE:` line per part in
   the order they must run; synthesise the returned parts into one
   coherent answer and state which agent produced which part.
4. Only answer directly when no specialist adds value; use web search for
   anything time-sensitive and cite sources.
5. Any deliverable or submission-of-record draft (report, executive
   summary, finding, ticket, Form B answer set) -> `ROUTE: output-verifier`
   BEFORE presenting it for human approval. On FAIL, route the findings
   back to the producing agent, get a corrected draft, and re-verify (at
   most twice; then surface the FAIL to the user).

Never fabricate a specialist's output; if a hand-off fails, say so and give
your best direct answer, clearly labelled as such.
"""

# Same mandatory gate the converter appends to every specialist agent.
sys.path.insert(0, str(HERE))
from convert_skills import APPROVAL_GATE, ALIASES  # noqa: E402
from _azure_helpers import (dedupe_tools, integration_tools,  # noqa: E402
                            kit_metadata, reconcile_store,
                            routing_table_block, tool_type)
from inference_profiles import params_for  # noqa: E402
from _foundry_runtime import (ai_search_tool, bing_grounding_tool,  # noqa: E402
                              get_runtime, knowledge_source, memory_backend,
                              record_version)


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

    ks, mem = knowledge_source(), memory_backend()
    if args.dry_run:
        print(f"[dry-run] {ADVISOR}: model={REASONING_MODEL}, "
              f"combined knowledge files={len(knowledge)}, "
              f"file_search store=[{KNOWLEDGE_STORE}] (ONE store per agent "
              f"— finding C3), memory backend={mem}"
              + (f" -> AI Search index {ks['memory_index']}"
                 if mem == "search-index" else
                 f" -> {MEMORY_STORE} (created, not attached)")
              + f", web-search + instructions {len(advisor_text)} chars "
                f"(integration tools preserved on update)")
        print(f"[dry-run] {VERIFIER}: model={REASONING_MODEL}, "
              f"deterministic PASS/FAIL rules, no tools, generates nothing")
        print(f"[dry-run] {ORCHESTRATOR}: model={REASONING_MODEL}, "
              f"web-search, ROUTE table over {len(allow)} manifest agents + "
              f"delivery agents + {ADVISOR} + {VERIFIER}; NOT routable: "
              f"{excluded or 'none'}; aliases: {ALIASES}; "
              f"A2A tool={'requested' if ENABLE_A2A else 'off'} "
              f"(no ConnectedAgentTool — finding C2)")
        assert not any(manifest[n].get("platform_specific") for n in allow), \
            "platform-specific agent would be routable"
        return 0

    if not ENDPOINT:
        sys.exit("Set PROJECT_ENDPOINT (setup/.env)")
    from azure.ai.agents.models import FileSearchTool
    rt = get_runtime(ENDPOINT)
    live = rt.list_agents()

    # Grounding with Bing needs the project connection's ID, not its name:
    # resolve BING_CONNECTION_NAME once and report a miss instead of
    # attaching a tool that would never ground (the residual-risk acceptance
    # for web grounding itself is finding C13, integrations/registry.json).
    bing_conn = rt.connection_id(BING_CONNECTION)
    if not bing_conn:
        print(f"note: project connection {BING_CONNECTION!r} not found — web "
              f"grounding NOT attached to {ADVISOR}/{ORCHESTRATOR}; create it "
              f"(infra/main.bicep, integrations/connections/) or set "
              f"BING_CONNECTION_NAME in setup/.env")

    # ---- advisor -----------------------------------------------------
    from _azure_helpers import UploadCache, upload_files
    kids = upload_files(rt, knowledge,
                        UploadCache(BUILD / "upload-cache.json"),
                        label="combined knowledge")
    kstore = ensure_store(rt, KNOWLEDGE_STORE, kids)

    tools, resources = [], {}
    # ONE vector store per agent (finding C3): the combined knowledge base.
    fs = FileSearchTool(vector_store_ids=[kstore.id])
    tools += fs.definitions
    resources.update(fs.resources)

    # Durable memory: an Azure AI Search index, or the transition notes
    # store which memory_store.py still manages but which is NOT attached
    # as a second file_search store (the service refuses two).
    if mem == "search-index":
        conn = rt.connection_id(ks["connection"])
        defs = ai_search_tool(conn, ks["memory_index"]) if conn else []
        if defs:
            tools += defs
            print(f"  memory: Azure AI Search index {ks['memory_index']} "
                  f"via connection {ks['connection']}")
        else:
            print(f"note: MEMORY_BACKEND=search-index but connection "
                  f"{ks['connection']!r} or the AI Search tool is "
                  f"unavailable — memory not attached; falling back to "
                  f"MEMORY_BACKEND=vector-store semantics "
                  f"(enterprise/MEMORY_AND_LEARNING.md §2)")
            ensure_store(rt, MEMORY_STORE, [])
    else:
        ensure_store(rt, MEMORY_STORE, [])
        print(f"  memory: {MEMORY_STORE} kept for memory_store.py, not "
              f"attached (one vector store per agent — finding C3)")

    if ADVISOR in live:
        # keep what attach_integrations.py attached (OpenAPI/MCP/Bing/Search)
        tools += integration_tools(live[ADVISOR])
    if not any(tool_type(t) == "bing_grounding" for t in tools):
        tools += bing_grounding_tool(bing_conn)
    # integration_tools() + the definitions built here can overlap on a re-run
    tools = dedupe_tools(tools, label=ADVISOR)

    had_advisor = ADVISOR in live
    advisor = rt.upsert_agent(
        model=REASONING_MODEL, name=ADVISOR,
        description="Senior reasoning advisor across all InfoSec "
                    "Assurance domains, grounded in the combined "
                    "knowledge base with durable team memory.",
        instructions=advisor_text,
        tools=tools, tool_resources=resources,
        metadata=kit_metadata(),
        inference=params_for(ADVISOR, REASONING_MODEL),
        existing=live.get(ADVISOR))
    record_version(advisor)
    print(f"{'updated' if had_advisor else 'created'}  {advisor.ref} "
          f"({advisor.id})")
    live[ADVISOR] = advisor

    # ---- output-verifier (verifier-gated pattern) ---------------------
    had_verifier = VERIFIER in live
    verifier = rt.upsert_agent(
        model=REASONING_MODEL, name=VERIFIER, metadata=kit_metadata(),
        description="Independent verification layer: checks every "
                    "deliverable draft against deterministic rules "
                    "(completeness, threshold consistency, grounding, no "
                    "placeholders, data minimisation) and returns "
                    "PASS/FAIL before human approval. Generates nothing.",
        instructions=verifier_instructions(),
        inference=params_for(VERIFIER, REASONING_MODEL),
        existing=live.get(VERIFIER))
    record_version(verifier)
    print(f"{'updated' if had_verifier else 'created'}  {verifier.ref} "
          f"({verifier.id})")
    live[VERIFIER] = verifier

    # ---- orchestrator ------------------------------------------------
    otools = list(bing_grounding_tool(bing_conn))
    if ORCHESTRATOR in live:
        otools += integration_tools(live[ORCHESTRATOR])
    alias_notes: dict[str, list[str]] = {}
    for alias, target in ALIASES.items():
        alias_notes.setdefault(target, []).append(alias)
    rows: list[tuple[str, str]] = []
    for name, agent in sorted(live.items()):
        if name == ORCHESTRATOR or (name in manifest and name not in allow):
            continue                      # platform-specific / alias twins
        desc = (agent.description or f"Specialist agent {name}")
        for alias in alias_notes.get(name, []):
            desc += f" Also answers requests phrased for '{alias}'."
        rows.append((name, desc))

    # Connected agents were removed from the Agent Service (finding C2).
    # Primary: the ROUTE table below (deterministic, traceable, read-only).
    # Optional: the A2A tool when ENABLE_A2A_TOOL=true and the pinned SDK
    # (setup/requirements.txt) exposes it; the fallback is the table alone.
    if ENABLE_A2A:
        try:
            from azure.ai.agents.models import A2ATool
            for name, _ in rows:
                otools += A2ATool(agent_name=name).definitions
            print(f"  A2A tool attached for {len(rows)} agents (preview)")
        except (ImportError, AttributeError, TypeError, ValueError) as e:
            print(f"note: ENABLE_A2A_TOOL=true but this SDK has no A2A tool "
                  f"({type(e).__name__}) — using the ROUTE table only "
                  f"(enterprise/series/06-agents-conversion-and-deploy.md §D)")

    had_orch = ORCHESTRATOR in live
    orchestrator = rt.upsert_agent(
        model=REASONING_MODEL, name=ORCHESTRATOR,
        description="Entry point: routes and decomposes InfoSec "
                    "Assurance requests across all agents.",
        instructions=orchestrator_instructions() + routing_table_block(rows),
        tools=dedupe_tools(otools, label=ORCHESTRATOR), metadata=kit_metadata(),
        inference=params_for(ORCHESTRATOR, REASONING_MODEL),
        existing=live.get(ORCHESTRATOR))
    record_version(orchestrator, note="routing table")
    print(f"{'updated' if had_orch else 'created'}  {orchestrator.ref} "
          f"-> ROUTE table over {len(rows)} agents")
    return 0


if __name__ == "__main__":
    sys.exit(main())
