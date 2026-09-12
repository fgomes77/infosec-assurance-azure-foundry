# RACI — InfoSec Assurance Foundry Platform

> **HISTORICAL DESIGN VARIANT — not the model of record.** This file is the
> least-privilege lens kept as a design record; it uses a superseded
> vocabulary (six groups, approval tiers 1/2/3). The authoritative model is
> `../TEAM_MODEL.md` (decisions in §21) with `../RACI.md`,
> `../approval-policy.json` and `../rbac.bicep`. See `README.md` in this
> folder for the name mapping. Do not implement from this file.

R = Responsible (does it), A = Accountable (one per row), C = Consulted,
I = Informed. "Users" = the four assurance users collectively
(`{upn:jose.mogollon}`, `{upn:pedro.santos}`, `{upn:jose.meireles}`,
`{upn:tania.morais}`); the owner is also a user but appears in his own
column.

| Activity | Owner `{upn:francisco.gomes}` | Deputy `{upn:deputy-approver}` | Users | Line manager / CISO delegate | Azure landing-zone team | Entra IAM team | System owners (Jira, Confluence, OneTrust, SSC, IAF, ENX gateway) | M365 / SharePoint admin | DPO | Internal audit |
|---|---|---|---|---|---|---|---|---|---|---|
| Platform creation (Bicep, agents, connections, workflows, Function) | **A/R** | C | I | I | C (subscription, region, policy) | C (groups, consent) | C (service accounts, scopes) | C (site, Sites.Selected) | C (RoPA, DPIA of the platform) | I |
| Planning (roadmap, capacity, new agents/integrations) | **A/R** | C | C (needs) | C (priorities) | I | I | I | I | I | I |
| Maintenance (patching SDK pins, renderer re-staging, workflow fixes, monitoring) | **A/R** | R (when break-glass active) | I | I | C | I | I | I | I | I |
| Optimisation (model-tier tuning, token economy, RAG tuning, prompt refinements) | **A/R** | C (reviews owner's changes) | C (quality feedback) | I | I | I | I | I | I | I |
| Updates / re-sync from the claude.ai export (`deploy.sh` convert→verify→create) | **A/R** | C (PR review) | I (release note) | I | I | I | I | I | I | I |
| Template changes (req. j) | **A** (approver) | R for approval when requester = owner | R (request, review preview) | I | I | I | I | I | C (if the template carries personal data fields) | I |
| Integration credential rotation (`conn-*`, ENX gateway, Bing) | **A/R** | C (verifies closure) | I | I | I | C (app registrations, consent) | R (issue new token/scope) | C (Graph grants) | I | I |
| Incident response (platform: egress alert, prompt-injection finding, credential exposure, unavailable service) | **A/R** (first responder, containment) | R (if owner unavailable — break-glass) | R (report, stop using affected system) | I (P1/P2), A for break-glass approval | C | C (revoke, reset) | C | C | I (if personal data involved; A for breach notification) | I |
| Evaluation review (verifier first-pass rate, known-good output comparison, human approval rate, model drift) — monthly | **A/R** | C | R (sample review of outputs in their domain) | I (quarterly summary) | I | I | I | I | I | I |
| Cost review (tokens per deliverable, capacity, Bing/App Insights spend) — monthly | **A/R** | I | I | I (budget) | C (cost management, budgets/alerts) | I | I | I | I | I |
| User support (how-to, failed runs, approvals stuck, access) | **A/R** (L2) | R (L1 backup) | R (L1 peer help) | I | C (L3 Azure) | C (L3 identity) | C (L3 integration) | C (L3 SharePoint) | I | I |
| Quarterly access review (groups, RBAC, PIM, Sites.Selected, connections, GitHub, memory) | **R** | C | C (self-attest) | **A** (reviews the owner's own access) | I | R (runs Entra access reviews) | I | C | I | I (receives evidence) |
| On/offboarding of an assurance user | **A/R** | C | I | R (request via access package) | I | R (execute, revoke) | I | R (site membership) | I | I |
| AIMS / EU AI Act deployer records (Art. 26), ISO 42001 A.6 lifecycle evidence, Copilot channel scope | **A/R** | I | C | C | I | I | I | I | C | C |

Rules: exactly one **A** per row; the owner is never the only pair of
eyes on his own change (see `APPROVAL_ROUTING.md` §3); the line manager is
A for reviewing the owner's access and for approving break-glass, which
is the only place the accountability sits outside the owner.
