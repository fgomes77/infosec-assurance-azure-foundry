"""Delivery Function App — SharePoint storage, report rendering and the
governed compute endpoints the converted skills need but Foundry's
code_interpreter cannot provide (no network, no Node, no Chromium).

Called by the Logic App pipelines in ../../workflows/ and (compute routes
only) by agents through the OpenAPI connections in
../../integrations/openapi/ (osint-proxy, passive-recon, pdf-coverage).
Function-key + VNet restricted; optional Easy Auth principal pinning
(ALLOWED_CALLER_PRINCIPAL_IDS). The managed identity holds Graph
Sites.Selected write on the InfoSec Assurance site — agents themselves are
read-only, see ../../sharepoint/README.md.

  POST /api/ensure_folder   {driveId, rootItemId, segments: [Supplier, Service]}
      -> {folderId}            idempotent, race-safe, reuse-never-duplicate
  POST /api/upload           {driveId, folderId, fileName, contentBase64, share?}
      -> {itemId, webUrl, shareUrl?}
  POST /api/render           {format: html|docx|pptx|xlsx|pdf|png|svg, template?,
                              data|content, fileName?, pdf?: {format, landscape}}
      -> {fileName, contentBase64, files: [{fileName, contentBase64, kind}], gate}
         `files` carries EVERY file the renderer produced (multi-file
         deliverables: ciso-reporting HTML+PDF+PPTX, tprm HTML+XLSX+PPTX);
         fileName/contentBase64 = the primary file of the requested format.
  POST /api/portfolio_update {supplierName, serviceName, tpaStatus, reportType, reportUrl, runId, approvedBy}
  POST /api/history_append   {supplierName, serviceName, assessmentDate, composite, reportType, reportUrl, runId}
  POST /api/fetch_evidence   {driveId, itemId} -> {fileId, fileName, bytes}   (SharePoint -> Foundry file)
  GET  /api/fetch_public_page?url=&supplierDomain=&mode=&maxBytes=   (osint-proxy.yaml)
  GET  /api/allowlist
  GET  /api/passive_recon?domain=                                     (passive-recon.yaml)
  POST /api/pdf/{stage}      stage: triage|inventory|chunk|verify|cross_check (pdf-coverage.yaml)
  POST /api/speaker_clips    {transcript, audioBase64|driveId+itemId, format} -> zip
  GET  /api/health

Rendering executes the byte-verified generators staged by
../../scripts/stage_renderers.py into renderers/<template>/ (manifest.json
per renderer, see renderers-src/README.md) so outputs match claude.ai.
"""

from __future__ import annotations

import base64
import io
import json
import logging
import os
import re
import shutil
import socket
import ssl
import subprocess
import tempfile
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

import azure.functions as func
import requests
from azure.identity import DefaultAzureCredential

import gates
import urlpolicy

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)
log = logging.getLogger("delivery")

GRAPH = "https://graph.microsoft.com/v1.0"
_cred = DefaultAzureCredential()

HERE = Path(__file__).parent
RENDERERS = HERE / "renderers"                 # staged by stage_renderers.py
SCHEMA_DIRS = [RENDERERS / "_schemas", HERE.parent.parent / "templates"]

MAX_PAYLOAD = int(os.environ.get("MAX_PAYLOAD_BYTES", str(50 * 1024 * 1024)))
FORMATS = {"html", "docx", "pptx", "xlsx", "pdf", "png", "svg", "zip", "json", "md"}
TEMPLATE_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,39}$")
FILENAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ._()\-]{0,180}\.(html|docx|pptx|xlsx|pdf|png|svg|zip|json|md)$")
ILLEGAL = re.compile(r'[\"*:<>?/\\|]')
ALLOWED_PRINCIPALS = {p.strip() for p in os.environ.get("ALLOWED_CALLER_PRINCIPAL_IDS", "").split(",") if p.strip()}

SITE_ID = os.environ.get("SHAREPOINT_SITE_ID", "")
PORTFOLIO_LIST = os.environ.get("PORTFOLIO_LIST_NAME", "TPRM Portfolio")
HISTORY_LIST = os.environ.get("HISTORY_LIST_NAME", "TPSRCA History")
PROJECT_ENDPOINT = os.environ.get("PROJECT_ENDPOINT", "").rstrip("/")
FOUNDRY_API_VERSION = os.environ.get("FOUNDRY_API_VERSION", "2025-05-15-preview")


# --------------------------------------------------------------------- utils
class Http(Exception):
    def __init__(self, status: int, msg: str, extra: dict | None = None):
        super().__init__(msg)
        self.status, self.msg, self.extra = status, msg, extra or {}


def _json(obj, status=200) -> func.HttpResponse:
    return func.HttpResponse(json.dumps(obj, ensure_ascii=False), status_code=status,
                             mimetype="application/json")


def _guard(fn):
    """Common wrapper: caller pinning, payload cap, structured errors."""
    def inner(req: func.HttpRequest) -> func.HttpResponse:
        try:
            if ALLOWED_PRINCIPALS:
                pid = req.headers.get("x-ms-client-principal-id", "")
                if pid not in ALLOWED_PRINCIPALS:
                    raise Http(403, "caller principal not allowed")
            if len(req.get_body() or b"") > MAX_PAYLOAD:
                raise Http(413, f"payload exceeds {MAX_PAYLOAD} bytes")
            return fn(req)
        except Http as e:
            log.warning("%s -> %s %s", req.url, e.status, e.msg)
            return _json({"error": e.msg, **e.extra}, e.status)
        except (KeyError, ValueError, json.JSONDecodeError) as e:
            return _json({"error": f"bad request: {e}"}, 400)
        except subprocess.CalledProcessError as e:
            tail = (e.stderr or e.stdout or b"")
            tail = tail.decode(errors="replace") if isinstance(tail, bytes) else str(tail)
            return _json({"error": "renderer failed", "detail": tail[-4000:]}, 500)
        except requests.HTTPError as e:
            return _json({"error": "upstream error", "detail": str(e)[:500]}, 502)
    inner.__name__ = fn.__name__
    return inner


def _token(scope="https://graph.microsoft.com/.default") -> str:
    return _cred.get_token(scope).token


def _graph(method: str, url: str, **kw) -> requests.Response:
    headers = kw.pop("headers", {})
    headers["Authorization"] = f"Bearer {_token()}"
    return requests.request(method, url, headers=headers, timeout=60, **kw)


def normalise(name: str) -> str:
    """Trim and replace Graph-illegal characters so name variants of the
    same supplier/service resolve to one folder."""
    return ILLEGAL.sub("-", name.strip()).rstrip(". ")


def check_filename(name: str, fmt: str) -> str:
    name = normalise(name)
    if not FILENAME_RE.match(name):
        raise Http(400, "fileName must match <ReportType>_<Supplier>_<Service>_<yyyy-MM-dd>.<ext>")
    if fmt and not name.lower().endswith("." + fmt):
        raise Http(400, f"fileName extension does not match format {fmt}")
    return name


# ------------------------------------------------------------ SharePoint
def ensure_path(drive_id: str, parent_id: str, segments: list[str]) -> str:
    """The requirement-a/c/d/e/f folder rule: reuse an existing folder,
    create only what is missing. Returns the final folder's item id."""
    for raw in segments:
        seg = normalise(raw)
        if not seg:
            raise ValueError("empty folder segment")
        got = _graph("GET", f"{GRAPH}/drives/{drive_id}/items/{parent_id}:/{seg}")
        if got.status_code == 200:
            parent_id = got.json()["id"]           # exists -> reuse, never duplicate
            continue
        if got.status_code != 404:
            got.raise_for_status()
        made = _graph(
            "POST", f"{GRAPH}/drives/{drive_id}/items/{parent_id}/children",
            json={"name": seg, "folder": {},
                  "@microsoft.graph.conflictBehavior": "fail"},
        )
        if made.status_code == 409:                # concurrent creation race
            got = _graph("GET", f"{GRAPH}/drives/{drive_id}/items/{parent_id}:/{seg}")
            got.raise_for_status()
            parent_id = got.json()["id"]
        else:
            made.raise_for_status()
            parent_id = made.json()["id"]
    return parent_id


@app.route(route="ensure_folder", methods=["POST"])
@_guard
def ensure_folder(req: func.HttpRequest) -> func.HttpResponse:
    body = req.get_json()
    folder_id = ensure_path(body["driveId"], body["rootItemId"], body["segments"])
    return _json({"folderId": folder_id})


@app.route(route="upload", methods=["POST"])
@_guard
def upload(req: func.HttpRequest) -> func.HttpResponse:
    body = req.get_json()
    drive, folder = body["driveId"], body["folderId"]
    name = check_filename(body["fileName"], "")
    content = base64.b64decode(body["contentBase64"])

    # <4 MiB simple upload, else chunked upload session (Graph requirement)
    if len(content) < 4 * 1024 * 1024:
        up = _graph(
            "PUT",
            f"{GRAPH}/drives/{drive}/items/{folder}:/{name}:/content"
            "?@microsoft.graph.conflictBehavior=replace",
            data=content,
            headers={"Content-Type": "application/octet-stream"},
        )
        up.raise_for_status()
        item = up.json()
    else:
        sess = _graph(
            "POST",
            f"{GRAPH}/drives/{drive}/items/{folder}:/{name}:/createUploadSession",
            json={"item": {"@microsoft.graph.conflictBehavior": "replace"}},
        )
        sess.raise_for_status()
        url = sess.json()["uploadUrl"]
        chunk = 5 * 1024 * 1024
        for i in range(0, len(content), chunk):
            part = content[i:i + chunk]
            r = requests.put(url, data=part, timeout=120, headers={
                "Content-Length": str(len(part)),
                "Content-Range": f"bytes {i}-{i + len(part) - 1}/{len(content)}",
            })
            r.raise_for_status()
        item = r.json()

    out = {"itemId": item["id"], "webUrl": item.get("webUrl")}
    if body.get("share"):
        link = _graph(
            "POST", f"{GRAPH}/drives/{drive}/items/{item['id']}/createLink",
            json={"type": "view", "scope": "organization"},  # never anonymous
        )
        link.raise_for_status()
        out["shareUrl"] = link.json()["link"]["webUrl"]
    return _json(out)


@app.route(route="assign_label", methods=["POST"])
@_guard
def assign_label(req: func.HttpRequest) -> func.HttpResponse:
    """Assign a Purview sensitivity label to a delivered file (finding C16).
    Graph driveItem:assignSensitivityLabel is asynchronous, protected and
    metered (pay-as-you-go); 202 + Location is the success case. When no
    labelId is configured the pipeline skips this call and the library
    default label applies. The per-file label SUPPLEMENTS the library
    default, it does not replace it."""
    b = req.get_json()
    payload = {"sensitivityLabelId": b["labelId"],
               "assignmentMethod": b.get("assignmentMethod", "standard")}
    if b.get("justification"):
        payload["justificationText"] = b["justification"]
    r = _graph("POST",
               f"{GRAPH}/drives/{b['driveId']}/items/{b['itemId']}"
               f"/assignSensitivityLabel", json=payload)
    r.raise_for_status()
    return _json({"itemId": b["itemId"], "labelId": b["labelId"],
                  "status": "accepted", "reportType": b.get("reportType", ""),
                  "runId": b.get("runId", ""),
                  "jobUrl": r.headers.get("Location", "")}, 202)


def _list_upsert(list_name: str, match: dict, fields: dict) -> dict:
    """Create-or-update one SharePoint list item (Graph lists API) matched on
    the given fields — used for the TPRM Portfolio / TPSRCA History lists."""
    if not SITE_ID:
        raise Http(503, "SHAREPOINT_SITE_ID not configured")
    base = f"{GRAPH}/sites/{SITE_ID}/lists/{list_name}/items"
    hit = None
    if match:
        flt = " and ".join(f"fields/{k} eq '{str(v).replace(chr(39), chr(39)*2)}'" for k, v in match.items())
        r = _graph("GET", base, params={"$expand": "fields", "$filter": flt},
                   headers={"Prefer": "HonorNonIndexedQueriesWarningMayFailRandomly"})
        if r.status_code == 200 and r.json().get("value"):
            hit = r.json()["value"][0]
    if hit:
        r = _graph("PATCH", f"{base}/{hit['id']}/fields", json=fields)
        r.raise_for_status()
        return {"itemId": hit["id"], "action": "updated"}
    r = _graph("POST", base, json={"fields": {**match, **fields}})
    r.raise_for_status()
    return {"itemId": r.json()["id"], "action": "created"}


@app.route(route="portfolio_update", methods=["POST"])
@_guard
def portfolio_update(req: func.HttpRequest) -> func.HttpResponse:
    b = req.get_json()
    now = datetime.now(timezone.utc).isoformat()
    out = _list_upsert(PORTFOLIO_LIST,
                       {"Supplier": normalise(b["supplierName"]), "Service": normalise(b["serviceName"])},
                       {"TPAStatus": b["tpaStatus"], "LastReportType": b.get("reportType", ""),
                        "LastReportUrl": b.get("reportUrl", ""), "LastRunId": b.get("runId", ""),
                        "ApprovedBy": b.get("approvedBy", ""), "UpdatedAt": now})
    return _json(out)


@app.route(route="history_append", methods=["POST"])
@_guard
def history_append(req: func.HttpRequest) -> func.HttpResponse:
    b = req.get_json()
    comp = float(str(b["composite"]).strip())
    out = _list_upsert(HISTORY_LIST, {},
                       {"Supplier": normalise(b["supplierName"]), "Service": normalise(b["serviceName"]),
                        "AssessmentDate": b["assessmentDate"], "Composite": comp,
                        "ReportType": b.get("reportType", ""), "ReportUrl": b.get("reportUrl", ""),
                        "RunId": b.get("runId", "")})
    return _json(out)


def _drive_item_bytes(drive_id: str, item_id: str) -> tuple[bytes, str]:
    meta = _graph("GET", f"{GRAPH}/drives/{drive_id}/items/{item_id}")
    meta.raise_for_status()
    name = meta.json().get("name", "file.bin")
    content = _graph("GET", f"{GRAPH}/drives/{drive_id}/items/{item_id}/content", stream=True)
    content.raise_for_status()
    data = content.content
    if len(data) > MAX_PAYLOAD:
        raise Http(413, "evidence file larger than MAX_PAYLOAD_BYTES")
    return data, name


def _foundry_upload(data: bytes, name: str) -> str:
    if not PROJECT_ENDPOINT:
        raise Http(503, "PROJECT_ENDPOINT not configured")
    r = requests.post(f"{PROJECT_ENDPOINT}/files", params={"api-version": FOUNDRY_API_VERSION},
                      headers={"Authorization": f"Bearer {_token('https://ai.azure.com/.default')}"},
                      files={"file": (name, data)}, data={"purpose": "assistants"}, timeout=300)
    r.raise_for_status()
    return r.json()["id"]


def _foundry_download(file_id: str) -> bytes:
    r = requests.get(f"{PROJECT_ENDPOINT}/files/{file_id}/content",
                     params={"api-version": FOUNDRY_API_VERSION},
                     headers={"Authorization": f"Bearer {_token('https://ai.azure.com/.default')}"}, timeout=300)
    r.raise_for_status()
    return r.content


@app.route(route="fetch_evidence", methods=["POST"])
@_guard
def fetch_evidence(req: func.HttpRequest) -> func.HttpResponse:
    """Attach a SharePoint evidence file to the Foundry project (file_search /
    code_interpreter) without streaming it through the conversation."""
    b = req.get_json()
    data, name = _drive_item_bytes(b["driveId"], b["itemId"])
    return _json({"fileId": _foundry_upload(data, name), "fileName": name, "bytes": len(data)})


def _input_bytes(b: dict, key_prefix: str = "") -> tuple[bytes, str]:
    """Resolve an input file from contentBase64 | driveId+itemId | fileId."""
    if b.get(key_prefix + "contentBase64"):
        return base64.b64decode(b[key_prefix + "contentBase64"]), b.get(key_prefix + "fileName", "input.bin")
    if b.get(key_prefix + "driveId") and b.get(key_prefix + "itemId"):
        return _drive_item_bytes(b[key_prefix + "driveId"], b[key_prefix + "itemId"])
    if b.get(key_prefix + "fileId"):
        return _foundry_download(b[key_prefix + "fileId"]), b.get(key_prefix + "fileName", "input.bin")
    raise Http(400, f"provide {key_prefix}contentBase64, {key_prefix}driveId+{key_prefix}itemId or {key_prefix}fileId")


# ---------------------------------------------------------------- render
def _renderer_dir(name: str) -> Path:
    if not TEMPLATE_RE.match(name or ""):
        raise Http(400, "invalid template name")
    d = (RENDERERS / name).resolve()
    if RENDERERS.resolve() not in d.parents or not d.is_dir():
        raise Http(404, f"renderer '{name}' is not staged")
    _materialise(d)
    return d


def _materialise(d: Path) -> None:
    """Unpack the byte-verified <skill>-scripts.zip staged from build/agents/
    (once) so its scripts/ and assets/ trees are runnable in place."""
    for z in d.glob("*-scripts.zip"):
        marker = d / f".{z.stem}.unpacked"
        if marker.exists():
            continue
        with zipfile.ZipFile(z) as zf:
            for m in zf.namelist():
                if m.startswith("/") or ".." in Path(m).parts:
                    raise Http(500, f"unsafe member in {z.name}")
            zf.extractall(d)
        marker.write_text(datetime.now(timezone.utc).isoformat())


def _manifest(d: Path) -> dict:
    mf = d / "manifest.json"
    if mf.exists():
        return json.loads(mf.read_text(encoding="utf-8"))
    if (d / "render.py").exists():
        return {"runtime": "python", "entry": "render.py", "argv": ["{data}", "{out}"], "outputs": "single"}
    if (d / "generate_slide.js").exists():
        return {"runtime": "node", "entry": "generate_slide.js", "argv": ["{data}", "{out}"], "outputs": "single"}
    raise Http(500, f"renderer {d.name} has no manifest.json / render.py / generate_slide.js")


def _extract_payload(text, fmt: str):
    """Agent messages arrive as prose + one fenced ```json block (or the
    finished HTML). Return the JSON object / HTML string the renderer needs."""
    if isinstance(text, (dict, list)):
        return text
    if text is None:
        raise Http(400, "data/content missing")
    s = str(text)
    if fmt == "html" or (fmt == "pdf" and "<html" in s.lower() and "```json" not in s):
        m = re.search(r"<!doctype html.*?</html>|<html.*?</html>", s, re.I | re.S)
        return m.group(0) if m else s
    m = re.search(r"```json\s*(.*?)```", s, re.S | re.I)
    if m:
        return json.loads(m.group(1))
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        raise Http(400, "no fenced ```json block found in data")


def _validate_schema(template: str, data) -> None:
    for sd in SCHEMA_DIRS:
        for cand in (sd / f"{template}.schema.json", sd / f"{template.replace('-', '_')}.schema.json"):
            if cand.exists():
                import jsonschema
                try:
                    jsonschema.validate(data, json.loads(cand.read_text(encoding="utf-8")))
                except jsonschema.ValidationError as e:
                    raise Http(400, f"data does not match {cand.name}: {e.message}",
                               {"path": list(map(str, e.absolute_path))})
                return


def _run(cmd: list[str], cwd: Path, timeout=600) -> str:
    p = subprocess.run(cmd, cwd=str(cwd), capture_output=True, timeout=timeout)
    if p.returncode != 0:
        raise subprocess.CalledProcessError(p.returncode, cmd, p.stdout, p.stderr)
    return p.stdout.decode(errors="replace")


def _html_to_pdf(html_path: Path, pdf_path: Path, opts: dict | None = None) -> None:
    """HTML -> PDF with Playwright/Chromium (same call as the skills'
    html_to_pdf.py / render_pdf(): A3 landscape, 10 mm margins, background)."""
    from playwright.sync_api import sync_playwright
    o = {"format": "A3", "landscape": True, "margin": "10mm", **(opts or {})}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = browser.new_page()
        page.goto(f"file://{html_path.resolve()}", wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(2000)
        page.pdf(path=str(pdf_path), format=o["format"], landscape=bool(o["landscape"]),
                 print_background=True,
                 margin={k: o["margin"] for k in ("top", "bottom", "left", "right")})
        browser.close()


def _html_to_png(html_path: Path, png_path: Path, opts: dict | None = None) -> None:
    from playwright.sync_api import sync_playwright
    o = {"width": 1400, "height": 3000, "full_page": True, **(opts or {})}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = browser.new_page(viewport={"width": o["width"], "height": o["height"]})
        page.goto(f"file://{html_path.resolve()}", wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(2000)
        if o.get("clip"):
            page.screenshot(path=str(png_path), clip=o["clip"])
        else:
            page.screenshot(path=str(png_path), full_page=bool(o["full_page"]))
        browser.close()


def _collect(outdir: Path, primary_fmt: str, primary_name: str) -> tuple[dict, list[dict]]:
    files = []
    for f in sorted(p for p in outdir.rglob("*") if p.is_file()):
        ext = f.suffix.lstrip(".").lower()
        if ext in FORMATS:
            files.append({"fileName": f.name, "contentBase64": base64.b64encode(f.read_bytes()).decode(), "kind": ext})
    if not files:
        raise Http(500, "renderer produced no files")
    prim = next((x for x in files if x["kind"] == primary_fmt), files[0])
    prim = {**prim, "fileName": primary_name}
    return prim, files


def render_with(template: str, fmt: str, payload, out_name: str, td: Path,
                extra: dict | None = None) -> tuple[dict, list[dict], dict]:
    d = _renderer_dir(template)
    mf = _manifest(d)
    if mf.get("formats") and fmt not in mf["formats"]:
        raise Http(400, f"renderer {template} does not produce {fmt} (formats: {mf['formats']})")
    data = td / "data.json"
    data.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    outdir = td / "out"
    outdir.mkdir()
    out = outdir / out_name
    subs = {"{data}": str(data), "{out}": str(out), "{outdir}": str(outdir),
            "{renderer}": str(d), "{tmp}": str(td)}
    for k, v in (extra or {}).items():
        subs["{" + k + "}"] = str(v)
    argv = [re.sub(r"\{[a-z_]+\}", lambda m: subs.get(m.group(0), m.group(0)), a)
            for a in mf.get("argv", ["{data}", "{out}"])]
    runtime = mf.get("runtime", "python")
    exe = {"python": ["python3"], "node": ["node"], "bash": ["bash"]}[runtime]
    cwd = d / mf.get("cwd", ".")
    stdout = _run(exe + [str(d / mf["entry"])] + argv, cwd, timeout=int(mf.get("timeout", 600)))
    gate_info = {"passed": True, "checks": []}
    if mf.get("stdout_must_contain") and mf["stdout_must_contain"] not in stdout:
        raise Http(422, f"renderer QA gate failed (expected '{mf['stdout_must_contain']}' in output)",
                   {"stdout": stdout[-2000:]})
    prim, files = _collect(outdir, fmt, out_name)
    return prim, files, gate_info


@app.route(route="render", methods=["POST"])
@_guard
def render(req: func.HttpRequest) -> func.HttpResponse:
    body = req.get_json()
    fmt = str(body.get("format", "")).lower()
    if fmt not in FORMATS:
        raise Http(400, f"unsupported format {fmt}")
    template = body.get("template") or ""
    out_name = check_filename(body.get("fileName") or f"report.{fmt}", fmt)
    gate = {"passed": True, "checks": []}

    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        if fmt == "html" or (fmt in ("pdf", "png") and not template):
            html = _extract_payload(body.get("content") or body.get("data"), "html")
            if not isinstance(html, str) or "<html" not in html.lower():
                raise Http(400, "content must be a complete single-file HTML document")
            gate_key = body.get("gate") or template or ("deepsearch-html-dashboard" if "spiderChart" in html and 'id="corporate"' in html else "")
            if gate_key in gates.GATES and gates.GATES[gate_key][0] == "html":
                fails = gates.GATES[gate_key][1](html)
                gate = {"passed": not fails, "checks": fails, "gate": gate_key}
                if fails:
                    raise Http(422, "quality gate failed", {"gate": gate_key, "checks": fails})
            src = tdp / "report.html"
            src.write_text(html, encoding="utf-8")
            files = [{"fileName": "report.html", "contentBase64": base64.b64encode(html.encode("utf-8")).decode(), "kind": "html"}]
            if fmt == "html":
                prim = {**files[0], "fileName": out_name}
            elif fmt == "pdf":
                pdf = tdp / out_name
                _html_to_pdf(src, pdf, body.get("pdf"))
                prim = {"fileName": out_name, "contentBase64": base64.b64encode(pdf.read_bytes()).decode(), "kind": "pdf"}
                files.append(prim)
            else:
                png = tdp / out_name
                _html_to_png(src, png, body.get("png"))
                prim = {"fileName": out_name, "contentBase64": base64.b64encode(png.read_bytes()).decode(), "kind": "png"}
                files.append(prim)
        else:
            if not template:
                raise Http(400, f"template is required for format {fmt}")
            payload = _extract_payload(body.get("data"), fmt)
            _validate_schema(template, payload)
            if template in gates.GATES and gates.GATES[template][0] == "data":
                fails = gates.GATES[template][1](payload)
                if fails:
                    raise Http(422, "quality gate failed", {"gate": template, "checks": fails})
            extra = {}
            # optional binary input (e.g. the original OneTrust Form B export)
            if any(body.get(k) for k in ("inputContentBase64", "inputDriveId", "inputFileId")):
                data, name = _input_bytes(body, "input")
                inp = tdp / ("input" + Path(name).suffix.lower())
                inp.write_bytes(data)
                extra["input"] = inp
            prim, files, gate = render_with(template, fmt, payload, out_name, tdp, extra)
    return _json({"fileName": prim["fileName"], "contentBase64": prim["contentBase64"],
                  "files": files, "gate": gate, "template": template, "format": fmt})


# ----------------------------------------------------- public page fetch
_HTML_STRIP = re.compile(r"<(script|style|nav|header|footer|noscript)[^>]*>.*?</\1>", re.I | re.S)
_TAG = re.compile(r"<[^>]+>")
SEC_HEADERS = ("strict-transport-security", "content-security-policy", "x-frame-options",
               "x-content-type-options", "referrer-policy", "permissions-policy", "server",
               "x-powered-by", "cache-control", "set-cookie")
_rate: dict[str, float] = {}


def _rate_limit(key: str, per_seconds: float = 2.0) -> None:
    now = time.monotonic()
    if now - _rate.get(key, 0) < per_seconds:
        raise Http(429, "rate limited — one call per host every 2 s")
    _rate[key] = now


def _audit(kind: str, **kw) -> None:
    log.info(json.dumps({"audit": kind, "at": datetime.now(timezone.utc).isoformat(), **kw}))


def html_to_text(html: str) -> tuple[str, str]:
    title = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
    body = _HTML_STRIP.sub(" ", html)
    body = re.sub(r"<br\s*/?>|</p>|</div>|</li>|</h[1-6]>|</tr>", "\n", body, flags=re.I)
    text = _TAG.sub(" ", body)
    import html as _h
    text = _h.unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n", text).strip()
    return (title.group(1).strip() if title else ""), text


@app.route(route="allowlist", methods=["GET"])
@_guard
def get_allowlist(req: func.HttpRequest) -> func.HttpResponse:
    return _json(urlpolicy.allowlist())


@app.route(route="fetch_public_page", methods=["GET"])
@_guard
def fetch_public_page(req: func.HttpRequest) -> func.HttpResponse:
    url = req.params.get("url", "")
    supplier = req.params.get("supplierDomain") or None
    mode = req.params.get("mode", "text")
    max_bytes = min(int(req.params.get("maxBytes", 1048576)), 4194304)
    ok, why = urlpolicy.check_url(url, supplier)
    if not ok:
        _audit("fetch_public_page.refused", url=url[:300], reason=why)
        raise Http(403, why)
    host = urlsplit(url).hostname
    _rate_limit(host)
    sess = requests.Session()
    sess.max_redirects = 5
    headers = {"User-Agent": "ENX-OSINT-proxy/1.0 (+read-only assessment)", "Accept": "text/html,application/xhtml+xml,text/plain,application/pdf;q=0.5"}
    try:
        if mode == "head":
            r = sess.head(url, headers=headers, timeout=20, allow_redirects=True)
        else:
            r = sess.get(url, headers=headers, timeout=30, allow_redirects=True, stream=True)
    except requests.RequestException as e:
        _audit("fetch_public_page.error", url=url[:300], error=str(e)[:200])
        raise Http(422, f"page not retrievable: {e.__class__.__name__}")
    # every hop must stay inside the policy
    for hop in list(r.history) + [r]:
        ok, why = urlpolicy.check_url(hop.url, supplier, resolve=False)
        if not ok:
            raise Http(403, f"redirect left the allow-list: {why}")
    out = {"finalUrl": r.url, "status": r.status_code,
           "headers": {k: v for k, v in r.headers.items() if k.lower() in SEC_HEADERS},
           "retrievedAt": datetime.now(timezone.utc).isoformat(), "truncated": False}
    if mode in ("head", "headers"):
        r.close()
        _audit("fetch_public_page", url=url[:300], mode=mode, status=r.status_code, bytes=0)
        return _json(out)
    ctype = r.headers.get("Content-Type", "")
    buf = io.BytesIO()
    for chunk in r.iter_content(65536):
        buf.write(chunk)
        if buf.tell() >= max_bytes:
            out["truncated"] = True
            break
    r.close()
    raw = buf.getvalue()
    if "html" in ctype or raw[:200].lower().lstrip().startswith((b"<!doctype", b"<html")):
        out["title"], out["text"] = html_to_text(raw.decode(r.encoding or "utf-8", errors="replace"))
    elif "text/" in ctype or "json" in ctype or "xml" in ctype:
        out["title"], out["text"] = "", raw.decode(r.encoding or "utf-8", errors="replace")
    elif "pdf" in ctype:
        from pypdf import PdfReader
        rd = PdfReader(io.BytesIO(raw))
        out["title"] = (rd.metadata or {}).get("/Title", "") or ""
        out["text"] = "\n".join((p.extract_text() or "") for p in rd.pages[:50])
    else:
        raise Http(422, f"unsupported content type {ctype}")
    if urlpolicy.INTERNAL_MARKER.search(out["text"][:200000]):
        out["dlpNote"] = "internal-marker pattern seen in the PUBLIC page text (reported, not redacted)"
    _audit("fetch_public_page", url=url[:300], mode=mode, status=r.status_code, bytes=len(raw))
    return _json(out)


# ---------------------------------------------------------- passive recon
@app.route(route="passive_recon", methods=["GET"])
@_guard
def passive_recon(req: func.HttpRequest) -> func.HttpResponse:
    """Strictly passive technical fingerprint of a PUBLIC supplier domain —
    replaces the DeepSearch bash recon (curl -sIL, openssl s_client, dig).
    No scanning, no crawling, one TLS handshake + one HTTPS GET + DNS lookups.
    ActiveScanningAllowed is always No on this platform."""
    domain = (req.params.get("domain") or "").strip().lower()
    ok, why = urlpolicy.check_host(domain, supplier_domain=domain)
    if not ok:
        raise Http(403, why)
    _rate_limit("recon:" + domain, 60.0)
    out: dict = {"domain": domain, "retrievedAt": datetime.now(timezone.utc).isoformat(), "passive": True}
    # DNS
    dns_out: dict = {}
    try:
        dns_out["A"] = sorted({i[4][0] for i in socket.getaddrinfo(domain, 443, socket.AF_INET)})
    except socket.gaierror:
        dns_out["A"] = []
    try:
        dns_out["AAAA"] = sorted({i[4][0] for i in socket.getaddrinfo(domain, 443, socket.AF_INET6)})
    except socket.gaierror:
        dns_out["AAAA"] = []
    try:
        import dns.resolver
        for rr in ("MX", "NS", "TXT", "CAA"):
            try:
                dns_out[rr] = [r.to_text() for r in dns.resolver.resolve(domain, rr, lifetime=5)]
            except Exception:
                dns_out[rr] = []
        spf = [t for t in dns_out.get("TXT", []) if "v=spf1" in t]
        dns_out["SPF"] = spf
        try:
            dns_out["DMARC"] = [r.to_text() for r in dns.resolver.resolve("_dmarc." + domain, "TXT", lifetime=5)]
        except Exception:
            dns_out["DMARC"] = []
    except ImportError:
        dns_out["note"] = "dnspython not installed — A/AAAA only"
    out["dns"] = dns_out
    # TLS certificate
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=10) as s, ctx.wrap_socket(s, server_hostname=domain) as ts:
            cert = ts.getpeercert()
            out["tls"] = {"protocol": ts.version(), "cipher": ts.cipher()[0],
                          "subject": dict(x[0] for x in cert.get("subject", ())),
                          "issuer": dict(x[0] for x in cert.get("issuer", ())),
                          "notBefore": cert.get("notBefore"), "notAfter": cert.get("notAfter"),
                          "san": [v for k, v in cert.get("subjectAltName", ()) if k == "DNS"][:50]}
    except (OSError, ssl.SSLError) as e:
        out["tls"] = {"error": e.__class__.__name__}
    # HTTP response headers (one GET, no body kept)
    try:
        r = requests.get(f"https://{domain}/", timeout=20, allow_redirects=True, stream=True,
                         headers={"User-Agent": "ENX-OSINT-proxy/1.0 (+passive)"})
        hdrs = {k.lower(): v for k, v in r.headers.items()}
        r.close()
        out["http"] = {"finalUrl": r.url, "status": r.status_code,
                       "securityHeaders": {h: hdrs.get(h) for h in SEC_HEADERS if h != "set-cookie"},
                       "hsts": "strict-transport-security" in hdrs, "csp": "content-security-policy" in hdrs,
                       "redirects": [h.url for h in r.history]}
        srv = (hdrs.get("server", "") + " " + hdrs.get("x-powered-by", "") + " " + hdrs.get("via", "")).lower()
        cdn = [n for n in ("cloudflare", "akamai", "fastly", "cloudfront", "azure", "imperva", "incapsula", "sucuri", "f5") if n in srv or n in json.dumps(hdrs).lower()]
        out["http"]["cdnWafIndicators"] = cdn
        out["http"]["cmsIndicators"] = [n for n in ("wordpress", "drupal", "sitecore", "aem", "hubspot", "webflow") if n in json.dumps(hdrs).lower()]
    except requests.RequestException as e:
        out["http"] = {"error": e.__class__.__name__}
    if os.environ.get("ENABLE_SECURITYHEADERS_GRADE") == "1":
        try:
            r = requests.get("https://securityheaders.com/", params={"q": domain, "followRedirects": "on"}, timeout=20,
                             headers={"User-Agent": "ENX-OSINT-proxy/1.0"})
            m = re.search(r'class="score[^"]*"[^>]*>\s*<span>([A-F][+-]?)', r.text) or re.search(r"Grade:\s*([A-F][+-]?)", r.text)
            out["securityHeadersGrade"] = m.group(1) if m else None
        except requests.RequestException:
            out["securityHeadersGrade"] = None
    _audit("passive_recon", domain=domain)
    return _json(out)


# ------------------------------------------------------------ pdf-coverage
PDF_STAGES = {"triage": "triage.py", "inventory": "inventory.py", "chunk": "chunk_extract.py",
              "verify": "verify_coverage.py", "cross_check": "cross_check.py"}


@app.route(route="pdf/{stage}", methods=["POST"])
@_guard
def pdf_coverage(req: func.HttpRequest) -> func.HttpResponse:
    """Runs the byte-verified pdf-full-coverage-analyzer scripts (poppler,
    tesseract, PyMuPDF, pdfplumber are in this container) on a SharePoint
    item / Foundry file / inline bytes. Non-mutating compute: registered as a
    'compute_connections' OpenAPI tool (integrations/openapi/pdf-coverage.yaml)."""
    stage = req.route_params.get("stage", "")
    if stage not in PDF_STAGES:
        raise Http(404, f"unknown stage {stage}; one of {sorted(PDF_STAGES)}")
    b = req.get_json()
    d = _renderer_dir("pdf-coverage")
    scripts = d / "scripts"
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        pdf = tdp / "input.pdf"
        data, _ = _input_bytes(b)
        pdf.write_bytes(data)
        opts = b.get("options") or {}
        if stage in ("triage", "inventory"):
            argv = [str(pdf), "--out", str(tdp / "out.json")]
            if stage == "inventory" and opts.get("ocrPages"):
                argv += ["--ocr-pages", str(opts["ocrPages"])]
            _run(["python3", str(scripts / PDF_STAGES[stage])] + argv, tdp, timeout=900)
            return _json(json.loads((tdp / "out.json").read_text(encoding="utf-8")))
        if stage == "chunk":
            cdir = tdp / "chunks"
            argv = [str(pdf), "--output-dir", str(cdir), "--chunk-size", str(opts.get("chunkSize", 10))]
            if opts.get("ocr"):
                argv.append("--ocr")
            if opts.get("ocrPages"):
                argv += ["--ocr-pages", str(opts["ocrPages"])]
            log_ = _run(["python3", str(scripts / PDF_STAGES[stage])] + argv, tdp, timeout=1800)
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
                for f in sorted(cdir.rglob("*")):
                    if f.is_file():
                        zf.write(f, f.relative_to(cdir).as_posix())
            out = {"chunks": sorted(f.name for f in cdir.iterdir()), "log": log_[-4000:],
                   "chunksZipBase64": base64.b64encode(buf.getvalue()).decode()}
            if b.get("attachToProject"):
                out["fileId"] = _foundry_upload(buf.getvalue(), "chunks.zip")
            return _json(out)
        # verify / cross_check need the chunks produced earlier
        cdir = tdp / "chunks"
        cdir.mkdir()
        if not b.get("chunksZipBase64"):
            raise Http(400, "chunksZipBase64 (from /api/pdf/chunk) is required")
        with zipfile.ZipFile(io.BytesIO(base64.b64decode(b["chunksZipBase64"]))) as zf:
            zf.extractall(cdir)
        if stage == "verify":
            inv = tdp / "inventory.json"
            inv.write_text(json.dumps(b.get("inventory") or {}), encoding="utf-8")
            _run(["python3", str(scripts / PDF_STAGES[stage]), "--inventory", str(inv), "--chunks", str(cdir),
                  "--out", str(tdp / "out.json")], tdp, timeout=900)
        else:
            _run(["python3", str(scripts / PDF_STAGES[stage]), "--pdf", str(pdf), "--chunks", str(cdir),
                  "--pages", str(opts.get("pages", "all")), "--out", str(tdp / "out.json")], tdp, timeout=1800)
        return _json(json.loads((tdp / "out.json").read_text(encoding="utf-8")))


# ------------------------------------------------------------ speaker clips
@app.route(route="speaker_clips", methods=["POST"])
@_guard
def speaker_clips(req: func.HttpRequest) -> func.HttpResponse:
    """Per-speaker audio clips (whisperx-transcribe-diarize
    scripts/extract_speaker_clips.py, ffmpeg in this container). Audio stays
    in-tenant: input is a SharePoint item / Foundry file / inline bytes."""
    b = req.get_json()
    d = _renderer_dir("whisperx")
    script = d / "scripts" / "extract_speaker_clips.py"
    if not script.exists():
        raise Http(501, "extract_speaker_clips.py not staged")
    fmt = b.get("format", "m4a")
    if fmt not in ("m4a", "mp3", "wav"):
        raise Http(400, "format must be m4a|mp3|wav")
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        audio, name = _input_bytes(b, "audio")
        ap = tdp / ("audio" + (Path(name).suffix.lower() or ".wav"))
        ap.write_bytes(audio)
        tr = tdp / "transcript.json"
        tr.write_text(json.dumps(b["transcript"]), encoding="utf-8")
        outd = tdp / "clips"
        _run(["python3", str(script), "--input", str(tr), "--audio", str(ap), "--output-dir", str(outd),
              "--format", fmt], tdp, timeout=1800)
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            for f in sorted(outd.rglob("*")):
                if f.is_file():
                    zf.write(f, f.relative_to(outd).as_posix())
    return _json({"fileName": "speaker_clips.zip", "contentBase64": base64.b64encode(buf.getvalue()).decode()})


# ------------------------------------------------------------------ health
@app.route(route="health", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def health(req: func.HttpRequest) -> func.HttpResponse:
    staged = sorted(p.name for p in RENDERERS.iterdir() if p.is_dir()) if RENDERERS.exists() else []
    tools = {t: bool(shutil.which(t)) for t in ("node", "pdftotext", "pdftoppm", "tesseract", "ffmpeg")}
    try:
        import playwright  # noqa: F401
        tools["playwright"] = True
    except ImportError:
        tools["playwright"] = False
    return _json({"status": "ok", "renderers": staged, "tools": tools,
                  "dataBoundary": os.environ.get("ENX_DATA_BOUNDARY", "EU")})
