"""Outbound URL policy for the sanitised public-page fetch and the passive
recon endpoints (integrations/openapi/osint-proxy.yaml, passive-recon.yaml).

Guarantees (DATA_PROTECTION_GUARDRAILS §1 "no Euronext data to the web"):
  * only public hosts: no private / link-local / loopback IPs, no internal
    domain suffixes ({internal-domain-suffixes}), no bare IP hosts
  * host must be on the curated registry allow-list OR under the supplier
    domain named in the request
  * the URL itself must not carry internal markers (ENX-*, assessment ids,
    e-mail addresses, employee-name list) — outbound DLP regex
  * https only, standard port only
The same module is copied into functions/web-render/ (kept identical).
"""

from __future__ import annotations

import ipaddress
import os
import re
import socket
from urllib.parse import urlsplit

# BEGIN generated allow-list (scripts/sync_url_allowlist.py)
# Generated from integrations/knowledge-sources.json — do not
# edit by hand: add the source there (with its tier, citation
# rule and reason) and re-run the script. Adding a domain here
# widens what the platform can reach: Tier-B change.
DEFAULT_ALLOWLIST = [
    "aicpa-cima.com", "aicpa.org", "api.first.org",
    "api.securityscorecard.io", "attack.mitre.org", "aws.amazon.com",
    "boe.es", "bsi.bund.de", "cert.europa.eu", "cert.pt",
    "cert.ssi.gouv.fr", "cisa.gov", "cisecurity.org", "cloud.google.com",
    "cloudsecurityalliance.org", "cofrac.fr", "companieshouse.gov.uk",
    "crt.sh", "csrc.nist.gov", "cve.org", "cveproject.github.io",
    "d3fend.mitre.org", "dakks.de", "digital-strategy.ec.europa.eu",
    "dre.pt", "e-justice.europa.eu", "eba.europa.eu", "ec.europa.eu",
    "edpb.europa.eu", "edps.europa.eu", "eiopa.europa.eu",
    "enisa.europa.eu", "esma.europa.eu", "eur-lex.europa.eu",
    "european-accreditation.org", "finance.ec.europa.eu", "first.org",
    "gesetze-im-internet.de", "gleif.org", "iaasb.org",
    "iafcertsearch.org", "iec.ch", "ifac.org", "ipac.pt", "iso.org",
    "legifrance.gouv.fr", "legislation.gov.uk", "msrc.microsoft.com",
    "ncsc.gov.uk", "ncsc.nl", "nist.gov", "normattiva.it", "nvd.nist.gov",
    "nvlpubs.nist.gov", "observatory.mozilla.org", "op.europa.eu",
    "owasp.org", "pcisecuritystandards.org", "pentest-standard.org",
    "publications.europa.eu", "rva.nl", "sec.gov", "securityheaders.com",
    "securityscorecard.com", "services.nvd.nist.gov", "ssllabs.com",
    "ukas.com", "wetten.overheid.nl",
]
# END generated allow-list

INTERNAL_SUFFIXES = [s.strip().lower() for s in
                     os.environ.get("INTERNAL_DOMAIN_SUFFIXES",
                                    "{internal-domain-suffix}").split(",")
                     if s.strip()]

# Outbound DLP: internal markers that must never leave the boundary.
INTERNAL_MARKER = re.compile(
    r"(ENX-[A-Z0-9-]+|\bTPA-\d{3,}\b|\bassessment[_-]?id=\d+|"
    r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}|\b\d{6,}-OT\b)", re.I)


def allowlist() -> list[str]:
    extra = [s.strip().lower() for s in
             os.environ.get("ALLOWLIST_EXTRA", "").split(",") if s.strip()]
    return sorted(set(DEFAULT_ALLOWLIST + extra))


def _host_under(host: str, domain: str) -> bool:
    host, domain = host.lower().rstrip("."), domain.lower().lstrip("*.").rstrip(".")
    return host == domain or host.endswith("." + domain)


def _is_public_ip(ip: str) -> bool:
    try:
        a = ipaddress.ip_address(ip)
    except ValueError:
        return False
    return not (a.is_private or a.is_loopback or a.is_link_local or
                a.is_multicast or a.is_reserved or a.is_unspecified)


def check_host(host: str, supplier_domain: str | None = None,
               resolve: bool = True) -> tuple[bool, str]:
    """(ok, reason). Pure host-level checks + DNS resolution to public IPs."""
    if not host:
        return False, "empty host"
    host = host.lower().rstrip(".")
    try:
        ipaddress.ip_address(host)
        return False, "bare IP hosts are refused"
    except ValueError:
        pass
    if "." not in host or host.endswith(".local") or host.endswith(".internal"):
        return False, "non-public host"
    for suf in INTERNAL_SUFFIXES:
        if suf and _host_under(host, suf):
            return False, "internal domain suffix"
    allowed = any(_host_under(host, d) for d in allowlist())
    if not allowed and supplier_domain:
        sd = supplier_domain.lower().strip()
        if INTERNAL_MARKER.search(sd) or any(_host_under(sd, s) for s in INTERNAL_SUFFIXES if s):
            return False, "supplier domain not public"
        allowed = _host_under(host, sd)
    if not allowed:
        return False, "host not on the allow-list (pass supplierDomain)"
    if resolve:
        try:
            infos = socket.getaddrinfo(host, 443, proto=socket.IPPROTO_TCP)
        except socket.gaierror:
            return False, "host does not resolve"
        ips = {i[4][0] for i in infos}
        if not ips or not all(_is_public_ip(ip) for ip in ips):
            return False, "host resolves to a non-public address"
    return True, "ok"


def check_url(url: str, supplier_domain: str | None = None,
              resolve: bool = True) -> tuple[bool, str]:
    if INTERNAL_MARKER.search(url or ""):
        return False, "internal marker in URL"
    try:
        u = urlsplit(url)
    except ValueError:
        return False, "malformed URL"
    if u.scheme != "https":
        return False, "https only"
    if u.port not in (None, 443):
        return False, "non-standard port"
    if u.username or u.password:
        return False, "credentials in URL"
    return check_host(u.hostname or "", supplier_domain, resolve=resolve)
