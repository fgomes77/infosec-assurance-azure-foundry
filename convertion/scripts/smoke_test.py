#!/usr/bin/env python3
"""Smoke-test a converted agent: send one prompt, print the reply.

Runs on the GA Responses API (conversations + responses) through
_foundry_runtime.py, which falls back to the classic threads/runs runtime
when the environment is still pinned to azure-ai-projects 1.x (finding C1
— the classic runtime retires 2027-03-31). The wire version is pinned by
FOUNDRY_API_VERSION (setup/.env, default v1).

When build/agent-versions.json records a version for the agent (finding
C19), the request pins that exact version — the same reference the
pipelines use — so a smoke test never silently exercises a portal edit.

Usage:
    python3 smoke_test.py --agent dora \
        --prompt "Summarise DORA Art. 30 contractual provisions"
    python3 smoke_test.py --agent dora --prompt "..." --latest
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
try:
    from dotenv import load_dotenv
    load_dotenv(HERE.parent / "setup" / ".env")
except ImportError:
    pass  # plain environment variables still work

from _foundry_runtime import get_runtime, pinned_ref  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", required=True)
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--latest", action="store_true",
                    help="ignore the recorded version and use the latest")
    args = ap.parse_args()

    rt = get_runtime()
    target = rt.list_agents().get(args.agent)
    if target is None:
        sys.exit(f"No agent named {args.agent!r} — run create_agents.py first")

    ref = pinned_ref(args.agent)
    if args.latest:
        target.version = None
    elif ref and ":" in ref:
        want = ref.split(":", 1)[1]
        if target.version and target.version != want:
            print(f"note: live latest is {target.ref}, testing the deployed "
                  f"version {ref} (build/agent-versions.json; --latest to "
                  f"test the newest)")
        target.version = want

    conv, text = rt.ask(target, args.prompt)
    print(f"conversation: {conv}")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
