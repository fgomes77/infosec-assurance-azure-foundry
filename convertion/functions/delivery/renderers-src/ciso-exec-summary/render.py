#!/usr/bin/env python3
"""ciso-executive-summary renderer wrapper (Steps 6-7: HTML -> A3 PDF and
section PNGs -> PPTX), run in the Function because code_interpreter has
neither Chromium nor Node.

Usage: render.py <data.json> <outdir>

data.json: { "html": "<finished single-file dashboard>", "vendor": str,
             "assessment": str, "baseName": str? }

Steps (all from the staged ciso-executive-summary-scripts.zip):
  1. <outdir>/<base>_CISO_ExecSummary.html   <- data.html verbatim
  2. scripts/html_to_pdf.py html pdf          (verbatim, A3 landscape)
  3. render_sections.py                        executed with HTML_PATH/OUT_DIR
     rebound (same SECTIONS clip table: s3..s6 PNG + full_page.png)
  4. generate_pptx_template.js                 executed with VENDOR /
     ASSESSMENT / IMG_DIR / OUT rebound        -> <base>_CISO_TPRM_Governance.pptx
The rebinding is done on an in-memory copy of each script (regex on the
constant assignments); the staged files are never modified.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE / "scripts"


def _rebind(src: str, pairs: dict[str, str]) -> str:
    for name, value in pairs.items():
        src, n = re.subn(rf'^(\s*(?:const|let|var)?\s*{re.escape(name)}\s*=\s*)(?:"[^"]*"|\'[^\']*\')',
                         lambda m: m.group(1) + json.dumps(value), src, count=1, flags=re.M)
        if n != 1:
            raise RuntimeError(f"could not rebind {name} in staged script")
    return src


def main(data_path: str, outdir: str) -> int:
    d = json.loads(Path(data_path).read_text(encoding="utf-8"))
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    base = re.sub(r"[^A-Za-z0-9]+", "", d.get("baseName") or d.get("vendor", "Vendor")) or "Vendor"
    html = out / f"{base}_CISO_ExecSummary.html"
    pdf = out / f"{base}_CISO_ExecSummary.pdf"
    pptx = out / f"{base}_CISO_TPRM_Governance.pptx"
    html.write_text(d["html"], encoding="utf-8")

    subprocess.run([sys.executable, str(SCRIPTS / "html_to_pdf.py"), str(html), str(pdf)], check=True, timeout=300)

    with tempfile.TemporaryDirectory() as td:
        img_dir = Path(td) / "pptx_sections"
        rs = _rebind((SCRIPTS / "render_sections.py").read_text(encoding="utf-8"),
                     {"HTML_PATH": str(html), "OUT_DIR": str(img_dir)})
        rs_path = Path(td) / "render_sections.py"
        rs_path.write_text(rs, encoding="utf-8")
        subprocess.run([sys.executable, str(rs_path)], check=True, timeout=300, cwd=td)

        js = _rebind((SCRIPTS / "generate_pptx_template.js").read_text(encoding="utf-8"),
                     {"VENDOR": d.get("vendor", ""), "ASSESSMENT": d.get("assessment", ""),
                      "IMG_DIR": str(img_dir), "OUT": str(pptx)})
        js_path = Path(td) / "generate_pptx_template.js"
        js_path.write_text(js, encoding="utf-8")
        subprocess.run(["node", str(js_path)], check=True, timeout=300, cwd=td,
                       env={**os.environ, "NODE_PATH": str(HERE / "node_modules")})
        for png in sorted(img_dir.glob("*.png")):
            (out / f"{base}_{png.name}").write_bytes(png.read_bytes())
    print("PRODUCED:", ", ".join(sorted(p.name for p in out.iterdir())))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
