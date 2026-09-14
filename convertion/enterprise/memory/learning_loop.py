#!/usr/bin/env python3
"""Aggregate feedback, evaluation results, verifier FAIL outcomes and approval
rework into ONE monthly improvement proposal for the platform owner.

Offline by design: reads exported files, writes a proposal, and never touches
an agent, the registry, a template, a vector store or the memory store. The
proposal is INPUT to the owner's decision (enterprise/MEMORY_AND_LEARNING.md
section 4 -> operations/CONTINUOUS_IMPROVEMENT.md backlog -> UPGRADE_CHECKLIST
-> operations/CHANGE_MANAGEMENT.md). No agent, workflow or scheduled job may
act on the output; only Francisco Gustavo Gomes ({upn:francisco.gomes}) or,
for his own changes, the deputy ({upn:deputy-approver}) decides.

Inputs (all optional; a missing input is reported, never fabricated, except in
--dry-run which uses built-in synthetic samples when the inbox is empty):

    <inbox>/feedback*.jsonl | *.json   records per enterprise/memory/feedback-schema.json
                                       (portal thumbs export, Teams form, MCP client,
                                       SharePoint list {list:PlatformFeedback} export)
    <inbox>/verifier-*.json            list of {timestamp, agent, pipeline, run_id,
                                       verdict, finding_code} exported from
                                       operations/kql/verifier-fail-rate.kql
    <inbox>/approvals-*.json           list of {timestamp, pipeline, agent, run_id,
                                       decision (APPROVED|REJECTED|REWORK), reason_code,
                                       requested_by, reviewed_by} exported from
                                       {list:ApprovalDecisions} (ids and codes only)
    <evals>/**/eval-report.json        operations/evaluation/run_evals.py reports
                                       (cases below floor become golden_set_eval signals)

Usage
    python3 learning_loop.py --dry-run                       # synthetic samples, no files needed
    python3 learning_loop.py --dry-run --month 2026-09 --inbox build/learning/inbox --evals build/evals
    python3 learning_loop.py --month 2026-09 --out build/learning/2026-09

Output: <out>/proposal.md and <out>/proposal.json (attach to the M1 evaluation
note under Governance/Operations/{yyyy}-{mm}/). Exit 0 always in --dry-run
unless an input file is malformed; exit 2 when a record carries an
invariant_touched value (that is an incident path, not an improvement).

Privacy: descriptions are scanned for e-mail addresses, IPv4 addresses, UPN-like
strings and secret-like tokens; matches are masked and the record is flagged
`redacted` so the collector can be fixed. No report content is ever read.

Controls: ISO 27001:2022 cl. 10.1, A.5.27, A.8.32; ISO 42001 cl. 10.1-10.2,
A.6.2.6, A.8.3; EU AI Act Art. 26(5)-(7); DORA Art. 13.
"""

from __future__ import annotations

import argparse
import datetime as dt
import glob
import hashlib
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONV = HERE.parent.parent
DEFAULT_SCHEMA = HERE / "feedback-schema.json"
DEFAULT_INBOX = CONV / "build" / "learning" / "inbox"
DEFAULT_EVALS = CONV / "build" / "evals"

# --------------------------------------------------------------------------- policy tables
# category -> (change path per operations/CHANGE_MANAGEMENT.md section 1, risk class 1/3/5,
#              default effort 1-5, mandatory gates)
CATEGORY_TO_CHANGE = {
    "accuracy":           ("prompt",    3, 3, "verify_conversion; create_*.py --dry-run; G1 control vs candidate; comparison set for report agents"),
    "grounding":          ("knowledge", 3, 2, "knowledge-refresh.md section 3 intake form; G1 on affected agents"),
    "citation":           ("knowledge", 3, 2, "knowledge-refresh.md section 3; advisor comparison set g/h/i"),
    "structure":          ("prompt",    3, 2, "verify_conversion; G1; verifier_first_pass = 1.00"),
    "threshold":          ("template",  3, 3, "template-update-approval (P7D); update_templates.py --dry-run; RISK_THRESHOLDS.md review"),
    "template":           ("template",  3, 3, "template-update-approval (P7D); update_templates.py --dry-run"),
    "tone-style":         ("prompt",    1, 1, "verify_conversion; wording delta signed by reviewer"),
    "tool-failure":       ("registry",  3, 2, "attach_integrations.py --dry-run shows [read-only]; model_tool_matrix check; connection smoke test"),
    "latency":            ("tier",      3, 2, "kql/latency-and-tokens.kql; staged rollout one agent, 1 week"),
    "cost":               ("tier",      3, 2, "MODEL_ROUTING.md accuracy floor; comparison set on downgrade; advisory agents never leave reasoning"),
    "safety-block":       ("infra",     5, 3, "RAI policy = high-risk change; R12 tally; content-filter block count"),
    "regulatory-claim":   ("knowledge", 3, 2, "AI concern: acknowledged same day; knowledge-refresh.md section 3; advisor comparison set"),
    "injection-suspected":("infra",     5, 3, "incident path RUNBOOK.md first; DATA_PROTECTION_GUARDRAILS.md; Prompt Shields settings"),
    "personal-data":      ("memory-delete", 5, 1, "MEMORY_POLICY.md deletion; DPO channel informed; R13"),
    "usability":          ("docs",      1, 1, "user guide / SUPPORT_MODEL.md known-issue list"),
    "other":              ("docs",      1, 1, "owner classifies at triage"),
}
SEVERITY_WEIGHT = {"low": 1, "medium": 2, "high": 3}
MAX_SCHEDULED_PER_QUARTER = 6  # CONTINUOUS_IMPROVEMENT.md section 2
METRIC_TO_CATEGORY = {
    "verifier_first_pass": "structure", "structure_fidelity": "structure",
    "placeholder_free": "template", "threshold_exactness": "threshold",
    "grounding_rate": "grounding", "citation_validity": "citation",
    "egress_clean": "injection-suspected", "budget_ok": "cost",
    "groundedness": "grounding", "relevance": "accuracy",
    "task_adherence": "accuracy", "tool_call_accuracy": "tool-failure",
}

# --------------------------------------------------------------------------- privacy guard
RE_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
RE_IPV4 = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
RE_SECRET = re.compile(r"(?i)(?:secret|password|token|key)\s*[:=]\s*\S{8,}")
RE_UPN_RAW = re.compile(r"\b[a-z]+\.[a-z]+@", re.I)


def redact(text: str) -> tuple[str, bool]:
    flagged = False
    for rx, mask in ((RE_EMAIL, "{email-redacted}"), (RE_IPV4, "{ip-redacted}"),
                     (RE_SECRET, "{secret-redacted}"), (RE_UPN_RAW, "{upn-redacted}@")):
        if rx.search(text):
            flagged = True
            text = rx.sub(mask, text)
    return text, flagged


# --------------------------------------------------------------------------- schema (light validation)
def load_schema(path: Path) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def validate_record(rec: dict, schema: dict) -> list[str]:
    """Minimal validation without external deps: required keys, enums, types of
    the fields learning_loop relies on. jsonschema (if installed) does the full check."""
    errs: list[str] = []
    for k in schema.get("required", []):
        if k not in rec:
            errs.append(f"missing required field '{k}'")
    props = schema.get("properties", {})
    for field in ("source", "category", "channel", "severity"):
        if field in rec and rec[field] is not None:
            allowed = props.get(field, {}).get("enum")
            if allowed and rec[field] not in allowed:
                errs.append(f"{field}='{rec[field]}' not in enum")
    if "signal" in rec:
        sig = rec["signal"]
        if not isinstance(sig, dict) or not any(sig.get(k) is not None for k in ("thumbs", "rating", "metric", "verdict")):
            errs.append("signal needs one of thumbs/rating/metric/verdict")
    sb = rec.get("submitted_by", "")
    if not re.match(r"^\{upn:[a-z0-9.-]+\}$|^\{system:[a-z0-9-]+\}$", str(sb)):
        errs.append("submitted_by must be a {upn:name} or {system:collector} placeholder")
    try:
        import jsonschema  # type: ignore
        jsonschema.validate(rec, schema)
    except ImportError:
        pass
    except Exception as exc:  # noqa: BLE001 - report, do not crash
        errs.append(f"jsonschema: {str(exc).splitlines()[0][:160]}")
    return errs


# --------------------------------------------------------------------------- loaders
def month_of(ts: str) -> str:
    return (ts or "")[:7]


def load_feedback(inbox: Path) -> list[dict]:
    recs: list[dict] = []
    for f in sorted(glob.glob(str(inbox / "feedback*.jsonl"))):
        with open(f, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    recs.append(json.loads(line))
    for f in sorted(glob.glob(str(inbox / "feedback*.json"))):
        with open(f, encoding="utf-8") as fh:
            data = json.load(fh)
        recs.extend(data if isinstance(data, list) else [data])
    return recs


def load_verifier(inbox: Path) -> list[dict]:
    out: list[dict] = []
    for f in sorted(glob.glob(str(inbox / "verifier-*.json"))):
        with open(f, encoding="utf-8") as fh:
            rows = json.load(fh)
        for r in rows:
            if str(r.get("verdict", "")).upper() != "FAIL":
                continue
            out.append({
                "id": synth_id("v", r), "timestamp": r.get("timestamp", ""),
                "source": "verifier_fail", "submitted_by": "{system:verifier-export}",
                "channel": "export", "agent": r.get("agent", "unknown"),
                "agent_version": r.get("agent_version"), "pipeline": r.get("pipeline"),
                "run_id": r.get("run_id"), "category": r.get("category", "structure"),
                "signal": {"verdict": "FAIL", "finding_code": r.get("finding_code")},
                "description": f"verifier FAIL {r.get('finding_code', '?')}",
                "severity": "low", "ai_concern": False, "invariant_touched": None,
                "evidence_refs": [x for x in [r.get("run_id")] if x],
            })
    return out


def load_approvals(inbox: Path) -> list[dict]:
    out: list[dict] = []
    for f in sorted(glob.glob(str(inbox / "approvals-*.json"))):
        with open(f, encoding="utf-8") as fh:
            rows = json.load(fh)
        for r in rows:
            decision = str(r.get("decision", "")).upper()
            if decision not in ("REJECTED", "REWORK"):
                continue
            sev = "medium" if decision == "REJECTED" else "low"
            if r.get("requested_by") and r.get("requested_by") == r.get("reviewed_by"):
                sev = "high"  # R4 approver = requester is a flow defect (P1), surfaced as mandatory
            out.append({
                "id": synth_id("a", r), "timestamp": r.get("timestamp", ""),
                "source": "approval_rework", "submitted_by": "{system:approvals-export}",
                "channel": "export", "agent": r.get("agent", "unknown"),
                "agent_version": r.get("agent_version"), "pipeline": r.get("pipeline"),
                "run_id": r.get("run_id"), "category": r.get("category", "accuracy"),
                "signal": {"verdict": decision, "finding_code": r.get("reason_code")},
                "description": f"approval {decision.lower()} reason {r.get('reason_code', '?')}",
                "severity": sev, "ai_concern": False,
                "invariant_touched": "approval-before-write" if sev == "high" else None,
                "evidence_refs": [x for x in [r.get("run_id")] if x],
            })
    return out


def load_eval_reports(evals: Path) -> list[dict]:
    out: list[dict] = []
    for f in sorted(glob.glob(str(evals / "**" / "eval-report.json"), recursive=True)):
        with open(f, encoding="utf-8") as fh:
            rep = json.load(fh)
        floors = rep.get("floors", {})
        for case in rep.get("cases", []):
            if case.get("status") != "fail":
                continue
            for metric, value in (case.get("metrics") or {}).items():
                floor = floors.get(metric)
                if value is None or floor is None or value >= floor:
                    continue
                out.append({
                    "id": synth_id("e", {"f": f, "c": case.get("id"), "m": metric}),
                    "timestamp": rep.get("generated", ""), "source": "golden_set_eval",
                    "submitted_by": "{system:run-evals}", "channel": "export",
                    "agent": case.get("agent", "unknown"), "agent_version": case.get("model"),
                    "pipeline": case.get("pipeline"), "run_id": None,
                    "category": METRIC_TO_CATEGORY.get(metric, "accuracy"),
                    "signal": {"metric": metric, "value": value, "floor": floor},
                    "description": f"golden-set case {case.get('id')} metric {metric} {value} < floor {floor} ({rep.get('mode')})",
                    "severity": "medium", "ai_concern": False, "invariant_touched": None,
                    "evidence_refs": [os.path.relpath(f, CONV) if str(f).startswith(str(CONV)) else f],
                })
    return out


def synth_id(prefix: str, row: dict) -> str:
    h = hashlib.sha256(json.dumps(row, sort_keys=True, default=str).encode()).hexdigest()[:8]
    ts = (row.get("timestamp") or row.get("f") or "00000000")
    day = re.sub(r"[^0-9]", "", str(ts))[:8].ljust(8, "0")
    return f"fb-{day}-{h}"  # prefix kept for readability of call sites


# --------------------------------------------------------------------------- synthetic samples (dry run)
def synthetic(month: str) -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    d = f"{month}-1"
    fb = [
        {"id": "fb-20260903-a1b2c3d4", "timestamp": f"{d}0T09:00:00Z", "source": "user_feedback",
         "submitted_by": "{upn:jose.mogollon}", "channel": "teams", "agent": "dora", "agent_version": "dora:14",
         "pipeline": None, "requirement": "g", "run_id": None, "conversation_id": "{conversation-id}",
         "category": "citation", "signal": {"thumbs": "down", "rating": 2},
         "description": "Cited RTS article number off by one.", "severity": "medium", "ai_concern": True,
         "invariant_touched": None, "evidence_refs": ["{trace-id}"], "retain_until": "2028-09-03"},
        {"id": "fb-20260911-b2c3d4e5", "timestamp": f"{d}1T14:20:00Z", "source": "user_feedback",
         "submitted_by": "{upn:tania.morais}", "channel": "portal", "agent": "dora", "agent_version": "dora:14",
         "pipeline": None, "requirement": "g", "run_id": None, "conversation_id": "{conversation-id}",
         "category": "citation", "signal": {"thumbs": "down"},
         "description": "Second occurrence: article reference does not resolve.", "severity": "medium",
         "ai_concern": True, "invariant_touched": None, "evidence_refs": ["{trace-id}"], "retain_until": "2028-09-11"},
        {"id": "fb-20260905-c3d4e5f6", "timestamp": f"{d}2T10:00:00Z", "source": "human_eval_template",
         "submitted_by": "{upn:pedro.santos}", "channel": "portal", "agent": "ciso-executive-summary",
         "agent_version": "ciso-executive-summary:9", "pipeline": "ciso-exec-summary", "requirement": "c",
         "run_id": "{run-id}", "conversation_id": None, "category": "tone-style",
         "signal": {"rating": 4}, "description": "Would sign; executive wording slightly long.",
         "severity": "low", "ai_concern": False, "invariant_touched": None, "evidence_refs": ["{run-id}"],
         "retain_until": "2028-09-05"},
        {"id": "fb-20260908-d4e5f6a7", "timestamp": f"{d}3T16:45:00Z", "source": "user_feedback",
         "submitted_by": "{upn:jose.meireles}", "channel": "mcp", "agent": "cyber-forum",
         "agent_version": "cyber-forum:11", "pipeline": None, "requirement": "h", "run_id": None,
         "conversation_id": "{conversation-id}", "category": "tool-failure", "signal": {"thumbs": "down"},
         "description": "Confluence tool returned no results for a page the user can open; agent answered from memory.",
         "severity": "medium", "ai_concern": False, "invariant_touched": None, "evidence_refs": ["{trace-id}"],
         "retain_until": "2028-09-08"},
    ]
    ver = [
        {"timestamp": f"{d}2T08:00:00Z", "agent": "soc-report-analyzer", "pipeline": "soc-report-summary",
         "run_id": "{run-id-1}", "verdict": "FAIL", "finding_code": "V-STRUCT-03"},
        {"timestamp": f"{d}4T08:00:00Z", "agent": "soc-report-analyzer", "pipeline": "soc-report-summary",
         "run_id": "{run-id-2}", "verdict": "FAIL", "finding_code": "V-STRUCT-03"},
        {"timestamp": f"{d}5T08:00:00Z", "agent": "soc-report-analyzer", "pipeline": "soc-report-summary",
         "run_id": "{run-id-3}", "verdict": "PASS", "finding_code": None},
    ]
    appr = [
        {"timestamp": f"{d}6T11:00:00Z", "pipeline": "dpia-dpo-report", "agent": "dpia", "run_id": "{run-id-4}",
         "decision": "REWORK", "reason_code": "A-WORDING", "requested_by": "{upn:pedro.santos}",
         "reviewed_by": "{upn:jose.mogollon}"},
        {"timestamp": f"{d}7T11:00:00Z", "pipeline": "dpia-dpo-report", "agent": "dpia", "run_id": "{run-id-5}",
         "decision": "APPROVED", "reason_code": None, "requested_by": "{upn:tania.morais}",
         "reviewed_by": "{upn:jose.meireles}"},
    ]
    evals = [{
        "generated": f"{d}8T07:00:00Z", "mode": "dry-run", "golden_version": "synthetic",
        "floors": {"citation_validity": 0.95, "verifier_first_pass": 1.0},
        "cases": [
            {"id": "g-dora-art30-provisions", "agent": "dora", "pipeline": None, "status": "fail",
             "model": "dora:14", "metrics": {"citation_validity": 0.8, "verifier_first_pass": None}},
            {"id": "e-soc-report-summary", "agent": "soc-report-analyzer", "pipeline": "soc-report-summary",
             "status": "pass", "model": "soc-report-analyzer:7", "metrics": {"verifier_first_pass": 1.0}},
        ],
    }]
    return fb, ver, appr, evals


def evals_from_objects(reports: list[dict]) -> list[dict]:
    """Same normalisation as load_eval_reports, for in-memory synthetic reports."""
    out: list[dict] = []
    for rep in reports:
        floors = rep.get("floors", {})
        for case in rep.get("cases", []):
            if case.get("status") != "fail":
                continue
            for metric, value in (case.get("metrics") or {}).items():
                floor = floors.get(metric)
                if value is None or floor is None or value >= floor:
                    continue
                out.append({
                    "id": synth_id("e", {"c": case.get("id"), "m": metric, "timestamp": rep.get("generated")}),
                    "timestamp": rep.get("generated", ""), "source": "golden_set_eval",
                    "submitted_by": "{system:run-evals}", "channel": "export",
                    "agent": case.get("agent", "unknown"), "agent_version": case.get("model"),
                    "pipeline": case.get("pipeline"), "run_id": None,
                    "category": METRIC_TO_CATEGORY.get(metric, "accuracy"),
                    "signal": {"metric": metric, "value": value, "floor": floor},
                    "description": f"golden-set case {case.get('id')} metric {metric} {value} < floor {floor}",
                    "severity": "medium", "ai_concern": False, "invariant_touched": None,
                    "evidence_refs": ["synthetic"],
                })
    return out


# --------------------------------------------------------------------------- aggregation
def cluster(records: list[dict], min_recurrence: int = 2) -> list[dict]:
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for r in records:
        groups[(r.get("agent", "unknown"), r.get("category", "other"))].append(r)
    items: list[dict] = []
    for (agent, category), recs in groups.items():
        path, risk, effort, gates = CATEGORY_TO_CHANGE.get(category, CATEGORY_TO_CHANGE["other"])
        sev = max(SEVERITY_WEIGHT.get(r.get("severity", "low"), 1) for r in recs)
        ai_concern = any(r.get("ai_concern") for r in recs)
        invariant = sorted({r["invariant_touched"] for r in recs if r.get("invariant_touched")})
        sources = sorted({r.get("source", "?") for r in recs})
        authors = sorted({r.get("submitted_by", "?") for r in recs})
        pipelines = sorted({r["pipeline"] for r in recs if r.get("pipeline")})
        versions = sorted({r["agent_version"] for r in recs if r.get("agent_version")})
        recurrence = len(recs)
        # value 1-5: recurrence and severity, capped; mandatory items bypass scoring
        value = min(5, 1 + (recurrence - 1) + (sev - 1))
        score = round(value * (6 - risk) / effort, 2)
        mandatory = ai_concern or bool(invariant)
        # CONTINUOUS_IMPROVEMENT.md S1/S2: same cause twice, any rejection, any AI concern
        qualifies = recurrence >= min_recurrence or sev >= 2 or mandatory
        items.append({
            "title": f"{category}: {agent}" + (f" ({', '.join(pipelines)})" if pipelines else ""),
            "agent": agent, "category": category, "pipelines": pipelines, "agent_versions": versions,
            "recurrence": recurrence, "sources": sources, "authors": authors,
            "severity_max": {1: "low", 2: "medium", 3: "high"}[sev],
            "ai_concern": ai_concern, "invariant_touched": invariant,
            "change_path": path, "risk_class": risk, "effort": effort, "gates": gates,
            "value": value, "score": score, "mandatory": mandatory, "qualifies": qualifies,
            "evidence_refs": sorted({e for r in recs for e in (r.get("evidence_refs") or [])})[:10],
            "record_ids": [r.get("id") for r in recs],
            "sample": [r.get("description", "")[:160] for r in recs[:3]],
        })
    items.sort(key=lambda i: (not i["mandatory"], -i["score"], -i["recurrence"], i["title"]))
    return items


def approver_for(_items: list[dict]) -> str:
    return "owner {upn:francisco.gomes} (deputy {upn:deputy-approver} reviews items the owner authored)"


def render_md(report: dict) -> str:
    L: list[str] = []
    r = report
    L.append(f"# Monthly improvement proposal — {r['month']}" + ("  (DRY RUN — synthetic samples)" if r["dry_run_synthetic"] else ""))
    L.append("")
    L.append(f"Generated {r['generated']} by `enterprise/memory/learning_loop.py` (offline). "
             f"Decision: {approver_for(r['items'])}. This file proposes; it changes nothing. "
             "Accepted items become `{jira:INFOSEC-PLAT}` tickets and go through "
             "`enterprise/UPGRADE_CHECKLIST.md` and `operations/CHANGE_MANAGEMENT.md` §3.")
    L.append("")
    s = r["summary"]
    L.append("## 1. Inputs")
    L.append("")
    L.append("| Source | Records in month | Notes |")
    L.append("|---|---|---|")
    for k, v in s["by_source"].items():
        L.append(f"| {k} | {v} | |")
    L.append(f"| total | {s['records']} | invalid {s['invalid']}, redacted {s['redacted']}, outside month {s['outside_month']} |")
    L.append("")
    if r["input_notes"]:
        L.append("Input notes: " + "; ".join(r["input_notes"]))
        L.append("")
    L.append("## 2. Mandatory items (AI concerns, invariants) — not subject to scoring")
    L.append("")
    mand = [i for i in r["items"] if i["mandatory"]]
    if not mand:
        L.append("None.")
    for i in mand:
        L.append(f"- **{i['title']}** — recurrence {i['recurrence']}, severity {i['severity_max']}, "
                 f"ai_concern={i['ai_concern']}, invariants={i['invariant_touched'] or '—'}; "
                 f"path `{i['change_path']}`; gates: {i['gates']}; evidence: {', '.join(i['evidence_refs']) or '—'}")
        if i["invariant_touched"]:
            L.append("  - Invariant touched: handle as incident / risk-acceptance (`RUNBOOK.md`, `CHANGE_MANAGEMENT.md` §5) — NOT an improvement.")
        if i["ai_concern"]:
            L.append("  - AI concern: acknowledge the same day in the channel; ISO 42001 A.8.3; EU AI Act Art. 26(7).")
    L.append("")
    L.append("## 3. Scored proposals (CONTINUOUS_IMPROVEMENT.md §2 format; max "
             f"{MAX_SCHEDULED_PER_QUARTER} scheduled per quarter)")
    L.append("")
    L.append("| # | Title | Recurrence | Sources | Sev | Change path | Risk | Effort | Value | Score | Qualifies | Decision |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    n = 0
    for i in r["items"]:
        if i["mandatory"]:
            continue
        n += 1
        L.append(f"| {n} | {i['title']} | {i['recurrence']} | {', '.join(i['sources'])} | {i['severity_max']} | "
                 f"`{i['change_path']}` | {i['risk_class']} | {i['effort']} | {i['value']} | {i['score']} | "
                 f"{'yes' if i['qualifies'] else 'watch'} | scheduled Q{r['quarter']} / deferred / declined |")
    L.append("")
    L.append("## 4. Per-item detail")
    L.append("")
    for i in r["items"]:
        L.append(f"### {i['title']}")
        L.append("")
        L.append(f"- Agent versions seen: {', '.join(i['agent_versions']) or 'unknown'}; pipelines: {', '.join(i['pipelines']) or '—'}")
        L.append(f"- Authors / collectors: {', '.join(i['authors'])}")
        L.append(f"- Mandatory gates before merge: {i['gates']}")
        L.append("- Invariant check: read-only agents / approval before write / taxonomy / identities / EU / no egress — must remain unchanged")
        L.append(f"- Records: {', '.join(i['record_ids'])}")
        for smp in i["sample"]:
            L.append(f"  - sample: {smp}")
        L.append("")
    L.append("## 5. What this proposal does not do")
    L.append("")
    L.append("- It does not modify any agent, template, registry entry, knowledge store or memory note.")
    L.append("- It does not promote an agent version, run the Agent Optimizer, or change a model deployment.")
    L.append("- It contains identifiers and generic descriptions only; no report content or personal data.")
    L.append("")
    L.append("Owner decision record: `Governance/Operations/{yyyy}-{mm}/evaluation.md` (RUNBOOK M1).")
    return "\n".join(L) + "\n"


# --------------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dry-run", action="store_true", help="offline; synthetic samples when the inbox is empty")
    ap.add_argument("--month", default=dt.date.today().strftime("%Y-%m"), help="yyyy-mm (default: current month)")
    ap.add_argument("--inbox", type=Path, default=DEFAULT_INBOX)
    ap.add_argument("--evals", type=Path, default=DEFAULT_EVALS)
    ap.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    ap.add_argument("--out", type=Path, help="default build/learning/<month>")
    ap.add_argument("--min-recurrence", type=int, default=2, help="recurrence that makes a cluster qualify (CONTINUOUS_IMPROVEMENT.md S1: same cause twice)")
    args = ap.parse_args()

    if not re.match(r"^\d{4}-\d{2}$", args.month):
        sys.exit("--month must be yyyy-mm")
    schema = load_schema(args.schema)
    notes: list[str] = []

    fb = ver = appr = evals = []
    synthetic_used = False
    if args.inbox.exists():
        fb, ver, appr = load_feedback(args.inbox), load_verifier(args.inbox), load_approvals(args.inbox)
    else:
        notes.append(f"inbox {args.inbox} not found")
    if args.evals.exists():
        evals = load_eval_reports(args.evals)
    else:
        notes.append(f"evals {args.evals} not found")
    if not (fb or ver or appr or evals):
        if not args.dry_run:
            print("no inputs found; nothing to propose (use --dry-run for synthetic samples)")
            return 0
        sfb, sver, sappr, sevals = synthetic(args.month)
        # route synthetic exports through the same normalisers as real files
        tmp_inbox = {"verifier-synthetic.json": sver, "approvals-synthetic.json": sappr}
        fb = sfb
        ver = [r for r in _normalise_rows(load_verifier, tmp_inbox["verifier-synthetic.json"], "verifier-")]
        appr = [r for r in _normalise_rows(load_approvals, tmp_inbox["approvals-synthetic.json"], "approvals-")]
        evals = evals_from_objects(sevals)
        synthetic_used = True
        notes.append("synthetic samples used (dry run)")

    # validate + redact + month filter
    valid: list[dict] = []
    invalid = redacted = outside = 0
    for rec in fb:
        errs = validate_record(rec, schema)
        if errs:
            invalid += 1
            notes.append(f"invalid record {rec.get('id', '?')}: {errs[0]}")
            continue
        desc, flagged = redact(rec.get("description", "") or "")
        if flagged:
            redacted += 1
            rec["description"] = desc
            rec["redacted"] = True
        valid.append(rec)
    records = valid + ver + appr + evals
    in_month = [r for r in records if month_of(r.get("timestamp", "")) == args.month]
    outside = len(records) - len(in_month)

    items = cluster(in_month, args.min_recurrence)
    by_source: dict[str, int] = defaultdict(int)
    for r in in_month:
        by_source[r.get("source", "?")] += 1
    quarter = (int(args.month[5:7]) - 1) // 3 + 1
    report = {
        "generated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "month": args.month, "quarter": quarter, "dry_run": args.dry_run, "dry_run_synthetic": synthetic_used,
        "schema": str(args.schema), "inbox": str(args.inbox), "evals": str(args.evals),
        "summary": {"records": len(in_month), "by_source": dict(sorted(by_source.items())),
                    "invalid": invalid, "redacted": redacted, "outside_month": outside,
                    "items": len(items), "mandatory": sum(1 for i in items if i["mandatory"]),
                    "qualifying": sum(1 for i in items if i["qualifies"])},
        "input_notes": notes, "items": items,
        "decision_by": "{upn:francisco.gomes}", "deputy_review_when_owner_authored": "{upn:deputy-approver}",
        "writes_nothing_else": True,
    }
    out = args.out or (CONV / "build" / "learning" / args.month)
    out.mkdir(parents=True, exist_ok=True)
    (out / "proposal.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    (out / "proposal.md").write_text(render_md(report), encoding="utf-8")

    s = report["summary"]
    print(f"month {args.month}: {s['records']} records -> {s['items']} items "
          f"({s['mandatory']} mandatory, {s['qualifying']} qualifying); invalid {s['invalid']}, redacted {s['redacted']}")
    for i in items[:8]:
        print(f"  {'!' if i['mandatory'] else '-'} {i['title']}  x{i['recurrence']}  path={i['change_path']}  score={i['score']}")
    print(f"proposal: {out / 'proposal.md'}  (decision: owner; nothing was changed)")
    if any(i["invariant_touched"] for i in items):
        print("!! an item touches a platform invariant — incident / risk-acceptance path, not an improvement")
        return 2
    return 0


def _normalise_rows(loader, rows: list[dict], prefix: str) -> list[dict]:
    """Run a file-based loader on in-memory rows by writing them to a temp dir."""
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / f"{prefix}synthetic.json"
        p.write_text(json.dumps(rows), encoding="utf-8")
        return loader(Path(td))


if __name__ == "__main__":
    sys.exit(main())
