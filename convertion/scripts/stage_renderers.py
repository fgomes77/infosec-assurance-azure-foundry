#!/usr/bin/env python3
"""Stage the byte-verified report generators into the delivery Function's
renderers/ folder (functions/delivery/renderers/<template>/), per the
`renderer` fields in templates/registry.json.

Run AFTER convert_skills.py + verify_conversion.py — staging only ever
copies out of the verified build (build/agents/<n>/code-tree/, ORIGINAL
layout so ../assets/ requires and --template paths resolve), which is
what keeps rendered files identical to the previous claude.ai environment.
Re-run after any approved template update (update_templates.py calls it
automatically).

The Function calls renderers/<template>/render.py (docx/xlsx) or
generate_slide.js (pptx) - the entry named in templates/registry.json. When
the verified tree keeps that entry under scripts/, a one-line shim is
written at the renderer root; when no entry exists at all, the template
is reported (exit 1 under CI=true / --strict, else a note) so a missing
renderer never fails silently.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONV = HERE.parent
BUILD = CONV / "build"
DEST = CONV / "functions" / "delivery" / "renderers"

# renderer folder -> source(s) in the verified build (first match wins)
SOURCES = {
    "dpia": ["build/agents/dpia/code-tree"],
    "ciso-reporting": ["build/agents/ciso-reporting/code-tree"],
    "ciso-global": ["functions/delivery/renderers-src/ciso-global"],
    "evidence-summary": ["functions/delivery/renderers-src/evidence-summary"],
    "xlsx-generic": ["functions/delivery/renderers-src/xlsx-generic",
                     "build/agents/xlsx/code-tree"],
    "docx-generic": ["functions/delivery/renderers-src/docx-generic"],
    "pptx-generic": ["functions/delivery/renderers-src/pptx-generic"],
}
SHIMS = {
    ".js": "#!/usr/bin/env node\n// staged shim: entry lives in scripts/ (verified layout)\n"
           "require(require('path').join(__dirname, 'scripts', '{entry}'));\n",
    ".py": "#!/usr/bin/env python3\n# staged shim: entry lives in scripts/ (verified layout)\n"
           "import os, runpy, sys\n"
           "runpy.run_path(os.path.join(os.path.dirname(__file__), 'scripts', '{entry}'), "
           "run_name='__main__')\n",
}


def ensure_entry(dest: Path, entry: str) -> str:
    """Return 'ok' | 'shim' | 'missing' for the registry entry file."""
    if (dest / entry).is_file():
        return "ok"
    if (dest / "scripts" / entry).is_file() and Path(entry).suffix in SHIMS:
        (dest / entry).write_text(SHIMS[Path(entry).suffix].format(entry=entry),
                                  encoding="utf-8")
        return "shim"
    return "missing"


def main() -> int:
    reg = json.loads((CONV / "templates" / "registry.json")
                     .read_text(encoding="utf-8"))
    strict = "--strict" in sys.argv or os.environ.get("CI", "").lower() == "true"
    wanted = {Path(t["renderer"]).parent.name: Path(t["renderer"]).name
              for t in reg["templates"] if t.get("renderer")}
    staged, missing, no_entry = [], [], []
    for name, entry in sorted(wanted.items()):
        for cand in SOURCES.get(name, []):
            src = CONV / cand
            if src.is_dir() and any(src.iterdir()):
                dest = DEST / name
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(src, dest, ignore=shutil.ignore_patterns("__pycache__"))
                state = ensure_entry(dest, entry)
                staged.append(f"{name} <- {cand} [{entry}: {state}]")
                if state == "missing":
                    no_entry.append(f"{name}/{entry}")
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
    if no_entry:
        print(f"{'ERROR' if strict else 'note'}: renderer entry not in the "
              f"verified source: {', '.join(no_entry)} — fix the 'renderer' "
              f"path in templates/registry.json or add the renderer under "
              f"functions/delivery/renderers-src/", file=sys.stderr)
        return 1 if strict else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
