#!/usr/bin/env python3
"""InfoSec Assurance MCP server.

Exposes the Microsoft Foundry (formerly Azure AI Foundry) agent environment
to any MCP client (Claude Desktop/Code, the ENX gateway, internal tools):

    ask_orchestrator(prompt, conversation_id?)  one entry point, routed
    ask_agent(agent, prompt, conversation_id?)  a specific specialist agent
    list_agents()                               discover what is deployed
    save_memory(note)                           persist a durable team-memory note
    search_memory(query)                        ask the advisor what memory holds

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

import os
import re
import sys
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


if __name__ == "__main__":
    # stdio for a local client; `streamable-http` for the shared Container
    # Apps endpoint (README.md) — set by MCP_TRANSPORT so the hosted image is
    # the same code as the desktop one.
    mcp.run(transport=os.environ.get("MCP_TRANSPORT", "stdio"))
