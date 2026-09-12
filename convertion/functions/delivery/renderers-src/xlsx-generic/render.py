#!/usr/bin/env python3
"""Generic tabular XLSX renderer (template `xlsx-generic`, openpyxl).

Usage: render.py <data.json> <out.xlsx>

Replaces the claude.ai xlsx-skill "create with openpyxl" path for governed
deliverables (advisory tables, TPRM registers, Form B drafts). The Function
then calls office-tools /api/recalc (the skill's mandatory recalc.py gate)
before the file is released — see manifest.json "post".

data.json contract (templates/xlsx_generic.schema.json):
{
  "title": str, "supplier": str?, "service": str?, "reportDate": "YYYY-MM-DD"?,
  "classification": str?,                    # default "Euronext Internal"
  "sheets": [ { "name": str, "columns": [str, ...],
                "rows": [[...], ...],          # values; strings starting with "=" are formulas
                "widths": [int, ...]?, "freeze": "A2"?,
                "number_formats": {"<column name>": "0.0"}?,
                "conditional": {"<column name>": "risk_band"}? } ],
  "legend": [ {"label": str, "meaning": str}, ... ]?,
  "assumptions": [str, ...]?, "sources": [str, ...]?
}
House style: Verdana, teal RGB(0,141,127) header fill, white bold header
font, blue inputs / black formulas (financial-model colour convention),
legend + example row on a `Legend` sheet for fill-in workbooks.
"""

from __future__ import annotations

import json
import sys
from datetime import date

from openpyxl import Workbook
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

TEAL = "008D7F"
FONT = "Verdana"
HDR_FILL = PatternFill("solid", fgColor=TEAL)
HDR_FONT = Font(name=FONT, bold=True, color="FFFFFF", size=10)
BODY_FONT = Font(name=FONT, size=9)
INPUT_FONT = Font(name=FONT, size=9, color="0000FF")      # hard-coded inputs
FORMULA_FONT = Font(name=FONT, size=9, color="000000")    # formulas
THIN = Side(style="thin", color="CCCCCC")
BORDER = Border(top=THIN, bottom=THIN, left=THIN, right=THIN)
BANDS = [(">=", 7.0, "FFC7CE"), (">=", 4.0, "FFEB9C"), ("<", 4.0, "C6EFCE")]  # High/Medium/Low


def _sheet(wb, spec: dict, first: bool):
    ws = wb.active if first else wb.create_sheet()
    ws.title = spec["name"][:31]
    cols = spec["columns"]
    for i, c in enumerate(cols, 1):
        cell = ws.cell(row=1, column=i, value=c)
        cell.fill, cell.font, cell.border = HDR_FILL, HDR_FONT, BORDER
        cell.alignment = Alignment(vertical="center", wrap_text=True)
    for r, row in enumerate(spec.get("rows", []), 2):
        for i, v in enumerate(row, 1):
            cell = ws.cell(row=r, column=i, value=v)
            is_formula = isinstance(v, str) and v.startswith("=")
            cell.font = FORMULA_FONT if is_formula else (INPUT_FONT if isinstance(v, (int, float)) else BODY_FONT)
            cell.border = BORDER
            cell.alignment = Alignment(vertical="top", wrap_text=True)
    widths = spec.get("widths") or [max(12, min(60, len(str(c)) + 4)) for c in cols]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = spec.get("freeze", "A2")
    ws.auto_filter.ref = ws.dimensions
    for cname, fmt in (spec.get("number_formats") or {}).items():
        if cname in cols:
            col = get_column_letter(cols.index(cname) + 1)
            for r in range(2, ws.max_row + 1):
                ws[f"{col}{r}"].number_format = fmt
    for cname, kind in (spec.get("conditional") or {}).items():
        if cname in cols and kind == "risk_band" and ws.max_row > 1:
            col = get_column_letter(cols.index(cname) + 1)
            rng = f"{col}2:{col}{ws.max_row}"
            ws.conditional_formatting.add(rng, CellIsRule(operator="greaterThanOrEqual", formula=["7"], fill=PatternFill("solid", fgColor="FFC7CE")))
            ws.conditional_formatting.add(rng, CellIsRule(operator="between", formula=["4", "6.999"], fill=PatternFill("solid", fgColor="FFEB9C")))
            ws.conditional_formatting.add(rng, CellIsRule(operator="lessThan", formula=["4"], fill=PatternFill("solid", fgColor="C6EFCE")))
    return ws


def render(data: dict, out: str) -> None:
    wb = Workbook()
    for i, spec in enumerate(data["sheets"]):
        _sheet(wb, spec, i == 0)
    info = wb.create_sheet("Legend")
    rows = [("Title", data.get("title", "")), ("Supplier", data.get("supplier", "")),
            ("Service", data.get("service", "")), ("Report date", data.get("reportDate", date.today().isoformat())),
            ("Classification", data.get("classification", "Euronext Internal")),
            ("Colour convention", "blue = input value, black = formula, teal header = column title"),
            ("Risk bands", "High >= 7.0 (red) | Medium >= 4.0 (amber) | Low < 4.0 (green)")]
    for lg in data.get("legend", []):
        rows.append((lg.get("label", ""), lg.get("meaning", "")))
    for a in data.get("assumptions", []):
        rows.append(("Assumption", a))
    for s in data.get("sources", []):
        rows.append(("Source", s))
    for r, (k, v) in enumerate(rows, 1):
        info.cell(row=r, column=1, value=k).font = Font(name=FONT, bold=True, size=9, color=TEAL)
        info.cell(row=r, column=2, value=v).font = BODY_FONT
    info.column_dimensions["A"].width, info.column_dimensions["B"].width = 22, 90
    wb.properties.title = data.get("title", "")
    wb.properties.creator = "Euronext InfoSec Assurance (delivery Function)"
    wb.save(out)


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as fh:
        render(json.load(fh), sys.argv[2])
    print("OK", sys.argv[2])
