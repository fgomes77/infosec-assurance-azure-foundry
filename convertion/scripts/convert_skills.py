#!/usr/bin/env python3
"""Convert the Claude account export into Azure AI Foundry agent definitions.

Reads ../../claude-account-export/skills/<name>/ and writes, per skill:

    ../build/agents/<name>/
        instructions.md     persona preamble + SKILL.md body (frontmatter
                            stripped; description saved separately)
        knowledge/          files for a file_search vector store
                            (references/, plus any *.md outside scripts/)
        code/               files for code_interpreter (scripts/, assets/)

plus ../build/manifest.json describing every agent (name, description,
tools, flags). Deterministic and offline — safe to re-run; the build dir is
rebuilt from scratch each time.

Usage:
    python3 convert_skills.py                 # custom + document skills
    python3 convert_skills.py --include-examples
    python3 convert_skills.py --only dora,nis2
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXPORT = HERE.parent.parent / "claude-account-export" / "skills"
BUILD = HERE.parent / "build"
PERSONA = HERE.parent / "agents" / "persona_system_prompt.md"

# Anthropic example skills: converted only with --include-examples, and
# several only make sense on the Claude platform (marked platform_specific).
EXAMPLE_SKILLS = {
    "algorithmic-art", "brand-guidelines", "canvas-design", "doc-coauthoring",
    "import-memory", "internal-comms", "learn", "mcp-builder", "morning",
    "skill-creator", "slack-gif-creator", "theme-factory",
    "web-artifacts-builder",
}
PLATFORM_SPECIFIC = {
    "canvas-design", "import-memory", "morning", "skill-creator",
    "slack-gif-creator", "web-artifacts-builder", "theme-factory",
}
# Router skill: becomes a connected-agents router (create_agents.py wires it).
ROUTER = {"enx-tprm-control-center": [
    "dpia", "ciso-reporting", "cyber-forum", "onetrust-form-b",
    "deepsearch-protocol",
]}
# Skills whose generators are Node.js — code_interpreter is Python-only.
EXTERNAL_RUNTIME = {"tprm-slide-generator", "pptx-executive-summary-ciso",
                    "ciso-reporting", "pptx", "docx"}
KNOWLEDGE_ONLY = {"whisperx-transcribe-diarize"}
GROUNDING_RECOMMENDED = {"deepsearch-protocol",
                         "ai-deepsearch-osint-gathering-report", "cyber-forum"}

FRONTMATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse_skill_md(path: Path) -> tuple[str, str]:
    """Return (description, body) from a SKILL.md with YAML frontmatter."""
    text = path.read_text(encoding="utf-8")
    m = FRONTMATTER.match(text)
    if not m:
        return "", text
    desc = ""
    fm = m.group(1)
    dm = re.search(r"^description:\s*(.*(?:\n(?:  |\t).*)*)", fm, re.MULTILINE)
    if dm:
        desc = re.sub(r"\s+", " ", dm.group(1)).strip().strip("\"'")
    return desc, text[m.end():]


def convert_one(src: Path, persona: str) -> dict:
    name = src.name
    out = BUILD / "agents" / name
    out.mkdir(parents=True)

    desc, body = parse_skill_md(src / "SKILL.md")
    (out / "instructions.md").write_text(persona + "\n\n---\n\n" + body,
                                         encoding="utf-8")

    knowledge, code = [], []
    for p in sorted(src.rglob("*")):
        if not p.is_file() or p.name == "SKILL.md" or "__pycache__" in p.parts:
            continue
        rel = p.relative_to(src)
        top = rel.parts[0]
        bucket = "code" if top in ("scripts", "assets") else "knowledge"
        if name in KNOWLEDGE_ONLY:
            bucket = "knowledge"
        dest = out / bucket / "__".join(rel.parts)  # flatten: vector stores take flat files
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dest)
        (knowledge if bucket == "knowledge" else code).append(dest.name)

    return {
        "name": name,
        "description": desc[:512],
        "instructions_file": f"agents/{name}/instructions.md",
        "knowledge_files": knowledge,
        "code_files": code,
        "tools": (["file_search"] if knowledge else [])
                 + (["code_interpreter"] if code else []),
        "router_targets": ROUTER.get(name, []),
        "requires_external_runtime": name in EXTERNAL_RUNTIME,
        "grounding_recommended": name in GROUNDING_RECOMMENDED,
        "platform_specific": name in PLATFORM_SPECIFIC,
        "is_example_skill": name in EXAMPLE_SKILLS,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--include-examples", action="store_true")
    ap.add_argument("--only", help="comma-separated skill names")
    args = ap.parse_args()

    if not EXPORT.is_dir():
        sys.exit(f"Export not found at {EXPORT}")
    if BUILD.exists():
        shutil.rmtree(BUILD)

    persona = PERSONA.read_text(encoding="utf-8")
    persona = persona.split("---", 2)[-1].strip()  # drop the file's own header

    only = set(args.only.split(",")) if args.only else None
    manifest = []
    for src in sorted(EXPORT.iterdir()):
        if not src.is_dir() or not (src / "SKILL.md").is_file():
            continue
        if only is not None and src.name not in only:
            continue
        if only is None and src.name in EXAMPLE_SKILLS and not args.include_examples:
            continue
        manifest.append(convert_one(src, persona))
        print(f"converted {src.name}: "
              f"{len(manifest[-1]['knowledge_files'])} knowledge, "
              f"{len(manifest[-1]['code_files'])} code")

    (BUILD / "manifest.json").write_text(
        json.dumps({"agents": manifest}, indent=2), encoding="utf-8")
    print(f"\n{len(manifest)} agent definitions -> {BUILD}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
