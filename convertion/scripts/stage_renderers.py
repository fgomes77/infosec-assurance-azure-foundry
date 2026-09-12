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
    # renderers-src first: the runnable Python ports of generators the
    # verified code-tree carries in a form the Function cannot execute
    # (dpia: Node `docx`; ciso-reporting: generate_reports_v2.py needs the
    # skill's own layout). The code-tree stays the visual reference.
    "dpia": ["functions/delivery/renderers-src/dpia",
             "build/agents/dpia/code-tree"],
    "ciso-reporting": ["functions/delivery/renderers-src/ciso-reporting",
                       "build/agents/ciso-reporting/code-tree"],
    "ciso-global": ["functions/delivery/renderers-src/ciso-global"],
    "evidence-summary": ["functions/delivery/renderers-src/evidence-summary"],
    "xlsx-generic": ["functions/delivery/renderers-src/xlsx-generic",
                     "build/agents/xlsx/code-tree"],
    "docx-generic": ["functions/delivery/renderers-src/docx-generic"],
    "pptx-generic": ["functions/delivery/renderers-src/pptx-generic"],
    # Renderers the Function reaches by template name or through a dedicated
    # endpoint. They have no `renderer` field in templates/registry.json (or
    # none yet), so `wanted` would never name them and they answered 404/501
    # at runtime. ALWAYS_STAGE below adds them.
    "charts": ["functions/delivery/renderers-src/charts"],
    "diagrams": ["functions/delivery/renderers-src/diagrams"],
    "transcript": ["functions/delivery/renderers-src/transcript"],
    "form-b-fill": ["functions/delivery/renderers-src/form-b-fill",
                    "build/agents/onetrust-form-b/code"],
    # whisperx and pdf-coverage are endpoint-only: function_app.py calls
    # _renderer_dir("whisperx") and _renderer_dir("pdf-coverage") directly.
    # Their manifest entries point into scripts/ on purpose — the
    # byte-verified layout — so they need the *-scripts.zip from
    # build/agents/<skill>/code/ beside them for _materialise to unpack.
    "whisperx": ["functions/delivery/renderers-src/whisperx",
                 "build/agents/whisperx-transcribe-diarize/code"],
    "pdf-coverage": ["functions/delivery/renderers-src/pdf-coverage",
                     "build/agents/pdf-full-coverage-analyzer/code"],
    "ciso-exec-summary": ["functions/delivery/renderers-src/ciso-exec-summary",
                          "build/agents/ciso-executive-summary/code-tree"],
    "tprm-board-slide": ["functions/delivery/renderers-src/tprm-board-slide",
                         "build/agents/pptx-executive-summary-ciso/code-tree"],
}

# Staged whether or not templates/registry.json names them in a `renderer`
# field. Everything else in SOURCES is reached through a registered template.
ALWAYS_STAGE = {"charts", "diagrams", "transcript", "form-b-fill",
                "whisperx", "pdf-coverage", "ciso-exec-summary",
                "tprm-board-slide"}

# The entry every renderer exposes at its root, unless its manifest says
# otherwise. whisperx and pdf-coverage deliberately keep their entries under
# scripts/ (byte-verified layout) and are invoked by their endpoints, not by
# the generic render path, so they are not given a root entry here.
DEFAULT_ENTRY = {"charts": "render.py", "diagrams": "generate_slide.js",
                 "transcript": "render.py", "form-b-fill": "render.py",
                 "ciso-exec-summary": "render.py",
                 "tprm-board-slide": "render.py"}
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
    for name in ALWAYS_STAGE:
        wanted.setdefault(name, DEFAULT_ENTRY.get(name, ""))
    staged, missing, no_entry = [], [], []
    for name, entry in sorted(wanted.items()):
        cands = [c for c in SOURCES.get(name, [])
                 if (CONV / c).is_dir() and any((CONV / c).iterdir())]
        if not cands:
            missing.append(name)
            continue
        dest = DEST / name
        if dest.exists():
            shutil.rmtree(dest)
        # The first source wins per file; later sources only ADD what the
        # first did not provide (the byte-verified *-scripts.zip and the
        # assets a runnable port needs beside it). A runnable port is never
        # overwritten by the code-tree it was ported from.
        for cand in cands:
            shutil.copytree(CONV / cand, dest, dirs_exist_ok=True,
                            ignore=shutil.ignore_patterns("__pycache__"))
        state = ensure_entry(dest, entry) if entry else "endpoint-only"
        staged.append(f"{name} <- {' + '.join(cands)} [{entry or '-'}: {state}]")
        if state == "missing":
            no_entry.append(f"{name}/{entry}")
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
