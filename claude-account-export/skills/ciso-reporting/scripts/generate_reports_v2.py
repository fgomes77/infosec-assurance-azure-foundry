#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_reports_v2.py
=======================================================================
CISO ExecSummary skill — canonical pipeline ORCHESTRATOR (v2).

One command turns a verified OneTrust Infosec Form v14 assessment into the
three Group CISO Governance Meeting deliverables:

    1.  {Vendor}_CISO_ExecSummary.html        interactive dashboard
    2.  {Vendor}_CISO_ExecSummary.pdf         A3 landscape (Playwright)
    3.  {Vendor}_CISO_TPRM_Governance.pptx    8-slide deck (token render)

INPUT CONTRACT
--------------
The orchestrator consumes a *verified* assessment JSON — the canonical
extracted shape. PDF -> JSON extraction is intentionally NOT done here:
OneTrust v14 exports are OCR-noisy and vendor-tunable, so extraction lives
in the separate `extract_pdf.py`, and a human verifies the JSON before this
runs (the data-accuracy lesson from the 3/3-vs-2/3 KPI miss).

    python generate_reports_v2.py --assessment vendor.json \\
           --template Group_CISO_Report_Template_v3.1.pptx \\
           --outdir /mnt/user-data/outputs

    python generate_reports_v2.py --demo          # synthetic self-test

PIPELINE  (declarative-prompt phases 2-9; phase 1 = extract_pdf.py)
    classify -> domain scores -> thresholds -> perimeter -> rationale
    -> HTML -> spider PNG -> A3 PDF -> PPTX token substitution -> QA

KEY RULES ENFORCED
    Thresholds      >12 HIGH(#DC2626) | >4..<=12 MEDIUM(#D97706) | <=4 LOW(#007D71)
    Domain score    MAX(IT residual) across risks mapped to the domain
    Perimeter       control id startswith "Euronext" -> Internal, else External
    Proxy mode      residuals absent / Under Review -> use Inherent, DISCLOSE
    Euronext KPI    "fully Implemented / with any Pending"; amber if any gap
    DORA in-scope   triggers Art. 28-30 action block + red banner
=======================================================================
"""
from __future__ import annotations
import argparse, json, math, os, re, sys, textwrap
from dataclasses import dataclass, field

# ----------------------------------------------------------------------
# CONSTANTS
# ----------------------------------------------------------------------
THRESHOLDS = (                       # (upper-bound, label, hex, bg-hex)
    (4.0,  "LOW",    "007D71", "E0F5F2"),
    (12.0, "MEDIUM", "D97706", "FEF3C7"),
    (25.0, "HIGH",   "DC2626", "FEE2E2"),
)
DOMAINS = ["Cybersecurity", "Data Management", "IT",
           "Business Continuity", "Third-Parties"]
SPIDER_RINGS = [4, 8, 12, 17, 25]
TEAL = "007D71"

# ----------------------------------------------------------------------
# DATA MODEL
# ----------------------------------------------------------------------
@dataclass
class Risk:
    rid: str
    desc: str
    category: str            # "Security" | "Operational"
    domain: str              # one of DOMAINS
    inherent: float
    residual: float          # 0 / None when Under Review
    target: float
    stage: str               # "Treated" | "In Treatment" | "Open"
    controls: list = field(default_factory=list)   # [{id,status}]

@dataclass
class Assessment:
    vendor: str
    assessment_id: str
    organisation: str
    template_name: str
    date_created: str
    date_completed: str
    analyst: str
    analyst_decision: str
    manager: str
    manager_decision: str
    dora_in_scope: bool
    critical_supplier: bool
    service_criticality: str
    supplier_type: str
    certifications: str          # e.g. "ISO 27001 - Valid & in scope"
    cert_valid: bool
    approval_status: str         # "Approved" | "Approved (Conditional)" ...
    risks: list                  # list[Risk]
    findings: list               # list[str]  (key findings, slide 2)
    perimeter: dict              # {domain: {"external":txt,"internal":txt}}
    crit_findings: list          # list[(title, body, positive_bool)]
    dora_actions: list           # list[(timeline, text)]
    analyst_notes: list = field(default_factory=list)

    @staticmethod
    def from_json(d: dict) -> "Assessment":
        risks = [Risk(**{**r, "controls": r.get("controls", [])})
                 for r in d.pop("risks", [])]
        return Assessment(risks=risks, **d)


# ----------------------------------------------------------------------
# PHASE 2-3  — CLASSIFICATION & THRESHOLDS
# ----------------------------------------------------------------------
def classify(score: float):
    """Return (label, hex, bg-hex) per the mandatory threshold model."""
    for ub, label, hexv, bg in THRESHOLDS:
        if score <= ub:
            return label, hexv, bg
    return THRESHOLDS[-1][1:]

def working_score(r: Risk, proxy: bool) -> float:
    """Residual when present; Inherent proxy when Under Review."""
    return r.inherent if proxy else (r.residual or r.inherent)

def is_proxy(a: Assessment) -> bool:
    """Proxy mode: no risk carries a positive residual score."""
    return not any((r.residual or 0) > 0 for r in a.risks)

def domain_scores(a: Assessment, proxy: bool) -> dict:
    """Domain score = MAX working score across risks in that domain (>=1.0)."""
    out = {d: 1.0 for d in DOMAINS}
    for r in a.risks:
        if r.domain in out:
            out[r.domain] = max(out[r.domain], working_score(r, proxy))
    return out


# ----------------------------------------------------------------------
# PHASE 5  — INHERENT RISK RATIONALE
# ----------------------------------------------------------------------
def inherent_rationale(a: Assessment) -> str:
    sec = sum(1 for r in a.risks if r.category.lower().startswith("sec"))
    ops = len(a.risks) - sec
    dora = "in-scope for DORA" if a.dora_in_scope else "out of DORA scope"
    crit = ("a critical supplier" if a.critical_supplier
            else f"a {a.service_criticality.lower()}-criticality, non-critical supplier")
    cert = ("a valid certification posture (%s) that mitigates the external "
            "perimeter" % a.certifications) if a.cert_valid else \
           ("no valid certification, which leaves the external perimeter "
            "materially exposed")
    return (f"{a.vendor} is a {a.supplier_type} supplier classified as {crit}, "
            f"{dora}. The assessment carries {len(a.risks)} inherent risks "
            f"({sec} security, {ops} operational). The supplier presents {cert}. "
            f"The resulting inherent profile reflects the security-weighted "
            f"taxonomy distribution and the supplier's regulatory classification.")


# ----------------------------------------------------------------------
# PHASE 6/9 helpers — KPIs & DERIVED VALUES
# ----------------------------------------------------------------------
def derive(a: Assessment) -> dict:
    proxy = is_proxy(a)
    dscores = domain_scores(a, proxy)
    overall = max(dscores.values())
    o_label, o_hex, o_bg = classify(overall)

    treated = sum(1 for r in a.risks if r.stage.lower() == "treated")
    in_treat = sum(1 for r in a.risks if r.stage.lower() == "in treatment")
    open_ = sum(1 for r in a.risks if r.stage.lower() == "open")
    sec = sum(1 for r in a.risks if r.category.lower().startswith("sec"))

    # Euronext-controls KPI — fully Implemented vs with any Pending
    ctrl = {}
    for r in a.risks:
        for c in r.controls:
            if str(c.get("id", "")).startswith("Euronext"):
                cid = c["id"]
                impl = str(c.get("status", "")).lower() == "implemented"
                ctrl[cid] = ctrl.get(cid, True) and impl
    full = sum(1 for v in ctrl.values() if v)
    pend = sum(1 for v in ctrl.values() if not v)
    has_ctrl = bool(ctrl)

    all_negative = all(not p for (_, _, p) in a.crit_findings) and \
        len(a.crit_findings) > 0

    return dict(proxy=proxy, dscores=dscores, overall=overall,
                o_label=o_label, o_hex=o_hex, o_bg=o_bg,
                treated=treated, in_treat=in_treat, open=open_, sec=sec,
                ops=len(a.risks) - sec, ctrl_full=full, ctrl_pend=pend,
                has_ctrl=has_ctrl, all_negative=all_negative)


# ----------------------------------------------------------------------
# PHASE 9 — TOKEN DICTIONARY  (213 tokens of the v3.1 template)
# ----------------------------------------------------------------------
def build_tokens(a: Assessment, d: dict) -> dict:
    t = {}
    pct = (100 * d["treated"] // len(a.risks)) if a.risks else 0
    proxy_note = ("PROXY DISCLOSURE — assessment Under Review: no residual "
                  "scores assigned. Inherent Risk Scores are used as working "
                  "residual values. Treat all residual figures as provisional."
                  ) if d["proxy"] else \
                 "Residual risk scores validated from the OneTrust assessment."

    # ---- slide 1 ----
    t["REPORT_TITLE"]   = "Current Third-Party Risks above Risk Appetite"
    t["VENDOR_NAME"]    = a.vendor
    t["ASSESSMENT_ID"]  = a.assessment_id
    t["ASSESSMENT_DATE"] = a.date_completed
    t["TEMPLATE_NAME"]  = a.template_name
    t["DORA_BADGE"]     = "DORA IN-SCOPE" if a.dora_in_scope else "DORA OUT-OF-SCOPE"
    t["CERT_BADGE"]     = (a.certifications.split(" - ")[0].upper() + " - VALID"
                           if a.cert_valid else "NO VALID CERTIFICATION")
    t["APPROVAL_BADGE"] = a.approval_status.upper()
    t["OVERALL_RISK"]   = d["o_label"]
    t["PREPARED_BY"]    = a.analyst
    t["MEETING_NAME"]   = "Group CISO Governance Meeting"
    t["CONFIDENTIALITY"] = "EURONEXT NV - CONFIDENTIAL - TPRM Executive Summary"

    # ---- slide 2 ----
    t["SUPPLIER_TYPE"]       = a.supplier_type
    t["SERVICE_CRITICALITY"] = a.service_criticality
    t["DORA_SCOPE"]          = "YES" if a.dora_in_scope else "NO"
    t["APPROVAL_STATUS"]     = a.approval_status
    t["ORGANISATION"]        = a.organisation
    t["CRITICAL_SUPPLIER"]   = "YES" if a.critical_supplier else "NO"
    t["DATE_CREATED"]        = a.date_created
    t["DATE_COMPLETED"]      = a.date_completed
    t["INFOSEC_ANALYST"]     = f"{a.analyst} ({a.analyst_decision})"
    t["INFOSEC_MANAGER"]     = f"{a.manager} ({a.manager_decision})"
    for i in range(3):
        t[f"FINDING_{i+1}"] = a.findings[i] if i < len(a.findings) else "-"

    # ---- slide 3 : KPIs + profile + domain bars ----
    t["KPI_OVERALL"]  = d["o_label"]
    t["KPI_OVERALL_SUB"] = f"max residual {d['overall']:.0f}/25"
    t["KPI_TOTAL"]    = str(len(a.risks))
    t["KPI_TOTAL_SUB"] = f"{d['sec']} security / {d['ops']} operational"
    t["KPI_TREATED"]  = f"{d['treated']} / {d['in_treat']}"
    t["KPI_TREATED_SUB"] = f"{pct}% treated - {d['open']} open"
    t["KPI_CONTROLS"] = (f"{d['ctrl_full']} / {d['ctrl_pend']}"
                         if d["has_ctrl"] else "n/a")
    t["KPI_CONTROLS_SUB"] = ("Implemented / with Pending" if d["has_ctrl"]
                             else "no granular control IDs in export")
    t["KPI_CERT"]     = (a.certifications.split(" - ")[0]
                         if a.cert_valid else "None valid")
    t["KPI_CERT_SUB"] = "Valid & in scope" if a.cert_valid else "Not OK"
    t["SPIDER_CHART"] = a.vendor + " - risk profile"
    t["CERT_SUMMARY"] = a.certifications
    t["REVIEW_SUMMARY"] = f"{a.analyst} / {a.manager}"
    for i, dom in enumerate(DOMAINS, 1):
        sc = d["dscores"][dom]
        t[f"DOM{i}_SCORE"] = f"{sc:.0f}"
        t[f"DOM{i}_STAGE"] = classify(sc)[0]

    # ---- slide 4 : risk register ----
    t["PROXY_DISCLOSURE"]   = proxy_note
    t["INHERENT_RATIONALE"] = inherent_rationale(a)
    for n in range(1, 17):
        r = a.risks[n-1] if n <= len(a.risks) else None
        if r:
            t[f"R{n:02d}_ID"]     = r.rid
            t[f"R{n:02d}_DESC"]   = r.desc
            t[f"R{n:02d}_CAT"]    = r.category
            t[f"R{n:02d}_DOMAIN"] = r.domain
            t[f"R{n:02d}_INH"]    = f"{r.inherent:.0f}"
            t[f"R{n:02d}_RES"]    = (f"{working_score(r, d['proxy']):.0f}"
                                     + ("*" if d["proxy"] else ""))
            t[f"R{n:02d}_TGT"]    = f"{r.target:.0f}"
            t[f"R{n:02d}_STAGE"]  = r.stage
        else:
            for k in ("ID", "DESC", "CAT", "DOMAIN", "INH", "RES", "TGT", "STAGE"):
                t[f"R{n:02d}_{k}"] = ""

    # ---- slide 5 : perimeter matrix ----
    for i, dom in enumerate(DOMAINS, 1):
        p = a.perimeter.get(dom, {})
        t[f"P{i}_EXTERNAL"] = p.get("external", "-")
        t[f"P{i}_INTERNAL"] = p.get("internal", "-")
    ext_ok = all("Mitigated" in a.perimeter.get(dom, {}).get("external", "")
                 for dom in DOMAINS)
    int_gap = any("Mitigated" not in a.perimeter.get(dom, {}).get("internal", "")
                  for dom in DOMAINS)
    if ext_ok and int_gap:
        t["PERIMETER_CALLOUT"] = (
            "ALL-INTERNAL RESIDUAL EXPOSURE - every residual gap is owned by "
            "the Euronext (Internal) perimeter; the vendor (External) perimeter "
            "is fully mitigated. Remediation is a TPRM governance action, not a "
            "vendor-side control failure.")
    else:
        t["PERIMETER_CALLOUT"] = (
            "Residual exposure spans both perimeters; treatment plans are "
            "required on the vendor side as well as Euronext-internal controls.")

    # ---- slide 6 : findings + DORA + actions ----
    t["DORA_BANNER"] = (
        "DORA IN-SCOPE - Regulation (EU) 2022/2554. Articles 28-30 obligations "
        "apply: contractual provisions, Register of Information, and ongoing "
        "monitoring are mandatory." if a.dora_in_scope else
        "DORA OUT-OF-SCOPE - Articles 28-30 do not apply to this engagement.")
    for i in range(4):
        if i < len(a.crit_findings):
            ti, bo, _ = a.crit_findings[i]
        else:
            ti, bo = "-", "-"
        t[f"F{i+1}_TITLE"] = ti
        t[f"F{i+1}_BODY"]  = bo
    t["DORA_STATUS"] = (
        "This engagement is in scope for DORA. The Register of Information "
        "must be updated (Art. 28(3)) and a quarterly residual review plus "
        "annual reassessment applied (Art. 28-30)." if a.dora_in_scope else
        "Not in scope for DORA; standard TPRM monitoring cadence applies.")
    for i in range(5):
        if i < len(a.dora_actions):
            tl, tx = a.dora_actions[i]
        else:
            tl, tx = "-", "-"
        t[f"A{i+1}_TIMELINE"] = tl
        t[f"A{i+1}_TEXT"]     = tx

    # ---- slides 7-8 ----
    t["CLOSING_TITLE"] = "Thank You"
    t["CLOSING_TEXT"]  = (f"{a.vendor} third-party risk assessment - "
                          f"{d['o_label']} overall. Questions to Information "
                          f"Security Assurance, TPRM.")
    t["DISCLAIMER_TEXT"] = (
        "This document is produced by Euronext NV Information Security "
        "Assurance for the Group CISO Governance Meeting. It summarises a "
        "third-party risk assessment based on supplier-declared information "
        "and the OneTrust Infosec Form. Euronext makes no warranty as to the "
        "completeness or accuracy of third-party-provided information. "
        "Risk classifications follow the TPRM threshold model "
        "(>12 HIGH, >4 MEDIUM, <=4 LOW on the 1-25 scale). "
        + (proxy_note + " " if d["proxy"] else "") +
        "This document shall not be reproduced or disclosed without the prior "
        "written consent of the Group CISO. (c) 2026 Euronext NV.")
    t["DISCLAIMER_FOOTER"] = ("EURONEXT NV - Information Security Assurance - "
                              "TPRM - CONFIDENTIAL")
    return t


# ----------------------------------------------------------------------
# PHASE 9 — PPTX RENDER  (run-length-safe token substitution)
# ----------------------------------------------------------------------
TOKEN_RE = re.compile(r"\{\{[A-Z0-9_]+\}\}")

def _sub_text_frame(tf, tokens):
    """Substitute tokens in a text frame, run-length-safe."""
    for para in tf.paragraphs:
        runs = para.runs
        if not runs:
            continue
        joined = "".join(r.text for r in runs)
        if "{{" not in joined:
            continue
        new = TOKEN_RE.sub(lambda m: str(tokens.get(m.group(0)[2:-2], m.group(0))),
                           joined)
        if new == joined:
            continue
        # write result into first run, preserving its formatting; clear rest
        runs[0].text = new
        for r in runs[1:]:
            r.text = ""

def render_pptx(template_path, tokens, spider_png, out_path,
                all_negative=False, dscores=None):
    from pptx import Presentation
    from pptx.util import Emu
    from pptx.dml.color import RGBColor

    # Domain Score Bars (slide 3): Bar_1..Bar_5 are the coloured fill segments
    # sitting on a fixed-width grey track. The template ships them all at one
    # static width; resize each to score/25 of the track and recolour to the
    # threshold band so the deck bars are data-driven like the HTML dashboard.
    BAR_TRACK_EMU = 3291840          # full-scale track width (Rectangle 52..76)
    BAR_MIN_EMU   = 65000            # floor so a score of 1 stays visible

    prs = Presentation(template_path)
    for slide in prs.slides:
        for shape in slide.shapes:
            if shape.has_text_frame:
                _sub_text_frame(shape.text_frame, tokens)
            if shape.has_table:
                for row in shape.table.rows:
                    for cell in row.cells:
                        _sub_text_frame(cell.text_frame, tokens)
            # spider PNG swap on slide 3
            if shape.name == "SpiderPlaceholder" and spider_png \
                    and os.path.exists(spider_png):
                x, y, w, h = shape.left, shape.top, shape.width, shape.height
                shape._element.getparent().remove(shape._element)
                slide.shapes.add_picture(spider_png, x, y, w, h)
            # v3.1 D3 — domain-score bar resize + threshold recolour
            if dscores and shape.name.startswith("Bar_"):
                try:
                    idx = int(shape.name.split("_")[1]) - 1
                except (IndexError, ValueError):
                    idx = -1
                if 0 <= idx < len(DOMAINS):
                    sc = dscores.get(DOMAINS[idx], 1.0)
                    frac = min(sc, 25.0) / 25.0
                    shape.width = Emu(max(BAR_MIN_EMU,
                                          int(BAR_TRACK_EMU * frac)))
                    hexv = classify(sc)[1]
                    shape.fill.solid()
                    shape.fill.fore_color.rgb = RGBColor(
                        int(hexv[0:2], 16), int(hexv[2:4], 16),
                        int(hexv[4:6], 16))
            # v3.1 D3 — F4 finding-icon recolor for all-negative vendors
            if all_negative and shape.name == "F4_Icon":
                shape.fill.solid()
                shape.fill.fore_color.rgb = RGBColor(0xFE, 0xF3, 0xC7)
            if all_negative and shape.name == "F4_Glyph" and shape.has_text_frame:
                for p in shape.text_frame.paragraphs:
                    for r in p.runs:
                        r.text = "!"
                        r.font.color.rgb = RGBColor(0xD9, 0x77, 0x06)
    prs.save(out_path)

    # QA — zero unsubstituted tokens is the pass criterion
    leftover = []
    for slide in Presentation(out_path).slides:
        for shape in slide.shapes:
            if shape.has_text_frame:
                leftover += TOKEN_RE.findall(shape.text_frame.text)
            if shape.has_table:
                for row in shape.table.rows:
                    for cell in row.cells:
                        leftover += TOKEN_RE.findall(cell.text_frame.text)
    return sorted(set(leftover))


# ----------------------------------------------------------------------
# PHASE 6 — HTML DASHBOARD
# ----------------------------------------------------------------------
def _spider_svg(dscores: dict) -> str:
    cx = cy = 210.0
    R = 150.0
    n = 5
    def pt(scale, idx):
        ang = math.radians(-90 + idx * 360 / n)
        return cx + scale * R * math.cos(ang), cy + scale * R * math.sin(ang)
    parts = ['<svg viewBox="0 0 560 460" width="100%" height="420" '
             'xmlns="http://www.w3.org/2000/svg">']
    for ring in SPIDER_RINGS:
        sc = ring / 25.0
        pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in (pt(sc, i) for i in range(n)))
        col = "#DC2626" if ring == 12 else ("#007D71" if ring == 4 else "#CBD6D3")
        dash = ' stroke-dasharray="4 3"' if ring in (4, 12) else ""
        parts.append(f'<polygon points="{pts}" fill="none" stroke="{col}"'
                      f' stroke-width="1.1"{dash}/>')
    poly = []
    for i, dom in enumerate(DOMAINS):
        sc = min(dscores[dom], 25) / 25.0
        poly.append(pt(sc, i))
    pstr = " ".join(f"{x:.1f},{y:.1f}" for x, y in poly)
    parts.append(f'<polygon points="{pstr}" fill="rgba(0,125,113,.22)" '
                  f'stroke="#007D71" stroke-width="2"/>')
    for i, dom in enumerate(DOMAINS):
        x, y = poly[i]
        col = "#" + classify(dscores[dom])[1]
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5.5" fill="{col}" '
                      f'stroke="#fff" stroke-width="1.6"/>')
        lx, ly = pt(1.18, i)
        anchor = ("middle" if abs(lx - cx) < 6 else
                  ("start" if lx > cx else "end"))
        parts.append(f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anchor}" '
                      f'font-size="12" font-weight="600" fill="#334155">'
                      f'{dom}</text>')
        parts.append(f'<text x="{lx:.1f}" y="{ly+15:.1f}" text-anchor="{anchor}"'
                      f' font-size="11" font-weight="700" fill="{col}">'
                      f'{dscores[dom]:.0f}/25</text>')
    parts.append("</svg>")
    return "".join(parts)

def render_html(a: Assessment, d: dict, out_path: str):
    o_hex, o_bg = "#" + d["o_hex"], "#" + d["o_bg"]
    rows = ""
    for r in a.risks:
        ws = working_score(r, d["proxy"])
        rc = "#" + classify(ws)[1]
        rows += (f"<tr><td class='mono'>{r.rid}</td><td>{r.desc}</td>"
                 f"<td>{r.category}</td><td>{r.domain}</td>"
                 f"<td class='mono' style='color:{rc};font-weight:700'>"
                 f"{ws:.0f}{'*' if d['proxy'] else ''}</td>"
                 f"<td class='mono'>{r.target:.0f}</td><td>{r.stage}</td></tr>")
    bars = ""
    for dom in sorted(DOMAINS, key=lambda x: -d["dscores"][x]):
        sc = d["dscores"][dom]
        bc = "#" + classify(sc)[1]
        w = min(sc, 25) / 25 * 100
        bars += (f"<div class='bar'><span>{dom}</span>"
                 f"<div class='track'><div class='fill' style='width:{w:.0f}%;"
                 f"background:{bc}'><b>{sc:.0f}</b></div></div></div>")
    pmatrix = ""
    for dom in DOMAINS:
        p = a.perimeter.get(dom, {})
        ext, intl = p.get("external", "-"), p.get("internal", "-")
        eok = "ok" if "Mitigated" in ext else "warn"
        iok = "ok" if "Mitigated" in intl else "warn"
        pmatrix += (f"<tr><td><b>{dom}</b></td>"
                    f"<td class='{eok}'>{ext}</td>"
                    f"<td class='{iok}'>{intl}</td></tr>")
    proxy_banner = ""
    if d["proxy"]:
        proxy_banner = ("<div class='proxy'>PROXY DISCLOSURE - assessment Under "
                        "Review: no residual scores assigned. Inherent Risk "
                        "Scores used as working residual values (marked *).</div>")
    html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<title>TPRM Executive Summary - {a.vendor}</title>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@500;600&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'IBM Plex Sans',sans-serif;background:#f3f4f6;color:#1e293b;font-size:13px}}
.mono{{font-family:'IBM Plex Mono',monospace}}
.wrap{{max-width:1400px;margin:0 auto;padding:0 20px 40px}}
header{{background:linear-gradient(120deg,#003530,#007D71);color:#fff;padding:32px 40px;margin-bottom:20px}}
header h1{{font-size:26px;font-weight:700}}
header p{{color:#cdeee9;margin-top:6px}}
.badges{{margin-top:14px}}
.badge{{display:inline-block;padding:5px 12px;border-radius:14px;font-weight:600;font-size:11px;margin-right:8px}}
.kpis{{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-bottom:20px}}
.kpi{{background:#fff;border:1px solid #e2e8f0;border-radius:8px;padding:14px 16px}}
.kpi .l{{font-size:10px;font-weight:600;color:#64748b;letter-spacing:.6px}}
.kpi .v{{font-size:22px;font-weight:700;margin:4px 0}}
.kpi .s{{font-size:11px;color:#64748b}}
.grid{{display:grid;grid-template-columns:560px 1fr;gap:18px;margin-bottom:20px}}
.card{{background:#fff;border:1px solid #e2e8f0;border-radius:8px;padding:18px}}
.card h3{{font-size:14px;color:#007D71;margin-bottom:10px}}
.bar{{margin:8px 0}}
.bar span{{font-size:12px;font-weight:600}}
.track{{background:#f1f5f9;border-radius:4px;height:24px;margin-top:3px}}
.fill{{height:24px;border-radius:4px;display:flex;align-items:center;justify-content:flex-end;padding-right:8px}}
.fill b{{color:#fff;font-family:'IBM Plex Mono',monospace;font-size:12px}}
table{{width:100%;border-collapse:collapse;margin-top:8px}}
th{{background:#005048;color:#fff;font-size:11px;padding:7px 8px;text-align:left}}
td{{padding:6px 8px;border-bottom:1px solid #eef2f1;font-size:12px}}
td.ok{{background:#D1FAE5;color:#047857}}
td.warn{{background:#FEF3C7;color:#92400e}}
.proxy{{background:#FEF3C7;border-left:5px solid #D97706;color:#92400e;padding:12px 16px;border-radius:4px;margin-bottom:16px;font-weight:600}}
.callout{{background:#E0F5F2;border:1px solid #007D71;border-radius:6px;padding:14px 16px;margin-top:12px;color:#005048}}
footer{{text-align:center;color:#64748b;font-size:11px;margin-top:24px}}
</style></head><body>
<header>
<h1>TPRM Executive Summary - {a.vendor}</h1>
<p>Assessment {a.assessment_id} &nbsp;|&nbsp; Completed {a.date_completed} &nbsp;|&nbsp; {a.template_name}</p>
<div class="badges">
<span class="badge" style="background:{o_bg};color:{o_hex}">OVERALL RISK: {d['o_label']}</span>
<span class="badge" style="background:{'#FEE2E2' if a.dora_in_scope else '#E0F5F2'};color:{'#DC2626' if a.dora_in_scope else '#007D71'}">DORA {'IN-SCOPE' if a.dora_in_scope else 'OUT-OF-SCOPE'}</span>
<span class="badge" style="background:#EDE9FE;color:#7C3AED">{a.service_criticality}</span>
</div></header>
<div class="wrap">
{proxy_banner}
<div class="kpis">
<div class="kpi"><div class="l">OVERALL RISK</div><div class="v" style="color:{o_hex}">{d['o_label']}</div><div class="s">max residual {d['overall']:.0f}/25</div></div>
<div class="kpi"><div class="l">TOTAL RISKS</div><div class="v">{len(a.risks)}</div><div class="s">{d['sec']} security / {d['ops']} operational</div></div>
<div class="kpi"><div class="l">TREATED / IN TREATMENT</div><div class="v">{d['treated']} / {d['in_treat']}</div><div class="s">{d['open']} open</div></div>
<div class="kpi"><div class="l">EURONEXT CONTROLS</div><div class="v">{(str(d['ctrl_full'])+' / '+str(d['ctrl_pend'])) if d['has_ctrl'] else 'n/a'}</div><div class="s">{'Implemented / w. Pending' if d['has_ctrl'] else 'no granular IDs'}</div></div>
<div class="kpi"><div class="l">CERTIFICATION</div><div class="v" style="font-size:15px">{a.certifications.split(' - ')[0] if a.cert_valid else 'None valid'}</div><div class="s">{'Valid &amp; in scope' if a.cert_valid else 'Not OK'}</div></div>
</div>
<div class="grid">
<div class="card"><h3>Risk Profile - 5 Domains</h3>{_spider_svg(d['dscores'])}</div>
<div class="card"><h3>Domain Score Bars</h3>{bars}
<div style="margin-top:14px;font-size:11px;color:#64748b">Threshold model: &gt;12 HIGH &nbsp; &gt;4 MEDIUM &nbsp; &le;4 LOW (OneTrust 1-25 scale)</div></div>
</div>
<div class="card"><h3>Inherent Risk Rationale</h3>
<div class="callout">{inherent_rationale(a)}</div></div>
<div class="card" style="margin-top:18px"><h3>Risk Register</h3>
<table><tr><th>ID</th><th>Description</th><th>Category</th><th>Domain</th><th>Residual</th><th>Target</th><th>Stage</th></tr>{rows}</table></div>
<div class="card" style="margin-top:18px"><h3>Dual-Perimeter Matrix</h3>
<table><tr><th>Domain</th><th>External (Vendor)</th><th>Internal (Euronext)</th></tr>{pmatrix}</table></div>
<footer>EURONEXT NV - Information Security Assurance | TPRM Executive Summary | {a.vendor} | CONFIDENTIAL</footer>
</div></body></html>"""
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(html)


# ----------------------------------------------------------------------
# PHASE 8/9A — PLAYWRIGHT  (spider PNG + A3 PDF)
# ----------------------------------------------------------------------
def render_spider_png(html_path, out_path):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("  [skip] playwright not installed - spider PNG not rendered")
        return None
    with sync_playwright() as p:
        br = p.chromium.launch(headless=True)
        pg = br.new_page(viewport={"width": 1400, "height": 1200})
        pg.goto("file://" + os.path.abspath(html_path),
                wait_until="networkidle", timeout=30000)
        pg.wait_for_timeout(3000)                      # Google Fonts settle
        el = pg.query_selector(".card svg") or pg.query_selector(".card")
        if el:
            el.screenshot(path=out_path)
        br.close()
    return out_path if os.path.exists(out_path) else None

def render_pdf(html_path, out_path):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("  [skip] playwright not installed - PDF not rendered")
        return None
    with sync_playwright() as p:
        br = p.chromium.launch(headless=True)
        pg = br.new_page()
        pg.goto("file://" + os.path.abspath(html_path),
                wait_until="networkidle", timeout=30000)
        pg.wait_for_timeout(3000)
        pg.pdf(path=out_path, format="A3", landscape=True,
               print_background=True,
               margin={"top": "10mm", "bottom": "10mm",
                       "left": "10mm", "right": "10mm"})
        br.close()
    return out_path


# ----------------------------------------------------------------------
# SYNTHETIC SELF-TEST ASSESSMENT
# ----------------------------------------------------------------------
def demo_assessment() -> Assessment:
    cats = (["Security"] * 13) + (["Operational"] * 3)
    doms = (["Cybersecurity"] * 5 + ["Data Management"] * 3 + ["IT"] * 3 +
            ["Business Continuity"] * 2 + ["Third-Parties"] * 3)
    stages = (["Treated"] * 6 + ["In Treatment"] * 9 + ["Open"] * 1)
    risks = []
    for i in range(16):
        risks.append(Risk(
            rid=f"R{i+1:02d}",
            desc=f"Inherent risk {i+1} - OneTrust v14 taxonomy item.",
            category=cats[i], domain=doms[i],
            inherent=6.0, residual=0.0, target=4.0, stage=stages[i],
            controls=[{"id": "Euronext-TPRM-%02d" % (i+1),
                       "status": "Implemented" if i % 3 else "Pending"}]))
    return Assessment(
        vendor="DEMO_VENDOR", assessment_id="9999", organisation="EURONEXT NV",
        template_name="Infosec Form (v14)", date_created="01/05/2026",
        date_completed="20/05/2026", analyst="F. Gomes",
        analyst_decision="Approved", manager="P. Santos",
        manager_decision="Approved", dora_in_scope=True,
        critical_supplier=False, service_criticality="Standard",
        supplier_type="Technology",
        certifications="ISO 27001 - Valid & in scope", cert_valid=True,
        approval_status="Approved (Conditional)", risks=risks,
        findings=["Six controls treated; nine in treatment; one open risk.",
                  "DORA in-scope - Art. 28-30 contractual actions required.",
                  "Residual scores absent - inherent proxy applied."],
        perimeter={d: {"external": "Mitigated",
                       "internal": "Treatment plan pending"} for d in DOMAINS},
        crit_findings=[("Pending Euronext controls",
                        "Internal treatment plans not yet closed.", False),
                       ("Overall MEDIUM",
                        "Max residual sits in the MEDIUM band.", False),
                       ("Vendor posture adequate",
                        "External perimeter fully certified.", True),
                       ("Conditional approval",
                        "Go-live gated on TPOPS finalisation.", False)],
        dora_actions=[("IMMEDIATE", "Finalise the TPOPS contractual addendum."),
                      ("Q2 2026", "Update the DORA Register of Information."),
                      ("Q2 2026", "Close pending Euronext internal controls."),
                      ("ONGOING", "Apply quarterly residual review cadence."),
                      ("GOVERNANCE", "Annual reassessment per Art. 28-30.")])


# ----------------------------------------------------------------------
# ORCHESTRATION
# ----------------------------------------------------------------------
def run(a: Assessment, template, outdir):
    os.makedirs(outdir, exist_ok=True)
    safe = re.sub(r"[^A-Za-z0-9]+", "", a.vendor) or "Vendor"
    html = os.path.join(outdir, f"{safe}_CISO_ExecSummary.html")
    pdf  = os.path.join(outdir, f"{safe}_CISO_ExecSummary.pdf")
    pptx = os.path.join(outdir, f"{safe}_CISO_TPRM_Governance.pptx")
    spider = os.path.join(outdir, f"{safe}_spider.png")

    print(f"[1/6] deriving values for {a.vendor} ...")
    d = derive(a)
    print(f"      overall={d['o_label']} ({d['overall']:.0f}/25)  "
          f"proxy={'YES' if d['proxy'] else 'no'}  "
          f"all-negative={'YES' if d['all_negative'] else 'no'}")

    print("[2/6] rendering HTML dashboard ...")
    render_html(a, d, html)

    print("[3/6] rendering spider PNG (Playwright) ...")
    sp = render_spider_png(html, spider)

    print("[4/6] rendering A3 landscape PDF (Playwright) ...")
    render_pdf(html, pdf)

    print("[5/6] rendering PPTX (token substitution) ...")
    tokens = build_tokens(a, d)
    if not os.path.exists(template):
        print(f"      [skip] template not found: {template}")
        leftover = None
    else:
        leftover = render_pptx(template, tokens, sp, pptx,
                               all_negative=d["all_negative"],
                               dscores=d["dscores"])

    print("[6/6] QA ...")
    if leftover is None:
        print("      PPTX skipped (no template).")
    elif leftover:
        print(f"      FAIL - {len(leftover)} unsubstituted tokens: "
              f"{', '.join(leftover[:8])}")
    else:
        print("      PASS - zero unsubstituted tokens.")
    print("\nDeliverables:")
    for f in (html, pdf, pptx):
        print("  -", f if os.path.exists(f) else f + "  (not produced)")
    return html, pdf, pptx


def load(path) -> Assessment:
    with open(path, encoding="utf-8") as fh:
        return Assessment.from_json(json.load(fh))


def main():
    ap = argparse.ArgumentParser(
        description="CISO ExecSummary v2 pipeline orchestrator.")
    ap.add_argument("--assessment", help="verified assessment JSON")
    ap.add_argument("--template", default="Group_CISO_Report_Template_v3.1.pptx",
                    help="PPTX token template")
    ap.add_argument("--outdir", default="/mnt/user-data/outputs")
    ap.add_argument("--demo", action="store_true",
                    help="run the synthetic DEMO_VENDOR self-test")
    args = ap.parse_args()

    if args.demo:
        a = demo_assessment()
    elif args.assessment:
        a = load(args.assessment)
    else:
        ap.error("provide --assessment <json> or --demo")
    run(a, args.template, args.outdir)


if __name__ == "__main__":
    main()
