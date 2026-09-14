#!/usr/bin/env python3
"""Resolve the inference parameters an agent runs with.

`governance/MODEL_ROUTING.md` decides WHICH model serves an agent; this
module decides HOW it is called — sampling determinism, reasoning effort,
the output ceiling and retrieval width — from
`integrations/inference-profiles.json`.

Two call sites, one answer:

    from inference_profiles import params_for, retrieval_for
    params_for("soc-report-analyzer", model="o4-mini")
    # {'reasoning_effort': 'high', 'max_output_tokens': 32768,
    #  'parallel_tool_calls': True}

    params_for("dpia", model="gpt-4o")
    # {'temperature': 0.1, 'top_p': 0.95, 'max_output_tokens': 16384,
    #  'parallel_tool_calls': True}

The same agent resolves to DIFFERENT keys on different models because the
legality of a parameter is a property of the model family: o-series
reasoning models reject `temperature`/`top_p` and take `reasoning_effort`;
the gpt-4o family is the reverse. Nothing is dropped silently — a value
that is illegal for the resolved model is an error, so a tier switch can
never quietly change how an agent samples (the failure mode this module
exists to prevent).

CLI:

    python3 inference_profiles.py --check          # every registry agent is classed (CI)
    python3 inference_profiles.py --show <agent>   # resolved params per tier model
    python3 inference_profiles.py --table          # the whole assignment

Offline and deterministic: no Azure call, no credentials.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONV = HERE.parent
PROFILES = CONV / "integrations" / "inference-profiles.json"
REGISTRY = CONV / "integrations" / "registry.json"

# Keys a class may carry. `retrieval` is handled separately (it shapes the
# file_search tool, not the request), and `purpose`/`_reason` are prose.
_PARAM_KEYS = ("temperature", "top_p", "max_output_tokens",
               "parallel_tool_calls", "reasoning_effort")
_EFFORTS = ("low", "medium", "high")


class ProfileError(ValueError):
    """A profile that cannot be applied as written — never a silent drop."""


def load(path: Path | None = None) -> dict:
    return json.loads((path or PROFILES).read_text(encoding="utf-8"))


def family_of(model: str, profiles: dict | None = None) -> str:
    """Model family name, matched longest-first so 'gpt-4o-mini' does not
    resolve as 'gpt-4o'. Unknown models are an error: guessing the family
    is how an illegal parameter reaches the service."""
    profiles = profiles or load()
    best, best_len = None, -1
    for fam, spec in profiles["model_families"].items():
        for m in spec["matches"]:
            if model == m or model.startswith(m + "-"):
                if len(m) > best_len:
                    best, best_len = fam, len(m)
    if best is None:
        raise ProfileError(
            f"model {model!r} belongs to no family in "
            f"{PROFILES.relative_to(CONV)} — add it to model_families with "
            f"its supported/rejected parameters before pinning an agent to it")
    return best


def class_of(agent: str, profiles: dict | None = None) -> str:
    profiles = profiles or load()
    try:
        return profiles["agent_class"][agent]
    except KeyError:
        raise ProfileError(
            f"agent {agent!r} has no class in {PROFILES.relative_to(CONV)} — "
            f"add it to agent_class (one of "
            f"{', '.join(sorted(profiles['classes']))})") from None


def _merged(agent: str, profiles: dict) -> dict:
    base = dict(profiles["classes"][class_of(agent, profiles)])
    over = profiles.get("overrides", {}).get(agent, {})
    for k, v in over.items():
        if k.startswith("_"):
            continue
        base[k] = v
    return base


def params_for(agent: str, model: str, profiles: dict | None = None) -> dict:
    """Request parameters for this agent on this model — only the keys the
    model's family supports, with every value validated."""
    profiles = profiles or load()
    fam = family_of(model, profiles)
    spec = profiles["model_families"][fam]
    merged = _merged(agent, profiles)

    out: dict = {}
    for key in _PARAM_KEYS:
        if key not in merged:
            continue
        if key in spec.get("rejects", []):
            continue                      # not an error: the class carries
        if key not in spec["supports"]:   # values for both families on purpose
            continue
        out[key] = merged[key]

    if "reasoning_effort" in out and out["reasoning_effort"] not in _EFFORTS:
        raise ProfileError(
            f"{agent}: reasoning_effort {out['reasoning_effort']!r} is not one "
            f"of {_EFFORTS}")
    for key in ("temperature", "top_p"):
        if key in out and not 0.0 <= float(out[key]) <= 1.0:
            raise ProfileError(f"{agent}: {key} {out[key]} outside 0.0-1.0")
    if "max_output_tokens" in out and int(out["max_output_tokens"]) < 256:
        raise ProfileError(
            f"{agent}: max_output_tokens {out['max_output_tokens']} is below "
            f"the 256 floor — a ceiling that truncates a deliverable is a "
            f"verifier FAIL, not a saving (accuracy_floor in the profiles)")
    return out


def retrieval_for(agent: str, profiles: dict | None = None) -> dict:
    """file_search width for this agent: {'max_num_results', 'score_threshold'}."""
    profiles = profiles or load()
    return dict(_merged(agent, profiles).get("retrieval", {}))


def registry_agents() -> dict:
    return json.loads(REGISTRY.read_text(encoding="utf-8")).get("agents", {})


def tier_models(profiles: dict | None = None) -> dict:
    """Tier -> deployment of record, read from the registry (single source)."""
    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    rec = reg.get("model_tiers", {}).get("_deployment_of_record", {})
    return {t: rec[t] for t in ("light", "chat", "reasoning") if t in rec}


def check() -> int:
    """Every registry agent is classed, and every class resolves cleanly on
    the deployment of record for its tier."""
    profiles = load()
    models = tier_models(profiles)
    problems: list[str] = []
    for name, spec in sorted(registry_agents().items()):
        tier = spec.get("model_tier", "chat")
        model = models.get(tier)
        if not model:
            problems.append(f"{name}: tier {tier!r} has no deployment of record")
            continue
        try:
            resolved = params_for(name, model, profiles)
        except ProfileError as exc:
            problems.append(str(exc))
            continue
        if not resolved:
            problems.append(f"{name}: no parameter applies on {model} — the "
                            f"class carries none the family supports")
    # classes referenced by agent_class must exist
    for agent, cls in profiles["agent_class"].items():
        if cls not in profiles["classes"]:
            problems.append(f"{agent}: unknown class {cls!r}")
    if problems:
        print("inference profiles: " + str(len(problems)) + " problem(s)",
              file=sys.stderr)
        for p in problems:
            print("  - " + p, file=sys.stderr)
        return 1
    print(f"inference profiles OK — {len(registry_agents())} registry agents, "
          f"{len(profiles['agent_class'])} classed, "
          f"{len(profiles['classes'])} classes")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if any registry agent is unclassed (CI)")
    ap.add_argument("--show", metavar="AGENT", help="resolved params per tier")
    ap.add_argument("--table", action="store_true", help="the assignment")
    args = ap.parse_args()

    if args.show:
        profiles = load()
        for tier, model in tier_models(profiles).items():
            try:
                print(f"{tier:9} {model:12} "
                      f"{json.dumps(params_for(args.show, model, profiles))}")
            except ProfileError as exc:
                print(f"{tier:9} {model:12} ERROR {exc}")
        print(f"retrieval  {json.dumps(retrieval_for(args.show))}")
        return 0
    if args.table:
        profiles = load()
        models = tier_models(profiles)
        for name, spec in sorted(registry_agents().items()):
            model = models.get(spec.get("model_tier", "chat"), "?")
            print(f"{class_of(name, profiles):15} {name:38} {model:12} "
                  f"{json.dumps(params_for(name, model, profiles))}")
        return 0
    return check()


if __name__ == "__main__":
    sys.exit(main())
