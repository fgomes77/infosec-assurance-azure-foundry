#!/usr/bin/env python3
"""Stage the byte-verified document-skill scripts into this image's
`toolchain/` folder BEFORE `az acr build` (the office-tools counterpart of
scripts/stage_renderers.py).

Run AFTER convert_skills.py + verify_conversion.py — staging only ever copies
out of the verified build (`build/agents/<skill>/code-tree/`, ORIGINAL layout
so `from office.soffice import ...` and `from helpers import ...` resolve),
which is what keeps recalculation, redlining and validation semantics
identical to the previous claude.ai environment.

    python3 convertion/functions/office-tools/stage_toolchain.py [--strict]
    az acr build -r {registry} -t infosec-office-tools:{tag} convertion/functions/office-tools

Layout produced (consumed by function_app.FAMILY_SCRIPT):

    toolchain/xlsx/scripts/recalc.py            -> POST /api/recalc
    toolchain/docx/scripts/accept_changes.py    -> POST /api/accept_changes
    toolchain/pptx/scripts/thumbnail.py         -> POST /api/thumbnail
    toolchain/<family>/scripts/office/validate.py -> POST /api/validate
    toolchain/pdf/scripts/…                     -> poppler helpers of the pdf skill

`toolchain/` is build output: it is git-ignored like functions/delivery/renderers/
and never hand-edited. A missing script is a 501 at runtime (never a silent
wrong answer), and --strict / CI=true makes it a build failure here instead.
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONV = HERE.parent.parent                      # convertion/
BUILD = CONV / "build" / "agents"
DEST = HERE / "toolchain"

# family -> (source in the verified build, scripts that must exist afterwards)
FAMILIES = {
    "docx": ("docx/code-tree", ["scripts/accept_changes.py", "scripts/office/validate.py"]),
    "pptx": ("pptx/code-tree", ["scripts/thumbnail.py", "scripts/office/validate.py"]),
    "xlsx": ("xlsx/code-tree", ["scripts/recalc.py", "scripts/office/validate.py"]),
    "pdf": ("pdf/code-tree", []),
}


def main() -> int:
    strict = "--strict" in sys.argv or os.environ.get("CI", "").lower() == "true"
    missing_src, missing_entry, staged = [], [], []
    for family, (rel, entries) in FAMILIES.items():
        src = BUILD / rel
        if not src.is_dir() or not any(src.iterdir()):
            missing_src.append(f"{family} ({BUILD / rel})")
            continue
        dest = DEST / family
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(src, dest, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        for e in entries:
            if not (dest / e).is_file():
                missing_entry.append(f"{family}/{e}")
        staged.append(f"{family} <- build/agents/{rel}")

    for line in staged:
        print("staged ", line)
    if missing_src:
        print(f"MISSING verified sources for: {', '.join(missing_src)} — run "
              f"scripts/convert_skills.py + scripts/verify_conversion.py first",
              file=sys.stderr)
        return 1
    if missing_entry:
        print(f"{'ERROR' if strict else 'note'}: script not in the verified "
              f"source: {', '.join(missing_entry)} — the matching endpoint "
              f"answers 501 until it is staged", file=sys.stderr)
        return 1 if strict else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
