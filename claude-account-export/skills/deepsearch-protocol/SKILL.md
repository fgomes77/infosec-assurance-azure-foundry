---
name: deepsearch-protocol
description: >
  Executes the Supplier Security DeepSearch Protocol V17.02.11 — a full OSINT-based third-party
  security assessment that produces a professional HTML dashboard. ALWAYS use this skill when
  the user says "Assess Security of [supplier/domain]", "Run DeepSearch on", "DeepSearch
  assessment", or provides a supplier URL and asks for a security assessment, vendor risk report,
  TPRM deep dive, or supplier security analysis. The skill orchestrates 11 structured sections
  (Executive Summary, Service ID, Corporate Metadata, Security Posture, Technical Infrastructure,
  Vulnerability & Threat Landscape, Incidents & Exposure, AI Governance, Integrations, Controls
  Validation, Confidence Scoring) and renders a single-file interactive HTML dashboard — dark teal
  theme (RGB 0,141,127), Verdana font, 9 expandable section buttons, spider graph, and
  downloadable output. Trigger even for partial requests like "check the security of X",
  "do a vendor check on X", or "what is the security posture of X".
---

# Supplier Security DeepSearch Protocol — V17.02.11

Full-stack OSINT supplier security assessment engine producing a self-contained interactive HTML
dashboard for executive and technical stakeholders.

**Protocol Date:** 16 December 2025 (latest revision)
**Report Title Standard:** "INFOSEC AI THIRD-PARTY SECURITY & COMPLIANCE OSINT DEEPSEARCH REPORT"
**Brand:** "InfoSec AI TPSRCA OSINT"

---

## Trigger Phrases

Primary: **"Assess Security of [supplier name or URL]"**

Also triggers on:
- "Run DeepSearch on [X]"
- "DeepSearch assessment for [X]"
- "Vendor security assessment for [X]"
- "What is the security posture of [X]"
- "Do a TPRM deep dive on [X]"
- "Check security of [X]"
- "Supplier security analysis for [X]"

---

## Scope, Authorization, and Constraints (mandatory)

- Analyze **only** the domain(s) explicitly provided (and clearly-owned subdomains).
- **Active scanning** authorized only if user explicitly sets `ActiveScanningAllowed=Yes`.
  Otherwise **passive methods only** (DNS/WHOIS/CT logs/public scanners/public docs).
- Do **not** provide exploitation steps, payloads, credential attacks, social engineering,
  or bypass instructions.
- Record **analysis date (UTC)** and any **scope exclusions** (third-party CDNs, shared SaaS).

---

## Inputs (collect before starting)

| Input | Required | Default |
|-------|----------|---------|
| `supplier_url` / Domain | Yes | — |
| `company_legal_name` | Recommended | Infer from domain |
| `parent_company` | Optional | Infer if possible |
| `service_type` | Recommended | Infer from website |
| `core_offering` | Recommended | Infer from website |
| `ai_in_product` | Optional | Infer from website |
| `ActiveScanningAllowed` | Optional | `No` (passive-only default) |

**If the user provides only a name/URL, proceed immediately** — do not block on missing inputs.
Infer what you can from public sources during OSINT collection.

### AI Capabilities (assess during OSINT)
- AI in product/service: Yes / No / Unclear
- AI functionality summary
- AI model source: Supplier-built / Third-party model / Both / Unclear
- EU AI Act posture: Claimed compliant / No claim / Unclear (cite evidence if "Claimed")

---

## Execution Workflow

### PHASE 1 — Input Parsing

Parse all provided inputs. If `supplier_url` is a company name rather than a URL, resolve the
canonical homepage via web search before proceeding.

Determine:
- `service_type`: [AI / SaaS / PaaS / IaaS / On-prem / Hybrid / External Provider / Professional Services]
- `ai_enabled`: Yes / No / Unclear — drives Section 8 inclusion
- `has_integrations`: Yes / No / Unclear — drives Section 9 inclusion

---

### PHASE 2 — OSINT Intelligence Collection

Execute web searches across all 11 report sections. Use **minimum 5–8 web searches** to cover
all dimensions adequately.

**Do not guess. If evidence is missing → mark "Not publicly found".**

#### 2A — Corporate & Service Intelligence
- Homepage, About, Careers, Press/News pages
- LinkedIn, Crunchbase, Companies House / local corporate registry
- Trust Center, Security page, Status page
- Parent company + trust center
- **Corporate registries by country:** Polish KRS (rejestr.io, bizraport.pl); Italian SIREN/SIRET;
  Norwegian Finanstilsynet; French CNIL/Legifrance; UK Companies House; US SEC/EDGAR

#### 2B — Compliance & Certifications
- ISO 27001 certificate (**verify via IAF CertSearch**, BSI, Bureau Veritas, SGS, DNV, TÜV registries)
- SOC 2 Type II report access or summary
- ISO/IEC 42001 (AI), ISO 22301, ISO 27018, ISO 27701 evidence
- GDPR: DPA template, subprocessor list, privacy notice
- ISAE 3402 / SSAE 18
- **PCI DSS**: verify against PCI SSC public registry; self-declarations are unreliable without AOC/SAQ
- **ISO scope matters**: verify certifications apply to the specific entity and product in scope,
  not just the parent group

#### 2C — Technical Posture
- Security headers: `https://securityheaders.com/?q=[domain]&followRedirects=on`
- TLS posture: `https://www.ssllabs.com/ssltest/analyze.html?d=[domain]`
- DNS/WHOIS/ASN via passive sources (Shodan summary, censys.io public view)
- Passive HTTP header inspection: `curl -sIL https://[domain]`
- TLS certificate check: `openssl s_client -connect [domain]:443 -servername [domain]`
  (fallback to web search if DNS blocked from container)
- Authentication: SAML/OIDC/OAuth2/SCIM/LDAP/Kerberos/RADIUS/TACACS+ claims in public docs
- CDN/WAF indicators from public sources

#### 2D — Vulnerability & Threat Intelligence
- NVD: `https://nvd.nist.gov/vuln/search/results?query=[vendor]`
- MITRE CVE: `https://cve.mitre.org/cgi-bin/cvekey.cgi?keyword=[vendor]`
- OSV: `https://osv.dev/`
- Exploit-DB, CERT/CC Vulnerability Notes Database, CVE Details, vendor advisories
- AI-specific threats: prompt injection, data leakage, model inversion, poisoning, jailbreaks

#### 2E — Incident History (12–36 month lookback)
- HIBP / breach databases (public aggregators)
- News search: "[supplier] breach", "[supplier] security incident", "[supplier] data leak"
- Regulatory filings / enforcement actions (ICO, CNIL, DPC, HDPA, CNPD, AEPD, etc.)

#### 2F — AI Governance (if ai_enabled = Yes or Unclear)
- Model cards, AI policy, responsible AI page
- EU AI Act public posture statements
- ISO/IEC 42001:2023, ISO/IEC 23894 evidence
- Training data handling, opt-out policies, output retention
- **AI governance gap is systemic**: Nearly every supplier lacks ISO/IEC 42001 or EU AI Act
  conformity documentation — this is a standard finding to probe and document

#### 2G — Integrations
- Marketplace listings (Salesforce AppExchange, Atlassian Marketplace, Zapier, etc.)
- API documentation (public), developer portal
- Named integration partners (minimum 5 if available)

---

### PHASE 3 — Risk Scoring

Apply the following calibrated matrix to each risk category:

**Likelihood × Impact (1–5 each)**

| Score | Range | Label |
|-------|-------|-------|
| 🟢 | 1–4 | Low |
| 🟠 | 5–12 | Medium |
| 🔴 | 13–25 | High |

**Confidence bands:**
- 🟢 ≥ 90% — verified via primary sources (Trust Center, cert registries, regulators)
- 🟠 75–89% — corroborated via secondary sources
- 🔴 < 75% — limited/conflicting evidence

**Spider graph axes (score 1–5 each, where 1=low risk, 5=high risk):**
1. Security Posture (Supplier + Parent)
2. Technical Infrastructure
3. Vulnerability & Threat Landscape
4. Incidents & Exposure
5. AI Governance & Security
6. Integrations Security

**DORA supplier tiers:** DORA Critical / DORA Not Critical / Non-DORA Scope

---

### PHASE 4 — HTML Dashboard Generation

Generate a **single self-contained `.html` file** with all findings embedded.

#### Design Specifications

| Attribute | Value |
|-----------|-------|
| Body background | `#0a1a1f` (dark) |
| Header gradient | `#003530 → #005048` |
| Primary accent / section bg | `#008D7F` (RGB 0,141,127) |
| Secondary accent | `#5ce0d2` |
| Highlight accent | `#00B5A3` |
| Text | White, Verdana font family |
| Minimum font size | 11px |
| Target resolution | 1920 × 1200 |
| Chart library | Chart.js 4.x via CDN (cdnjs.cloudflare.com) |

#### Layout Structure

```
┌─────────────────────────────────────────────────────────────┐
│  TOP HEADER                                                   │
│  Report Title | Supplier Name | Service Type                  │
│  Domain | Assessment Date UTC | Overall Risk Level             │
├────────────────────────────────┬────────────────────────────┤
│  LEFT COLUMN                   │  RIGHT COLUMN (420px)       │
│  Overall Risk Assessment        │  Spider Graph               │
│  (KPI cards: Risk Level /       │  (6-axis, Chart.js radar)   │
│   Result / DORA / Confidence)   │                             │
├────────────────────────────────┴────────────────────────────┤
│  9 PILL BUTTONS (sticky, centered):                           │
│  Risk │ Corporate │ Security Posture │ Technical │ Incidents  │
│  AI Governance │ Integrations │ Controls │ Confidence         │
├─────────────────────────────────────────────────────────────┤
│  EXPANDABLE SECTION PANEL (accordion)                         │
│  Each section: 5-column table                                 │
│  Item │ Finding │ Evidence (link) │ Confidence │ Notes/Mitig  │
├─────────────────────────────────────────────────────────────┤
│  FOOTER: Download HTML button | Report timestamp | Brand      │
└─────────────────────────────────────────────────────────────┘
```

#### Section Button → Report Section Mapping

| Button | Report Section |
|--------|---------------|
| Risk | §1 Executive Summary + Top 5 risks + Top 5 mitigations + §6 Vulns sub-table |
| Corporate | §2 Service ID + §3 Corporate Metadata |
| Security Posture | §4 Security Posture (certs, compliance, program indicators) |
| Technical | §5 Technical Infrastructure |
| Incidents | §7 Incidents & Exposure (12–36 months) |
| AI Governance | §8 AI Governance & Security |
| Integrations | §9 Integrations with other applications |
| Controls | §10 Controls Validation |
| Confidence | §11 Confidence Scoring (per section) |

**Vulnerability section (§6)** embedded inside the **Risk** button expansion as a sub-table
after Top 5 risks, clearly labelled "Known CVEs & Threat Vectors".

#### Interactive Behaviour
- Clicking a button **expands** its section panel and scrolls to it
- Clicking same button again **or** `×` close button **collapses** it
- **Only one section open at a time** (accordion pattern)
- Spider graph renders on page load using Chart.js radar chart
- KPI cards use frosted-glass style with accent background per risk type

#### Download Button
Include **"⬇ Download Report"** button in footer that triggers Blob save of the full HTML
as: `TPSRCA_[SupplierName]_v17_02_11.html`

---

### PHASE 4B — HTML Generation Best Practices (Critical)

These patterns prevent common generation failures:

1. **Python heredoc method (recommended):** Write full HTML as a Python plain string variable
   in a `.py` script file, then execute. Use `cat > script.py << 'PYEOF'` to avoid shell escaping.
   **Never use f-strings for HTML containing JavaScript braces** — use plain Python strings
   or `data-*` attributes for template variables.

2. **UTF-8 encoding (always apply):**
   - Add `# -*- coding: utf-8 -*-` header to all Python scripts
   - Use `encoding='utf-8'` in all Python `open()` calls
   - Use HTML entity codes for emojis in templates, not literal Unicode characters
   - Spider graph score variables go in HTML `data-*` attributes, not inline JS

3. **Standard emoji set (HTML entities):**
   - 🟢 (`&#x1F7E2;`) = Low risk / Yes
   - 🟡 (`&#x1F7E1;`) = Low-Medium
   - 🟠 (`&#x1F7E0;`) = Medium risk
   - 🔴 (`&#x1F534;`) = High risk / Critical
   - ✅ (`&#x2705;`) = Yes/Present
   - ❌ (`&#x274C;`) = No/Absent
   - 🔗 (`&#x1F517;`) = Link
   - — (`&mdash;`) = Em dash
   - 🛡️ (`&#x1F6E1;&#xFE0F;`) = Shield
   - 📊🏢🌐🔒⚙️🚨🤖 (use corresponding HTML entities)

4. **File output path:**
   - Work in `/home/claude/`
   - Copy final to `/mnt/user-data/outputs/`
   - Use `present_files` to deliver

---

### PHASE 5 — Quality Gate

Before presenting the HTML, run inline Python validation:

```python
checks = []
sections = ['risk','corporate','security','technical','incidents','ai','integrations','controls','confidence']
for s in sections:
    checks.append(f"Section '{s}': {'PASS' if f'id=\"{s}\"' in html else 'FAIL'}")
checks.append(f"Chart.js CDN: {'PASS' if 'chart.umd.min.js' in html else 'FAIL'}")
checks.append(f"Spider canvas: {'PASS' if 'spiderChart' in html else 'FAIL'}")
checks.append(f"Download button: {'PASS' if 'downloadReport' in html else 'FAIL'}")
# Verify JS brace balance
# Verify UTF-8 encoding
# Verify HTML ends with </html>
# Count report tables (expect 10+)
```

Checklist:
- [ ] All 9 section panels present with correct IDs
- [ ] All 11 report sections populated (or "Not publicly found" for missing evidence)
- [ ] Every table row has at least one source reference
- [ ] Risk scores follow L×I matrix (no arbitrary scores)
- [ ] Spider graph axes scored 1–5 with justification
- [ ] Confidence per section assigned with rationale
- [ ] AI section present if ai_enabled = Yes/Unclear
- [ ] Integrations section present if has_integrations = Yes/Unclear
- [ ] HTML is self-contained (no external dependencies except CDN Chart.js)
- [ ] Download button functional
- [ ] JS braces balanced (opens == closes)
- [ ] UTF-8 encoding valid
- [ ] File ends with `</html>`
- [ ] File size > 20KB (indicates substantial content)

---

## Section Content Requirements (inline reference)

### §1 Executive Summary (Risk)
- Overall risk level: 🔴 High / 🟠 Medium / 🟢 Low / ⚪ Not Found
- Top 5 risks impacting customers (attack surface + AI risks if present)
- Top 5 mitigations (split: Supplier actions vs Customer controls)
- State whether findings are mostly public-doc-based or scan-output-based
- Spider graph scores with justification

### §2 Service Identification
- Core product/service, key features (3–5), target industries
- Support contact, incident contact, security contact (or "Not publicly found")
- Security/Trust Center URL
- ICT supplier type

### §3 Corporate Metadata
- HQ city/country, physical address (if verifiable)
- Ownership/founding/acquisitions timeline (credible sources only)
- Parent company + Trust Center links (supplier + parent)

### §4 Security Posture (Supplier + Parent)
Treat "compliance" as **evidence-based claims**, not assumptions.
- ISO 27001 (certificate evidence), ISO 22301, ISO/IEC 42001 (AI), SOC 2 Type II, ISAE 3402
- Privacy posture: GDPR alignment claims (DPA/privacy notice), data residency statements
- Security program indicators: bug bounty, responsible disclosure, security whitepapers,
  pen test summaries (public)

### §5 Technical Infrastructure
- **Hosting**: cloud provider, datacenter locations
- **Encryption**: TLS version, cipher details, at-rest encryption standard (AES-256)
- **WAF/CDN**: vendor details, version info if available
- **Open ports/Services**: unwanted ports via passive scanning
- **Technical documentation**: available on website? (include link)
- **Access management protocols**: SAML, OAuth2, OpenID Connect, Kerberos, LDAP, RADIUS,
  TACACS+. Include supplier website link to auth method documentation, especially SAML config.

### §6 Vulnerability & Threat Landscape
- Public known vulnerabilities from MITRE CVE, NVD, Exploit-DB, CVE Details, CERT/CC, OSV
  — date of first finding, affected systems
- Critical CVEs: top 3 with patching status
- Dark web exposure: leaked credentials or exposures
- Possible threat vectors: injection, DoS/DDoS, XSS, etc.

### §7 Incidents & Exposure (12–36 months)
- Known data breaches or security incidents (past 12–36 months)
- Leaked credentials on dark web
- Notable misconfigurations via passive scanning (Shodan, DNS, security headers)

### §8 AI Governance & Security (if AI present or Unclear)
- **AI Role**: Model Provider / Model Integrator / AI-enabled SaaS / Internal-only AI / Unclear
- Model(s) used (names/versions) or "Not publicly found"
- Model provider (legal entity)
- Deployment: API vs embedded vs on-prem; hosting region claims
- Data handling: prompts/outputs stored? retention? training usage? opt-out? (cite policy)
- Security controls: prompt injection mitigation, tenant isolation, logging, abuse monitoring,
  rate limiting, human oversight (public claims only)
- EU AI Act posture: "Claimed" only with published statement; otherwise "No public claim/Unclear"
- AI certifications: ISO/IEC 42001, ISO/IEC 23894, third-party model assessments

### §9 Integrations (if present or Unclear)
- Integration classification: API / Interface / Other / Unclear
- Top 5 API integrations/interfaces listed or "Not publicly found"
- API/Interface security mechanisms or "Not publicly found"

### §10 Required Control Validation (Public Evidence Only)
Answer each as: **Yes (evidence) / No (evidence) / Not publicly found**
Group under:
- Information Security
- Data Protection
- Identity & Access
- Privacy
- Regulatory / Locations
- Subprocessors

### §11 Confidence Scoring (per section)
Compact row list — each section with 🟢/🟠/🔴 and one-line rationale.

---

## TPRM Dashboard Integration (post-assessment)

After generating the TPSRCA HTML report:

1. **Update portfolio**: If `/home/claude/tprm-dashboard/tprm_portfolio.json` exists,
   update the supplier entry: set TPA Status to "Ongoing" (DeepSearch generated).
2. **Rebuild dashboard**: Run `python3 rebuild_tprm_dashboard.py --deepsearch SUP-XXX`
   to update the TPRM Dashboard.
3. **Google Drive convention**: Upload to `TPA Ai/{SupplierName}/TPSRCA_*.html`

TPA Status Logic:
- Generating a DeepSearch HTML → TPA Status = "Ongoing"
- Generating a CISO PPTX → TPA Status = "Complete"

---

## Output

1. Deliver the complete HTML file via `present_files` tool
2. State the **overall risk level** and **top 3 findings** inline in chat
3. Note any sections where evidence was limited (🔴 confidence)

---

## Important Rules

- **Never fabricate findings.** Absent evidence → "Not publicly found"
- **Prefer primary sources**: Trust Center > cert registries > vendor docs > news
- **Conflicting sources**: note conflict, downgrade confidence to 🔴
- **No exploitation steps, payloads, or credential attacks** regardless of ActiveScanningAllowed
- **Passive-only by default** unless user explicitly sets `ActiveScanningAllowed=Yes`
- **EU regulatory applicability**: always state DORA / NIS2 / EU AI Act relevance by service type
- **GDPR**: note DPA/SCC evidence if any personal data processing is indicated
- **ISO certification scope**: verify certs apply to the specific entity and product in scope,
  not just the parent group
- **PCI DSS self-declarations**: always verify against PCI SSC public registry
- **Document comparison discipline**: when reconciling document versions, identify structural
  gaps rather than accepting either version as authoritative

---

## Regulatory Frameworks in Scope

- DORA Art. 28/30
- GDPR Art. 28/33
- NIS2 Art. 21
- EU AI Act
- ISO/IEC 27001:2022
- ISO/IEC 42001:2023
- ISO 22301
- ISO 27701
- NIST CSF 2.0
- CIS v8.1
- PCI DSS
- SOC 2 Type II
