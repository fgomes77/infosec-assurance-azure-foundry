#!/usr/bin/env python3
"""Smoke-test a converted agent: send one prompt, print the reply.

Usage:
    python3 smoke_test.py --agent dora \
        --prompt "Summarise DORA Art. 30 contractual provisions"
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / "setup" / ".env")
except ImportError:
    pass  # plain environment variables still work


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", required=True)
    ap.add_argument("--prompt", required=True)
    args = ap.parse_args()

    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential

    endpoint = os.environ.get("PROJECT_ENDPOINT")
    if not endpoint:
        sys.exit("Set PROJECT_ENDPOINT (setup/.env)")

    client = AIProjectClient(endpoint=endpoint,
                             credential=DefaultAzureCredential())
    agents = client.agents

    target = next((a for a in agents.list_agents() if a.name == args.agent),
                  None)
    if target is None:
        sys.exit(f"No agent named {args.agent!r} — run create_agents.py first")

    thread = agents.threads.create()
    agents.messages.create(thread_id=thread.id, role="user",
                           content=args.prompt)
    run = agents.runs.create_and_process(thread_id=thread.id,
                                         agent_id=target.id)
    if run.status != "completed":
        sys.exit(f"Run ended with status {run.status}: {run.last_error}")

    for msg in agents.messages.list(thread_id=thread.id):
        if msg.role == "assistant":
            for part in msg.content:
                if getattr(part, "text", None):
                    print(part.text.value)
            break
    return 0


if __name__ == "__main__":
    sys.exit(main())
