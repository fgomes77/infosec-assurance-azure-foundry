// Build the Project Dossier .docx (professional, with embedded infographics).
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, Table,
  TableRow, TableCell, WidthType, ShadingType, BorderStyle, ImageRun,
  PageBreak, TableOfContents, LevelFormat, Footer, Header, PageNumber,
} = require("docx");

const TEAL = "008D7F", DARK = "0B3B36", LIGHT = "E4F3F1", GREY = "5B6B69";
const IMG = (p) => path.join(__dirname, "infographics", p);

function pngSize(file) {
  const b = fs.readFileSync(file);
  return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) };
}
function image(file, caption) {
  const { w, h } = pngSize(file);
  const width = 620, height = Math.round((h / w) * 620);
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER, spacing: { before: 200, after: 60 },
      children: [new ImageRun({ type: "png", data: fs.readFileSync(file), transformation: { width, height } })],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER, spacing: { after: 240 },
      children: [new TextRun({ text: caption, italics: true, size: 18, color: GREY })],
    }),
  ];
}
const H1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { before: 360, after: 160 }, children: [new TextRun({ text: t })] });
const H2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 260, after: 120 }, children: [new TextRun({ text: t })] });
const P = (t, o = {}) => new Paragraph({ spacing: { after: 140 }, alignment: AlignmentType.JUSTIFIED, children: [new TextRun({ text: t, ...o })] });
const B = (t) => new Paragraph({ numbering: { reference: "bullets", level: 0 }, spacing: { after: 80 }, children: [new TextRun(t)] });
const BB = (lead, rest) => new Paragraph({ numbering: { reference: "bullets", level: 0 }, spacing: { after: 80 }, children: [new TextRun({ text: lead + ": ", bold: true }), new TextRun(rest)] });

function table(headers, rows, widths) {
  const total = widths.reduce((a, b) => a + b, 0);
  const cell = (t, head, w, band) => new TableCell({
    width: { size: w, type: WidthType.DXA },
    shading: head ? { type: ShadingType.CLEAR, fill: TEAL }
                  : band ? { type: ShadingType.CLEAR, fill: LIGHT } : undefined,
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    children: [new Paragraph({ children: [new TextRun({ text: t, bold: head, color: head ? "FFFFFF" : undefined, size: 19 })] })],
  });
  return new Table({
    width: { size: total, type: WidthType.DXA }, columnWidths: widths,
    rows: [new TableRow({ tableHeader: true, children: headers.map((h, i) => cell(h, true, widths[i], false)) }),
      ...rows.map((r, ri) => new TableRow({ children: r.map((c, i) => cell(c, false, widths[i], ri % 2 === 1)) }))],
  });
}
const spacer = () => new Paragraph({ spacing: { after: 200 }, children: [] });

const PART = (n, t, sub) => [
  new Paragraph({ children: [new PageBreak()] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 1400 }, children: [new TextRun({ text: n, bold: true, size: 26, color: GREY })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 160 }, children: [new TextRun({ text: t, bold: true, size: 44, color: TEAL })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 200, after: 1400 }, children: [new TextRun({ text: sub, size: 22, color: DARK })] }),
  new Paragraph({ children: [new PageBreak()] }),
];

const children = [
  // ---- Cover ----
  new Paragraph({ spacing: { before: 2600 }, children: [] }),
  new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "PROJECT DOSSIER", bold: true, size: 30, color: GREY })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 200 }, children: [new TextRun({ text: "InfoSec Assurance Agent Platform", bold: true, size: 56, color: TEAL })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120 }, children: [new TextRun({ text: "The Euronext GRC / TPRM assurance toolset on Microsoft Foundry", size: 28, color: DARK })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 500 }, children: [new TextRun({ text: "Project · Plan · Requirements · Workflows · Architecture · Connections", size: 22, color: GREY })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 140 }, children: [new TextRun({ text: "Part I for stakeholders  ·  Part II for implementers", italics: true, size: 21, color: TEAL })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 1500 }, children: [new TextRun({ text: "Version 2.0  ·  13 September 2026  ·  Classification: Euronext Internal", size: 20, color: GREY })] }),
  new Paragraph({ children: [new PageBreak()] }),

  // ---- Document control ----
  H1("Document Control"),
  table(["Item", "Detail"], [
    ["Title", "Project Dossier — InfoSec Assurance Agent Platform on Microsoft Foundry (the product formerly named Azure AI Foundry)"],
    ["Version / Status", "2.0 — Draft for owner review and Tier-C approval"],
    ["Date", "13 September 2026"],
    ["Owner (accountable)", "Francisco Gustavo Gomes — InfoSec Assurance & Third-Party Risk"],
    ["Audience", "Part I: CISO, DPO, ICT risk, procurement and the assurance team. Part II: platform engineers implementing and operating the solution in Microsoft Foundry"],
    ["Repository", "github.com/fgomes77/infosec-assurance-azure-foundry — the conversion kit under convertion/ is the source of truth; this document is a rendering of it"],
    ["Classification", "Euronext Internal — internal system names only; no credentials, no personal data, every identity a placeholder"],
    ["Change control", "Tier C (owner-only) per convertion/team/TEAM_MODEL.md §12.1; the deputy approver reviews owner-authored changes (.github/CODEOWNERS)"],
  ], [2600, 6760]),
  spacer(),
  H2("How to read this document"),
  P("The document is in two parts because it answers two different questions. Part I answers “what is being built, why, what it costs, what it changes for the team, and how the risk is held” — it needs no Azure knowledge. Part II answers “how is it built in Microsoft Foundry, resource by resource, agent by agent, gate by gate” — it assumes an engineer with access to the subscription. Both parts describe the same platform and are generated from the same kit, so they cannot drift apart: if a number appears in both, it came from the same file."),
  P("Every claim that a reader may want to verify carries the path of the artefact that implements it (for example convertion/workflows/pipelines.json). Those paths are the evidence trail for an ISMS audit as much as they are a convenience for the reader."),
  spacer(),
  H2("Table of Contents"),
  new TableOfContents("Table of Contents", { hyperlink: true, headingStyleRange: "1-2" }),

  // ============================ PART I ============================
  ...PART("PART I", "For Stakeholders", "The business case, the ten systems, governance, cost, risk and the plan"),

  H1("1. Executive Summary"),
  P("The InfoSec Assurance team runs Euronext's third-party security assurance, ISMS and ICT-GRC work on a toolset of 35 AI skills built on claude.ai: supplier OSINT assessments, OneTrust-driven reports for the DPO and the CISO forums, evidence review, SOC and penetration-test analysis, and day-to-day regulatory advice across ISO 27001, DORA, NIS2, the EU AI Act and ISO 42001. That toolset works, but it lives outside the Euronext tenant, outside its identity model, outside its data-residency boundary and outside its change control."),
  P("This project moves the whole toolset into Microsoft Foundry inside the Euronext Azure tenant, without changing the deliverables the team produces. Fidelity is enforced mechanically: the skills' instructions, templates, thresholds and report generators are converted and then hash-verified against the export, so a deliverable produced on the new platform matches the one produced on the old. Around that core the project adds what an enterprise platform needs and a SaaS toolset could not provide — EU data residency, Entra-only identity, read-only access to enterprise systems, an independent verification step, a human approval gate before every write, full audit evidence, and a documented cost and change model."),
  P("Ten business systems are delivered (requirements a–j, §4). The platform is deployed as infrastructure-as-code, and every change to it passes an automated gate set before a human can approve it."),
  table(["In one line", "Detail"], [
    ["What", "35 exported skills → a governed agent platform in Microsoft Foundry: 36 registered agents, 12 delivery pipelines, 17 workflows, 20 read-only enterprise connections"],
    ["Why now", "Residency, identity, auditability and change control cannot be retrofitted onto a SaaS account; the regulatory obligations (DORA, NIS2, EU AI Act) apply to the tooling as well as to the assessments it produces"],
    ["Deliverable fidelity", "Byte-verified conversion — the same templates, thresholds and generators produce the same reports"],
    ["Who operates it", "Five assurance users; one accountable owner for creation, planning, maintenance, optimisation and updates"],
    ["What the team must do differently", "Approve each deliverable before it is stored or sent — the platform drafts and verifies, a person decides"],
    ["Status", "Built and gated in the repository; pending owner approval and tenant deployment"],
  ], [2200, 7160]),

  H1("2. Context and Problem Statement"),
  P("The assurance toolset grew on claude.ai because that is where it could be built quickly. It now carries real operational weight: supplier assessments that feed contract decisions, DPO reports, CISO forum material and the evidence register behind third-party risk. Four properties of the current arrangement are incompatible with that weight."),
  BB("Residency and data protection", "supplier evidence and Euronext internal context are processed outside the tenant's data boundary, with a third-party processor relationship the DPO did not design."),
  BB("Identity and access", "access is by account, not by Entra identity; there is no conditional access, no PIM, no leaver process tied to the corporate directory."),
  BB("Auditability", "there is no durable, exportable record of who approved which deliverable on which evidence — the record an ISO 27001 audit and DORA Art. 28 ask for."),
  BB("Change control", "a prompt or template can be changed by anyone with the account, with no review, no version and no way to reproduce last quarter's output."),
  P("None of these are arguments against the toolset — they are arguments about where it should run. The project therefore preserves the toolset and changes its foundation."),

  H1("3. Objectives, Scope and Success Criteria"),
  H2("3.1 Objectives"),
  B("Preserve deliverable quality exactly: the same reports, from the same rules, on Euronext infrastructure."),
  B("Bring the toolset inside the tenant: EU data residency, Entra-only identity, Key Vault-held secrets, tenant-owned storage."),
  B("Make every write deliberate: an independent verification step and a human approval gate before anything is stored, posted or sent."),
  B("Give the team read-only reach into the systems they already use — Confluence, Jira, SharePoint, OneTrust, Defender, the ENX gateway — without any ability to write to them."),
  B("Operate it as a managed service: monitored, budgeted, versioned, reviewed and improvable, with a named accountable owner."),
  H2("3.2 In scope"),
  B("The ten business systems of §4 (requirements a–j), their agents, pipelines and deliverable templates."),
  B("The Foundry landing zone: project, model deployments, networking, encryption, identity, policy and monitoring."),
  B("Delivery to SharePoint under the supplier/service taxonomy, with Purview sensitivity labelling."),
  B("Governance: approval policy, data-protection guardrails, memory policy, model routing, change and lifecycle management."),
  H2("3.3 Out of scope"),
  B("Anthropic Claude model tiers. The models are offered in the Foundry catalogue; they are excluded here by the EU data-residency rule, not by availability, and the exclusion is re-checked quarterly (convertion/governance/CLAUDE_ON_FOUNDRY.md)."),
  B("Local-hardware transcription (replaced by the Foundry speech path) and any skill excluded from the export for data-protection reasons."),
  B("Writing to enterprise systems. The platform reads; people write. This is a design boundary, not a phase-two item."),
  H2("3.4 Success criteria"),
  table(["Criterion", "Measure", "Target"], [
    ["Fidelity", "verify_conversion.py on every deployment", "Verified — every instruction, template and generator hash-matched to the export"],
    ["Parity", "UAT deliverables vs the claude.ai baselines for the same inputs", "No material deviation, accepted by the team"],
    ["Human control", "Write grants in the integration registry; stores without an approval callback", "Zero and zero"],
    ["Quality", "Verifier first-pass PASS rate on report agents", "≥ 90 % steady state; investigated on decline"],
    ["Adoption", "Assurance users producing deliverables on the platform", "All five within one quarter of go-live"],
    ["Economy", "Token cost per deliverable; prompt-cache hit rate", "Baseline in hypercare, then a downward trend; cache ≥ 0.6"],
  ], [2000, 4360, 3000]),

  new Paragraph({ children: [new PageBreak()] }),
  H1("4. The Ten Systems (Business Requirements a–j)"),
  P("The requirements were stated by the assurance team in their own terms; each became a system with a named agent, an output contract, a delivery pipeline and an approval gate. The traceability matrix of record is convertion/REQUIREMENTS.md."),
  table(["Req", "System — what a user asks for", "What it produces", "Pipeline"], [
    ["a", "DeepSearch OSINT assessment of a supplier", "Interactive single-file HTML dashboard: 11 sections, spider graph, confidence scoring", "deepsearch-report · ai-deepsearch-report"],
    ["b", "Turn a OneTrust assessment PDF into the DPO's report", "InfoSec TPA report (DOCX) for the DPO team", "dpia-dpo-report"],
    ["c", "Material for the Cyber Forum from OneTrust assessments", "Governance deck (PPTX) plus the HTML executive dashboard", "cyber-forum-pptx · ciso-exec-summary"],
    ["d", "A Global CISO briefing on one supplier/service", "9-slide PPTX: contract owner, impacted ENX entities, service and supplier description, executive risk and control résumé, internal/external exposure diagram, ICT inherent and residual scores, actions addressed to the contract owner", "ciso-global-pptx"],
    ["d2", "Analyse everything filed for a supplier in the evidence library", "Per file: content identification, scope, emission date, validity period read from the document content, and findings — ISO certificates, SOC 1/2/3 Type 1/2, pentests, vulnerability reports, CAIQ, PDFs and scans", "tpa-evidence-analysis"],
    ["e", "Summarise a SOC report", "Opinion, scope, period, every exception, CUEC mapping, carve-outs, reliance verdict (DOCX)", "soc-report-summary"],
    ["f", "Summarise a penetration test", "Normalised findings register by severity, scope and currency adequacy, Euronext relevance, reliance verdict (DOCX)", "pentest-report-summary"],
    ["g", "Ask a framework question and get a usable artefact", "Advice plus Word/Excel/PowerPoint/HTML output across ISO 27001/27002/27005/22301/20000/42001, NIST CSF 2.0, CIS v8.1, GDPR Art. 28 and SCCs, DORA, NIS2, EU AI Act, CSA CCM/CAIQ, PCI DSS v4, OWASP/PTES/CVSS", "advisory-file-delivery"],
    ["h", "Ask a TPRM lifecycle question", "The same, grounded in the third-party risk methodology and the team's own thresholds", "advisory-file-delivery"],
    ["i", "Let the assistants see the systems we work in", "Read-only reach into Confluence, Jira, SharePoint, OneTrust, the ENX gateway and the security tooling; full web search with no Euronext data leaving", "— (platform capability)"],
    ["j", "Change a report template safely", "Inventory → choose → edit → visual before/after review → approval-gated propagation, atomic with rollback", "template-update-approval"],
  ], [500, 3100, 4200, 1560]),
  spacer(),
  P("Two rules run through all ten. First, the supplier/service storage rule the team asked for: a report is filed under Reports/<Supplier>/<Service>/ — an existing supplier folder is reused, a missing service folder is created, never a duplicate. Second, nothing reaches SharePoint, Teams or a ticket without passing the verifier and then a named human approver."),

  H1("5. What Changes for the Team"),
  H2("5.1 The five users and the one owner"),
  P("Five people use the platform with the same professional persona — the identity, tone, evidence standard and English-only policy are part of every agent's instructions rather than a habit each user has to enforce. One of them is accountable for the platform itself."),
  table(["Person", "Role on the platform", "What they can do"], [
    ["Francisco Gustavo Gomes", "Accountable owner — creation, planning, maintenance, optimisation and updates", "Everything a user can do, plus platform and template changes (Tier C), approvals routing, PIM-elevated administration"],
    ["José Mogollon", "Assurance user", "Run any of the ten systems; approve report deliverables per the approval matrix"],
    ["Pedro Santos", "Assurance user", "Same"],
    ["José Meireles", "Assurance user", "Same"],
    ["Tânia Morais", "Assurance user", "Same"],
  ], [2400, 3200, 3760]),
  P("Identities in the repository are placeholders; the real UPNs and group object ids are supplied at deployment from the tenant (convertion/team/TEAM_MODEL.md, ACCESS_REGISTER.md)."),
  H2("5.2 The approval habit"),
  P("The single behavioural change is that a deliverable is drafted, then verified, then approved — in that order, and the approval is a click by a person who is accountable for it. The platform makes the first two steps free and the third unavoidable: an unapproved draft cannot be stored, posted or sent, because the identity that writes to SharePoint is only reachable after the approval callback."),
  ...image(IMG("03-release-approval-flow.png"), "Figure 1 — The release path every deliverable of record follows, from request to stored report"),
  H2("5.3 What the team stops doing"),
  B("Re-reading evidence that has not changed: the platform reads only what moved since the last assessment and tells the approver which rows were carried forward."),
  B("Re-typing report structure: templates, thresholds and generators are held centrally and changed under review."),
  B("Hunting for last quarter's numbers: the portfolio and score history lists are written by the platform after each approval."),

  H1("6. Governance, Compliance and Data Protection"),
  H2("6.1 Three layers of control, not one"),
  table(["Layer", "Control", "Where it lives"], [
    ["1 — Structural", "Agents are read-only by construction: every non-GET operation is stripped from every enterprise tool at deployment; no write grant exists to be misused", "convertion/scripts/attach_integrations.py"],
    ["2 — Instructional", "Every agent carries an injection-resistant draft-then-approve gate in its instructions, and states what it may not do", "the APPROVAL GATE block in every charter"],
    ["3 — Procedural", "The pipeline suspends on a human-approval webhook before any write; rejections are recorded without writing", "convertion/workflows/report-delivery-pipeline.json"],
  ], [1600, 4600, 3160]),
  P("An independent output-verifier agent sits between the draft and the human: it checks completeness, threshold consistency, grounding, absence of placeholders and data minimisation, and returns PASS or FAIL. It generates nothing, so it cannot rescue a bad draft by rewriting it — a FAIL goes back to a person."),
  H2("6.2 Data protection and residency"),
  BB("Residency", "every model deployment uses the EU Data Zone SKU; Global routing is refused by Azure Policy, not merely by convention. Conversations, vector stores and deliverables are held in tenant-owned EU resources."),
  BB("Web access", "the assistants may search the public web, but only on public terms: supplier names, CVEs, standards. Euronext identifiers, assessment ids and internal markers are never sent outbound, a detective KQL alert watches for it, and the fact that Bing/Web Search sits outside the Azure compliance boundary (the DPA does not apply) is written into the RoPA rather than assumed away."),
  BB("Sensitivity labelling", "every delivered report is labelled through Microsoft Purview at the moment it is stored, so downstream DLP and Copilot honour the classification."),
  BB("Memory", "durable team memory holds identifiers and generic notes only — never report content or personal data — with a 24-month retention cap and per-note deletion."),
  H2("6.3 Standards and regulation"),
  table(["Framework", "How this platform answers it"], [
    ["ISO/IEC 27001:2022", "A.5.16 identity, A.5.23 cloud services, A.8.6 capacity, A.8.12 data leakage, A.8.15 logging, A.8.16 monitoring, A.8.24 cryptography — each mapped to a control in convertion/governance/ with its evidence path"],
    ["ISO/IEC 42001:2023", "An AI management system in practice: documented operating parameters per agent, human oversight, change gates, evaluation against a golden set, and an incident and improvement loop"],
    ["EU AI Act", "Deployer duties (Art. 26): use per instructions, human oversight (Art. 14), logging and transparency; the platform's own classification and the reasoning behind it are recorded"],
    ["DORA", "Art. 9 ICT risk controls and resource use, Art. 28 third-party evidence retention ≥ 1 year, and the assurance workflows that feed the Register of Information"],
    ["NIS2 / GDPR", "Art. 21 measures reflected in the control set; Art. 28 processor terms and the SCC position documented for every external dependency"],
  ], [2200, 7160]),

  H1("7. Benefits, Cost and Measurement"),
  H2("7.1 Benefits"),
  BB("Assurance capacity", "the heavy reading — evidence trees, SOC reports, penetration tests, OneTrust exports — is drafted in minutes and reviewed by a person, so the team's time goes to judgement rather than transcription."),
  BB("Consistency", "one set of templates, thresholds and scoring rules, applied the same way every time, with the scores computed by code rather than estimated in prose."),
  BB("Defensibility", "each deliverable carries its sources, its audit artefacts and the identity of the person who approved it."),
  BB("Reach", "the assistants see Confluence, Jira, the CMDB, OneTrust, Defender and SharePoint — read-only — so answers reflect the estate as it is."),
  H2("7.2 Cost model"),
  P("The platform is metered, budgeted and alerted. The dominant line is model inference, and it is controlled by routing each task to the cheapest tier that can do it well, by rendering every file with code rather than tokens, and by explicit per-agent inference profiles. The second line is observability, controlled by a retention split that keeps the evidence horizon at archive prices."),
  table(["Line", "Control of record"], [
    ["Model inference", "Three tiers (light/chat/reasoning) with a per-agent assignment; request-time profiles bounding effort and output; prompt-caching discipline; monthly tier-tuning review"],
    ["Observability", "90-day interactive retention, 365-day total retention in the archive tier; no ingestion cap, because dropping telemetry would drop security evidence"],
    ["Orchestration", "One Logic Apps plan for every workflow; every loop bounded so throttling does not turn into retry cost"],
    ["Document rendering", "Deterministic generators in the delivery Function — a delivered file costs zero completion tokens"],
    ["Evidence re-analysis", "Delta re-analysis: a reassessment reads only the evidence whose content actually changed"],
  ], [2400, 6960]),
  H2("7.3 What is measured"),
  table(["Indicator", "Query / source", "Why it matters"], [
    ["Tokens and cost per agent per deliverable", "operations/kql/latency-and-tokens.kql", "Drives the monthly tier-tuning decision"],
    ["Prompt-cache hit rate", "operations/kql/prompt-cache-hit-rate.kql", "A fall means a per-run value entered an agent's instructions — a defect, not a price"],
    ["Verifier fail rate", "operations/kql/verifier-fail-rate.kql", "Quality signal on the producing agents"],
    ["Approval SLA", "operations/kql/approval-sla.kql", "Deliverables waiting on people, not on the platform"],
    ["Egress markers", "operations/kql/egress-detection.kql", "Detective control on the web-search boundary"],
  ], [2600, 3400, 3360]),

  H1("8. Risks and How They Are Held"),
  table(["Risk", "Holding control", "Residual position"], [
    ["An AI-drafted report contains an unsupported claim", "Verifier grounding rule + human approval + per-item source citation", "Accepted: a person signs every deliverable of record"],
    ["Prompt injection through supplier evidence or a web page", "Indirect-attack detection on web-facing agents, injection-resistant instruction gate, read-only tools, no write path to abuse", "Accepted and monitored"],
    ["Euronext data reaching a public search engine", "Sanitise-then-search rule, outbound marker inspection, detective KQL alert, documented DPA gap", "Accepted for public-term queries only; risk owner named"],
    ["A model version changes and deliverables change with it", "Pinned versions with NoAutoUpgrade; a migration runs the golden set before any switch", "Controlled; two tiers have a 2027 retirement to plan for"],
    ["Platform change breaks a control", "Automated gate set on every change (fidelity, residency, read-only, secrets, tests) plus owner review and segregation of duties", "Controlled"],
    ["Key-person dependency on the owner", "Documented runbooks, infrastructure-as-code, deputy approver, onboarding/offboarding procedure", "Reduced; the deputy is named in CODEOWNERS"],
  ], [2600, 4200, 2560]),

  H1("9. Implementation Plan"),
  P("The plan is a sequence of gated steps, each producing evidence before the next begins. The infrastructure is deployed from code, the agents are converted and verified before they reach the tenant, and go-live is a hypercare period rather than a switch."),
  ...image(IMG("05-implementation-roadmap.png"), "Figure 2 — Implementation roadmap: preparation, landing zone, agents, integration, go-live and steady state"),
  table(["Phase", "What happens", "Exit evidence"], [
    ["0 — Prerequisites", "Subscription, groups, quota, licences, decisions D1–D10 recorded (including the web-search risk acceptance)", "Signed decision record"],
    ["1 — Landing zone", "Network, private endpoints, DNS, Key Vault, policy assignments in audit mode", "Policy compliance export"],
    ["2 — Foundry", "Account, project, three model deployments (EU Data Zone, pinned), guardrail policies", "Deployment outputs + portal checklist"],
    ["3 — Identity", "Entra groups, RBAC, PIM, agent identities registered", "Access register"],
    ["4 — Connections", "20 read-only connections; secrets in Key Vault; read-only proof per spec", "attach_integrations dry-run output"],
    ["5 — Delivery", "SharePoint taxonomy, delivery Function, sensitivity labels, lists", "Folder rule and label verified on a test report"],
    ["6 — Agents", "Conversion, fidelity verification, agent creation, profiles, versions pinned", "verify_conversion + agent-versions ledger"],
    ["7 — Workflows", "Logic Apps deployed, approval webhooks wired, pipelines pinned to agent versions", "End-to-end run of one report type"],
    ["8 — Guardrails & evaluation", "Monitoring, alerts, evaluation golden set, red-team plan", "First evaluation report"],
    ["9 — User surfaces", "MCP server, Teams / M365 Copilot publication for the advisory agents", "User acceptance per system"],
    ["10 — Go-live & hypercare", "Phased rollout, daily checks, then the monthly and quarterly operating rhythm", "Hypercare exit report"],
  ], [1700, 4700, 2960]),
  P("The detailed, command-level procedure for each phase is the implementation series in convertion/enterprise/series/00–10, which Part II summarises."),

  // ============================ PART II ============================
  ...PART("PART II", "For Implementers", "Microsoft Foundry architecture, agents, connections, pipelines, deployment and operations"),

  H1("10. Target Architecture"),
  P("The platform is a workload-owned Foundry landing zone: the platform team owns hub networking, DNS and policy; the workload owner owns the Foundry account, its project, the agents and the connections. Users reach the platform through three surfaces — the MCP server, Microsoft 365 Copilot / Teams, and the Logic Apps pipelines — and all three converge on the same agents, tools and gates."),
  ...image(IMG("01-solution-architecture.png"), "Figure 3 — Solution architecture: access surfaces, orchestration, agents, knowledge and tools, Azure foundation"),
  H2("10.1 Resource inventory"),
  table(["Resource", "Name pattern", "Provisioned by", "Notes"], [
    ["Foundry account + project", "{baseName}-aif / {baseName}-proj", "infra/main.bicep", "Entra-only (disableLocalAuth); capability host and network injection set at creation — neither can be added later"],
    ["Model deployments", "gpt-4o · o4-mini · gpt-4o-mini", "infra/main.bicep", "DataZoneStandard SKU, pinned versions, NoAutoUpgrade"],
    ["Guardrail policies", "infosec-security-analysis · infosec-web-facing", "infra/main.bicep", "The web-facing policy adds indirect-attack (XPIA) detection and is assigned per agent"],
    ["Agent state (standard setup)", "{baseName}-cosmos · {baseName}-search", "infra/agent-stores.bicep", "Customer-owned conversations, agent definitions and vector/knowledge indexes; 90-day TTL on run state"],
    ["Delivery Function", "{baseName}-fn-delivery", "infra/delivery.bicep", "The only identity that writes to SharePoint; renders DOCX/XLSX/PPTX/HTML and PDF"],
    ["Office toolchain", "office-tools container", "infra/delivery.bicep", "LibreOffice/pandoc conversions and the XLSX recalculation gate, isolated from the credential-holding app"],
    ["Workflows", "{baseName}-la (Logic Apps Standard)", "infra/main.bicep", "One plan carries all 17 workflow definitions"],
    ["Network", "{baseName}-vnet + snet-pe/apps/aca/agents", "infra/network.bicep + enterprise/landing-zone.bicep", "Agent egress leaves through a delegated subnet the hub firewall can see"],
    ["Key Vault / Storage / Log Analytics / App Insights", "{baseName}-kv · {baseName}sa · -logs · -appi", "infra/main.bicep", "CMK from the vault; retention split 90 d interactive / 365 d total"],
    ["Policy + Defender for AI", "subscription scope", "enterprise/azure-policy-assignments.bicep · infra/defender-ai.bicep", "Preventive policy (no Global SKUs, EU locations, no local auth) and AI threat protection"],
  ], [2100, 2000, 2200, 3060]),
  P("Thirteen Bicep modules plus two enterprise templates describe all of it; convertion/infra/validate.sh builds, lints and policy-checks them offline before any deployment."),

  H1("11. Model Tiers and Inference Profiles"),
  P("Two decisions govern every model call: which model serves an agent, and how that model is called. They are separate records because they change for different reasons."),
  H2("11.1 Tiers"),
  table(["Tier", "Deployment of record", "Assigned to", "Why"], [
    ["light", "gpt-4o-mini", "Routing, deterministic transformation into a fixed schema, document toolkits", "The template carries the quality; the model only has to be exact"],
    ["chat", "gpt-4o", "Templated deliverables: DPIA, CISO reporting, slide generators, Form B, template manager", "Verified extraction rules plus a fixed template"],
    ["reasoning", "o4-mini", "OSINT research, evidence/SOC/pentest analysis, scoring, regulatory advisory, orchestration, verification", "Judgement is the product — and the model must be able to carry the tool surface"],
  ], [1100, 2000, 3600, 2660]),
  P("Tool support is part of the routing rule, not a footnote: o3-mini supports none of the OpenAPI, MCP, AI Search, SharePoint or Web Search tools that every reasoning agent carries, so pinning the reasoning tier to it would produce agents that answer without ever calling a tool. The deployment script refuses that combination outright."),
  H2("11.2 Inference profiles"),
  P("Every agent runs with an explicit profile rather than service defaults. The profile is a property of the agent's behavioural class, so it survives a change of tier model; the resolver returns only the parameters the model family accepts, because o-series reasoning models take a reasoning effort and reject sampling parameters, and the gpt-4o family is the reverse."),
  table(["Class", "Agents", "Determinism", "Effort", "Output ceiling", "Retrieval"], [
    ["router", "control centre, orchestrator", "0.0", "low", "512", "3 @ 0.5"],
    ["file-transform", "docx, pdf, pptx, xlsx, morning, whisperx", "0.0", "low", "4 096", "5 @ 0.5"],
    ["report", "dpia, ciso-reporting, exec summary, slide generators, form B, template manager", "0.1", "medium", "16 384", "8 @ 0.45"],
    ["analysis", "deepsearch ×2, ciso-global, tpa/soc/pentest analyzers, pdf coverage, tpsrca", "0.0", "high", "32 768", "12 @ 0.4"],
    ["advisory", "cyber-forum, advisor, iso27001, iso42001, dora, nis2, eu-ai-act, learn", "0.2", "high", "32 768", "12 @ 0.4"],
    ["verifier", "output-verifier", "0.0", "medium", "2 048", "6 @ 0.5"],
  ], [1300, 3300, 1150, 900, 1300, 1410]),
  P("Anything whose output is diffed, scored or compared samples at zero, so the same evidence yields the same score and a reviewer can reproduce it. The output ceiling is a runaway guard sized from each deliverable's JSON schema — a truncated response is a verifier FAIL, never a shipped deliverable, so the remedy is to raise the ceiling and investigate the prompt, never to trim the schema."),
  P("Instructions are also a cached prefix: they carry the persona and the charter only, never a date, run id or supplier name, so the cache survives between calls. A CI test enforces it and a KQL query measures the hit rate."),

  H1("12. Agents and the Conversion Pipeline"),
  H2("12.1 Inventory"),
  table(["Group", "Count", "Examples"], [
    ["Converted GRC/TPRM specialists", "18", "deepsearch-protocol, dpia, ciso-reporting, ciso-executive-summary, onetrust-form-b, cyber-forum, iso27001, iso42001, dora, nis2, eu-ai-act, tpsrca-assessment-engine, pdf-full-coverage-analyzer, tprm-slide-generator, enx-tprm-control-center"],
    ["Document toolkits", "4", "docx, pdf, pptx, xlsx — code-interpreter production agents"],
    ["Delivery agents (requirements d, d2, e, f, j)", "5", "ciso-global-report, tpa-evidence-analyzer, soc-report-analyzer, pentest-report-analyzer, template-manager"],
    ["Platform agents", "3", "infosec-assurance-orchestrator (routing and decomposition), infosec-assurance-advisor (reasoning generalist with combined knowledge and durable memory), output-verifier"],
    ["TPSRCA sub-agents", "2", "tpsrca-calc (deterministic scoring, carries calculation_engine.py) and tpsrca-analysis"],
  ], [2900, 700, 5760]),
  P("Thirty-six agents are registered with their tier, tools and guardrail policy in convertion/integrations/registry.json; thirty-eight carry an inference-profile class. Hand-off between them is A2A / Agent Framework — Connected Agents no longer exist in the service — and every deliverable hand-off passes through the verifier."),
  H2("12.2 Conversion and fidelity"),
  P("An agent is not authored here; it is converted. SKILL.md becomes the instructions, references become the vector store, scripts and assets become code-interpreter files, and the persona, overlays and approval gate are prepended. The verification step then hashes every instruction, template and generator against the export: a definition that drifted cannot reach the tenant."),
  ...image(IMG("02-conversion-pipeline.png"), "Figure 4 — The gated conversion and deployment pipeline with its reliability substrate"),
  BB("Runtime", "the GA Responses API (agents / conversations / responses). The classic threads-and-runs surface retires 2027-03-31 and exists in the kit only as a documented fallback that warns on use."),
  BB("Versioning", "every save produces an immutable agent version; pipelines pin <agent>:<version>, and a nightly drift check compares the live version against the ledger."),
  BB("Reliability", "exponential-backoff retries, parallel uploads, a content-hash upload cache and per-agent failure isolation."),

  new Paragraph({ children: [new PageBreak()] }),
  H1("13. Connections and Integrations"),
  P("Twenty connections give the agents reach into the Euronext estate. Every one of them is read-only by construction: the deployment script strips each non-GET operation from the OpenAPI specification before it ever becomes a tool, and the five surviving POST operations are query operations (JQL, AQL, KQL hunting, Graph search, code search) explicitly allow-listed because they are the only way to ask those systems a question. No connection carries a write grant."),
  ...image(IMG("04-integration-map.png"), "Figure 5 — Interconnections with the Euronext technology stack"),
  table(["Connection", "System", "What the agents read"], [
    ["confluence-cloud", "Confluence Cloud", "Spaces, pages, search — policy and standard content"],
    ["jira-cloud", "Jira Cloud", "Issues and JQL search — findings and remediation state"],
    ["jira-assets-cmdb", "Jira Assets", "CMDB objects via AQL — services, owners, dependencies"],
    ["sharepoint-graph", "SharePoint (Graph)", "Drives, folders, items, drive-scoped search — the evidence library"],
    ["sharepoint-grounding", "SharePoint tool (preview)", "Registered, disabled by default: permission-trimmed citations for interactive advisors only"],
    ["onetrust", "OneTrust", "Assessments, inventories, risks — the source for requirements b, c, d"],
    ["defender-graph", "Microsoft Defender (Graph security)", "Alerts, incidents and advanced hunting"],
    ["entra-iam-graph", "Entra ID (Graph)", "Directory, groups, roles — identity context for assessments"],
    ["exchange-graph", "Exchange (Graph)", "Evidence that arrives by e-mail, as metadata"],
    ["teams-graph", "Teams (Graph)", "Channel context for notifications"],
    ["m365-personal-graph", "M365 personal scope", "The requesting user's own calendar/mail for the morning brief"],
    ["azure-devops", "Azure DevOps", "Work items and code search"],
    ["securityscorecard", "SecurityScorecard", "External ratings and issue detail for supplier assessments"],
    ["iaf-api", "Internal assurance API (IAF)", "Euronext's own assurance data"],
    ["enx-gateway-mcp", "ENX gateway (MCP)", "The internal MCP server, read-only tools only"],
    ["osint-proxy", "Delivery Function", "Public supplier pages (Trust Center, DPA, subprocessor lists) through a policed proxy"],
    ["passive-recon", "Delivery Function", "Strictly passive DNS/TLS/header fingerprint of a public domain — no scan, no crawl"],
    ["evidence-cache", "Delivery Function", "Facts already extracted from unchanged evidence — the delta re-analysis path"],
    ["web-search", "Bing grounding / Web Search", "Public terms only; outside the Azure compliance boundary and recorded as such"],
    ["followup-scheduler", "Delivery Function", "Registered and disabled: a scheduling surface that is deliberately not an agent tool"],
  ], [1750, 2400, 5210]),
  P("Secrets never appear in the repository or in a workflow body: each connection resolves its credential from Key Vault through a Foundry project connection, and the platform's own identities are managed identities and OIDC federated credentials."),

  H1("14. Workflows and the Delivery Pipeline"),
  P("Seventeen Logic Apps definitions plus a pipelines manifest replace the claude.ai Routines and carry every delivery. One generic delivery pipeline is instantiated twelve times — once per deliverable type — so the approval gate, the storage rule, the labelling and the audit trail exist once and cannot drift between report types."),
  ...image(IMG("06-workflow-schematics.png"), "Figure 6 — Automated workflows and their human-approval gates"),
  H2("14.1 The twelve delivery pipelines"),
  table(["Pipeline", "Req", "Producing agent", "Output"], [
    ["deepsearch-report", "a", "deepsearch-protocol", "HTML dashboard"],
    ["ai-deepsearch-report", "a", "ai-deepsearch-osint-gathering-report", "HTML dashboard"],
    ["dpia-dpo-report", "b", "dpia", "DOCX for the DPO"],
    ["cyber-forum-pptx", "c", "ciso-reporting", "PPTX governance deck"],
    ["ciso-exec-summary", "c/d", "ciso-executive-summary", "HTML executive dashboard"],
    ["ciso-global-pptx", "d", "ciso-global-report", "9-slide PPTX"],
    ["tpa-evidence-analysis", "d2", "tpa-evidence-analyzer", "DOCX evidence register"],
    ["soc-report-summary", "e", "soc-report-analyzer", "DOCX findings summary"],
    ["pentest-report-summary", "f", "pentest-report-analyzer", "DOCX findings summary"],
    ["advisory-file-delivery", "g/h", "any advisory agent (pinned by reference)", "DOCX/XLSX/PPTX/HTML"],
    ["cyber-forum-brief", "c", "cyber-forum", "DOCX threat-intel brief"],
    ["transcript-summary", "—", "whisperx-transcribe-diarize", "DOCX transcript"],
  ], [2300, 700, 3400, 2960]),
  H2("14.2 What one delivery run does"),
  table(["Step", "Action", "Control"], [
    ["1", "Resolve supplier and service names; refuse to continue without them", "The storage rule cannot be bypassed by omission"],
    ["2", "Create a conversation and run the producing agent in the background, polling to completion", "Agent pinned to a version; profile applied per request"],
    ["3", "Run the output-verifier on the draft", "PASS/FAIL against deterministic rules; FAIL notifies and stops — no regeneration loop"],
    ["4", "Suspend on the human-approval webhook", "Approver identity recorded; expiry bounded"],
    ["5", "Render the verified JSON into the final file", "Deterministic generators; XLSX passes a recalculation gate"],
    ["6", "Ensure Reports/<Supplier>/<Service>/ and upload", "Supplier folder reused, service folder created if missing, race-safe"],
    ["7", "Apply the Purview sensitivity label", "Classification travels with the file"],
    ["8", "Upload audit artefacts, update the portfolio and score history, notify Teams", "The report names its own evidence; the register stays current"],
    ["9", "Store the evidence facts (requirement d2 only)", "Written only after approval, so the next assessment reads the delta"],
  ], [500, 4600, 4260]),
  H2("14.3 The other workflows"),
  table(["Workflow", "Trigger", "Purpose"], [
    ["onetrust-assessment-intake", "Schedule", "New completed assessments → the right report pipeline"],
    ["defender-incident-brief", "Event", "Incident → cyber-forum brief for the team"],
    ["scheduled-deepsearch", "Schedule", "Watchlist suppliers reassessed on a cadence"],
    ["jira-finding-sync", "Schedule", "Finding state synchronised from Jira, read-only"],
    ["mailbox-intake", "Schedule", "Evidence that arrives by e-mail filed for human triage"],
    ["template-update-approval", "Request", "Requirement j: visual before/after review, sample render, verifier, then apply"],
    ["scheduled-evaluation-redteam", "Schedule", "Weekly golden-set evaluation and red-team run"],
    ["memory-retention", "Schedule", "Retention sweep over durable memory"],
    ["agent-fanout · watch-until · report-status · generic-event-intake · teams-post-approved · speech-transcription · morning-brief · scheduled-followup", "Various", "Platform utilities: bounded parallel hand-off, polling, status, event intake, notification, transcription, personal brief, follow-up"],
  ], [2900, 1400, 5060]),
  P("Every loop in every workflow declares a concurrency bound and the API limit it respects; a CI gate fails the build if a new one does not, because an unbounded loop against a rate-limited API is both slower and more expensive than a small steady number of branches."),

  H1("15. Delivery, Storage and the Evidence Cache"),
  H2("15.1 The storage taxonomy"),
  table(["Purpose", "Path", "Written by"], [
    ["Assessment reports", "Reports/<Supplier>/<Service>/", "Delivery Function, after approval"],
    ["DPO deliverables", "Reports/DPO/<Supplier>/<Service>/", "Delivery Function (unique permissions)"],
    ["Advisory deliverables", "Advisory/<Framework-or-Topic>/<Subtopic>/", "Delivery Function"],
    ["Audit artefacts", "Reports/<Supplier>/<Service>/audit/<date>/", "Delivery Function"],
    ["Evidence library (read-only input)", "Infosec Assurance/GRC/TPA/Active/<Supplier>[/<Service>]/", "People — the platform only reads it"],
    ["Templates and reviews", "Templates/ and Templates/Reviews/", "Delivery Function after a template approval"],
  ], [2600, 4200, 2560]),
  P("Three SharePoint lists carry state the team relies on: the TPRM portfolio, the TPSRCA score history, and the evidence cache. All three are written exclusively by the delivery Function's managed identity, after approval — no agent and no connector can write to them."),
  H2("15.2 Delta re-analysis of evidence"),
  P("The evidence analysis (requirement d2) is the heaviest recurring run: a whole supplier tree read on the reasoning tier with a chunked full-coverage method. Between two assessments almost none of those files change, so the platform reads the delta rather than the tree. Before reading a file the analyzer asks the cache what a previously approved run extracted from it; a match on the SharePoint eTag means the bytes are identical and the facts can be reused."),
  BB("What is cached", "facts a reader cannot recompute: document type, issuer, content identification, scope statement, emission date, validity window, findings."),
  BB("What is never cached", "anything time-dependent. VALID / EXPIRING ≤ 90 days / EXPIRED / period-gap are recomputed against each report date, because a certificate valid in March is not valid in September."),
  BB("How it stays honest", "three invalidations — a changed eTag, a changed extractor version, and age; a cached finding that would drive a HIGH or CRITICAL verdict must be re-read before it decides anything; and every inventory row is marked fresh or reused with the run it came from, so the approver sees the provenance they are signing."),

  H1("16. Security Controls in Implementation Terms"),
  table(["Control", "Implementation", "Verification"], [
    ["Read-only enterprise access", "Non-GET operations stripped at attach time; MCP tools carry readOnlyHint; no write_connections grant exists", "attach_integrations.py --dry-run prints [read-only] per tool; verify_conversion audits what survived"],
    ["Human approval before every write", "HttpWebhook suspension in the delivery pipeline; the writing identity is only reached after the callback", "An end-to-end run; the approval record in the list"],
    ["Independent verification", "output-verifier agent, deterministic rules, PASS/FAIL, generates nothing", "verifier-fail-rate.kql; golden-set evaluation"],
    ["Prompt-injection resistance", "infosec-web-facing guardrail policy with indirect-attack detection, assigned per agent; instruction-level gate; read-only tools", "Portal agent checklist; red-team run"],
    ["EU residency", "DataZoneStandard SKUs, EU-only regions, BYO EU stores, Azure Policy denying Global SKUs", "ci/tests/test_residency.py (7 offline checks) and the policy compliance export"],
    ["Encryption", "Customer-managed key from the project's Key Vault on the account, storage, Cosmos DB and AI Search; versionless URI, annual rotation", "Deployment pass 2 outputs"],
    ["Network", "Private endpoints for inbound; agent egress through a delegated subnet with an FQDN allow-list on the hub firewall", "Deployment what-if; firewall rule set"],
    ["Secrets", "Key Vault-backed connections; managed identities and OIDC federated credentials; nothing in the repository", "gitleaks over the tree and the history; scan_secrets.py"],
    ["Auditability", "Traces, token metrics, approval records, audit artefacts per report; 365-day total retention", "Log Analytics queries; the evidence pack exported quarterly"],
  ], [2000, 4200, 3160]),

  H1("17. Identity, RBAC and Segregation of Duties"),
  table(["Principal", "Grant", "How"], [
    ["Assurance users (5)", "Foundry User on the project; read on the deliverable libraries", "Entra group sg-infosec-foundry-users"],
    ["Accountable owner", "Foundry Owner / platform administration, elevated through PIM rather than standing", "sg-infosec-foundry-owner + sg-infosec-foundry-admin-pim"],
    ["Report approvers", "Approve report deliverables per the approval matrix", "sg-infosec-foundry-report-approvers"],
    ["Delivery Function identity", "Sites.Selected WRITE on the one InfoSec Assurance site plus the metered label API — the only writer in the platform", "Managed identity, granted per site"],
    ["Foundry project identity", "Read on the enterprise connections; agent identities registered and inventoried", "Managed identity + Entra Agent ID"],
    ["CI/CD", "Deploy with OIDC federated credentials; no stored secret", "GitHub Actions environment with the owner's approval"],
  ], [2200, 4200, 2960]),
  P("Segregation of duties is enforced where it matters: CODEOWNERS requires the deputy approver on team, governance, operations, infrastructure and CI changes, so the accountable owner cannot self-approve a change to the controls that bind them."),

  H1("18. Deployment"),
  P("Two deployment surfaces exist and they are deliberately the same steps: convertion/deploy.sh for an operator, and the CI pipelines for the automated path. The detailed procedure is the eleven-part implementation series."),
  table(["Step", "Command / template", "Produces"], [
    ["Infrastructure", "infra/main.bicep (+ enterprise/landing-zone.bicep, azure-policy-assignments.bicep)", "The landing zone, in two passes because the capability host, the network injection and the CMK cannot all be set at once"],
    ["Connections", "integrations/connections/create_connections.sh", "Twenty project connections resolving secrets from Key Vault"],
    ["Conversion", "scripts/convert_skills.py → verify_conversion.py", "Agent definitions, byte-verified against the export"],
    ["Agents", "scripts/create_agents.py · create_delivery_agents.py · create_orchestrator.py", "Agents with instructions, knowledge, tools, profiles and versions"],
    ["Profiles and tools", "scripts/attach_integrations.py · apply_advisory_profile.py", "Tier model applied, read-only tools attached, inference profile stamped"],
    ["Renderers", "scripts/stage_renderers.py --strict", "The byte-verified generators staged into the delivery Function image"],
    ["Workflows", "ci/deploy_logicapps.sh", "Seventeen definitions and twelve pipeline instances pinned to agent versions"],
    ["Verification", "scripts/verify_deployment.py", "Live state compared against the version ledger"],
  ], [1700, 3700, 3960]),

  H1("19. Change Control and the Gate Set"),
  P("Every change to the platform passes an automated gate set before a human reviews it. The gates are offline: they need no Azure session, so they run on every pull request in seconds and cannot be skipped by a reviewer in a hurry."),
  table(["Gate", "What it proves"], [
    ["Conversion + fidelity", "Every agent still matches the byte-verified export"],
    ["Kit consistency", "No secret, no unparsable file, every cross-reference resolves"],
    ["Syntax + shell lint", "Python, JSON, YAML, JavaScript, Bicep and shell all parse and lint"],
    ["EU residency", "No template, parameter file or policy assignment can route outside the EU"],
    ["Workflow efficiency", "Every loop declares a concurrency bound"],
    ["Self-knowledge", "The platform's description of itself matches what is deployed"],
    ["Inference profiles", "Every registered agent resolves to legal parameters on its tier model"],
    ["Test suites", "The delivery Function, the office toolchain and the scripts, including the controls' own failure modes"],
    ["Infrastructure policy", "Bicep builds and lints; the policy decisions hold"],
    ["Secret scan", "gitleaks over the working tree and the history"],
  ], [2600, 6760]),
  P("Change classes are explicit: a patch is self-service, a peer-approved change needs a second pair of eyes, and an owner-only change — a model tier, a guardrail, a template of record — needs the owner and re-runs the golden set before it serves traffic."),

  H1("20. Operations"),
  H2("20.1 Operating rhythm"),
  table(["Cadence", "Activity"], [
    ["Daily (hypercare)", "Pipeline failures, verifier fails, approval queue, egress alerts"],
    ["Weekly", "Evaluation and red-team run; backlog triage"],
    ["Monthly", "Tier tuning against token, latency and cache telemetry; cost review against budget; access review"],
    ["Quarterly", "Platform currency review (model retirements, preview→GA transitions, region availability, Claude residency re-check); policy compliance export; DR test"],
  ], [1800, 7560]),
  H2("20.2 Monitoring and alerting"),
  P("Traces and metrics flow to Log Analytics and Application Insights. Alerts cover delivery failures, verifier fail-rate spikes, latency and token budgets, approval expiry, egress markers and Defender for AI detections, routed to the owner or the SOC by severity."),
  H2("20.3 Resilience and retention"),
  BB("Retention", "90 days interactive, 365 days total in the archive tier — the DORA Art. 28 evidence horizon at archive prices. The ingestion cap stays off on purpose: a cap drops telemetry, and the dropped items would include the egress detector's own data."),
  BB("Backup and recovery", "agent definitions, connections and the version ledger are exportable artefacts; the runbook covers redeploying a previous release tag."),
  BB("Housekeeping", "conversations, orphan files and stores, and durable memory notes are swept against retention horizons that live in configuration, not in code."),
  H2("20.4 Optimisation register"),
  P("What has been optimised, what was examined and left alone, and what remains open with a decision, is a standing record: convertion/operations/FOUNDRY_OPTIMIZATION_REGISTER.md. Its current open items are the 2027 model retirements on two tiers (a six-phase migration with the golden set, not a swap), the knowledge-source switch (gated on measurement), a domain-restricted web search pilot, and two logging tiers awaiting a month of actuals."),

  // ---- Appendices ----
  new Paragraph({ children: [new PageBreak()] }),
  H1("Appendix A — Requirement Traceability"),
  table(["Req", "Agent", "Contract / template", "Pipeline", "Storage"], [
    ["a", "deepsearch-protocol · ai-deepsearch-osint-gathering-report", "deepsearch_dashboard schema", "deepsearch-report · ai-deepsearch-report", "Reports/<Supplier>/<Service>/"],
    ["b", "dpia", "dpia_report schema → dpia renderer", "dpia-dpo-report", "Reports/DPO/<Supplier>/<Service>/"],
    ["c", "ciso-reporting · ciso-executive-summary · cyber-forum", "ciso_reporting_assessment · ciso_exec_summary_render", "cyber-forum-pptx · ciso-exec-summary · cyber-forum-brief", "Reports/<Supplier>/<Service>/ · Reports/General/Threat-Intel/"],
    ["d", "ciso-global-report", "ciso_global_deck schema → ciso-global renderer", "ciso-global-pptx", "Reports/<Supplier>/<Service>/"],
    ["d2", "tpa-evidence-analyzer", "evidence_summary schema (+ cacheRecords)", "tpa-evidence-analysis", "Reports/<Supplier>/<Service>/ (+ audit/)"],
    ["e", "soc-report-analyzer", "evidence_summary schema", "soc-report-summary", "Reports/<Supplier>/<Service>/"],
    ["f", "pentest-report-analyzer", "evidence_summary schema", "pentest-report-summary", "Reports/<Supplier>/<Service>/"],
    ["g", "iso27001 · iso42001 · dora · nis2 · eu-ai-act · advisor", "docx/xlsx/pptx generic schemas", "advisory-file-delivery", "Advisory/<Framework>/<Subtopic>/"],
    ["h", "infosec-assurance-advisor · tpsrca engine", "same", "advisory-file-delivery", "Advisory/"],
    ["i", "all agents", "read-only toolset (20 connections)", "—", "—"],
    ["j", "template-manager", "templates/registry.json", "template-update-approval", "Templates/ + Templates/Reviews/"],
  ], [420, 2400, 2100, 2200, 2240]),

  new Paragraph({ children: [new PageBreak()] }),
  H1("Appendix B — Repository Map"),
  table(["Path", "Contents"], [
    ["claude-account-export/", "Source of truth: the complete account export (35 skills, persona, capabilities) — never edited"],
    ["convertion/agents/", "Persona, charters, overlays, knowledge packs, advisor knowledge"],
    ["convertion/scripts/", "Conversion, creation, attachment, verification, profiles, memory, cleanup, staging"],
    ["convertion/infra/ · enterprise/", "Thirteen Bicep modules, landing zone, policy, the implementation series 00–10"],
    ["convertion/integrations/", "registry.json, 17 OpenAPI specs, connections, MCP, Copilot"],
    ["convertion/workflows/", "Seventeen Logic Apps definitions plus pipelines.json"],
    ["convertion/functions/", "Delivery Function (the single writer) and the office toolchain"],
    ["convertion/templates/", "Thirteen registered templates, their schemas, samples and themes"],
    ["convertion/governance/ · team/ · operations/", "Approval policy, data protection, model routing, inference profiles, team model, runbooks, FinOps, optimisation register"],
    ["convertion/ci/ · .github/", "The gate set, in two pipelines that run the same scripts in the same order"],
    ["project-dossier/", "This document, its diagrams and their generators — build outputs, never hand-edited"],
  ], [2900, 6460]),

  H1("Appendix C — Glossary"),
  table(["Term", "Meaning here"], [
    ["Agent", "A Foundry prompt agent: instructions, a model, knowledge and tools, saved as an immutable version"],
    ["A2A hand-off", "Agent-to-agent delegation; replaces Connected Agents, which no longer exist in the service"],
    ["Responses API", "The GA data plane (agents / conversations / responses); classic threads and runs retire 2027-03-31"],
    ["Inference profile", "The request-time parameters an agent runs with: determinism, reasoning effort, output ceiling, retrieval width"],
    ["Verifier", "An agent that checks a draft against deterministic rules and returns PASS or FAIL; it never rewrites"],
    ["Delivery pipeline", "The Logic App that takes a request to a stored, labelled, approved deliverable"],
    ["Golden set", "Known-good deliverables used to prove a change did not alter output quality"],
    ["Delta re-analysis", "Reading only the evidence whose content changed since the last approved assessment"],
    ["TPSRCA", "The team's third-party security risk and controls assessment methodology"],
  ], [2400, 6960]),

  H1("Appendix D — References"),
  B("convertion/REQUIREMENTS.md — requirements a–j and where each is satisfied"),
  B("convertion/ARCHITECTURE.md · README.md · MAPPING.md — design, conversion guide, per-skill mapping"),
  B("convertion/enterprise/ENTERPRISE_BLUEPRINT.md and series/00–10 — the target architecture and the command-level implementation series"),
  B("convertion/governance/HUMAN_APPROVAL.md · DATA_PROTECTION_GUARDRAILS.md · MODEL_ROUTING.md · INFERENCE_PROFILES.md · MEMORY_POLICY.md · CLAUDE_ON_FOUNDRY.md"),
  B("convertion/team/TEAM_MODEL.md · ACCESS_REGISTER.md · sharepoint-permissions.md — people, roles and grants"),
  B("convertion/operations/RUNBOOK.md · MONITORING.md · FINOPS.md · LIFECYCLE.md · BACKUP_DR.md · OPTIMIZATION_REVIEW.md · FOUNDRY_OPTIMIZATION_REGISTER.md"),
  B("convertion/workflows/README.md · sharepoint/README.md · functions/delivery/README.md — delivery mechanics"),
  B("convertion/integrations/README.md · registry.json — the connection layer and its read-only proof"),
];
const doc = new Document({
  numbering: { config: [{ reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 420, hanging: 260 } } } }] }] },
  styles: {
    default: { document: { run: { font: "Calibri", size: 21 }, paragraph: { spacing: { line: 276 } } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 30, bold: true, color: TEAL, font: "Calibri" }, paragraph: { spacing: { before: 360, after: 160 } } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 24, bold: true, color: DARK, font: "Calibri" }, paragraph: { spacing: { before: 260, after: 120 } } },
    ],
  },
  sections: [{
    properties: { page: { margin: { top: 1200, bottom: 1200, left: 1300, right: 1300 } } },
    headers: { default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [new TextRun({ text: "InfoSec Assurance Agent Platform — Project Dossier · Internal", size: 16, color: GREY })] })] }) },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ children: ["Page ", PageNumber.CURRENT, " of ", PageNumber.TOTAL_PAGES], size: 16, color: GREY })] })] }) },
    children,
  }],
});

Packer.toBuffer(doc).then((b) => {
  fs.writeFileSync(path.join(__dirname, "Project-Dossier-InfoSec-Assurance-Agent-Platform.docx"), b);
  console.log("wrote Project-Dossier-InfoSec-Assurance-Agent-Platform.docx");
});
