# Inference Profiles — how each agent runs, not just which model runs it

`MODEL_ROUTING.md` answers *which model serves an agent*. This file is the
other half of requirement j — *how that model is called*: sampling
determinism, reasoning effort, the output ceiling and retrieval width.
Together they are the platform's efficiency-and-accuracy contract.

- Values of record: `../integrations/inference-profiles.json`
- Resolver: `../scripts/inference_profiles.py` (`params_for`, `retrieval_for`)
- Applied at: agent save (`create_agents.py`, `create_delivery_agents.py`,
  `create_orchestrator.py`, `apply_advisory_profile.py`), tier application
  (`attach_integrations.py`) and request time
  (`_foundry_runtime.Runtime.ask`)
- Guarded by: `../scripts/tests/test_inference_profiles.py` (13 offline
  checks) and `inference_profiles.py --check` in CI

## 1. Why this layer exists

Before it, every agent ran on **service defaults**. Two consequences, both
measurable:

| | Without a profile | With one |
|---|---|---|
| A scoring agent re-run on the same evidence | free to vary — `temperature` at the service default | `temperature: 0.0`, so the same evidence yields the same score and a reviewer can reproduce it |
| A reasoning agent doing routing | spends full reasoning tokens deciding which specialist to call | `reasoning_effort: low` on the router class |
| A structured extraction | may emit unbounded prose around the JSON | ceiling sized from the schema |
| Retrieval | service default width for every agent | narrow where precision matters, wide where coverage is the charter |

## 2. The classes

The **class**, not the tier, carries the parameters — so an agent keeps its
behaviour when its tier model changes.

| Class | Agents | Determinism | Effort | Ceiling | Retrieval |
|---|---|---|---|---|---|
| `router` | control centre, orchestrator | 0.0 | low | 512 | 3 @ 0.5 |
| `file-transform` | docx, pdf, pptx, xlsx, morning, whisperx | 0.0 | low | 4 096 | 5 @ 0.5 |
| `report` | dpia, ciso-reporting, ciso-executive-summary, tprm/pptx slide generators, onetrust-form-b, template-manager, doc-coauthoring, internal-comms, tpsrca-report | 0.1 | medium | 16 384 | 8 @ 0.45 |
| `analysis` | deepsearch (×2), ciso-global-report, tpa/soc/pentest analyzers, pdf-full-coverage, tpsrca-{engine,calc,analysis} | 0.0 | high | 32 768 | 12 @ 0.4 |
| `advisory` | cyber-forum, advisor, iso27001, iso42001, dora, nis2, eu-ai-act, learn, mcp-builder | 0.2 | high | 32 768 | 12 @ 0.4 |
| `verifier` | output-verifier | 0.0 | medium | 2 048 | 6 @ 0.5 |

`temperature` 0.2 for advisory is deliberate: these agents answer open
questions where a single rigid phrasing is worse than a considered one, and
their factual floor is enforced by the grounding rule, not by sampling.

## 3. Model families decide what is legal

A parameter's legality is a property of the **model family**, not of the tier
label:

| Family | Takes | Rejects |
|---|---|---|
| `gpt-4o`, `gpt-4o-mini`, `gpt-4.1*` | `temperature`, `top_p`, `max_output_tokens`, `parallel_tool_calls` | `reasoning_effort` |
| `o4-mini`, `o3-mini`, `gpt-5*` | `reasoning_effort`, `max_output_tokens`, `parallel_tool_calls` | `temperature`, `top_p` |

Each class therefore declares values for **both** families, and the resolver
returns only the legal subset for the model actually in force. This is why
the profile is re-resolved in `attach_integrations.py`, where the tier model
is finally applied: a profile stamped against the creation-time model would
be wrong for the model that ends up serving traffic. An unknown model is an
error, never a guess — guessing the family is how an illegal parameter
reaches the service and fails a production run.

The profile is also written into the agent's `metadata.inference_profile`,
so `ask()` re-applies it per request even when the SDK on the deploy host is
older than the service and the definition could not carry the fields. An
agent cannot end up on service defaults because of a stale SDK.

## 4. Prompt caching

Cached input tokens are billed at a fraction of uncached ones, and the only
requirement is a **byte-identical prefix**. The rules:

1. Agent instructions carry the persona and the charter **only** — never a
   date, run id, supplier name or any per-run value.
2. The persona block is assembled first, so the long static prefix is shared
   across every agent that carries it.
3. Everything volatile travels in the user message.

Rule 1 is tested offline (`test_agent_instructions_carry_no_per_run_values`),
so a charter edit that would break every cache in the platform fails in CI
rather than showing up as a cost line a month later. The hit rate is measured
by `../operations/kql/prompt-cache-hit-rate.kql`; target ≥ 0.6 per agent, and
a falling rate is read as *a prefix has been broken*, not as *prices moved*.

## 5. Accuracy floor

`max_output_tokens` is a **runaway guard sized from the deliverable's JSON
schema**, not a budget. A truncated response is a verifier FAIL, never a
shipped deliverable: if an agent truncates, raise the ceiling and investigate
the prompt — never trim the schema to fit the ceiling.

No value here may be relaxed to save tokens on an agent whose output is a
report of record. Changing a profile is a **Tier-B change**
(`../operations/CHANGE_MANAGEMENT.md`): the golden set
(`../operations/evaluation/`) runs before it serves traffic, exactly as a
tier move does. The two reviews are the same monthly conversation —
`MODEL_ROUTING.md` §Token-economy rules 7.

## 6. Control mapping

| Control | How this layer satisfies it |
|---|---|
| ISO/IEC 27001:2022 A.8.6 — capacity management | Per-agent output ceilings and effort levels bound the load a single run can create |
| ISO/IEC 42001:2023 A.6.2.4 — AI system operation | Documented, versioned operating parameters per AI component, changed under a gate |
| EU AI Act Art. 26(1) — deployer use per instructions | Parameters are declared, reviewed and evidenced rather than left to defaults |
| DORA Art. 9(2) — resource use | Token and latency envelopes are explicit and monitored |
