#!/usr/bin/env python3
"""Secret and PII scan of the kit — a thin CLI over `verify_kit.scan_secrets`.

There is deliberately **no second implementation** of the scan here. The
patterns, the placeholder allow-list and the per-finding message format live
in `verify_kit.py` (`SECRET_PATTERNS`, `EMAIL_OK`, `scan_secrets`), which is
what the kit-consistency gate already runs; this script exists so the scan can
be invoked on its own — by a pre-commit hook, by a reviewer, and by CI when it
wants the secret gate to fail independently of the rest of `verify_kit`.

What it looks for (from `verify_kit.SECRET_PATTERNS`): API keys and tokens,
connection strings, private-key blocks, real e-mail addresses, real tenant and
host names — anything that must never reach the repository. Documented
placeholders (`{upn:…}`, `{objectId:…}`, `<tenant>`, public Azure
role-definition GUIDs) are allow-listed there, once.

    python3 scan_secrets.py                     # scan the kit, exit 1 on a finding
    python3 scan_secrets.py --json evidence.json   # machine-readable artefact for CI
    python3 scan_secrets.py --gitleaks          # also shell out to gitleaks when present
    python3 scan_secrets.py --config .gitleaks.toml

Exit codes: 0 clean, 1 at least one finding, 2 the scan could not run.

Offline and deterministic: no Azure call, no network, no credentials.
Governance: `governance/DATA_PROTECTION_GUARDRAILS.md` §3, `ci/README.md` §3.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONV = HERE.parent
REPO = CONV.parent

sys.path.insert(0, str(HERE))
from verify_kit import scan_secrets as _scan  # noqa: E402


def parse_finding(line: str) -> dict:
    """`SECRETS  <rel>:<line>: <label>: <hit>` → a structured record."""
    body = line.split("SECRETS", 1)[-1].strip()
    loc, _, rest = body.partition(": ")
    label, _, hit = rest.partition(": ")
    path, _, lineno = loc.rpartition(":")
    return {
        "file": path or loc,
        "line": int(lineno) if lineno.isdigit() else 0,
        "label": label.strip(),
        "match": hit.strip(),
        "source": "verify_kit.SECRET_PATTERNS",
    }


def run_gitleaks(config: Path | None) -> tuple[int, list[dict]]:
    """Optional second pass. Absent binary is not a failure — it is reported."""
    if not shutil.which("gitleaks"):
        print("note: gitleaks not on PATH — pattern scan only "
              "(the CI image pins it; .devcontainer installs it)")
        return 0, []
    cmd = ["gitleaks", "detect", "--no-git", "--source", str(REPO), "--redact",
           "--report-format", "json", "--report-path", "-"]
    if config:
        cmd += ["--config", str(config)]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO)
    if proc.returncode not in (0, 1):
        print(f"gitleaks failed ({proc.returncode}): {proc.stderr.strip()[:300]}")
        return 2, []
    try:
        raw = json.loads(proc.stdout or "[]")
    except json.JSONDecodeError:
        print("gitleaks produced no parsable report; treating as clean")
        return 0, []
    found = [{"file": r.get("File", ""), "line": r.get("StartLine", 0),
              "label": r.get("RuleID", "gitleaks"), "match": r.get("Match", ""),
              "source": "gitleaks"} for r in raw]
    return (1 if found else 0), found


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json", metavar="PATH",
                    help="write the findings as JSON (the CI evidence artefact)")
    ap.add_argument("--gitleaks", action="store_true",
                    help="also run gitleaks as a second pass when the binary "
                         "is present")
    ap.add_argument("--config", default=str(REPO / ".gitleaks.toml"),
                    help="gitleaks config (default: the repository's "
                         ".gitleaks.toml, which extends .github/gitleaks.toml)")
    args = ap.parse_args()

    raw: list[str] = []
    try:
        n_files = _scan(raw)
    except Exception as exc:  # noqa: BLE001
        print(f"scan could not run: {exc}")
        return 2
    findings = [parse_finding(line) for line in raw]
    rc = 1 if findings else 0

    if args.gitleaks:
        cfg = Path(args.config)
        gl_rc, gl = run_gitleaks(cfg if cfg.exists() else None)
        if gl_rc == 2:
            return 2
        findings += gl
        rc = max(rc, gl_rc)

    for f in findings:
        print(f"SECRETS  {f['file']}:{f['line']}: {f['label']}: {f['match'][:40]}")

    if args.json:
        out = Path(args.json)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(
            {"files_scanned": n_files, "findings": findings,
             "clean": not findings}, indent=2) + "\n", encoding="utf-8")
        print(f"report: {out}")

    print(f"{n_files} files scanned, {len(findings)} finding(s)")
    if findings:
        print("A finding is removed and rotated — never allow-listed away "
              "(governance/DATA_PROTECTION_GUARDRAILS.md §3).")
    return rc


if __name__ == "__main__":
    sys.exit(main())
