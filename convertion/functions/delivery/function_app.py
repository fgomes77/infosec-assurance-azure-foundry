"""Delivery Function App — SharePoint storage + report rendering.

Three HTTP endpoints, called by the Logic App pipelines in ../workflows/
(function-key + VNet restricted; the managed identity holds Graph
Sites.Selected write on the InfoSec Assurance site — agents themselves are
read-only, see ../../sharepoint/README.md):

  POST /api/ensure_folder   {driveId, rootItemId, segments: [Supplier, Service]}
      -> {folderId}            idempotent, race-safe, reuse-never-duplicate
  POST /api/upload           {driveId, folderId, fileName, contentBase64, share?}
      -> {itemId, webUrl, shareUrl?}
  POST /api/render           {format: html|docx|pptx|xlsx, template?, data|content}
      -> {fileName, contentBase64}

Rendering reuses the byte-verified generators converted from the claude.ai
skills (build/agents/*/code/), so outputs match the previous environment:
  html  -> the deepsearch/ciso dashboard templates filled verbatim
  docx  -> python-docx flow from the dpia skill
  pptx  -> Node generators from ciso-reporting / pptx-executive-summary-ciso
           (this app ships Node, unlike agent code_interpreter)
  xlsx  -> openpyxl flow from the xlsx skill
"""

from __future__ import annotations

import base64
import json
import logging
import os
import re
import subprocess
import tempfile
from pathlib import Path

import azure.functions as func
import requests
from azure.identity import DefaultAzureCredential

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

GRAPH = "https://graph.microsoft.com/v1.0"
_cred = DefaultAzureCredential()

# Generators staged at deploy time by ../../scripts/stage_renderers.py
RENDERERS = Path(__file__).parent / "renderers"

ILLEGAL = re.compile(r'[\"*:<>?/\\|]')


def _token() -> str:
    return _cred.get_token("https://graph.microsoft.com/.default").token


def _graph(method: str, url: str, **kw) -> requests.Response:
    headers = kw.pop("headers", {})
    headers["Authorization"] = f"Bearer {_token()}"
    resp = requests.request(method, url, headers=headers, timeout=60, **kw)
    return resp


def normalise(name: str) -> str:
    """Trim and replace Graph-illegal characters so name variants of the
    same supplier/service resolve to one folder."""
    return ILLEGAL.sub("-", name.strip()).rstrip(". ")


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
def ensure_folder(req: func.HttpRequest) -> func.HttpResponse:
    body = req.get_json()
    folder_id = ensure_path(body["driveId"], body["rootItemId"], body["segments"])
    return func.HttpResponse(json.dumps({"folderId": folder_id}),
                             mimetype="application/json")


@app.route(route="upload", methods=["POST"])
def upload(req: func.HttpRequest) -> func.HttpResponse:
    body = req.get_json()
    drive, folder = body["driveId"], body["folderId"]
    name = normalise(body["fileName"])
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
    return func.HttpResponse(json.dumps(out), mimetype="application/json")


@app.route(route="render", methods=["POST"])
def render(req: func.HttpRequest) -> func.HttpResponse:
    body = req.get_json()
    fmt = body["format"]
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        out: Path
        if fmt == "html":
            # Agent supplies the finished single-file HTML (the skill
            # templates are filled by the agent itself, verbatim).
            out = tdp / body.get("fileName", "report.html")
            out.write_text(body["content"], encoding="utf-8")
        elif fmt in ("docx", "xlsx"):
            data = tdp / "data.json"
            data.write_text(json.dumps(body["data"]), encoding="utf-8")
            script = RENDERERS / body["template"] / "render.py"
            out = tdp / body.get("fileName", f"report.{fmt}")
            subprocess.run(["python3", str(script), str(data), str(out)],
                           check=True, timeout=600)
        elif fmt == "pptx":
            data = tdp / "data.json"
            data.write_text(json.dumps(body["data"]), encoding="utf-8")
            script = RENDERERS / body["template"] / "generate_slide.js"
            out = tdp / body.get("fileName", "report.pptx")
            subprocess.run(["node", str(script), str(data), str(out)],
                           check=True, timeout=600,
                           cwd=str(script.parent))
        else:
            return func.HttpResponse(f"unsupported format {fmt}", status_code=400)
        payload = base64.b64encode(out.read_bytes()).decode()
    return func.HttpResponse(
        json.dumps({"fileName": out.name, "contentBase64": payload}),
        mimetype="application/json")
