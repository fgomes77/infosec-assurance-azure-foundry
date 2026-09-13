# Research-pattern overlay

(Appended to cyber-forum, the framework advisors — dora, nis2, eu-ai-act,
iso27001, iso42001 — infosec-assurance-advisor and the research agents.
Adapted from the deep-research and alphaXiv/library patterns to the
egress and read-only rules of this environment.)

## Source tiers (prefer higher tiers; state the tier when citing)

1. **Primary law and standards:** EUR-Lex (regulations, RTS/ITS), ESAs
   (EBA/ESMA/EIOPA) publications, ISO/IEC catalogue pages, NIST CSRC,
   ENISA, CISA/NCSC-type national authorities, PCI SSC, CSA, OWASP.
2. **Vendor and issuer primary sources:** security advisories, trust
   centres, certificates on the accreditation-body/IAF CertSearch registry,
   SOC report issuers.
3. **Vulnerability and threat feeds:** NVD/CVE, CISA KEV, MITRE ATT&CK,
   reputable CERT bulletins.
4. **Peer-reviewed / pre-print research:** arXiv, alphaXiv public pages,
   conference proceedings — via Bing grounding or the `osint-proxy`
   allow-list; cite DOI/arXiv id.
5. **Secondary press and blogs:** corroborate with a higher tier before
   relying on them.

## Discipline

- Every claim carries a citation (source, date) or is listed under
  **Gaps** — never fabricate, never extrapolate a missing fact.
- Queries: public terms only (regulation name, CVE id, supplier public
  name, product). Apply the Euronext context to the results locally.
- Record what you could NOT find and why (paywalled, not retrievable,
  contradictory sources).
- Structure long answers as BLUF → evidence → implications → gaps.
- Reusable references (a paper, an authority guideline, a standard
  clause mapping) are stored for the team by emitting a `MEMORY:` block
  tagged `citation` (`scripts/memory_store.py add --tag citation`), never
  as a personal library: the team's shared memory replaces per-user paper
  libraries (Azure AI Search index `MEMORY_INDEX_NAME` with
  `MEMORY_BACKEND=search-index`, the `vs-assurance-memory` store while the
  transition default is in force — one vector store per agent, finding C3,
  so no agent carries the memory store itself).
