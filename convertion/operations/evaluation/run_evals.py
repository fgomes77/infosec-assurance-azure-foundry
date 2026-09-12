#!/usr/bin/env python3
"""Run the evaluation golden set against the InfoSec Assurance Foundry agents.

Implements the gates of operations/evaluation/EVALUATION.md (G0 offline in CI,
G1 before any model / tier / prompt / template change, G3 monthly M1) and the
accuracy-floor test of operations/TOKEN_ECONOMY_PLAYBOOK.md §7.

Modes
    --dry-run            offline: validates the golden set against the schema
                         and runs every deterministic check on each case's
                         synthetic `fixture` (no Azure, no network). Used by CI.
    --candidates DIR     offline: checks real outputs you downloaded from a run
                         (DIR/<case-id>.{html,json,md,txt}, optional
                         DIR/<case-id>.verdict.txt and DIR/<case-id>.usage.json).
    (default)            live: needs PROJECT_ENDPOINT (setup/.env) and
                         azure-ai-projects; sends each case to its agent, then
                         report drafts to `output-verifier`, records tokens and
                         latency, runs the same checks. Never approves a gate,
                         never renders or stores anything: the run stops at the
                         verifier (EVALUATION.md §3).
    --model-override D   live only: evaluate a CANDIDATE deployment without
                         touching production — each producing agent is cloned
                         as <agent>-eval with the model swapped and deleted at
                         the end (needs Azure AI Developer: owner PIM window L1).

Usage
    python3 run_evals.py --dry-run
    python3 run_evals.py --dry-run --golden golden-set.example.json --only a-deepsearch-public-domain
    python3 run_evals.py --candidates build/evals/downloads --out build/evals/2026-09
    python3 run_evals.py --only g-dora-art30-provisions,h-advisor-tprm-lifecycle
    python3 run_evals.py --only b-dpia-synthetic-onetrust-pdf --model-override gpt-4o-mini

Output: <out>/eval-report.json and <out>/eval-report.md (attach both to the PR
or file under Governance/Operations/{yyyy}-{mm}/). Exit code 1 when any case
fails or any aggregate metric is below its floor; skipped cases do not fail
the run unless --strict.

Identity: DefaultAzureCredential (az login) — no keys. Reading agents and
running threads needs `Azure AI User`; cloning needs `Azure AI Developer`.
Controls: ISO 42001 A.6.2.4, A.8.4; ISO 27001:2022 A.8.29; EU AI Act
Art. 9(6)–(8); DORA Art. 9(4)(e).
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONV = HERE.parent.parent
try:
    from dotenv import load_dotenv
    load_dotenv(CONV / "setup" / ".env")
except ImportError:
    pass  # plain environment variables still work

SCHEMA_PATH = HERE / "golden-set.schema.json"
DEFAULT_GOLDEN = HERE / "golden-set.example.json"

REQUIREMENTS = {"a", "b", "c", "d", "d2", "e", "f", "g", "h", "i", "j", "verifier"}
KINDS = {"report", "advisory", "routing", "verifier-negative"}
TIERS = {"light", "chat", "reasoning"}
FORMATS = {"html", "json", "text", "markdown", "verifier"}
METRICS = ["verifier_first_pass", "structure_fidelity", "placeholder_free",
           "threshold_exactness", "grounding_rate", "citation_validity",
           "egress_clean", "budget_ok"]
DEFAULT_FLOORS = {"verifier_first_pass": 1.0, "structure_fidelity": 1.0,
                  "placeholder_free": 1.0, "threshold_exactness": 1.0,
                  "grounding_rate": 0.9, "citation_validity": 0.95,
                  "egress_clean": 1.0, "budget_ok": 0.9}
# Verifier rule 4 (agents/verifier_instructions.md) as regexes.
DEFAULT_FORBIDDEN = [r"\{\{[A-Za-z0-9_]+\}\}", r"\bTBD\b", r"lorem ipsum", r"\bxxx\b"]
# Egress markers (governance/DATA_PROTECTION_GUARDRAILS.md; kql/egress-detection.kql).
DEFAULT_MARKERS = ["{marker:internal}", "ENX-INTERNAL"]
# Verifier rule 7: a draft is never framed as already submitted.
WRITE_LANGUAGE = [r"\bhas been (created|submitted|uploaded|posted|filed)\b",
                  r"\bticket created\b", r"\bsubmitted successfully\b",
                  r"\bI (have )?(created|submitted|uploaded|posted) (the|a|this)\b"]
# EUR per 1M tokens — placeholders (FINOPS.md §2); override via
# PRICE_EUR_PER_1M_IN / PRICE_EUR_PER_1M_OUT = "name:val,name:val".
PRICE_IN = {"gpt-4o-mini": 0.15, "gpt-4o": 2.50, "o3-mini": 1.10}
PRICE_OUT = {"gpt-4o-mini": 0.60, "gpt-4o": 10.00, "o3-mini": 4.40}
VERIFIER = "output-verifier"


# --------------------------------------------------------------------------- golden set
def _prices_from_env(var: str, base: dict) -> dict:
    raw = os.environ.get(var, "")
    out = dict(base)
    for item in raw.split(","):
        if ":" in item:
            name, val = item.rsplit(":", 1)
            try:
                out[name.strip()] = float(val)
            except ValueError:
                pass
    return out


def load_golden(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def validate_golden(golden: dict) -> list[str]:
    """Structural validation without third-party dependencies; jsonschema is
    used additionally when installed."""
    errors: list[str] = []
    if not isinstance(golden, dict):
        return ["golden set must be a JSON object"]
    if not re.fullmatch(r"[0-9]+\.[0-9]+(\.[0-9]+)?", str(golden.get("version", ""))):
        errors.append("version must look like 1.0 or 1.0.0")
    cases = golden.get("cases")
    if not isinstance(cases, list) or not cases:
        return errors + ["cases must be a non-empty array"]
    for name, val in (golden.get("floors") or {}).items():
        if name not in DEFAULT_FLOORS or not isinstance(val, (int, float)) or not 0 <= val <= 1:
            errors.append(f"floors.{name}: unknown metric or value outside 0..1")
    seen: set[str] = set()
    for i, c in enumerate(cases):
        where = f"cases[{i}]"
        if not isinstance(c, dict):
            errors.append(f"{where}: must be an object")
            continue
        cid = c.get("id", "")
        where = f"case {cid or i}"
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{2,63}", str(cid)):
            errors.append(f"{where}: id must match ^[a-z0-9][a-z0-9-]{{2,63}}$")
        if cid in seen:
            errors.append(f"{where}: duplicate id")
        seen.add(cid)
        for key in ("requirement", "kind", "agent", "tier_of_record", "input", "checks"):
            if key not in c:
                errors.append(f"{where}: missing '{key}'")
        if c.get("requirement") not in REQUIREMENTS:
            errors.append(f"{where}: requirement must be one of {sorted(REQUIREMENTS)}")
        if c.get("kind") not in KINDS:
            errors.append(f"{where}: kind must be one of {sorted(KINDS)}")
        if c.get("tier_of_record") not in TIERS:
            errors.append(f"{where}: tier_of_record must be one of {sorted(TIERS)}")
        if c.get("expected_verdict", "PASS") not in ("PASS", "FAIL"):
            errors.append(f"{where}: expected_verdict must be PASS or FAIL")
        if c.get("kind") == "verifier-negative" and c.get("expected_verdict") != "FAIL":
            errors.append(f"{where}: verifier-negative cases must set expected_verdict FAIL")
        if c.get("kind") == "report" and not c.get("pipeline"):
            errors.append(f"{where}: report cases must name their pipeline")
        inp = c.get("input") or {}
        if not isinstance(inp, dict) or not str(inp.get("prompt", "")).strip():
            errors.append(f"{where}: input.prompt is required")
        for f in (inp.get("files") or []) if isinstance(inp, dict) else []:
            if not isinstance(f, dict) or not f.get("path"):
                errors.append(f"{where}: every input file needs a path")
            elif Path(str(f["path"])).is_absolute() or ".." in Path(str(f["path"])).parts:
                errors.append(f"{where}: input file path must be relative and inside inputs_root")
        checks = c.get("checks") or {}
        if not isinstance(checks, dict):
            errors.append(f"{where}: checks must be an object")
            checks = {}
        if checks.get("output_format", "text") not in FORMATS:
            errors.append(f"{where}: checks.output_format must be one of {sorted(FORMATS)}")
        for key in ("forbidden_patterns",):
            for pat in checks.get(key) or []:
                try:
                    re.compile(pat)
                except re.error as exc:
                    errors.append(f"{where}: {key} '{pat}' is not a valid regex ({exc})")
        if checks.get("citation_pattern"):
            try:
                re.compile(checks["citation_pattern"])
            except re.error as exc:
                errors.append(f"{where}: citation_pattern invalid ({exc})")
        sa = checks.get("score_attribute")
        if sa:
            try:
                if re.compile(sa.get("pattern", "")).groups < 1:
                    errors.append(f"{where}: score_attribute.pattern needs one capture group")
            except re.error as exc:
                errors.append(f"{where}: score_attribute.pattern invalid ({exc})")
        bl = checks.get("baseline")
        if bl and not re.fullmatch(r"[a-f0-9]{64}", str(bl.get("sha256", ""))):
            errors.append(f"{where}: baseline.sha256 must be 64 hex chars")
        for key, val in (c.get("budget") or {}).items():
            if not isinstance(val, (int, float)) or val <= 0:
                errors.append(f"{where}: budget.{key} must be a positive number")
        if c.get("fixture") is not None and not isinstance(c["fixture"], str):
            errors.append(f"{where}: fixture must be a string")
        # Placeholder discipline: no real-looking e-mail addresses in the repo.
        blob = json.dumps(c)
        if re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", blob):
            errors.append(f"{where}: contains an e-mail address — use {{upn:...}} placeholders")
    try:
        import jsonschema  # type: ignore
        with SCHEMA_PATH.open(encoding="utf-8") as fh:
            schema = json.load(fh)
        for err in sorted(jsonschema.Draft202012Validator(schema).iter_errors(golden),
                          key=lambda e: list(e.path)):
            errors.append("schema: " + "/".join(str(p) for p in err.path) + ": " + err.message)
    except ImportError:
        pass
    return errors


# --------------------------------------------------------------------------- checks
def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def parse_json_output(text: str):
    """The agent's JSON draft may be fenced or preceded by a sentence."""
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        pass
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    start, end = text.find("{"), text.rfind("}")
    if 0 <= start < end:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass
    return None


def parse_verdict(text: str) -> str | None:
    m = re.search(r"VERDICT:\s*(PASS|FAIL)", text or "", re.I)
    return m.group(1).upper() if m else None


def _contains(text: str, needle: str) -> bool:
    return needle.lower() in text.lower()


def run_checks(case: dict, text: str, verdict: str | None, usage: dict | None,
               floors: dict) -> tuple[dict, dict]:
    """Return (checks: name -> {ok, evidence}, metrics: name -> value|None)."""
    checks = case.get("checks") or {}
    fmt = checks.get("output_format", "text")
    results: dict[str, dict] = {}
    metrics: dict[str, float | None] = {m: None for m in METRICS}
    low = text.lower()

    def add(name: str, ok: bool, evidence: str) -> None:
        results[name] = {"ok": bool(ok), "evidence": evidence}

    # ---- structure_fidelity: sections / keys / must_contain / hand-off / framing
    structural: list[bool] = []
    obj = parse_json_output(text) if fmt == "json" else None
    if fmt == "json":
        ok = isinstance(obj, dict)
        add("json_parses", ok, "top-level object" if ok else "no JSON object found")
        structural.append(ok)
    req = checks.get("required_sections") or []
    if req:
        if fmt == "json" and isinstance(obj, dict):
            missing = [s for s in req if s not in obj]
        else:
            missing = [s for s in req if not _contains(text, s)]
        add("required_sections", not missing, f"missing: {missing}" if missing else f"{len(req)} present")
        structural.append(not missing)
    keys = checks.get("json_required_keys") or []
    if keys:
        missing = [k for k in keys if not (isinstance(obj, dict) and k in obj)]
        add("json_required_keys", not missing, f"missing: {missing}" if missing else f"{len(keys)} present")
        structural.append(not missing)
    if checks.get("min_sections") is not None:
        count = len(re.findall(r"^\s*(#{1,6}\s|<h[1-6])", text, re.M | re.I))
        ok = count >= int(checks["min_sections"])
        add("min_sections", ok, f"{count} headings")
        structural.append(ok)
    mc = checks.get("must_contain") or []
    if mc:
        missing = [s for s in mc if not _contains(text, s)]
        add("must_contain", not missing, f"missing: {missing}" if missing else "all present")
        structural.append(not missing)
    if checks.get("expect_handoff_to"):
        ok = _contains(text, checks["expect_handoff_to"])
        add("expect_handoff_to", ok, checks["expect_handoff_to"])
        structural.append(ok)
    if checks.get("expect_no_write_language", True) and fmt != "verifier" \
            and case.get("kind") in ("report", "routing"):
        hits = [p for p in WRITE_LANGUAGE if re.search(p, text, re.I)]
        add("no_write_language", not hits, f"matched: {hits}" if hits else "framed as draft")
        structural.append(not hits)
    if structural:
        metrics["structure_fidelity"] = 1.0 if all(structural) else 0.0

    # ---- placeholder_free (skipped for verifier output, which quotes defects)
    if fmt != "verifier":
        pats = checks.get("forbidden_patterns") or DEFAULT_FORBIDDEN
        hits = [p for p in pats if re.search(p, text, re.I)]
        add("forbidden_patterns", not hits, f"matched: {hits}" if hits else "none")
        mnc = checks.get("must_not_contain") or []
        bad = [s for s in mnc if _contains(text, s)]
        if mnc:
            add("must_not_contain", not bad, f"found: {bad}" if bad else "none")
        metrics["placeholder_free"] = 1.0 if not hits and not bad else 0.0

    # ---- threshold_exactness: score range + deterministic baseline hash
    exact: list[bool] = []
    sa = checks.get("score_attribute")
    if sa:
        m = re.search(sa["pattern"], text)
        if not m:
            add("score_attribute", False, "pattern not found")
            exact.append(False)
        else:
            try:
                val = float(m.group(1))
            except (ValueError, IndexError):
                val = float("nan")
            ok = (val == val) and (sa.get("min") is None or val >= sa["min"]) \
                and (sa.get("max") is None or val <= sa["max"])
            add("score_attribute", ok, f"value {val} in [{sa.get('min')}, {sa.get('max')}]")
            exact.append(ok)
    bl = checks.get("baseline")
    if bl:
        digest = sha256_text(text)
        same = digest == bl["sha256"]
        if bl.get("deterministic"):
            add("baseline_sha256", same, f"{digest[:12]} vs {bl['sha256'][:12]}")
            exact.append(same)
        else:
            add("baseline_sha256_info", True, f"{'identical' if same else 'differs'} (informational)")
    if exact:
        metrics["threshold_exactness"] = 1.0 if all(exact) else 0.0

    # ---- grounding_rate / citation_validity
    cp = checks.get("citation_pattern")
    if cp:
        cites = list(re.finditer(cp, text))
        need = int(checks.get("min_citations", 1))
        ok = len(cites) >= need
        add("min_citations", ok, f"{len(cites)} citations (need {need})")
        metrics["grounding_rate"] = 1.0 if ok else 0.0
        sources = checks.get("allowed_citation_sources") or []
        if sources and cites:
            valid = 0
            for c in cites:
                window = text[max(0, c.start() - 200): c.end() + 60]
                if any(_contains(window, s) for s in sources):
                    valid += 1
            frac = valid / len(cites)
            floor = (case.get("floors") or {}).get("citation_validity", floors["citation_validity"])
            add("citation_sources", frac >= floor, f"{valid}/{len(cites)} name an allowed source")
            metrics["citation_validity"] = frac
        elif sources:
            metrics["citation_validity"] = 0.0

    # ---- egress_clean: internal markers never appear in the output
    markers = checks.get("internal_markers")
    if markers is not None or case.get("kind") in ("report", "routing"):
        markers = markers or DEFAULT_MARKERS
        hits = [mk for mk in markers if mk.lower() in low]
        add("internal_markers", not hits, f"found: {hits}" if hits else "none")
        metrics["egress_clean"] = 1.0 if not hits else 0.0

    # ---- verifier_first_pass
    expected = case.get("expected_verdict", "PASS")
    if verdict is not None:
        ok = verdict == expected
        add("verifier_verdict", ok, f"{verdict} (expected {expected})")
        metrics["verifier_first_pass"] = 1.0 if ok else 0.0

    # ---- budget_ok
    budget = case.get("budget") or {}
    if usage and budget:
        problems = []
        if budget.get("max_input_tokens") and usage.get("input_tokens", 0) > budget["max_input_tokens"]:
            problems.append("input_tokens")
        if budget.get("max_output_tokens") and usage.get("output_tokens", 0) > budget["max_output_tokens"]:
            problems.append("output_tokens")
        if budget.get("max_latency_s") and usage.get("latency_s", 0) > budget["max_latency_s"]:
            problems.append("latency_s")
        if budget.get("max_cost_eur") is not None and usage.get("cost_eur") is not None \
                and usage["cost_eur"] > budget["max_cost_eur"]:
            problems.append("cost_eur")
        add("budget", not problems, f"over: {problems}" if problems else "within budget")
        metrics["budget_ok"] = 1.0 if not problems else 0.0

    return results, metrics


def estimate_cost(model: str | None, usage: dict) -> float | None:
    if not model:
        return None
    pin = _prices_from_env("PRICE_EUR_PER_1M_IN", PRICE_IN)
    pout = _prices_from_env("PRICE_EUR_PER_1M_OUT", PRICE_OUT)
    key = next((k for k in pin if k in model), None)
    if key is None:
        return None
    return round(usage.get("input_tokens", 0) / 1e6 * pin[key]
                 + usage.get("output_tokens", 0) / 1e6 * pout.get(key, 0.0), 4)


# --------------------------------------------------------------------------- offline sources
def load_candidate(cdir: Path, cid: str) -> tuple[str | None, str | None, dict | None]:
    text = None
    for ext in ("html", "json", "md", "txt", "text"):
        p = cdir / f"{cid}.{ext}"
        if p.is_file():
            text = p.read_text(encoding="utf-8", errors="replace")
            break
    verdict = None
    vp = cdir / f"{cid}.verdict.txt"
    if vp.is_file():
        verdict = parse_verdict(vp.read_text(encoding="utf-8", errors="replace"))
    usage = None
    up = cdir / f"{cid}.usage.json"
    if up.is_file():
        try:
            usage = json.loads(up.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            usage = None
    return text, verdict, usage


# --------------------------------------------------------------------------- live runner
class LiveRunner:
    """Talks to Azure AI Foundry with the caller's own Entra identity. Reads
    agents, creates threads/messages/runs (Azure AI User). With
    model_override it also creates and deletes <agent>-eval clones
    (Azure AI Developer). It never approves, renders or uploads anything."""

    def __init__(self, endpoint: str, verifier: str, model_override: str | None,
                 inputs_dir: Path, keep_clones: bool):
        from azure.ai.projects import AIProjectClient
        from azure.identity import DefaultAzureCredential
        self.client = AIProjectClient(endpoint=endpoint, credential=DefaultAzureCredential())
        self.agents = self.client.agents
        self.live = {a.name: a for a in self.agents.list_agents()}
        self.verifier = verifier
        self.model_override = model_override
        self.inputs_dir = inputs_dir
        self.keep_clones = keep_clones
        self.clones: dict[str, object] = {}
        self.file_cache: dict[str, str] = {}

    def resolve(self, name: str):
        if name not in self.live:
            raise RuntimeError(f"agent {name!r} not found — run deploy.sh first")
        base = self.live[name]
        if not self.model_override or name == self.verifier:
            return base
        if name not in self.clones:
            clone_name = f"{name}-eval"
            kwargs = dict(model=self.model_override, name=clone_name,
                          instructions=base.instructions,
                          description=f"EVALUATION CLONE of {name} on {self.model_override} — delete after run_evals.py",
                          tools=getattr(base, "tools", None),
                          tool_resources=getattr(base, "tool_resources", None))
            self.clones[name] = self.agents.create_agent(**{k: v for k, v in kwargs.items() if v is not None})
            print(f"  cloned {name} -> {clone_name} ({self.clones[name].id}) model={self.model_override}")
        return self.clones[name]

    def upload(self, rel: str) -> str:
        if rel in self.file_cache:
            return self.file_cache[rel]
        path = (self.inputs_dir / rel).resolve()
        if not str(path).startswith(str(self.inputs_dir.resolve())) or not path.is_file():
            raise FileNotFoundError(f"input file {rel!r} not under {self.inputs_dir}")
        f = self.agents.files.upload_and_poll(file_path=str(path), purpose="agents")
        self.file_cache[rel] = f.id
        return f.id

    def ask(self, agent, prompt: str, files: list[dict]) -> tuple[str, dict, str | None]:
        attachments = []
        for spec in files:
            tool = spec.get("attach_as", "code_interpreter")
            attachments.append({"file_id": self.upload(spec["path"]), "tools": [{"type": tool}]})
        thread = self.agents.threads.create()
        self.agents.messages.create(thread_id=thread.id, role="user", content=prompt,
                                    attachments=attachments or None)
        t0 = time.monotonic()
        run = self.agents.runs.create_and_process(thread_id=thread.id, agent_id=agent.id)
        latency = round(time.monotonic() - t0, 1)
        if run.status != "completed":
            raise RuntimeError(f"run {run.status}: {getattr(run, 'last_error', None)}")
        text = ""
        for msg in self.agents.messages.list(thread_id=thread.id):
            if msg.role == "assistant":
                text = "\n".join(p.text.value for p in msg.content if getattr(p, "text", None))
                break
        u = getattr(run, "usage", None)
        usage = {"input_tokens": int(getattr(u, "prompt_tokens", 0) or 0),
                 "output_tokens": int(getattr(u, "completion_tokens", 0) or 0),
                 "latency_s": latency}
        model = getattr(run, "model", None) or getattr(agent, "model", None)
        usage["cost_eur"] = estimate_cost(model, usage)
        return text, usage, model

    def run_case(self, case: dict) -> tuple[str, str | None, dict, str | None]:
        agent = self.resolve(case["agent"])
        inp = case["input"]
        text, usage, model = self.ask(agent, inp["prompt"], inp.get("files") or [])
        verdict = None
        if case.get("kind") == "verifier-negative":
            verdict = parse_verdict(text)
        elif case.get("kind") == "report":
            vtext, vusage, _ = self.ask(self.resolve(self.verifier),
                                        "Verify this draft deliverable (do not rewrite it):\n\n" + text, [])
            verdict = parse_verdict(vtext)
            usage["verifier_input_tokens"] = vusage["input_tokens"]
            usage["verifier_output_tokens"] = vusage["output_tokens"]
        return text, verdict, usage, model

    def cleanup(self) -> None:
        if self.keep_clones:
            for name, a in self.clones.items():
                print(f"  kept clone {a.name} ({a.id}) — delete it after review")
            return
        for name, a in self.clones.items():
            try:
                self.agents.delete_agent(a.id)
                print(f"  deleted clone {a.name}")
            except Exception as exc:  # noqa: BLE001 - report, never hide
                print(f"  WARNING could not delete clone {a.name}: {exc}")


# --------------------------------------------------------------------------- report
def aggregate(case_results: list[dict], floors: dict) -> tuple[dict, dict]:
    metrics: dict[str, dict] = {}
    for m in METRICS:
        vals = [r["metrics"][m] for r in case_results
                if r["status"] in ("pass", "fail") and r["metrics"].get(m) is not None]
        value = round(sum(vals) / len(vals), 4) if vals else None
        metrics[m] = {"value": value, "floor": floors[m], "cases": len(vals),
                      "ok": (value is None) or value >= floors[m]}
    failed = [r["id"] for r in case_results if r["status"] == "fail"]
    errored = [r["id"] for r in case_results if r["status"] == "error"]
    gate_ok = not failed and not errored and all(v["ok"] for v in metrics.values())
    return metrics, {"result": "PASS" if gate_ok else "FAIL", "failed_cases": failed,
                     "errored_cases": errored,
                     "metrics_below_floor": [m for m, v in metrics.items() if not v["ok"]]}


def write_markdown(report: dict, path: Path) -> None:
    lines = [f"# Evaluation report — {report['generated']}", "",
             f"Mode: `{report['mode']}` · golden set: `{report['golden']}` (v{report['golden_version']}) "
             f"· cases: {len(report['cases'])} · gate: **{report['gate']['result']}**", "",
             "Controls: ISO 42001 A.6.2.4 / A.8.4; ISO 27001:2022 A.8.29; EU AI Act Art. 9(6)–(8). "
             "Nothing was approved, rendered or stored by this run (EVALUATION.md §3).", "",
             "## Metrics vs floors", "", "| Metric | Value | Floor | Cases | OK |", "|---|---|---|---|---|"]
    for m, v in report["metrics"].items():
        val = "n/a" if v["value"] is None else f"{v['value']:.2f}"
        lines.append(f"| {m} | {val} | {v['floor']:.2f} | {v['cases']} | {'yes' if v['ok'] else '**NO**'} |")
    lines += ["", "## Cases", "",
              "| Id | Req | Agent | Tier | Model | Status | Verdict | Failed checks | Tokens in/out | Latency s | € |",
              "|---|---|---|---|---|---|---|---|---|---|---|"]
    for c in report["cases"]:
        failed = ", ".join(n for n, r in c["checks"].items() if not r["ok"]) or "—"
        u = c.get("usage") or {}
        tok = f"{u.get('input_tokens', '—')}/{u.get('output_tokens', '—')}" if u else "—"
        cost = u.get("cost_eur")
        lines.append(f"| {c['id']} | {c['requirement']} | {c['agent']} | {c['tier_of_record']} | "
                     f"{c.get('model') or '—'} | {c['status']} | {c.get('verdict') or '—'} | {failed} | "
                     f"{tok} | {u.get('latency_s', '—') if u else '—'} | "
                     f"{cost if cost is not None else '—'} |")
    lines += ["", "## Check evidence", ""]
    for c in report["cases"]:
        lines.append(f"### {c['id']} — {c['status']}")
        if c.get("error"):
            lines.append(f"- error: {c['error']}")
        for n, r in c["checks"].items():
            lines.append(f"- {'ok ' if r['ok'] else 'FAIL'} `{n}`: {r['evidence']}")
        lines.append("")
    if report["gate"]["result"] != "PASS":
        lines += ["## Gate outcome", "",
                  f"Failed cases: {report['gate']['failed_cases'] or 'none'}; errored: "
                  f"{report['gate']['errored_cases'] or 'none'}; metrics below floor: "
                  f"{report['gate']['metrics_below_floor'] or 'none'}. The change must not proceed "
                  "(EVALUATION.md §5); add the failing pattern to the golden set."]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--golden", type=Path, default=DEFAULT_GOLDEN, help="golden set JSON (default: example)")
    ap.add_argument("--dry-run", action="store_true", help="offline: validate + check fixtures; no Azure")
    ap.add_argument("--validate-only", action="store_true", help="only validate the golden set")
    ap.add_argument("--list", action="store_true", help="list cases and exit")
    ap.add_argument("--only", help="comma-separated case ids")
    ap.add_argument("--agent", help="only cases of this producing agent")
    ap.add_argument("--candidates", type=Path, help="offline: directory with downloaded outputs per case id")
    ap.add_argument("--inputs-dir", type=Path, default=CONV / "build" / "comparison-set" / "inputs",
                    help="local mirror of Governance/ComparisonSet/inputs/ (live mode file uploads)")
    ap.add_argument("--out", type=Path, help="report directory (default build/evals/<timestamp>)")
    ap.add_argument("--model-override", help="live: evaluate this deployment via <agent>-eval clones")
    ap.add_argument("--keep-clones", action="store_true", help="live: do not delete the -eval clones")
    ap.add_argument("--verifier-agent", default=VERIFIER)
    ap.add_argument("--strict", action="store_true", help="skipped cases fail the run")
    args = ap.parse_args()

    golden = load_golden(args.golden)
    errors = validate_golden(golden)
    if errors:
        print("Golden set INVALID:")
        for e in errors:
            print("  -", e)
        return 2
    print(f"golden set OK: {args.golden} v{golden['version']} ({len(golden['cases'])} cases)")
    if args.validate_only:
        return 0

    cases = golden["cases"]
    if args.only:
        wanted = {s.strip() for s in args.only.split(",") if s.strip()}
        unknown = wanted - {c["id"] for c in cases}
        if unknown:
            sys.exit(f"unknown case id(s): {sorted(unknown)}")
        cases = [c for c in cases if c["id"] in wanted]
    if args.agent:
        cases = [c for c in cases if c["agent"] == args.agent]
    if args.list:
        for c in cases:
            print(f"{c['id']:40} {c['requirement']:8} {c['kind']:17} {c['agent']:36} {c['tier_of_record']}")
        return 0
    if not cases:
        sys.exit("no cases selected")

    floors = dict(DEFAULT_FLOORS)
    floors.update(golden.get("floors") or {})

    endpoint = os.environ.get("PROJECT_ENDPOINT")
    if args.dry_run or args.candidates:
        mode = "dry-run" if args.dry_run else "candidates"
        runner = None
    else:
        if not endpoint:
            sys.exit("Set PROJECT_ENDPOINT (setup/.env) for a live run, or use --dry-run / --candidates")
        mode = "live" + (f" (model-override {args.model_override})" if args.model_override else "")
        runner = LiveRunner(endpoint, args.verifier_agent, args.model_override,
                            args.inputs_dir, args.keep_clones)
    print(f"mode: {mode}; {len(cases)} case(s)")

    results: list[dict] = []
    try:
        for case in cases:
            entry = {"id": case["id"], "requirement": case["requirement"], "kind": case["kind"],
                     "agent": case["agent"], "tier_of_record": case["tier_of_record"],
                     "pipeline": case.get("pipeline"), "status": "skipped", "verdict": None,
                     "model": None, "usage": None, "checks": {}, "metrics": {m: None for m in METRICS}}
            text = verdict = model = None
            usage = None
            try:
                if args.candidates:
                    text, verdict, usage = load_candidate(args.candidates, case["id"])
                    if text is None and args.dry_run and case.get("fixture"):
                        text, verdict = case["fixture"], case.get("fixture_verdict")
                elif args.dry_run:
                    if case.get("fixture") is not None:
                        text, verdict = case["fixture"], case.get("fixture_verdict")
                        model = {"light": "gpt-4o-mini", "chat": "gpt-4o",
                                 "reasoning": "o3-mini"}[case["tier_of_record"]] + " (fixture)"
                else:
                    text, verdict, usage, model = runner.run_case(case)  # type: ignore[union-attr]
                if text is None:
                    entry["note"] = "no candidate output / fixture"
                else:
                    checks, metrics = run_checks(case, text, verdict, usage, floors)
                    entry.update(checks=checks, metrics=metrics, verdict=verdict, usage=usage,
                                 model=model, output_sha256=sha256_text(text),
                                 status="pass" if all(r["ok"] for r in checks.values()) else "fail")
            except Exception as exc:  # noqa: BLE001 - one bad case must not hide the others
                entry.update(status="error", error=str(exc))
            results.append(entry)
            print(f"  {entry['status']:7} {case['id']}"
                  + (f"  verdict={entry['verdict']}" if entry.get("verdict") else "")
                  + (f"  ({entry.get('error') or entry.get('note')})" if entry["status"] in ("error", "skipped") else ""))
    finally:
        if runner is not None:
            runner.cleanup()

    metrics, gate = aggregate(results, floors)
    skipped = [r["id"] for r in results if r["status"] == "skipped"]
    if args.strict and skipped:
        gate["result"] = "FAIL"
        gate["skipped_cases"] = skipped

    out = args.out or (CONV / "build" / "evals" / dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    out.mkdir(parents=True, exist_ok=True)
    report = {"generated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
              "mode": mode, "golden": str(args.golden), "golden_version": golden["version"],
              "floors": floors, "metrics": metrics, "gate": gate, "cases": results,
              "never_approved_or_stored": True}
    (out / "eval-report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    write_markdown(report, out / "eval-report.md")
    print(f"gate: {gate['result']}  (report: {out / 'eval-report.md'})")
    if skipped:
        print(f"skipped: {skipped}")
    return 0 if gate["result"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
