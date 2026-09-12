"""office-tools Function App — the binary document toolchain the four
converted document skills (docx · pptx · xlsx · pdf) assume and that neither
Foundry `code_interpreter` nor the delivery Function provides: LibreOffice
(`soffice`), pandoc, poppler, qpdf, tesseract, ImageMagick.

Split rationale (infra/delivery.bicep, agents/document_agents_addendum.md):
the delivery Function image carries Node 20 + Playwright/Chromium and is the
ONLY SharePoint writer; LibreOffice more than doubles that image and needs a
writable profile, so it lives here in a second container on the same Elastic
Premium plan (`{baseName}-office`).

Trust boundary — this app is deliberately the least-privileged component:

  * **No outbound calls.** It never talks to Graph, Foundry, Document
    Intelligence or the internet: every endpoint takes the file inline
    (`contentBase64`) and returns bytes inline. Callers that hold the
    SharePoint/Foundry identity (the delivery Function `/api/render`
    post-gate, the Logic App pipelines) fetch and store the bytes.
  * **Key-protected.** Every route is `AuthLevel.FUNCTION` (`x-functions-key`);
    `/api/health` is anonymous for the platform probe and returns tool status only,
    never document content.
    `ALLOWED_CALLER_PRINCIPAL_IDS` additionally pins the Easy Auth principal
    to the delivery Function / Logic Apps managed identities, and
    `delivery.bicep` restricts inbound IP to the caller subnet.
  * **No agent ever calls it directly.** It is not registered as an OpenAPI
    tool (attach_integrations.py strips non-GET anyway); agents ask the
    pipeline, which asks this app.

  POST /api/convert        {contentBase64, fileName, to, engine?, options?}
      -> {fileName, contentBase64, kind, engine, files[], log}
  POST /api/recalc         {contentBase64, fileName, timeoutSeconds?, force?}
      -> {gate:{passed,checks}, status, total_errors, total_formulas,
          error_summary, contentBase64}            (xlsx skill recalc.py gate)
  POST /api/accept_changes {contentBase64, fileName}   -> {contentBase64, message}
  POST /api/thumbnail      {contentBase64, fileName, cols?, pages?, dpi?}
      -> {files: [{fileName, contentBase64, kind}], count}
  POST /api/validate       {contentBase64, fileName, originalContentBase64?,
                            autoRepair?, author?}
      -> {ok, exitCode, report, contentBase64?}
  GET  /api/health

The four scripts executed here (`recalc.py`, `accept_changes.py`,
`thumbnail.py`, `office/validate.py`) are the BYTE-VERIFIED originals staged
out of the conversion build by `stage_toolchain.py` — they are executed, never
edited, which is what keeps recalculation, redlining and validation semantics
identical to the previous claude.ai environment.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import azure.functions as func

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)
log = logging.getLogger("office-tools")

HERE = Path(__file__).parent
TOOLCHAIN = Path(os.environ.get("TOOLCHAIN_DIR") or (HERE / "toolchain"))

MAX_PAYLOAD = int(os.environ.get("MAX_PAYLOAD_BYTES", str(50 * 1024 * 1024)))
SOFFICE_TIMEOUT = int(os.environ.get("SOFFICE_TIMEOUT_SECONDS", "300"))
ALLOWED_PRINCIPALS = {p.strip() for p in os.environ.get("ALLOWED_CALLER_PRINCIPAL_IDS", "").split(",") if p.strip()}

# Extensions this app will accept as input / produce as output. Anything else
# is refused before a byte reaches the toolchain (no .exe, no .zip bombs, no
# LibreOffice "any filter" surprises).
OFFICE_IN = {"docx", "dotx", "doc", "odt", "rtf", "pptx", "potx", "ppt", "odp",
             "xlsx", "xltx", "xls", "ods", "csv"}
TEXT_IN = {"md", "markdown", "html", "htm", "txt", "rst"}
PDF_IN = {"pdf"}
IMAGE_OUT = {"png", "jpg", "jpeg", "tiff"}
CONVERT_TARGETS = OFFICE_IN | TEXT_IN | PDF_IN | IMAGE_OUT
FILENAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ._()\-]{0,180}$")

# Skill family that owns each byte-verified script (stage_toolchain.py layout:
# toolchain/<family>/scripts/...). `pdf` is staged for the poppler-backed
# helpers of the pdf skill; the routes below use docx/pptx/xlsx.
FAMILY_SCRIPT = {
    "recalc": ("xlsx", "scripts/recalc.py"),
    "accept_changes": ("docx", "scripts/accept_changes.py"),
    "thumbnail": ("pptx", "scripts/thumbnail.py"),
    "validate_docx": ("docx", "scripts/office/validate.py"),
    "validate_pptx": ("pptx", "scripts/office/validate.py"),
    "validate_xlsx": ("xlsx", "scripts/office/validate.py"),
}

# --------------------------------------------------------- request contracts
# jsonschema is applied to every body before any file is written, so a
# malformed payload is a deterministic 400 (never a renderer stack trace).
_FILE_IN = {
    "contentBase64": {"type": "string", "minLength": 4},
    "fileName": {"type": "string", "minLength": 3, "maxLength": 180},
}
REQUEST_SCHEMAS: dict[str, dict] = {
    "convert": {
        "type": "object",
        "required": ["contentBase64", "fileName", "to"],
        "additionalProperties": False,
        "properties": {
            **_FILE_IN,
            "to": {"type": "string", "enum": sorted(CONVERT_TARGETS)},
            "engine": {"type": "string", "enum": ["auto", "soffice", "pandoc", "poppler"]},
            "options": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "filter": {"type": "string", "maxLength": 120},
                    "pages": {"type": "string", "pattern": r"^\d{1,5}(-\d{1,5})?$"},
                    "dpi": {"type": "integer", "minimum": 36, "maximum": 600},
                    "standalone": {"type": "boolean"},
                },
            },
        },
    },
    "recalc": {
        "type": "object",
        "required": ["contentBase64", "fileName"],
        "additionalProperties": False,
        "properties": {
            **_FILE_IN,
            "timeoutSeconds": {"type": "integer", "minimum": 5, "maximum": 600},
            "force": {"type": "boolean"},
        },
    },
    "accept_changes": {
        "type": "object",
        "required": ["contentBase64", "fileName"],
        "additionalProperties": False,
        "properties": dict(_FILE_IN),
    },
    "thumbnail": {
        "type": "object",
        "required": ["contentBase64", "fileName"],
        "additionalProperties": False,
        "properties": {
            **_FILE_IN,
            "cols": {"type": "integer", "minimum": 1, "maximum": 6},
            "pages": {"type": "string", "pattern": r"^\d{1,5}(-\d{1,5})?$"},
            "dpi": {"type": "integer", "minimum": 36, "maximum": 600},
        },
    },
    "validate": {
        "type": "object",
        "required": ["contentBase64", "fileName"],
        "additionalProperties": False,
        "properties": {
            **_FILE_IN,
            "originalContentBase64": {"type": "string", "minLength": 4},
            "autoRepair": {"type": "boolean"},
            "author": {"type": "string", "maxLength": 120},
        },
    },
}


# --------------------------------------------------------------------- utils
class Http(Exception):
    def __init__(self, status: int, msg: str, extra: dict | None = None):
        super().__init__(msg)
        self.status, self.msg, self.extra = status, msg, extra or {}


def _json(obj, status=200) -> func.HttpResponse:
    return func.HttpResponse(json.dumps(obj, ensure_ascii=False), status_code=status,
                             mimetype="application/json")


def _guard(fn):
    """Caller pinning, payload cap, structured errors — same contract as the
    delivery Function's _guard so both apps fail the same way."""
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
            log.warning("%s -> %s %s", getattr(req, "url", "?"), e.status, e.msg)
            return _json({"error": e.msg, **e.extra}, e.status)
        except (KeyError, ValueError, json.JSONDecodeError) as e:
            return _json({"error": f"bad request: {e}"}, 400)
        except subprocess.TimeoutExpired:
            return _json({"error": "toolchain timeout", "hint": "raise timeoutSeconds or split the document"}, 504)
        except subprocess.CalledProcessError as e:
            tail = e.stderr or e.stdout or b""
            tail = tail.decode(errors="replace") if isinstance(tail, bytes) else str(tail)
            return _json({"error": "toolchain failed", "detail": tail[-4000:]}, 500)
    inner.__name__ = fn.__name__
    return inner


def body_of(req: func.HttpRequest, contract: str) -> dict:
    """Parse + jsonschema-validate the request body. Any shape error is a 400
    naming the offending path — never a 500 from deep inside a script."""
    raw = req.get_body() or b""
    if not raw.strip():
        raise Http(400, f"empty body; {contract} expects a JSON object")
    try:
        b = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise Http(400, f"body is not valid UTF-8 JSON: {e}")
    if not isinstance(b, dict):
        raise Http(400, "body must be a JSON object")
    schema = REQUEST_SCHEMAS[contract]
    try:
        import jsonschema
    except ImportError:  # fail closed: never skip validation silently
        raise Http(500, "jsonschema is not installed in this image")
    try:
        jsonschema.validate(b, schema)
    except jsonschema.ValidationError as e:
        raise Http(400, f"invalid {contract} payload: {e.message}",
                   {"path": list(map(str, e.absolute_path)) or ["<root>"]})
    return b


def decode_input(b: dict, key: str = "contentBase64") -> bytes:
    try:
        # tolerate the line-wrapped base64 some Logic App expressions emit
        data = base64.b64decode(re.sub(r"\s+", "", str(b[key])), validate=True)
    except (ValueError, TypeError) as e:
        raise Http(400, f"{key} is not valid base64: {e}")
    if not data:
        raise Http(400, f"{key} decodes to zero bytes")
    if len(data) > MAX_PAYLOAD:
        raise Http(413, f"{key} exceeds {MAX_PAYLOAD} bytes")
    return data


def safe_name(name: str) -> str:
    """Reject path traversal / odd characters before anything touches disk."""
    n = str(name)
    if n != Path(n).name or "\\" in n:
        raise Http(400, "fileName must not contain a path separator")
    if not FILENAME_RE.match(n) or "." not in n:
        raise Http(400, "fileName must be a plain <name>.<ext>")
    return n


def ext_of(name: str) -> str:
    return safe_name(name).rsplit(".", 1)[-1].lower()


def script(kind: str) -> Path:
    """Locate a byte-verified script staged by stage_toolchain.py."""
    family, rel = FAMILY_SCRIPT[kind]
    p = TOOLCHAIN / family / rel
    if not p.is_file():
        raise Http(501, f"{family}/{rel} is not staged in this image",
                   {"hint": "run functions/office-tools/stage_toolchain.py before `az acr build`",
                    "toolchainDir": str(TOOLCHAIN)})
    return p


def run(cmd: list[str], cwd: Path, timeout: int | None = None, check: bool = True) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env.setdefault("HOME", tempfile.gettempdir())      # soffice needs a writable HOME
    env.setdefault("SAL_USE_VCLPLUGIN", "svp")         # headless VCL, no X server
    p = subprocess.run(cmd, cwd=str(cwd), capture_output=True,
                       timeout=timeout or SOFFICE_TIMEOUT, env=env)
    if check and p.returncode != 0:
        raise subprocess.CalledProcessError(p.returncode, cmd, p.stdout, p.stderr)
    return p


def out(path: Path) -> dict:
    return {"fileName": path.name,
            "contentBase64": base64.b64encode(path.read_bytes()).decode(),
            "kind": path.suffix.lstrip(".").lower()}


# ------------------------------------------------------------------ convert
def _engine_for(src_ext: str, to: str, requested: str) -> str:
    if requested and requested != "auto":
        return requested
    if src_ext in PDF_IN and to in IMAGE_OUT:
        return "poppler"
    if src_ext in TEXT_IN and to in TEXT_IN | {"docx"}:
        return "pandoc"
    return "soffice"


@app.route(route="convert", methods=["POST"])
@_guard
def convert(req: func.HttpRequest) -> func.HttpResponse:
    """Format conversion for the skills' `soffice --convert-to` / `pandoc` /
    `pdftoppm` steps (legacy .doc/.ppt/.xls intake, DOCX->PDF visual QA,
    Markdown->DOCX, PDF->PNG page images)."""
    b = body_of(req, "convert")
    name = safe_name(b["fileName"])
    src_ext = ext_of(name)
    to = b["to"].lower()
    if src_ext not in OFFICE_IN | TEXT_IN | PDF_IN:
        raise Http(400, f"unsupported source extension .{src_ext}")
    if src_ext == to:
        raise Http(400, "source and target format are identical")
    opts = b.get("options") or {}
    engine = _engine_for(src_ext, to, b.get("engine", "auto"))

    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        src = tdp / name
        src.write_bytes(decode_input(b))
        outdir = tdp / "out"
        outdir.mkdir()

        if engine == "soffice":
            if not shutil.which("soffice"):
                raise Http(501, "soffice (LibreOffice) is not installed in this image")
            target = opts.get("filter") or to      # e.g. 'pdf:writer_pdf_Export'
            p = run(["soffice", "--headless", "--norestore", "--nolockcheck",
                     f"-env:UserInstallation={(tdp / 'lo_profile').as_uri()}",
                     "--convert-to", target, "--outdir", str(outdir), str(src)])
        elif engine == "pandoc":
            if not shutil.which("pandoc"):
                raise Http(501, "pandoc is not installed in this image")
            dest = outdir / f"{Path(name).stem}.{to}"
            cmd = ["pandoc", str(src), "-o", str(dest)]
            if opts.get("standalone", True) and to in ("html", "htm"):
                cmd.append("--standalone")
            p = run(cmd)
        else:  # poppler: pdf -> page images
            if src_ext != "pdf":
                raise Http(400, "engine 'poppler' only converts PDF input")
            fmt = "jpeg" if to in ("jpg", "jpeg") else to
            if fmt not in ("png", "jpeg", "tiff"):
                raise Http(400, "poppler targets are png|jpg|tiff")
            cmd = ["pdftoppm", f"-{fmt}", "-r", str(opts.get("dpi", 150))]
            if opts.get("pages"):
                first, _, last = opts["pages"].partition("-")
                cmd += ["-f", first, "-l", last or first]
            p = run(cmd + [str(src), str(outdir / "page")], timeout=SOFFICE_TIMEOUT)

        files = [out(f) for f in sorted(outdir.rglob("*")) if f.is_file()]
        if not files:
            raise Http(500, "conversion produced no output",
                       {"engine": engine,
                        "detail": (p.stderr or p.stdout or b"").decode(errors="replace")[-2000:]})
        want = {to, "jpg", "jpeg"} if to in ("jpg", "jpeg") else {to, "htm" if to == "html" else to}
        prim = next((f for f in files if f["kind"] in want), files[0])
        return _json({**prim, "files": files, "engine": engine,
                      "log": (p.stdout or b"").decode(errors="replace")[-2000:]})


# ------------------------------------------------------------------- recalc
@app.route(route="recalc", methods=["POST"])
@_guard
def recalc(req: func.HttpRequest) -> func.HttpResponse:
    """The xlsx skill's MANDATORY formula gate: `scripts/recalc.py` drives
    LibreOffice to calculateAll() + store, then reports every Excel error it
    finds. `gate.passed` is false unless status=='success' and
    total_errors==0 — the delivery Function refuses to release a workbook
    whose gate failed (renderers-src/xlsx-generic/manifest.json 'post',
    verifier rule 9)."""
    b = body_of(req, "recalc")
    name = safe_name(b["fileName"])
    if ext_of(name) not in ("xlsx", "xlsm", "xltx"):
        raise Http(400, "recalc accepts .xlsx/.xlsm/.xltx")
    s = script("recalc")
    timeout = int(b.get("timeoutSeconds", 60))
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        wb = tdp / name
        wb.write_bytes(decode_input(b))
        argv = [str(wb), str(timeout)] + (["--force"] if b.get("force") else [])
        # recalc.py exits 1 when the JSON carries an 'error' key: read the
        # JSON, do not treat the exit code as the outcome.
        p = run(["python3", s.name] + argv, cwd=s.parent, timeout=timeout + 120, check=False)
        stdout = (p.stdout or b"").decode(errors="replace")
        try:
            result = json.loads(stdout[stdout.index("{"):stdout.rindex("}") + 1])
        except (ValueError, json.JSONDecodeError):
            raise Http(500, "recalc.py produced no JSON result",
                       {"stdout": stdout[-2000:],
                        "stderr": (p.stderr or b"").decode(errors="replace")[-2000:]})
        checks = []
        if "error" in result:
            checks.append(str(result["error"]))
        if result.get("status") != "success":
            checks.append(f"recalc status={result.get('status')!r}")
        if result.get("total_errors"):
            checks.append(f"{result['total_errors']} Excel error(s): "
                          f"{', '.join(sorted((result.get('error_summary') or {}).keys()))}")
        return _json({"gate": {"passed": not checks, "checks": checks},
                      **result,
                      "contentBase64": base64.b64encode(wb.read_bytes()).decode(),
                      "fileName": name})


# ----------------------------------------------------------- accept changes
@app.route(route="accept_changes", methods=["POST"])
@_guard
def accept_changes(req: func.HttpRequest) -> func.HttpResponse:
    """docx skill `scripts/accept_changes.py`: flatten tracked changes into a
    clean DOCX (redlining semantics unchanged — the script is the original)."""
    b = body_of(req, "accept_changes")
    name = safe_name(b["fileName"])
    if ext_of(name) not in ("docx", "dotx"):
        raise Http(400, "accept_changes accepts .docx/.dotx")
    s = script("accept_changes")
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        src = tdp / name
        src.write_bytes(decode_input(b))
        dest = tdp / f"{Path(name).stem}_clean.docx"
        p = run(["python3", s.name, str(src), str(dest)], cwd=s.parent, timeout=300, check=False)
        message = (p.stdout or b"").decode(errors="replace").strip()
        if p.returncode != 0 or not dest.exists():
            raise Http(422, "accept_changes failed",
                       {"message": message[-2000:],
                        "detail": (p.stderr or b"").decode(errors="replace")[-2000:]})
        return _json({**out(dest), "message": message[-2000:]})


# --------------------------------------------------------------- thumbnails
@app.route(route="thumbnail", methods=["POST"])
@_guard
def thumbnail(req: func.HttpRequest) -> func.HttpResponse:
    """Visual QA images. .pptx goes through the pptx skill's own
    `scripts/thumbnail.py` (labelled slide grid, hidden-slide placeholders);
    .pdf is rasterised with poppler; .docx/.xlsx are converted to PDF first,
    so the "render it and look at it" step of the skills works here."""
    b = body_of(req, "thumbnail")
    name = safe_name(b["fileName"])
    ext = ext_of(name)
    dpi = int(b.get("dpi", 100))
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        src = tdp / name
        src.write_bytes(decode_input(b))
        outdir = tdp / "out"
        outdir.mkdir()

        if ext == "pptx":
            s = script("thumbnail")
            run(["python3", s.name, str(src), str(outdir / "thumbnails"),
                 "--cols", str(int(b.get("cols", 3)))], cwd=s.parent, timeout=900)
        else:
            pdf = src
            if ext != "pdf":
                if ext not in OFFICE_IN:
                    raise Http(400, f"thumbnail accepts .pptx, .pdf or an office format, not .{ext}")
                if not shutil.which("soffice"):
                    raise Http(501, "soffice (LibreOffice) is not installed in this image")
                run(["soffice", "--headless", "--norestore", "--nolockcheck",
                     f"-env:UserInstallation={(tdp / 'lo_profile').as_uri()}",
                     "--convert-to", "pdf", "--outdir", str(tdp / "pdf"), str(src)])
                cands = sorted((tdp / "pdf").glob("*.pdf"))
                if not cands:
                    raise Http(500, "conversion to PDF produced no file")
                pdf = cands[0]
            cmd = ["pdftoppm", "-jpeg", "-r", str(dpi)]
            if b.get("pages"):
                first, _, last = b["pages"].partition("-")
                cmd += ["-f", first, "-l", last or first]
            run(cmd + [str(pdf), str(outdir / "page")], timeout=600)

        files = [out(f) for f in sorted(outdir.rglob("*")) if f.is_file()]
        if not files:
            raise Http(500, "no thumbnails produced")
        return _json({"files": files, "count": len(files)})


# ----------------------------------------------------------------- validate
@app.route(route="validate", methods=["POST"])
@_guard
def validate(req: func.HttpRequest) -> func.HttpResponse:
    """OOXML XSD + redlining validation (`office/validate.py` of the docx /
    pptx / xlsx skills). `--author` (requires `originalContentBase64`) turns
    on the untracked-edit check; `autoRepair` writes the repaired file back
    and it is returned as `contentBase64`."""
    b = body_of(req, "validate")
    name = safe_name(b["fileName"])
    ext = ext_of(name)
    family = {"docx": "docx", "dotx": "docx", "pptx": "pptx", "potx": "pptx",
              "xlsx": "xlsx", "xltx": "xlsx"}.get(ext)
    if not family:
        raise Http(400, "validate accepts .docx/.dotx, .pptx/.potx, .xlsx/.xltx")
    if b.get("author") and not b.get("originalContentBase64"):
        raise Http(400, "author requires originalContentBase64 (tracked-change check)")
    s = script(f"validate_{family}")
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        src = tdp / name
        src.write_bytes(decode_input(b))
        argv = [str(src)]
        if b.get("originalContentBase64"):
            orig = tdp / f"original_{name}"
            orig.write_bytes(decode_input(b, "originalContentBase64"))
            argv += ["--original", str(orig)]
        if b.get("autoRepair"):
            argv.append("--auto-repair")
        if b.get("author"):
            argv += ["--author", str(b["author"])[:120]]
        # validate.py imports `helpers` / `validators` as siblings: run it
        # from its own office/ directory (sys.path[0]), exactly as the skill does.
        p = run(["python3", s.name] + argv, cwd=s.parent, timeout=600, check=False)
        report = ((p.stdout or b"") + (p.stderr or b"")).decode(errors="replace")
        body = {"ok": p.returncode == 0, "exitCode": p.returncode,
                "report": report[-8000:], "family": family}
        if b.get("autoRepair"):
            body["contentBase64"] = base64.b64encode(src.read_bytes()).decode()
            body["fileName"] = name
        return _json(body)


# ------------------------------------------------------------------- health
@app.route(route="health", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def health(req: func.HttpRequest) -> func.HttpResponse:
    tools = {t: bool(shutil.which(t)) for t in
             ("soffice", "pandoc", "pdftoppm", "pdftotext", "qpdf", "tesseract", "convert", "gcc")}
    staged = sorted(p.name for p in TOOLCHAIN.iterdir() if p.is_dir()) if TOOLCHAIN.is_dir() else []
    scripts = {k: (TOOLCHAIN / f / r).is_file() for k, (f, r) in FAMILY_SCRIPT.items()}
    return _json({"status": "ok" if all(tools[t] for t in ("soffice", "pdftoppm")) else "degraded",
                  "tools": tools, "toolchain": staged, "scripts": scripts,
                  "dataBoundary": os.environ.get("ENX_DATA_BOUNDARY", "EU")})
