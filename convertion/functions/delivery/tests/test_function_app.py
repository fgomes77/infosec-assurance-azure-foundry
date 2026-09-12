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
