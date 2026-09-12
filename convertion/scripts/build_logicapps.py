#!/usr/bin/env python3
"""Derive the deployable Logic App definitions (workflows/README.md
"Deployment note"): one instance of workflows/report-delivery-pipeline.json
per entry of workflows/pipelines.json, plus every standalone workflow file,
into build/logicapps/<name>/workflow.json.

Substitutions (never hand-edited):
  - pipelines.json keys -> parameter defaultValue of the same meaning
    (agent -> agentId, libraryRoot -> libraryRootItemId, ...)
  - agent NAMES -> live Foundry agent ids (read-only list_agents), or from
    --agents-json {name: id} for offline/CI builds
  - ${ENV_VAR} placeholders in pipelines.json "shared" -> environment
    (setup/.env); unresolved ones are left as-is and reported.

    python3 build_logicapps.py [--agents-json ids.json] [--dry-run]

ci/deploy_logicapps.sh (or `az logicapp deployment source config-zip`)
ships the folder; secrets stay @Microsoft.KeyVault(...) app settings.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONV = HERE.parent
WF = CONV / "workflows"
OUT = CONV / "build" / "logicapps"
try:
    from dotenv import load_dotenv
    load_dotenv(CONV / "setup" / ".env")
except ImportError:
    pass

KEY_MAP = {"agent": "agentId", "libraryRoot": "libraryRootItemId"}
SHARED_MAP = {"verifierAgent": "verifierAgentId", "sharepointDrive": "sharepointDriveId",
              "apiVersion": "apiVersion"}
ENV_RE = re.compile(r"\$\{([A-Z0-9_]+)\}")


def resolve_env(value, unresolved: set[str]):
    if isinstance(value, str):
        def sub(m):
            v = os.environ.get(m.group(1))
            if v is None:
                unresolved.add(m.group(1))
                return m.group(0)
            return v
        return ENV_RE.sub(sub, value)
    return value


def agent_ids(args) -> dict[str, str]:
    if args.agents_json:
        return json.loads(Path(args.agents_json).read_text(encoding="utf-8"))
    if args.dry_run:
        return {}
    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential
    endpoint = os.environ.get("PROJECT_ENDPOINT") or sys.exit("Set PROJECT_ENDPOINT")
    ac = AIProjectClient(endpoint=endpoint, credential=DefaultAzureCredential()).agents
    return {a.name: a.id for a in ac.list_agents()}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--agents-json", help="{name: id} map instead of the live listing")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    pipes = json.loads((WF / "pipelines.json").read_text(encoding="utf-8"))
    template = json.loads((WF / "report-delivery-pipeline.json").read_text(encoding="utf-8"))
    ids = agent_ids(args)
    unresolved: set[str] = set()
    missing_agents: set[str] = set()
    raw_shared = {k: resolve_env(v, unresolved)
                  for k, v in pipes.get("shared", {}).items() if not k.startswith("_")}
    # only SHARED_MAP keys are workflow parameters; the *Root keys are the
    # lookup table for libraryRoot
    shared = {SHARED_MAP[k]: v for k, v in raw_shared.items() if k in SHARED_MAP}
    if "verifierAgentId" in shared:
        name = shared["verifierAgentId"]
        shared["verifierAgentId"] = ids.get(name, f"{{agentId:{name}}}")
        if name not in ids:
            missing_agents.add(name)

    written = []
    for name, cfg in pipes["pipelines"].items():
        wf = copy.deepcopy(template)
        params = wf["definition"]["parameters"]
        values = dict(shared)
        for k, v in cfg.items():
            if k.startswith("_") or k in ("requirement", "notes"):
                continue
            key = KEY_MAP.get(k, k)
            if k == "agent":
                if v == "TRIGGER":
                    v = ""                       # caller passes agentId
                else:
                    if v not in ids:
                        missing_agents.add(v)
                    v = ids.get(v, f"{{agentId:{v}}}")
            elif k == "libraryRoot":
                v = raw_shared.get(v, v)
            values[key] = v
        for key, v in values.items():
            if key in params:
                params[key]["defaultValue"] = v
            else:
                print(f"note: {name}: parameter {key!r} not in the template - skipped")
        wf["_generated"] = {"from": "workflows/report-delivery-pipeline.json",
                            "pipeline": name}
        dest = OUT / name / "workflow.json"
        if not args.dry_run:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(json.dumps(wf, indent=2) + "\n", encoding="utf-8")
        written.append(name)

    for f in sorted(WF.glob("*.json")):
        if f.name in ("pipelines.json", "report-delivery-pipeline.json"):
            continue
        wf = json.loads(resolve_env(f.read_text(encoding="utf-8"), unresolved))
        dest = OUT / f.stem / "workflow.json"
        if not args.dry_run:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(json.dumps(wf, indent=2) + "\n", encoding="utf-8")
        written.append(f.stem)

    print(f"{'[dry-run] ' if args.dry_run else ''}{len(written)} workflow "
          f"definitions -> {OUT}")
    if missing_agents:
        print(f"note: agent ids left as placeholders (not deployed / offline): "
              f"{sorted(missing_agents)}")
    if unresolved:
        print(f"note: unresolved environment placeholders: {sorted(unresolved)} "
              f"(setup/.env)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
