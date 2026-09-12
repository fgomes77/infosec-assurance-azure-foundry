#!/usr/bin/env python3
"""form-b-fill renderer wrapper (onetrust-form-b Steps 7/8).

Usage: render.py <answers.json> <out.xlsx> <original_form_b.xlsx>

answers.json = the human-approved answer set the agent emitted:
  { "sheet": "Assessment Responses - v2"?,          # optional override
    "answers": { "<QID>": {"response": str, "justification": str}, ... } }
(or the bare {"<QID>": {...}} map). Runs the byte-verified fill_form_b.py,
which edits ONLY the Response/Justification columns of the round-trip file
and validates single-select answers against the option ladder. Any
"VALIDATION WARNINGS" or "WARNING -" line on stdout FAILS the render, so an
unvalidated workbook never reaches Reports/<Supplier>/<Service>/.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "scripts" / "fill_form_b.py"


def main(answers_path: str, out: str, original: str) -> int:
    if not SCRIPT.exists():
        print("FAIL - fill_form_b.py not staged", file=sys.stderr)
        return 2
    if not original or not Path(original).exists():
        print("FAIL - original Form B xlsx input missing (render body inputFileId/inputDriveId+inputItemId/inputContentBase64)", file=sys.stderr)
        return 2
    payload = json.loads(Path(answers_path).read_text(encoding="utf-8"))
    sheet = payload.get("sheet") if isinstance(payload, dict) else None
    answers = payload.get("answers", payload) if isinstance(payload, dict) else payload
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as fh:
        json.dump(answers, fh, ensure_ascii=False)
        ans = fh.name
    cmd = [sys.executable, str(SCRIPT), "--xlsx", original, "--answers", ans, "--out", out]
    if sheet:
        cmd += ["--sheet", sheet]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    sys.stdout.write(p.stdout)
    sys.stderr.write(p.stderr)
    if p.returncode != 0:
        return p.returncode
    if "VALIDATION WARNINGS" in p.stdout or "WARNING -" in p.stdout:
        print("FAIL - fill_form_b.py reported validation warnings; fix the answer set (verifier rule: responses must be verbatim option strings)")
        return 5
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else ""))
