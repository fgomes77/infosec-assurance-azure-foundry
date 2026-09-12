# Knowledge Refresh — Scheduled Refresh of Knowledge Sources and Review of New Sources Before Inclusion

How the knowledge the agents ground on (M3 per-agent stores, M4 combined
store, advisor knowledge, knowledge packs, templates, and any future
Foundry IQ knowledge base) is kept current, and how a **new** source is
reviewed before it may be included. A refresh is a change: it follows
`../UPDATE_AND_UPGRADE_REVIEW_POLICY.md` (class *knowledge source*) and
the standard flow of `../../operations/CHANGE_MANAGEMENT.md` §3. Agents
never add, fetch or rewrite knowledge themselves — web grounding is a
per-request lookup, not a store (`../MEMORY_AND_LEARNING.md` §1).

Owner: `{upn:francisco.gomes}`; reviewer of the owner's own refreshes:
`{upn:deputy-approver}`. Control: ISO 27001:2022 A.5.7 (threat
intelligence), A.5.33, A.8.32; ISO 42001 A.7.2–A.7.5 (data for AI
systems, provenance, quality), A.6.2.6; EU AI Act Art. 9, Art. 26(5);
DORA Art. 13(1)–(2).

## 1. Knowledge inventory

| # | Source | Lives in | Enters the platform via | Refresh trigger / cadence | Review before inclusion |
|---|---|---|---|---|---|
| K1 | Skill knowledge from the claude.ai export (`references/`, catalogues, schemas) | `vs-<agent>` (M3) from `build/agents/<name>/knowledge/` | `convert_skills.py` → `verify_conversion.py` (byte-identical — FIDELITY check) | semi-annual re-sync (F6, `LIFECYCLE.md` §3) or when a source skill changed | §3 applies to every file whose hash changed |
| K2 | Authored advisor knowledge (`../../agents/advisor-knowledge/*.md`) | `vs-assurance-combined` (M4) + per-agent globs | PR to `agents/` → `create_orchestrator.py` | quarterly currency check; on regulatory change (S16) | §3 |
| K3 | Knowledge packs (`../../agents/knowledge-packs/*.md`: file intake, PDF reading, HTML design guide, writing style, platform self-knowledge) | relevant `vs-<agent>` + M4 | PR → `create_agents.py` | on platform change (e.g. SDK/runtime behaviour) — checked at the quarterly platform currency review | §3 (platform facts must cite a Learn page with date) |
| K4 | Templates (`../../templates/registry.json`, requirement j) | vector stores + code_interpreter files + renderers | `update_templates.py` after `template-update-approval` (P7D) | as proposed (F4); quarterly inventory | template approval flow is the review |
| K5 | Regulatory texts and framework references cited by advisors (DORA, NIS2, EU AI Act, ISO clause lists) | K1/K2 files | as K1/K2 | on publication of an RTS/ITS, transposition act, ISO amendment (S16 watch) | §3 + advisor comparison set (g/h/i cases) |
| K6 | Golden set and comparison-set baselines (`../../operations/evaluation/`, `Governance/ComparisonSet/`) | not agent knowledge — evaluation data | `EVALUATION.md` §5 G4 quarterly refresh from **approved** outputs only | quarterly | owner signs the refreshed set version |
| K7 | Durable team memory (`vs-assurance-memory` / `kb-assurance-memory`) | M2 | humans via `memory_store.py` / `save_memory` | continuous; W5 weekly hygiene, quarterly prune | note format + banned content (`MEMORY_POLICY.md`) — no source review needed, it is the team's own record |
| K8 | Future: Foundry IQ knowledge base `kb-assurance` over a Blob mirror of K1–K3 | Azure AI Search (EU) | scheduled indexer (5 min – 24 h) over `st-{env}-knowledge/knowledge-mirror` | indexer runs on schedule, but the **mirror** is only written by `deploy.sh` — so the review gate is unchanged | §3; SharePoint indexed source stays out (preview) |

Not knowledge and never indexed: users' conversations, SharePoint report
libraries (read live through the read-only Graph tool), mailboxes, Teams
messages, OneTrust/Jira/Confluence records (read live, read-only), web
pages returned by grounding.

## 2. Refresh calendar

| Cadence | Activity | Command / evidence | Gate |
|---|---|---|---|
| Weekly (W5) | memory hygiene: format, banned content, `retain_until` | `python3 scripts/memory_store.py list` | R13 = 0 |
| Monthly (M1) | knowledge-related drift from the evaluation review: wrong citations, stale clause numbers, outdated thresholds → backlog items | `run_evals.py` report; `learning_loop.py` proposal category `knowledge` | ticket per confirmed item |
| Quarterly | currency check of K2/K3/K5: each file's `reviewed:` line ≤ 12 months old or re-reviewed; regulatory watch reconciled; K6 refresh (G4) | PR `change/{ticket}` touching `agents/`; `EVALUATION.md` §5 | comparison set for advisors; owner sign-off |
| Semi-annual | re-sync from a fresh claude.ai export (K1) | `LIFECYCLE.md` §3 steps 1–10 | `verify_conversion.py` PASS; manifest diff reviewed |
| On event | regulatory change (S16), incident lesson (S9), AI-concern (S15) touching knowledge | ticket → PR | mandatory item — not deferred to the quarter |
| Per deploy | rebuild of K1–K4 stores by `deploy.sh`; K8 mirror sync (when enabled) | `build/manifest.json`; indexer run history | H8 drift check: only expected stores differ |

## 3. New-source intake review (mandatory before inclusion)

A "new source" is any file that would be added to K1–K5 or K8 and does not
come byte-identical from the reviewed export. The proposer completes the
form; the owner (or deputy) reviews; the PR carries both.

| # | Check | Pass criterion | Evidence in the PR |
|---|---|---|---|
| 1 | **Provenance** | origin named (standard body, regulator, Microsoft Learn with `ms.date`, internal policy id, team-authored); URL and access date recorded in the file header | header lines `source:` / `retrieved:` |
| 2 | **Licence / IP** | redistribution inside the tenant permitted; no verbatim reproduction of paid standards beyond quotation limits (`../../governance/THIRD_PARTY_IP.md`); no supplier confidential material | THIRD_PARTY_IP row |
| 3 | **Classification** | Euronext Internal at most; no personal data beyond role/company; no credentials, hostnames, object ids | `verify_conversion.py` secret/UPN grep passes |
| 4 | **Currency** | version/date of the source stated; superseded versions removed or marked | `reviewed:` line |
| 5 | **Consistency** | no conflict with verifier rules, `RISK_THRESHOLDS.md`, template contracts or existing knowledge; conflicts resolved in the same PR | reviewer note |
| 6 | **Injection scan** | file contains no instructions addressed to agents ("ignore previous", tool-call text, hidden HTML/markdown); knowledge is DATA (persona injection rule) | grep + reviewer read-through |
| 7 | **Size and placement** | within the 10,000-files / 512 MB store limits; placed in the right store (per-agent vs combined) | manifest diff |
| 8 | **Evaluation** | G1 run on the affected agents' cases (`run_evals.py --agent <agent>`); advisors: comparison set g/h/i; no metric below floor; citations resolve to the new source where expected | `eval-report.md` attached |
| 9 | **Approval** | owner approves (deputy when the owner authored); change ticket references this form | PR review + ticket |

Refused by design: sources harvested from users' mail or chat; pages
fetched by an agent during a run; documents whose provenance cannot be
stated; anything an agent generated (including summaries) unless a human
rewrote and signed it as team-authored.

## 4. Removal and supersession

| Case | Action |
|---|---|
| Superseded standard / regulation | replace the file in the same PR; keep the old version in git history; add a one-line supersession note at the top of the new file |
| Source withdrawn (licence, error) | delete the file; `create_agents.py --only <agent>` / `create_orchestrator.py` rebuild the stores without it; run G1 |
| Knowledge that caused an AI concern (S15) | mandatory ticket; disable the affected agent in the orchestrator if the concern is material (`RUNBOOK.md`); fix or remove; G1 before re-enabling |
| K8 mirror | files are removed from the Blob mirror by `deploy.sh`; the indexer deletes orphaned documents on its next run (verify in the indexer run history) |

## 5. Sources (status as of 2026-09-12)

| Claim | Source | Date | Status |
|---|---|---|---|
| Vector store limits (files, size, one store per agent) | https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/limits-quotas-regions#default-service-limits | 2026-09-07 | GA |
| File search GA; Standard setup keeps files in customer Storage/AI Search; not in Italy North | https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/file-search | 2026-08-05 | GA |
| Foundry IQ knowledge bases (`azureBlob`, `searchIndex` GA in REST 2026-04-01; scheduled indexer) | https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/what-is-foundry-iq | 2026-07-31 | GA core |
| Indexed SharePoint knowledge source | https://learn.microsoft.com/en-us/azure/search/agentic-knowledge-source-how-to-sharepoint-indexed | 2026-09-02 | Preview |
| Document-level permissions only where configured; remote SharePoint needs M365 Copilot licence | https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/foundry-iq-faq | 2026-06-05 | GA doc |
| SharePoint grounding tool (delegated identity, one per agent) | https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/sharepoint | 2026-08-21 | Preview |
| Grounding with Bing / Web Search: data leaves the Azure compliance boundary, DPA does not apply | https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/bing-tools | 2026-08-27 | GA |
