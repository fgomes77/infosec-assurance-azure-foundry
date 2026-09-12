"""Deterministic render-time quality gates (the skills' inline quality-gate
scripts that used to run in the claude.ai sandbox). Each gate returns a
list of failed checks; an empty list means PASS. /api/render answers 422
with the failed list, and agents/verifier_instructions.md rule 1 cites the
same checks so the verifier and the Function agree.

Sources (byte-verified, never edited):
  deepsearch-protocol/SKILL.md PHASE 5 "Quality Gate" (9 section ids,
  Chart.js CDN, spiderChart canvas, downloadReport, self-contained, braces
  balanced, UTF-8, ends with </html>, size > 20 KB) + the data-overall-score
  addendum (pipelines.json deepsearch-report notes).
"""

from __future__ import annotations

import re

DEEPSEARCH_SECTIONS = ['risk', 'corporate', 'security', 'technical', 'incidents',
                       'ai', 'integrations', 'controls', 'confidence']
_EXTERNAL_REF = re.compile(r'(?:src|href)\s*=\s*["\'](https?://[^"\']+)', re.I)
_ALLOWED_EXTERNAL = ("cdn.jsdelivr.net/npm/chart.js", "cdnjs.cloudflare.com/ajax/libs/Chart.js")


def deepsearch_dashboard(html: str) -> list[str]:
    fails: list[str] = []
    for s in DEEPSEARCH_SECTIONS:
        if f'id="{s}"' not in html:
            fails.append(f"section id=\"{s}\" missing")
    if "chart.umd.min.js" not in html:
        fails.append("Chart.js CDN (chart.umd.min.js) missing")
    if "spiderChart" not in html:
        fails.append("spider canvas 'spiderChart' missing")
    if "downloadReport" not in html:
        fails.append("download button handler 'downloadReport' missing")
    for ref in _EXTERNAL_REF.findall(html):
        if not any(a in ref for a in _ALLOWED_EXTERNAL):
            fails.append(f"external dependency not allowed: {ref[:120]}")
    if html.count("{") != html.count("}"):
        fails.append("JS braces unbalanced")
    try:
        html.encode("utf-8")
    except UnicodeEncodeError:
        fails.append("invalid UTF-8")
    if not html.rstrip().lower().endswith("</html>"):
        fails.append("file does not end with </html>")
    if len(html.encode("utf-8")) <= 20 * 1024:
        fails.append("file size <= 20 KB (insufficient content)")
    if not re.search(r'<body[^>]*data-overall-score="\d{1,3}"', html):
        fails.append('data-overall-score="NN" missing on <body> (ENX addendum)')
    if re.search(r"\{\{[A-Z_]+\}\}|\bTBD\b|lorem ipsum", html):
        fails.append("placeholder text present")
    return fails


def ciso_exec_summary_html(html: str) -> list[str]:
    """ciso-executive-summary / ciso-reporting HTML dashboard: spider with
    5 domains, dual perimeter, no placeholders, self-contained."""
    fails = []
    if "spider" not in html.lower():
        fails.append("spider chart missing")
    if not html.rstrip().lower().endswith("</html>"):
        fails.append("file does not end with </html>")
    if re.search(r"\{\{[A-Z_]+\}\}|\bTBD\b|lorem ipsum", html):
        fails.append("placeholder text present")
    for ref in _EXTERNAL_REF.findall(html):
        if not any(a in ref for a in _ALLOWED_EXTERNAL):
            fails.append(f"external dependency not allowed: {ref[:120]}")
    return fails


def tprm_board_slide(data: dict) -> list[str]:
    """tprm-slide-generator quality checklist: 5 domain scores, top-3 risks =
    highest residuals, footer date present."""
    fails = []
    scores = data.get("domain_scores") or data.get("domains") or {}
    if isinstance(scores, dict):
        n = len([v for v in scores.values() if isinstance(v, (int, float))])
    else:
        n = len(scores)
    if n != 5:
        fails.append(f"expected 5 domain scores, got {n}")
    risks = data.get("top_risks") or data.get("risks") or []
    if risks:
        res = [r.get("residual", 0) for r in risks if isinstance(r, dict)]
        if res != sorted(res, reverse=True)[:len(res)]:
            fails.append("top risks are not ordered by highest residual")
        if len(risks) > 3:
            fails.append("more than 3 top risks")
    if not (data.get("footer_date") or data.get("date") or data.get("assessment_date")):
        fails.append("footer date missing")
    return fails


GATES = {
    "deepsearch-html-dashboard": ("html", deepsearch_dashboard),
    "ciso-executive-summary-html": ("html", ciso_exec_summary_html),
    "tprm-board-slide": ("data", tprm_board_slide),
}
