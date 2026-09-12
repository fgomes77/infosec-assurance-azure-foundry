"""Foundry data-plane runtime used by every script in this folder (C1, C19).

WHY
  The classic Agent Service runtime (threads + runs, `azure-ai-agents`
  `AgentsClient`) retires **2027-03-31**; the GA service is
  agents / conversations / responses on `azure-ai-projects` 2.x with REST
  `api-version=v1` (enterprise/series/06-agents-conversion-and-deploy.md
  §A; enterprise/ENTERPRISE_BLUEPRINT.md finding C1).

WHAT
  One adapter with two modes, selected from the installed SDK and
  overridable with `FOUNDRY_RUNTIME=responses|classic`:

    responses  azure-ai-projects >= 2 — `agents.create_version(...)` plus
               `conversations` / `responses` through the project's OpenAI
               client. Every save is an immutable version `<name>:<n>`;
               the pinned wire version is `FOUNDRY_API_VERSION`
               (setup/.env, default `v1`).
    classic    azure-ai-projects 1.x + azure-ai-agents 1.x —
               `create_agent` / `update_agent` + threads/runs on
               api-version `2025-05-01`.
               **DOCUMENTED FALLBACK ONLY.** It exists so an environment
               still pinned to the previous `setup/requirements.txt`
               keeps deploying while it is upgraded; it must be gone
               before the retirement date. `deploy.sh` step [0b] prints a
               warning whenever a run takes this path.

  Both modes are presented to the callers with the SAME surface, so
  `_azure_helpers.py` (uploads, vector-store reconciliation) is unchanged:
  `.files`, `.vector_stores`, `.vector_store_files` always answer to the
  classic method names.

VERSIONS (C19)
  `record_version()` writes `build/agent-versions.json` — the promoted
  `<agent>:<version>` of every agent this deploy created. Pipelines pin
  that reference (`workflows/pipelines.json`), `verify_deployment.py`
  compares the live version against it, and `update_templates.py` records
  the version a template change promoted. In `classic` mode the service
  has no versions; the ledger stores `version: null` and the comparison is
  reported as "not versioned by this runtime" instead of as drift.

  `build/` is git-ignored, so the ledger is a DEPLOY ARTEFACT: the release
  pipeline must publish `build/agent-versions.json` with the run (it is the
  ISMS evidence that links a release tag to the versions serving traffic)
  and restore it before the nightly `verify_deployment.py`. Without it the
  drift check still runs and simply skips the version comparison.
"""

from __future__ import annotations

import datetime as dt
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUILD = HERE.parent / "build"

# Pinned Foundry data-plane version. `v1` is the GA agents/conversations/
# responses surface; the fallback below is the classic threads/runs one.
# Kept identical to the Logic Apps app setting of the same name
# (workflows/README.md) so scripts and workflows never disagree.
API_VERSION = os.environ.get("FOUNDRY_API_VERSION", "v1")
LEGACY_API_VERSION = "2025-05-01"

VERSION_LEDGER = BUILD / "agent-versions.json"


# -------------------------------------------------- knowledge source (C3)
def knowledge_source() -> dict:
    """Where cross-agent ("combined") knowledge is served from.

    The service allows exactly ONE vector store per agent (limits page,
    2026-09-07), so the advisory profile's old design — the agent's own
    `vs-<agent>` PLUS `vs-assurance-combined` on the same file_search tool
    — is invalid (finding C3). The per-agent store stays; everything
    shared moves to an Azure AI Search index / Foundry IQ knowledge base
    reached through the GA Azure AI Search tool.

    `KNOWLEDGE_SOURCE` (setup/.env):
      vector-store  default / transition — per-agent store only; combined
                    knowledge is reached by ROUTE-ing to the advisor,
                    which holds `vs-assurance-combined` as its one store
      ai-search     attach the Azure AI Search tool for
                    `KNOWLEDGE_INDEX_NAME` over the project connection
                    `SEARCH_CONNECTION_NAME` (category CognitiveSearch)
      none          no combined grounding at all (isolated environments)
    """
    return {
        "mode": (os.environ.get("KNOWLEDGE_SOURCE", "vector-store")
                 .strip().lower() or "vector-store"),
        "connection": os.environ.get("SEARCH_CONNECTION_NAME", "ai-search"),
        "endpoint": os.environ.get("SEARCH_SERVICE_ENDPOINT", ""),
        # KNOWLEDGE_BASE_NAME is the name used by
        # enterprise/memory-learning/MEMORY_LEARNING_RESEARCH.md §4; both
        # spellings are accepted so docs and .env cannot drift apart.
        "index": (os.environ.get("KNOWLEDGE_INDEX_NAME")
                  or os.environ.get("KNOWLEDGE_BASE_NAME")
                  or "kb-assurance"),
        "memory_index": os.environ.get("MEMORY_INDEX_NAME",
                                       "kb-assurance-memory"),
    }


def memory_backend() -> str:
    """`vector-store` (transition default) or `search-index`
    (enterprise/MEMORY_AND_LEARNING.md §2, delta D-ML-2/D-ML-3)."""
    return (os.environ.get("MEMORY_BACKEND", "vector-store")
            .strip().lower() or "vector-store")


def ai_search_tool(connection_id: str, index_name: str) -> list:
    """Azure AI Search tool definitions, or [] when this SDK has no such
    tool (then the caller prints the documented fallback and continues)."""
    try:
        from azure.ai.agents.models import (AzureAISearchTool,
                                            AzureAISearchQueryType)
        return AzureAISearchTool(
            index_connection_id=connection_id, index_name=index_name,
            query_type=AzureAISearchQueryType.VECTOR_SEMANTIC_HYBRID,
        ).definitions
    except Exception:  # noqa: BLE001 - SDK shape varies across majors
        try:
            from azure.ai.agents.models import AzureAISearchTool
            return AzureAISearchTool(index_connection_id=connection_id,
                                     index_name=index_name).definitions
        except Exception:  # noqa: BLE001
            return []


# --------------------------------------------------------------- SDK probing
def sdk_version() -> str:
    try:
        import azure.ai.projects as p
        return str(getattr(p, "__version__", "") or "")
    except ImportError:
        return ""


def sdk_major() -> int:
    v = sdk_version().split(".")[0]
    return int(v) if v.isdigit() else 0


def runtime_mode() -> str:
    """"responses" (GA) or "classic" (fallback). FOUNDRY_RUNTIME wins."""
    forced = os.environ.get("FOUNDRY_RUNTIME", "").strip().lower()
    if forced in ("responses", "classic"):
        return forced
    return "responses" if sdk_major() >= 2 else "classic"


def runtime_banner() -> str:
    mode = runtime_mode()
    if mode == "responses":
        return (f"runtime: responses API (azure-ai-projects {sdk_version()}, "
                f"api-version={API_VERSION})")
    return (f"runtime: CLASSIC threads/runs FALLBACK "
            f"(azure-ai-projects {sdk_version() or 'not installed'}, "
            f"api-version={LEGACY_API_VERSION}) — retires 2027-03-31; "
            f"upgrade setup/requirements.txt to azure-ai-projects>=2.3.0,<3")


# ------------------------------------------------------- OpenAI-client shims
# The 2.x SDK serves files and vector stores through the project's OpenAI
# client. These wrappers re-expose them under the classic method names so
# _azure_helpers.py, memory_store.py and cleanup_foundry.py are unchanged.
class _FilesShim:
    def __init__(self, oai):
        self._o = oai

    def upload_and_poll(self, *, file_path, purpose="assistants"):
        with open(file_path, "rb") as fh:
            return self._o.files.create(file=fh, purpose=purpose)

    def delete(self, file_id):
        return self._o.files.delete(file_id)

    def list(self, **kw):
        return list(self._o.files.list(**kw))


class _VectorStoresShim:
    def __init__(self, oai):
        self._o = oai

    def list(self):
        return list(self._o.vector_stores.list())

    def create_and_poll(self, *, name, file_ids=None):
        return self._o.vector_stores.create(name=name,
                                            file_ids=list(file_ids or []))

    def delete(self, vector_store_id):
        return self._o.vector_stores.delete(vector_store_id)


class _VectorStoreFilesShim:
    def __init__(self, oai):
        self._o = oai

    def list(self, *, vector_store_id):
        return list(self._o.vector_stores.files.list(
            vector_store_id=vector_store_id))

    def create_and_poll(self, *, vector_store_id, file_id):
        return self._o.vector_stores.files.create(
            vector_store_id=vector_store_id, file_id=file_id)

    def delete(self, *, vector_store_id, file_id):
        return self._o.vector_stores.files.delete(
            vector_store_id=vector_store_id, file_id=file_id)


# ------------------------------------------------------------- agent reading
class AgentView:
    """Normalised read view of a live agent.

    In `responses` mode instructions/model/tools live on the version
    definition (`agent.definition` or `agent.latest_version.definition`);
    in `classic` mode they are attributes of the agent itself. Callers
    read this view and never branch on the runtime.
    """

    def __init__(self, raw, mode: str):
        self.raw = raw
        self.mode = mode
        d = (getattr(raw, "definition", None)
             or getattr(getattr(raw, "latest_version", None), "definition", None)
             or raw)
        self.definition = d
        self.name = getattr(raw, "name", "") or getattr(d, "name", "") or ""
        self.id = getattr(raw, "id", "") or self.name
        ver = getattr(raw, "version", None)
        if ver is None:
            ver = getattr(getattr(raw, "latest_version", None), "version", None)
        self.version = None if ver is None else str(ver)
        self.model = getattr(d, "model", None) or getattr(raw, "model", "") or ""
        self.instructions = (getattr(d, "instructions", None)
                             or getattr(raw, "instructions", "") or "")
        self.tools = list(getattr(d, "tools", None)
                          or getattr(raw, "tools", None) or [])
        self.tool_resources = (getattr(d, "tool_resources", None)
                               if getattr(d, "tool_resources", None) is not None
                               else getattr(raw, "tool_resources", None))
        self.description = (getattr(d, "description", None)
                            or getattr(raw, "description", "") or "")

    @property
    def ref(self) -> str:
        """`<name>:<version>` — what pipelines pin (C19)."""
        return f"{self.name}:{self.version}" if self.version else self.name

    def __repr__(self) -> str:  # deploy logs
        return f"<agent {self.ref}>"


# ------------------------------------------------------------------- runtime
class Runtime:
    """The single data-plane handle the scripts use."""

    def __init__(self, endpoint: str):
        from azure.identity import DefaultAzureCredential
        from azure.ai.projects import AIProjectClient
        self.mode = runtime_mode()
        self.endpoint = endpoint
        kwargs = {"endpoint": endpoint, "credential": DefaultAzureCredential()}
        try:  # the 2.x client accepts the pinned wire version; 1.x does not
            self.project = AIProjectClient(api_version=API_VERSION, **kwargs)
        except TypeError:
            self.project = AIProjectClient(**kwargs)
        self._oai = None
        if self.mode == "responses":
            self._oai = self.project.get_openai_client()
            self.files = _FilesShim(self._oai)
            self.vector_stores = _VectorStoresShim(self._oai)
            self.vector_store_files = _VectorStoreFilesShim(self._oai)
        else:
            ac = self.project.agents
            self.files = ac.files
            self.vector_stores = ac.vector_stores
            self.vector_store_files = ac.vector_store_files

    # -- agents ------------------------------------------------------------
    def list_agents(self) -> dict[str, AgentView]:
        src = (self.project.agents.list() if self.mode == "responses"
               else self.project.agents.list_agents())
        out: dict[str, AgentView] = {}
        for a in src:
            v = AgentView(a, self.mode)
            if v.name:
                out[v.name] = v
        return out

    def upsert_agent(self, *, name: str, model: str, instructions: str,
                     tools=None, tool_resources=None, description: str = "",
                     metadata: dict | None = None,
                     existing: AgentView | None = None) -> AgentView:
        """Create the agent or save a new version of it.

        `responses`: one immutable version per call (previous versions are
        kept and can be re-activated — the rollback in series/06 §G).
        `classic`: create or update in place (no versions exist).
        """
        if self.mode == "responses":
            from azure.ai.projects.models import PromptAgentDefinition
            definition = PromptAgentDefinition(
                model=model, instructions=instructions,
                tools=list(tools or []) or None,
                tool_resources=tool_resources or None,
                description=description or None)
            created = self.project.agents.create_version(
                agent_name=name, definition=definition,
                metadata=metadata or None)
            return AgentView(created, self.mode)
        kwargs = dict(model=model, name=name,
                      description=description or None,
                      instructions=instructions,
                      tools=list(tools or []) or None,
                      tool_resources=tool_resources or None,
                      metadata=metadata or None)
        ac = self.project.agents
        raw = (ac.update_agent(existing.id, **kwargs) if existing
               else ac.create_agent(**kwargs))
        return AgentView(raw, self.mode)

    # -- connections --------------------------------------------------------
    def connection_id(self, name: str) -> str | None:
        """Id of a project connection by name (AI Search, Bing, ...).
        None when it does not exist — callers degrade, never crash."""
        try:
            return self.project.connections.get(name=name).id
        except Exception:  # noqa: BLE001 - absent connection / older SDK
            return None

    # -- conversation -------------------------------------------------------
    def ask(self, agent: AgentView, prompt: str,
            conversation_id: str | None = None) -> tuple[str, str]:
        """One turn. Returns (conversation/thread id, assistant text)."""
        if self.mode == "responses":
            conv = conversation_id or self._oai.conversations.create().id
            ref = {"name": agent.name, "type": "agent_reference"}
            if agent.version:
                ref["version"] = agent.version     # pin the promoted version
            resp = self._oai.responses.create(
                conversation=conv, input=prompt,
                extra_body={"agent_reference": ref})
            if getattr(resp, "status", "completed") not in ("completed", None):
                raise RuntimeError(f"response status {resp.status}: "
                                   f"{getattr(resp, 'error', None)}")
            return conv, (getattr(resp, "output_text", "") or "")
        ac = self.project.agents
        thread_id = conversation_id or ac.threads.create().id
        ac.messages.create(thread_id=thread_id, role="user", content=prompt)
        run = ac.runs.create_and_process(thread_id=thread_id,
                                         agent_id=agent.id)
        if run.status != "completed":
            raise RuntimeError(f"run status {run.status}: {run.last_error}")
        for msg in ac.messages.list(thread_id=thread_id):
            if msg.role == "assistant":
                return thread_id, "\n".join(
                    p.text.value for p in msg.content
                    if getattr(p, "text", None))
        return thread_id, ""


def get_runtime(endpoint: str | None = None) -> Runtime:
    import sys
    endpoint = endpoint or os.environ.get("PROJECT_ENDPOINT")
    if not endpoint:
        sys.exit("Set PROJECT_ENDPOINT (setup/.env) — printed by provision.sh")
    rt = Runtime(endpoint)
    print(runtime_banner())
    return rt


# ------------------------------------------------------- version ledger (C19)
def read_ledger() -> dict:
    try:
        return json.loads(VERSION_LEDGER.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"agents": {}}


def record_version(agent: AgentView, *, note: str = "") -> None:
    """Merge one agent into build/agent-versions.json (the deployed set)."""
    led = read_ledger()
    led.setdefault("agents", {})[agent.name] = {
        "version": agent.version,
        "ref": agent.ref,
        "id": agent.id,
        "model": agent.model,
        "runtime": agent.mode,
        "note": note or None,
    }
    led["_kit_release"] = os.environ.get("KIT_RELEASE", "unversioned")
    led["_api_version"] = (API_VERSION if runtime_mode() == "responses"
                           else LEGACY_API_VERSION)
    led["_generated"] = dt.datetime.now(dt.timezone.utc).isoformat(
        timespec="seconds")
    VERSION_LEDGER.parent.mkdir(parents=True, exist_ok=True)
    VERSION_LEDGER.write_text(json.dumps(led, indent=1, sort_keys=True) + "\n",
                              encoding="utf-8")


def pinned_ref(name: str) -> str | None:
    """`<name>:<version>` recorded by the last deploy, or None."""
    entry = read_ledger().get("agents", {}).get(name) or {}
    return entry.get("ref")
