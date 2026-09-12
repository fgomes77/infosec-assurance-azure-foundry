#!/usr/bin/env python3
"""Apply an APPROVED template change and propagate it everywhere
(requirement j — invoked ONLY by the template-update-approval workflow
after recorded human approval; never run it against an unapproved draft).

Steps (atomic: any failure rolls the source file back):
  1. Resolve the template in templates/registry.json.
  2. Back up the current source file, write the approved new content.
  3. Re-run the fidelity chain: convert_skills.py -> verify_conversion.py.
  4. Recreate ONLY the consuming agents (create_agents.py --only /
     create_delivery_agents.py --only) so their vector stores and
     code_interpreter files pick up the new template.
  5. Re-stage the delivery-function renderers (stage_renderers.py) when
     the template has a renderer.
  6. Bump the registry version + last_approved and write the audit line.

Usage:
    python3 update_templates.py --template <id> --file <new-content-file> \
        --approved-by "<name>" [--approval-run <logic-app-run-id>] [--dry-run]
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONV = HERE.parent
REPO = CONV.parent
REGISTRY = CONV / "templates" / "registry.json"
AUDIT = CONV / "templates" / "audit.log"


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True, cwd=str(HERE))


def bump(version: str) -> str:
    parts = version.split(".")
    try:
        parts[-1] = str(int(parts[-1]) + 1)
        return ".".join(parts)
    except ValueError:
        return version + ".1"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--template", required=True)
    ap.add_argument("--file", required=True,
                    help="file holding the approved new template content")
    ap.add_argument("--approved-by", required=True)
    ap.add_argument("--approval-run", default="")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    entry = next((t for t in reg["templates"] if t["id"] == args.template), None)
    if not entry:
        sys.exit(f"template {args.template!r} not in {REGISTRY}")

    src = REPO / entry["source"].split("#")[0]
    new = Path(args.file)
    if not new.exists():
        sys.exit(f"missing new-content file {new}")
    if src.is_dir():
        sys.exit(f"source {src} is a directory — pass the specific file as "
                 f"the registry source (edit registry.json first)")

    consumers = entry.get("consumers", [])
    print(f"template={args.template} source={src} consumers={consumers}")

    if args.dry_run:
        print("[dry-run] would write source, run convert->verify, recreate "
              f"{consumers}, restage renderers, bump "
              f"{entry.get('version')} -> {bump(entry.get('version') or '1.0')}")
        return 0

    backup = src.with_suffix(src.suffix + ".pre-update.bak")
    shutil.copy2(src, backup)
    src.write_bytes(new.read_bytes())
    try:
        run([sys.executable, "convert_skills.py"])
        run([sys.executable, "verify_conversion.py"])
        delivery = {"ciso-global-report", "tpa-evidence-analyzer",
                    "soc-report-analyzer", "pentest-report-analyzer",
                    "template-manager"}
        for agent in consumers:
            script = ("create_delivery_agents.py" if agent in delivery
                      else "create_agents.py")
            run([sys.executable, script, "--only", agent])
        if entry.get("renderer"):
            run([sys.executable, "stage_renderers.py"])
    except Exception:
        print("PROPAGATION FAILED — rolling source back", file=sys.stderr)
        shutil.copy2(backup, src)
        raise

    entry["version"] = bump(entry.get("version") or "1.0")
    entry["last_approved"] = dt.date.today().isoformat()
    REGISTRY.write_text(json.dumps(reg, indent=2) + "\n", encoding="utf-8")
    with AUDIT.open("a", encoding="utf-8") as f:
        f.write(f"{dt.datetime.now().isoformat()} template={args.template} "
                f"version={entry['version']} approved_by={args.approved_by} "
                f"approval_run={args.approval_run}\n")
    backup.unlink(missing_ok=True)
    print(f"applied: {args.template} -> v{entry['version']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
