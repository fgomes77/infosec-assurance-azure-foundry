# Onboarding — New Assurance User (and the Owner / Deputy Overlays)

Person-centric checklist for a joiner to the InfoSec Assurance platform;
the administrative side (access package, group change, snapshot) is
`../operations/access-governance/ACCESS_LIFECYCLE.md` §1 and the model is
`TEAM_MODEL.md` §14. Target: use on day 1, approver rights after the
attestation (§5). Every step leaves evidence in SharePoint
`Governance/Onboarding/{upn}.md` or the Entra audit log. Placeholders in
`{braces}`.

## 1. Day 0 — before the joiner's first day (line manager, owner, IAM)

| # | Step | Who | Evidence | Control |
|---|---|---|---|---|
| 1 | Request access package `AP-InfoSec-Foundry-User` (12-month expiry) stating "InfoSec Assurance team member, systems a–j" | `{upn:line-manager}` | request id | A.5.18 |
| 2 | Approve → membership of `sg-infosec-foundry-users` (one act grants Foundry `Azure AI User`, SharePoint Members, Copilot audience, MCP, CA scope) | `{upn:francisco.gomes}` | approval record; `az ad group member check` | A.5.15 |
| 3 | Add to Teams channels `{teams:infosec-assurance-platform}` (support) and `{teams:infosec-assurance-approvals}` (approval cards); GitHub team `infosec-assurance-users` (Read) | owner | — | A.5.16 |
| 4 | Confirm the device is Intune-compliant and MFA is registered (CA `CA-InfoSec-Foundry` requires both) | joiner + IT | Entra sign-in log | A.8.5 |
| 5 | Snapshot `access_snapshot.sh --tag joiner-{upn}` — expect exactly one `sg-infosec-foundry-*` membership | owner | snapshot folder | A.5.18 |

Nothing else is granted: no Azure role beyond the group, no SharePoint
write, no Key Vault, no monitoring role (`TEAM_MODEL.md` §4 "not granted
to users, and why").

## 2. Day 1 — read and sign-in (joiner)

| # | Read | Why |
|---|---|---|
| 1 | `USER_QUICKSTART.md` | how each system a–j is invoked, inputs, output path, approval tier |
| 2 | `../governance/HUMAN_APPROVAL.md`, `../governance/DATA_PROTECTION_GUARDRAILS.md`, `../governance/MODEL_ROUTING.md` | the three invariants: read-only agents, verifier + human approval, no Euronext data to the web |
| 3 | `../sharepoint/README.md` | `Reports/<Supplier>/<Service>/` rule — the folder names you type become the record |
| 4 | `TEAM_MODEL.md` §1, §12, §13 | who approves what; thread and memory conventions |
| 5 | `../agents/persona_system_prompt.md` | the persona every agent carries — identical for all five |

Self-checks (own `az login`; nothing here changes anything):

```bash
az login                                   # own Entra account, MFA prompt expected
az ad group member check --group sg-infosec-foundry-users --member-id "$(az ad signed-in-user show --query id -o tsv)"   # value: true
az role assignment list --assignee "$(az ad signed-in-user show --query id -o tsv)" --all --include-groups \
  --query "[].{role:roleDefinitionName,scope:scope}" -o table                        # exactly: Azure AI User (or the agent-consumer role) on the project
```

Open the Foundry portal project (`PROJECT_ENDPOINT` from the owner) and
the SharePoint site `{sharepoint:infosec-assurance}`: `Reports/` opens
read-only, `Infosec Assurance/GRC/TPA/Active/` allows upload. In Teams,
`@ENX Assurance` answers an advisory question (Copilot channel).

## 3. Day 1 — MCP registration with your own identity

Local stdio is the default for the five (`TEAM_MODEL.md` §11; hosted MCP
only if the ENX gateway needs it). The server authenticates as **you**
(`DefaultAzureCredential` → `az login`); removing you from the group
revokes it. Use only a client on the approved register
(`ACCESS_REGISTER.md` "Approved AI / MCP clients") — a client's model
provider receives the agents' answers, so an unapproved client is an
egress of Euronext data (ISO 27001:2022 A.5.19/A.5.20; GDPR Art. 28).

```bash
cd convertion/mcp-server && pip install -r requirements.txt
az login
export PROJECT_ENDPOINT="https://{account}.services.ai.azure.com/api/projects/{project}"   # not a secret
python3 server.py            # stdio; Ctrl-C to stop
```

Client registration (`mcpServers` entry, path and endpoint per your
machine — never a token):

```json
{ "infosec-assurance": { "command": "python3",
    "args": ["/path/to/convertion/mcp-server/server.py"],
    "env": { "PROJECT_ENDPOINT": "https://{account}.services.ai.azure.com/api/projects/{project}" } } }
```

Verify: `list_agents` returns the platform agents; `ask_agent` on `dora`
answers; the thread it creates carries `owner_upn` = your UPN (the server
stamps it). Record the client name in your attestation (§5).

## 4. Day 1–5 — first thread, memory conventions, first report

| # | Step | Convention | Evidence |
|---|---|---|---|
| 1 | Create your first engagement thread | name `<initials>/<Supplier>/<Service>/<yyyy-mm>`; metadata `{owner_upn, supplier, service, system, engagement, classification:"internal"}` (MCP/Copilot set it; in the playground state it in the first message). One thread per engagement, not per day. Threads are team-visible — treat them as shared working papers | thread id in attestation |
| 2 | Ask an advisory question (g / h / i) | check the citations; try a question that needs the CMDB or Confluence to see the read-only surface at work | — |
| 3 | Save your first memory note | `YYYY-MM-DD \| <Supplier> \| <Service or -> \| decision/fact/position/follow-up \| <text> \| by {upn} \| review <YYYY-Qn>` via MCP `save_memory` or `python3 ../scripts/memory_store.py add "…"`. Never: special-category data, personal data beyond role + company, credentials, hostnames, verbatim contract text, personal reminders. You may delete your own note (`memory_store.py delete <file_id>`); the owner deletes others' via `MEMORY_DELETE` | `memory_store.py list` shows the note |
| 4 | Produce one Tier A report end-to-end (e or f is quickest: upload a SOC or pentest report) | Supplier + Service exactly as in OneTrust; watch the verifier verdict; a **peer** approves in Teams | Logic Apps run id; stored file path |
| 5 | Review one peer's draft as approver-in-training (shadow, no decision rights yet) | learn what a Tier A approval checks: verifier PASS, source fidelity, no internal identifier in web queries, right folder | peer's name in attestation |
| 6 | Personal notes | there is no personal store on the platform; use OneNote/OneDrive, or a `personal-working` thread you delete yourself | — |

## 5. Attestation → approver rights (EU AI Act Art. 26(2) competence)

File `Governance/Onboarding/{upn}.md`:

```markdown
# Onboarding attestation — {upn}
| Field | Value |
|---|---|
| Joined sg-infosec-foundry-users | {date} (access package request {id}) |
| Documents read (§2) | {date} |
| MCP client registered | {client name, on the approved register} — own az login |
| First thread | {thread name} |
| First memory note | {file id} |
| Tier A report produced | {pipeline}, run {id}, approved by {upn:peer}, stored at Reports/{Supplier}/{Service}/{file} |
| Draft shadow-reviewed | {pipeline}, requester {upn:peer} |
| I confirm I understand: read-only agents, verifier + human approval, no Euronext data to the web, thread/memory conventions | signature {upn}, {date} |
| Owner confirmation | {upn:francisco.gomes}, {date} |
```

Then the owner adds the joiner to `sg-infosec-foundry-report-approvers`
(`az ad group member add`), records the row in `ACCESS_REGISTER.md`
("People" + change log) and re-runs the snapshot (`--tag joiner-{upn}`,
now two memberships). From this point the joiner may approve Tier A
items requested by others (never their own — the approval flow enforces
`approver ≠ requestedBy`).

## 6. Overlays — only when the joiner takes on a role beyond "user"

| Overlay | Extra steps | Who executes |
|---|---|---|
| Deputy (`{upn:deputy-approver}`) | owner nominates, `{upn:line-manager}` confirms; IAM adds to `sg-infosec-foundry-senior-approvers` and `-breakglass`; GitHub `Write` (reviews only); CODEOWNERS entry; register row; read `../operations/access-governance/BREAK_GLASS.md` and `TEAM_MODEL.md` §12 | `{group:iam-admins}`, owner |
| Owner succession | `TEAM_MODEL.md` §14 hand-over checklist (group ownership of the user-facing groups, `-owner` / `-admin-pim` membership, site ownership, Copilot maker, GitHub Maintain, custodianship rows, RoPA entry); hand-over check = `../deploy.sh --dry-run`, `least-privilege/scripts/provision_identity.sh --verify`, `access-review.sh` | `{upn:line-manager}`, IAM, successor |
| Reader (audit / DPO engagement) | `sg-infosec-foundry-readers` for the engagement only; no onboarding attestation (read-only); removed at engagement end | owner on request of `{group:isms-audit}` / `{group:dpo}` |

## 7. Troubleshooting the first week

| Symptom | Likely cause | Fix |
|---|---|---|
| Portal shows no project / MCP `list_agents` is empty | group membership not yet replicated, or `az login` used another tenant | wait 15 min; `az login --tenant {tenantId}`; re-check §2 |
| CA blocks sign-in | device not compliant / MFA not registered | IT; CA is not relaxed per person |
| `Reports/` folder allows edit | inheritance not broken on the folder | owner runs `sharepoint-permissions.md` §2c and files the finding |
| Approval card never arrives | not in `{teams:infosec-assurance-approvals}` or `requestedBy` = you (self-approval excluded) | owner adds you; a peer must approve |
| Memory note rejected | format or forbidden content | fix per §4 step 3 |

## 8. Controls implemented by this checklist

| Control | Step |
|---|---|
| ISO 27001:2022 A.5.15, A.5.16, A.5.18 | §1 group-only grant, snapshot |
| ISO 27001:2022 A.6.3, A.6.6 (awareness, confidentiality) | §2 reading, §5 attestation |
| ISO 27001:2022 A.5.19 / A.5.20; GDPR Art. 28 | §3 approved MCP clients only |
| ISO 27001:2022 A.5.12, A.5.34, A.8.10; GDPR Art. 5(1)(c) | §4 thread and memory conventions |
| ISO 27001:2022 A.5.3; EU AI Act Art. 14, 26(2); ISO 42001 A.9.2 | §5 approver rights only after competence attestation; requester exclusion |
| DORA Art. 9(4)(c), 13(6) | §1 access management; §2–§4 ICT awareness |
