"""Copilot / Teams wrapper Function for the ENX InfoSec Assurance platform.

Endpoints (integrations/copilot/openapi/ask.yaml):
  POST /api/ask                    - one question to ONE advisory agent on the GA
                                     conversations/responses data plane (finding C1),
                                     with the ROUTE: hand-off of finding C2
  POST /api/request_report         - start the report-delivery Logic App (async)
  GET  /api/report_status/{runId}  - status of a requested report
  POST /api/approval/subscribe     - approval-gate subscribe target (workflows' approvalWebhookUrl)
  GET  /api/approval/{id}          - minimal approval UI (draft summary + Approve/Reject)
  POST /api/approval/{id}/decide   - records the decision and calls the workflow back

Identity: Easy Auth (Entra) in front of every route; the caller UPN comes
from the X-MS-CLIENT-PRINCIPAL-NAME header (never from the body). The
Function calls Foundry and the Logic App with its MANAGED IDENTITY; for
user-scoped Graph reads it exchanges the caller's token on-behalf-of (OBO).
Approver checks use team/approval-policy.json (kind -> tier -> groups) via
Graph checkMemberGroups. No secrets in code: settings come from Key Vault
references. Deploy: copy this folder to functions/ask/ (or deploy as its own
Function App '{copilot-wrapper-function}') with host.json + requirements.txt.
"""
from __future__ import annotations

import base64
import html
import json
import logging
import os
import re
import time
import uuid

import azure.functions as func
import requests
from azure.data.tables import TableServiceClient
from azure.identity import DefaultAzureCredential, OnBehalfOfCredential

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)  # Easy Auth in front
_cred = DefaultAzureCredential()

PROJECT_ENDPOINT = os.environ.get("PROJECT_ENDPOINT", "")
API_VERSION = os.environ.get("FOUNDRY_API_VERSION", "v1")
# Finding C1/C19: the Agents v2 runtime addresses agents by NAME + immutable
# VERSION, never by an assistant id. ADVISORY_AGENT_VERSIONS_JSON is the
# deploy ledger build/agent-versions.json projected to {"<name>": "<version>"};
# an empty version means "latest", which a production surface should not use.
AGENT_VERSIONS = json.loads(os.environ.get("ADVISORY_AGENT_VERSIONS_JSON", "{}"))
ALLOWED_AGENTS = set(AGENT_VERSIONS) or set(
    json.loads(os.environ.get("ADVISORY_AGENT_NAMES_JSON", "[]")))
DEFAULT_AGENT = os.environ.get("DEFAULT_ADVISORY_AGENT", "infosec-assurance-advisor")
PIPELINE_TRIGGER_URLS = json.loads(os.environ.get("PIPELINE_TRIGGER_URLS_JSON", "{}"))  # {"deepsearch-report": "https://..."}
USERS_GROUP_ID = os.environ.get("ENTRA_GROUP_USERS_OBJECT_ID", "")
POLICY = json.loads(os.environ.get("APPROVAL_POLICY_JSON", "{}"))  # contents of team/approval-policy.json
TABLE_CONN = os.environ.get("STATE_TABLE_ENDPOINT", "")  # https://{storage}.table.core.windows.net
TEAMS_WEBHOOK = os.environ.get("TEAMS_APPROVAL_WEBHOOK_URL", "")
RUN_BUDGET_S = int(os.environ.get("ASK_RUN_BUDGET_SECONDS", "110"))
MAX_QUESTION = 8000

log = logging.getLogger("copilot-wrapper")


# ----------------------------------------------------------------- helpers
def _caller(req: func.HttpRequest) -> str:
    return req.headers.get("X-MS-CLIENT-PRINCIPAL-NAME", "")


def _bearer(req: func.HttpRequest) -> str:
    return req.headers.get("X-MS-TOKEN-AAD-ACCESS-TOKEN") or req.headers.get("Authorization", "").removeprefix("Bearer ")


def _json(body, status=200) -> func.HttpResponse:
    return func.HttpResponse(json.dumps(body), status_code=status, mimetype="application/json")


def _foundry_token() -> str:
    return _cred.get_token("https://ai.azure.com/.default").token


def _foundry(method: str, path: str, **kw) -> dict:
    r = requests.request(method, f"{PROJECT_ENDPOINT}{path}",
                         params={"api-version": API_VERSION},
                         headers={"Authorization": f"Bearer {_foundry_token()}"},
                         timeout=60, **kw)
    r.raise_for_status()
    return r.json() if r.text else {}


def _graph_as_user(user_token: str):
    """OBO credential for user-scoped Graph reads (Teams/Outlook/SharePoint)."""
    return OnBehalfOfCredential(tenant_id=os.environ["TENANT_ID"],
                                client_id=os.environ["WRAPPER_CLIENT_ID"],
                                client_assertion_func=lambda: os.environ["WRAPPER_FEDERATED_ASSERTION"],
                                user_assertion=user_token)


def _is_member(user_token: str, group_ids: list[str], as_app: bool = False) -> bool:
    if not group_ids:
        return False
    tok = _cred.get_token("https://graph.microsoft.com/.default").token if as_app \
        else _graph_as_user(user_token).get_token("https://graph.microsoft.com/.default").token
    r = requests.post("https://graph.microsoft.com/v1.0/me/checkMemberGroups",
                      headers={"Authorization": f"Bearer {tok}"},
                      json={"groupIds": group_ids}, timeout=30)
    return r.ok and set(r.json().get("value", [])) == set(group_ids)


def _table(name: str):
    svc = TableServiceClient(endpoint=TABLE_CONN, credential=_cred)
    svc.create_table_if_not_exists(name)
    return svc.get_table_client(name)


def _agent_reference(name: str) -> dict:
    """agent_reference body field of the Responses API, pinned to the promoted
    version when the deploy ledger knows one (finding C19)."""
    ref = {"type": "agent_reference", "name": name}
    version = AGENT_VERSIONS.get(name)
    if version:
        ref["version"] = str(version)
    return ref


_ROUTE_RE = re.compile(r"^ROUTE:\s*(\S+)\s*$", re.MULTILINE)


def _route_target(answer: str) -> str:
    m = _ROUTE_RE.search(answer or "")
    return m.group(1) if m else ""


def _respond(conv_id: str, agent: str, question: str, upn: str):
    """One turn on the GA responses surface; returns (text, citations, usage)."""
    resp = _foundry("POST", "/openai/v1/responses",
                    json={"conversation": conv_id, "input": question,
                          "agent_reference": _agent_reference(agent),
                          "metadata": {"requestedBy": upn}})
    deadline = time.time() + RUN_BUDGET_S
    while resp.get("status") in ("queued", "in_progress", "requires_action"):
        if time.time() > deadline:
            raise TimeoutError(conv_id)
        time.sleep(2)
        resp = _foundry("GET", f"/openai/v1/responses/{resp['id']}")
    if resp.get("status") not in (None, "completed"):
        raise RuntimeError(f"response {resp.get('status')}")
    answer = resp.get("output_text") or ""
    cites = []
    for item in resp.get("output", []) or []:
        for part in item.get("content", []) or []:
            if not answer and part.get("type") in ("output_text", "text"):
                answer += part.get("text", "") if isinstance(part.get("text"), str) \
                    else part.get("text", {}).get("value", "")
            for a in part.get("annotations", []) or []:
                url = a.get("url") or a.get("url_citation", {}).get("url", "")
                if url:
                    cites.append(url)
    return answer, cites, resp.get("usage")


# --------------------------------------------------------------------- /ask
@app.route(route="ask", methods=["POST"])
def ask(req: func.HttpRequest) -> func.HttpResponse:
    upn = _caller(req)
    if not upn or (USERS_GROUP_ID and not _is_member(_bearer(req), [USERS_GROUP_ID])):
        return _json({"error": "caller not in sg-infosec-foundry-users"}, 403)
    try:
        body = req.get_json()
    except ValueError:
        return _json({"error": "invalid json"}, 400)
    agent = body.get("agent") or DEFAULT_AGENT
    question = (body.get("question") or "").strip()
    if agent not in ALLOWED_AGENTS or not question or len(question) > MAX_QUESTION:
        return _json({"error": "unknown agent or empty/oversized question"}, 400)

    # "threadId" is accepted for one release as a deprecated alias of
    # "conversationId" (integrations/copilot/openapi/ask.yaml, finding C1).
    conv_id = body.get("conversationId") or body.get("threadId") or _foundry(
        "POST", "/openai/v1/conversations",
        json={"metadata": {"owner": upn, "channel": "copilot"}})["id"]

    try:
        answer, cites, usage = _respond(conv_id, agent, question, upn)
    except TimeoutError:
        return _json({"error": "response still in progress",
                      "conversationId": conv_id, "threadId": conv_id}, 504)
    except RuntimeError as exc:
        return _json({"error": str(exc), "conversationId": conv_id,
                      "threadId": conv_id}, 502)

    # Finding C2: Connected Agents no longer exist. The orchestrator answers with
    # a single line `ROUTE: <agent-name>`; the CALLER performs the hand-off as a
    # second response on that agent (orchestrator/README.md, mcp-server/server.py
    # and workflows/agent-fanout.json implement the same contract).
    route = _route_target(answer)
    if route and route in ALLOWED_AGENTS and route != agent:
        try:
            r_answer, r_cites, _ = _respond(conv_id, route, question, upn)
        except (TimeoutError, RuntimeError) as exc:
            return _json({"error": f"routed response failed: {exc}",
                          "conversationId": conv_id, "routedTo": route}, 502)
        log.info("ask route agent=%s -> %s user=%s conversation=%s", agent, route, upn, conv_id)
        return _json({"answer": r_answer, "conversationId": conv_id, "threadId": conv_id,
                      "agent": route, "routedFrom": agent,
                      "routing": answer.strip(),
                      "citations": [c for c in (cites + r_cites) if c]})

    log.info("ask agent=%s user=%s conversation=%s tokens=%s", agent, upn, conv_id, usage)
    return _json({"answer": answer, "conversationId": conv_id, "threadId": conv_id,
                  "agent": agent, "citations": [c for c in cites if c]})


# ------------------------------------------------------------ /request_report
@app.route(route="request_report", methods=["POST"])
def request_report(req: func.HttpRequest) -> func.HttpResponse:
    upn = _caller(req)
    if not upn or (USERS_GROUP_ID and not _is_member(_bearer(req), [USERS_GROUP_ID])):
        return _json({"error": "caller not in sg-infosec-foundry-users"}, 403)
    body = req.get_json()
    pipeline = body.get("pipeline")
    if pipeline not in PIPELINE_TRIGGER_URLS:
        return _json({"error": "unknown pipeline"}, 400)
    run_id = str(uuid.uuid4())
    payload = {
        "supplierName": body.get("supplierName"), "serviceName": body.get("serviceName"),
        "requestText": (body.get("requestText") or "")[:MAX_QUESTION],
        "inputFileIds": body.get("inputFileIds") or [], "requestedBy": upn,
        "callbackUrl": f"{os.environ.get('WRAPPER_BASE_URL', '')}/api/report_status/{run_id}",
    }
    tok = _cred.get_token("https://management.azure.com/.default").token  # Logic App trigger with MI (AAD-auth policy)
    r = requests.post(PIPELINE_TRIGGER_URLS[pipeline], json=payload,
                      headers={"Authorization": f"Bearer {tok}"}, timeout=30)
    if r.status_code >= 300:
        return _json({"error": "pipeline trigger failed", "status": r.status_code}, 502)
    _table("reportruns").upsert_entity({"PartitionKey": "run", "RowKey": run_id, "status": "running",
                                        "pipeline": pipeline, "requestedBy": upn,
                                        "supplierName": payload["supplierName"] or ""})
    return _json({"runId": run_id, "statusUrl": payload["callbackUrl"],
                  "message": "Report requested. It will be verified, approved by a human and stored in "
                             "SharePoint Reports/<Supplier>/<Service>/; you will be notified in Teams."}, 202)


@app.route(route="report_status/{runId}", methods=["GET", "POST"])
def report_status(req: func.HttpRequest) -> func.HttpResponse:
    run_id = req.route_params["runId"]
    tbl = _table("reportruns")
    if req.method == "POST":  # pipeline outcome callback (MI-authenticated Logic App)
        outcome = req.get_json()
        tbl.upsert_entity({"PartitionKey": "run", "RowKey": run_id, "status": outcome.get("status", "delivered"),
                           "webUrl": outcome.get("webUrl", ""), "shareUrl": outcome.get("shareUrl", ""),
                           "fileName": outcome.get("fileName", ""), "overallScore": str(outcome.get("overallScore", ""))})
        return _json({"ok": True})
    try:
        e = tbl.get_entity("run", run_id)
    except Exception:
        return _json({"error": "unknown runId"}, 404)
    return _json({k: v for k, v in e.items() if not k.startswith("odata") and k not in ("PartitionKey",)})


# --------------------------------------------------- approval gate (Layer 3)
@app.route(route="approval/subscribe", methods=["POST"])
def approval_subscribe(req: func.HttpRequest) -> func.HttpResponse:
    """Target of every workflow's approvalWebhookUrl (workflows/README.md contract)."""
    sub = req.get_json()
    aid = str(uuid.uuid4())
    tier = POLICY.get("kinds", {}).get(sub.get("kind", ""), {}).get("tier", "A")
    _table("approvals").upsert_entity({
        "PartitionKey": "approval", "RowKey": aid, "callbackUrl": sub["callbackUrl"],
        "kind": sub.get("kind", ""), "tier": tier, "requestedBy": sub.get("requestedBy", ""),
        "correlationId": sub.get("correlationId", ""), "draft": json.dumps(sub.get("draft", sub))[:60000],
        "decision": "", "approver": "", "createdAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
    link = f"{os.environ.get('WRAPPER_BASE_URL', '')}/api/approval/{aid}"
    if TEAMS_WEBHOOK:
        requests.post(TEAMS_WEBHOOK, json={"text": f"Approval requested ({sub.get('kind')}) by {sub.get('requestedBy')}: {link}"}, timeout=15)
    return _json({"approvalId": aid, "url": link}, 202)


@app.route(route="approval/{id}", methods=["GET"])
def approval_page(req: func.HttpRequest) -> func.HttpResponse:
    e = _table("approvals").get_entity("approval", req.route_params["id"])
    draft = html.escape(json.dumps(json.loads(e["draft"]), indent=2, ensure_ascii=False))
    page = (f"<h2>Approval {e['RowKey']} - {html.escape(e['kind'])} (tier {e['tier']})</h2>"
            f"<p>Requested by {html.escape(e['requestedBy'])}. Decision: {html.escape(e['decision'] or 'pending')}</p>"
            f"<pre style='white-space:pre-wrap;max-height:60vh;overflow:auto'>{draft}</pre>"
            f"<form method='post' action='/api/approval/{e['RowKey']}/decide'>"
            "<button name='decision' value='approved'>Approve</button> "
            "<button name='decision' value='rejected'>Reject</button> "
            "<input name='comment' placeholder='comment'></form>")
    return func.HttpResponse(page, mimetype="text/html")


@app.route(route="approval/{id}/decide", methods=["POST"])
def approval_decide(req: func.HttpRequest) -> func.HttpResponse:
    upn = _caller(req)
    tbl = _table("approvals")
    e = tbl.get_entity("approval", req.route_params["id"])
    if e["decision"]:
        return _json({"error": "already decided"}, 409)
    form = req.form if req.form else req.get_json()
    decision = "approved" if (form.get("decision") == "approved") else "rejected"
    tier = POLICY.get("tiers", {}).get(e["tier"], {})
    groups = [POLICY["groups"][g]["object_id"] for g in tier.get("approver_groups", []) if g in POLICY.get("groups", {})]
    if not upn or (upn.lower() == (e["requestedBy"] or "").lower() and not tier.get("self_approval", False)):
        return _json({"error": "self-approval not allowed"}, 403)
    if not _is_member(_bearer(req), groups):
        return _json({"error": "approver not in the required group(s)"}, 403)
    tbl.update_entity({"PartitionKey": "approval", "RowKey": e["RowKey"], "decision": decision, "approver": upn,
                       "decidedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                       "comment": str(form.get("comment", ""))[:2000]})
    r = requests.post(e["callbackUrl"], json={"decision": decision, "approver": upn,
                                              "comment": str(form.get("comment", ""))[:2000]}, timeout=30)
    log.info("approval %s kind=%s decision=%s approver=%s callback=%s", e["RowKey"], e["kind"], decision, upn, r.status_code)
    return _json({"decision": decision, "approver": upn, "callbackStatus": r.status_code})
