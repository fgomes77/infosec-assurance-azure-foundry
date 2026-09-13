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
                  packaged .py members compile, their MODULE-LEVEL imports
                  resolve against the stdlib, the Function requirements.txt
                  pins and the package's own modules, and every
                  require(path.join(__dirname, "<rel>")) resolves.
                  Limit, deliberately: this is static resolution, not an
                  import smoke — nothing here executes an import, and lazy
                  imports inside a function/try (the pdf-coverage scripts'
                  fitz/pypdf/pytesseract behind a poppler/tesseract CLI
                  fallback) are out of scope by design. The executing proof
                  is the delivery image build, whose last layer runs
                  `python3 -c "import playwright, docx, pptx, openpyxl,
                  fitz, pdfplumber"` (functions/delivery/Dockerfile).
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

  7. DECISIONS  - templates/skill-decisions.json checks C1-C10: every
                  skill folder has exactly one decision row and every row
                  a folder; unique ids and agreeing counts; valid decision
                  and tier values; AGENT+deployed implies the manifest and
                  the registry; EXCLUDED implies neither; KNOWLEDGE-PACK
                  and SUPERSEDED targets exist; ALIAS resolves; duplicates
                  agree; rationale/owner/date non-empty. It also asserts
                  that convert_skills' EXAMPLE_SKILLS / PLATFORM_SPECIFIC /
                  ALIASES agree with the table, so the prose record, the
                  converter and this verifier cannot drift.

  8. READ-ONLY   - audit of what non-GET survives the attach-time strip:
                  only the five documented query POSTs, each carrying
                  `x-enx-read-only: true` AND an operationId in
                  attach_integrations.READ_ONLY_POST_OPS. A spec that
                  flags anything else FAILS, so editing a spec cannot
                  widen the Layer-1 rule. The MCP gateway definition
                  must carry no `headers` and no write-shaped tool name.

Exit 0 = conversion verified; exit 1 = discrepancies listed.
Run convert_skills.py first (same flags, e.g. --include-examples).
"""

from __future__ import annotations

import ast
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

from convert_skills import (ALIASES, EXAMPLE_SKILLS,  # noqa: E402
                            FILE_SEARCH_EXT, LICENSE_RESTRICTED,
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


# ------------------------------------------------- staged-package imports
# Module-level imports of a staged .py member must resolve in the delivery
# Function image, which installs exactly functions/delivery/requirements.txt on
# top of the stdlib. py_compile (below) proves a member PARSES; it never
# executes an import, so it cannot see a missing dependency — this map plus
# check_imports is the offline stand-in for the import smoke a container could
# run. Lazy imports inside a function/try are deliberately NOT checked: the
# staged pdf-coverage scripts import fitz/pypdf/pytesseract/PIL that way behind
# a CLI fallback (poppler/tesseract binaries in the Dockerfile), which is the
# documented degradation path, not a missing pin.
DIST_MODULES = {            # distribution in requirements.txt -> module it provides
    "pymupdf": {"fitz", "pymupdf"}, "pillow": {"PIL"},
    "python-docx": {"docx"}, "python-pptx": {"pptx"},
    "pyyaml": {"yaml"}, "beautifulsoup4": {"bs4"},
    "azure-functions": {"azure"}, "azure-identity": {"azure"},
    "dnspython": {"dns"}, "python-dateutil": {"dateutil"},
}
# A staged package runs in one of the two Function images, so the pin may be in
# either requirements file (the office scripts need defusedxml/lxml, which are
# office-tools' pins by the image split documented in functions/delivery/Dockerfile).
RUNTIME_REQS = (CONV / "functions" / "delivery" / "requirements.txt",
                CONV / "functions" / "office-tools" / "requirements.txt")


def _installed_modules() -> set[str]:
    mods: set[str] = set()
    for req in RUNTIME_REQS:
        if not req.is_file():
            continue
        for line in req.read_text(encoding="utf-8").splitlines():
            line = line.split("#")[0].strip()
            if not line or line.startswith("-"):
                continue
            dist = re.split(r"[=<>!~\[;]", line)[0].strip().lower()
            mods |= DIST_MODULES.get(dist, {dist.replace("-", "_")})
    return mods


def _local_names(members: dict[str, bytes]) -> set[str]:
    """Names importable from inside the package: module stems AND the package
    directories they live in (scripts run with their own directory on sys.path,
    so `office`, `helpers`, `validators` are local imports, not dependencies)."""
    names: set[str] = set()
    for m in members:
        if not m.endswith(".py"):
            continue
        p = Path(m)
        names.add(p.stem)
        names |= set(p.parts[:-1])
    return names


def check_imports(name: str, member: str, data: bytes, siblings: set[str],
                  problems: list[str]) -> None:
    """Module-level imports of a staged member resolve in the delivery image."""
    try:
        tree = ast.parse(data)
    except SyntaxError:
        return                                   # py_compile reports it
    allowed = sys.stdlib_module_names | _installed_modules() | siblings | {"__future__"}
    for node in tree.body:                       # top level only — lazy imports are fine
        names = []
        if isinstance(node, ast.Import):
            names = [a.name.split(".")[0] for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names = [node.module.split(".")[0]]
        for mod in names:
            if mod not in allowed:
                problems.append(
                    f"{name}: {member} imports {mod!r} at module level, which is "
                    f"neither stdlib, a package pinned in a Function "
                    f"requirements.txt, nor another package member — it would "
                    f"ImportError in the runtime image")


def check_package(name: str, zpath: Path, src: Path, problems: list[str]) -> int:
    """Zip members byte-identical to source, .py compiles AND its module-level
    imports resolve against functions/delivery/requirements.txt, require()
    resolves."""
    n = 0
    with zipfile.ZipFile(zpath) as z:
        members = {zi.filename: z.read(zi) for zi in z.infolist()}
    siblings = _local_names(members)
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
            check_imports(name, member, data, siblings, problems)
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


# --------------------------------------------------------- skill decisions
DECISIONS = CONV / "templates" / "skill-decisions.json"


def check_skill_decisions(manifest: dict, options: dict,
                          problems: list[str]) -> int:
    """Enforce templates/skill-decisions.json checks C1-C10.

    The JSON is the machine form of MAPPING.md and
    governance/PLATFORM_SKILLS_DECISION.md: one row per skill, so a skill can
    never be silently dropped or silently deployed. Every check below is
    decidable offline from the export tree, build/manifest.json and
    integrations/registry.json. Each failure is one line naming the skill id,
    matching the style of the other checks in this file.
    """
    try:
        table = json.loads(DECISIONS.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        problems.append(f"templates/skill-decisions.json unreadable: {e}")
        return 0
    rows = table.get("decisions", [])
    try:
        registry = json.loads(
            (CONV / "integrations" / "registry.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        problems.append(f"integrations/registry.json unreadable: {e}")
        registry = {}
    reg_agents = set(registry.get("agents", {}))
    reg_examples = set(registry.get("example_agents", {}))
    if isinstance(registry.get("example_agents"), dict):
        for v in registry["example_agents"].values():
            if isinstance(v, list):
                reg_examples |= set(v)
    tiers = set(registry.get("model_tiers", {}))

    # --- C1: folder <-> row, both directions, per origin
    folders = {"export": {d.name for d in EXPORT.iterdir()
                          if d.is_dir() and (d / "SKILL.md").is_file()}}
    for origin, root in (("platform-skills/public", EXPORT_ROOT / "platform-skills" / "public"),
                         ("platform-skills/examples", EXPORT_ROOT / "platform-skills" / "examples")):
        folders[origin] = ({d.name for d in root.iterdir() if d.is_dir()}
                           if root.is_dir() else set())
    by_origin: dict[str, list[dict]] = {}
    for r in rows:
        by_origin.setdefault(r.get("origin", "?"), []).append(r)
    for origin, names in folders.items():
        listed = [r.get("skill") for r in by_origin.get(origin, [])]
        for name in sorted(names - set(listed)):
            problems.append(f"{origin}/{name}: skill folder has no decision row "
                            f"(C1 - templates/skill-decisions.json)")
        for name in sorted(set(listed) - names):
            problems.append(f"{origin}/{name}: decision row has no skill folder (C1)")
        for name in sorted({n for n in listed if listed.count(n) > 1}):
            problems.append(f"{origin}/{name}: more than one decision row (C1)")

    # --- C2: unique ids, counts agree
    ids = [r.get("id") for r in rows]
    for i in sorted({i for i in ids if ids.count(i) > 1}):
        problems.append(f"{i}: duplicate decision id (C2)")
    counts = table.get("counts", {})
    for origin, rs in by_origin.items():
        if origin in counts and counts[origin] != len(rs):
            problems.append(f"counts['{origin}'] says {counts[origin]}, "
                            f"{len(rs)} rows present (C2)")
    if "total_enforced" in counts and counts["total_enforced"] != len(rows):
        problems.append(f"counts['total_enforced'] says {counts['total_enforced']}, "
                        f"{len(rows)} rows present (C2)")

    values = set(table.get("decision_values", {}))
    index = {r.get("id"): r for r in rows}
    for r in rows:
        rid = r.get("id", "<no id>")
        decision = r.get("decision")

        # --- C3: decision and tier are in their vocabularies
        if decision not in values:
            problems.append(f"{rid}: decision {decision!r} not in decision_values (C3)")
        if r.get("tier") and tiers and r["tier"] not in tiers:
            problems.append(f"{rid}: tier {r['tier']!r} is not a model_tier in "
                            f"integrations/registry.json (C3)")

        # --- C4: AGENT + deployed => built and registered
        if decision == "AGENT" and r.get("deployed"):
            flag = r.get("requires_flag")
            skipped = (
                (flag == "--include-examples" and not options.get("include_examples"))
                # The Anthropic-licensed skills are conversion-gated until the IP
                # position is settled (governance/THIRD_PARTY_IP.md §2). A build
                # without the acceptance is a legitimate build, not a gap.
                or (r.get("skill") in LICENSE_RESTRICTED
                    and not options.get("accept_anthropic_license")))
            agent = r.get("agent")
            if not agent:
                problems.append(f"{rid}: decision AGENT but no 'agent' name (C4)")
            else:
                if not skipped and not options.get("only") and agent not in manifest:
                    problems.append(f"{rid}: AGENT+deployed but {agent!r} is not in "
                                    f"build/manifest.json (C4)")
                if reg_agents and agent not in reg_agents and agent not in reg_examples:
                    problems.append(f"{rid}: AGENT+deployed but {agent!r} is in neither "
                                    f"registry.agents nor registry.example_agents (C4)")

        # --- C5: EXCLUDED => not an agent, not deployed, not registered
        if decision == "EXCLUDED":
            if r.get("agent"):
                problems.append(f"{rid}: EXCLUDED but carries agent {r['agent']!r} (C5)")
            if r.get("deployed"):
                problems.append(f"{rid}: EXCLUDED but deployed is true (C5)")
            if r.get("skill") in reg_agents:
                problems.append(f"{rid}: EXCLUDED but {r['skill']!r} is in "
                                f"integrations/registry.json agents (C5)")

        # --- C6: KNOWLEDGE-PACK => no agent, target file exists
        if decision == "KNOWLEDGE-PACK":
            if r.get("agent"):
                problems.append(f"{rid}: KNOWLEDGE-PACK but carries an agent (C6)")
            target = r.get("target")
            if not target or not (CONV.parent / target).exists():
                problems.append(f"{rid}: KNOWLEDGE-PACK target {target!r} does not exist (C6)")

        # --- C7: SUPERSEDED => superseded_by path exists
        if decision == "SUPERSEDED":
            sb = r.get("superseded_by") or ""
            # More than one component may supersede a skill; the field then
            # lists them joined by ' + ' (e.g. a script AND the policy that
            # governs it). Every path-looking token must resolve.
            parts = [t.strip() for t in sb.split("+") if "/" in t]
            if not parts:
                problems.append(f"{rid}: SUPERSEDED but superseded_by {sb!r} names "
                                f"no kit path (C7)")
            for part in parts:
                if not (CONV.parent / part).exists():
                    problems.append(f"{rid}: SUPERSEDED by {part!r}, "
                                    f"which does not exist (C7)")

        # --- C8: ALIAS resolves to an AGENT row and to convert_skills.ALIASES
        if decision == "ALIAS":
            ao = r.get("alias_of")
            twin = next((x for x in rows
                         if x.get("agent") == ao or x.get("skill") == ao), None)
            if twin is None or twin.get("decision") != "AGENT":
                problems.append(f"{rid}: alias_of {ao!r} is not an AGENT entry (C8)")
            if ALIASES.get(r.get("skill")) != ao:
                problems.append(f"{rid}: convert_skills.ALIASES maps "
                                f"{r.get('skill')!r} to {ALIASES.get(r.get('skill'))!r}, "
                                f"the table says {ao!r} (C8)")

        # --- C9: a duplicate carries the same decision as its twin
        dup = r.get("duplicate_of")
        if dup:
            twin = index.get(dup)
            if twin is None:
                problems.append(f"{rid}: duplicate_of {dup!r} is not an entry (C9)")
            elif twin.get("decision") != decision:
                problems.append(f"{rid}: decision {decision!r} disagrees with its twin "
                                f"{dup} ({twin.get('decision')!r}) (C9)")

        # --- C10: provenance
        for field in ("rationale", "owner", "date"):
            if not str(r.get(field) or "").strip():
                problems.append(f"{rid}: empty {field} (C10)")

    # --- PLATFORM_INCLUDE / PLATFORM_EXCLUDED (governance/PLATFORM_SKILLS_DECISION.md §4)
    # The constants that document names are derived FROM this table, so the
    # assertion is that convert_skills agrees with it, not that a second
    # hard-coded list exists.
    from convert_skills import ALIASES as _A, EXAMPLE_SKILLS as _E, PLATFORM_SPECIFIC as _P
    want_examples = {r["skill"] for r in rows
                     if r.get("origin") == "export"
                     and r.get("requires_flag") == "--include-examples"}
    if want_examples and want_examples != set(_E):
        problems.append(f"convert_skills.EXAMPLE_SKILLS disagrees with the decision table: "
                        f"only in code {sorted(set(_E) - want_examples)}, "
                        f"only in table {sorted(want_examples - set(_E))}")
    # PLATFORM_SPECIFIC is not the same set as "EXCLUDED or SUPERSEDED": a
    # skill can be excluded for having no assurance use (algorithmic-art,
    # brand-guidelines) without being Claude-platform-specific. The invariant
    # that must hold is the one that matters — a platform-specific skill is
    # never deployed as an agent.
    for name in sorted(_P):
        rs = [r for r in rows if r.get("skill") == name]
        if not rs:
            problems.append(f"convert_skills.PLATFORM_SPECIFIC lists {name!r}, "
                            f"which has no decision row (C1)")
        for r in rs:
            if r.get("decision") == "AGENT":
                problems.append(f"{r['id']}: decision AGENT but {name!r} is in "
                                f"convert_skills.PLATFORM_SPECIFIC — a "
                                f"platform-specific skill is never deployed")
    want_aliases = {r["skill"]: r.get("alias_of") for r in rows
                    if r.get("decision") == "ALIAS" and r.get("origin") == "export"}
    if want_aliases and want_aliases != dict(_A):
        problems.append(f"convert_skills.ALIASES disagrees with the decision table: "
                        f"code {dict(_A)}, table {want_aliases}")
    return len(rows)


def check_read_only_audit(problems: list[str]) -> list[str]:
    """Audit what non-GET survives the attach-time strip.

    `attach_integrations.load_openapi_spec` keeps a non-GET operation only when
    it carries `x-enx-read-only: true` AND its operationId is in
    `READ_ONLY_POST_OPS`. This re-derives that list straight from the specs, so
    a spec that quietly flags a write is a discrepancy here rather than a
    surprise at deploy time. It also refuses an MCP definition that carries
    run-time `headers` (the bearer belongs to the project connection, finding
    C10) or an allow-listed tool whose NAME reads like a write.
    """
    kept: list[str] = []
    try:
        import yaml
        from attach_integrations import READ_ONLY_POST_OPS
    except ImportError as e:
        problems.append(f"read-only audit skipped: {e}")
        return kept
    for spec_path in sorted((CONV / "integrations" / "openapi").glob("*.yaml")):
        try:
            spec = yaml.safe_load(spec_path.read_text(encoding="utf-8")) or {}
        except Exception as e:  # noqa: BLE001
            problems.append(f"{spec_path.name}: unreadable ({e})")
            continue
        for path, ops in (spec.get("paths") or {}).items():
            if not isinstance(ops, dict):
                continue
            for verb, op in ops.items():
                if verb.lower() in ("get", "parameters") or not isinstance(op, dict):
                    continue
                op_id = op.get("operationId")
                flagged = op.get("x-enx-read-only") is True
                if flagged and op_id in READ_ONLY_POST_OPS:
                    kept.append(f"{spec_path.name}: {verb.upper()} {path} ({op_id})")
                elif flagged:
                    problems.append(
                        f"{spec_path.name}: {verb.upper()} {path} flags "
                        f"x-enx-read-only but {op_id!r} is not in the allow-set "
                        f"{sorted(READ_ONLY_POST_OPS)} — a spec edit must not be "
                        f"able to widen the Layer-1 read-only rule")
    mcp = CONV / "integrations" / "mcp" / "enx-gateway.json"
    if mcp.exists():
        try:
            cfg = json.loads(mcp.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            problems.append(f"integrations/mcp/enx-gateway.json unreadable: {e}")
            cfg = {}
        if "headers" in cfg:
            problems.append("integrations/mcp/enx-gateway.json carries a 'headers' "
                            "key: the gateway bearer belongs to the project "
                            "connection conn-enx-gateway, never to the definition "
                            "or to a run payload (finding C10)")
        for t in cfg.get("allowed_tools", []):
            if re.search(r"(submit|create|update|delete|post|write)", str(t), re.I):
                problems.append(f"integrations/mcp/enx-gateway.json allows tool "
                                f"{t!r}, whose name reads as a write "
                                f"(governance/HUMAN_APPROVAL.md Layer 1)")
    return kept


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
        if name in LICENSE_RESTRICTED and not options.get("accept_anthropic_license"):
            continue        # decision: conversion-gated (governance/THIRD_PARTY_IP.md §2)
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

    decisions_checked = check_skill_decisions(manifest, options, problems)
    kept_posts = check_read_only_audit(problems)

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
    print(f"skill decisions  : {decisions_checked} enforced "
          f"(templates/skill-decisions.json C1-C10)")
    print(f"read-only audit  : {len(kept_posts)} non-GET operation(s) kept")
    for line in kept_posts:
        print(f"                   {line}")
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
