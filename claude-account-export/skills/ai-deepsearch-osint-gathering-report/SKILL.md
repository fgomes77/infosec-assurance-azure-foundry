---
name: ai-deepsearch-osint-gathering-report
description: >
  Executes the AI DeepSearch OSINT Gathering Report — a full OSINT-based third-party security
  assessment that produces a professional HTML dashboard. ALWAYS use this skill when the user says
  "Assess Security of [supplier/domain]", "Run DeepSearch on", "DeepSearch assessment", or provides
  a supplier URL and asks for a security assessment, vendor risk report, TPRM deep dive, or
  supplier security analysis. The skill orchestrates 11 structured sections (Executive Summary,
  Service ID, Corporate Metadata, Security Posture, Technical Infrastructure, Vulnerability &
  Threat Landscape, Incidents & Exposure, AI Governance, Integrations, Controls Validation,
  Confidence Scoring) and renders a single-file interactive HTML dashboard — dark teal theme
  (RGB 0,141,127), Verdana font, 9 expandable section buttons, spider graph, and downloadable output.
  Trigger even for partial requests like "check the security of X", "do a vendor check on X", or
  "what is the security posture of X".
---

# AI DeepSearch OSINT Gathering Report

# Supplier Security DeepSearch Protocol — V17.02.11

OSINT intelligence collection and passive reconnaissance methodology for the TPSRCA assessment
engine. This skill defines the search strategies, source prioritization, and evidence gathering
patterns that feed into the DeepSearch Protocol HTML dashboard.

**Companion skill:** `deepsearch-protocol/SKILL.md` — covers the full protocol, scoring,
HTML generation, quality gates, and dashboard integration.

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

---

## OSINT Collection Strategy

### Search Stream Architecture

Execute a **minimum of 5–8 distinct web searches** organized by intelligence stream.
Each stream targets a specific report dimension. Run them in sequence, building context
as findings emerge.

#### Stream 1 — Corporate & Service Identity (2 searches minimum)
**Goal:** Establish legal entity, HQ, ownership, service description, contacts.

Search patterns:
- `[domain] company [country]` — primary identity
- `"[company name]" about founded CEO headquarters` — corporate metadata
- `[domain] LinkedIn` — employee count, competencies, recent activity

Sources to extract from:
- Official website: homepage, about, careers, press/news
- LinkedIn company page
- ZoomInfo, Crunchbase, Companies House / local registries
- Trust Center, Security page, Status page
- Parent company website + trust center

**Key data points:** Legal name, HQ address, founding date, CEO/leadership, employee count,
revenue estimate, parent company, ownership structure, notable clients, key partnerships.

#### Stream 2 — Compliance & Certifications (1–2 searches)
**Goal:** Evidence-based certification status, not assumptions.

Search patterns:
- `"[company name]" ISO 27001 certification security` — certifications
- `"[company name]" SOC 2 trust center compliance` — assurance reports

Verification sources:
- **IAF CertSearch** (iaf.nu) — ISO certificate verification
- **PCI SSC** — PCI DSS validation (don't trust self-declarations)
- BSI, Bureau Veritas, SGS, DNV, TÜV registries
- Company Trust Center / Security page
- SOC 2 Type II summary or report access page

**Critical rule:** ISO certification scope matters. Verify the certificate applies to the
specific entity and product in scope, not just the parent group.

#### Stream 3 — Privacy & Data Protection (1 search)
**Goal:** GDPR alignment evidence, DPA availability, data residency.

Search patterns:
- `"[domain]" privacy policy GDPR DPA` — privacy posture

Sources:
- Privacy policy page (look for: DPO contact, data subject rights, retention periods,
  lawful basis, subprocessor references)
- DPA template availability
- Subprocessor list (published or upon request)
- Data residency statements
- Cookie consent mechanism

#### Stream 4 — Technical Posture (passive reconnaissance)
**Goal:** Web security headers, TLS, hosting, CMS, exposed endpoints.

**Passive methods (always available):**
```bash
# HTTP headers
curl -sIL https://[domain] 2>&1 | head -60

# TLS certificate details (if DNS resolves from container)
echo | openssl s_client -connect [domain]:443 -servername [domain] 2>/dev/null | \
  openssl x509 -noout -subject -issuer -dates -ext subjectAltName

# Fallback: web search for SSL Labs / SecurityHeaders results
```

**Web-based scanners (always reference):**
- SecurityHeaders.com: `https://securityheaders.com/?q=[domain]&followRedirects=on`
- SSL Labs: `https://www.ssllabs.com/ssltest/analyze.html?d=[domain]`

**Key headers to check:**
- Strict-Transport-Security (HSTS)
- Content-Security-Policy (CSP)
- X-Frame-Options
- X-Content-Type-Options
- Permissions-Policy
- Referrer-Policy
- Server header (information disclosure)

**Key indicators to extract:**
- Web server / proxy (Nginx, Apache, Envoy, Cloudflare, etc.)
- CMS platform (WordPress: wp-json, xmlrpc.php; Drupal; etc.)
- CDN/WAF indicators
- Exposed API endpoints
- Technology stack (from headers, ZoomInfo, BuiltWith)

#### Stream 5 — Vulnerability & Incident Intelligence (1–2 searches)
**Goal:** CVEs, breaches, dark web exposure, threat vectors.

Search patterns:
- `"[company name]" breach incident security vulnerability` — incidents
- `CVE "[company name]" OR "[domain]" vulnerability` — CVEs

Sources:
- NVD: `https://nvd.nist.gov/vuln/search/results?query=[vendor]`
- MITRE CVE: `https://cve.mitre.org/cgi-bin/cvekey.cgi?keyword=[vendor]`
- OSV: `https://osv.dev/`
- Exploit-DB, CERT/CC, vendor advisories
- HIBP (public breach aggregator)
- News search for incidents in past 12–36 months
- Regulatory enforcement actions (ICO, CNIL, DPC, HDPA, etc.)

**Important distinction:** For system integrators and service providers (not software vendors),
no direct CVEs is expected. Document this as a finding, not a gap.

#### Stream 6 — AI Governance (if AI detected, 1 search)
**Goal:** AI role classification, model details, governance documentation.

Search patterns:
- `"[company name]" AI copilot machine learning model governance` — AI posture

Sources:
- Model cards, AI policy, responsible AI page
- EU AI Act posture statements
- ISO/IEC 42001:2023, ISO/IEC 23894 evidence
- Training data handling, opt-out policies, output retention

**Systemic pattern:** AI governance gap (absence of ISO/IEC 42001 and EU AI Act conformity
claims) is a recurring finding across virtually all assessed suppliers.

#### Stream 7 — Integrations (if detected, 1 search)
**Goal:** API security, integration ecosystem, attack surface via third parties.

Search patterns:
- `"[company name]" API integrations marketplace` — integration ecosystem

Sources:
- Marketplace listings (AppExchange, Atlassian Marketplace, Zapier, etc.)
- API documentation portal (public)
- Developer portal / SDK documentation
- Named integration partners (minimum 5 if available)

---

## Evidence Source Hierarchy

Prefer sources in this order (highest to lowest reliability):

1. **Trust Center / Security page** — vendor-published, maintained
2. **Certificate registries** — IAF CertSearch, PCI SSC, CB websites
3. **Regulatory filings** — enforcement actions, DPA registrations
4. **Official vendor documentation** — privacy policy, DPA, terms
5. **LinkedIn / corporate registries** — company profiles, registrations
6. **Reputable tech press** — news reporting on incidents
7. **Third-party intelligence** — ZoomInfo, Crunchbase, BuiltWith
8. **Blog posts / forums** — lowest confidence, use only if nothing else available

**If sources conflict:** Note the conflict explicitly and downgrade confidence to 🔴.

---

## OSINT Search Best Practices

1. **Keep search queries short and specific** — 3–6 words for best results
2. **Start broad, then narrow** — first search establishes identity, subsequent searches drill down
3. **Use domain name in quotes** for precise matching: `"dis.com.gr"`
4. **Company name variations**: search both short name and full legal name
5. **Combine supplier name with key terms**: `ISO 27001`, `breach`, `privacy policy`, `GDPR`,
   `SOC 2`, `trust center`, `AI`, `CVE`
6. **Always search for security contact**: many suppliers have `security@`, `csirt@`, or
   responsible disclosure pages that indicate maturity
7. **Check for Trust Center even if not linked from homepage**: try
   `trust.[domain]`, `security.[domain]`, `[domain]/security`, `[domain]/trust`
8. **Fetch key pages when needed**: use `web_fetch` to read privacy policies, trust center
   pages, or DPA templates in detail

---

## Assessment Execution Pattern (standard workflow)

1. Read protocol + template files from `/mnt/project/` (skill files)
2. Multi-stream OSINT via web search (Streams 1–7 above)
3. Passive HTTP/TLS recon via `curl -sIL` and `openssl s_client`
   (fallback to web search if DNS blocked from container)
4. Generate HTML report via Python heredoc script in `/home/claude/`
5. Run quality gate validation (inline Python)
6. Copy validated HTML to `/mnt/user-data/outputs/`
7. Deliver via `present_files`
8. (If TPRM dashboard exists) Update `tprm_portfolio.json` and rebuild dashboard

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
- **ISO certification scope**: verify certs apply to specific entity and product in scope
- **PCI DSS self-declarations**: always verify against PCI SSC public registry
