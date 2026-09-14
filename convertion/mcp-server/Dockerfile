# Shared MCP endpoint (Azure Container Apps, streamable HTTP).
#
#   BUILD CONTEXT IS convertion/, NOT mcp-server/ — server.py shares the
#   Foundry runtime adapter and the memory backend with the deploy scripts
#   (scripts/_foundry_runtime.py, scripts/memory_store.py; finding C1):
#
#   az acr build -r {registry} -t infosec-mcp:{tag} \
#       -f convertion/mcp-server/Dockerfile convertion
#
# No credential is baked in: the container app runs with a system-assigned
# managed identity granted `Azure AI User` on the Foundry project, and
# PROJECT_ENDPOINT is a plain app setting (not a secret). Put Entra
# authentication in front of the ingress so only the assurance team reaches it
# (README.md "Shared hosting").
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MCP_TRANSPORT=streamable-http

WORKDIR /app

COPY mcp-server/requirements.txt mcp-server/requirements.txt
RUN pip install --no-cache-dir -r mcp-server/requirements.txt

# scripts/ first: it changes less often than the server itself.
COPY scripts/ scripts/
COPY mcp-server/ mcp-server/

RUN useradd --system --uid 10001 mcp && chown -R mcp /app
USER mcp

EXPOSE 8000
CMD ["python3", "mcp-server/server.py"]
