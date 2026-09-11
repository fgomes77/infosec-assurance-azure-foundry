# InfoSec Assurance MCP Server

Exposes the Foundry agent environment as MCP tools so any MCP client —
Claude Desktop / Claude Code, the ENX gateway, or internal tooling — can
drive it: `ask_orchestrator`, `ask_agent`, `list_agents`, `save_memory`,
`search_memory`. Conversation context persists via the returned `thread_id`;
durable team memory lives in the `vs-assurance-memory` store.

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

## Shared hosting (Azure Container Apps, streamable HTTP)

For a team-shared endpoint: switch `mcp.run()` to
`mcp.run(transport="streamable-http")`, containerise (python:3.12-slim +
requirements), deploy to Azure Container Apps with a **system-assigned
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
