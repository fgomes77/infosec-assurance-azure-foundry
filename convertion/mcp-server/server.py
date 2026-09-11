#!/usr/bin/env python3
"""InfoSec Assurance MCP server.

Exposes the Azure AI Foundry agent environment to any MCP client (Claude
Desktop/Code, the ENX gateway, internal tools):

    ask_orchestrator(prompt, thread_id?)   one entry point, routed
    ask_agent(agent, prompt, thread_id?)   a specific specialist agent
    list_agents()                          discover what is deployed
    save_memory(note)                      persist a durable team-memory note
    search_memory(query)                   ask the advisor what memory holds

Threads: pass back the thread_id a call returns to continue that
conversation with full context (this is the session memory; durable memory
lives in the vs-assurance-memory store).

Run locally (stdio):  python3 server.py
Auth: DefaultAzureCredential (az login / managed identity) +
PROJECT_ENDPOINT env var. See README.md for Azure Container Apps hosting.
"""

from __future__ import annotations

import datetime as dt
import os
import sys
import tempfile
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / "setup" / ".env")
except ImportError:
    pass

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("infosec-assurance")

ORCHESTRATOR = "infosec-assurance-orchestrator"
ADVISOR = "infosec-assurance-advisor"
MEMORY_STORE = "vs-assurance-memory"
_client = None


def agents_client():
    global _client
    if _client is None:
        from azure.ai.projects import AIProjectClient
        from azure.identity import DefaultAzureCredential
        endpoint = os.environ.get("PROJECT_ENDPOINT")
        if not endpoint:
            sys.exit("Set PROJECT_ENDPOINT")
        _client = AIProjectClient(endpoint=endpoint,
                                  credential=DefaultAzureCredential()).agents
    return _client


def _find_agent(name: str):
    for a in agents_client().list_agents():
        if a.name == name:
            return a
    raise ValueError(f"No agent named {name!r} is deployed")


def _run(agent_name: str, prompt: str, thread_id: str | None) -> dict:
    ac = agents_client()
    agent = _find_agent(agent_name)
    thread = (ac.threads.get(thread_id) if thread_id
              else ac.threads.create())
    ac.messages.create(thread_id=thread.id, role="user", content=prompt)
    run = ac.runs.create_and_process(thread_id=thread.id, agent_id=agent.id)
    if run.status != "completed":
        return {"thread_id": thread.id, "status": str(run.status),
                "error": str(run.last_error)}
    reply = ""
    for msg in ac.messages.list(thread_id=thread.id):
        if msg.role == "assistant":
            reply = "\n".join(p.text.value for p in msg.content
                              if getattr(p, "text", None))
            break
    return {"thread_id": thread.id, "status": "completed", "reply": reply}


@mcp.tool()
def ask_orchestrator(prompt: str, thread_id: str | None = None) -> dict:
    """Send an InfoSec Assurance request to the orchestrator, which answers
    directly or routes to the right specialist agent(s). Pass the returned
    thread_id on follow-ups to keep conversational context."""
    return _run(ORCHESTRATOR, prompt, thread_id)


@mcp.tool()
def ask_agent(agent: str, prompt: str, thread_id: str | None = None) -> dict:
    """Send a prompt to a specific deployed agent by name (see list_agents),
    e.g. 'dora', 'dpia', 'cyber-forum', 'infosec-assurance-advisor'."""
    return _run(agent, prompt, thread_id)


@mcp.tool()
def list_agents() -> list[dict]:
    """List the deployed InfoSec Assurance agents (name + description)."""
    return [{"name": a.name, "description": a.description or ""}
            for a in agents_client().list_agents()]


@mcp.tool()
def save_memory(note: str) -> str:
    """Persist a durable team-memory note (decision, supplier fact, agreed
    position) into the advisor's memory store. One self-contained fact per
    call; no special-category personal data."""
    ac = agents_client()
    store = next((v for v in ac.vector_stores.list()
                  if v.name == MEMORY_STORE), None)
    if store is None:
        return f"{MEMORY_STORE} not found — run create_orchestrator.py"
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / f"memory-{stamp}.txt"
        f.write_text(f"[{stamp}]\n{note.strip()}\n", encoding="utf-8")
        up = ac.files.upload_and_poll(file_path=str(f), purpose="assistants")
        ac.vector_store_files.create_and_poll(vector_store_id=store.id,
                                              file_id=up.id)
    return f"stored as {up.id}"


@mcp.tool()
def search_memory(query: str) -> dict:
    """Ask the advisor what the durable team memory holds about a topic or
    supplier (it searches the memory store and cites the notes found)."""
    return _run(ADVISOR,
                "Search ONLY the durable memory store and report what it "
                f"contains about: {query}. Quote the matching notes with "
                "their timestamps; do not answer from general knowledge.",
                None)


if __name__ == "__main__":
    mcp.run()
