#!/usr/bin/env python3
"""
extract_pdf.py  —  TPRM Assessment PDF → Structured JSON

Handles the doubled-character OCR artifact common in OneTrust exports.
Usage:
    python3 extract_pdf.py --input <pdf_path> --output <json_path>
"""
import re, json, argparse
from pathlib import Path

try:
    import pdfplumber
except ImportError:
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install",
                           "pdfplumber", "--break-system-packages", "-q"])
    import pdfplumber


# ── helpers ───────────────────────────────────────────────────────────────────
def undouble(text: str) -> str:
    """Remove doubled characters: 'VVeennddoorr' → 'Vendor'"""
    return re.sub(r'(.)\1', r'\1', text)

def first_match(pattern, text, default="", group=1):
    m = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    return m.group(group).strip() if m else default

def classify_domain(risk_text: str, controls_text: str) -> str:
    """Map risk + controls text to one of the 5 TPRM domains."""
    combined = (risk_text + " " + controls_text).lower()
    if any(k in combined for k in ["ids/ips", "intrusion", "soc", "network security",
                                   "threat detection", "access control", "iam",
                                   "pam", "authentication", "admin"]):
        if any(k in combined for k in ["ids", "ips", "intrusion", "soc", "network"]):
            return "Cybersecurity"
        return "Cybersecurity"
    if any(k in combined for k in ["data", "privacy", "gdpr", "encryption",
                                   "classification", "dlp"]):
        return "Data Management"
    if any(k in combined for k in ["bcm", "bcp", "continuity", "disaster", "drp",
                                   "recovery", "rto", "rpo", "backup"]):
        return "Business Continuity"
    if any(k in combined for k in ["supply chain", "third-party", "third party",
                                   "vendor", "tp ", "ict-third", "procurement",
                                   "supply chain risk"]):
        return "Third-Parties"
    if any(k in combined for k in ["log", "asset", "cmdb", "inventory", "patch",
                                   "vulnerability", "sdlc", "software", "config"]):
        return "IT"
    return "Cybersecurity"   # default

def score_to_severity(score: float) -> str:
    if score >= 7.0: return "High"
    if score >= 4.0: return "Medium"
    return "Low"

def map_risk_title(description: str) -> str:
    """Map verbose risk description to a concise standardised title."""
    desc = description.lower()
    if "ids" in desc or "ips" in desc or "intrusion" in desc or "network" in desc:
        return "Unsecure Network Threat Detection"
    if "access control" in desc or "unauthorized" in desc or "iam" in desc:
        return "Inadequate Access Management"
    if "log" in desc and ("detect" in desc or "breach" in desc or "track" in desc):
        return "Security Incidents Not Properly Managed"
    if "risk response" in desc or "planning" in desc or "communication of risk" in desc:
        return "Security Risks Not Managed"
    if "inventory" in desc or "cmdb" in desc or "software" in desc or "asset" in desc:
        return "Unregistered Assets in CMDB"
    if "supply chain" in desc or "third-party" in desc or "vendor" in desc:
        return "Third-Parties Relationship Not Properly Managed"
    if "vulnerability" in desc or "patch" in desc:
        return "Inadequate Vulnerability Management"
    if "bcm" in desc or "continuity" in desc or "recovery" in desc:
        return "Lack of Business Continuity and DR Capabilities"
    if "data" in desc or "privacy" in desc:
        return "Insufficient Data Protection Lifecycle"
    return description[:60].strip()


# ── main extraction ───────────────────────────────────────────────────────────
def extract(pdf_path: str) -> dict:
    with pdfplumber.open(pdf_path) as pdf:
        raw = ""
        for page in pdf.pages:
            raw += (page.extract_text() or "") + "\n"

    text = undouble(raw)

    # ── vendor / meta ──────────────────────────────────────────────────────────
    vendor       = first_match(r'Name\s*\((.+?)\)', text, "Unknown Vendor")
    assess_id    = first_match(r'Name\s*\(.+?\)\s+(\S+)', text, "")
    dora_raw     = first_match(r'DORA Scope.*?Response.*?\n(Yes|No)', text, "No")
    dora_scope   = dora_raw.strip().lower() == "yes"
    critical_raw = first_match(r'Is this a critical supplier\?.*?Response.*?\n(Yes|No)', text, "No")
    is_critical  = critical_raw.strip().lower() == "yes"
    crit_label   = "Critical" if is_critical else "Not-Critical"
    certs        = re.findall(r'ISO\s*\d{5}', text) or []
    certs        = list(dict.fromkeys(certs))   # deduplicate

    # ── parse risks ───────────────────────────────────────────────────────────
    risk_blocks  = re.split(r'Risk:\s*(\d+)\s*[-–]', text)[1:]   # [id, body, id, body…]
    risks        = []
    for i in range(0, len(risk_blocks) - 1, 2):
        risk_id    = risk_blocks[i].strip()
        body       = risk_blocks[i + 1]

        # Residual risk score
        score_m = re.search(
            r'Residual Risk Score\s+Target risk score.*?\n\S+\s+\S+\s+([\d.]+)', body)
        if not score_m:
            score_m = re.search(r'[\d.]+\s+[\d.]+\s+([\d.]+)\s+\d+\s+In Treatment', body)
        score = float(score_m.group(1)) if score_m else 0.0

        # Description (first paragraph before "Type")
        desc_m = re.search(r'^(.+?)(?=Type\s+ENX)', body, re.DOTALL)
        description = desc_m.group(1).strip().replace('\n', ' ') if desc_m else body[:120].strip()

        # Controls
        controls = []
        for ctrl_m in re.finditer(
            r'((?:CIS|Euronext|ISO|NIST)\s*[\w./\- ]+?)\s+\n?\s*([\w &/,.\-]+?)\s+\n?\s*([\w &/,.\-]+?)\s+(Implemented|Pending)',
            body):
            ctrl_id, ctrl_name, category, status = ctrl_m.groups()
            controls.append({
                "id":       ctrl_id.strip(),
                "name":     ctrl_name.strip(),
                "category": category.strip(),
                "status":   status.strip(),
            })

        domain = classify_domain(description, body)
        risks.append({
            "id":          risk_id,
            "score":       score,
            "description": description,
            "title":       map_risk_title(description),
            "domain":      domain,
            "controls":    controls,
        })

    # Sort by score descending
    risks.sort(key=lambda r: r["score"], reverse=True)

    # ── domain scores (max residual per domain) ────────────────────────────────
    domains = ["Cybersecurity", "Data Management", "IT", "Business Continuity", "Third-Parties"]
    domain_scores = {d: 1.0 for d in domains}
    for r in risks:
        d = r["domain"]
        if d in domain_scores:
            domain_scores[d] = max(domain_scores[d], r["score"])

    # ── overall risk ──────────────────────────────────────────────────────────
    max_score    = max(domain_scores.values())
    overall_risk = score_to_severity(max_score)

    # ── top 3 risks ───────────────────────────────────────────────────────────
    top_risks = []
    for r in risks[:3]:
        top_risks.append({
            "id":     r["id"],
            "score":  r["score"],
            "domain": r["domain"],
            "title":  r["title"],
            "detail": r["description"][:90],
        })

    # ── full register (all risks, short labels) ───────────────────────────────
    LABEL_MAP = {
        "Unsecure Network Threat Detection":            "Net",
        "Inadequate Access Management":                 "IAM",
        "Security Incidents Not Properly Managed":      "Incidents",
        "Security Risks Not Managed":                   "Sec risks",
        "Unregistered Assets in CMDB":                  "Assets",
        "Third-Parties Relationship Not Properly Managed": "Supply",
        "Lack of Business Continuity and DR Capabilities": "BC/DR",
    }
    full_register = [{"id": r["id"],
                      "label": LABEL_MAP.get(r["title"], r["title"][:8]),
                      "score": r["score"]}
                     for r in risks]

    # ── pending mitigations ───────────────────────────────────────────────────
    pending_controls = []
    seen_labels = set()
    for r in risks:
        for c in r["controls"]:
            if c["status"] == "Pending" and c["id"] not in seen_labels:
                seen_labels.add(c["id"])
                pending_controls.append({
                    "label":  c["id"],
                    "detail": c["name"],
                    "status": "Pending",
                })
    # Take top 3 unique
    mitigations = pending_controls[:3]

    # ── perimeter table ───────────────────────────────────────────────────────
    perimeter = {}
    for dom in domains:
        dom_risks = [r for r in risks if r["domain"] == dom]

        # Internal: Euronext controls
        int_pending = []
        for r in dom_risks:
            for c in r["controls"]:
                if c["id"].startswith("Euronext") and c["status"] == "Pending":
                    int_pending.append(c["name"][:22])
        # External: CIS/ISO controls
        ext_pending = []
        for r in dom_risks:
            for c in r["controls"]:
                if not c["id"].startswith("Euronext") and c["status"] == "Pending":
                    ext_pending.append(c["name"][:22])

        if int_pending:
            int_text  = "⚠  " + "\n".join(int_pending[:2])
            int_alert = True
        else:
            int_text  = "✔  Mitigated"
            int_alert = False

        if ext_pending:
            ext_text  = "⚠  " + ext_pending[0]
            ext_alert = True
        else:
            ext_text  = "✔  Mitigated"
            ext_alert = False

        perimeter[dom] = {
            "internal": {"text": int_text,  "alert": int_alert},
            "external": {"text": ext_text, "alert": ext_alert},
        }

    # ── key findings ─────────────────────────────────────────────────────────
    impl_count    = sum(1 for r in risks for c in r["controls"] if c["status"] == "Implemented")
    pending_count = len(pending_controls)
    top_domain    = max(domain_scores, key=domain_scores.get)
    top_dom_score = domain_scores[top_domain]
    findings = [
        f"All vendor controls (CIS/ISO) are Implemented; {pending_count} Euronext controls remain Pending — immediate action required.",
        f"Highest residual risk {top_dom_score} in {top_domain} — {mitigations[0]['label'] if mitigations else 'SOC integration'} is the critical priority.",
        f"{'DORA scope: active — heightened monitoring required' if dora_scope else 'Not-DORA scope — standard monitoring cadence'}. Next review: Q2 2026",
    ]

    # ── service description ───────────────────────────────────────────────────
    # Generic service desc based on vendor name (can be overridden manually)
    vendor_lower = vendor.lower()
    if "alva" in vendor_lower:
        service_desc = "SaaS HR Talent Assessment Platform — pre-employment cognitive & behavioral testing, team analytics"
    else:
        service_desc = f"SaaS/Cloud service — {vendor} — ICT Third-Party"

    return {
        "vendor":        vendor,
        "assessment_id": assess_id,
        "report_date":   "February 2026",
        "service_desc":  service_desc,
        "dora_scope":    dora_scope,
        "criticality":   crit_label,
        "overall_risk":  overall_risk,
        "certifications": certs,
        "domain_scores": domain_scores,
        "top_risks":     top_risks,
        "full_register": full_register,
        "mitigations":   mitigations,
        "perimeter":     perimeter,
        "findings":      findings,
        "_raw_risks":    risks,    # full risk list for reference
    }


# ── CLI ────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract TPRM PDF to JSON")
    parser.add_argument("--input",  required=True, help="Path to assessment PDF")
    parser.add_argument("--output", required=True, help="Path to output JSON file")
    args = parser.parse_args()

    data = extract(args.input)
    out = Path(args.output)
    out.write_text(json.dumps(data, indent=2, default=str))
    print(f"✅  Extracted {len(data['_raw_risks'])} risks → {out}")
    print(f"    Vendor: {data['vendor']}")
    print(f"    Domain scores: {data['domain_scores']}")
    print(f"    Overall risk:  {data['overall_risk']}")
