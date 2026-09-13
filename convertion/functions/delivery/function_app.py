"""Delivery Function App — SharePoint storage, report rendering and the
governed compute endpoints the converted skills need but Foundry's
code_interpreter cannot provide (no network, no Node, no Chromium).

Called by the Logic App pipelines in ../../workflows/ and (compute routes
only) by agents through the OpenAPI connections in
../../integrations/openapi/ (osint-proxy, passive-recon). The PDF-coverage
surface below is POST-only and therefore NOT agent-attachable — see its route.
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
  GET  /api/evidence_cache?driveId=&itemId=&eTag=&extractorRef=
  POST /api/evidence_cache   {files:[{driveId,itemId,eTag,facts}], extractorRef, runId}
      Delta re-analysis for requirement d2. A supplier's TPA/Active tree
      barely changes between assessments, but every reassessment used to
      re-read every file on the reasoning tier. The GET (a read-only agent
      tool) returns the FACTS extracted from a file whose Graph eTag is
      unchanged; the POST records them, from the pipeline, after approval. Time-dependent STATUS (VALID / EXPIRING /
      EXPIRED) is never cached — it is recomputed at each report date.
  GET  /api/research_ledger?supplier=&service=&sourceId=&query=&topic=&maxAgeDays=
  POST /api/research_ledger  {supplier, service?, records:[...], runId, originatingAction}
      The supplier research ledger: every web search and authority lookup,
      what it returned, WHEN, and which action asked for it. The GET is a
      read-only agent tool answered before searching again — a fresh
      observation is reused and cited as such; a stale one is re-fetched.
      The POST is the pipeline's post-approval write, and it also refreshes
      the human-readable knowledge file
      Reports/<Supplier>/_Knowledge/research-ledger.md.

  POST /api/extract_pdf      {model?: prebuilt-read|prebuilt-layout, pages?,
                              contentBase64|driveId+itemId|fileId, attachToProject?}
      -> {content, pages, tables, confidence: {mean, min}, source}
         Azure AI Document Intelligence (EU) — the OCR path for scanned or
         garbled evidence; pure-Python and office-tools come first
         (agents/knowledge-packs/pdf-reading-foundry.md §4).
  GET  /api/fetch_public_page?url=&supplierDomain=&mode=&maxBytes=   (osint-proxy.yaml)
  GET  /api/allowlist
  GET  /api/passive_recon?domain=                                     (passive-recon.yaml)
  POST /api/pdf/{stage}      stage: triage|inventory|chunk|verify|cross_check
                             (pipeline-invoked only — POST, so not an agent tool)
  POST /api/speaker_clips    {transcript, audioBase64|driveId+itemId, format} -> zip
  GET  /api/health

Rendering executes the byte-verified generators staged by
../../scripts/stage_renderers.py into renderers/<template>/ (manifest.json
per renderer, see renderers-src/README.md) so outputs match claude.ai.

The LibreOffice/pandoc toolchain lives in the SEPARATE office-tools Function
App (../office-tools): this app calls it over `OFFICE_TOOLS_BASE_URL` with
`OFFICE_TOOLS_KEY` for the mandatory xlsx recalc gate, and never runs soffice
itself — see ../office-tools/README.md §"Trust boundary" and the Dockerfile
header here for the image split.
"""

from __future__ import annotations

import base64
import hashlib
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
from datetime import datetime, timedelta, timezone
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
EVIDENCE_CACHE_LIST = os.environ.get("EVIDENCE_CACHE_LIST_NAME",
                                     "TPA Evidence Cache")
# A cached extraction is trusted for this long even if the file never
# changes: evidence that nobody has re-read in six months is re-read, so a
# silent mis-extraction cannot live in the register forever.
EVIDENCE_CACHE_MAX_AGE_DAYS = int(os.environ.get("EVIDENCE_CACHE_MAX_AGE_DAYS", "180"))
RESEARCH_LEDGER_LIST = os.environ.get("RESEARCH_LEDGER_LIST_NAME",
                                      "Supplier Research Ledger")
# How long an observation may be REUSED instead of re-fetched, per source
# family. These are reuse windows, not truth windows: a fact whose value is
# time-dependent (a validity status, "is it in force", an exploitation flag)
# is recomputed every time regardless (see the knowledge pack). Overridable
# per deployment with RESEARCH_TTL_OVERRIDES="nvd-cve=3,web-search=5".
RESEARCH_TTL_DAYS = {
    "eur-lex": 90,          # the text of an act does not move; a consolidation might
    "iso": 180, "nist": 180, "cis": 180, "aicpa": 180, "iaasb": 180,
    "esas": 30, "edpb": 30, "enisa": 30, "ec-europa": 30,
    "eu-lex-national": 30, "company-registries": 90,
    "iaf-certsearch": 30,   # a certificate can be withdrawn
    "nvd-cve": 7, "cve-org": 7, "mitre-attack": 90,
    "cisa-kev": 1, "first-epss": 1,   # both move daily
    "vendor-advisories": 1, "transparency": 14,
    "securityscorecard": 7, "ssl-observatories": 14,
    "web-search": 7, "osint-proxy": 14, "passive-recon": 14,
}
RESEARCH_TTL_DEFAULT = int(os.environ.get("RESEARCH_TTL_DEFAULT_DAYS", "14"))
# Nothing is reused past this, whatever its source says.
RESEARCH_LEDGER_MAX_AGE_DAYS = int(
    os.environ.get("RESEARCH_LEDGER_MAX_AGE_DAYS", "365"))
for _pair in os.environ.get("RESEARCH_TTL_OVERRIDES", "").split(","):
    if "=" in _pair:
        _k, _, _v = _pair.partition("=")
        try:
            RESEARCH_TTL_DAYS[_k.strip()] = int(_v)
        except ValueError:
            pass

PROJECT_ENDPOINT = os.environ.get("PROJECT_ENDPOINT", "").rstrip("/")
FOUNDRY_API_VERSION = os.environ.get("FOUNDRY_API_VERSION", "2025-05-15-preview")

# Azure AI Document Intelligence (OCR of scanned evidence). Reached ONLY from
# this app with its managed identity — main.bicep sets disableLocalAuth, so no
# key exists to leak. Empty endpoint = enableDocumentIntelligence=false.
DOCINTEL_ENDPOINT = os.environ.get("DOCINTEL_ENDPOINT", "").rstrip("/")
DOCINTEL_API_VERSION = os.environ.get("DOCINTEL_API_VERSION", "2024-11-30")  # v4.0 GA
DOCINTEL_MODELS = ("prebuilt-read", "prebuilt-layout")
DOCINTEL_MAX_CHARS = int(os.environ.get("DOCINTEL_MAX_CHARS", "400000"))


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


# ------------------------------------------------------- request contracts
# Bodies of the file-handling routes are jsonschema-validated before any byte
# is fetched or written, so a malformed payload is a deterministic 400 naming
# the offending field instead of a KeyError deep inside a Graph call. (The
# RENDER payload has its own per-template schema gate: _validate_schema.)
_FILE_SOURCE = {
    "contentBase64": {"type": "string", "minLength": 4},
    "fileName": {"type": "string", "minLength": 1, "maxLength": 180},
    "driveId": {"type": "string", "minLength": 1, "maxLength": 300},
    "itemId": {"type": "string", "minLength": 1, "maxLength": 300},
    "fileId": {"type": "string", "minLength": 1, "maxLength": 300},
}
REQUEST_SCHEMAS: dict[str, dict] = {
    "fetch_evidence": {
        "type": "object",
        "required": ["driveId", "itemId"],
        "properties": {"driveId": _FILE_SOURCE["driveId"], "itemId": _FILE_SOURCE["itemId"]},
    },
    "evidence_cache": {
        "type": "object",
        "required": ["files"],
        "properties": {
            "extractorRef": {"type": "string", "maxLength": 200},
            "runId": {"type": "string", "maxLength": 200},
            "files": {
                "type": "array",
                "maxItems": 500,
                "items": {
                    "type": "object",
                    "required": ["driveId", "itemId", "eTag"],
                    "properties": {
                        "driveId": {"type": "string", "maxLength": 300},
                        "itemId": {"type": "string", "maxLength": 300},
                        "eTag": {"type": "string", "maxLength": 300},
                        "fileName": {"type": "string", "maxLength": 400},
                        "facts": {"type": "object"},
                    },
                },
            },
        },
    },
    "extract_pdf": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            **_FILE_SOURCE,
            "model": {"type": "string", "enum": list(DOCINTEL_MODELS)},
            "pages": {"type": "string", "pattern": r"^\d{1,5}(-\d{1,5})?(,\d{1,5}(-\d{1,5})?)*$"},
            "outputContentFormat": {"type": "string", "enum": ["text", "markdown"]},
            "attachToProject": {"type": "boolean"},
        },
        "anyOf": [
            {"required": ["contentBase64"]},
            {"required": ["driveId", "itemId"]},
            {"required": ["fileId"]},
        ],
    },
}


def _body(req: func.HttpRequest, contract: str) -> dict:
    """Parse + jsonschema-validate a request body. Fails closed: no
    jsonschema in the image, or an invalid payload, is never a silent pass."""
    raw = req.get_body() or b""
    if not raw.strip():
        raise Http(400, f"empty body; {contract} expects a JSON object")
    try:
        b = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise Http(400, f"body is not valid UTF-8 JSON: {e}")
    if not isinstance(b, dict):
        raise Http(400, "body must be a JSON object")
    try:
        import jsonschema
    except ImportError:
        raise Http(500, "jsonschema is not installed in this image")
    try:
        jsonschema.validate(b, REQUEST_SCHEMAS[contract])
    except jsonschema.ValidationError as e:
        raise Http(400, f"invalid {contract} payload: {e.message}",
                   {"path": list(map(str, e.absolute_path)) or ["<root>"]})
    return b


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


# ------------------------------------------------- evidence cache (req. d2)
# Why this exists: the TPA evidence analysis is the heaviest recurring run in
# the platform — a whole supplier tree read on the reasoning tier with the
# chunked full-coverage method. Between two assessments almost none of those
# files change, yet every one of them used to be re-read in full.
#
# What is cached: the FACTS a reader cannot recompute — document type, issuer,
# content identification, scope statement, emission date, validity window,
# findings. What is NEVER cached: anything time-dependent. VALID / EXPIRING
# <=90 days / EXPIRED / period-gap are recomputed against the report date on
# every run, because a certificate that was VALID in March is not valid in
# September and a cached status would quietly assert that it is.
#
# Invalidation, three ways, all of them cheap:
#   1. the Graph eTag changed          -> the file was edited or replaced
#   2. the extractor ref changed       -> a new agent version reads differently
#   3. the entry is older than the cap -> nothing is trusted indefinitely
def _cache_key(drive_id: str, item_id: str) -> str:
    return f"{drive_id}|{item_id}"


def _evidence_cache_lookup(drive_id: str, item_id: str, etag: str,
                           extractor_ref: str) -> dict:
    """One file. Returns {hit, facts?, reason} — never raises on a miss: a
    cache that fails closed would make the analyzer read everything, which is
    exactly the behaviour this endpoint exists to avoid being forced into."""
    if not SITE_ID:
        raise Http(503, "SHAREPOINT_SITE_ID not configured")
    key = _cache_key(drive_id, item_id)
    r = _graph("GET", f"{GRAPH}/sites/{SITE_ID}/lists/{EVIDENCE_CACHE_LIST}/items",
               params={"$expand": "fields",
                       "$filter": f"fields/CacheKey eq '{key.replace(chr(39), chr(39) * 2)}'"},
               headers={"Prefer": "HonorNonIndexedQueriesWarningMayFailRandomly"})
    row = (r.json().get("value") or [None])[0] if r.status_code == 200 else None
    if not row:
        return {"hit": False, "reason": "not-cached"}
    fields = row.get("fields", {})
    if fields.get("ETag") != etag:
        return {"hit": False, "reason": "etag-changed"}
    if extractor_ref and fields.get("ExtractorRef") != extractor_ref:
        return {"hit": False, "reason": "extractor-changed"}
    try:
        stored_at = datetime.fromisoformat(
            fields.get("StoredAt", "").replace("Z", "+00:00"))
    except ValueError:
        return {"hit": False, "reason": "unreadable"}
    age_days = (datetime.now(timezone.utc) - stored_at).days
    if age_days > EVIDENCE_CACHE_MAX_AGE_DAYS:
        return {"hit": False, "reason": "expired", "ageDays": age_days}
    try:
        facts = json.loads(fields.get("Facts") or "{}")
    except json.JSONDecodeError:
        return {"hit": False, "reason": "unreadable"}
    return {"hit": True, "facts": facts, "fileName": fields.get("FileName", ""),
            "storedAt": fields.get("StoredAt"), "ageDays": age_days,
            "sourceRunId": fields.get("RunId", ""),
            "extractorRef": fields.get("ExtractorRef", "")}


def _evidence_cache_store(files: list[dict], extractor_ref: str,
                          run_id: str) -> dict:
    """Record the facts of a run that PASSED the verifier and was approved.
    Called from the pipeline's post-approval branch only — an unapproved
    extraction never enters the cache, so reuse can never launder a draft."""
    now = datetime.now(timezone.utc).isoformat()
    stored = 0
    for f in files:
        if not f.get("facts"):
            continue                      # nothing extracted: nothing to reuse
        _list_upsert(EVIDENCE_CACHE_LIST,
                     {"CacheKey": _cache_key(f["driveId"], f["itemId"])},
                     {"DriveId": f["driveId"], "ItemId": f["itemId"],
                      "ETag": f["eTag"], "FileName": f.get("fileName", ""),
                      "Facts": json.dumps(f["facts"], ensure_ascii=False),
                      "ExtractorRef": extractor_ref, "RunId": run_id,
                      "StoredAt": now})
        stored += 1
    return {"stored": stored, "storedAt": now}


@app.route(route="evidence_cache", methods=["GET"])
@_guard
def evidence_cache_lookup(req: func.HttpRequest) -> func.HttpResponse:
    """READ-ONLY agent tool (evidence-cache.yaml). GET keeps it inside the
    read-only rule that attach_integrations.py enforces: an agent may ask what
    was already extracted, and can never write to the cache."""
    q = req.params
    missing = [k for k in ("driveId", "itemId", "eTag") if not q.get(k)]
    if missing:
        raise Http(400, f"missing query parameter(s): {', '.join(missing)}")
    return _json(_evidence_cache_lookup(q["driveId"], q["itemId"], q["eTag"],
                                        q.get("extractorRef", "")))


@app.route(route="evidence_cache", methods=["POST"])
@_guard
def evidence_cache_store(req: func.HttpRequest) -> func.HttpResponse:
    b = _body(req, "evidence_cache")
    return _json(_evidence_cache_store(b.get("files") or [],
                                       b.get("extractorRef", ""),
                                       b.get("runId", "")))


# ------------------------------------------------- supplier research ledger
#
# Requirement: every search — web, authority API or platform tool — and what
# it returned is kept in the supplier's own knowledge file, with the date and
# the action that caused it, so the next run reads instead of re-searching.
#
# Two representations of the same records, written by this Function (the only
# writer identity on the platform):
#   * a SharePoint list, for lookup (what the agent's GET queries);
#   * Reports/<Supplier>/_Knowledge/research-ledger.md, for people — the
#     "knowledge file" a reviewer opens to see what is known about a supplier
#     and where each fact came from.
#
# What may be stored is exactly what was already allowed to leave: a public
# query, a public URL, a public result. The same outbound DLP that guards the
# fetch guards the ledger (_ledger_clean), so an internal marker cannot enter
# it by way of a note field and be re-read later as if it were public.

def _research_key(supplier: str, service: str, source_id: str,
                  query: str) -> str:
    """Stable identity of an observation: same supplier, same service, same
    source, same question. A re-run overwrites rather than appends, so the
    ledger records the LATEST answer per question and does not grow without
    bound."""
    norm = " ".join((query or "").lower().split())
    raw = "|".join([normalise(supplier).lower(), normalise(service or "").lower(),
                    (source_id or "").lower(), norm])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:40]


def _ledger_clean(value: str, limit: int = 2000) -> tuple[str, bool]:
    """(text, redacted). Refuse to persist an internal marker: the ledger is
    re-read by later runs and would otherwise launder an identifier that the
    egress rule kept out of the query in the first place."""
    text = (value or "").strip()[:limit]
    if urlpolicy.INTERNAL_MARKER.search(text):
        return "[redacted: internal marker — the record was stored without it]", True
    return text, False


def _ttl_days(source_id: str) -> int:
    return RESEARCH_TTL_DAYS.get((source_id or "").lower(), RESEARCH_TTL_DEFAULT)


def _ledger_lookup(supplier: str, service: str, source_id: str, query: str,
                   topic: str, max_age_days: int | None) -> dict:
    """Answer 'do we already know this?'. Never raises on a miss — a ledger
    that fails closed would send the agent back to the web, which is the cost
    this endpoint exists to avoid."""
    if not SITE_ID:
        raise Http(503, "SHAREPOINT_SITE_ID not configured")
    flt = [f"fields/Supplier eq '{normalise(supplier).replace(chr(39), chr(39) * 2)}'"]
    if service:
        flt.append(f"fields/Service eq '{normalise(service).replace(chr(39), chr(39) * 2)}'")
    if source_id:
        flt.append(f"fields/SourceId eq '{source_id.replace(chr(39), chr(39) * 2)}'")
    if query:
        flt.append(f"fields/RecordKey eq '{_research_key(supplier, service, source_id, query)}'")
    r = _graph("GET", f"{GRAPH}/sites/{SITE_ID}/lists/{RESEARCH_LEDGER_LIST}/items",
               params={"$expand": "fields", "$filter": " and ".join(flt),
                       "$top": "100", "$orderby": "fields/ObservedAt desc"},
               headers={"Prefer": "HonorNonIndexedQueriesWarningMayFailRandomly"})
    if r.status_code != 200:
        return {"hit": False, "reason": "ledger-unavailable", "records": []}
    now = datetime.now(timezone.utc)
    topic_l = (topic or "").lower()
    out: list[dict] = []
    for row in r.json().get("value", []):
        f = row.get("fields", {})
        if topic_l and topic_l not in (f.get("Topic", "") + " " +
                                       f.get("Query", "")).lower():
            continue
        try:
            observed = datetime.fromisoformat(
                (f.get("ObservedAt") or "").replace("Z", "+00:00"))
        except ValueError:
            continue
        age = (now - observed).days
        if age > RESEARCH_LEDGER_MAX_AGE_DAYS:
            continue
        ttl = _ttl_days(f.get("SourceId", ""))
        try:
            facts = json.loads(f.get("Facts") or "{}")
        except json.JSONDecodeError:
            facts = {}
        out.append({
            "recordKey": f.get("RecordKey", ""),
            "supplier": f.get("Supplier", ""), "service": f.get("Service", ""),
            "sourceId": f.get("SourceId", ""), "tool": f.get("Tool", ""),
            "tier": f.get("Tier"), "query": f.get("Query", ""),
            "topic": f.get("Topic", ""), "url": f.get("Url", ""),
            "title": f.get("Title", ""), "citation": f.get("Citation", ""),
            "facts": facts, "observedAt": f.get("ObservedAt"),
            "ageDays": age, "ttlDays": ttl,
            "fresh": age <= (max_age_days if max_age_days is not None else ttl),
            "originatingAction": f.get("OriginatingAction", ""),
            "runId": f.get("RunId", ""),
        })
    fresh = [o for o in out if o["fresh"]]
    return {"hit": bool(fresh), "records": out, "freshCount": len(fresh),
            "staleCount": len(out) - len(fresh),
            "reason": "" if fresh else ("only-stale" if out else "not-recorded")}


def _ledger_markdown(supplier: str, records: list[dict]) -> str:
    """The supplier's knowledge file, rebuilt from the ledger rows. Plain
    Markdown on purpose: a reviewer, an auditor and the next analyst all read
    it without a renderer, and every line carries its date and its cause."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [f"# {supplier} — research knowledge file", "",
             f"Every search and authority lookup this platform made about "
             f"{supplier}, what it returned, when, and which action asked for "
             f"it. Regenerated {now} by the delivery Function; do not edit by "
             f"hand — records come from the runs themselves.", "",
             "Reuse rule: a record inside its freshness window is quoted with "
             "its observation date instead of being searched again; anything "
             "older is re-fetched. A time-dependent status (certificate "
             "validity, in-force, exploited-in-the-wild) is always recomputed, "
             "never reused.", "",
             "| Observed | Service | Source | Question / query | Result | "
             "Citation | Originating action | Run |",
             "|---|---|---|---|---|---|---|---|"]
    for rec in sorted(records, key=lambda r: r.get("observedAt", ""),
                      reverse=True):
        facts = rec.get("facts") or {}
        esc = lambda t: (t or "").replace("|", "\\|").replace("\n", " ")
        summary = esc(facts.get("summary") or rec.get("title") or "")
        lines.append(
            f"| {(rec.get('observedAt') or '')[:10]} | {rec.get('service') or '—'} "
            f"| {rec.get('sourceId') or rec.get('tool') or '—'} "
            f"| {esc(rec.get('query'))[:120]} "
            f"| {summary[:200]} | {esc(rec.get('citation'))[:160]} "
            f"| {rec.get('originatingAction') or '—'} | {rec.get('runId') or '—'} |")
    lines += ["", f"{len(records)} record(s). Source registry: "
                  "integrations/knowledge-sources.json. Citation discipline: "
                  "agents/knowledge-packs/authoritative-sources.md."]
    return "\n".join(lines) + "\n"


def _ledger_write_file(drive_id: str, reports_root: str, supplier: str,
                       records: list[dict]) -> dict:
    """Refresh Reports/<Supplier>/_Knowledge/research-ledger.md."""
    folder = ensure_path(drive_id, reports_root, [supplier, "_Knowledge"])
    body = _ledger_markdown(supplier, records).encode("utf-8")
    r = _graph("PUT",
               f"{GRAPH}/drives/{drive_id}/items/{folder}:/research-ledger.md:/content",
               data=body, headers={"Content-Type": "text/markdown"})
    r.raise_for_status()
    item = r.json()
    return {"itemId": item.get("id"), "webUrl": item.get("webUrl"),
            "bytes": len(body)}


def _ledger_store(supplier: str, service: str, records: list[dict],
                  run_id: str, originating_action: str,
                  drive_id: str = "", reports_root: str = "") -> dict:
    """Record what a run learned. Called from the pipeline after the verifier
    passed and a person approved — the same discipline as the evidence cache,
    so nothing a human rejected can be reused later as if it were established.
    The Function's own fetch endpoints record their observations directly
    (they never produce a deliverable to approve)."""
    if not supplier:
        raise Http(400, "supplier is required — the ledger is per supplier")
    now = datetime.now(timezone.utc).isoformat()
    stored, redacted = 0, 0
    for rec in records:
        source_id = (rec.get("sourceId") or rec.get("tool") or "").strip()
        query, q_red = _ledger_clean(rec.get("query") or rec.get("topic") or "")
        if not source_id or not query:
            continue
        facts = rec.get("facts") or {}
        facts_text, f_red = _ledger_clean(
            json.dumps(facts, ensure_ascii=False), 8000)
        citation, c_red = _ledger_clean(rec.get("citation") or "", 400)
        url, u_red = _ledger_clean(rec.get("url") or "", 500)
        if any((q_red, f_red, c_red, u_red)):
            redacted += 1
        _list_upsert(RESEARCH_LEDGER_LIST,
                     {"RecordKey": _research_key(supplier, service, source_id,
                                                 query)},
                     {"Supplier": normalise(supplier),
                      "Service": normalise(service or ""),
                      "SourceId": source_id,
                      "Tool": (rec.get("tool") or source_id)[:100],
                      "Tier": str(rec.get("tier") or ""),
                      "Query": query, "Topic": (rec.get("topic") or "")[:200],
                      "Url": url, "Title": (rec.get("title") or "")[:300],
                      "Citation": citation,
                      "Facts": facts_text if not f_red else "{}",
                      "ObservedAt": rec.get("observedAt") or now,
                      "OriginatingAction": (originating_action or
                                            rec.get("originatingAction") or "")[:200],
                      "RunId": run_id})
        stored += 1
    out = {"stored": stored, "redacted": redacted, "storedAt": now}
    if stored and drive_id and reports_root:
        found = _ledger_lookup(supplier, "", "", "", "", None)
        out["knowledgeFile"] = _ledger_write_file(drive_id, reports_root,
                                                  supplier, found["records"])
    return out


def _ledger_observe(tool: str, source_id: str, req: func.HttpRequest,
                    query: str, facts: dict, url: str = "",
                    title: str = "") -> None:
    """Record an observation the Function itself made (fetch_public_page,
    passive_recon). Best-effort by design: a ledger failure must never fail
    the fetch the analyst is waiting for — it is a speed-up, not a control."""
    supplier = (req.params.get("supplier") or "").strip()
    if not supplier or not SITE_ID:
        return
    try:
        _ledger_store(supplier, (req.params.get("service") or "").strip(),
                      [{"sourceId": source_id, "tool": tool, "query": query,
                        "url": url, "title": title, "facts": facts,
                        "citation": f"{url} (retrieved {facts.get('retrievedAt', '')[:10]})"
                                    if url else ""}],
                      run_id=(req.params.get("runId") or ""),
                      originating_action=(req.params.get("originatingAction")
                                          or ""))
    except Exception as e:                                    # noqa: BLE001
        _audit("research_ledger.observe_failed", tool=tool,
               error=str(e)[:200])


@app.route(route="research_ledger", methods=["GET"])
@_guard
def research_ledger_lookup(req: func.HttpRequest) -> func.HttpResponse:
    """READ-ONLY agent tool (research-ledger.yaml): what do we already know
    about this supplier, from which source, how old is it, and who asked?
    GET keeps it inside the read-only rule attach_integrations.py enforces —
    an agent can read the ledger and can never write to it."""
    q = req.params
    if not q.get("supplier"):
        raise Http(400, "missing query parameter: supplier")
    max_age = q.get("maxAgeDays")
    out = _ledger_lookup(q["supplier"], q.get("service", ""),
                         q.get("sourceId", ""), q.get("query", ""),
                         q.get("topic", ""),
                         int(max_age) if max_age else None)
    # Measured, not assumed: operations/kql/research-reuse-rate.kql reads these
    # to show whether the ledger is actually saving the work it claims to.
    _audit("research_ledger.lookup", supplier=normalise(q["supplier"]),
           sourceId=q.get("sourceId", ""),
           outcome=("fresh" if out["hit"] else
                    {"only-stale": "stale", "not-recorded": "miss",
                     "ledger-unavailable": "unavailable"}.get(out["reason"],
                                                              "miss")),
           freshCount=out.get("freshCount", 0),
           staleCount=out.get("staleCount", 0))
    return _json(out)


@app.route(route="research_ledger", methods=["POST"])
@_guard
def research_ledger_store(req: func.HttpRequest) -> func.HttpResponse:
    b = _body(req, "research_ledger")
    return _json(_ledger_store(b.get("supplier", ""), b.get("service", ""),
                               b.get("records") or [], b.get("runId", ""),
                               b.get("originatingAction", ""),
                               b.get("driveId", ""), b.get("reportsRoot", "")))


@app.route(route="fetch_evidence", methods=["POST"])
@_guard
def fetch_evidence(req: func.HttpRequest) -> func.HttpResponse:
    """Attach a SharePoint evidence file to the Foundry project (file_search /
    code_interpreter) without streaming it through the conversation."""
    b = _body(req, "fetch_evidence")
    data, name = _drive_item_bytes(b["driveId"], b["itemId"])
    return _json({"fileId": _foundry_upload(data, name), "fileName": name, "bytes": len(data)})


def _input_bytes(b: dict, key_prefix: str = "") -> tuple[bytes, str]:
    """Resolve an input file from contentBase64 | driveId+itemId | fileId."""
    if b.get(key_prefix + "contentBase64"):
        try:
            data = base64.b64decode(re.sub(r"\s+", "", str(b[key_prefix + "contentBase64"])), validate=True)
        except (ValueError, TypeError) as e:
            raise Http(400, f"{key_prefix}contentBase64 is not valid base64: {e}")
        if not data:
            raise Http(400, f"{key_prefix}contentBase64 decodes to zero bytes")
        if len(data) > MAX_PAYLOAD:
            raise Http(413, f"{key_prefix}contentBase64 exceeds {MAX_PAYLOAD} bytes")
        return data, b.get(key_prefix + "fileName", "input.bin")
    if b.get(key_prefix + "driveId") and b.get(key_prefix + "itemId"):
        return _drive_item_bytes(b[key_prefix + "driveId"], b[key_prefix + "itemId"])
    if b.get(key_prefix + "fileId"):
        return _foundry_download(b[key_prefix + "fileId"]), b.get(key_prefix + "fileName", "input.bin")
    raise Http(400, f"provide {key_prefix}contentBase64, {key_prefix}driveId+{key_prefix}itemId or {key_prefix}fileId")


# ------------------------------------------- Document Intelligence (OCR)
def _docintel_confidence(result: dict) -> dict:
    """Mean / minimum word confidence — the number the knowledge pack tells
    agents to record ("OCR via Document Intelligence, confidence X") and the
    signal for quoting a passage as "(OCR)"."""
    vals = [w.get("confidence") for p in result.get("pages", []) or []
            for w in p.get("words", []) or [] if isinstance(w.get("confidence"), (int, float))]
    if not vals:
        return {"mean": None, "min": None, "words": 0}
    return {"mean": round(sum(vals) / len(vals), 4), "min": round(min(vals), 4), "words": len(vals)}


@app.route(route="extract_pdf", methods=["POST"])
@_guard
def extract_pdf(req: func.HttpRequest) -> func.HttpResponse:
    """OCR / layout extraction for scanned or garbled evidence, on Azure AI
    Document Intelligence in the EU region — the replacement for the
    sandbox's pytesseract (agents/knowledge-packs/pdf-reading-foundry.md §4,
    document_agents_addendum.md). Fallback order stays: pure-Python first,
    office-tools (poppler) second, this endpoint last.

    Document Intelligence is reached ONLY from here, with this app's managed
    identity (main.bicep: disableLocalAuth, no key anywhere) — it is never an
    agent tool connection, so nothing can send it a document that has not
    passed through the pipeline.

    Body: {model?: prebuilt-read|prebuilt-layout, pages?: "1-5",
           contentBase64 | driveId+itemId | fileId, fileName?,
           outputContentFormat?: text|markdown, attachToProject?: bool}
    """
    b = _body(req, "extract_pdf")
    if not DOCINTEL_ENDPOINT:
        raise Http(503, "DOCINTEL_ENDPOINT not configured (enableDocumentIntelligence=false)")
    model = b.get("model", "prebuilt-read")
    data, name = _input_bytes(b)
    params = {"api-version": DOCINTEL_API_VERSION,
              "outputContentFormat": b.get("outputContentFormat", "text")}
    if b.get("pages"):
        params["pages"] = b["pages"]
    token = _token("https://cognitiveservices.azure.com/.default")
    r = requests.post(f"{DOCINTEL_ENDPOINT}/documentintelligence/documentModels/{model}:analyze",
                      params=params, timeout=120,
                      headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                      json={"base64Source": base64.b64encode(data).decode()})
    if r.status_code not in (200, 202):
        raise Http(502, "Document Intelligence rejected the document",
                   {"status": r.status_code, "detail": r.text[:500]})
    op = r.headers.get("operation-location") or r.headers.get("Operation-Location")
    if not op:
        raise Http(502, "Document Intelligence returned no operation-location")

    deadline = time.monotonic() + float(os.environ.get("DOCINTEL_TIMEOUT_SECONDS", "420"))
    delay, payload = 1.0, {}
    while True:
        if time.monotonic() > deadline:
            raise Http(504, "Document Intelligence analysis timed out")
        time.sleep(delay)
        delay = min(delay * 1.5, 10.0)
        poll = requests.get(op, headers={"Authorization": f"Bearer {token}"}, timeout=60)
        poll.raise_for_status()
        payload = poll.json()
        status = str(payload.get("status", "")).lower()
        if status == "succeeded":
            break
        if status in ("failed", "canceled"):
            raise Http(502, "Document Intelligence analysis failed",
                       {"detail": json.dumps(payload.get("error", {}))[:500]})

    result = payload.get("analyzeResult") or {}
    content = result.get("content") or ""
    truncated = len(content) > DOCINTEL_MAX_CHARS
    tables = [{"rowCount": t.get("rowCount"), "columnCount": t.get("columnCount"),
               "pageNumber": (t.get("boundingRegions") or [{}])[0].get("pageNumber"),
               "cells": [{"rowIndex": c.get("rowIndex"), "columnIndex": c.get("columnIndex"),
                          "content": c.get("content", "")} for c in (t.get("cells") or [])]}
              for t in (result.get("tables") or [])]
    out = {"model": model, "fileName": name, "bytes": len(data),
           "apiVersion": DOCINTEL_API_VERSION,
           "pages": len(result.get("pages") or []),
           "pageRange": b.get("pages", "all"),
           "content": content[:DOCINTEL_MAX_CHARS],
           "truncated": truncated,
           "tables": tables,
           "confidence": _docintel_confidence(result),
           "source": f"OCR via Document Intelligence ({model}, {DOCINTEL_API_VERSION}), EU region"}
    if b.get("attachToProject"):
        out["fileId"] = _foundry_upload(content.encode("utf-8"), f"{Path(name).stem}.ocr.txt")
    _audit("extract_pdf", model=model, pages=out["pages"], bytes=len(data))
    return _json(out)


# ------------------------------------------- office-tools (LibreOffice app)
OFFICE_TOOLS_BASE = os.environ.get("OFFICE_TOOLS_BASE_URL", "").rstrip("/")
OFFICE_TOOLS_KEY = os.environ.get("OFFICE_TOOLS_KEY", "")


def _office_tools(path: str, payload: dict, timeout: int = 600) -> dict:
    """Call the separate office-tools Function App (functions/office-tools:
    LibreOffice/pandoc/poppler). Key-protected; this app holds the key, the
    agents never see it."""
    if not OFFICE_TOOLS_BASE:
        raise Http(503, "OFFICE_TOOLS_BASE_URL not configured (office-tools app not deployed)")
    headers = {"Content-Type": "application/json"}
    if OFFICE_TOOLS_KEY:
        headers["x-functions-key"] = OFFICE_TOOLS_KEY
    r = requests.post(f"{OFFICE_TOOLS_BASE}/{path}", json=payload, headers=headers, timeout=timeout)
    if r.status_code >= 400:
        raise Http(502, f"office-tools /{path} failed",
                   {"status": r.status_code, "detail": r.text[:1000]})
    return r.json()


def _recalc_gate(prim: dict, files: list[dict]) -> dict:
    """The xlsx skill's mandatory recalc gate (renderers-src/xlsx-generic/
    manifest.json 'post', verifier rule 9): every workbook leaving /api/render
    is recalculated by LibreOffice in the office-tools app and must report
    total_errors=0. The RECALCULATED bytes replace the rendered ones, so the
    stored record opens with cached values rather than uncalculated formulas.

    Degrades explicitly, never silently: with no office-tools app configured
    the gate is reported as {"passed": null, "reason": ...} so the verifier
    and the approver can see the check did not run."""
    xlsx = [f for f in files if f["kind"] == "xlsx"]
    if not xlsx:
        return {"passed": True, "checks": []}
    if not OFFICE_TOOLS_BASE:
        return {"passed": None, "gate": "xlsx-recalc",
                "reason": "office-tools not configured (OFFICE_TOOLS_BASE_URL empty)"}
    checks, details = [], []
    for f in xlsx:
        res = _office_tools("recalc", {"fileName": f["fileName"],
                                       "contentBase64": f["contentBase64"],
                                       "timeoutSeconds": 60})
        g = res.get("gate") or {}
        checks += [f"{f['fileName']}: {c}" for c in g.get("checks", [])]
        details.append({"fileName": f["fileName"], "totalErrors": res.get("total_errors"),
                        "totalFormulas": res.get("total_formulas")})
        if res.get("contentBase64"):
            # `prim` is a copy of one of these entries under the requested
            # output name: match it on content, not on position.
            if prim["kind"] == "xlsx" and prim.get("contentBase64") == f["contentBase64"]:
                prim["contentBase64"] = res["contentBase64"]
            f["contentBase64"] = res["contentBase64"]
    if checks:
        raise Http(422, "quality gate failed", {"gate": "xlsx-recalc", "checks": checks})
    return {"passed": True, "gate": "xlsx-recalc", "checks": [], "recalc": details}


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


_FENCE = re.compile(r"```[ \t]*(?:json|jsonc|JSON)?[ \t]*\r?\n(.*?)```", re.S)
_ZWSP = re.compile("[\u200b-\u200f\u2028\u2029\ufeff]")


def _extract_payload(text, fmt: str):
    """Agent messages arrive as prose + one fenced ```json block (or the
    finished HTML). Return the JSON object / HTML string the renderer needs.

    Defensive on purpose: the producer is a language model, so every fenced
    block is tried in order (a first block that is an example or truncated
    must not lose a valid second one), invisible characters and a leading BOM
    are stripped, a bare object embedded in prose is the last resort, and the
    result must be an object/array — a JSON *string* or number is a contract
    error, never a renderer input. Every failure is a 400 that says what was
    seen (the pipeline shows it to the requester), never a 500."""
    if isinstance(text, (dict, list)):
        return text
    if text is None or (isinstance(text, str) and not text.strip()):
        raise Http(400, "data/content missing")
    if isinstance(text, (int, float, bool)):
        raise Http(400, f"data must be an object or a fenced ```json block, got {type(text).__name__}")
    s = _ZWSP.sub("", str(text)).lstrip("\ufeff")

    if fmt == "html" or (fmt == "pdf" and "<html" in s.lower() and "```" not in s):
        m = re.search(r"<!doctype html.*?</html>|<html.*?</html>", s, re.I | re.S)
        return m.group(0) if m else s

    tried = 0
    for m in _FENCE.finditer(s):
        tried += 1
        try:
            obj = json.loads(m.group(1))
        except json.JSONDecodeError:
            continue
        if isinstance(obj, (dict, list)):
            return obj
    try:
        obj = json.loads(s)
        if isinstance(obj, (dict, list)):
            return obj
    except json.JSONDecodeError:
        pass
    # last resort: a bare {...} embedded in prose without a fence
    brace = re.search(r"\{.*\}", s, re.S)
    if brace:
        try:
            obj = json.loads(brace.group(0))
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            pass
    raise Http(400, f"no parsable JSON object found in data ({tried} fenced block(s) tried)",
               {"preview": s[:200]})


_REGISTRY_SCHEMAS: dict[str, str] | None = None


def _registry_schema_name(template: str) -> str | None:
    """The `schema` key templates/registry.json records for this template."""
    global _REGISTRY_SCHEMAS
    if _REGISTRY_SCHEMAS is None:
        _REGISTRY_SCHEMAS = {}
        reg = HERE.parent.parent / "templates" / "registry.json"
        try:
            for t in json.loads(reg.read_text(encoding="utf-8")).get("templates", []):
                if t.get("id") and t.get("schema"):
                    _REGISTRY_SCHEMAS[t["id"]] = t["schema"]
        except (OSError, json.JSONDecodeError, AttributeError):
            pass  # the registry is not shipped in every image; manifests still resolve
    return _REGISTRY_SCHEMAS.get(template)


def _schema_path(template: str, mf: dict | None = None) -> tuple[Path | None, str | None]:
    """Resolve the contract file for a template.

    Order: the renderer manifest's `schema` key, then templates/registry.json,
    then the `<template>.schema.json` name convention (and its underscored
    variant). The name convention alone is NOT enough — four contracts are
    deliberately named after the document rather than the template id
    (`dpia` -> dpia_report, `ciso-reporting` -> ciso_reporting_assessment,
    `ciso-global` -> ciso_global_deck, `ciso-exec-summary` ->
    ciso_exec_summary_render), and resolving by convention alone silently
    skipped validation for all four. The files are NOT renamed: the manifests
    and the agent charters cite these names (templates/README.md "Schema
    resolution").

    Returns (path, declared_name). `declared_name` is set when a manifest or
    the registry declares a schema, so a declared-but-missing file can be a
    500 instead of a silent pass.
    """
    declared = (mf or {}).get("schema") or _registry_schema_name(template)
    names = [declared] if declared else []
    names += [f"{template}.schema.json", f"{template.replace('-', '_')}.schema.json"]
    for name in names:
        for sd in SCHEMA_DIRS:
            cand = sd / name
            if cand.exists():
                return cand, declared
    return None, declared


def _validate_schema(template: str, data, mf: dict | None = None) -> None:
    """jsonschema gate: a payload that does not match the registered contract
    is a 400 naming the failing field, before any renderer is started. Fails
    CLOSED — an unreadable schema, a missing jsonschema package, or a contract
    that is declared but not shipped is a 500, never a silent pass (a renderer
    fed an off-contract payload produces a plausible-looking wrong report).

    A template that declares no schema anywhere is the only pass-through case,
    and it is deliberate: `enx-theme` and the endpoint-only renderers have no
    payload contract to check.
    """
    cand, declared = _schema_path(template, mf)
    if cand is None:
        if declared:
            raise Http(500, f"template '{template}' declares schema '{declared}' "
                            f"but it is not in this image")
        return
    try:
        import jsonschema
    except ImportError:
        raise Http(500, "jsonschema is not installed in this image")
    try:
        schema = json.loads(cand.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        raise Http(500, f"schema {cand.name} is unreadable: {e}")
    try:
        jsonschema.validate(data, schema)
    except jsonschema.ValidationError as e:
        raise Http(400, f"data does not match {cand.name}: {e.message}",
                   {"path": list(map(str, e.absolute_path)) or ["<root>"],
                    "schemaPath": list(map(str, e.absolute_schema_path))})
    except jsonschema.SchemaError as e:
        raise Http(500, f"schema {cand.name} is invalid: {e.message}")


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
            # The renderer's own manifest is the first place the contract name
            # is looked up, so a template whose schema file is named after the
            # document rather than the template id still validates.
            _validate_schema(template, payload, _manifest(_renderer_dir(template)))
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
    # xlsx leaves this endpoint only after LibreOffice has recalculated it in
    # the office-tools app (raises 422 when the workbook still has errors).
    recalc = _recalc_gate(prim, files)
    if recalc.get("gate"):
        gate = {**gate, **recalc}
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
    # The page was fetched for a reason; record it against the supplier so the
    # next run reads the ledger instead of fetching it again (no-op unless the
    # caller named the supplier).
    _ledger_observe("osint-proxy", req.params.get("sourceId") or "osint-proxy",
                    req, query=url,
                    facts={"retrievedAt": out["retrievedAt"],
                           "status": out["status"],
                           "summary": (out.get("title") or
                                       out.get("text", "")[:300]).strip()},
                    url=out["finalUrl"], title=out.get("title", ""))
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
    _ledger_observe("passive-recon", "passive-recon", req,
                    query=f"passive fingerprint of {domain}",
                    facts={"retrievedAt": out.get("retrievedAt", ""),
                           "summary": f"DNS/TLS/header fingerprint of {domain}",
                           "dns": out.get("dns"), "tls": out.get("tls"),
                           "http": out.get("http")},
                    title=domain)
    return _json(out)


# ------------------------------------------------------------ pdf-coverage
PDF_STAGES = {"triage": "triage.py", "inventory": "inventory.py", "chunk": "chunk_extract.py",
              "verify": "verify_coverage.py", "cross_check": "cross_check.py"}


@app.route(route="pdf/{stage}", methods=["POST"])
@_guard
def pdf_coverage(req: func.HttpRequest) -> func.HttpResponse:
    """Runs the byte-verified pdf-full-coverage-analyzer scripts (poppler,
    tesseract, PyMuPDF, pdfplumber are in this container) on a SharePoint
    item / Foundry file / inline bytes. Non-mutating compute — but POST-only,
    and scripts/attach_integrations.py strips every non-GET operation from
    every attached spec (governance/HUMAN_APPROVAL.md Layer 1). So there is
    deliberately NO integrations/openapi/pdf-coverage.yaml: this surface is
    invoked by the delivery pipeline, never by an agent. Attaching it would
    have meant carving the first exception into the read-only rule, for an
    endpoint the pipeline can call on the agent's behalf anyway."""
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
                  "officeTools": bool(OFFICE_TOOLS_BASE),
                  "documentIntelligence": bool(DOCINTEL_ENDPOINT),
                  "dataBoundary": os.environ.get("ENX_DATA_BOUNDARY", "EU")})
