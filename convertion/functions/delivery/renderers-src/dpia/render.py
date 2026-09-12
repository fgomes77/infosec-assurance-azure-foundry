#!/usr/bin/env python3
"""InfoSec TPA Report for DPO Team — DOCX renderer (template `dpia`).

Usage: render.py <data.json> <out.docx>

python-docx port of the byte-verified dpia skill generator
(claude-account-export/skills/dpia/scripts/generate_report.js, Node `docx`
package with the assessment data hard-coded for one supplier). The port
reproduces the layout 1:1 — A4 portrait, 720-twip (0.5") margins, Arial
9 pt body, teal 008D7F headings, header "CONFIDENTIAL - Euronext NV",
"Page X of Y" footer, 4x3 supplier table, 4 stat cards, status legend,
risk register with merged risk cells and status shading
C6EFCE / FFEB9C / FFC7CE, conclusion with bold domains, approval line,
annex 5-column summary, Annexes 1-3 — but is driven by data.json
(templates/dpia_report.schema.json) so every supplier renders through the
same governed path. Golden comparison: evaluation/ (Oracle Portugal sample).

data.json:
{
  "supplier": str, "assessment": str, "client": "EURONEXT NV"?, "dateRange": str,
  "doraScope": str, "certifications": str,
  "executiveSummary": str,
  "risks": [ {"title": str, "inherentRisk": "12-Medium", "residualRisk": "4-Low",
              "controls": [{"name": str, "status": "Implemented|Pending|Not Doing", "responsible": str}]} ],
  "implementedDomains": [str, ...],
  "riskRating": {"label": "LOW"|"MEDIUM"|"HIGH", "text": str},
  "approval": str,                         # "<Analyst> (Analyst) - Approved | <Manager> (Manager) - Approved"
  "dueDate": "DD/MM/YYYY"?,               # default: today + 2 months (as in the source)
  "annex1": [ {"ref": str, "issue": str, "rag": {"score": "6", "label": "MEDIUM"},
               "individuals": str, "compliance": str, "corporate": str} ],
  "annex2": [ {"ref": str, "risk": str, "rag": {"score": "6", "label": "MEDIUM"}, "solution": str,
               "result": str, "outcome": str, "residual": {"score": "4", "label": "LOW"}} ],
  "annex3": [ {"ref": str, "action": str, "owner": str, "status": str, "due": str} ]
}
"""

from __future__ import annotations

import json
import sys
from datetime import date

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor, Twips

TEAL = "008D7F"
LIGHT_GRAY = "F0F0F0"
MEDIUM_GRAY = "CCCCCC"
STATUS_FILL = {"Implemented": "C6EFCE", "Pending": "FFEB9C", "Not Doing": "FFC7CE"}
STATUS_TEXT = {"Implemented": "008D7F", "Pending": "9C6500", "Not Doing": "C00000"}
RAG_FILL = {"LOW": "C6EFCE", "MEDIUM": "FFEB9C", "HIGH": "FFC7CE"}
FONT = "Arial"


def hp(size_half_points: int) -> Pt:      # docx-js sizes are half-points
    return Pt(size_half_points / 2)


def _shade(cell, fill: str | None):
    if not fill:
        return
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    tcPr.append(shd)


def _borders(table):
    tbl = table._tbl
    tblPr = tbl.tblPr
    b = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        e = OxmlElement(f"w:{edge}")
        e.set(qn("w:val"), "single")
        e.set(qn("w:sz"), "4")
        e.set(qn("w:color"), MEDIUM_GRAY)
        b.append(e)
    tblPr.append(b)


def _run(p, text, size=14, bold=False, color=None, italic=False):
    r = p.add_run(text)
    r.font.name, r.font.size, r.bold, r.italic = FONT, hp(size), bold, italic
    if color:
        r.font.color.rgb = RGBColor.from_string(color)
    return r


def _cell(cell, text, fill=None, bold=False, size=14, align=WD_ALIGN_PARAGRAPH.LEFT, color=None, width=None):
    cell.text = ""
    p = cell.paragraphs[0]
    p.alignment = align
    _run(p, text, size, bold, color)
    _shade(cell, fill)
    if width:
        cell.width = Twips(width)
    return cell


def _header_cell(cell, text, width=None):
    return _cell(cell, text, TEAL, True, 16, WD_ALIGN_PARAGRAPH.CENTER, "FFFFFF", width)


def _card(cell, label, value, color=None):
    cell.text = ""
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _run(p, label, 14, color="666666")
    p2 = cell.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _run(p2, value, 28, True, color or "000000")
    _shade(cell, LIGHT_GRAY)


def _table(doc, rows, cols, widths):
    t = doc.add_table(rows=rows, cols=cols)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    _borders(t)
    for r in t.rows:
        for i, w in enumerate(widths):
            r.cells[i].width = Twips(w)
    return t


def _heading(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before, p.paragraph_format.space_after = Pt(10), Pt(5)
    _run(p, text, 24, True, TEAL)
    return p


def _page_number_field(p, instr):
    r = p.add_run()
    r.font.size, r.font.name, r.font.color.rgb = hp(14), FONT, RGBColor.from_string("666666")
    for tag, txt in (("begin", None), ("instr", instr), ("end", None)):
        if tag == "instr":
            e = OxmlElement("w:instrText")
            e.set(qn("xml:space"), "preserve")
            e.text = txt
        else:
            e = OxmlElement("w:fldChar")
            e.set(qn("w:fldCharType"), tag)
        r._r.append(e)


def _due_date(d: dict) -> str:
    if d.get("dueDate"):
        return d["dueDate"]
    t = date.today()
    m, y = t.month + 2, t.year
    if m > 12:
        m, y = m - 12, y + 1
    return date(y, m, min(t.day, 28)).strftime("%d/%m/%Y")


def render(d: dict, out: str) -> None:
    doc = Document()
    st = doc.styles["Normal"]
    st.font.name, st.font.size = FONT, hp(18)
    sec = doc.sections[0]
    sec.orientation = WD_ORIENT.PORTRAIT
    sec.page_width, sec.page_height = Twips(11906), Twips(16838)
    sec.top_margin = sec.bottom_margin = sec.left_margin = sec.right_margin = Twips(720)
    h = sec.header.paragraphs[0]
    h.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    _run(h, "CONFIDENTIAL - Euronext NV", 14, color="666666")
    f = sec.footer.paragraphs[0]
    f.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _run(f, "Page ", 14, color="666666")
    _page_number_field(f, "PAGE")
    _run(f, " of ", 14, color="666666")
    _page_number_field(f, "NUMPAGES")

    risks = d["risks"]
    controls = [c for r in risks for c in r["controls"]]
    total_controls = len(controls) or 1
    implemented = sum(c["status"] == "Implemented" for c in controls)
    pending = sum(c["status"] == "Pending" for c in controls)
    not_doing = sum(c["status"] == "Not Doing" for c in controls)
    due = _due_date(d)

    # Title
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(8)
    _run(p, "InfoSec TPA Report for DPO Team", 32, True, TEAL)

    # Supplier info 3x4
    t = _table(doc, 3, 4, [1800, 3400, 1800, 3400])
    info = [("Supplier:", d["supplier"], "Assessment:", d["assessment"]),
            ("Client:", d.get("client", "EURONEXT NV"), "Date:", d["dateRange"]),
            ("DORA Scope:", d["doraScope"], "Certifications:", d["certifications"])]
    for r, row in enumerate(info):
        for c, v in enumerate(row):
            _cell(t.rows[r].cells[c], v, LIGHT_GRAY if c % 2 == 0 else None, c % 2 == 0)

    # 1. Executive Summary
    _heading(doc, "1. Executive Summary")
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(5)
    _run(p, "Security measures in place to protect identifiable information: ", 16, True, TEAL)
    _run(p, d["executiveSummary"], 16)
    t = _table(doc, 1, 4, [2600] * 4)
    _card(t.rows[0].cells[0], "Total Risks", str(len(risks)), TEAL)
    _card(t.rows[0].cells[1], "Total Controls", str(len(controls)), TEAL)
    _card(t.rows[0].cells[2], "Implemented", f"{implemented} ({round(implemented / total_controls * 100)}%)", TEAL)
    pn = pending + not_doing
    _card(t.rows[0].cells[3], "Pending / Not Doing", f"{pn} ({round(pn / total_controls * 100)}%)", "C00000" if pn else "000000")

    # 2. Risk register
    _heading(doc, "2. Risk Register with Control Implementation Status")
    lg = _table(doc, 1, 3, [3466, 3467, 3467])
    for i, s in enumerate(("Implemented", "Pending", "Not Doing")):
        _cell(lg.rows[0].cells[i], s, STATUS_FILL[s], True, 14, WD_ALIGN_PARAGRAPH.CENTER)
    doc.add_paragraph().paragraph_format.space_before = Pt(4)
    widths = [900, 900, 2400, 3200, 1200, 900, 900]
    rt = _table(doc, 1, 7, widths)
    for i, hdr in enumerate(("Inherent", "Residual", "Risk Title", "Control Name", "Responsible", "Status", "Due Date")):
        _header_cell(rt.rows[0].cells[i], hdr)
    for risk in risks:
        first = None
        for ci, ctrl in enumerate(risk["controls"] or [{"name": "-", "status": "-", "responsible": "-"}]):
            cells = rt.add_row().cells
            for i, w in enumerate(widths):
                cells[i].width = Twips(w)
            if ci == 0:
                first = cells
                _cell(cells[0], risk["inherentRisk"], None, True, 14, WD_ALIGN_PARAGRAPH.CENTER)
                _cell(cells[1], risk["residualRisk"], None, True, 14, WD_ALIGN_PARAGRAPH.CENTER)
                _cell(cells[2], risk["title"], None, True)
            else:
                for k in range(3):
                    first[k].merge(cells[k])
            _cell(cells[3], ctrl["name"])
            _cell(cells[4], ctrl["responsible"], None, False, 14, WD_ALIGN_PARAGRAPH.CENTER)
            _cell(cells[5], ctrl["status"], STATUS_FILL.get(ctrl["status"]), True, 14, WD_ALIGN_PARAGRAPH.CENTER)
            _cell(cells[6], due if ctrl["status"] == "Pending" else "N/A", None, False, 14, WD_ALIGN_PARAGRAPH.CENTER)

    # 3. Conclusion
    _heading(doc, "3. InfoSec TPRM Conclusion on Data Protection and Privacy")
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(4)
    _run(p, "The security controls implemented are: ", 16, True)
    doms = d.get("implementedDomains", [])
    for i, dom in enumerate(doms):
        _run(p, dom, 16, True)
        _run(p, "; " if i < len(doms) - 1 else ".", 16)
    rr = d["riskRating"]
    t = _table(doc, 1, 2, [2600, 7800])
    _cell(t.rows[0].cells[0], "Risk Rating:", LIGHT_GRAY, True)
    _cell(t.rows[0].cells[1], f"{rr['label'].upper()} - {rr['text']}", RAG_FILL.get(rr["label"].upper()), True)
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(5)
    _run(p, "Approval: ", 16, True)
    _run(p, d["approval"], 16)

    # Annexes summary page
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(10)
    _run(p, "Annexes", 28, True, TEAL)
    aw = [2000, 3200, 1600, 1600, 2000]
    at = _table(doc, 2, 5, aw)
    for i, hdr in enumerate(("List of All Risks Identified", "List of All Controls", "List of all Status",
                             "List of all Responsable", "List of All Due Dates")):
        _cell(at.rows[0].cells[i], hdr, TEAL, True, 14, WD_ALIGN_PARAGRAPH.CENTER, "FFFFFF")
    seen, uniq = set(), []
    for r in risks:
        for c in r["controls"]:
            if c["name"] not in seen:
                seen.add(c["name"])
                uniq.append(c)
    cols = at.rows[1].cells
    for c in cols:
        c.text = ""
    for r in risks:
        _run(cols[0].add_paragraph(), r["title"], 10)
    for c in uniq:
        _run(cols[1].add_paragraph(), c["name"], 9)
        p = cols[2].add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        _run(p, c["status"], 9, True, STATUS_TEXT.get(c["status"], "000000"))
        p = cols[3].add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        _run(p, c["responsible"], 9)
        p = cols[4].add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        _run(p, due if c["status"] == "Pending" else "N/A", 9)

    def annex_title(text, band):
        doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
        p = doc.add_paragraph()
        _run(p, text, 24, True, TEAL)
        bt = _table(doc, 1, 1, [10400])
        _cell(bt.rows[0].cells[0], band, TEAL, True, 16, WD_ALIGN_PARAGRAPH.LEFT, "FFFFFF")

    def rag_cell(cell, rag):
        cell.text = ""
        _shade(cell, RAG_FILL.get(str(rag.get("label", "")).upper()))
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        _run(p, str(rag.get("score", "")), 14, True)
        p2 = cell.add_paragraph()
        p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        _run(p2, str(rag.get("label", "")).upper(), 10, True)

    # Annex 1
    annex_title("Annex 1: Privacy Issues & Risks", "IDENTIFIED PRIVACY ISSUES AND ASSOCIATED RISKS")
    p = doc.add_paragraph()
    _run(p, "Please refer to annex 3 for more information", 14, italic=True)
    w1 = [600, 2200, 600, 2200, 2200, 2200]
    t = _table(doc, 2, 6, w1)
    for i, hdr in enumerate(("REF", "PRIVACY ISSUE", "RAG", "RISKS TO INDIVIDUAL(S)", "COMPLIANCE RISK", "CORPORATE RISK")):
        _header_cell(t.rows[0].cells[i], hdr)
    for i, hint in enumerate(("#", "Use assessment response to detail the privacy factor resulting in risk", "Inherent Risk Rating",
                              "Complete if risk impacts data subject(s) or put N/A if not applicable",
                              "Complete if risk causes non-compliance or put N/A if not applicable",
                              "Complete if risk impacts business or put N/A if not applicable")):
        _cell(t.rows[1].cells[i], hint, LIGHT_GRAY, False, 8, WD_ALIGN_PARAGRAPH.CENTER if i in (0, 2) else WD_ALIGN_PARAGRAPH.LEFT)
    for a in d.get("annex1", []):
        c = t.add_row().cells
        _cell(c[0], a["ref"], None, True, 12, WD_ALIGN_PARAGRAPH.CENTER)
        _cell(c[1], a["issue"], None, True, 10)
        rag_cell(c[2], a["rag"])
        _cell(c[3], a["individuals"], None, False, 10)
        _cell(c[4], a["compliance"], None, False, 10)
        _cell(c[5], a["corporate"], None, False, 10)

    # Annex 2
    annex_title("Annex 2: Proposed Risk Solutions and Mitigating Actions", "PROPOSED RISK SOLUTIONS AND MITIGATING ACTIONS")
    w2 = [600, 1800, 600, 4200, 1000, 1000, 800]
    t = _table(doc, 2, 7, w2)
    for i, hdr in enumerate(("REF", "RISK", "RAG", "SOLUTION/MITIGATING ACTIONS", "RESULT", "OUTCOME", "RAG")):
        _header_cell(t.rows[0].cells[i], hdr)
    for i, hint in enumerate(("#", "Risk to be mitigated", "Inherent Risk Rating",
                              "Detail corrective actions, solutions and mitigating controls that address the risk",
                              "Reduced, Eliminated or Accepted",
                              "Has the solution(s) reduced the risk enough to proceed with processing?", "Residual Risk Rating")):
        _cell(t.rows[1].cells[i], hint, LIGHT_GRAY, False, 8, WD_ALIGN_PARAGRAPH.CENTER if i in (0, 2, 6) else WD_ALIGN_PARAGRAPH.LEFT)
    for a in d.get("annex2", []):
        c = t.add_row().cells
        _cell(c[0], a["ref"], None, True, 12, WD_ALIGN_PARAGRAPH.CENTER)
        _cell(c[1], a["risk"], None, True, 10)
        rag_cell(c[2], a["rag"])
        _cell(c[3], a["solution"], None, False, 10)
        _cell(c[4], a["result"], None, False, 10, WD_ALIGN_PARAGRAPH.CENTER)
        _cell(c[5], a["outcome"], None, False, 10, WD_ALIGN_PARAGRAPH.CENTER)
        rag_cell(c[6], a["residual"])

    # Annex 3
    annex_title("Annex 3: Action Plan", "ACTION PLAN")
    w3 = [800, 4400, 1600, 1600, 2000]
    t = _table(doc, 1, 5, w3)
    for i, hdr in enumerate(("REF", "SOLUTION/MITIGATING ACTIONS", "OWNER", "STATUS", "DUE DATE")):
        _header_cell(t.rows[0].cells[i], hdr)
    for a in d.get("annex3", []):
        c = t.add_row().cells
        _cell(c[0], a["ref"], None, True, 12, WD_ALIGN_PARAGRAPH.CENTER)
        _cell(c[1], a["action"], None, False, 10)
        _cell(c[2], a["owner"], None, False, 10, WD_ALIGN_PARAGRAPH.CENTER)
        _cell(c[3], a["status"], STATUS_FILL.get(a["status"]), True, 10, WD_ALIGN_PARAGRAPH.CENTER)
        _cell(c[4], a["due"], None, False, 10, WD_ALIGN_PARAGRAPH.CENTER)

    doc.core_properties.title = f"InfoSec TPA Report for DPO Team - {d['supplier']}"
    doc.core_properties.author = "Euronext InfoSec Assurance (delivery Function)"
    doc.save(out)


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as fh:
        render(json.load(fh), sys.argv[2])
    print("OK", sys.argv[2])
