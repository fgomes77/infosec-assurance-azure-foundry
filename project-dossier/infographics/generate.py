#!/usr/bin/env python3
"""Project dossier infographics — reference-grade visual style:
pastel panels, rounded cards, badges, chips, labeled connectors."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle
from pathlib import Path

OUT = Path(__file__).resolve().parent

# ---- design system ----------------------------------------------------------
NAVY = "#1B2A4A"          # titles / body text
INK = "#33415C"           # secondary text
TEAL = "#008D7F"          # brand accent
GREEN, GREEN_BG = "#2E8B57", "#EDF7EF"
BLUE, BLUE_BG = "#3B6FC9", "#EEF3FB"
ORANGE, ORANGE_BG = "#D98324", "#FDF3E7"
PURPLE, PURPLE_BG = "#7A5FBF", "#F3EFFA"
RED, RED_BG = "#C0504D", "#FBEFEF"
TEAL_BG = "#E4F3F1"
GREY, GREY_BG = "#8A94A6", "#F4F6F9"
WHITE = "#FFFFFF"
plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": NAVY,
                     "font.size": 10})

def fig_ax(w, h):
    f, ax = plt.subplots(figsize=(w, h), dpi=200)
    ax.set_xlim(0, w); ax.set_ylim(0, h); ax.axis("off")
    f.patch.set_facecolor(WHITE)
    return f, ax

def rbox(ax, x, y, w, h, fc, ec="none", lw=1.4, r=0.10):
    ax.add_patch(FancyBboxPatch((x, y), w, h, fc=fc, ec=ec, lw=lw,
                 boxstyle=f"round,pad=0,rounding_size={r}", mutation_aspect=1))

def txt(ax, x, y, s, size=9, color=NAVY, bold=False, ha="center", va="center"):
    ax.text(x, y, s, fontsize=size, color=color, ha=ha, va=va,
            fontweight="bold" if bold else "normal", linespacing=1.45)

def card(ax, x, y, w, h, title, body="", ec=TEAL, fc=WHITE, ts=9.5, bs=8.2,
         title_color=None):
    rbox(ax, x, y, w, h, fc, ec, 1.6)
    if body:
        txt(ax, x + w / 2, y + h - 0.30, title, ts, title_color or ec, True)
        txt(ax, x + w / 2, y + (h - 0.52) / 2, body, bs, INK)
    else:
        txt(ax, x + w / 2, y + h / 2, title, ts, title_color or NAVY, True)

def badge(ax, x, y, n, color, r=0.17, fs=10):
    ax.add_patch(Circle((x, y), r, fc=color, ec="none"))
    txt(ax, x, y - 0.005, str(n), fs, WHITE, True)

def chip(ax, x, y, s, ok=True, size=8.2):
    c = GREEN if ok else RED
    ax.add_patch(Circle((x, y), 0.105, fc=c, ec="none"))
    txt(ax, x, y - 0.004, "✓" if ok else "✗", 7.5, WHITE, True)
    txt(ax, x + 0.24, y, s, size, INK, ha="left")

def arr(ax, x1, y1, x2, y2, color=INK, lw=1.7, ls="-", style="-|>",
        shrinkA=2, shrinkB=2, connectionstyle=None):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style, lw=lw,
                 color=color, linestyle=ls, mutation_scale=15,
                 shrinkA=shrinkA, shrinkB=shrinkB,
                 connectionstyle=connectionstyle or "arc3,rad=0"))

def header(ax, W, H, title, subtitle):
    txt(ax, W / 2, H - 0.42, title, 19, NAVY, True)
    txt(ax, W / 2, H - 0.80, subtitle, 10, GREY)

def footer_bar(ax, x, y, w, text, fc=GREY_BG, ec=GREY, tc=INK):
    rbox(ax, x, y, w, 0.62, fc, ec, 1.0)
    txt(ax, x + w / 2, y + 0.31, text, 8.8, tc)

def save(f, name):
    f.savefig(OUT / name, bbox_inches="tight", facecolor=WHITE, pad_inches=0.15)
    plt.close(f)
    print("wrote", name)

# ═════════════════ 1 · SOLUTION ARCHITECTURE ════════════════════════════════
W, H = 13, 9.2
f, ax = fig_ax(W, H)
header(ax, W, H, "Solution Architecture — InfoSec Assurance on Microsoft Foundry",
       "Five layers · every access path converges on the orchestrator · agents draw on governed knowledge and read-only tools")

bands = [
    (6.92, 1.10, "ACCESS", BLUE, BLUE_BG,
     [("MCP server", "Claude Desktop / Code,\ninternal MCP clients"),
      ("Microsoft 365 Copilot", "Copilot Studio agent\nin Teams & Copilot chat"),
      ("Logic Apps workflows", "schedules & events,\napproval-gated")]),
    (5.62, 1.02, "ORCHESTRATION", TEAL, TEAL_BG,
     [("infosec-assurance-orchestrator", "planner–executor · o3-mini reasoning · web search · routes, decomposes, aggregates")]),
    (4.14, 1.10, "AGENTS", TEAL, TEAL_BG,
     [("assurance advisor", "reasoning generalist\n+ durable memory"),
      ("output-verifier", "independent PASS/FAIL\nrules · generates nothing"),
      ("18 GRC/TPRM specialists", "DORA · NIS2 · EU AI Act · ISO\nDeepSearch · DPIA · CISO…"),
      ("4 document agents", "docx · pdf\npptx · xlsx")]),
    (2.66, 1.10, "KNOWLEDGE & TOOLS", ORANGE, ORANGE_BG,
     [("Vector stores — RAG", "combined + per-agent\n+ team memory"),
      ("Code interpreter", "generation scripts\n& canonical templates"),
      ("Read-only OpenAPI + MCP", "writes stripped · ENX\ngateway MCP tools")]),
    (1.18, 1.10, "AZURE FOUNDATION", PURPLE, PURPLE_BG,
     [("Foundry project", "gpt-4o + o3-mini\ndeployments"),
      ("Entra ID + Key Vault", "RBAC, connections,\nno local auth"),
      ("App Insights", "traces · tokens ·\napproval evidence"),
      ("Storage + Bing", "deliverables ·\ngrounded search")]),
]
for y, h, label, ec, bg, cards in bands:
    rbox(ax, 0.35, y - 0.14, W - 0.7, h + 0.42, bg, "none", r=0.14)
    rbox(ax, 0.55, y + h - 0.14, 2.35, 0.36, ec, "none", r=0.16)
    txt(ax, 0.55 + 1.175, y + h + 0.04, label, 8.3, WHITE, True)
    n = len(cards)
    total_w = W - 1.5
    cw = (total_w - 0.3 * (n - 1)) / n
    x = 0.75
    for t, b in cards:
        card(ax, x, y - 0.02, cw, h - 0.10, t, b, ec=ec, ts=9.2 if n > 1 else 10.5,
             bs=7.9)
        x += cw + 0.3
for y in (6.89, 5.58, 4.10, 2.62):
    arr(ax, W / 2, y - 0.10, W / 2, y - 0.30, color=GREY, lw=2.2)
footer_bar(ax, 0.35, 0.28, W - 0.7,
           "Identity everywhere: Entra ID · Secrets: Key Vault-backed Foundry connections · Writes leave this platform only through human-approved workflows")
save(f, "01-solution-architecture.png")

# ═════════════════ 2 · CONVERSION PIPELINE ══════════════════════════════════
W, H = 13, 6.6
f, ax = fig_ax(W, H)
header(ax, W, H, "Conversion & Deployment Pipeline",
       "deploy.sh — six steps, each gated on the previous; fidelity verification stands between source and cloud")

steps = [
    ("claude.ai\nexport", "35 skills · persona\nknowledge · templates\n(source of truth)", GREY, GREY_BG),
    ("convert\nskills", "SKILL.md → instructions\nreferences → RAG\nscripts → interpreter", TEAL, TEAL_BG),
    ("verify\nconversion", "SHA-256 fidelity\nrules completeness\nfreshness markers", ORANGE, ORANGE_BG),
    ("create\nagents", "22 agents · vector\nstores · code tools\nidempotent by name", TEAL, TEAL_BG),
    ("attach\nintegrations", "read-only OpenAPI\nMCP · web search\nmodel tiers", TEAL, TEAL_BG),
    ("create\norchestrator", "advisor + memory\noutput-verifier\norchestrator wiring", TEAL, TEAL_BG),
    ("smoke\ntest", "end-to-end run\nvia the\norchestrator", GREEN, GREEN_BG),
]
n = len(steps); cw = (W - 1.0 - 0.34 * (n - 1)) / n; x = 0.5
for i, (t, b, ec, bg) in enumerate(steps):
    rbox(ax, x, 2.85, cw, 1.95, bg, ec, 1.6)
    badge(ax, x + cw / 2, 4.80, i + 1, ec, r=0.19, fs=10)
    txt(ax, x + cw / 2, 4.30, t, 8.6, ec, True)
    txt(ax, x + cw / 2, 3.45, b, 7.3, INK)
    if i < n - 1:
        arr(ax, x + cw + 0.02, 3.8, x + cw + 0.32, 3.8, color=INK, lw=2.0)
    x += cw + 0.34
txt(ax, 2.62, 2.52, "GATE: a failed verification stops the pipeline — drifted definitions never deploy",
    8.4, ORANGE, True, ha="left")
arr(ax, 2.5, 2.60, 2.28, 2.82, color=ORANGE, lw=1.4, ls="--")
rbox(ax, 0.5, 0.95, W - 1.0, 1.25, GREY_BG, GREY, 1.2)
txt(ax, W / 2, 1.92, "Reliability substrate", 9.5, NAVY, True)
for i, s in enumerate(["retry + exponential backoff on every Azure call",
                       "parallel uploads (8-way) with content-hash cache",
                       "per-agent failure isolation, non-zero exit on any failure",
                       "re-sync = the same command on a fresh export"]):
    chip(ax, 0.95 + (i % 2) * 6.1, 1.55 - (i // 2) * 0.38, s, True)
save(f, "02-conversion-pipeline.png")

# ═════════════════ 3 · RELEASE & APPROVAL FLOW ══════════════════════════════
W, H = 13, 6.9
f, ax = fig_ax(W, H)
header(ax, W, H, "Release Path — Every Submission of Record",
       "Reflexive self-check → independent verifier → human approval → gated submission (defence in depth)")

flow = [
    ("Specialist agent", "produces the complete\ndraft deliverable", TEAL, TEAL_BG),
    ("Reflexive self-check", "report agents critique\n& fix once (max 2)", TEAL, TEAL_BG),
    ("output-verifier", "deterministic rules:\ncompleteness · thresholds ·\ncitations · minimisation", ORANGE, ORANGE_BG),
    ("HUMAN APPROVAL", "explicit 'approved' in\nconversation or Teams\ncallback — 3-day expiry", RED, RED_BG),
    ("Gated workflow", "submits of record:\nJira · IAF · SharePoint\n· OneTrust", PURPLE, PURPLE_BG),
]
n = len(flow); cw = 2.05; gap = (W - 1.0 - n * cw) / (n - 1); x = 0.5
centers = []
for i, (t, b, ec, bg) in enumerate(flow):
    rbox(ax, x, 3.45, cw, 1.85, bg, ec, 1.7)
    txt(ax, x + cw / 2, 5.02, t, 9.0, ec, True)
    txt(ax, x + cw / 2, 4.18, b, 7.6, INK)
    centers.append(x + cw / 2)
    if i < n - 1:
        arr(ax, x + cw + 0.03, 4.38, x + cw + gap - 0.03, 4.38, color=INK, lw=2.0)
    x += cw + gap
# fail loops
arr(ax, centers[2], 3.40, centers[0], 3.40, color=RED, lw=1.6, ls="--",
    connectionstyle="arc3,rad=-0.22")
txt(ax, (centers[0] + centers[2]) / 2, 2.68, "FAIL → findings back to producer (max 2 retries)", 8.2, RED)
arr(ax, centers[3], 3.40, centers[0] - 0.35, 3.35, color=RED, lw=1.6, ls="--",
    connectionstyle="arc3,rad=-0.34")
txt(ax, 9.0, 2.30, "rejected / edit request →\nfresh draft, cycle restarts", 8.2, RED)
# verdict chips
chip(ax, 4.35, 5.62, "PASS → forwarded to approver", True)
chip(ax, 8.05, 5.62, "approval logged in run history", True)
rbox(ax, 0.5, 0.50, W - 1.0, 1.05, TEAL_BG, TEAL, 1.2)
txt(ax, W / 2, 1.26, "Technical backstop — Layer 1", 9.3, TEAL, True)
txt(ax, W / 2, 0.85,
    "Agents hold READ-ONLY tools (every non-GET operation stripped; write grants: zero).\nSubmission is physically possible only through the human-approved workflow path.",
    8.2, INK)
save(f, "03-release-approval-flow.png")

# ═════════════════ 4 · INTEGRATION MAP ══════════════════════════════════════
W, H = 13, 9.15
f, ax = fig_ax(W, H)
header(ax, W, H, "Interconnections — Euronext Technology Stack",
       "Declared once in registry.json · credentials in Key Vault-backed connections · least-privilege Entra scopes")

groups = [
    ("ATLASSIAN", BLUE, BLUE_BG, 0.45, 5.05,
     [("Jira Cloud", "remediation & finding\ntickets · JQL"),
      ("Jira Assets CMDB", "DORA RoI · AQL ·\nconcentration risk")]),
    ("MICROSOFT", PURPLE, PURPLE_BG, 9.35, 5.05,
     [("Defender (Graph)", "incidents · alerts ·\nKQL hunting"),
      ("SharePoint (Graph)", "evidence reads ·\ndeliverable publishing")]),
    ("RISK & GRC", ORANGE, ORANGE_BG, 0.45, 1.05,
     [("OneTrust", "assessments ·\nvendor inventory"),
      ("SecurityScorecard", "external security\nratings evidence")]),
    ("INTERNAL", GREEN, GREEN_BG, 9.35, 1.05,
     [("IAF API", "findings · controls\n(template → align spec)"),
      ("ENX Gateway MCP", "internal tools\n(allow-listed)")]),
]
for label, ec, bg, gx, gy, cards in groups:
    rbox(ax, gx, gy, 3.2, 3.0, bg, "none", r=0.14)
    rbox(ax, gx + 0.2, gy + 2.62, 1.7, 0.34, ec, "none", r=0.16)
    txt(ax, gx + 1.05, gy + 2.79, label, 8.0, WHITE, True)
    for i, (t, b) in enumerate(cards):
        card(ax, gx + 0.2, gy + 1.36 - i * 1.18, 2.8, 1.1, t, b, ec=ec, ts=8.8, bs=7.6)
# hub
rbox(ax, 4.7, 3.35, 3.6, 2.15, TEAL, "none", r=0.16)
txt(ax, 6.5, 5.12, "Microsoft Foundry agents", 10.5, WHITE, True)
txt(ax, 6.5, 4.52, "orchestrator · advisor · verifier\n22 specialists", 8.6, WHITE)
rbox(ax, 4.9, 3.52, 3.2, 0.5, "#0B6E63", "none", r=0.12)
txt(ax, 6.5, 3.77, "Bing web search — grounded citations", 7.9, WHITE, True)
for x1, y1 in [(3.65, 6.4), (9.35, 6.4), (3.65, 2.4), (9.35, 2.4)]:
    arr(ax, 6.5, 4.4, x1, y1, color=GREY, lw=1.5, style="<|-|>", shrinkA=68, shrinkB=6)
# legend chips
chip(ax, 4.2, 0.62, "READS: broad, least-privilege scopes", True)
chip(ax, 7.6, 0.62, "WRITES: only via approval-gated Logic Apps", False)
save(f, "04-integration-map.png")

# ═════════════════ 5 · IMPLEMENTATION ROADMAP ═══════════════════════════════
W, H = 13, 7.6
f, ax = fig_ax(W, H)
header(ax, W, H, "Implementation Roadmap",
       "Five phases over six weeks · every phase closes on verifiable exit criteria")

phases = [
    ("1", "Foundation", "Week 1", BLUE, BLUE_BG,
     ["Bicep deployment", "Entra apps + consent", "Azure AI User roles", "Key Vault population"],
     "Infra live · roles effective"),
    ("2", "Agents", "Week 2", TEAL, TEAL_BG,
     ["deploy.sh pipeline", "22 agents + advisor", "verifier +\norchestrator", "smoke tests green"],
     "Verified · 0 write grants"),
    ("3", "Integrations", "Weeks 3–4", ORANGE, ORANGE_BG,
     ["conn-* credentials", "IAF spec alignment", "ENX gateway allowlist", "per-system read tests"],
     "Live data in agent runs"),
    ("4", "Workflows\n& UAT", "Week 5", PURPLE, PURPLE_BG,
     ["Logic Apps deployed", "Teams approval wiring", "Copilot pilot", "UAT vs claude.ai\nbaselines"],
     "Gates proven · UAT sign-off"),
    ("5", "Go-live", "Week 6", GREEN, GREEN_BG,
     ["hypercare", "metrics baseline", "ISO 42001 / AI Act\ndeployer assessment"],
     "Steering acceptance"),
]
n = len(phases); cw = (W - 1.0 - 0.35 * (n - 1)) / n; x = 0.5
for num, name, wk, ec, bg, items, exit_c in phases:
    rbox(ax, x, 1.55, cw, 4.7, bg, ec, 1.6)
    badge(ax, x + 0.36, 5.85, num, ec, r=0.2, fs=11)
    txt(ax, x + cw / 2 + 0.22, 5.85, name, 9.2, ec, True)
    txt(ax, x + cw / 2, 5.42, wk, 8.0, GREY, True)
    for i, it in enumerate(items):
        chip(ax, x + 0.30, 4.92 - i * 0.62, it, True, size=7.3)
    rbox(ax, x + 0.14, 1.70, cw - 0.28, 0.72, WHITE, ec, 1.2)
    txt(ax, x + cw / 2, 2.22, "EXIT", 6.6, GREY, True)
    txt(ax, x + cw / 2, 1.96, exit_c, 6.9, ec, True)
    if num != "5":
        arr(ax, x + cw + 0.02, 3.9, x + cw + 0.34, 3.9, color=INK, lw=2.0)
    x += cw + 0.35
footer_bar(ax, 0.5, 0.55, W - 1.0,
           "Global exit criteria: verification green on every deployment · zero write grants · approval gates tested end-to-end · UAT outputs match claude.ai baselines")
save(f, "05-implementation-roadmap.png")

# ═════════════════ 6 · WORKFLOW SCHEMATICS ══════════════════════════════════
W, H = 13, 9.05
f, ax = fig_ax(W, H)
header(ax, W, H, "Automated Workflows — Logic Apps with Human-Approval Gates",
       "Four pipelines replace claude.ai Routines · every submission of record suspends until a person approves (3-day expiry)")

def lane(y, name, trigger, steps_, ec, bg):
    rbox(ax, 0.45, y, W - 0.9, 1.62, bg, "none", r=0.12)
    txt(ax, 0.70, y + 1.30, name, 9.2, ec, True, ha="left")
    rbox(ax, 0.68, y + 0.30, 1.55, 0.72, ec, "none", r=0.12)
    txt(ax, 1.455, y + 0.66, trigger, 7.6, WHITE, True)
    x = 2.55
    for si, (t, kind) in enumerate(steps_):
        w = 1.62 if kind != "gate" else 1.5
        if kind == "gate":
            rbox(ax, x, y + 0.30, w, 0.72, RED_BG, RED, 1.5)
            txt(ax, x + w / 2, y + 0.80, "APPROVAL", 7.0, RED, True)
            txt(ax, x + w / 2, y + 0.50, t, 6.8, INK)
        else:
            rbox(ax, x, y + 0.30, w, 0.72, WHITE, ec, 1.3)
            txt(ax, x + w / 2, y + 0.66, t, 7.2, INK)
        nx = x + w + 0.24
        if si < len(steps_) - 1:
            arr(ax, x + w + 0.02, y + 0.66, nx - 0.02, y + 0.66, color=INK, lw=1.5)
        x = nx

lane(6.35, "onetrust-assessment-intake", "DAILY",
     [("fetch completed\nassessments", "s"), ("dpia agent\n→ report", "s"),
      ("suspend until\napproved", "gate"), ("upload to\nSharePoint", "s"),
      ("Teams\nsummary", "s")], BLUE, BLUE_BG)
lane(4.45, "defender-incident-brief", "WEBHOOK",
     [("cyber-forum\nbrief", "s"), ("200 → caller\n(no blocking)", "s"),
      ("suspend until\napproved", "gate"), ("create Jira\nissue", "s")],
     PURPLE, PURPLE_BG)
lane(2.55, "scheduled-deepsearch", "WEEKLY",
     [("watchlist from\nSharePoint", "s"), ("deepsearch per\nsupplier", "s"),
      ("suspend until\napproved", "gate"), ("dashboard →\nSharePoint", "s"),
      ("low score →\n2nd gate → Jira", "s")], ORANGE, ORANGE_BG)
lane(0.65, "jira-finding-sync", "HOURLY",
     [("JQL: updated\nTPRM findings", "s"), ("suspend until\napproved", "gate"),
      ("submit status\nto IAF API", "s"), ("Jira comment\non failure", "s")],
     GREEN, GREEN_BG)
save(f, "06-workflow-schematics.png")
