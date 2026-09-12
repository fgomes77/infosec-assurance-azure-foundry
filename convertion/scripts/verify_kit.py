#!/usr/bin/env python3
"""Deploy gate for the conversion kit itself (deploy.sh step 2, next to
verify_conversion.py). Offline, read-only.

  1. SECRETS    - no tokens/keys/passwords, private keys, Basic-auth blobs,
                  real tenant hostnames or e-mail addresses anywhere under
                  convertion/ (placeholders in {braces} / <angle> are fine)
                  - governance/DATA_PROTECTION_GUARDRAILS.md §3.
  2. SYNTAX     - every *.json parses (workflows, registries, connections),
                  every OpenAPI *.yaml parses (PyYAML; skipped with a note
                  when the module is absent), every *.sh passes `bash -n`.
  3. CROSS-REFS - integrations/registry.json agents ⊆ manifest ∪ delivery
                  ∪ advisor; advisory toolset agents ⊆ registry; every
                  connection's spec/config exists; write_connections empty
                  (read-only enterprise access) unless listed in
                  registry "write_exceptions"; templates/registry.json
                  consumers exist, pipelines exist in workflows/pipelines.json,
                  renderer folders are known to stage_renderers.SOURCES;
                  pipelines.json agents exist; every delivery agent has
                  agents/<name>_instructions.md; the overlays/addenda the
                  converter expects exist.

Exit 0 = kit consistent; exit 1 = findings listed.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
CONV = HERE.parent
BUILD = CONV / "build"

SKIP_DIRS = {"build", "__pycache__", "renderers", "backups", "node_modules"}
TEXT_EXT = {".md", ".json", ".yaml", ".yml", ".py", ".sh", ".bicep", ".txt",
            ".env", ".example", ".js", ".html", ".csv", ".kql"}

SECRET_PATTERNS = [
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("OpenAI-style key", re.compile(r"\bsk-[A-Za-z0-9]{20,}\b")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b")),
    ("Slack token", re.compile(r"\bxox[abpr]-[A-Za-z0-9-]{10,}\b")),
    ("private key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("Basic auth blob", re.compile(r"Authorization:\s*Basic\s+[A-Za-z0-9+/=]{16,}")),
    ("Bearer token literal", re.compile(r"Bearer\s+ey[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}")),
    ("SAS signature", re.compile(r"[?&]sig=[A-Za-z0-9%+/=]{20,}")),
    ("assigned secret", re.compile(
        r"(?i)\b(client_secret|api[_-]?key|password|secret)\b\s*[:=]\s*['\"]?"
        r"(?![{<$@\s'\"]|\{\{|Microsoft\.KeyVault|<|\$\(|\$\{|none|null|\*+|"
        r"placeholder|redacted|from|see|stored|lives|in |key vault|keyvault)"
        r"[A-Za-z0-9~._+/=-]{16,}")),
    ("real SharePoint tenant", re.compile(r"\b(?!<tenant>)(?!\{)[a-z0-9]{3,}\.sharepoint\.com\b")),
    ("e-mail address", re.compile(r"(?<![{<`])\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b(?![}>`])")),
]
EMAIL_OK = re.compile(r"@(example\.(com|org|net)|contoso\.com|noreply\.[a-z]+|"
                      r"microsoft\.com|anthropic\.com|euronext\.com)$|"
                      r"^(noreply|no-reply|placeholder)@", re.I)


def iter_files():
    for p in CONV.rglob("*"):
        if not p.is_file() or set(p.parts) & SKIP_DIRS:
            continue
        if p.suffix.lower() in TEXT_EXT or p.name in (".env.example",):
            yield p


def scan_secrets(findings: list[str]) -> int:
    n = 0
    for p in iter_files():
        n += 1
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        rel = p.relative_to(CONV)
        for label, rx in SECRET_PATTERNS:
            for m in rx.finditer(text):
                hit = m.group(0)
                if label == "e-mail address" and (EMAIL_OK.search(hit)
                                                  or "{" in hit or "<" in hit):
                    continue
                if label == "real SharePoint tenant" and re.match(
                        r"(tenant|contoso|example|yourtenant|\{)", hit):
                    continue
                line = text.count("\n", 0, m.start()) + 1
                findings.append(f"SECRETS  {rel}:{line}: {label}: {hit[:40]}…")
    return n


def check_syntax(findings: list[str]) -> None:
    for p in iter_files():
        rel = p.relative_to(CONV)
        if p.suffix == ".json":
            try:
                json.loads(p.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                findings.append(f"SYNTAX   {rel}: invalid JSON ({e.msg} line {e.lineno})")
        elif p.suffix in (".yaml", ".yml"):
            try:
                import yaml
                yaml.safe_load(p.read_text(encoding="utf-8"))
            except ImportError:
                print(f"note: PyYAML missing - {rel} not parsed")
            except Exception as e:  # noqa: BLE001
                findings.append(f"SYNTAX   {rel}: invalid YAML ({str(e)[:80]})")
        elif p.suffix == ".sh":
            r = subprocess.run(["bash", "-n", str(p)], capture_output=True, text=True)
            if r.returncode:
                findings.append(f"SYNTAX   {rel}: bash -n failed: {r.stderr.strip()[:100]}")


def check_crossrefs(findings: list[str]) -> None:
    reg = json.loads((CONV / "integrations" / "registry.json").read_text(encoding="utf-8"))
    treg = json.loads((CONV / "templates" / "registry.json").read_text(encoding="utf-8"))
    pipes = json.loads((CONV / "workflows" / "pipelines.json").read_text(encoding="utf-8"))
    from create_delivery_agents import AGENTS as DELIVERY
    from create_orchestrator import ADVISOR, ORCHESTRATOR, VERIFIER
    from stage_renderers import SOURCES
    from convert_skills import EXAMPLE_SKILLS, ALIASES

    manifest = {}
    if (BUILD / "manifest.json").is_file():
        manifest = {a["name"] for a in json.loads(
            (BUILD / "manifest.json").read_text())["agents"]}
    else:
        print("note: build/manifest.json missing - run convert_skills.py; "
              "manifest cross-references skipped")
    known = set(manifest) | set(DELIVERY) | {ADVISOR, ORCHESTRATOR, VERIFIER} \
        | EXAMPLE_SKILLS | set(ALIASES)

    for name, cfg in reg["agents"].items():
        if manifest and name not in known:
            findings.append(f"XREF     registry agent {name!r} is neither converted "
                            f"nor a delivery/advisor agent")
        for t in cfg.get("tools", []):
            if t not in reg["connections"]:
                findings.append(f"XREF     registry agent {name}: unknown connection {t!r}")
        # finding C4/C9: the registry must not contradict itself - a tier model
        # that cannot carry a tool, or a disabled connection listed on an agent
        tier = cfg.get("model_tier", "chat")
        dep = reg.get("model_tiers", {}).get("_deployment_of_record", {}).get(tier)
        row = reg.get("model_tiers", {}).get(
            "_tool_compatibility", {}).get("models", {}).get(dep, {})
        for t in cfg.get("tools", []):
            conn = reg["connections"].get(t, {})
            if row.get(conn.get("type")) == "no":
                findings.append(f"XREF     registry agent {name}: tier {tier!r} model {dep!r} "
                                f"cannot carry tool type {conn.get('type')!r} of {t!r} (finding C4)")
            if not conn.get("enabled", True):
                findings.append(f"XREF     registry agent {name}: connection {t!r} is "
                                f"disabled (enabled=false) but attached")
        writes = cfg.get("write_connections", [])
        if writes and name not in reg.get("write_exceptions", {}):
            findings.append(f"XREF     registry agent {name}: write_connections {writes} "
                            f"but enterprise access is read-only (HUMAN_APPROVAL.md L1)")
    for name in reg.get("advisory_read_only_toolset", {}).get("agents", []):
        if name not in reg["agents"]:
            findings.append(f"XREF     advisory agent {name!r} has no registry entry")
    for key, conn in reg["connections"].items():
        ref = conn.get("spec") or conn.get("config")
        if ref and not (CONV / ref).is_file():
            findings.append(f"XREF     connection {key}: missing file {ref}")

    for t in treg["templates"]:
        for c in t.get("consumers", []):
            if manifest and c not in known:
                findings.append(f"XREF     template {t['id']}: unknown consumer {c!r}")
        for pid in t.get("pipelines", []):
            if pid not in pipes["pipelines"]:
                findings.append(f"XREF     template {t['id']}: pipeline {pid!r} not in pipelines.json")
        if t.get("renderer"):
            folder = Path(t["renderer"]).parent.name
            if folder not in SOURCES:
                findings.append(f"XREF     template {t['id']}: renderer folder {folder!r} "
                                f"unknown to stage_renderers.SOURCES")
        src = t.get("source", "").split("#")[0]
        if src and not (CONV.parent / src).exists():
            findings.append(f"XREF     template {t['id']}: source {src} missing")
    for pid, cfg in pipes["pipelines"].items():
        # "TRIGGER" = agent id supplied by the caller (advisory-file-delivery)
        if manifest and cfg.get("agent") not in (None, "TRIGGER") \
                and cfg["agent"] not in known:
            findings.append(f"XREF     pipeline {pid}: unknown agent {cfg['agent']!r}")
    for name in DELIVERY:
        if not (CONV / "agents" / f"{name}_instructions.md").is_file():
            findings.append(f"XREF     delivery agent {name}: charter missing")
    for rel in ("agents/overlays/_foundry-environment.md",
                "agents/overlays/research-pattern.md",
                "agents/document_agents_addendum.md",
                "agents/advisory_addendum.md", "agents/persona_system_prompt.md",
                "agents/orchestrator_instructions.md",
                "agents/verifier_instructions.md", "agents/advisor_instructions.md"):
        if not (CONV / rel).is_file():
            findings.append(f"XREF     required file missing: {rel}")
    for wf in (CONV / "workflows").glob("*.json"):
        if wf.name == "pipelines.json":
            continue
        d = json.loads(wf.read_text(encoding="utf-8"))
        if "definition" not in d:
            findings.append(f"XREF     workflow {wf.name}: no 'definition' object")


def main() -> int:
    findings: list[str] = []
    n = scan_secrets(findings)
    check_syntax(findings)
    check_crossrefs(findings)
    print(f"files scanned    : {n}")
    if findings:
        print(f"\nFINDINGS ({len(findings)}):")
        for f in findings:
            print(f"  - {f}")
        print("\nRESULT: kit NOT consistent")
        return 1
    print("\nRESULT: kit consistent - no secrets, all JSON/YAML/shell parse, "
          "cross-references resolve.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
