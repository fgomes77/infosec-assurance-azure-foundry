# InfoSec Assurance MCP Server

Exposes the Foundry agent environment as MCP tools so any MCP client —
Claude Desktop / Claude Code, the ENX gateway, or internal tooling — can
drive it: `ask_orchestrator`, `ask_agent`, `list_agents`, `save_memory`,
`search_memory`. Context persists via the returned `conversation_id`
(`thread_id` remains as a deprecated alias of the same value); durable team
memory follows `MEMORY_BACKEND` — the `vs-assurance-memory` store or the
Azure AI Search memory index (finding C3).

**Runtime (finding C1).** `server.py` does not call the SDK directly: it
imports `../scripts/_foundry_runtime.py`, the adapter the deploy scripts
use, so the server speaks the GA **Responses API** (agents /
conversations / responses, `api-version=v1`) and falls back to the classic
threads/runs runtime only where an environment is still pinned to it —
that runtime retires **2027-03-31**. Every reply carries `agent_ref`, the
promoted `<agent>:<version>` that produced it (finding C19). Consequence
for packaging: the server needs `../scripts/` and `../setup/.env` next to
it (see hosting below).

## Run locally (per team member, stdio)

```bash
pip install -r requirements.txt
az login                      # DefaultAzureCredential
export PROJECT_ENDPOINT=...   # or use ../setup/.env
python3 server.py
```

Claude Desktop / Claude Code registration (`mcpServers` entry):

```json
{
  "infosec-assurance": {
    "command": "python3",
    "args": ["/path/to/convertion/mcp-server/server.py"],
    "env": { "PROJECT_ENDPOINT": "https://<account>.services.ai.azure.com/api/projects/<project>" }
  }
}
```

Each user's own Entra identity (az login) is used — access follows the
Azure AI User role assignments, so revoking a person in Entra revokes their
MCP access too.

Per-user registration checklist (own `az login`, approved MCP clients only,
first conversation and memory conventions): `../team/ONBOARDING.md` §3–§4.

## Shared hosting (Azure Container Apps, streamable HTTP)

For a team-shared endpoint: set `MCP_TRANSPORT=streamable-http` (no code
change), build the image with `Dockerfile` — whose **build context is
`convertion/`**, so `scripts/_foundry_runtime.py` and `scripts/memory_store.py`
are inside it:

```bash
az acr build -r {registry} -t infosec-mcp:{tag} -f convertion/mcp-server/Dockerfile convertion
```

then deploy to Azure Container Apps with a **system-assigned
managed identity** granted `Azure AI User` on the Foundry project, and put
Entra authentication (Easy Auth) in front so only assurance-team members
reach it. Register the resulting URL in clients (and, if desired, in the
ENX gateway) as a remote MCP server.

## Security notes

- No credentials in this folder: local runs use the caller's `az login`;
  hosted runs use managed identity. `PROJECT_ENDPOINT` is not a secret.
- `save_memory` writes to a shared store — restrict the hosted endpoint to
  the assurance team and keep notes free of special-category personal data
  (the tool description instructs models accordingly).
- Log/trace via Foundry's built-in tracing; the MCP layer adds no storage
  of its own.
