# Team Model — Roles, Ownership, Minimum Access per System

> **HISTORICAL DESIGN VARIANT — not the model of record.** This file is the
> least-privilege lens kept as a design record; it uses a superseded
> vocabulary (six groups, approval tiers 1/2/3). The authoritative model is
> `../TEAM_MODEL.md` (decisions in §21) with `../RACI.md`,
> `../approval-policy.json` and `../rbac.bicep`. See `README.md` in this
> folder for the name mapping. Do not implement from this file.

## 1. Roles (three, not five)

Least privilege is about roles, not people. The platform has exactly
three human roles; every person maps to one or two of them.

| Role | Held by | What it exists for |
|---|---|---|
| **Assurance user** | all five (`{upn:francisco.gomes}`, `{upn:jose.mogollon}`, `{upn:pedro.santos}`, `{upn:jose.meireles}`, `{upn:tania.morais}`) | Run every system a–j, receive deliverables, approve peers' reports (four-eyes), propose template changes, write to shared memory |
| **Platform owner** | `{upn:francisco.gomes}` only | Create, plan, maintain, optimise, update/re-sync the platform; approve template/platform/prompt/registry changes; own credentials and connections; own the ISMS/AIMS evidence for the platform |
| **Deputy platform approver** | `{upn:deputy-approver}` (one of the four, nominated by the owner, confirmed by `{upn:line-manager}`) | Approve the **owner's own** template/platform changes (segregation of duties); hold *eligible* (not active) break-glass admin for continuity when the owner is unavailable |

Rationale: the requirement is "five users with identical persona
experience, one accountable owner". Two roles would satisfy that; the
third (deputy) is the single addition, and it exists because ISO 27001
A.5.3 and DORA Art. 5(2) do not allow the person who changes a control to
be the only person who can approve that change.

## 2. Ownership statement

| Object | Owner (accountable) | Custodian (does the work) | Consulted |
|---|---|---|---|
| Foundry account, project, agents, vector stores, model deployments | `{upn:francisco.gomes}` | owner; deploy identity `sp-infosec-foundry-deploy` via GitHub Actions | Azure landing-zone team |
| Foundry project connections (`conn-*`, `bing-grounding`, `enx-gateway-mcp`) | `{upn:francisco.gomes}` | owner | system owners (Jira, Confluence, OneTrust, SecurityScorecard, IAF, ENX gateway, M365) |
| Logic Apps (pipelines, workflows), delivery Function, Key Vault, storage, Log Analytics/App Insights | `{upn:francisco.gomes}` | owner | Azure landing-zone team |
| SharePoint InfoSec Assurance site (`Reports/`, `Templates/`, `Governance/`) | `{upn:francisco.gomes}` (site owner) | M365/SharePoint admin team (site-collection admin) | DPO (for `Reports/DPO`) |
| Shared team memory (`vs-assurance-memory`) | `{upn:francisco.gomes}` | every assurance user adds; owner/author deletes | DPO (RoPA entry) |
| Template inventory (`templates/registry.json`) | `{upn:francisco.gomes}` | template-manager agent + `update_templates.py`, after owner approval | assurance users (requesters) |
| GitHub repository (this kit) | `{upn:francisco.gomes}` (CODEOWNERS) | owner; deputy reviews owner's PRs | GitHub org admins |
| Copilot Studio agent(s) | `{upn:francisco.gomes}` (environment maker) | owner | Power Platform admin team, M365 admin |

## 3. Minimum access per system (a–j)

Start point for every row: what a user physically needs to press the
button and receive the result. Agent-side credentials (Foundry
connections) are never user permissions — the agent, not the person,
holds the read-only enterprise access (`../../governance/DATA_PROTECTION_GUARDRAILS.md` §2).

| Req | System | User action | Minimum user grant | Agent/pipeline identity involved | Approver |
|---|---|---|---|---|---|
| a | DeepSearch report (HTML) | Ask agent / submit Teams form with Supplier + Service; receive link | `Azure AI User` on the Foundry project; SharePoint `Reports/` **Read** | project MI (Bing, SecurityScorecard, IAF, CMDB, ENX gateway — read-only); Logic App MI; Function MI (only writer) | Author sign-off (tier 2) — see `APPROVAL_ROUTING.md` |
| b | OneTrust PDF → DPO DOCX | Upload PDF to own thread; trigger pipeline | `Azure AI User`; `Reports/DPO/` **Read** (so the team can see what was sent to the DPO) | `conn-onetrust` (viewer), Function MI | **Peer four-eyes** (tier 1: leaves the team) |
| c | OT PDF → Cyber Forum PPTX | Upload / reference registered assessment; trigger pipeline | `Azure AI User`; `Reports/` Read | `conn-onetrust`, `conn-sharepoint-graph` (read), Function MI | **Peer four-eyes** (tier 1) |
| d | OT PDF → Global CISO PPTX | Same as c | Same as c | + `conn-jira-assets` (CMDB read) | **Peer four-eyes** (tier 1) |
| d2 | TPA evidence tree analysis | Trigger with Supplier (+Service) | `Azure AI User`; `Reports/` Read. The user's existing **Edit** on `Infosec Assurance/GRC/TPA/Active` is a pre-existing job permission, not a platform grant | project MI Graph `Sites.Selected` (read) on the site | Author sign-off (tier 2) |
| e | SOC report upload → summary | Upload file to own thread; trigger | `Azure AI User`; `Reports/` Read | Function MI | Author sign-off (tier 2) |
| f | Pentest report upload → summary | Same as e | Same as e | Function MI | Author sign-off (tier 2) |
| g | Per-framework advisory + file generation | Converse; download generated files from the thread | `Azure AI User` (thread file download is a data-plane read) | project MI read surface (advisory toolset) | None — conversational output stays inside the platform; files the user forwards are the user's act |
| h | TPRM end-to-end knowledge | Converse | `Azure AI User` | same | None |
| i | Persona with read-only enterprise access + sanitised web | Converse (Foundry playground, MCP client, Copilot) | `Azure AI User`; membership of `sg-infosec-foundry-users` for the Copilot Studio agent and hosted MCP Easy Auth | project MI (all `conn-*` read-only) | None |
| j | Template management | Select/analyse/edit/preview with `template-manager`; propose a change | `Azure AI User`; `Templates/` **Read** | Function MI publishes the review page to `Templates/Reviews/` | **Owner only** (deputy if requester = owner) |

What users do **not** get, and why:

| Not granted | Reason |
|---|---|
| Any Azure RBAC beyond `Azure AI User` on the project | Portal visibility of Key Vault, Logic Apps, Function, storage is not needed to use a–j; all outputs arrive via thread, Teams and SharePoint |
| SharePoint write on `Reports/` or `Templates/` | The delivery Function's managed identity is the only writer (`../../sharepoint/README.md`); templates change only via the approved workflow |
| Foundry connection secrets, Key Vault | Agents hold the credentials; users never need them |
| GitHub write | Template and platform changes flow through `template-manager` + `update_templates.py`, not through git commits by users |
| Log Analytics access | Users receive their run results in-thread; audit access is the owner's/auditor's, not a per-user need |

## 4. Additions ledger (every grant above the minimum, with justification)

| # | Principal | Addition | Justification | Control |
|---|---|---|---|---|
| A1 | `{upn:francisco.gomes}` | `Azure AI Developer` on the Foundry account (PIM-eligible, 8 h) | Creates/updates agents, vector stores, connections, model tier switches (`deploy.sh` steps 3–6b) | PIM activation with justification + MFA; Activity Log; A.8.2 |
| A2 | `{upn:francisco.gomes}` | `Contributor` on `rg-infosec-foundry` (PIM-eligible, 8 h) | Bicep deployments, Logic Apps/Function configuration when the pipeline cannot (hotfix) | PIM; preferred path is the GitHub deploy identity, so activations are exceptions and are reviewed quarterly |
| A3 | `{upn:francisco.gomes}` | `Key Vault Secrets Officer` on the platform Key Vault (PIM-eligible, 2 h) | Credential rotation for `conn-*` API-token connections | PIM; secret versions are immutable and dated (evidence for A.5.17) |
| A4 | `{upn:francisco.gomes}` | `Logic Apps Standard Developer` + `Logic Apps Standard Operator` (PIM-eligible) | Deploy workflow definitions; resubmit failed runs; disable a workflow in an incident | PIM; run history retained |
| A5 | `{upn:francisco.gomes}` | `Website Contributor` on the delivery Function (PIM-eligible) | `func azure functionapp publish` after renderer re-staging | PIM |
| A6 | `{upn:francisco.gomes}` | `Log Analytics Reader` on the workspace + `Reader` on the RG (**permanent**) | Continuous monitoring duty (egress alerts, verifier fail rate, cost) is daily work; read-only, low blast radius | Quarterly review; A.8.15/A.8.16 |
| A7 | `{upn:francisco.gomes}` | `Storage Blob Data Reader` on the deliverables container (PIM-eligible) | Troubleshooting rendered artefacts before upload | PIM |
| A8 | `{upn:francisco.gomes}` | SharePoint site **Owner**; `Templates/` Edit; `Reports/` Contribute (no delete) | Site administration; record corrections after approval (versioned); `Sites.Selected` grants require site ownership | SharePoint versioning + audit log |
| A9 | `{upn:deputy-approver}` | Membership of `sg-infosec-foundry-platform-approvers` for owner-requested changes only; **eligible** member of `sg-infosec-foundry-breakglass` | Segregation of duties (A.5.3) and continuity (DORA Art. 9) | Routing rule in `approvals/routing.json`; PIM approval by `{upn:line-manager}` |
| A10 | `sp-infosec-foundry-deploy` (GitHub OIDC federated credential, no secret) | `Contributor` on the RG + `Role Based Access Control Administrator` constrained to the role set in `infra/rbac.bicep` | Reproducible, reviewable deployments; removes the need for the owner's standing write access | GitHub environment protection (owner approval on `prod`); ABAC condition on assignable roles |
| A11 | Logic Apps MI | `Azure AI User` on the project; `Key Vault Secrets User`; `Storage Blob Data Contributor` on its own runtime storage | Runs agents, reads API tokens by reference, Logic Apps Standard runtime requirement | Managed identity, no keys |
| A12 | Delivery Function MI | Graph `Sites.Selected` with **write** on the one InfoSec Assurance site; `Storage Blob Data Contributor` on its runtime storage | The single write path to SharePoint after verifier PASS + human approval | `../../functions/delivery/README.md` |
| A13 | Foundry project MI | Graph application permissions (all read) for `defender-graph`, `sharepoint-graph`, `entra-iam-graph`; `Key Vault Secrets User` | OpenAPI tools authenticate with managed identity instead of secrets; the agent surface is read-only by construction | Non-GET stripped; admin consent recorded |
| A14 | `sg-infosec-foundry-auditors` (empty by default) | `Log Analytics Reader`, `Logic Apps Standard Reader`, SharePoint `Governance/` Read | Internal audit / ISO 27001 surveillance evidence without touching the owner's account | Populated per audit engagement, removed after; A.5.35 |

Anything not in this ledger is not granted. A new row requires the owner's
approval **and** the deputy's review (the ledger is itself a platform change).
