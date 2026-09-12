"""Unit tests for the office-tools Function (`python -m pytest
convertion/functions/office-tools/tests -q`, or together with the delivery
suite). azure.functions is stubbed when absent; no LibreOffice, no network and
no staged toolchain needed — these cover the request contracts, the input
guards and the script resolution.

The module is loaded under the unique name `office_function_app` rather than
through sys.path: the delivery Function has a `function_app` module too, and
one pytest run must not resolve both to the same import."""

from __future__ import annotations

import base64
import importlib.util
import json
import sys
import types
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent.parent


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

_spec = importlib.util.spec_from_file_location("office_function_app", HERE / "function_app.py")
oa = importlib.util.module_from_spec(_spec)
sys.modules["office_function_app"] = oa
_spec.loader.exec_module(oa)


class FakeReq:
    """Minimal HttpRequest: body + headers are all the guards read."""
    def __init__(self, body, headers=None):
        self._b = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.headers = headers or {}
        self.url = "http://localhost/api/test"

    def get_body(self):
        return self._b


def _payload(**kw):
    return {"contentBase64": base64.b64encode(b"PK\x03\x04stub").decode(),
            "fileName": "Book.xlsx", **kw}


# ------------------------------------------------------------ body contracts
def test_body_of_accepts_a_valid_payload():
    b = oa.body_of(FakeReq(_payload(timeoutSeconds=30)), "recalc")
    assert b["fileName"] == "Book.xlsx" and b["timeoutSeconds"] == 30


@pytest.mark.parametrize("body,fragment", [
    (b"", "empty body"),
    (b"{not json", "not valid UTF-8 JSON"),
    ([1, 2], "must be a JSON object"),
])
def test_body_of_rejects_malformed_bodies(body, fragment):
    with pytest.raises(oa.Http) as e:
        oa.body_of(FakeReq(body), "recalc")
    assert e.value.status == 400 and fragment in e.value.msg


def test_body_of_rejects_missing_and_unknown_fields():
    with pytest.raises(oa.Http) as missing:
        oa.body_of(FakeReq({"fileName": "Book.xlsx"}), "recalc")
    assert missing.value.status == 400
    with pytest.raises(oa.Http) as extra:
        oa.body_of(FakeReq(_payload(driveId="sneaky")), "recalc")
    assert extra.value.status == 400        # additionalProperties: no SharePoint reads here


def test_body_of_rejects_an_unsupported_convert_target():
    with pytest.raises(oa.Http) as e:
        oa.body_of(FakeReq(_payload(fileName="a.docx", to="exe")), "convert")
    assert e.value.status == 400 and "invalid convert payload" in e.value.msg


# ----------------------------------------------------------------- guards
@pytest.mark.parametrize("name", ["../../etc/passwd", "a/b.docx", "no-extension", ""])
def test_safe_name_rejects_traversal_and_oddities(name):
    with pytest.raises(oa.Http):
        oa.safe_name(name)


def test_safe_name_keeps_the_report_naming_convention():
    assert oa.safe_name("CISO_Acme_Portal_2026-09-12.xlsx") == "CISO_Acme_Portal_2026-09-12.xlsx"


def test_decode_input_tolerates_wrapped_base64_and_rejects_junk():
    wrapped = "UEsD\nBBQ=\n"
    assert oa.decode_input({"contentBase64": wrapped}).startswith(b"PK")
    with pytest.raises(oa.Http) as e:
        oa.decode_input({"contentBase64": "not base64 !!"})
    assert e.value.status == 400


def test_decode_input_enforces_the_payload_cap(monkeypatch):
    monkeypatch.setattr(oa, "MAX_PAYLOAD", 4)
    with pytest.raises(oa.Http) as e:
        oa.decode_input({"contentBase64": base64.b64encode(b"0123456789").decode()})
    assert e.value.status == 413


def test_missing_toolchain_is_501_not_500(monkeypatch, tmp_path):
    monkeypatch.setattr(oa, "TOOLCHAIN", tmp_path)
    with pytest.raises(oa.Http) as e:
        oa.script("recalc")
    assert e.value.status == 501 and "stage_toolchain" in json.dumps(e.value.extra)


# ------------------------------------------------------------ engine choice
@pytest.mark.parametrize("src,to,expected", [
    ("docx", "pdf", "soffice"),
    ("doc", "docx", "soffice"),
    ("md", "docx", "pandoc"),
    ("html", "md", "pandoc"),
    ("pdf", "png", "poppler"),
])
def test_engine_selection_matches_the_skill_toolchain(src, to, expected):
    assert oa._engine_for(src, to, "auto") == expected


def test_engine_can_be_forced():
    assert oa._engine_for("docx", "pdf", "pandoc") == "pandoc"
