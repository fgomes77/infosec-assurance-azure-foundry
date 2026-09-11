#!/usr/bin/env python3
"""Generate the project dossier infographics (flat style, ENX teal)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from pathlib import Path

OUT = Path(__file__).resolve().parent
TEAL, DARK, LIGHT = "#008D7F", "#0B3B36", "#E4F3F1"
AMBER, RED, GREY, WHITE = "#E8A33D", "#C0504D", "#5B6B69", "#FFFFFF"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})


def box(ax, x, y, w, h, text, fc=TEAL, tc=WHITE, fs=10, ec="none", bold=True):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.12",
                                fc=fc, ec=ec, lw=1.2, mutation_aspect=0.6))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", color=tc,
            fontsize=fs, fontweight="bold" if bold else "normal", wrap=True)


def arrow(ax, x1, y1, x2, y2, color=DARK, style="-|>", lw=1.8, ls="-"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style, lw=lw,
                                 color=color, linestyle=ls, mutation_scale=16))


def canvas(w=12, h=7.2):
    fig, ax = plt.subplots(figsize=(w, h), dpi=160)
    ax.set_xlim(0, 12); ax.set_ylim(0, 7.2); ax.axis("off")
    return fig, ax


def title(ax, t):
    ax.text(6, 6.9, t, ha="center", fontsize=15, fontweight="bold", color=DARK)


def save(fig, name):
    fig.savefig(OUT / name, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("wrote", name)


# 1 ─ Solution architecture (layers) -----------------------------------------
fig, ax = canvas()
title(ax, "Solution Architecture — InfoSec Assurance on Azure AI Foundry")
layers = [
    (5.85, "ACCESS", GREY, [("MCP server\n(Claude / clients)", 0.4), ("Microsoft 365 Copilot\n(Copilot Studio)", 4.2), ("Logic Apps workflows\n(schedules & events)", 8.0)]),
    (4.55, "ORCHESTRATION", TEAL, [("infosec-assurance-orchestrator  ·  planner-executor  ·  reasoning model + web search", 0.4)]),
    (3.25, "AGENTS", TEAL, [("assurance advisor\nreasoning + memory", 0.4), ("output-verifier\nPASS / FAIL rules", 3.2), ("18 GRC/TPRM specialists\nDORA·NIS2·ISO·DeepSearch", 6.0), ("4 document agents\ndocx·pdf·pptx·xlsx", 8.8)]),
    (1.95, "KNOWLEDGE & TOOLS", AMBER, [("vector stores (RAG)\ncombined + per-agent + memory", 0.4), ("code interpreter\nscripts & templates", 4.2), ("read-only OpenAPI tools\n+ ENX gateway MCP", 8.0)]),
    (0.65, "AZURE FOUNDATION", DARK, [("Foundry project\ngpt-4o + o3-mini", 0.4), ("Key Vault & Entra\nconnections, RBAC", 3.2), ("App Insights\ntraces & metrics", 6.0), ("Storage & Bing\ndeliverables, search", 8.8)]),
]
for y, label, color, boxes in layers:
    ax.text(0.05, y + 0.5, label, fontsize=8, color=GREY, rotation=90, va="center")
    for text, x in boxes:
        w = 11.2 if len(boxes) == 1 else (2.65 if len(boxes) == 4 else 3.4)
        box(ax, x, y, w, 1.0, text, fc=color, fs=8.4 if len(boxes) > 1 else 10)
for y in (5.75, 4.45, 3.15, 1.85):
    arrow(ax, 6, y, 6, y - 0.18)
save(fig, "01-solution-architecture.png")

# 2 ─ Conversion pipeline -----------------------------------------------------
fig, ax = canvas(12, 5.2)
ax.set_ylim(0, 5.2)
ax.text(6, 4.9, "Conversion & Deployment Pipeline (deploy.sh — each gate must pass)",
        ha="center", fontsize=15, fontweight="bold", color=DARK)
steps = [("claude.ai\nskill export\n(35 skills)", GREY), ("convert_skills.py\nskills → agent\ndefinitions", TEAL),
         ("verify_conversion.py\nbyte-fidelity vs\nexport  ✓", AMBER), ("create_agents.py\n22 agents +\nknowledge + code", TEAL),
         ("attach_integrations\nread-only tools\n+ model tiers", TEAL), ("create_orchestrator\nadvisor · verifier ·\norchestrator", TEAL),
         ("smoke test\nvia orchestrator", DARK)]
x = 0.15
for i, (t, c) in enumerate(steps):
    box(ax, x, 2.6, 1.55, 1.5, t, fc=c, fs=8)
    if i < len(steps) - 1:
        arrow(ax, x + 1.6, 3.35, x + 2.03, 3.35)
    x += 1.68
box(ax, 1.9, 0.7, 8.2, 1.0, "Reliability substrate: retry + backoff · parallel uploads · content-hash cache ·\nper-agent failure isolation · any failed gate stops the pipeline", fc=LIGHT, tc=DARK, fs=9, bold=False)
arrow(ax, 6, 2.5, 6, 1.8, color=GREY, ls=":")
save(fig, "02-conversion-pipeline.png")

# 3 ─ Release & approval flow -------------------------------------------------
fig, ax = canvas(12, 5.6)
ax.set_ylim(0, 5.6)
ax.text(6, 5.3, "Release Path — Every Submission of Record", ha="center",
        fontsize=15, fontweight="bold", color=DARK)
box(ax, 0.2, 3.4, 2.2, 1.2, "Specialist agent\nproduces draft", fc=TEAL, fs=9)
box(ax, 2.95, 3.4, 2.2, 1.2, "Reflexive\nself-check\n(report agents)", fc=TEAL, fs=9)
box(ax, 5.7, 3.4, 2.2, 1.2, "output-verifier\ndeterministic rules\nPASS / FAIL", fc=AMBER, fs=9)
box(ax, 8.45, 3.4, 2.2, 1.2, "HUMAN APPROVAL\nexplicit 'approved'\n(3-layer control)", fc=RED, fs=9)
box(ax, 8.45, 1.2, 2.2, 1.2, "Gated workflow\nsubmits: Jira · IAF ·\nSharePoint · OneTrust", fc=DARK, fs=9)
arrow(ax, 2.45, 4.0, 2.9, 4.0); arrow(ax, 5.2, 4.0, 5.65, 4.0); arrow(ax, 7.95, 4.0, 8.4, 4.0)
arrow(ax, 9.55, 3.35, 9.55, 2.45)
arrow(ax, 6.4, 3.35, 1.5, 3.35, color=RED, ls="--"); ax.text(3.6, 2.85, "FAIL → rework (max 2)", fontsize=8.5, color=RED)
arrow(ax, 9.1, 3.35, 1.2, 2.6, color=RED, ls="--"); ax.text(5.4, 2.25, "rejected / edits → new draft", fontsize=8.5, color=RED)
box(ax, 0.2, 0.5, 6.6, 0.9, "Technical backstop: agents hold READ-ONLY tools (writes stripped) — submission is\nphysically possible only through the human-approved workflow path", fc=LIGHT, tc=DARK, fs=8.5, bold=False)
save(fig, "03-release-approval-flow.png")

# 4 ─ Integration map ---------------------------------------------------------
fig, ax = canvas(12, 7.2)
title(ax, "Interconnections — Euronext Technology Stack")
box(ax, 4.3, 3.0, 3.4, 1.3, "Foundry agents\norchestrator · advisor\nspecialists", fc=TEAL, fs=10)
spokes = [
    ("Jira Cloud\ntickets & JQL", 0.4, 5.4), ("Jira Assets CMDB\nDORA RoI · AQL", 4.3, 5.6),
    ("OneTrust\nassessments · vendors", 8.4, 5.4), ("SecurityScorecard\nexternal ratings", 0.4, 3.1),
    ("Microsoft Defender\nincidents · hunting", 8.4, 3.1), ("SharePoint\nevidence · deliverables", 0.4, 0.8),
    ("IAF API (internal)\nfindings · controls", 4.3, 0.6), ("ENX Gateway MCP\ninternal tools", 8.4, 0.8),
]
for t, x, y in spokes:
    box(ax, x, y, 3.2, 1.0, t, fc=WHITE, tc=DARK, fs=9, ec=TEAL)
    cx, cy = x + 1.6, y + 0.5
    ax.add_patch(FancyArrowPatch((6, 3.65), (cx, cy), arrowstyle="<|-|>",
                                 lw=1.2, color=GREY, mutation_scale=14,
                                 shrinkA=52, shrinkB=58))
box(ax, 4.3, 1.9, 3.4, 0.75, "Bing web search (grounded citations)", fc=AMBER, fs=8.5)
ax.text(6, 0.12, "reads: unrestricted (least-privilege scopes)   ·   writes: only via approval-gated Logic Apps",
        fontsize=9.5, color=GREY, ha="center")
save(fig, "04-integration-map.png")

# 5 ─ Implementation roadmap --------------------------------------------------
fig, ax = canvas(12, 5.6)
ax.set_ylim(0, 5.6)
ax.text(6, 5.3, "Implementation Roadmap", ha="center", fontsize=15,
        fontweight="bold", color=DARK)
phases = [
    ("Phase 1 · Wk 1\nFoundation", "Provision infra (Bicep)\nEntra roles · Key Vault\nconnections", TEAL),
    ("Phase 2 · Wk 2\nAgents", "deploy.sh pipeline\n22 agents + advisor +\nverifier + orchestrator", TEAL),
    ("Phase 3 · Wk 3-4\nIntegrations", "conn-* credentials\nIAF & ENX specs aligned\nread-only validation", AMBER),
    ("Phase 4 · Wk 5\nWorkflows & UAT", "Logic Apps + approval\nwiring · Copilot pilot ·\nteam UAT vs claude.ai", AMBER),
    ("Phase 5 · Wk 6\nGo-live", "hypercare · metrics\nbaseline · ISO 42001 /\nAI Act assessment", DARK),
]
x = 0.3
for i, (h, b, c) in enumerate(phases):
    box(ax, x, 3.1, 2.1, 1.4, h, fc=c, fs=9)
    box(ax, x, 1.3, 2.1, 1.6, b, fc=LIGHT, tc=DARK, fs=8, bold=False)
    if i < 4:
        arrow(ax, x + 2.15, 3.8, x + 2.5, 3.8)
    x += 2.35
box(ax, 0.3, 0.25, 11.1, 0.7, "Exit criteria per phase: verification green · zero write grants · approval gates tested end-to-end · UAT outputs match claude.ai baselines",
    fc=WHITE, tc=GREY, fs=9, ec=GREY, bold=False)
save(fig, "05-implementation-roadmap.png")
