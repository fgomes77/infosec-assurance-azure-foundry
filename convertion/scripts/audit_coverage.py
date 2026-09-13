#!/usr/bin/env python3
"""Cross-artefact coverage audit — the checks no single file can make.

Every other gate verifies one artefact against its own rules: the residency
gate reads Bicep, the profile gate reads the profile registry, verify_kit
parses and cross-references. Nothing checked that the artefacts agree with
EACH OTHER — that every skill in the export has a recorded decision, that a
pipeline's agent is registered, that a declared toolset is the toolset the
agents actually carry, that a template has a sample to regress against.

Those disagreements are what rot looks like in a kit this size: nothing is
broken, every file is internally consistent, and the platform quietly stops
matching its own description. This script is the gate for that class.

    python3 audit_coverage.py            # report, exit 1 on a finding
    python3 audit_coverage.py --list     # report everything, exit 0

Offline and deterministic: no Azure call, no credentials.
"""

from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONV = HERE.parent
EXPORT = CONV.parent / "claude-account-export"


def _json(rel: str):
    return json.loads((CONV / rel).read_text(encoding="utf-8"))


def audit() -> list[tuple[str, str]]:
    """Return [(check, finding)] — empty means the artefacts agree."""
    findings: list[tuple[str, str]] = []
    reg = _json("integrations/registry.json")
    prof = _json("integrations/inference-profiles.json")
    pipes = _json("workflows/pipelines.json")["pipelines"]
    treg = _json("templates/registry.json")["templates"]
    dec = _json("templates/skill-decisions.json")

    # 1. Every skill in the export has a recorded decision, wherever it lives.
    decided = {d["skill"] for d in dec["decisions"]}
    decided |= {d["skill"] for d in dec.get("harness_skills", [])}
    for folder in ("skills", "platform-skills/public", "platform-skills/examples",
                   "local-skills"):
        src = EXPORT / folder
        if not src.is_dir():
            continue
        for path in sorted(p for p in src.iterdir() if p.is_dir()):
            if path.name not in decided:
                findings.append((
                    "skill-decisions",
                    f"{folder}/{path.name} has no recorded decision — every "
                    f"exported skill is a deliberate AGENT / KNOWLEDGE-PACK / "
                    f"SUPERSEDED / EXCLUDED call (PLATFORM_SKILLS_DECISION.md)"))

    # 2. A declared toolset is the toolset the agents carry. A promise the
    #    deployment does not keep is worse than no promise: it is read as
    #    access that exists.
    adv = reg.get("advisory_read_only_toolset", {})
    core = adv.get("core") or adv.get("tools") or []
    for name in adv.get("agents", []):
        have = set(reg["agents"].get(name, {}).get("tools", []))
        gap = [t for t in core if t not in have]
        if gap:
            findings.append((
                "advisory-toolset",
                f"{name} is listed as an advisory system but does not carry "
                f"{', '.join(gap)} — either attach it or correct the declaration"))
    for name, tools in (adv.get("supplier_facing") or {}).items():
        have = set(reg["agents"].get(name, {}).get("tools", []))
        gap = [t for t in tools if t not in have]
        if gap:
            findings.append((
                "advisory-toolset",
                f"{name} is declared supplier-facing but does not carry "
                f"{', '.join(gap)}"))

    # 3. Every pipeline names an agent that exists.
    for pid, cfg in sorted(pipes.items()):
        agent = cfg.get("agent")
        if agent and agent != "TRIGGER" and agent not in reg["agents"]:
            findings.append(("pipelines",
                             f"{pid} routes to unregistered agent {agent!r}"))

    # 4. Every registered agent is classed, guarded and reachable.
    for name, cfg in sorted(reg["agents"].items()):
        if name not in prof["agent_class"]:
            findings.append(("profiles", f"{name} has no inference-profile class"))
        if not cfg.get("guardrail_policy"):
            findings.append(("guardrails", f"{name} has no guardrail_policy"))

    # 5. Specs and connections are in step in both directions.
    on_disk = {Path(p).as_posix() for p in glob.glob("integrations/openapi/*.yaml",
                                                     root_dir=CONV)}
    declared = {c["spec"] for c in reg["connections"].values() if c.get("spec")}
    for spec in sorted(on_disk - declared):
        findings.append(("connections", f"{spec} is not registered by any connection"))
    for spec in sorted(declared - on_disk):
        findings.append(("connections", f"registry references missing spec {spec}"))

    # 6. Every template can be regression-tested and rendered.
    ids = {t["id"] for t in treg}
    samples = {Path(p).stem for p in glob.glob("templates/samples/*.json",
                                               root_dir=CONV)}
    for tid in sorted(ids - samples):
        findings.append(("templates",
                         f"{tid} has no sample under templates/samples/ — "
                         f"run_regression.py cannot exercise it"))

    # 7. Everything described in the console is described everywhere.
    for name, cfg in sorted(reg["connections"].items()):
        if not cfg.get("_comment"):
            findings.append(("descriptions",
                             f"connection {name} has no _comment"))
    return findings


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--list", action="store_true",
                    help="report and exit 0 (for a review, not a gate)")
    args = ap.parse_args()

    findings = audit()
    checks = ("skill-decisions", "advisory-toolset", "pipelines", "profiles",
              "guardrails", "connections", "templates", "descriptions")
    print(f">> cross-artefact coverage audit — {len(checks)} check(s)")
    by_check: dict[str, list[str]] = {}
    for check, msg in findings:
        by_check.setdefault(check, []).append(msg)
    for check in checks:
        hits = by_check.get(check, [])
        print(f"   {'ok  ' if not hits else 'FAIL'} {check}"
              f"{'' if not hits else f' — {len(hits)}'}")
        for msg in hits:
            print(f"        - {msg}", file=sys.stderr)
    if findings and not args.list:
        print(f"coverage audit FAILED — {len(findings)} finding(s)", file=sys.stderr)
        return 1
    print("coverage audit OK" if not findings
          else f"coverage audit: {len(findings)} finding(s) (--list, not failing)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
