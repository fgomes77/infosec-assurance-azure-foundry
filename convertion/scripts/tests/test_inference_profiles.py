"""Offline tests for the inference-profile layer (run in the PR job).

These are the accuracy guards, not style checks: each one encodes a way a
profile can be wrong that would cost tokens or quality in production.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent.parent          # scripts/
CONV = HERE.parent
sys.path.insert(0, str(HERE))

import inference_profiles as ip  # noqa: E402

PROFILES = ip.load()
AGENT_DIRS = CONV / "agents"


def test_every_registry_agent_is_classed():
    """A new agent cannot ship on service defaults by omission."""
    missing = sorted(set(ip.registry_agents()) - set(PROFILES["agent_class"]))
    assert not missing, (
        f"unclassed agents: {missing} — add them to "
        f"integrations/inference-profiles.json agent_class")


def test_check_cli_passes():
    assert ip.check() == 0


def test_o_series_never_receives_temperature():
    """o-series models reject temperature/top_p; sending them fails the call."""
    for agent in PROFILES["agent_class"]:
        params = ip.params_for(agent, "o4-mini", PROFILES)
        assert "temperature" not in params and "top_p" not in params, agent
        assert "reasoning_effort" in params, agent


def test_gpt4o_never_receives_reasoning_effort():
    for agent in PROFILES["agent_class"]:
        params = ip.params_for(agent, "gpt-4o", PROFILES)
        assert "reasoning_effort" not in params, agent
        assert "temperature" in params, agent


def test_family_matching_is_longest_first():
    """'gpt-4o-mini' must not resolve through the 'gpt-4o' prefix."""
    assert ip.family_of("gpt-4o-mini", PROFILES) == "gpt-4o"
    assert ip.family_of("o4-mini", PROFILES) == "o-series"
    with pytest.raises(ip.ProfileError):
        ip.family_of("some-unknown-model", PROFILES)


def test_unknown_agent_is_an_error_not_a_default():
    with pytest.raises(ip.ProfileError):
        ip.params_for("not-an-agent", "gpt-4o", PROFILES)


def test_deterministic_agents_are_deterministic():
    """Anything whose output is compared, diffed or scored samples at 0."""
    for agent in ("template-manager", "output-verifier", "tpsrca-calc",
                  "soc-report-analyzer", "pentest-report-analyzer",
                  "tpa-evidence-analyzer", "xlsx", "docx"):
        params = ip.params_for(agent, "gpt-4o", PROFILES)
        assert params["temperature"] == 0.0, agent


def test_advisory_agents_keep_the_highest_effort():
    """Requirement g/h/i: reasoning quality is the product for these."""
    for agent, cls in PROFILES["agent_class"].items():
        if cls != "advisory":
            continue
        assert ip.params_for(agent, "o4-mini",
                             PROFILES)["reasoning_effort"] == "high", agent


def test_output_ceilings_are_above_the_truncation_floor():
    for agent in PROFILES["agent_class"]:
        cap = ip.params_for(agent, "gpt-4o", PROFILES)["max_output_tokens"]
        assert cap >= 512, f"{agent}: {cap} would truncate a deliverable"


def test_full_coverage_analyzer_keeps_the_widest_retrieval():
    """Its charter forbids losing a passage to a retrieval cut-off."""
    wide = ip.retrieval_for("pdf-full-coverage-analyzer", PROFILES)
    normal = ip.retrieval_for("soc-report-analyzer", PROFILES)
    assert wide["max_num_results"] > normal["max_num_results"]
    assert wide["score_threshold"] <= normal["score_threshold"]


def test_every_override_states_its_reason():
    for agent, over in PROFILES.get("overrides", {}).items():
        assert over.get("_reason"), (
            f"override for {agent} has no _reason — an unexplained deviation "
            f"from the class is how a profile rots")


# --- prompt-caching discipline --------------------------------------------
# A cached prefix only survives if the instructions are byte-identical call
# after call. These check that no per-run value can reach them.
_VOLATILE = re.compile(
    r"\b(20\d{2}-\d{2}-\d{2}T\d{2}:\d{2}|run[_-]?id\s*[:=]\s*\S|"
    r"conversation[_-]?id\s*[:=]\s*\S)", re.I)


def test_agent_instructions_carry_no_per_run_values():
    offenders = []
    for path in sorted(AGENT_DIRS.glob("*_instructions.md")):
        text = path.read_text(encoding="utf-8")
        for m in _VOLATILE.finditer(text):
            offenders.append(f"{path.name}: {m.group(0)!r}")
    assert not offenders, (
        "instructions must be a stable cache prefix — move per-run values to "
        "the user message: " + "; ".join(offenders))


def test_caching_policy_is_declared():
    cache = PROFILES["caching"]
    assert cache["instructions_must_be_static"] is True
    assert cache["min_prefix_tokens"] >= 1024
    assert 0 < cache["target_hit_rate"] <= 1
