#!/usr/bin/env python3
"""Split the TPSRCA 12-agent methodology into real published sub-agents.

`agents/overlays/tpsrca-assessment-engine.md` says the 12 "agents" of the
skill are roles inside one agent **unless the deployment published
`tpsrca_calc` / `tpsrca_analysis` / `tpsrca_report` as separate agents
reached by an A2A / ROUTE hand-off (optional split)**. This script performs
that split, and it is the only supported way to do it:

    tpsrca-calc       roles 4-8   inherent risk, control effectiveness,
                                  residual risk, framework compliance,
                                  composite score. Carries the SAME
                                  `calculation_engine.py` package, so the
                                  numbers stay deterministic and identical
                                  to the single-agent path.
    tpsrca-analysis   roles 2,3,9-11  data confidence, evidence validation,
                                  gap register, trend, recommendations.
    tpsrca-report     role 12     assembles the TPSRCA report from the two
                                  above; never recomputes a score.

Role 1 (Assessment Orchestrator) is NOT split out: `tpsrca-assessment-engine`
keeps it and becomes the coordinator that ROUTEs to the three sub-agents.

Every charter section is taken VERBATIM out of the byte-verified build
(`build/agents/tpsrca-assessment-engine/instructions.md`) — nothing is
paraphrased, so a sub-agent scores exactly as the parent does. Knowledge and
the code package are the parent's, re-used by content hash through the
shared upload cache.

Idempotent by name: on the GA runtime each run saves a new immutable version
`<name>:<n>` recorded in build/agent-versions.json (finding C19); on the
classic fallback runtime the agent is updated in place. Re-running with no
kit change re-saves the same definition and nothing else.

    python3 create_tpsrca_subagents.py --dry-run     # offline, no Azure SDK
    python3 create_tpsrca_subagents.py --only tpsrca-calc
    python3 create_tpsrca_subagents.py               # create/update all three

GOVERNANCE: these are live agents, so each one needs an entry in
`integrations/registry.json` (tools + model tier + guardrail policy) before
it is deployed — `attach_integrations.py` FAILS on any live agent without
one, by design. This script refuses to deploy an unregistered sub-agent
unless `--allow-unregistered` is given (a dev project only).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONV = HERE.parent
BUILD = CONV / "build"
PARENT = "tpsrca-assessment-engine"
PARENT_DIR = BUILD / "agents" / PARENT

try:
    from dotenv import load_dotenv
    load_dotenv(CONV / "setup" / ".env")
except ImportError:
    pass

ENDPOINT = os.environ.get("PROJECT_ENDPOINT")
CHAT_MODEL = os.environ.get("MODEL_DEPLOYMENT_NAME", "gpt-4o")
# finding C4: a reasoning tier model must still carry the tools
REASONING_MODEL = os.environ.get("REASONING_MODEL_DEPLOYMENT_NAME", "o4-mini")

sys.path.insert(0, str(HERE))
from create_orchestrator import persona  # noqa: E402
from convert_skills import APPROVAL_GATE  # noqa: E402
from _azure_helpers import (dedupe_tools, file_map_block,  # noqa: E402
                            integration_tools, kit_metadata)
from _foundry_runtime import get_runtime, record_version  # noqa: E402

# Sections every sub-agent needs from the parent charter (environment rules,
# tool-name translation) - kept verbatim so the three agents cannot drift.
COMMON_SECTIONS = ("Tool-name translation", "Fixed rules of this environment")

SUBAGENTS: dict[str, dict] = {
    "tpsrca-calc": {
        "roles": [4, 5, 6, 7, 8],
        "model": REASONING_MODEL,
        "sections": ("Calculation Reference Card", "CODE PACKAGE (this environment)"),
        "code": True,
        "description": "TPSRCA deterministic scoring (roles 4-8): inherent "
                       "risk, control effectiveness, residual risk, framework "
                       "compliance and composite score, computed with "
                       "calculation_engine.py. Returns scores as JSON; never "
                       "estimates a score in prose.",
        "preamble": (
            "You are the TPSRCA **calculation** sub-agent (roles 4-8 of the "
            "12-role methodology). `tpsrca-assessment-engine` coordinates the "
            "assessment and hands you the collected data; you return the "
            "scores.\n\n"
            "- Input: the assessment JSON produced by the coordinator "
            "(supplier type, scope, `osint_data`, control evidence).\n"
            "- Run `calculation_engine.py` from your `code_interpreter` "
            "package for EVERY number. It is the single deterministic scorer: "
            "never compute or estimate a score in prose, and never round a "
            "value it produced.\n"
            "- Output: the score object of the methodology (inherent, control "
            "effectiveness factor, residual, per-framework compliance, "
            "composite + rating) plus the inputs each number used.\n"
            "- You do not write findings, recommendations or the report; "
            "return to the coordinator when the scores are complete."),
    },
    "tpsrca-analysis": {
        "roles": [2, 3, 9, 10, 11],
        "model": REASONING_MODEL,
        "sections": (),
        "code": False,
        "description": "TPSRCA analysis (roles 2, 3, 9-11): data confidence, "
                       "evidence validation, gap register, trend comparison "
                       "and prioritised recommendations over the scores "
                       "produced by tpsrca-calc.",
        "preamble": (
            "You are the TPSRCA **analysis** sub-agent (roles 2, 3, 9, 10 and "
            "11 of the 12-role methodology). `tpsrca-assessment-engine` "
            "coordinates the assessment; `tpsrca-calc` owns every number.\n\n"
            "- Input: the collected data and the score object from "
            "`tpsrca-calc`.\n"
            "- Validate data confidence and evidence BEFORE interpreting "
            "anything, and carry the confidence rating into every conclusion "
            "you draw. An unverifiable source is reported as unverified — "
            "never silently defaulted.\n"
            "- Never recompute or adjust a score: if a number looks wrong, say "
            "so and return it to the coordinator for a re-run of "
            "`tpsrca-calc`.\n"
            "- Output: gap register, trend indicators and the prioritised "
            "action plan, each item traceable to the evidence that supports it."),
    },
    "tpsrca-report": {
        "roles": [12],
        "model": CHAT_MODEL,
        "sections": (),
        "code": False,
        "description": "TPSRCA report generation (role 12): assembles the "
                       "assessment output from the scores and the analysis, "
                       "in the methodology's schema. Recomputes nothing.",
        "preamble": (
            "You are the TPSRCA **report** sub-agent (role 12 of the 12-role "
            "methodology).\n\n"
            "- Input: the score object from `tpsrca-calc` and the analysis "
            "from `tpsrca-analysis`, passed by "
            "`tpsrca-assessment-engine`.\n"
            "- Assemble the assessment output exactly per "
            "`references__output_schema.json` in your knowledge store. Every "
            "value is copied from the inputs — you recompute nothing, and you "
            "never fill a missing value with an estimate: mark it as missing "
            "and name the role that must supply it.\n"
            "- State the data-confidence rating and the supplier type/scope "
            "the assessment used, so the reader can judge the result.\n"
            "- The deliverable goes to the coordinator, then to "
            "`output-verifier` and human approval before it is stored."),
    },
}

HANDOFF_NOTE = """

## THIS DEPLOYMENT SPLIT THE 12 ROLES (overlay: optional split)

`tpsrca-assessment-engine` is the coordinator (role 1) and the three
sub-agents `tpsrca-calc`, `tpsrca-analysis` and `tpsrca-report` are
separately published agents. You are ONE of them: perform only the roles
listed in your preamble. Hand work back by returning your output to the
coordinator — reply with the single line `ROUTE: <agent-name>` when a role
outside yours is needed and stop; the caller performs the hand-off (there
are no connected agents on this runtime, finding C2).
"""


# ------------------------------------------------------------- charter slicing
def parent_charter() -> str:
    path = PARENT_DIR / "instructions.md"
    if not path.is_file():
        sys.exit(f"missing {path} — run convert_skills.py first (the sub-agent "
                 f"charters are sliced out of the byte-verified build)")
    return path.read_text(encoding="utf-8")


def _slice(text: str, start: int) -> str:
    """From a heading offset to the next top-level `## ` heading."""
    nxt = text.find("\n## ", start + 1)
    return text[start:len(text) if nxt < 0 else nxt].rstrip() + "\n"


def role_section(text: str, role: int) -> str:
    m = re.search(rf"^## Agent {role}: .*$", text, re.MULTILINE)
    if not m:
        sys.exit(f"role {role} not found in {PARENT}/instructions.md — the "
                 f"export changed; re-check the 12-role table before splitting")
    # `## Agent N:` sections contain their own sub-headings (e.g. the
    # recommendation template), so the slice runs to the NEXT role heading or
    # to the first section that is not part of a role.
    body = _slice_role(text, m.start())
    return body.replace(f"## Agent {role}:", f"## Role {role} —", 1)


def _slice_role(text: str, start: int) -> str:
    nxt = re.search(r"^## (Agent \d+:|Calculation Reference Card|"
                    r"Tool-name translation|Fixed rules of this environment|"
                    r"CODE PACKAGE|APPROVAL GATE)", text[start + 1:], re.MULTILINE)
    end = len(text) if not nxt else start + 1 + nxt.start()
    return text[start:end].rstrip() + "\n"


def named_section(text: str, heading: str) -> str:
    m = re.search(rf"^## {re.escape(heading)}\s*$", text, re.MULTILINE)
    if not m:
        sys.exit(f"section {heading!r} not found in {PARENT}/instructions.md")
    return _slice(text, m.start())


def build_instructions(name: str) -> str:
    """persona + role preamble + the parent's verbatim role sections + the
    environment sections + the gate. Importable so a verifier can hash it
    offline."""
    spec = SUBAGENTS[name]
    charter = parent_charter()
    parts = [persona(), spec["preamble"].strip()]
    parts += [role_section(charter, r).strip() for r in spec["roles"]]
    parts += [named_section(charter, h).strip() for h in spec["sections"]]
    parts += [named_section(charter, h).strip() for h in COMMON_SECTIONS]
    return ("\n\n---\n\n".join(parts) + HANDOFF_NOTE + APPROVAL_GATE)


def knowledge_files(name: str) -> list[Path]:
    """The parent's knowledge store, minus the packs a role cannot use."""
    files = sorted(p for p in (PARENT_DIR / "knowledge").glob("*") if p.is_file())
    if name == "tpsrca-calc":
        # the calculator needs the methodology and the schema, not the
        # HTML/writing-style packs (smaller store, same numbers)
        files = [p for p in files if not p.name.startswith(
            ("pack__enx-html", "pack__enx-writing"))]
    return files


def code_files(name: str) -> list[Path]:
    if not SUBAGENTS[name]["code"]:
        return []
    return sorted(p for p in (PARENT_DIR / "code").glob("*.zip") if p.is_file())


# -------------------------------------------------------------------- registry
def registry_gaps(names: list[str]) -> list[str]:
    reg = json.loads((CONV / "integrations" / "registry.json").read_text(
        encoding="utf-8"))
    known = set(reg.get("agents", {})) | set(
        reg.get("example_agents", {}).get("unmanaged_ok", []))
    return [n for n in names if n not in known]


# ------------------------------------------------------------------------ main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", help="single sub-agent name")
    ap.add_argument("--allow-unregistered", action="store_true",
                    help="deploy even though integrations/registry.json has no "
                         "entry for a sub-agent (dev projects only)")
    args = ap.parse_args()

    todo = {k: v for k, v in SUBAGENTS.items() if not args.only or k == args.only}
    if not todo:
        sys.exit(f"unknown sub-agent {args.only!r} "
                 f"(choose from {', '.join(SUBAGENTS)})")

    plans = {n: (s, build_instructions(n), knowledge_files(n), code_files(n))
             for n, s in todo.items()}
    gaps = registry_gaps(list(todo))

    if args.dry_run:
        for name, (spec, instructions, know, code) in plans.items():
            print(f"[dry-run] {name}: roles {spec['roles']}, "
                  f"model={spec['model']}, knowledge files={len(know)}, "
                  f"code files={len(code)}, instructions "
                  f"{len(instructions)} chars")
        print(f"[dry-run] coordinator {PARENT} keeps role 1 and ROUTEs to "
              f"{', '.join(todo)}")
        if gaps:
            print(f"[dry-run] registry: NO entry for {gaps} — add them to "
                  f"integrations/registry.json (tools, model_tier, "
                  f"guardrail_policy) before deploying, or "
                  f"attach_integrations.py will fail the deploy")
        return 0

    if gaps and not args.allow_unregistered:
        print(f"FAIL: integrations/registry.json has no entry for {gaps}.\n"
              f"An unregistered live agent is an ungoverned tool surface "
              f"(registry _comment); add the entries — tools, model_tier "
              f"matching this script, guardrail_policy 'infosec-web-facing' "
              f"for any role that reads untrusted content — or re-run with "
              f"--allow-unregistered on a dev project.")
        return 1
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
            kids = upload_files(rt, know, cache, label=f"{name} knowledge")
            store = ensure_store(rt, f"vs-{name}", kids)
            fs = FileSearchTool(vector_store_ids=[store.id])
            tools += fs.definitions
            resources.update(fs.resources)
        if code:
            cids = upload_files(rt, code, cache, label=f"{name} code")
            ci = CodeInterpreterTool(file_ids=cids)
            tools += ci.definitions
            resources.update(ci.resources)
            instructions += file_map_block(list(zip([c.name for c in code], cids)))
        if name in live:
            tools += integration_tools(live[name])   # keep attach_integrations work
        tools = dedupe_tools(tools, label=name)

        agent = rt.upsert_agent(name=name, model=spec["model"],
                                description=spec["description"][:512],
                                instructions=instructions,
                                tools=tools, tool_resources=resources,
                                metadata=kit_metadata(), existing=live.get(name))
        record_version(agent, note="tpsrca split")
        print(f"{'updated' if name in live else 'created'}  {agent.ref} "
              f"({agent.id}) — roles {spec['roles']}")

    print(f"\ndone: {len(plans)} sub-agents. Re-run create_orchestrator.py so "
          f"the ROUTE table covers them, and attach_integrations.py for their "
          f"tools.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
