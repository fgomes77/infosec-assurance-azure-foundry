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

import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "scripts" / "generate_reports_v2.py"
TEMPLATE = HERE / "assets" / "Group_CISO_Report_Template_v3_1.pptx"


def main(data: str, outdir: str) -> int:
    if not SCRIPT.exists() or not TEMPLATE.exists():
        print(f"FAIL - staged sources missing: {SCRIPT.exists()=} {TEMPLATE.exists()=}", file=sys.stderr)
        return 2
    env = {**os.environ, "PYTHONUNBUFFERED": "1"}
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
