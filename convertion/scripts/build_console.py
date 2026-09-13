#!/usr/bin/env python3
"""Build the ENX Assurance Console — one page that holds the whole platform.

WHY
  The platform is deliberately spread across files: charters in agents/,
  wiring in integrations/, pipelines in workflows/, queries in operations/kql/.
  That is right for change control and wrong for a person who has to USE and
  DEVELOP it. This generator collapses the whole inventory into a single
  self-contained page — every system, agent, pipeline, workflow, connection,
  dashboard query, template and runbook, each with what it is, where it lives,
  how to launch it and how to change it.

  It is GENERATED, never authored: the console cannot describe an agent the
  kit does not have, and a new agent appears in it the moment it is registered.
  That is the whole point — a hand-written index of a platform this size is
  wrong within a week.

OUTPUTS (build/console/, git-ignored build artefacts)
  catalog.json      the inventory as data — also served by the MCP `catalog`
                    tool, so chat surfaces and the page never disagree
  enx-console.html  the page: self-contained, no CDN, no network call, so it
                    opens from SharePoint or a laptop with equal success
                    (the same rule every delivered HTML dashboard follows)

USAGE
  python3 build_console.py                 # write both artefacts
  python3 build_console.py --check         # CI: every item is described
  python3 build_console.py --out DIR       # elsewhere

Offline and deterministic: no Azure call, no credentials. Placeholders
({baseName}, <tenant>) stay placeholders — the page is safe to store.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONV = HERE.parent
BUILD = CONV / "build"

# Systems a–j as the user stated them (REQUIREMENTS.md is the record). The
# console repeats the ASK, not a paraphrase, so a user recognises their own
# request in it.
SYSTEMS = [
    ("a", "Supplier OSINT assessment (DeepSearch)",
     "Assess a supplier from public sources and produce the interactive HTML dashboard.",
     "deepsearch-report · ai-deepsearch-report"),
    ("b", "OneTrust PDF → DPO report",
     "Turn a OneTrust assessment into the InfoSec TPA report the DPO team reads.",
     "dpia-dpo-report"),
    ("c", "Cyber Forum material",
     "Governance deck and executive dashboard for the CISO forums from OneTrust assessments.",
     "cyber-forum-pptx · ciso-exec-summary · cyber-forum-brief"),
    ("d", "Global CISO briefing",
     "Nine slides on one supplier/service: contract owner, impacted entities, exposure "
     "diagram, inherent and residual ICT scores, actions for the contract owner.",
     "ciso-global-pptx"),
    ("d2", "Evidence library analysis",
     "Every file filed for a supplier: identification, scope, emission date, validity "
     "period read from the content, findings. Reads only what changed since last time.",
     "tpa-evidence-analysis"),
    ("e", "SOC report summary",
     "Opinion, scope, period, every exception, CUEC mapping, reliance verdict.",
     "soc-report-summary"),
    ("f", "Penetration test summary",
     "Normalised findings by severity, scope and currency adequacy, reliance verdict.",
     "pentest-report-summary"),
    ("g", "Framework advisory with files",
     "ISO 27001/27002/27005/22301/20000/42001, NIST CSF, CIS, GDPR Art. 28, DORA, NIS2, "
     "EU AI Act, CSA, PCI DSS, OWASP — answers plus Word/Excel/PowerPoint/HTML.",
     "advisory-file-delivery"),
    ("h", "TPRM lifecycle advisory",
     "Third-party risk methodology, thresholds and process questions, same file output.",
     "advisory-file-delivery"),
    ("i", "Read-only reach into the estate",
     "Confluence, Jira, CMDB, SharePoint, OneTrust, Defender, Entra, the ENX gateway — "
     "read-only; plus public web search with no Euronext data outbound.",
     "platform capability"),
    ("j", "Template change control",
     "List, choose, edit, see the before/after, approve — then it propagates.",
     "template-update-approval"),
]

# How the owner develops each kind of change. Every row is a real command in
# this kit; the console is useless if its commands are aspirational.
DEVELOP = [
    ("Add or change an agent charter",
     "agents/&lt;name&gt;_instructions.md (or the export for a converted skill)",
     "python3 scripts/convert_skills.py &amp;&amp; python3 scripts/verify_conversion.py",
     "python3 scripts/create_agents.py --only &lt;name&gt;",
     "Tier B — peer approved; the golden set runs for a report agent"),
    ("Attach or detach a tool",
     "integrations/registry.json (agent.tools) + the spec under integrations/openapi/",
     "python3 scripts/attach_integrations.py --dry-run",
     "python3 scripts/attach_integrations.py --only &lt;name&gt;",
     "Tier B — non-GET operations are stripped automatically; a write grant is refused"),
    ("Change how an agent runs (sampling, effort, ceiling, retrieval)",
     "integrations/inference-profiles.json (class or per-agent override with a reason)",
     "python3 scripts/inference_profiles.py --show &lt;name&gt;",
     "python3 scripts/attach_integrations.py --only &lt;name&gt;",
     "Tier B — re-run the golden set: every value here can move accuracy"),
    ("Change a report template",
     "templates/ + templates/registry.json",
     "python3 scripts/update_templates.py --template &lt;id&gt; --file &lt;f&gt; --dry-run",
     "the template-update-approval workflow (visual before/after, then apply)",
     "Tier C — owner only"),
    ("Add or change a workflow / pipeline",
     "workflows/&lt;name&gt;.json · workflows/pipelines.json",
     "python3 ci/tests/test_workflow_efficiency.py",
     "ci/deploy_logicapps.sh",
     "Tier B — every Foreach must declare its concurrency bound"),
    ("Change infrastructure",
     "infra/*.bicep · infra/main.parameters*.json",
     "convertion/infra/validate.sh (build, lint, policy) + test_residency.py",
     "az deployment group create … (series/01–02)",
     "Tier C — owner only, deputy reviews"),
    ("Change a model tier",
     "integrations/registry.json model_tiers._deployment_of_record + infra params",
     "python3 enterprise/upgrade/check_model_lifecycle.py --dry-run",
     "the six-phase migration in UPDATE_AND_UPGRADE_REVIEW_POLICY.md R3",
     "Tier C — golden set before it serves traffic"),
    ("Add durable team knowledge",
     "agents/advisor-knowledge/ or a memory note",
     "python3 scripts/memory_store.py --list",
     "python3 scripts/memory_store.py --add …",
     "Tier A — no report content, no personal data (MEMORY_POLICY.md)"),
]


sys.path.insert(0, str(HERE))
from create_delivery_agents import AGENTS as DELIVERY  # noqa: E402
from build_self_knowledge import FLAGSHIP  # noqa: E402
from create_tpsrca_subagents import SUBAGENTS  # noqa: E402

EXPORT = CONV.parent / "claude-account-export"


def _json(rel: str) -> dict:
    p = CONV / rel
    if not p.is_file():
        sys.exit(f"missing {p} — the console is generated from the kit")
    return json.loads(p.read_text(encoding="utf-8"))


def _first_sentence(text: str, limit: int = 240) -> str:
    flat = re.sub(r"\s+", " ", (text or "")).strip().lstrip("> -")
    if len(flat) <= limit:
        return flat
    cut = flat[:limit]
    dot = cut.rfind(". ")
    return (cut[:dot + 1] if dot > limit // 3 else cut.rstrip() + "…")


def _export_description(name: str) -> str:
    """The skill's own `description:` from the export front matter — used for
    skills that convert on demand and are therefore absent from the manifest."""
    for rel in (f"skills/{name}/SKILL.md",
                f"platform-skills/examples/{name}/SKILL.md",
                f"platform-skills/public/{name}/SKILL.md",
                f"local-skills/{name}/SKILL.md"):
        path = EXPORT / rel
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        m = re.search(r"^description:\s*(\|?)\s*\n?(.*?)(?=^\w+:|^---)",
                      text, re.S | re.M)
        if m:
            return _first_sentence(m.group(2))
    return ""


def _doc_purpose(path: Path) -> str:
    """A document's own first line of prose — never a hand-kept summary."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return ""
    for line in lines[1:]:
        s = line.strip()
        if s and not s.startswith(("#", ">", "|", "-", "*", "```", "<!--")):
            return _first_sentence(s)
    return ""


def _kql_purpose(path: Path) -> str:
    body = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("//"):
            break
        body.append(line.lstrip("/ ").strip())
    return _first_sentence(" ".join(b for b in body if b), 300)


def collect() -> dict:
    registry = _json("integrations/registry.json")
    profiles = _json("integrations/inference-profiles.json")
    pipes = _json("workflows/pipelines.json")["pipelines"]
    templates = _json("templates/registry.json")["templates"]
    # Descriptions come from wherever the agent is actually defined — the
    # converted manifest, the delivery-agent table, the flagship trio, or the
    # export's own SKILL.md for a skill that converts on demand. An agent with
    # no description anywhere is a real gap, and --check says so.
    manifest = (json.loads((BUILD / "manifest.json").read_text(encoding="utf-8"))
                if (BUILD / "manifest.json").is_file() else {"agents": []})
    desc = {a["name"]: a.get("description", "") for a in manifest["agents"]}
    for name, spec in DELIVERY.items():
        desc.setdefault(name, spec.get("description", ""))
    for name, (purpose, _tier) in FLAGSHIP.items():
        desc.setdefault(name, purpose)
    for name, spec in SUBAGENTS.items():
        desc.setdefault(name, spec.get("description", ""))
    for name in list(registry["agents"]):
        if desc.get(name):
            continue
        skill = _export_description(name)
        if skill:
            desc[name] = skill

    pipe_of: dict[str, list[str]] = {}
    for pid, cfg in pipes.items():
        pipe_of.setdefault(cfg.get("agent") or "", []).append(pid)

    agents = []
    for name, cfg in sorted(registry["agents"].items()):
        charter = CONV / "agents" / f"{name}_instructions.md"
        agents.append({
            "name": name,
            "description": _first_sentence(desc.get(name, "")),
            "tier": cfg.get("model_tier", "—"),
            "class": profiles["agent_class"].get(name, "—"),
            "tools": cfg.get("tools", []),
            "guardrail": cfg.get("guardrail_policy", "—"),
            "pipelines": sorted(pipe_of.get(name, [])),
            "charter": (f"agents/{name}_instructions.md" if charter.is_file()
                        else f"build/agents/{name}/ (converted)"),
        })

    connections = []
    for name, cfg in sorted(registry["connections"].items()):
        connections.append({
            "name": name,
            "type": cfg.get("type", "—"),
            "spec": cfg.get("spec", "—"),
            "connection": cfg.get("foundry_connection", "—"),
            "enabled": cfg.get("enabled", True),
            "description": _first_sentence(cfg.get("_comment", ""), 300),
        })

    workflows = []
    for wf in sorted((CONV / "workflows").glob("*.json")):
        if wf.name == "pipelines.json":
            continue
        data = json.loads(wf.read_text(encoding="utf-8"))
        trigger = ", ".join((data.get("definition", {})
                             .get("triggers", {}) or {}).keys()) or "—"
        workflows.append({
            "name": wf.stem,
            "trigger": trigger,
            "description": _first_sentence(data.get("_comment", ""), 300),
            "path": f"workflows/{wf.name}",
        })

    pipelines = []
    for pid, cfg in sorted(pipes.items()):
        pipelines.append({
            "id": pid,
            "requirement": cfg.get("requirement", "—"),
            "agent": cfg.get("agent", "—"),
            "format": cfg.get("renderFormat", "—"),
            "template": cfg.get("renderTemplate", "—"),
            "approval": cfg.get("approvalKind", "—"),
            "description": _first_sentence(cfg.get("notes", ""), 300),
        })

    queries = [{"name": p.stem, "path": str(p.relative_to(CONV)),
                "description": _kql_purpose(p)}
               for p in sorted((CONV / "operations" / "kql").glob("*.kql"))
               + sorted((CONV / "infra" / "kql").glob("*.kql"))]

    docs = []
    for folder in ("governance", "operations", "team", "enterprise"):
        for p in sorted((CONV / folder).glob("*.md")):
            docs.append({"name": p.stem, "path": str(p.relative_to(CONV)),
                         "area": folder, "description": _doc_purpose(p)})

    return {
        "generated": date.today().isoformat(),
        "systems": [{"id": i, "title": t, "description": d, "pipelines": p}
                    for i, t, d, p in SYSTEMS],
        "agents": agents,
        "pipelines": pipelines,
        "workflows": workflows,
        "connections": connections,
        "queries": queries,
        "templates": [{"id": t.get("id"), "format": t.get("format", "—"),
                       "renderer": t.get("renderer", "—"),
                       "description": _first_sentence(t.get("description", ""), 240)}
                      for t in templates],
        "docs": docs,
        "develop": [{"change": c, "edit": e, "check": ch, "apply": a, "gate": g}
                    for c, e, ch, a, g in DEVELOP],
    }


# ------------------------------------------------------------------ render
CSS = """
:root{--teal:#008D7F;--dark:#0B3B36;--light:#E4F3F1;--ink:#1B2A4A;
--grey:#5B6B69;--line:#D8E3E1;--bg:#F7FAF9;--warn:#D98324}
*{box-sizing:border-box}
body{margin:0;font:14px/1.55 Verdana,Segoe UI,system-ui,sans-serif;color:var(--ink);background:var(--bg)}
header{background:var(--dark);color:#fff;padding:18px 24px}
header h1{margin:0;font-size:20px;letter-spacing:.3px}
header p{margin:6px 0 0;font-size:12.5px;color:#B9D6D1}
.wrap{max-width:1180px;margin:0 auto;padding:0 20px 60px}
nav{position:sticky;top:0;z-index:5;background:#fff;border-bottom:1px solid var(--line);
padding:10px 20px;display:flex;gap:8px;flex-wrap:wrap;align-items:center}
nav a{font-size:12.5px;text-decoration:none;color:var(--dark);background:var(--light);
border-radius:14px;padding:5px 11px;white-space:nowrap}
nav a:hover{background:var(--teal);color:#fff}
#q{margin-left:auto;padding:6px 10px;border:1px solid var(--line);border-radius:6px;
font:13px Verdana,sans-serif;min-width:220px}
section{margin-top:34px}
h2{color:var(--teal);font-size:17px;margin:0 0 4px;border-bottom:2px solid var(--light);padding-bottom:6px}
.sub{color:var(--grey);font-size:12.5px;margin:0 0 14px}
table{width:100%;border-collapse:collapse;background:#fff;font-size:12.8px}
th{background:var(--teal);color:#fff;text-align:left;padding:7px 9px;font-weight:bold}
td{border-bottom:1px solid var(--line);padding:7px 9px;vertical-align:top}
tr:nth-child(even) td{background:#FBFDFD}
code,.mono{font-family:Consolas,Monaco,monospace;font-size:12px;background:var(--light);
padding:1px 5px;border-radius:3px}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(330px,1fr));gap:12px}
.card{background:#fff;border:1px solid var(--line);border-left:4px solid var(--teal);
border-radius:6px;padding:12px 14px}
.card h3{margin:0 0 4px;font-size:13.5px;color:var(--dark)}
.card .id{display:inline-block;background:var(--dark);color:#fff;border-radius:10px;
padding:1px 8px;font-size:11px;margin-right:6px}
.card p{margin:6px 0 8px;font-size:12.5px;color:#333}
.pill{display:inline-block;background:var(--light);color:var(--dark);border-radius:10px;
padding:1px 8px;font-size:11px;margin:2px 4px 0 0}
.note{background:#FFF8EC;border-left:4px solid var(--warn);padding:10px 14px;
font-size:12.5px;margin:14px 0}
footer{color:var(--grey);font-size:11.5px;margin-top:40px;border-top:1px solid var(--line);padding-top:12px}
.hidden{display:none}
@media print{nav{position:static}#q{display:none}}
"""

JS = """
const q=document.getElementById('q');
q.addEventListener('input',()=>{
  const t=q.value.trim().toLowerCase();
  document.querySelectorAll('[data-row]').forEach(el=>{
    el.classList.toggle('hidden', t.length>1 && !el.textContent.toLowerCase().includes(t));
  });
  document.querySelectorAll('section').forEach(s=>{
    const rows=s.querySelectorAll('[data-row]');
    const any=[...rows].some(r=>!r.classList.contains('hidden'));
    s.classList.toggle('hidden', rows.length>0 && !any);
  });
});
"""


def esc(s) -> str:
    return html.escape(str(s if s is not None else ""), quote=True)


def table(headers, rows, widths=None) -> str:
    def th(label, width):
        style = ' style="width:%s"' % width if width else ""
        return "<th%s>%s</th>" % (style, esc(label))
    head = "".join(th(h, w)
                   for h, w in zip(headers, widths or [None] * len(headers)))
    body = "".join("<tr data-row>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>"
                   for r in rows)
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def section(anchor, title, sub, body) -> str:
    return (f'<section id="{anchor}"><h2>{esc(title)}</h2>'
            f'<p class="sub">{sub}</p>{body}</section>')


def render(cat: dict) -> str:
    nav = "".join(
        f'<a href="#{a}">{esc(t)}</a>' for a, t in [
            ("systems", "Systems a–j"), ("develop", "Develop"),
            ("agents", "Agents"), ("pipelines", "Pipelines"),
            ("workflows", "Workflows"), ("connections", "Connections"),
            ("templates", "Templates"), ("queries", "Dashboards"),
            ("docs", "Runbooks")])

    cards = "".join(
        f'<div class="card" data-row><h3><span class="id">{esc(s["id"])}</span>'
        f'{esc(s["title"])}</h3><p>{esc(s["description"])}</p>'
        + "".join(f'<span class="pill">{esc(p)}</span>'
                  for p in s["pipelines"].split(" · "))
        + "</div>" for s in cat["systems"])

    develop = table(
        ["Change", "Edit", "Check before", "Apply with", "Gate"],
        [[esc(d["change"]), f'<code>{d["edit"]}</code>',
          f'<code>{d["check"]}</code>', f'<code>{d["apply"]}</code>',
          esc(d["gate"])] for d in cat["develop"]],
        ["17%", "22%", "22%", "22%", "17%"])

    agents = table(
        ["Agent", "What it does", "Tier", "Profile", "Tools", "Pipelines", "Charter"],
        [[f'<code>{esc(a["name"])}</code>', esc(a["description"]) or "—",
          esc(a["tier"]), esc(a["class"]), str(len(a["tools"])),
          ", ".join(esc(p) for p in a["pipelines"]) or "—",
          f'<span class="mono">{esc(a["charter"])}</span>']
         for a in cat["agents"]],
        ["13%", "34%", "7%", "8%", "5%", "15%", "18%"])

    pipelines = table(
        ["Pipeline", "Req", "Agent", "Output", "Approval", "Notes"],
        [[f'<code>{esc(p["id"])}</code>', esc(p["requirement"]),
          esc(p["agent"]), f'{esc(p["format"])} / {esc(p["template"]) or "—"}',
          esc(p["approval"]), esc(p["description"]) or "—"]
         for p in cat["pipelines"]],
        ["16%", "6%", "17%", "13%", "15%", "33%"])

    workflows = table(
        ["Workflow", "Trigger", "What it does"],
        [[f'<code>{esc(w["name"])}</code>', esc(w["trigger"]),
          esc(w["description"]) or "—"] for w in cat["workflows"]],
        ["18%", "20%", "62%"])

    connections = table(
        ["Connection", "Type", "Foundry connection", "Read surface"],
        [[f'<code>{esc(c["name"])}</code>'
          + ("" if c["enabled"] else ' <span class="pill">disabled</span>'),
          esc(c["type"]), esc(c["connection"]), esc(c["description"]) or "—"]
         for c in cat["connections"]],
        ["15%", "8%", "17%", "60%"])

    templates = table(
        ["Template", "Format", "Renderer", "Used for"],
        [[f'<code>{esc(t["id"])}</code>', esc(t["format"]),
          f'<span class="mono">{esc(t["renderer"])}</span>',
          esc(t["description"]) or "—"] for t in cat["templates"]],
        ["18%", "8%", "24%", "50%"])

    queries = table(
        ["Query", "Answers", "Path"],
        [[f'<code>{esc(q["name"])}</code>', esc(q["description"]) or "—",
          f'<span class="mono">{esc(q["path"])}</span>']
         for q in cat["queries"]],
        ["16%", "60%", "24%"])

    docs = table(
        ["Document", "Area", "Purpose"],
        [[f'<span class="mono">{esc(d["path"])}</span>', esc(d["area"]),
          esc(d["description"]) or "—"] for d in cat["docs"]],
        ["26%", "10%", "64%"])

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ENX Assurance Console</title><style>{CSS}</style></head><body>
<header>
  <h1>ENX Assurance Console</h1>
  <p>Every system, agent, pipeline, workflow, connection, dashboard and runbook
     of the InfoSec Assurance platform — generated from the kit on
     {esc(cat['generated'])}. Search filters every table below.</p>
</header>
<nav>{nav}<input id="q" type="search" placeholder="Filter everything…"
  aria-label="Filter"></nav>
<div class="wrap">
<div class="note"><b>This page is generated, never edited.</b> It is rebuilt by
<code>python3 scripts/build_console.py</code> from the registries themselves,
so it cannot describe an agent the platform does not have, and a new agent
appears here the moment it is registered. Everything it names is read-only or
gated: launching a pipeline still requires the verifier to pass and a person to
approve.</div>
{section("systems", "The ten systems (a–j)",
         "What the team asked for, and the pipeline that delivers it. "
         "Full record: <span class='mono'>REQUIREMENTS.md</span>.",
         f'<div class="cards">{cards}</div>')}
{section("develop", "Develop the platform",
         "The owner's change map: what to edit, what to run before, how to "
         "apply it, and which gate it has to pass. Every command is real.",
         develop)}
{section("agents", "Agents",
         "Registered agents with their model tier, inference-profile class, "
         "attached read-only tools and the pipelines they serve.", agents)}
{section("pipelines", "Delivery pipelines",
         "One generic delivery pipeline, instantiated per deliverable type — "
         "so the approval gate, the storage rule and the audit trail exist "
         "once and cannot drift between report types.", pipelines)}
{section("workflows", "Workflows", "Logic Apps definitions: schedules, "
         "intakes, approval flows and platform utilities.", workflows)}
{section("connections", "Connections and tools",
         "Read-only by construction: non-GET operations are stripped at "
         "deployment, so no agent can write to any of these systems.",
         connections)}
{section("templates", "Templates", "The deliverable templates of record and "
         "the renderer that produces each file.", templates)}
{section("queries", "Dashboards and queries",
         "The KQL behind the monitoring workbook and the alerts — cost, "
         "latency, cache, verifier quality, egress, drift.", queries)}
{section("docs", "Runbooks, governance and team documents",
         "Each document's own first line, so the index cannot drift from what "
         "the documents actually say.", docs)}
<footer>ENX InfoSec Assurance platform · generated from the conversion kit ·
Euronext Internal · no credentials, no personal data, placeholders only.</footer>
</div><script>{JS}</script></body></html>
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true",
                    help="CI: fail if any item has no description")
    ap.add_argument("--out", default=str(BUILD / "console"))
    args = ap.parse_args()

    cat = collect()
    if args.check:
        missing = []
        for a in cat["agents"]:
            if not a["description"]:
                missing.append(f"agent {a['name']}: no description")
        for c in cat["connections"]:
            if not c["description"]:
                missing.append(f"connection {c['name']}: no _comment")
        for w in cat["workflows"]:
            if not w["description"]:
                missing.append(f"workflow {w['name']}: no _comment")
        for q in cat["queries"]:
            if not q["description"]:
                missing.append(f"query {q['name']}: no header comment")
        if missing:
            print(f"console: {len(missing)} undescribed item(s) — the console "
                  f"is only as useful as the descriptions it reads",
                  file=sys.stderr)
            for m in missing:
                print("  - " + m, file=sys.stderr)
            return 1
        print(f"console OK — {len(cat['agents'])} agents, "
              f"{len(cat['pipelines'])} pipelines, {len(cat['workflows'])} "
              f"workflows, {len(cat['connections'])} connections, "
              f"{len(cat['queries'])} queries, {len(cat['docs'])} documents, "
              f"all described")
        return 0

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "catalog.json").write_text(
        json.dumps(cat, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    page = out / "enx-console.html"
    page.write_text(render(cat), encoding="utf-8")
    print(f"wrote {page} ({page.stat().st_size // 1024} KiB) and catalog.json — "
          f"{len(cat['agents'])} agents, {len(cat['pipelines'])} pipelines, "
          f"{len(cat['workflows'])} workflows, {len(cat['connections'])} "
          f"connections, {len(cat['queries'])} queries, {len(cat['docs'])} docs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
