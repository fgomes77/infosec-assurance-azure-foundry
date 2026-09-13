#!/usr/bin/env python3
"""InfoSec Assurance MCP server.

Exposes the Microsoft Foundry (formerly Azure AI Foundry) agent environment
to any MCP client (Claude Desktop/Code, the ENX gateway, internal tools):

    ask_orchestrator(prompt, conversation_id?)  one entry point, routed
    ask_agent(agent, prompt, conversation_id?)  a specific specialist agent
    list_agents()                               discover what is deployed
    save_memory(note)                           persist a durable team-memory note
    search_memory(query)                        ask the advisor what memory holds
    schedule_followup(...)                      re-open a conversation later

Runtime (finding C1). Every data-plane call goes through
`../scripts/_foundry_runtime.py`, the same adapter the deploy scripts use:
the GA **Responses API** (agents / conversations / responses,
`api-version=v1`) with the classic threads/runs runtime as a documented
fallback until it retires **2027-03-31**. Conversations replace threads:
pass back the `conversation_id` a call returns to continue that
conversation with full context (`thread_id` is still accepted and still
returned as a deprecated alias so existing client configurations keep
working). Answers are pinned to the promoted agent version `<name>:<n>`
(finding C19) — the reply carries the `agent_ref` that produced it.

Durable memory follows `MEMORY_BACKEND` (setup/.env): the
`vs-assurance-memory` vector store (transition default) or the Azure AI
Search index `MEMORY_INDEX_NAME` — the service allows one vector store per
agent, so shared knowledge lives in Search (finding C3).

Run locally (stdio):  python3 server.py
Hosted (streamable HTTP):  MCP_TRANSPORT=streamable-http python3 server.py
Auth: DefaultAzureCredential (az login / managed identity) +
PROJECT_ENDPOINT env var. See README.md for Azure Container Apps hosting.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONV = HERE.parent
# The runtime adapter and the memory backend are shared with the deploy
# scripts — never forked here (a hosted image must copy ../scripts/ too;
# see README.md "Shared hosting").
sys.path.insert(0, str(CONV / "scripts"))

try:
    from dotenv import load_dotenv
    load_dotenv(CONV / "setup" / ".env")
except ImportError:
    pass

from mcp.server.fastmcp import FastMCP  # noqa: E402

from _foundry_runtime import (get_runtime, memory_backend,  # noqa: E402
                              runtime_banner)

mcp = FastMCP("infosec-assurance")

ORCHESTRATOR = "infosec-assurance-orchestrator"
ADVISOR = "infosec-assurance-advisor"
MEMORY_STORE = "vs-assurance-memory"
_runtime = None


def runtime():
    """Lazy Foundry handle (Responses API, classic fallback)."""
    global _runtime
    if _runtime is None:
        if not os.environ.get("PROJECT_ENDPOINT"):
            raise RuntimeError("Set PROJECT_ENDPOINT (setup/.env)")
        _runtime = get_runtime()
        print(runtime_banner(), file=sys.stderr)
    return _runtime


def _find_agent(name: str):
    agents = runtime().list_agents()
    if name not in agents:
        raise ValueError(f"No agent named {name!r} is deployed")
    return agents[name]


def _run(agent_name: str, prompt: str, conversation_id: str | None) -> dict:
    rt = runtime()
    agent = _find_agent(agent_name)
    try:
        conv, reply = rt.ask(agent, prompt, conversation_id)
    except Exception as exc:  # noqa: BLE001 - report, never crash the server
        return {"conversation_id": conversation_id, "thread_id": conversation_id,
                "agent_ref": agent.ref, "status": "failed", "error": str(exc)}
    return {"conversation_id": conv,
            "thread_id": conv,          # deprecated alias (classic clients)
            "agent_ref": agent.ref,     # pinned <name>:<version> (C19)
            "status": "completed", "reply": reply}


_ROUTE_RE = re.compile(r"^ROUTE:\s*(\S+)\s*$", re.MULTILINE)


@mcp.tool()
def ask_orchestrator(prompt: str, conversation_id: str | None = None,
                     thread_id: str | None = None) -> dict:
    """Send an InfoSec Assurance request to the orchestrator, which answers
    directly or routes to the right specialist agent(s). Pass the returned
    conversation_id on follow-ups to keep context (thread_id is the
    deprecated name of the same value)."""
    first = _run(ORCHESTRATOR, prompt, conversation_id or thread_id)
    if first.get("status") != "completed":
        return first
    # Finding C2: Connected Agents do not exist on the Agents v2 runtime.
    # create_orchestrator.py injects a deploy-time ROUTING TABLE into the
    # orchestrator's instructions; the orchestrator answers `ROUTE: <agent>`
    # and the CALLER performs the hand-off as a second responses.create on
    # that agent, in the SAME conversation so context is preserved.
    match = _ROUTE_RE.search(first.get("reply") or "")
    if not match:
        return first
    target = match.group(1)
    if target in (ORCHESTRATOR, ""):
        return first
    try:
        second = _run(target, prompt, first["conversation_id"])
    except ValueError as exc:      # routed to an agent that is not deployed
        first["routing_error"] = str(exc)
        return first
    second["routing"] = first.get("reply", "").strip()
    second["routed_from"] = first.get("agent_ref", ORCHESTRATOR)
    second["routed_to"] = second.get("agent_ref", target)
    return second


@mcp.tool()
def ask_agent(agent: str, prompt: str, conversation_id: str | None = None,
              thread_id: str | None = None) -> dict:
    """Send a prompt to a specific deployed agent by name (see list_agents),
    e.g. 'dora', 'dpia', 'cyber-forum', 'infosec-assurance-advisor'."""
    return _run(agent, prompt, conversation_id or thread_id)


@mcp.tool()
def list_agents() -> list[dict]:
    """List the deployed InfoSec Assurance agents (name, promoted version
    reference and description)."""
    return [{"name": a.name, "ref": a.ref, "version": a.version,
             "description": a.description}
            for a in runtime().list_agents().values()]


@mcp.tool()
def catalog(area: str = "") -> dict:
    """The platform's own catalogue: every system (a-j), agent, pipeline,
    workflow, connection, template, dashboard query and runbook, each with
    what it is and where it lives — the same inventory the ENX Assurance
    Console page shows, so a chat client and the page can never disagree.

    Pass `area` to narrow: systems | develop | agents | pipelines | workflows |
    connections | templates | queries | docs. Omit it for everything.

    Answer capability questions from THIS, never from memory: it is generated
    from the registries, so it describes the platform as deployed rather than
    as remembered.
    """
    path = Path(__file__).resolve().parent.parent / "build" / "console" / "catalog.json"
    if not path.is_file():
        return {"error": "catalogue not built",
                "fix": "python3 scripts/build_console.py (deploy.sh runs it)"}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not area:
        return data
    if area not in data:
        return {"error": f"unknown area {area!r}",
                "areas": [k for k in data if k != "generated"]}
    return {"generated": data["generated"], area: data[area]}


@mcp.tool()
def save_memory(note: str, subject: str = "", author: str = "") -> str:
    """Persist a durable team-memory note (decision, supplier fact, agreed
    position) into the team's durable memory. One self-contained fact per
    call; no special-category or personal data.

    `subject` is the deletion handle — use the SharePoint `<Supplier>` or
    `<Supplier>/<Service>` name for supplier notes so a later GDPR Art. 17
    request can delete by subject (governance/MEMORY_POLICY.md §2). `author`
    is the caller's UPN; it is written into the note header. The reply names
    the stored note's id, so the caller can cite what to delete without a
    separate `memory_store.py list` run (delta D-MI-M1)."""
    text = note.strip()
    if not text:
        return "nothing to store"
    try:
        from memory_store import (SPECIAL_CATEGORY, SearchBackend,
                                  find_store, store_note)
        if SPECIAL_CATEGORY.search(text):
            return ("rejected: the note contains special-category or "
                    "personal data (governance/MEMORY_POLICY.md)")
        subj = subject.strip()
        who = author.strip() or os.environ.get("MEMORY_AUTHOR_UPN", "")
        if memory_backend() == "search-index":
            note_id = SearchBackend().add(text, author=who, subject=subj)
        else:
            rt = runtime()
            note_id = store_note(rt, find_store(rt), text,
                                 author=who, subject=subj)
        return (f"stored as {note_id} — delete it with "
                f"`memory_store.py delete {note_id.split()[0]}`")
    except SystemExit as exc:   # memory_store exits on missing config
        return f"not stored: {exc}"
    except Exception as exc:    # noqa: BLE001
        return f"not stored: {exc}"


@mcp.tool()
def search_memory(query: str) -> dict:
    """Ask the advisor what the durable team memory holds about a topic or
    supplier (it searches the memory backend and cites the notes found)."""
    return _run(ADVISOR,
                "Search ONLY the durable memory (memory store / memory "
                f"index) and report what it contains about: {query}. Quote "
                "the matching notes with their timestamps; do not answer "
                "from general knowledge.",
                None)


MAX_FOLLOWUP_DAYS = 90      # Logic Apps Wait limit (scheduled-followup.json)


@mcp.tool()
def schedule_followup(conversation_id: str, agent_ref: str, fire_at: str,
                      prompt: str, requested_by: str = "") -> str:
    """Schedule ONE follow-up run of a deployed agent inside an existing
    conversation, at a future time (max 90 days ahead) — the platform
    replacement for a one-shot "remind me / re-check this later" Routine.

    `conversation_id` is the value a previous ask_* call returned;
    `agent_ref` is `<agent-name>:<version>` (list_agents `ref`) or a bare
    name for the latest version; `fire_at` is an RFC3339 UTC timestamp.
    When it fires, the agent answers IN that conversation and the requester
    is notified on Teams — nothing is written to SharePoint, Jira, OneTrust
    or any other system of record, which is why scheduling needs no approval
    gate (governance/HUMAN_APPROVAL.md). A deliverable still goes through
    the delivery pipeline, the output-verifier and a human approval.

    Contract: integrations/openapi/followup-scheduler.yaml; workflow:
    workflows/scheduled-followup.json. The trigger URL (with its shared
    access signature) is FOLLOWUP_SCHEDULER_URL in setup/.env / Key Vault —
    absent, this tool says so instead of pretending to have scheduled.
    """
    url = os.environ.get("FOLLOWUP_SCHEDULER_URL", "").strip()
    if not url:
        return ("not scheduled: FOLLOWUP_SCHEDULER_URL is not set (setup/.env "
                "— the scheduled-followup Logic App trigger URL from Key "
                "Vault). Nothing was scheduled.")
    if not url.lower().startswith("https://"):
        return "not scheduled: FOLLOWUP_SCHEDULER_URL must be https"
    stamp = fire_at.strip().replace("Z", "+00:00")
    try:
        when = dt.datetime.fromisoformat(stamp)
    except ValueError:
        return (f"not scheduled: fire_at {fire_at!r} is not an RFC3339 "
                f"timestamp (e.g. 2026-12-01T09:00:00Z)")
    if when.tzinfo is None:
        when = when.replace(tzinfo=dt.timezone.utc)
    now = dt.datetime.now(dt.timezone.utc)
    if when <= now:
        return f"not scheduled: fire_at {fire_at!r} is in the past"
    if (when - now).days > MAX_FOLLOWUP_DAYS:
        return (f"not scheduled: fire_at is more than {MAX_FOLLOWUP_DAYS} "
                f"days ahead (Logic Apps Wait limit)")
    if not conversation_id.strip() or not agent_ref.strip():
        return "not scheduled: conversation_id and agent_ref are required"
    if not prompt.strip():
        return "not scheduled: prompt is required (what should the agent do?)"
    who = requested_by.strip() or os.environ.get("MEMORY_AUTHOR_UPN", "")
    if not who:
        return ("not scheduled: requested_by is required (the UPN the Teams "
                "notification goes to; set MEMORY_AUTHOR_UPN in setup/.env "
                "for a single-user client)")
    body = json.dumps({
        "conversationId": conversation_id.strip(),
        "agentRef": agent_ref.strip(),
        "fireAt": when.astimezone(dt.timezone.utc)
                      .strftime("%Y-%m-%dT%H:%M:%SZ"),
        "prompt": prompt.strip(),
        "requestedBy": who,
    }).encode("utf-8")
    req = urllib.request.Request(
        url, data=body, method="POST",
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:   # noqa: S310
            payload = json.loads(resp.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as exc:
        return (f"not scheduled: the scheduler returned HTTP {exc.code} "
                f"({exc.reason})")
    except Exception as exc:    # noqa: BLE001 - network/DNS/timeout
        return f"not scheduled: {exc}"
    ref = payload.get("followupId", "(no id returned)")
    return (f"scheduled as {ref} for {payload.get('fireAt', fire_at)} on "
            f"{agent_ref} in conversation {conversation_id} — the answer "
            f"appears in that conversation and as a Teams notification")


if __name__ == "__main__":
    # stdio for a local client; `streamable-http` for the shared Container
    # Apps endpoint (README.md) — set by MCP_TRANSPORT so the hosted image is
    # the same code as the desktop one.
    mcp.run(transport=os.environ.get("MCP_TRANSPORT", "stdio"))
