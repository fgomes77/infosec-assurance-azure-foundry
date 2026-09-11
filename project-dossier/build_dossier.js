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

const children = [
  // ---- Cover ----
  new Paragraph({ spacing: { before: 2800 }, children: [] }),
  new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "PROJECT DOSSIER", bold: true, size: 30, color: GREY })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 200 }, children: [new TextRun({ text: "InfoSec Assurance Agent Platform", bold: true, size: 56, color: TEAL })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120 }, children: [new TextRun({ text: "Migration of the Claude AI GRC/TPRM toolset to Azure AI Foundry", size: 28, color: DARK })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 600 }, children: [new TextRun({ text: "Information Security Assurance — TPRM · ISMS · GRC · ICT GRC", size: 22, color: GREY })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 1600 }, children: [new TextRun({ text: "Version 1.1  ·  11 September 2026  ·  Classification: Internal", size: 20, color: GREY })] }),
  new Paragraph({ children: [new PageBreak()] }),

  // ---- Document control ----
  H1("Document Control"),
  table(["Item", "Detail"], [
    ["Title", "Project Dossier — InfoSec Assurance Agent Platform on Azure AI Foundry"],
    ["Version / Status", "1.1 — Draft for review"],
    ["Date", "11 September 2026"],
    ["Owner", "InfoSec Assurance & Third-Party Risk (F. Gomes)"],
    ["Repository", "github.com/fgomes77/infosec-assurance-azure-foundry"],
    ["Classification", "Internal — contains internal system names; no credentials or personal data"],
    ["Related artefacts", "convertion/README.md · ARCHITECTURE.md · MAPPING.md · governance/HUMAN_APPROVAL.md · governance/PERSONA-COVERAGE.md"],
  ], [2600, 6760]),
  spacer(),
  H2("Table of Contents"),
  new TableOfContents("Table of Contents", { hyperlink: true, headingStyleRange: "1-2" }),
  new Paragraph({ children: [new PageBreak()] }),

  // ---- 1 Executive summary ----
  H1("1. Executive Summary"),
  P("The InfoSec Assurance team operates a mature toolset of 35 AI skills on claude.ai covering third-party risk management (TPRM), the information security management system (ISMS), and GRC / ICT GRC advisory: OSINT supplier assessments (DeepSearch), OneTrust-driven DPIA and CISO reporting, Form B questionnaire support, and regulatory advisors for DORA, NIS2, the EU AI Act, ISO/IEC 27001 and ISO/IEC 42001. This project replicates that capability, with equal or better assurance, on Microsoft Azure AI Foundry — the platform aligned with the wider Euronext technology estate (Entra ID, Microsoft Graph, Defender, SharePoint, Jira, OneTrust)."),
  P("The delivered solution converts every skill into a Foundry agent with its knowledge, templates and scripts intact (byte-verified against the claude.ai source), adds a reasoning orchestrator and a memory-backed assurance advisor, wires the surrounding toolchain through least-privilege integrations, and enforces a three-layer human-approval control so no agent submits anything of record without a person's explicit sign-off. A one-command, verification-gated pipeline deploys and re-synchronises the whole environment."),

  // ---- 2 Background ----
  H1("2. Background and Context"),
  P("The current capability lives in the claude.ai account as skills — packaged instructions, reference knowledge (control catalogues, framework mappings, methodologies) and generation scripts. A complete export of that account is preserved in this repository under claude-account-export/ and forms the single source of truth for the conversion. The business drivers for an Azure deployment are: platform alignment with the corporate Microsoft estate and its identity model; direct, governed integration with the systems of record (Jira, OneTrust, IAF, Defender, SharePoint); enterprise observability and audit; and organisational requirements on data residency and access control."),
  P("The conversion is faithful by construction: the pipeline reads the export directly and a verification step proves, file by file, that what runs on Azure is what was authored on claude.ai."),

  // ---- 3 Objectives ----
  H1("3. Objectives"),
  BB("O1 — Functional parity", "Every claude.ai skill is available as an Azure AI Foundry agent producing the same deliverables from the same inputs (reports, dashboards, slides, questionnaire responses, advisory answers)."),
  BB("O2 — Fidelity", "Agent knowledge, templates, rules and requirements are byte-identical to the claude.ai export, provably and repeatably (automated verification, not assertion)."),
  BB("O3 — Integration", "Agents work inside the Euronext toolchain — Jira Cloud, Jira Assets CMDB, OneTrust, SecurityScorecard, Microsoft Defender, SharePoint, the internal IAF API and ENX gateway — with web search and Microsoft 365 Copilot access for team members."),
  BB("O4 — Human control", "No agent submits anything of record without explicit human review and approval, enforced technically, behaviourally and procedurally."),
  BB("O5 — Assurance quality", "High-stakes outputs pass reflexive self-checks and an independent rules-based verifier before a human ever sees the release decision."),
  BB("O6 — Operability", "One-command gated deployment; re-synchronisation from a fresh claude.ai export is the same command; full observability of runs, cost and approvals."),

  // ---- 4 Scope ----
  H1("4. Scope"),
  H2("4.1 In scope"),
  B("Conversion of the 22 assurance-relevant skills (18 custom GRC/TPRM + 4 document skills); the 13 Anthropic example skills convert on demand via a flag."),
  B("Orchestration layer (orchestrator, advisor with durable memory, output verifier), integrations, workflows, MCP access, Copilot surfacing, infrastructure as code, and the governance controls."),
  H2("4.2 Out of scope"),
  B("Claude model hosting on Azure (not offered in the Azure catalogue — see §11.4); local-hardware transcription (replaced by AI Foundry Speech); the skill excluded from the export for data-protection reasons."),

  // ---- 5 Requirements ----
  H1("5. Requirements"),
  H2("5.1 Functional requirements"),
  table(["ID", "Requirement", "Where satisfied"], [
    ["FR-01", "Convert each exported skill into an agent: SKILL.md → instructions; references → RAG vector store; scripts/assets → code interpreter", "convertion/scripts/convert_skills.py"],
    ["FR-02", "Single entry point that routes or decomposes any assurance request across specialists", "infosec-assurance-orchestrator (connected agents)"],
    ["FR-03", "Reasoning generalist covering all persona domains, grounded in the combined knowledge base, with durable team memory", "infosec-assurance-advisor + vs-assurance-memory"],
    ["FR-04", "Integrations: Jira Cloud, Jira Assets CMDB, OneTrust, SecurityScorecard, Defender (Graph), SharePoint (Graph), IAF API, ENX gateway MCP, Bing web search", "integrations/ registry + attach_integrations.py"],
    ["FR-05", "Scheduled/event workflows replacing claude.ai Routines (OneTrust intake, Defender briefs, weekly DeepSearch, Jira–IAF sync)", "workflows/ (Logic Apps definitions)"],
    ["FR-06", "MCP access for team members and internal tooling (ask, route, memory)", "mcp-server/ (FastMCP)"],
    ["FR-07", "Microsoft 365 Copilot surfacing for Q&A agents", "integrations/copilot/README.md"],
  ], [900, 5060, 3400]),
  spacer(),
  H2("5.2 Non-functional requirements"),
  table(["ID", "Requirement", "Where satisfied"], [
    ["NFR-01", "Deployment is idempotent, gated on verification, and completes as one command", "deploy.sh (six gated steps)"],
    ["NFR-02", "Resilience: retries with backoff, parallel uploads, per-agent failure isolation, upload de-duplication", "scripts/_azure_helpers.py"],
    ["NFR-03", "Cost efficiency: reasoning model (o3-mini) only for analytic agents; gpt-4o for deterministic pipelines; content-hash cache avoids duplicate uploads", "registry model tiers + upload cache"],
    ["NFR-04", "Observability: traces, token/latency metrics, approval audit trail, 90-day ISMS-aligned log retention", "App Insights + Log Analytics (Bicep)"],
    ["NFR-05", "Re-sync from a fresh claude.ai export is the standard pipeline run, with drift detection", "verify_conversion.py"],
  ], [900, 5060, 3400]),
  spacer(),
  H2("5.3 Security and compliance requirements"),
  table(["ID", "Requirement", "Where satisfied"], [
    ["SEC-01", "No credentials in the repository; secrets in Key Vault-backed Foundry connections; Entra-only auth (local auth disabled)", "Bicep + integrations/README.md"],
    ["SEC-02", "Agents technically cannot write to external systems: non-GET operations stripped from every OpenAPI tool; write grants default to zero", "attach_integrations.py (Layer 1)"],
    ["SEC-03", "Every agent carries an injection-resistant draft-then-approve instruction gate", "APPROVAL GATE block (Layer 2)"],
    ["SEC-04", "Workflows suspend on human-approval webhooks (3-day expiry) before every submission of record", "Logic Apps gates (Layer 3)"],
    ["SEC-05", "Independent output verification (PASS/FAIL against deterministic rules) before human approval", "output-verifier agent"],
    ["SEC-06", "Data minimisation in durable memory; notes timestamped, listable, individually deletable", "memory_store.py"],
    ["SEC-07", "EU AI Act Art. 14 human oversight and ISO/IEC 42001 Annex A control mapping documented with audit evidence pointers", "governance/HUMAN_APPROVAL.md"],
  ], [900, 5060, 3400]),

  // ---- 6 Goals ----
  H1("6. Goals and Success Metrics"),
  table(["Goal", "Metric", "Target"], [
    ["Fidelity", "verify_conversion.py result on every deployment", "Verified, zero discrepancies (currently: 22 agents, 252 files hash-matched)"],
    ["Parity", "UAT: deliverables vs claude.ai baselines for the same inputs", "No material deviation accepted by the team"],
    ["Human control", "Write grants in registry; submissions without an approval callback", "0 and 0"],
    ["Quality", "Verifier first-pass PASS rate on report agents", "≥ 90% steady-state; investigate on decline"],
    ["Adoption", "Assurance team members active via MCP/Copilot per month", "Full team within one quarter"],
    ["Efficiency", "Token cost per deliverable; deployment wall-clock", "Baseline in hypercare; downward trend"],
  ], [1800, 4260, 3300]),

  // ---- 7 Solution structure ----
  new Paragraph({ children: [new PageBreak()] }),
  H1("7. Solution Structure"),
  P("The platform is a five-layer architecture. Team members reach it through three access paths (MCP clients such as Claude Desktop, Microsoft 365 Copilot, and the scheduled Logic Apps workflows); all paths converge on the orchestrator, which routes to the advisor or the specialist agents; agents draw on RAG vector stores, code-interpreter scripts and read-only integration tools; everything runs on the Azure foundation provisioned by the Bicep template."),
  ...image(IMG("01-solution-architecture.png"), "Figure 1 — Solution architecture: access, orchestration, agents, knowledge & tools, Azure foundation"),
  H2("7.1 Components"),
  table(["Component", "Role"], [
    ["infosec-assurance-orchestrator", "Planner-executor entry point (o3-mini + web search); answers, routes, or decomposes across all connected agents; routes deliverable drafts through the verifier"],
    ["infosec-assurance-advisor", "Reasoning generalist across all persona domains; combined knowledge base (55 sources: every skill's knowledge + the advisor knowledge pack) + durable team memory + web search; cites sources"],
    ["output-verifier", "Independent verification layer; strict PASS/FAIL against deterministic rules; generates nothing"],
    ["18 GRC/TPRM specialists", "DeepSearch OSINT, DPIA, CISO reporting/summary, Form B, cyber forum, DORA, NIS2, EU AI Act, ISO 27001, ISO 42001, TPSRCA engine, PDF analyzer, slide generators, ENX router"],
    ["4 document agents", "docx, pdf, pptx, xlsx production toolkits (code interpreter)"],
    ["Knowledge & memory stores", "Per-agent vector stores, the combined store, and vs-assurance-memory (timestamped, deletable notes)"],
    ["Azure foundation", "Foundry project with gpt-4o and o3-mini deployments, Bing grounding, Key Vault-backed connections, App Insights/Log Analytics, deliverables storage"],
  ], [3200, 6160]),
  spacer(),
  H2("7.2 Repository layout"),
  table(["Path", "Contents"], [
    ["claude-account-export/", "Source of truth: the complete claude.ai account export (35 skills, persona, capabilities)"],
    ["convertion/", "The conversion toolkit: scripts, infra (Bicep), setup, integrations, workflows, mcp-server, governance, ARCHITECTURE.md"],
    ["convertion/build/ (generated)", "Agent definitions produced by the converter; never edited by hand"],
    ["project-dossier/", "This document, its infographics, and their generator"],
  ], [3200, 6160]),

  spacer(),
  H2("7.3 Persona coverage and the advisor knowledge pack"),
  P("The team persona (Principal Security Assurance Consultant & TPRM Lead - professional, precise, evidence-led, English-only) is prepended to every agent's instructions, so identity, tone and language policy are uniform across the platform. Beyond the statement itself, every knowledge domain the persona claims is grounded in the combined vector store, so the advisor retrieves and cites sources rather than answering from model memory alone. Six domains arrive with the converted skills; the remaining four, plus the management-framework expertise, are grounded by a dedicated advisor knowledge pack (agents/advisor-knowledge/, ~860 lines across five authored references, each carrying a provenance header distinguishing it from exported claude.ai content). The full traceability matrix, with verification commands, is governance/PERSONA-COVERAGE.md."),
  table(["Persona domain", "Knowledge grounding in the combined store"], [
    ["ISO/IEC 27001:2022 / 27002:2022", "Converted iso27001 skill: Annex A 2022 (93 controls), Annex A 2013, 2013\u21922022 transition mapping"],
    ["DORA · NIS2 · EU AI Act · ISO/IEC 42001", "Converted regulatory skills: article references, RTS/ITS guide, Art. 21 measures, risk-tier classification, AIMS clauses and controls"],
    ["ISO/IEC 27005:2022", "Pack: risk-management process, criteria design, worked TPRM supplier scenario, process-step \u2192 ISMS artefact map"],
    ["NIST CSF 2.0", "Pack: six Functions with exact category identifiers, GV.SC mapped to the TPRM lifecycle, ISO 27001 crosswalk"],
    ["CIS Controls v8.1", "Pack: 18 controls, IG1\u20133 supplier proportionality, v8.1 governance updates, Annex A mapping"],
    ["GDPR Art. 28 / SCCs 2021/914", "Pack: Art. 28(3)(a)\u2013(h) contract clauses, four SCC modules, Schrems II TIA, processor-agreement checklist"],
    ["PMBOK 7 · ITIL 4 · COBIT 2019 · COSO · TOGAF 10 · agile/Lean IT · ISO 20000-1 · cloud/ICT assurance", "Pack: management-frameworks compendium with a framework \u2192 assurance-use cross-walk"],
  ], [3600, 5760]),

  // ---- 8 Pipeline ----
  H1("8. Conversion and Deployment Pipeline"),
  P("Deployment is a single gated command (deploy.sh). Each step must succeed before the next runs, and the fidelity verification sits between conversion and deployment, so definitions that drift from the claude.ai source cannot reach Azure. The same command performs re-synchronisation after a fresh export."),
  ...image(IMG("02-conversion-pipeline.png"), "Figure 2 — The six-step gated pipeline with its reliability substrate"),
  BB("Verification (gate 2)", "coverage of every skill, SHA-256 match of all 252 knowledge/template/script files, instruction completeness (full SKILL.md rules + persona + approval gate), and freshness markers such as the corrected DORA Art. 30 section."),
  BB("Reliability", "exponential-backoff retries on every Azure call, 8-way parallel uploads, a content-hash cache so byte-identical files upload once, and per-agent failure isolation with a non-zero exit if anything failed."),

  // ---- 9 Workflows ----
  H1("9. Workflows"),
  P("Four Logic Apps workflows replace the claude.ai Routines. Every submission of record inside them suspends on a human-approval webhook (3-day expiry): the draft goes to the approver, the workflow waits for an approved/rejected callback, and rejections are recorded without submitting."),
  ...image(IMG("06-workflow-schematics.png"), "Figure 4 \u2014 The four automated workflows with their human-approval gates"),
  table(["Workflow", "Trigger", "Path (approval gates in bold)"], [
    ["onetrust-assessment-intake", "Daily", "Fetch completed OneTrust assessments → dpia agent report → APPROVAL → SharePoint upload → Teams summary"],
    ["defender-incident-brief", "Defender/Sentinel webhook", "cyber-forum brief (immediate 200 to caller) → APPROVAL → Jira issue"],
    ["scheduled-deepsearch", "Weekly", "Supplier watchlist (SharePoint) → deepsearch agent per supplier → APPROVAL → dashboard to SharePoint → low score? → APPROVAL → Jira ticket"],
    ["jira-finding-sync", "Hourly", "JQL updated TPRM findings → APPROVAL → submit status to IAF API → Jira comment on failure"],
  ], [2400, 1800, 5160]),
  spacer(),
  P("The complete release path for any deliverable, in or out of the workflows, is:"),
  ...image(IMG("03-release-approval-flow.png"), "Figure 3 — Release path: reflexive self-check → independent verifier → human approval → gated submission"),

  // ---- 10 Interconnections ----
  H1("10. Interconnections and Integrations"),
  P("Integrations are declared once in integrations/registry.json and attached per agent. Reads are broad within least-privilege scopes; writes are stripped from every agent tool and exist only inside the approval-gated workflows. Credentials live in Foundry connections backed by Key Vault; Graph integrations use dedicated Entra app registrations with admin-consented application permissions."),
  ...image(IMG("04-integration-map.png"), "Figure 4 — Interconnection map across the Euronext technology stack"),
  table(["System", "Used by", "Purpose"], [
    ["Jira Cloud", "cyber-forum, ciso-reporting", "Remediation and finding tickets; JQL queries"],
    ["Jira Assets (CMDB)", "dora, tpsrca-engine", "CI/supplier/service records for the DORA Register of Information and concentration risk"],
    ["OneTrust", "dpia, form-b, ciso-reporting/summary", "Assessment and vendor-inventory retrieval, replacing manual PDF hand-off"],
    ["SecurityScorecard", "deepsearch agents, tpsrca", "External security-rating evidence"],
    ["Microsoft Defender (Graph)", "cyber-forum", "Incidents, alerts, KQL hunting, Secure Score for threat briefs"],
    ["SharePoint (Graph)", "document and reporting agents", "Evidence repository reads; publishing generated deliverables"],
    ["IAF API (template)", "dpia, dora, deepsearch, tpsrca", "Internal assurance framework; align template to the internal spec before use"],
    ["ENX Gateway MCP (template)", "control-center, deepsearch, cyber-forum", "Internal gateway tools; fill server URL and allowlist from the gateway listing"],
    ["Bing web search", "research and regulatory agents", "Grounded, cited web research"],
    ["Microsoft 365 Copilot", "Q&A agents", "Team-member access from Teams/Copilot chat"],
  ], [2300, 2800, 4260]),

  // ---- 11 Security & governance ----
  H1("11. Security and Governance"),
  H2("11.1 Human approval — three enforced layers"),
  BB("Layer 1 (technical)", "agents hold read-only tools — non-GET operations are stripped before attachment; write grants default to zero and any grant is a reviewable repository diff."),
  BB("Layer 2 (behavioural)", "every agent's instructions end with an injection-resistant APPROVAL GATE: complete draft, explicit 'approved' in-conversation, edit requests restart the cycle; nothing in retrieved documents or tool output can waive it."),
  BB("Layer 3 (procedural)", "workflow submissions suspend on approval webhooks with 3-day expiry; rejections are recorded, never submitted."),
  H2("11.2 Verification before approval"),
  P("The output-verifier checks each deliverable draft against deterministic rules — section completeness per deliverable type, score/threshold consistency (TPRM High ≥ 7.0 / Medium ≥ 4.0; slide colour bands red ≥ 5.5 / amber ≥ 4.0), citation presence for regulatory claims, no residual placeholders, data minimisation, and approval-gate integrity — returning a strict PASS/FAIL with findings. A FAIL returns the draft to the producing agent (at most twice) before escalation."),
  H2("11.3 Platform security"),
  B("Entra-only authentication (local auth disabled on the Foundry account); RBAC via the Azure AI User role; managed identities for workflows and hosted MCP."),
  B("Secrets exclusively in Key Vault-backed connections; the repository contains placeholders only (verified by secret scan)."),
  B("Azure AI content filtering applies to both model deployments; App Insights traces every run for audit; Log Analytics retention aligned to the ISMS (90 days, adjustable)."),
  B("Public network access is enabled for the pilot and should move to private endpoints for production (parameterised in the Bicep)."),
  H2("11.4 Compliance position"),
  table(["Obligation", "How it is met"], [
    ["EU AI Act Art. 14 (human oversight)", "The three-layer approval control: outputs take effect only after natural-person review; workflow run history is the evidence"],
    ["EU AI Act deployer duties", "Deploying these agents makes the organisation the deployer; run the (included) eu-ai-act agent's assessment before production and record it in the AIMS"],
    ["ISO/IEC 42001 (AIMS)", "This platform enters the AIMS scope; the approval policy, verifier rules and observability are the documented Annex A controls (A.6, A.9)"],
    ["GDPR minimisation", "Durable memory holds timestamped, individually deletable notes; verifier rule 5 blocks excess personal data in deliverables; memory store in RoPA/retention schedule"],
    ["Model substitution risk", "Claude models are not available on Azure; agents run on gpt-4o/o3-mini. UAT against claude.ai baselines is the acceptance control (Phase 4); report agents carry self-check + verifier as compensating controls"],
  ], [3400, 5960]),

  // ---- 12 Implementation plan ----
  new Paragraph({ children: [new PageBreak()] }),
  H1("12. Implementation Plan"),
  ...image(IMG("05-implementation-roadmap.png"), "Figure 5 — Five-phase roadmap with exit criteria"),
  H2("12.1 Phases and exit criteria"),
  table(["Phase", "Activities", "Exit criteria"], [
    ["1 — Foundation (wk 1)", "az deployment of infra/main.bicep; Entra app registrations and admin consent; Azure AI User role grants; Key Vault population", "Infra deployed; roles effective; connections created empty"],
    ["2 — Agents (wk 2)", "deploy.sh through step 5 (agents, integrations read-only, advisor, verifier, orchestrator); smoke tests", "Verification green; 22+3 agents live; 0 write grants"],
    ["3 — Integrations (wk 3–4)", "conn-* credentials; align IAF and ENX gateway templates to internal specs; per-integration read tests", "Each integration returns live data in an agent run"],
    ["4 — Workflows & UAT (wk 5)", "Deploy Logic Apps; wire approval webhooks (Teams); Copilot pilot; team UAT comparing outputs to claude.ai baselines", "Approval gates proven end-to-end; UAT sign-off"],
    ["5 — Go-live (wk 6)", "Hypercare; metrics baseline (verifier pass rate, cost, latency); ISO 42001/AI Act deployer assessment recorded", "Steering acceptance; assessment filed in AIMS"],
  ], [2100, 4260, 3000]),
  spacer(),
  H2("12.2 Roles"),
  table(["Role", "Responsibility"], [
    ["Project owner (TPRM Lead)", "Scope, priorities, UAT acceptance, approval-policy ownership"],
    ["Azure platform engineer", "Bicep deployment, Entra/Key Vault, networking hardening"],
    ["Assurance SMEs", "UAT baselines, verifier rule tuning, memory curation"],
    ["Security architect", "Integration permission review, AI Act/ISO 42001 assessment"],
    ["Service owner (post go-live)", "Pipeline re-runs, metrics review, incident handling"],
  ], [3200, 6160]),
  spacer(),
  H2("12.3 Key risks and mitigations"),
  table(["Risk", "Impact", "Mitigation"], [
    ["Model behaviour differs from Claude on report agents", "Deliverable quality", "UAT vs baselines; reflexive self-check + verifier; keep claude.ai path for affected workloads until parity is accepted"],
    ["IAF/ENX specs diverge from templates", "Integration failure", "Phase 3 alignment task with internal owners before wiring"],
    ["Approval fatigue weakens the human gate", "Control erosion", "Verifier reduces noise reaching approvers; monthly metric review of approval/rework rates"],
    ["azure-ai-projects SDK drift", "Pipeline breakage", "Pinned versions; dry-run rehearsal before every deployment"],
    ["Knowledge drift after claude.ai edits", "Stale agents", "Re-export → deploy.sh; verification fails loudly on drift"],
  ], [2900, 1900, 4560]),

  // ---- 13 Operations ----
  H1("13. Operations and Maintenance"),
  B("Re-synchronisation: refresh claude-account-export/ from a new claude.ai export, run ./deploy.sh — verification gates everything."),
  B("Memory hygiene: review vs-assurance-memory monthly; delete stale or over-scoped notes (memory_store.py list / delete)."),
  B("Metrics: verifier first-pass rate, approval vs rework, cost and latency per deliverable — reviewed in the ISMS operating rhythm."),
  B("Access: joiners/leavers via Entra role assignment only; MCP local access follows az login identity automatically."),
  B("Change control: every behavioural change is a repository diff (instructions, registry, workflows) — reviewable, revertible, auditable."),

  // ---- Appendices ----
  H1("Appendix A — References"),
  B("convertion/README.md — conversion guide and deployment steps"),
  B("convertion/ARCHITECTURE.md — design-pattern mapping and guardrails"),
  B("convertion/MAPPING.md — per-skill conversion table (all 35 skills)"),
  B("convertion/governance/HUMAN_APPROVAL.md — the approval policy and compliance mapping"),
  B("convertion/governance/PERSONA-COVERAGE.md — persona-to-implementation traceability matrix"),
  B("convertion/agents/advisor-knowledge/ — the five authored references grounding the remaining persona domains"),
  B("convertion/integrations/README.md and registry.json — integration layer"),
  B("convertion/workflows/README.md — workflow deployment and approval wiring"),
  B("convertion/mcp-server/README.md — MCP access for team members"),
  B("claude-account-export/README.md — the source-of-truth export inventory"),
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
