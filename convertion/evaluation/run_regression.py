#!/usr/bin/env python3
"""Template regression run — every registered template against its own sample.

`templates/registry.json` and `templates/README.md` both name this script as
the consumer of `templates/samples/`. It is the offline half of the template
change control (`operations/LIFECYCLE.md`, `agents/template-manager_instructions.md`):
before a template change is approved, every template still has to accept its
own sanitised dataset and still has to pass its own quality gate.

Per registered template, in this order:

  1. sample     the `sample` file exists and parses
  2. schema     when the template declares one, the sample validates against it
                (the same jsonschema gate `/api/render` applies)
  3. gate       when `functions/delivery/gates.GATES` has an entry:
                  - a `data` gate runs on the sample payload
                  - an `html` gate runs on the template asset FILLED with the
                    sample (`{{PLACEHOLDER}}` substitution), which is what the
                    agent produces and what the gate is written against
  4. render     only with `--render`: the staged renderer is executed on the
                sample in a temp dir and must produce a non-empty file. Skipped
                with a stated reason when its runtime is absent (no Node, no
                python-docx, …) — a missing local toolchain is never a failure
                of the template.

Offline and deterministic: no Azure call, no credentials, no network.

    python3 evaluation/run_regression.py                 # contract + gates
    python3 evaluation/run_regression.py --render        # also run renderers
    python3 evaluation/run_regression.py --only dpia-dpo-docx
    python3 evaluation/run_regression.py --json build/regression.json

Exit 0 = every template passed; exit 1 = at least one failed (the report names
the template and the check). A template with no sample is a failure: the
registry says one exists.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONV = HERE.parent
REPO = CONV.parent
REGISTRY = CONV / "templates" / "registry.json"
SCHEMA_DIR = CONV / "templates"
ASSETS = CONV / "templates" / "assets"
RENDERERS = CONV / "functions" / "delivery" / "renderers"

sys.path.insert(0, str(CONV / "functions" / "delivery"))

_PLACEHOLDER = re.compile(r"\{\{([A-Z0-9_]+)\}\}")

# Template id -> the HTML asset an `html` gate is written against. The gate
# checks the finished document, so the asset is filled with the sample first.
HTML_ASSETS = {
    "deepsearch-html-dashboard": ASSETS / "deepsearch-dashboard.html",
    "tpsrca-report": ASSETS / "tpsrca-report.html",
}


def fill(html: str, data: dict) -> tuple[str, list[str]]:
    """Substitute {{TOKEN}} from the sample. Returns (filled, unfilled tokens).

    Lists and objects are JSON-encoded, which is what the dashboards' inline
    scripts consume (SPIDER_SCORES and friends are arrays)."""
    missing: list[str] = []

    def one(m: re.Match) -> str:
        key = m.group(1)
        if key not in data:
            missing.append(key)
            return m.group(0)
        v = data[key]
        return json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else str(v)

    return _PLACEHOLDER.sub(one, html), sorted(set(missing))


def check_schema(t: dict, data, fails: list[str]) -> str:
    name = t.get("schema")
    if not name:
        return "no schema declared"
    path = SCHEMA_DIR / name
    if not path.exists():
        fails.append(f"declared schema {name} is missing")
        return "MISSING"
    try:
        import jsonschema
    except ImportError:
        return "skipped (jsonschema not installed)"
    try:
        jsonschema.validate(data, json.loads(path.read_text(encoding="utf-8")))
    except jsonschema.ValidationError as e:
        loc = "/".join(map(str, e.absolute_path)) or "<root>"
        fails.append(f"sample does not match {name} at {loc}: {e.message}")
        return "FAIL"
    except jsonschema.SchemaError as e:
        fails.append(f"schema {name} is invalid: {e.message}")
        return "FAIL"
    return f"ok ({name})"


def check_gate(tid: str, data, fails: list[str]) -> str:
    try:
        import gates
    except ImportError as e:
        return f"skipped (gates.py not importable: {e})"
    entry = gates.GATES.get(tid)
    if not entry:
        return "no gate"
    kind, fn = entry
    if kind == "data":
        bad = fn(data)
        if bad:
            fails.extend(f"gate: {b}" for b in bad)
            return "FAIL"
        return "ok (data gate)"
    asset = HTML_ASSETS.get(tid)
    if not asset or not asset.exists():
        return "skipped (no HTML asset to fill)"
    filled, missing = fill(asset.read_text(encoding="utf-8"), data)
    if missing:
        fails.append(f"sample has no value for {len(missing)} placeholder(s): "
                     f"{', '.join(missing[:8])}{' …' if len(missing) > 8 else ''}")
    bad = fn(filled)
    if bad:
        fails.extend(f"gate: {b}" for b in bad)
    return "FAIL" if (bad or missing) else "ok (html gate on the filled asset)"


def check_render(t: dict, sample: Path, fails: list[str]) -> str:
    rel = t.get("renderer")
    if not rel:
        return "no renderer"
    entry = CONV / rel
    d = entry.parent
    if not entry.exists():
        fails.append(f"renderer {rel} is not staged (run scripts/stage_renderers.py)")
        return "MISSING"
    mf_path = d / "manifest.json"
    mf = json.loads(mf_path.read_text(encoding="utf-8")) if mf_path.exists() else {}
    runtime = mf.get("runtime", "node" if entry.suffix == ".js" else "python")
    exe = {"python": "python3", "node": "node", "bash": "bash"}.get(runtime)
    if not exe or not shutil.which(exe):
        return f"skipped (no {runtime} runtime here)"
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        out = tdp / ("out." + (t.get("format") or "bin"))
        argv = [a.replace("{data}", str(sample)).replace("{out}", str(out))
                .replace("{outdir}", str(tdp)).replace("{renderer}", str(d))
                for a in mf.get("argv", ["{data}", "{out}"])]
        if any("{" in a and "}" in a for a in argv):
            return "skipped (renderer needs an input this run cannot supply)"
        try:
            p = subprocess.run([exe, str(entry)] + argv, cwd=str(d),
                               capture_output=True, timeout=300)
        except (subprocess.TimeoutExpired, OSError) as e:
            fails.append(f"renderer failed to start: {e}")
            return "FAIL"
        if p.returncode != 0:
            err = p.stderr.decode(errors="replace")
            out_txt = p.stdout.decode(errors="replace")
            tail = err.strip().splitlines()[-3:] or out_txt.strip().splitlines()[-3:]
            # A runtime this machine does not have is not a template defect.
            # The delivery image ships all of them; a laptop and a CI runner do
            # not, and a regression run that goes red for a missing Chromium
            # teaches people to ignore it.
            ABSENT = ("ModuleNotFoundError", "Cannot find module",
                      "Playwright unavailable", "staged sources missing",
                      "executable doesn't exist", "soffice", "libreoffice")
            hay = err + out_txt
            hit = next((m for m in ABSENT if m.lower() in hay.lower()), None)
            if hit:
                return f"skipped (runtime not available here: {hit})"
            fails.append("renderer exited %d: %s" % (p.returncode, " | ".join(tail)))
            return "FAIL"
        produced = [f for f in tdp.rglob("*") if f.is_file() and f.stat().st_size > 0]
        if not produced:
            fails.append("renderer produced no non-empty file")
            return "FAIL"
        return f"ok ({len(produced)} file(s))"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--only", help="one template id")
    ap.add_argument("--render", action="store_true",
                    help="also execute each staged renderer on its sample")
    ap.add_argument("--json", metavar="PATH", help="write the report as JSON")
    args = ap.parse_args()

    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    templates = [t for t in reg["templates"]
                 if not args.only or t["id"] == args.only]
    if args.only and not templates:
        raise SystemExit(f"unknown template id {args.only!r}")

    report, failed = [], 0
    for t in templates:
        tid = t["id"]
        fails: list[str] = []
        row = {"template": tid, "version": t.get("version")}
        sample_rel = t.get("sample")
        if not sample_rel:
            fails.append("registry declares no sample")
            sample = None
        else:
            sample = REPO / sample_rel
            if not sample.exists():
                fails.append(f"sample {sample_rel} does not exist")
                sample = None
        data = None
        if sample is not None:
            try:
                data = json.loads(sample.read_text(encoding="utf-8"))
                row["sample"] = "ok"
            except json.JSONDecodeError as e:
                fails.append(f"sample is not valid JSON: {e}")
        if data is not None:
            row["schema"] = check_schema(t, data, fails)
            row["gate"] = check_gate(tid, data, fails)
            if args.render:
                row["render"] = check_render(t, sample, fails)
        row["status"] = "FAIL" if fails else "pass"
        row["failures"] = fails
        # A template of record can only be changed through an approval run
        # (scripts/update_templates.py), so a defect found here is RECORDED in
        # the registry entry's `notes` rather than patched. Surfacing that here
        # keeps the run honest — it still fails — while telling the reader the
        # failure is already on the books and what the approved fix is.
        if fails and t.get("notes"):
            row["recorded_note"] = t["notes"]
        failed += bool(fails)
        report.append(row)

    width = max(len(r["template"]) for r in report)
    for r in report:
        mark = "FAIL" if r["failures"] else "pass"
        detail = " · ".join(f"{k}={r[k]}" for k in ("sample", "schema", "gate", "render")
                            if k in r)
        print(f"{mark:4}  {r['template']:{width}}  {detail}")
        for f in r["failures"]:
            print(f"        - {f}")
        if r.get("recorded_note"):
            print(f"        note (templates/registry.json): {r['recorded_note'][:300]}…"
                  if len(r["recorded_note"]) > 300 else
                  f"        note (templates/registry.json): {r['recorded_note']}")

    print(f"\n{len(report)} template(s), {len(report) - failed} passed, {failed} failed")
    if args.json:
        out = Path(args.json)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({"templates": report, "failed": failed},
                                  indent=2) + "\n", encoding="utf-8")
        print(f"report: {out}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
