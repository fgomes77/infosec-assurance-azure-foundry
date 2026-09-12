#!/usr/bin/env python3
"""ciso-reporting renderer wrapper (requirement c: Cyber Forum deck).

Usage: render.py <data.json> <outdir>

Runs the byte-verified orchestrator exactly as on claude.ai:
    python3 scripts/generate_reports_v2.py --assessment data.json \
        --template assets/Group_CISO_Report_Template_v3_1.pptx --outdir <outdir>
and produces ALL THREE deliverables (HTML dashboard, A3 landscape PDF,
8-slide PPTX) plus the spider PNG. The Function's manifest gate requires
"PASS - zero unsubstituted tokens" on stdout, i.e. the script's own QA line
becomes a hard gate instead of a printed note. `data.json` must be the
verified assessment JSON (assets/assessment_schema_example.json shape);
the Function already extracted it from the agent's fenced block.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "scripts" / "generate_reports_v2.py"
TEMPLATE = HERE / "assets" / "Group_CISO_Report_Template_v3_1.pptx"


def _strip_doc_keys(path: str, td: str) -> str:
    """Drop top-level keys beginning with '_' before handing the payload over.

    `generate_reports_v2.py` builds its dataclass with `Assessment(**d)`, so any
    key it does not declare is a TypeError. Underscore-prefixed keys are this
    kit's documentation convention — every file in templates/samples/ carries
    `_sample_note`, and registry/config files use the same rule — so a
    contract-correct sample crashed the verified script. Stripping them here,
    in the wrapper, keeps `generate_reports_v2.py` byte-identical to the
    claude.ai original, which is the whole point of the wrapper.
    """
    try:
        d = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return path                       # let the verified script report it
    if not isinstance(d, dict) or not any(k.startswith("_") for k in d):
        return path
    clean = Path(td) / "assessment.json"
    clean.write_text(json.dumps({k: v for k, v in d.items()
                                 if not k.startswith("_")}, ensure_ascii=False),
                     encoding="utf-8")
    return str(clean)


def main(data: str, outdir: str) -> int:
    if not SCRIPT.exists() or not TEMPLATE.exists():
        print(f"FAIL - staged sources missing: {SCRIPT.exists()=} {TEMPLATE.exists()=}", file=sys.stderr)
        return 2
    env = {**os.environ, "PYTHONUNBUFFERED": "1"}
    with tempfile.TemporaryDirectory() as td:
        data = _strip_doc_keys(data, td)
        p = subprocess.run([sys.executable, str(SCRIPT), "--assessment", data, "--template", str(TEMPLATE),
                            "--outdir", outdir], cwd=str(HERE), env=env, capture_output=True, text=True, timeout=800)
    sys.stdout.write(p.stdout)
    sys.stderr.write(p.stderr)
    if p.returncode != 0:
        return p.returncode
    if "[skip] playwright" in p.stdout:
        print("FAIL - Playwright unavailable: PDF/spider skipped (container must ship Chromium)")
        return 3
    produced = sorted(f.name for f in Path(outdir).iterdir())
    print("PRODUCED:", ", ".join(produced))
    missing = [ext for ext in (".html", ".pdf", ".pptx") if not any(n.endswith(ext) for n in produced)]
    if missing:
        print(f"FAIL - deliverables missing: {missing}")
        return 4
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
