# Optimization Review — what was measured, what changed, what is deliberately not optimized

A standing record of the efficiency audit across the platform's five cost and
effort surfaces. It exists so the next reviewer does not re-derive the same
trade-offs, and so the places where the platform **chooses not** to optimize
are written down as decisions rather than looking like oversights.

Reviewed: 2026-09-13. Next review: with the monthly tier-tuning loop
(`../governance/MODEL_ROUTING.md` §Token-economy rules 7).

## 1. Surfaces and their levers

| # | Surface | Lever of record | State |
|---|---|---|---|
| S1 | Model inference | Tier per agent + request-time profile | `MODEL_ROUTING.md`, `INFERENCE_PROFILES.md` — **applied** |
| S2 | Generation vs code | Every renderable byte produced by a script, never by tokens | Applied since the first conversion (delivery Function renderers) |
| S3 | Observability | Interactive/archive retention split; sampling-safe queries | **Applied this review** (§2) |
| S4 | Orchestration | Bounded loop concurrency; one Logic Apps plan for all workflows | **Applied this review** (§3) |
| S5 | Build and CI | Cached toolchain, one dependency install per job | **Applied this review** (§4) |

## 2. Observability: the retention split (S3)

The workspace kept **365 days of interactive retention for every table**.
Nothing queries beyond 30 days — the longest lookback the platform ships — so
eleven of those twelve months were paying interactive rates to answer no
query.

Now: interactive `retentionInDays` = 90 (a full quarter of incident review),
and `totalRetentionInDays` = 365 per evidence table (`AppDependencies`,
`AppRequests`, `AppExceptions`, `AppTraces`) in the archive tier at roughly a
tenth of the price. **The DORA Art. 28 evidence horizon is unchanged** — only
what it costs to hold. Archived data is restored or searched when an audit or
an investigation needs it.

Two connected accuracy fixes shipped with it:

- The token and cost queries now weight by `ItemCount`, the sampling weight
  Application Insights attaches to retained items. A plain `sum()` would
  under-report the token bill by the sampling ratio the day sampling is
  enabled — and a cost decision taken on an under-reported bill is worse than
  no decision.
- `latency-and-tokens.kql` priced the reasoning tier as `o3-mini`, a model
  finding C4 had already rejected. The most expensive tier was priced at zero
  and its budget breach could never fire. The map now names the deployments of
  record, and an unknown model raises `unpriced-model` rather than costing
  nothing.

**Deliberately NOT optimized:** the daily ingestion cap stays at `-1`
(uncapped). A cap does not slow ingestion, it drops telemetry for the rest of
the day — and the dropped items would include the `AppDependencies` the egress
detector reads. Cost is bounded by the retention split and the budget alert,
never by discarding security evidence.

**Still open (not blocking):** Basic-logs tier for `FunctionAppLogs`, and
sampling of `AppTraces` (never `AppDependencies`). Both are safe now that the
queries are `ItemCount`-weighted; neither has been measured against real
ingestion volume yet, and tuning a tier on a guess is how evidence goes
missing.

## 3. Orchestration: bounded loops (S4)

A Logic Apps `Foreach` with no `runtimeConfiguration.concurrency` runs up to
**20 branches in parallel**. Two loops had none: `jira-finding-sync`
(Jira Cloud) and the attachment loop in `mailbox-intake` (Microsoft Graph).
Both call rate-limited APIs that answer the excess with 429s the connector
then retries — so unbounded parallelism was *slower and more expensive* than a
small steady number of branches.

Both are now bounded, every bound is documented with the limit it respects
(`../workflows/README.md` §Loop concurrency), and
`../ci/tests/test_workflow_efficiency.py` (CI gate `[4b2]`) fails the build if
a new `Foreach` ships without one. The gate also reports, as advisory, the 63
HTTP actions that rely on the platform's default retry policy — a backlog
item, not a regression.

## 4. Build and CI (S5)

The gates job downloaded the pinned Bicep CLI on every run and invoked `pip`
twice, re-resolving the index mid-job. Both the pip wheel cache and the Bicep
binary are now cached across runs, and the job installs its dependencies once.

The full skill conversion still runs on every PR **on purpose**: it is what
proves byte-fidelity with the claude.ai export, and it is the gate that would
catch a drifted template. Caching it would cache away the check.

## 5. What was examined and found already optimal

| Checked | Finding |
|---|---|
| Entra token acquisition in the delivery Function | `azure-identity` caches and refreshes per credential instance; a hand-rolled cache would add a second expiry to get wrong |
| Rendering path | Already deterministic code, not generation — zero completion tokens per delivered file |
| Vector stores | One per agent is a service limit, not a choice; the combined store is reached by hand-off |
| Logic Apps plan | One WS1 plan carries all workflow definitions |
| Upload path | `UploadCache` already deduplicates by content hash across deploys |

## 6. Control mapping

| Control | Evidence |
|---|---|
| ISO/IEC 27001:2022 A.8.6 — capacity management | Per-agent output ceilings, bounded loop concurrency, ingestion and budget alerts |
| ISO/IEC 27001:2022 A.8.15 — logging | Retention split keeps the full evidence horizon; the cap stays off so no event is dropped |
| DORA Art. 9(2) / Art. 28 | Resource-use envelopes; ≥ 1 year of ICT evidence retained (interactive + archive) |
| ISO/IEC 42001:2023 A.6.2.4 | Documented, reviewed operating parameters per AI component |
