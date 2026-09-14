#!/usr/bin/env python3
"""Offline efficiency gate for the Logic Apps definitions.

Each check encodes a way a workflow silently wastes money or throttles a
downstream API. They run in CI (`[4b2]`) beside the residency gate.

    python3 convertion/ci/tests/test_workflow_efficiency.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONV = HERE.parent.parent
WORKFLOWS = CONV / "workflows"

# A Foreach with no bound runs up to 20 branches at once against a
# rate-limited API (workflows/README.md §Loop concurrency).
MAX_REPETITIONS = 5


def _iter_actions(node, path=""):
    if isinstance(node, dict):
        for key, value in node.items():
            if isinstance(value, dict) and "type" in value:
                yield f"{path}/{key}", value
            yield from _iter_actions(value, f"{path}/{key}")
    elif isinstance(node, list):
        for item in node:
            yield from _iter_actions(item, path)


def test_every_foreach_is_bounded() -> list[str]:
    problems = []
    for wf in sorted(WORKFLOWS.glob("*.json")):
        try:
            data = json.loads(wf.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            problems.append(f"{wf.name}: not JSON ({exc})")
            continue
        for path, action in _iter_actions(data):
            if action.get("type") != "Foreach":
                continue
            conc = (action.get("runtimeConfiguration", {})
                          .get("concurrency", {}))
            reps = conc.get("repetitions")
            name = path.rsplit("/", 1)[-1]
            if reps is None:
                problems.append(
                    f"{wf.name}: Foreach {name} has no concurrency bound — "
                    f"it defaults to 20 parallel branches against a "
                    f"rate-limited API (workflows/README.md)")
            elif not 1 <= int(reps) <= MAX_REPETITIONS:
                problems.append(
                    f"{wf.name}: Foreach {name} repetitions={reps} outside "
                    f"1..{MAX_REPETITIONS}")
    return problems


def test_retry_policies_are_declared() -> list[str]:
    """An HTTP action with no retryPolicy takes the platform default of four
    exponential retries — fine for a read, wasteful for an action that is
    already inside a bounded loop and expensive for a long agent call."""
    problems = []
    for wf in sorted(WORKFLOWS.glob("*.json")):
        try:
            data = json.loads(wf.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue                       # reported by the check above
        for path, action in _iter_actions(data):
            if action.get("type") != "Http":
                continue
            inputs = action.get("inputs", {})
            if "retryPolicy" not in inputs:
                problems.append(
                    f"{wf.name}: HTTP action {path.rsplit('/', 1)[-1]} "
                    f"declares no retryPolicy")
    return problems


def main() -> int:
    checks = [("every Foreach is bounded", test_every_foreach_is_bounded)]
    # The retry check is advisory for now: it reports, it does not fail, so
    # adding it does not block on a backlog it did not create.
    advisory = [("HTTP actions declare a retryPolicy",
                 test_retry_policies_are_declared)]
    print(f">> workflow efficiency gate — {len(list(WORKFLOWS.glob('*.json')))} "
          f"definition(s)")
    failed = 0
    for label, fn in checks:
        problems = fn()
        print(f"   {'ok  ' if not problems else 'FAIL'} {label}")
        for p in problems:
            print(f"        - {p}", file=sys.stderr)
        failed += len(problems)
    for label, fn in advisory:
        problems = fn()
        print(f"   {'ok  ' if not problems else 'note'} {label}"
              f"{'' if not problems else f' — {len(problems)} advisory'}")
    if failed:
        print("workflow efficiency gate FAILED", file=sys.stderr)
        return 1
    print("workflow efficiency gate OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
