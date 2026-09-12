#!/usr/bin/env python3
"""Verify that the built agent definitions (build/) are correct and carry
the LATEST templates, rules and requirements from the claude.ai export
(../claude-account-export/skills/ and, when converted on demand,
platform-skills/).

Checks:
  1. COVERAGE   - build -> export: every manifest agent has a source skill;
                  export -> build: every exported skill is in the manifest
                  OR carries a recorded decision (EXAMPLE_SKILLS need
                  --include-examples); the export's own manifest.json count
                  is reconciled.
  2. FIDELITY   - every knowledge file, code-tree file AND zip member's
                  SHA-256 matches its source (templates, catalogues,
                  schemas are byte-identical); shared__/pack__ copies match
                  the SSOT / knowledge-pack file they were copied from.
  3. COMPLETE   - no source file is missing from the build (and none
                  extra); every upload has an accepted extension
                  (file_search text types; code/ holds ONLY the zip);
                  packaged .py members compile and every
                  require(path.join(__dirname, "<rel>")) resolves.
  4. RULES      - instructions.md contains the full SKILL.md body (all
                  rules/requirements, contiguous), the persona preamble,
                  the Foundry environment overlay, the document addendum
                  (docx/pdf/pptx/xlsx), the code-package note when a zip
                  is attached, and the mandatory APPROVAL GATE block LAST.
  5. FRESHNESS  - marker checks that known latest content is present
                  (corrected DORA Art. 30 framing, regenerated templates,
                  current docx/pptx/xlsx skill revisions).
  6. DELIVERY   - the Foundry-only agents (advisor, verifier, orchestrator,
                  ciso-global-report, analyzers, template-manager) build
                  with persona + APPROVAL GATE; their SHA-256 is frozen in
                  build/instruction-hashes.json for verify_deployment.py.

Exit 0 = conversion verified; exit 1 = discrepancies listed.
Run convert_skills.py first (same flags, e.g. --include-examples).
"""

from __future__ import annotations

import hashlib
import json
import py_compile
import re
import sys
import tempfile
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
CONV = HERE.parent
EXPORT_ROOT = CONV.parent / "claude-account-export"
EXPORT = EXPORT_ROOT / "skills"
BUILD = CONV / "build"
PACKS = CONV / "agents" / "knowledge-packs"

from convert_skills import (EXAMPLE_SKILLS, FILE_SEARCH_EXT,  # noqa: E402
                            PLATFORM_ROOTS, bucket_for)

FRONTMATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
REQUIRE_RE = re.compile(r"""require\(\s*path\.join\(\s*__dirname\s*,\s*['"]([^'"]+)['"]""")

# Content markers that must be present if the build is on the latest export.
FRESHNESS_MARKERS = {
    "dora": ("instructions.md",
             "baseline provisions for ALL ICT service contracts"),
    "ciso-executive-summary": ("code-tree/assets/template.html",
                               "Reconstructed asset"),
    "tprm-slide-generator": ("knowledge/references__data_schema.md",
                             "Reconstructed reference"),
    "iso27001": ("knowledge/references__annex-a-2022.md", "5.7"),
    "docx": ("instructions.md", "PositionalTab"),
    "pptx": ("instructions.md", "secondaryValAxis"),
    "xlsx": ("instructions.md", "_xlfn."),
}
DELIVERY_AGENTS = ("ciso-global-report", "tpa-evidence-analyzer",
                   "soc-report-analyzer", "pentest-report-analyzer",
                   "template-manager")


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def source_dir(spec: dict) -> Path:
    tree = spec.get("source_tree", "skills")
    root = EXPORT if tree == "skills" else PLATFORM_ROOTS[tree]
    return root / spec["name"]


def check_package(name: str, zpath: Path, src: Path, problems: list[str]) -> int:
    """Zip members byte-identical to source, .py compiles, require() resolves."""
    n = 0
    with zipfile.ZipFile(zpath) as z:
        members = {zi.filename: z.read(zi) for zi in z.infolist()}
    for member, data in members.items():
        if member.startswith("foundry/"):
            adapter = HERE / "adapters" / Path(member).name
            if not adapter.is_file() or sha(adapter) != hashlib.sha256(data).hexdigest():
                problems.append(f"{name}: adapter {member} differs from scripts/adapters")
            continue
        origin = src / member
        if not origin.is_file():
            problems.append(f"{name}: zip member without source: {member}")
        elif sha(origin) != hashlib.sha256(data).hexdigest():
            problems.append(f"{name}: CONTENT DRIFT in package member {member}")
        else:
            n += 1
        if member.endswith(".py"):
            with tempfile.NamedTemporaryFile("wb", suffix=".py", delete=False) as t:
                t.write(data)
            try:
                py_compile.compile(t.name, doraise=True)
            except py_compile.PyCompileError as e:
                problems.append(f"{name}: {member} does not compile: {e.msg[:80]}")
            finally:
                Path(t.name).unlink(missing_ok=True)
        if member.endswith((".js", ".cjs", ".mjs")):
            for rel in REQUIRE_RE.findall(data.decode("utf-8", "replace")):
                target = _norm(f"{Path(member).parent.as_posix()}/{rel}")
                if target not in members and target + ".js" not in members:
                    problems.append(f"{name}: {member} requires {rel!r} which is "
                                    f"not in the package")
    return n


def _norm(p: str) -> str:
    parts: list[str] = []
    for seg in p.split("/"):
        if seg == "..":
            if parts:
                parts.pop()
        elif seg and seg != ".":
            parts.append(seg)
    return "/".join(parts)


def main() -> int:
    problems: list[str] = []
    mf = json.loads((BUILD / "manifest.json").read_text())
    manifest = {a["name"]: a for a in mf["agents"]}
    options = mf.get("options", {})

    # 1. coverage export -> build (every exported skill included or decided)
    exported = {d.name for d in EXPORT.iterdir() if (d / "SKILL.md").is_file()}
    for name in sorted(exported - set(manifest)):
        if options.get("only"):
            continue                                   # partial build by request
        if name in EXAMPLE_SKILLS and not options.get("include_examples"):
            continue                                   # decision: optional (MAPPING.md)
        problems.append(f"{name}: exported skill neither converted nor covered "
                        f"by a recorded decision (EXAMPLE_SKILLS)")
    try:
        listed = {s["name"] for s in json.loads(
            (EXPORT / "manifest.json").read_text())["skills"]}
        if listed != exported:
            problems.append(f"export manifest.json lists {len(listed)} skills, "
                            f"folders hold {len(exported)}: "
                            f"{sorted(listed ^ exported)}")
    except (OSError, KeyError, json.JSONDecodeError):
        problems.append("export manifest.json unreadable")

    checked_files = 0
    for name, spec in manifest.items():
        src = source_dir(spec)
        out = BUILD / "agents" / name
        if not src.is_dir():
            problems.append(f"{name}: no source skill in export")
            continue

        # 4. instructions completeness and ordering
        instr = (out / "instructions.md").read_text(encoding="utf-8")
        body = FRONTMATTER.sub("", (src / "SKILL.md").read_text(encoding="utf-8"))
        if body.strip() not in instr:
            problems.append(f"{name}: SKILL.md rules NOT fully present in instructions")
        if "Principal Security Assurance Consultant" not in instr:
            problems.append(f"{name}: persona preamble missing")
        if "APPROVAL GATE" not in instr:
            problems.append(f"{name}: approval gate missing")
        elif instr.rfind("## APPROVAL GATE") < instr.rfind("## CODE PACKAGE"):
            problems.append(f"{name}: approval gate must be the LAST block")
        if "Foundry environment overlay" not in instr:
            problems.append(f"{name}: Foundry environment overlay missing")
        if name in ("docx", "pdf", "pptx", "xlsx") and \
                "Document-agents addendum" not in instr:
            problems.append(f"{name}: document-agents addendum missing")
        if spec["code_files"] and "## CODE PACKAGE" not in instr:
            problems.append(f"{name}: code package note missing")
        if spec.get("source_tree", "skills") != "skills" and \
                "## FOUNDRY ADAPTATION" not in instr:
            problems.append(f"{name}: platform-skill FOUNDRY ADAPTATION missing")

        # 2+3. fidelity and completeness
        expected_k, expected_t = {}, {}
        for p in src.rglob("*"):
            if p.is_file() and p.name != "SKILL.md" and "__pycache__" not in p.parts:
                rel = p.relative_to(src)
                if bucket_for(name, rel) == "knowledge":
                    expected_k["__".join(rel.parts)] = sha(p)
                else:
                    expected_t[rel.as_posix()] = sha(p)
        built_k = {p.name: sha(p) for p in (out / "knowledge").iterdir()} \
            if (out / "knowledge").is_dir() else {}
        built_t = {p.relative_to(out / "code-tree").as_posix(): sha(p)
                   for p in (out / "code-tree").rglob("*") if p.is_file()} \
            if (out / "code-tree").is_dir() else {}
        for fname, digest in expected_k.items():
            if fname not in built_k:
                problems.append(f"{name}: source file missing from build: {fname}")
            elif built_k[fname] != digest:
                problems.append(f"{name}: CONTENT DRIFT in {fname}")
            else:
                checked_files += 1
        for fname, digest in built_k.items():
            if fname in expected_k:
                continue
            if fname.startswith("shared__"):
                origin = EXPORT / Path(*fname[len("shared__"):].split("__"))
            elif fname.startswith("pack__"):
                origin = PACKS / fname[len("pack__"):]
            else:
                problems.append(f"{name}: unexpected extra file in build: {fname}")
                continue
            if not origin.is_file() or sha(origin) != digest:
                problems.append(f"{name}: {fname} differs from its source {origin.name}")
            else:
                checked_files += 1
            if Path(fname).suffix.lower() not in FILE_SEARCH_EXT:
                problems.append(f"{name}: {fname} is not an accepted file_search type")
        for fname in expected_k:
            if Path(fname).suffix.lower() not in FILE_SEARCH_EXT:
                problems.append(f"{name}: knowledge file {fname} has an "
                                f"extension Azure file_search rejects")
        for fname, digest in expected_t.items():
            if fname not in built_t:
                problems.append(f"{name}: source file missing from code-tree: {fname}")
            elif built_t[fname] != digest:
                problems.append(f"{name}: CONTENT DRIFT in code-tree/{fname}")
            else:
                checked_files += 1
        for fname in built_t:
            if fname not in expected_t and not fname.startswith("foundry/"):
                problems.append(f"{name}: unexpected extra file in code-tree: {fname}")
        code_dir = out / "code"
        code_uploads = [p.name for p in code_dir.iterdir()] if code_dir.is_dir() else []
        if code_uploads != spec["code_files"]:
            problems.append(f"{name}: code/ uploads {code_uploads} != manifest")
        for fname in code_uploads:
            if not fname.endswith(".zip"):
                problems.append(f"{name}: code/ must hold only the package zip: {fname}")
            else:
                checked_files += check_package(name, code_dir / fname, src, problems)
        if expected_t and not code_uploads:
            problems.append(f"{name}: code-bearing files present but no package built")

    # 5. freshness markers
    for name, (rel, marker) in FRESHNESS_MARKERS.items():
        if name not in manifest:
            continue
        f = BUILD / "agents" / name / rel
        if not f.is_file() or marker not in f.read_text(encoding="utf-8",
                                                        errors="replace"):
            problems.append(f"{name}: freshness marker missing in {rel} "
                            f"(expected latest export content: {marker!r})")

    # 6. Foundry-only agents: instructions build offline, gates present, hashes frozen
    hashes: dict[str, str] = {}
    try:
        import create_orchestrator as co
        import create_delivery_agents as cda
        built = {co.ADVISOR: co.advisor_instructions(),
                 co.VERIFIER: co.verifier_instructions(),
                 co.ORCHESTRATOR: co.orchestrator_instructions()}
        for name in DELIVERY_AGENTS:
            built[name] = cda.build_instructions(name)
        for name, text in built.items():
            if "Principal Security Assurance Consultant" not in text:
                problems.append(f"{name}: persona preamble missing")
            if "APPROVAL GATE" not in text and name != co.VERIFIER:
                problems.append(f"{name}: approval gate missing")
            hashes[name] = hashlib.sha256(text.encode("utf-8")).hexdigest()
        for name, spec in manifest.items():
            hashes[name] = sha(BUILD / spec["instructions_file"])
        (BUILD / "instruction-hashes.json").write_text(
            json.dumps(hashes, indent=1, sort_keys=True), encoding="utf-8")
    except Exception as e:  # noqa: BLE001 - report, never crash the gate
        problems.append(f"delivery/orchestrator instructions could not be built: {e}")

    # informational: drift between platform-skills/ copies and skills/
    try:
        from diff_platform_copies import report as platform_drift
        for line in platform_drift():
            print(f"note: {line}")
    except Exception as e:  # noqa: BLE001
        print(f"note: platform copy comparison skipped: {e}")

    print(f"agents checked   : {len(manifest)}")
    print(f"files hash-match : {checked_files}")
    print(f"foundry-only     : {len(hashes) - len(manifest)} charters hashed")
    if problems:
        print(f"\nDISCREPANCIES ({len(problems)}):")
        for p in problems:
            print(f"  - {p}")
        print("\nRESULT: NOT verified - re-run convert_skills.py against a "
              "fresh export (git pull) and re-check.")
        return 1
    print("\nRESULT: verified - every agent carries the latest templates, "
          "rules and requirements from the claude.ai export, byte-identical, "
          "with persona, overlays and approval gate present.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
