"""Unit tests for the delivery Function (run in the PR job:
`python -m pytest convertion/functions/delivery/tests -q`).
azure.functions / azure.identity are stubbed when absent; no network."""

from __future__ import annotations

import base64
import json
import sys
import types
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))

# --- stubs so the module imports without the Functions host / Azure creds ----
def _stub_functions():
    fn = types.ModuleType("azure.functions")

    class _App:
        def __init__(self, **kw): pass
        def route(self, **kw):
            return lambda f: f

    class _Resp:
        def __init__(self, body="", status_code=200, mimetype=""):
            self.body, self.status_code = body, status_code
    fn.FunctionApp, fn.HttpResponse, fn.HttpRequest = _App, _Resp, object
    fn.AuthLevel = types.SimpleNamespace(FUNCTION=1, ANONYMOUS=0)
    return fn


try:
    import azure.functions  # noqa: F401
except Exception:  # ImportError or a broken native dependency
    sys.modules.setdefault("azure", types.ModuleType("azure"))
    sys.modules["azure.functions"] = _stub_functions()
# credentials are never exercised in unit tests: always stub the identity module
_idm = types.ModuleType("azure.identity")
_idm.DefaultAzureCredential = lambda: None
sys.modules["azure.identity"] = _idm

import function_app as fa  # noqa: E402
import gates  # noqa: E402
import urlpolicy  # noqa: E402


class FakeResp:
    def __init__(self, status, payload=None):
        self.status_code, self._p = status, payload or {}
    def json(self): return self._p
    def raise_for_status(self):
        if self.status_code >= 400:
            raise fa.requests.HTTPError(str(self.status_code))


def test_normalise_collapses_variants():
    assert fa.normalise(" Acme Test ") == "Acme Test"
    assert fa.normalise('A/B:C*D') == "A-B-C-D"
    assert fa.normalise("Acme.") == "Acme"


def test_ensure_path_reuses_existing_creates_missing_and_survives_race(monkeypatch):
    calls = []

    def graph(method, url, **kw):
        calls.append((method, url))
        if method == "GET" and url.endswith(":/Acme"):
            return FakeResp(200, {"id": "sup"})
        if method == "GET" and url.endswith(":/SOC"):
            return FakeResp(404) if len([c for c in calls if c[1].endswith(":/SOC")]) == 1 else FakeResp(200, {"id": "svc"})
        if method == "POST" and url.endswith("sup/children"):
            return FakeResp(409)                     # concurrent creation
        raise AssertionError(url)
    monkeypatch.setattr(fa, "_graph", graph)
    assert fa.ensure_path("d", "root", ["Acme ", "SOC"]) == "svc"
    assert ("POST", f"{fa.GRAPH}/drives/d/items/sup/children") in calls


def test_ensure_path_404_creates(monkeypatch):
    def graph(method, url, **kw):
        if method == "GET":
            return FakeResp(404)
        return FakeResp(201, {"id": "new-" + kw["json"]["name"]})
    monkeypatch.setattr(fa, "_graph", graph)
    assert fa.ensure_path("d", "root", ["Acme", "SOC"]) == "new-SOC"


def test_extract_payload_first_fenced_block_and_html():
    text = 'Here is the contract:\n```json\n{"a": 1}\n```\nthanks\n```json\n{"b": 2}\n```'
    assert fa._extract_payload(text, "docx") == {"a": 1}
    assert fa._extract_payload({"x": 1}, "docx") == {"x": 1}
    html = "prose <html><body data-overall-score=\"55\">x</body></html> trailing"
    assert fa._extract_payload(html, "html").startswith("<html>")
    with pytest.raises(fa.Http):
        fa._extract_payload("no json here", "docx")


def test_filename_pattern_enforced():
    assert fa.check_filename("DeepSearch_Acme_SOC_2026-09-12.html", "html")
    with pytest.raises(fa.Http):
        fa.check_filename("../evil.html", "html")
    with pytest.raises(fa.Http):
        fa.check_filename("report.docx", "pptx")


def test_renderer_dir_rejects_traversal(tmp_path, monkeypatch):
    monkeypatch.setattr(fa, "RENDERERS", tmp_path)
    (tmp_path / "ok").mkdir()
    assert fa._renderer_dir("ok") == (tmp_path / "ok").resolve()
    for bad in ("../x", "OK", "a b", "missing"):
        with pytest.raises(fa.Http):
            fa._renderer_dir(bad)


def test_materialise_unpacks_zip_once(tmp_path):
    import zipfile
    d = tmp_path / "r"; d.mkdir()
    with zipfile.ZipFile(d / "x-scripts.zip", "w") as z:
        z.writestr("scripts/a.py", "print(1)")
    fa._materialise(d); fa._materialise(d)
    assert (d / "scripts" / "a.py").exists() and (d / ".x-scripts.unpacked").exists()


def test_deepsearch_gate_detects_missing_sections():
    html = "<html><body data-overall-score=\"42\">" + "".join(f'<div id="{s}"></div>' for s in gates.DEEPSEARCH_SECTIONS[:-1])
    html += '<script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script><canvas id="spiderChart"></canvas>'
    html += "<button onclick=\"downloadReport()\">x</button>" + "x" * 25000 + "</body></html>"
    fails = gates.deepsearch_dashboard(html)
    assert any("confidence" in f for f in fails) and len(fails) == 1
    assert gates.deepsearch_dashboard(html.replace('<div id="controls">', '<div id="controls"><div id="confidence">')) == []


def test_url_policy_blocks_internal_and_private(monkeypatch):
    ok, why = urlpolicy.check_url("http://nvd.nist.gov/x", resolve=False)
    assert not ok and "https" in why
    assert not urlpolicy.check_url("https://10.0.0.1/", resolve=False)[0]
    assert not urlpolicy.check_url("https://intranet.local/", resolve=False)[0]
    assert not urlpolicy.check_url("https://nvd.nist.gov/?q=ENX-1234", resolve=False)[0]
    assert not urlpolicy.check_url("https://random-host.example/", resolve=False)[0]
    assert urlpolicy.check_url("https://nvd.nist.gov/vuln/detail/CVE-2026-0001", resolve=False)[0]
    assert urlpolicy.check_url("https://trust.vendor.example/security", "vendor.example", resolve=False)[0]
    assert not urlpolicy._is_public_ip("192.168.1.1") and urlpolicy._is_public_ip("93.184.216.34")


def test_html_to_text_strips_scripts():
    title, text = fa.html_to_text("<html><head><title>T</title><script>x()</script></head><body><p>Hello&nbsp;<b>w</b></p><nav>menu</nav></body></html>")
    assert title == "T" and "Hello" in text and "x()" not in text and "menu" not in text


def test_tprm_gate():
    assert gates.tprm_board_slide({"domain_scores": {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5}, "date": "2026-09-12",
                                   "top_risks": [{"residual": 8}, {"residual": 6}, {"residual": 5}]}) == []
    assert gates.tprm_board_slide({"domain_scores": {"a": 1}, "top_risks": [{"residual": 1}, {"residual": 9}]})


def test_manifest_fallbacks(tmp_path):
    (tmp_path / "render.py").write_text("")
    assert fa._manifest(tmp_path)["runtime"] == "python"
    (tmp_path / "manifest.json").write_text(json.dumps({"runtime": "node", "entry": "x.js"}))
    assert fa._manifest(tmp_path)["entry"] == "x.js"


def test_b64_roundtrip_collect(tmp_path):
    (tmp_path / "a.pptx").write_bytes(b"P")
    (tmp_path / "b.pdf").write_bytes(b"D")
    prim, files = fa._collect(tmp_path, "pdf", "X.pdf")
    assert prim["fileName"] == "X.pdf" and base64.b64decode(prim["contentBase64"]) == b"D" and len(files) == 2


# --------------------------- request contracts, OCR and the xlsx recalc gate
class FakeReq:
    def __init__(self, body):
        self._b = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.headers = {}
        self.url = "http://localhost/api/test"

    def get_body(self):
        return self._b


def test_body_validates_extract_pdf_and_names_the_bad_field():
    b = fa._body(FakeReq({"fileId": "asst-1", "model": "prebuilt-layout", "pages": "1-5"}), "extract_pdf")
    assert b["model"] == "prebuilt-layout"
    for bad in ({"fileId": "a", "model": "prebuilt-invoice"},     # not an allowed model
                {"fileId": "a", "pages": "one"},                  # not a page range
                {"model": "prebuilt-read"},                       # no file source at all
                {"fileId": "a", "unexpected": 1}):                # additionalProperties
        with pytest.raises(fa.Http) as e:
            fa._body(FakeReq(bad), "extract_pdf")
        assert e.value.status == 400


def test_body_rejects_non_object_and_unparsable_bodies():
    for bad in (b"", b"[1,2]", b"{oops"):
        with pytest.raises(fa.Http) as e:
            fa._body(FakeReq(bad), "fetch_evidence")
        assert e.value.status == 400


def test_extract_payload_survives_a_broken_first_block_and_rejects_scalars():
    assert fa._extract_payload('```json\n{broken\n```\n```json\n{"b": 2}\n```', "docx") == {"b": 2}
    assert fa._extract_payload('prose {"a": [1, 2]} tail', "docx") == {"a": [1, 2]}
    for scalar in ('"a string"', "42", "   "):
        with pytest.raises(fa.Http):
            fa._extract_payload(scalar, "docx")


def test_validate_schema_fails_closed_on_an_unreadable_schema(tmp_path, monkeypatch):
    (tmp_path / "t.schema.json").write_text("{not json", encoding="utf-8")
    monkeypatch.setattr(fa, "SCHEMA_DIRS", [tmp_path])
    with pytest.raises(fa.Http) as e:
        fa._validate_schema("t", {"any": 1})
    assert e.value.status == 500


def test_validate_schema_400_names_the_failing_path(tmp_path, monkeypatch):
    (tmp_path / "t.schema.json").write_text(json.dumps(
        {"type": "object", "required": ["title"],
         "properties": {"title": {"type": "string"}}}), encoding="utf-8")
    monkeypatch.setattr(fa, "SCHEMA_DIRS", [tmp_path])
    with pytest.raises(fa.Http) as e:
        fa._validate_schema("t", {"title": 7})
    assert e.value.status == 400 and e.value.extra["path"] == ["title"]


def _xlsx_files():
    prim = {"fileName": "R.xlsx", "kind": "xlsx", "contentBase64": "b2xk"}   # "old"
    return prim, [prim]


def test_recalc_gate_is_reported_as_not_run_when_office_tools_is_absent(monkeypatch):
    monkeypatch.setattr(fa, "OFFICE_TOOLS_BASE", "")
    prim, files = _xlsx_files()
    gate = fa._recalc_gate(prim, files)
    assert gate["passed"] is None and "office-tools" in gate["reason"]


def test_recalc_gate_replaces_the_bytes_with_the_recalculated_workbook(monkeypatch):
    monkeypatch.setattr(fa, "OFFICE_TOOLS_BASE", "https://office.invalid/api")
    monkeypatch.setattr(fa, "_office_tools", lambda p, payload, **kw: {
        "gate": {"passed": True, "checks": []}, "total_errors": 0, "total_formulas": 12,
        "contentBase64": "bmV3"})                                            # "new"
    prim, files = _xlsx_files()
    gate = fa._recalc_gate(prim, files)
    assert gate["passed"] and files[0]["contentBase64"] == "bmV3" and prim["contentBase64"] == "bmV3"


def test_recalc_gate_422s_on_excel_errors(monkeypatch):
    monkeypatch.setattr(fa, "OFFICE_TOOLS_BASE", "https://office.invalid/api")
    monkeypatch.setattr(fa, "_office_tools", lambda p, payload, **kw: {
        "gate": {"passed": False, "checks": ["2 Excel error(s): #REF!"]}, "total_errors": 2})
    prim, files = _xlsx_files()
    with pytest.raises(fa.Http) as e:
        fa._recalc_gate(prim, files)
    assert e.value.status == 422 and e.value.extra["gate"] == "xlsx-recalc"


def test_recalc_gate_is_a_noop_without_xlsx_output():
    prim = {"fileName": "R.pptx", "kind": "pptx", "contentBase64": "eA=="}
    assert fa._recalc_gate(prim, [prim]) == {"passed": True, "checks": []}


def test_docintel_confidence_summarises_word_confidence():
    c = fa._docintel_confidence({"pages": [{"words": [{"confidence": 0.9}, {"confidence": 0.7}]}]})
    assert c["mean"] == 0.8 and c["min"] == 0.7 and c["words"] == 2
    assert fa._docintel_confidence({"pages": []})["mean"] is None


# --- evidence cache (delta re-analysis, requirement d2) --------------------
# Each test encodes a way the cache could return a WRONG answer, which matters
# more than whether it returns a fast one: a bad hit puts stale facts in a
# report of record.
class _CacheGraph:
    """Stands in for the Graph list API with one stored row."""

    def __init__(self, row):
        self.row = row
        self.writes = []

    def __call__(self, method, url, **kw):
        if method == "GET":
            value = [self.row] if self.row else []
            return FakeResp(200, {"value": value})
        self.writes.append((url, kw.get("json")))
        return FakeResp(200, {"id": "1"})


def _row(fields):
    return {"id": "1", "fields": fields}


def _fresh_row(**over):
    base = {"CacheKey": "d1|i1", "ETag": "etag-1", "FileName": "iso27001.pdf",
            "Facts": json.dumps({"documentType": "ISO 27001 certificate"}),
            "ExtractorRef": "tpa-evidence-analyzer:7",
            "RunId": "run-123",
            "StoredAt": fa.datetime.now(fa.timezone.utc).isoformat()}
    base.update(over)
    return _row(base)


def test_cache_hit_returns_the_stored_facts(monkeypatch):
    monkeypatch.setattr(fa, "SITE_ID", "site")
    monkeypatch.setattr(fa, "_graph", _CacheGraph(_fresh_row()))
    out = fa._evidence_cache_lookup("d1", "i1", "etag-1", "tpa-evidence-analyzer:7")
    assert out["hit"] is True
    assert out["facts"]["documentType"] == "ISO 27001 certificate"
    assert out["sourceRunId"] == "run-123"


def test_changed_etag_is_a_miss(monkeypatch):
    """The file was edited or replaced: its old facts describe other bytes."""
    monkeypatch.setattr(fa, "SITE_ID", "site")
    monkeypatch.setattr(fa, "_graph", _CacheGraph(_fresh_row()))
    out = fa._evidence_cache_lookup("d1", "i1", "etag-2", "tpa-evidence-analyzer:7")
    assert out == {"hit": False, "reason": "etag-changed"}


def test_changed_extractor_is_a_miss(monkeypatch):
    """A newer charter reads documents differently, so its output is not
    interchangeable with the old one."""
    monkeypatch.setattr(fa, "SITE_ID", "site")
    monkeypatch.setattr(fa, "_graph", _CacheGraph(_fresh_row()))
    out = fa._evidence_cache_lookup("d1", "i1", "etag-1", "tpa-evidence-analyzer:8")
    assert out == {"hit": False, "reason": "extractor-changed"}


def test_entry_past_the_age_cap_is_a_miss(monkeypatch):
    monkeypatch.setattr(fa, "SITE_ID", "site")
    monkeypatch.setattr(fa, "EVIDENCE_CACHE_MAX_AGE_DAYS", 180)
    old = (fa.datetime.now(fa.timezone.utc) - fa.timedelta(days=200)).isoformat()
    monkeypatch.setattr(fa, "_graph", _CacheGraph(_fresh_row(StoredAt=old)))
    out = fa._evidence_cache_lookup("d1", "i1", "etag-1", "tpa-evidence-analyzer:7")
    assert out["hit"] is False and out["reason"] == "expired"


def test_missing_row_is_a_miss_not_an_error(monkeypatch):
    monkeypatch.setattr(fa, "SITE_ID", "site")
    monkeypatch.setattr(fa, "_graph", _CacheGraph(None))
    assert fa._evidence_cache_lookup("d1", "i1", "e", "")["reason"] == "not-cached"


def test_unreadable_facts_are_a_miss(monkeypatch):
    monkeypatch.setattr(fa, "SITE_ID", "site")
    monkeypatch.setattr(fa, "_graph", _CacheGraph(_fresh_row(Facts="{not json")))
    assert fa._evidence_cache_lookup("d1", "i1", "etag-1", "")["reason"] == "unreadable"


def test_store_skips_entries_without_facts(monkeypatch):
    """Nothing extracted means nothing to reuse — an empty row would turn into
    a hit that silently contributes no evidence."""
    seen = []
    monkeypatch.setattr(fa, "_list_upsert",
                        lambda lst, match, fields: seen.append(match) or {"action": "created"})
    out = fa._evidence_cache_store(
        [{"driveId": "d1", "itemId": "i1", "eTag": "e1", "facts": {"documentType": "SOC 2"}},
         {"driveId": "d1", "itemId": "i2", "eTag": "e2", "facts": {}}],
        "tpa-evidence-analyzer:7", "run-9")
    assert out["stored"] == 1
    assert seen == [{"CacheKey": "d1|i1"}]
