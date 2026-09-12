#!/usr/bin/env python3
"""Stage the byte-verified report generators into the delivery Function's
renderers/ folder (functions/delivery/renderers/<template>/), per the
`renderer` fields in templates/registry.json.

Run AFTER convert_skills.py + verify_conversion.py — staging only ever
copies out of the verified build, which is what keeps rendered files
identical to the previous claude.ai environment. Re-run after any
approved template update (update_templates.py calls it automatically).
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONV = HERE.parent
BUILD = CONV / "build"
DEST = CONV / "functions" / "delivery" / "renderers"

# renderer folder -> source(s) in the verified build (first match wins)
SOURCES = {
    "dpia": ["build/agents/dpia/code"],
    "ciso-reporting": ["build/agents/ciso-reporting/code"],
    "ciso-global": ["functions/delivery/renderers-src/ciso-global"],
    "evidence-summary": ["functions/delivery/renderers-src/evidence-summary"],
    "xlsx-generic": ["build/agents/xlsx/code"],
}


def main() -> int:
    reg = json.loads((CONV / "templates" / "registry.json")
                     .read_text(encoding="utf-8"))
    wanted = {Path(t["renderer"]).parent.name
              for t in reg["templates"] if t.get("renderer")}
    staged, missing = [], []
    for name in sorted(wanted):
        for cand in SOURCES.get(name, []):
            src = CONV / cand
            if src.is_dir() and any(src.iterdir()):
                dest = DEST / name
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(src, dest)
                staged.append(f"{name} <- {cand}")
                break
        else:
            missing.append(name)
    for line in staged:
        print("staged ", line)
    if missing:
        print(f"MISSING sources for: {', '.join(missing)} — run "
              f"convert_skills.py first (or add the renderer source)",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
