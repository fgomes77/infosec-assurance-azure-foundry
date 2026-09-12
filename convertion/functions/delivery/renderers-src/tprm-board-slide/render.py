#!/usr/bin/env python3
"""tprm-board-slide renderer wrapper (tprm-slide-generator /
pptx-executive-summary-ciso Steps 2-3, run here instead of code_interpreter
because the radar PNG cannot be handed from the agent to a Node script).

Usage: render.py <tprm_data.json> <out.pptx>

    python3 scripts/generate_radar.py --data <tprm_data.json> --output <radar.png>
    node scripts/generate_slide.js --data <tprm_data.json> --radar <radar.png> --out <out.pptx>

Both scripts are the byte-verified originals; Step 1 (extract_pdf.py) stays
in the agent, which emits the verified tprm_data.json contract.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RADAR = HERE / "scripts" / "generate_radar.py"
SLIDE = HERE / "scripts" / "generate_slide.js"


def main(data: str, out: str) -> int:
    if not RADAR.exists() or not SLIDE.exists():
        print("FAIL - staged scripts missing", file=sys.stderr)
        return 2
    radar_png = Path(out).with_suffix(".radar.png")
    subprocess.run([sys.executable, str(RADAR), "--data", data, "--output", str(radar_png)], cwd=str(HERE / "scripts"), check=True, timeout=300)
    env_path = HERE / "node_modules"
    subprocess.run(["node", str(SLIDE), "--data", data, "--radar", str(radar_png), "--out", out],
                   cwd=str(HERE / "scripts"), check=True, timeout=300,
                   env={"NODE_PATH": str(env_path), "PATH": "/usr/local/bin:/usr/bin:/bin"})
    radar_png.unlink(missing_ok=True)
    print("OK", out)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
