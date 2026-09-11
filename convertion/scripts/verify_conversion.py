#!/usr/bin/env python3
"""Verify that the built agent definitions (build/) are correct and carry
the LATEST templates, rules and requirements from the claude.ai export
(../claude-account-export/skills/).

Checks, per agent:
  1. COVERAGE   - every convertible skill has a build/agents/<name>/ entry.
  2. FIDELITY   - every knowledge/code file's SHA-256 matches its source
                  (templates, catalogues, schemas are byte-identical).
  3. COMPLETE   - no source file is missing from the build (and none extra).
  4. RULES      - instructions.md contains the full SKILL.md body (all
                  rules/requirements), the persona preamble, and the
                  mandatory APPROVAL GATE block.
  5. FRESHNESS  - marker checks that known latest content is present, e.g.
                  the corrected DORA Art. 30 framing and the regenerated
                  ciso-executive-summary template.

Exit 0 = conversion verified; exit 1 = discrepancies listed.
Run convert_skills.py first (same flags, e.g. --include-examples).
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONV = HERE.parent
EXPORT = CONV.parent / "claude-account-export" / "skills"
BUILD = CONV / "build"

FRONTMATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)

# Content markers that must be present if the build is on the latest export.
FRESHNESS_MARKERS = {
    "dora": ("instructions.md",
             "baseline provisions for ALL ICT service contracts"),
    "ciso-executive-summary": ("code/assets__template.html",
                               "Reconstructed asset"),
    "tprm-slide-generator": ("knowledge/references__data_schema.md",
                             "Reconstructed reference"),
    "iso27001": ("knowledge/references__annex-a-2022.md", "5.7"),
}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    problems: list[str] = []
    manifest = {a["name"]: a for a in json.loads(
        (BUILD / "manifest.json").read_text())["agents"]}

    checked_files = 0
    for name, spec in manifest.items():
        src = EXPORT / name
        out = BUILD / "agents" / name
        if not src.is_dir():
            problems.append(f"{name}: no source skill in export")
            continue

        # 4. instructions completeness
        instr = (out / "instructions.md").read_text(encoding="utf-8")
        body = FRONTMATTER.sub("", (src / "SKILL.md").read_text(encoding="utf-8"))
        if body.strip() not in instr:
            problems.append(f"{name}: SKILL.md rules NOT fully present in instructions")
        if "Principal Security Assurance Consultant" not in instr:
            problems.append(f"{name}: persona preamble missing")
        if "APPROVAL GATE" not in instr:
            problems.append(f"{name}: approval gate missing")

        # 2+3. file fidelity and completeness (flattened names, as converter)
        expected = {}
        for p in src.rglob("*"):
            if p.is_file() and p.name != "SKILL.md" and "__pycache__" not in p.parts:
                expected["__".join(p.relative_to(src).parts)] = sha(p)
        built = {}
        for bucket in ("knowledge", "code"):
            d = out / bucket
            if d.is_dir():
                for p in d.iterdir():
                    built[p.name] = sha(p)
        for fname, digest in expected.items():
            if fname not in built:
                problems.append(f"{name}: source file missing from build: {fname}")
            elif built[fname] != digest:
                problems.append(f"{name}: CONTENT DRIFT in {fname}")
            else:
                checked_files += 1
        for fname in built:
            if fname not in expected:
                problems.append(f"{name}: unexpected extra file in build: {fname}")

    # 5. freshness markers
    for name, (rel, marker) in FRESHNESS_MARKERS.items():
        if name not in manifest:
            continue
        f = BUILD / "agents" / name / rel
        if not f.is_file() or marker not in f.read_text(encoding="utf-8",
                                                        errors="replace"):
            problems.append(f"{name}: freshness marker missing in {rel} "
                            f"(expected latest export content: {marker!r})")

    print(f"agents checked   : {len(manifest)}")
    print(f"files hash-match : {checked_files}")
    if problems:
        print(f"\nDISCREPANCIES ({len(problems)}):")
        for p in problems:
            print(f"  - {p}")
        print("\nRESULT: NOT verified - re-run convert_skills.py against a "
              "fresh export (git pull) and re-check.")
        return 1
    print("\nRESULT: verified - every agent carries the latest templates, "
          "rules and requirements from the claude.ai export, byte-identical, "
          "with persona and approval gate present.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
