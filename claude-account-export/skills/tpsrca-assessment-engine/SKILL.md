---
name: tpsrca-assessment-engine
description: Comprehensive assessment engine for TPSRCA with 12 specialized agents for risk calculation (inherent/residual), score aggregation, data confidence validation, framework compliance scoring, gap analysis, evidence validation, and recommendation generation. Use this skill to orchestrate full TPSRCA assessments with automated scoring, calculations, and quality assurance. Integrates with tpsrca-supplier-classifier, tpsrca-osint-agents, and tpsrca-html-template for end-to-end assessment automation.
---

# TPSRCA Assessment Engine

Comprehensive orchestration engine with 12 specialized agents for automated TPSRCA assessment execution, scoring, and quality assurance.

## Agent Overview

| # | Agent | Purpose | Output |
|---|-------|---------|--------|
| 1 | **Orchestrator** | Coordinates all agents and workflow | Execution plan, status |
| 2 | **Data Confidence** | Validates and scores data quality | Confidence ratings |
| 3 | **Evidence Validator** | Verifies and rates evidence sources | Evidence scores |
| 4 | **Inherent Risk Calculator** | Calculates pre-control risk scores | Inherent risk matrix |
| 5 | **Control Effectiveness** | Assesses control implementation | Control scores |
| 6 | **Residual Risk Calculator** | Calculates post-control risk | Residual risk matrix |
| 7 | **Framework Scorer** | Calculates compliance percentages | Framework scores |
| 8 | **Composite Scorer** | Aggregates all scores | Overall rating |
| 9 | **Gap Analyzer** | Identifies and prioritizes gaps | Gap register |
| 10 | **Trend Analyzer** | Compares with previous assessments | Trend indicators |
| 11 | **Recommendation Engine** | Generates prioritized actions | Action plan |
| 12 | **Report Generator** | Produces final assessment output | TPSRCA report |

## Complete Assessment Workflow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TPSRCA ASSESSMENT ENGINE                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
         ┌──────────────────────────┼──────────────────────────┐
         │                          │                          │
         ▼                          ▼                          ▼
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│ PHASE 1: INPUT  │      │ PHASE 2: COLLECT│      │ PHASE 3: VALIDATE│
│ Classification  │─────▶│ OSINT Agents    │─────▶│ Quality Assure  │
│ (Classifier)    │      │ (8 Agents)      │      │ (Agents 2-3)    │
└─────────────────┘      └─────────────────┘      └─────────────────┘
                                                          │
         ┌────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PHASE 4: CALCULATE                                   │
├─────────────────┬─────────────────┬─────────────────┬─────────────────┬─────┤
│ Agent 4:        │ Agent 5:        │ Agent 6:        │ Agent 7:        │     │
│ Inherent Risk   │ Control Effect. │ Residual Risk   │ Framework Score │     │
│ Calculator      │ Assessor        │ Calculator      │ Calculator      │     │
└─────────────────┴─────────────────┴─────────────────┴─────────────────┴─────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PHASE 5: ANALYZE                                     │
├─────────────────┬─────────────────┬─────────────────┬─────────────────┬─────┤
│ Agent 8:        │ Agent 9:        │ Agent 10:       │ Agent 11:       │     │
│ Composite       │ Gap             │ Trend           │ Recommendation  │     │
│ Scorer          │ Analyzer        │ Analyzer        │ Engine          │     │
└─────────────────┴─────────────────┴─────────────────┴─────────────────┴─────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PHASE 6: OUTPUT                                      │
│                     Agent 12: Report Generator                               │
│                     (tpsrca-html-template)                                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Agent 1: Assessment Orchestrator

**Purpose:** Coordinate all agents, manage workflow, track progress

### Orchestration Protocol

```python
class AssessmentOrchestrator:
    def execute_assessment(supplier_url):
        # Phase 1: Classification
        classification = run_supplier_classifier(supplier_url)
        assessment_scope = determine_scope(classification)
        
        # Phase 2: Data Collection
        osint_data = run_osint_agents(supplier_url, assessment_scope)
        
        # Phase 3: Validation
        confidence_scores = run_data_confidence_agent(osint_data)
        evidence_ratings = run_evidence_validator(osint_data)
        
        # Phase 4: Calculations
        inherent_risks = run_inherent_risk_calculator(osint_data)
        control_scores = run_control_effectiveness(osint_data)
        residual_risks = run_residual_risk_calculator(inherent_risks, control_scores)
        framework_scores = run_framework_scorer(osint_data, control_scores)
        
        # Phase 5: Analysis
        composite_score = run_composite_scorer(framework_scores, residual_risks)
        gaps = run_gap_analyzer(osint_data, framework_scores)
        trends = run_trend_analyzer(composite_score, previous_assessments)
        recommendations = run_recommendation_engine(gaps, residual_risks)
        
        # Phase 6: Output
        report = run_report_generator(all_data)
        return report
```

### Assessment Scope Matrix

| Tier | Agents to Run | Frameworks | Depth |
|------|---------------|------------|-------|
| A.01-A.03 | All 12 | All 10 | Full + Enhanced |
| B.01-B.03 | All 12 | All 10 | Full |
| C.01-C.03 | 1-9, 11-12 | Core 6 | Standard |
| D.01-D.05 | 1-3, 8, 12 | Basic 3 | Lite |

---

## Agent 2: Data Confidence Validator

**Purpose:** Assess reliability and completeness of collected data

### Confidence Scoring Criteria

| Factor | Weight | Scoring |
|--------|--------|---------|
| **Source Authority** | 30% | Official=100, Semi-official=70, Third-party=50, Inferred=20 |
| **Data Freshness** | 25% | <30 days=100, <90 days=80, <1 year=60, >1 year=30 |
| **Corroboration** | 25% | 3+ sources=100, 2 sources=70, 1 source=40 |
| **Completeness** | 20% | All fields=100, Most fields=70, Partial=40, Minimal=20 |

### Confidence Level Thresholds

| Score | Level | Interpretation | Action |
|-------|-------|----------------|--------|
| 85-100 | **High** | Reliable data, suitable for decisions | Proceed |
| 70-84 | **Medium** | Generally reliable, some gaps | Note limitations |
| 50-69 | **Low** | Significant uncertainty | Request vendor data |
| 0-49 | **Very Low** | Insufficient for assessment | Escalate to vendor |

### Confidence Calculation

```
Confidence_Score = 
    (Source_Authority × 0.30) +
    (Data_Freshness × 0.25) +
    (Corroboration × 0.25) +
    (Completeness × 0.20)
```

### Output Schema

```json
{
  "data_confidence": {
    "overall_score": 78,
    "level": "Medium",
    "sections": {
      "corporate_profile": {"score": 92, "level": "High"},
      "security_posture": {"score": 85, "level": "High"},
      "data_protection": {"score": 72, "level": "Medium"},
      "ai_governance": {"score": 58, "level": "Low"},
      "integrations": {"score": 80, "level": "Medium"},
      "compliance": {"score": 75, "level": "Medium"},
      "risk_intelligence": {"score": 82, "level": "Medium"},
      "infrastructure": {"score": 70, "level": "Medium"}
    },
    "low_confidence_items": [
      {"field": "ISO 42001 certification", "score": 35, "recommendation": "Request from vendor"}
    ]
  }
}
```

---

## Agent 3: Evidence Validator

**Purpose:** Verify evidence sources and assign reliability ratings

### Evidence Categories

| Category | Examples | Base Reliability |
|----------|----------|------------------|
| **Primary Official** | Security page, DPA, Privacy policy | 95% |
| **Primary Technical** | SSL Labs, Security Headers tests | 90% |
| **Regulatory/Gov** | Company registry, DPA enforcement | 95% |
| **Certification Body** | ISO certificate, SOC report | 90% |
| **Third-Party Analyst** | Gartner, G2, Capterra | 70% |
| **News/Press** | Tech news, press releases | 60% |
| **Social/Community** | LinkedIn, forums | 40% |
| **Inferred** | Based on analysis, not stated | 30% |

### Evidence Validation Checks

```
For each evidence source:
1. URL accessibility (is it reachable?)
2. Content verification (does content match claim?)
3. Date validation (when was it published/updated?)
4. Authority check (is source authoritative?)
5. Cross-reference (do other sources confirm?)
```

### Evidence Score Calculation

```
Evidence_Score = Base_Reliability × Accessibility × Freshness × Cross_Reference

Where:
- Accessibility: 1.0 if reachable, 0.5 if cached/archived, 0 if unreachable
- Freshness: 1.0 if <1 year, 0.8 if 1-2 years, 0.5 if >2 years
- Cross_Reference: 1.0 if confirmed, 0.8 if consistent, 0.6 if single source
```

### Output Schema

```json
{
  "evidence_validation": {
    "total_sources": 45,
    "validated_sources": 42,
    "failed_sources": 3,
    "average_reliability": 78,
    "sources": [
      {
        "url": "https://example.com/security",
        "category": "Primary Official",
        "reliability_score": 92,
        "accessible": true,
        "last_verified": "2024-12-11",
        "supports_claims": ["ISO 27001 certified", "GDPR compliant"]
      }
    ],
    "unreliable_claims": [
      {"claim": "SOC 2 Type II certified", "reason": "No evidence found", "action": "Request documentation"}
    ]
  }
}
```

---

## Agent 4: Inherent Risk Calculator

**Purpose:** Calculate pre-control (inherent) risk scores

### Inherent Risk Formula

```
Inherent_Risk_Score = Likelihood × Impact

Where:
- Likelihood: 1 (Rare) to 5 (Almost Certain)
- Impact: 1 (Negligible) to 5 (Catastrophic)
- Score Range: 1-25
```

### Likelihood Assessment Criteria

| Score | Level | Frequency | Probability |
|-------|-------|-----------|-------------|
| 5 | Almost Certain | Multiple times per year | >90% |
| 4 | Likely | Once per year | 60-90% |
| 3 | Possible | Once per 2-3 years | 30-60% |
| 2 | Unlikely | Once per 5 years | 10-30% |
| 1 | Rare | Once per 10+ years | <10% |

### Impact Assessment Criteria

| Score | Level | Financial | Operational | Reputational | Regulatory |
|-------|-------|-----------|-------------|--------------|------------|
| 5 | Catastrophic | >€10M | Complete failure | Major public incident | License revocation |
| 4 | Major | €1-10M | Significant disruption | Significant media | Major fine |
| 3 | Moderate | €100K-1M | Partial disruption | Limited media | Regulatory warning |
| 2 | Minor | €10-100K | Minor inconvenience | Customer complaints | Minor findings |
| 1 | Negligible | <€10K | Minimal impact | Internal only | No action |

### Risk Category Mapping

| Category | Risk Domains | Typical Inherent Risks |
|----------|--------------|------------------------|
| **Security** | Confidentiality, Integrity, Availability | Data breach, unauthorized access, system compromise |
| **AI Governance** | Transparency, Bias, Accountability | Algorithmic bias, unexplainable decisions, data misuse |
| **Compliance** | Regulatory, Contractual, Legal | DORA non-compliance, GDPR violation, contract breach |
| **Operational** | Continuity, Performance, Dependency | Service disruption, vendor lock-in, concentration risk |

### Inherent Risk Rating Scale

| Score | Rating | Color | Action Priority |
|-------|--------|-------|-----------------|
| 20-25 | **Critical** | Red | Immediate action required |
| 15-19 | **High** | Orange | Priority remediation |
| 10-14 | **Medium** | Yellow | Planned remediation |
| 5-9 | **Low** | Green | Monitor and review |
| 1-4 | **Very Low** | Blue | Accept or monitor |

### Output Schema

```json
{
  "inherent_risks": {
    "total_risks": 35,
    "by_rating": {
      "critical": 3,
      "high": 8,
      "medium": 14,
      "low": 10
    },
    "by_category": {
      "security": 12,
      "ai_governance": 6,
      "compliance": 9,
      "operational": 8
    },
    "risks": [
      {
        "id": "IR-001",
        "category": "Security",
        "description": "Data breach due to inadequate access controls",
        "likelihood": 3,
        "impact": 5,
        "inherent_score": 15,
        "inherent_rating": "High",
        "risk_factors": ["Multi-tenant architecture", "API access", "Personal data processed"]
      }
    ],
    "total_inherent_exposure": 385
  }
}
```

---

## Agent 5: Control Effectiveness Assessor

**Purpose:** Evaluate implementation and effectiveness of controls

### Control Assessment Dimensions

| Dimension | Weight | Description |
|-----------|--------|-------------|
| **Design Effectiveness** | 40% | Is the control properly designed to mitigate the risk? |
| **Operating Effectiveness** | 40% | Is the control operating as intended? |
| **Coverage** | 20% | Does the control cover all relevant risks? |

### Control Implementation Status

| Status | Score | Definition |
|--------|-------|------------|
| **Implemented** | 100 | Fully deployed and operational |
| **Partial** | 60 | Partially implemented or limited scope |
| **Planned** | 30 | Planned but not yet implemented |
| **Gap** | 0 | No control in place |

### Control Effectiveness Rating

| Rating | Score Range | Effectiveness % | Risk Reduction |
|--------|-------------|-----------------|----------------|
| **Excellent** | 90-100 | 85-100% | Reduce risk by 4 levels |
| **Good** | 70-89 | 65-84% | Reduce risk by 3 levels |
| **Adequate** | 50-69 | 45-64% | Reduce risk by 2 levels |
| **Weak** | 30-49 | 25-44% | Reduce risk by 1 level |
| **Ineffective** | 0-29 | 0-24% | No risk reduction |

### Control Effectiveness Calculation

```
Control_Effectiveness = 
    (Design_Score × 0.40) +
    (Operating_Score × 0.40) +
    (Coverage_Score × 0.20)

Risk_Reduction_Factor = Control_Effectiveness / 100
```

### Control Categories

| Domain | Control Types | Key Indicators |
|--------|---------------|----------------|
| **Access Control** | IAM, MFA, RBAC, PAM | Authentication strength, access reviews |
| **Data Protection** | Encryption, DLP, Masking | Encryption standards, key management |
| **Network Security** | Firewall, WAF, Segmentation | Perimeter defense, traffic monitoring |
| **Incident Management** | SIEM, IRP, Forensics | Detection time, response capability |
| **BCP/DR** | Backup, Recovery, Failover | RTO/RPO, testing frequency |
| **AI Controls** | Oversight, Monitoring, Audit | Human review, model governance |

### Output Schema

```json
{
  "control_effectiveness": {
    "total_controls": 175,
    "by_status": {
      "implemented": 112,
      "partial": 43,
      "planned": 12,
      "gap": 8
    },
    "by_effectiveness": {
      "excellent": 45,
      "good": 67,
      "adequate": 38,
      "weak": 17,
      "ineffective": 8
    },
    "by_domain": {
      "access_control": {"count": 35, "avg_effectiveness": 78},
      "data_protection": {"count": 42, "avg_effectiveness": 82},
      "network_security": {"count": 28, "avg_effectiveness": 75},
      "incident_management": {"count": 25, "avg_effectiveness": 68},
      "bcp_dr": {"count": 20, "avg_effectiveness": 58},
      "ai_controls": {"count": 25, "avg_effectiveness": 42}
    },
    "overall_effectiveness": 72,
    "implementation_rate": 64
  }
}
```

---

## Agent 6: Residual Risk Calculator

**Purpose:** Calculate post-control (residual) risk scores

### Residual Risk Formula

```
Residual_Risk_Score = Inherent_Risk_Score × (1 - Control_Effectiveness_Factor)

Where:
- Inherent_Risk_Score: From Agent 4
- Control_Effectiveness_Factor: From Agent 5 (as decimal, e.g., 0.72)

Alternative formula with explicit reduction:
Residual_Likelihood = Inherent_Likelihood - Likelihood_Reduction
Residual_Impact = Inherent_Impact - Impact_Reduction
Residual_Score = Residual_Likelihood × Residual_Impact
```

### Control Effect on Risk Components

| Control Type | Primary Effect | Secondary Effect |
|--------------|----------------|------------------|
| **Preventive** | Reduces Likelihood | - |
| **Detective** | Reduces Likelihood | Enables Response |
| **Corrective** | Reduces Impact | Enables Recovery |
| **Compensating** | Reduces Both | Partial coverage |

### Risk Reduction Matrix

| Control Effectiveness | Likelihood Reduction | Impact Reduction |
|----------------------|---------------------|------------------|
| Excellent (90-100%) | -2 levels | -2 levels |
| Good (70-89%) | -1.5 levels | -1.5 levels |
| Adequate (50-69%) | -1 level | -1 level |
| Weak (30-49%) | -0.5 levels | -0.5 levels |
| Ineffective (0-29%) | 0 | 0 |

### Residual Risk Rating Thresholds

| Residual Score | Rating | Risk Appetite | Decision |
|----------------|--------|---------------|----------|
| 15-25 | **Critical** | Unacceptable | Do not proceed without remediation |
| 10-14 | **High** | Above tolerance | Conditional approval with plan |
| 5-9 | **Medium** | Within tolerance | Approve with monitoring |
| 1-4 | **Low** | Acceptable | Approve |

### Risk Treatment Options

| Residual Level | Treatment Options |
|----------------|-------------------|
| **Critical** | Avoid, Transfer (contractual), Mitigate (urgent) |
| **High** | Mitigate (priority), Transfer (insurance), Accept (executive) |
| **Medium** | Mitigate (planned), Accept (documented) |
| **Low** | Accept, Monitor |

### Output Schema

```json
{
  "residual_risks": {
    "total_risks": 35,
    "by_rating": {
      "critical": 0,
      "high": 3,
      "medium": 12,
      "low": 20
    },
    "risk_reduction_summary": {
      "average_inherent_score": 11.2,
      "average_residual_score": 5.8,
      "average_reduction": 48,
      "total_inherent_exposure": 385,
      "total_residual_exposure": 198,
      "overall_risk_reduction": 49
    },
    "risks": [
      {
        "id": "RR-001",
        "inherent_risk_id": "IR-001",
        "description": "Data breach due to inadequate access controls",
        "inherent_likelihood": 3,
        "inherent_impact": 5,
        "inherent_score": 15,
        "inherent_rating": "High",
        "control_effectiveness": 72,
        "residual_likelihood": 2,
        "residual_impact": 4,
        "residual_score": 8,
        "residual_rating": "Medium",
        "risk_reduction": 47,
        "treatment": "Accept with monitoring",
        "controls_applied": ["AC-001", "AC-003", "DP-002"]
      }
    ],
    "risks_requiring_treatment": [
      {"id": "RR-005", "residual_score": 12, "required_action": "Implement additional encryption"}
    ]
  }
}
```

---

## Agent 7: Framework Compliance Scorer

**Purpose:** Calculate compliance percentages for each framework

### Framework Scoring Methodology

```
Framework_Score = (Σ Control_Weighted_Scores) / (Σ Maximum_Possible_Scores) × 100

Where:
- Control_Weighted_Score = Control_Score × Control_Weight
- Control_Weight based on criticality (Critical=3, High=2, Medium=1.5, Low=1)
```

### Framework Control Mappings

| Framework | Total Controls | Critical | High | Medium | Low |
|-----------|---------------|----------|------|--------|-----|
| **DORA** | 45 | 12 | 18 | 10 | 5 |
| **ISO 27001** | 93 | 15 | 35 | 30 | 13 |
| **NIST CSF** | 108 | 18 | 40 | 35 | 15 |
| **GDPR** | 35 | 10 | 15 | 7 | 3 |
| **NIS2** | 28 | 8 | 12 | 6 | 2 |
| **EU AI Act** | 25 | 8 | 10 | 5 | 2 |
| **ISO 42001** | 42 | 10 | 18 | 10 | 4 |
| **CIS v8.1** | 153 | 20 | 55 | 50 | 28 |
| **EBA GL** | 38 | 12 | 16 | 8 | 2 |
| **CPMI-IOSCO** | 22 | 10 | 8 | 3 | 1 |

### Compliance Level Thresholds

| Score | Level | Visual | Interpretation |
|-------|-------|--------|----------------|
| 90-100% | **Excellent** | ████████████ | Fully compliant |
| 80-89% | **Good** | █████████░░░ | Minor gaps |
| 70-79% | **Satisfactory** | ████████░░░░ | Some improvements needed |
| 60-69% | **Needs Improvement** | ██████░░░░░░ | Significant gaps |
| 50-59% | **Concerning** | █████░░░░░░░ | Major gaps |
| <50% | **Critical** | ████░░░░░░░░ | Fundamental issues |

### DORA-Specific Scoring

| Article | Requirement Area | Weight | Max Points |
|---------|------------------|--------|------------|
| Art. 28(2)(a) | Service description | 10% | 10 |
| Art. 28(2)(b) | Data locations | 10% | 10 |
| Art. 28(2)(c) | SLA descriptions | 10% | 10 |
| Art. 28(2)(d) | Incident notification | 15% | 15 |
| Art. 28(2)(e) | Subcontracting | 10% | 10 |
| Art. 28(2)(f) | Business continuity | 10% | 10 |
| Art. 28(2)(g) | Data protection | 10% | 10 |
| Art. 28(2)(h) | Cooperation | 5% | 5 |
| Art. 28(2)(i) | Audit rights | 10% | 10 |
| Art. 28(2)(j) | Exit strategy | 10% | 10 |

### NIST CSF 2.0 Function Scoring

| Function | Weight | Categories |
|----------|--------|------------|
| **GOVERN** | 15% | Organizational Context, Risk Management Strategy, Roles |
| **IDENTIFY** | 15% | Asset Management, Business Environment, Risk Assessment |
| **PROTECT** | 25% | Access Control, Awareness, Data Security, Platform Security |
| **DETECT** | 15% | Continuous Monitoring, Detection Processes |
| **RESPOND** | 15% | Response Planning, Communications, Analysis, Mitigation |
| **RECOVER** | 15% | Recovery Planning, Improvements, Communications |

### Output Schema

```json
{
  "framework_scores": {
    "dora": {
      "overall_score": 65,
      "level": "Needs Improvement",
      "articles": {
        "28_2_a": {"score": 80, "status": "Good"},
        "28_2_b": {"score": 90, "status": "Excellent"},
        "28_2_c": {"score": 70, "status": "Satisfactory"},
        "28_2_d": {"score": 60, "status": "Needs Improvement"},
        "28_2_e": {"score": 55, "status": "Concerning"},
        "28_2_f": {"score": 45, "status": "Critical"},
        "28_2_g": {"score": 85, "status": "Good"},
        "28_2_h": {"score": 70, "status": "Satisfactory"},
        "28_2_i": {"score": 40, "status": "Critical"},
        "28_2_j": {"score": 50, "status": "Concerning"}
      },
      "gaps": ["Audit rights", "Exit strategy", "BCP"]
    },
    "iso_27001": {
      "overall_score": 82,
      "level": "Good",
      "annex_a": {
        "organizational": 85,
        "people": 80,
        "physical": 78,
        "technological": 84
      }
    },
    "nist_csf": {
      "overall_score": 75,
      "level": "Satisfactory",
      "functions": {
        "govern": 70,
        "identify": 78,
        "protect": 82,
        "detect": 75,
        "respond": 68,
        "recover": 65
      }
    },
    "gdpr": {"overall_score": 85, "level": "Good"},
    "nis2": {"overall_score": 68, "level": "Needs Improvement"},
    "eu_ai_act": {"overall_score": 45, "level": "Critical"},
    "iso_42001": {"overall_score": 35, "level": "Critical"}
  }
}
```

---

## Agent 8: Composite Scorer

**Purpose:** Aggregate all scores into overall supplier rating

### Composite Score Formula

```
Composite_Score = 
    (Framework_Score × 0.35) +
    (Control_Effectiveness × 0.25) +
    (Residual_Risk_Score × 0.25) +
    (Data_Confidence × 0.15)

Where:
- Framework_Score = Weighted average of applicable frameworks
- Control_Effectiveness = Overall implementation rate and effectiveness
- Residual_Risk_Score = 100 - (Normalized residual exposure)
- Data_Confidence = Overall confidence level
```

### Framework Weighting by Tier

| Tier | DORA | ISO 27001 | GDPR | NIST | NIS2 | EU AI | Other |
|------|------|-----------|------|------|------|-------|-------|
| A.01-A.03 | 25% | 20% | 15% | 15% | 10% | 10% | 5% |
| B.01-B.03 | 20% | 25% | 20% | 15% | 10% | 5% | 5% |
| C.01-C.03 | 15% | 30% | 25% | 20% | 5% | 0% | 5% |

### Supplier Rating Scale

| Score | Rating | Tier | Approval Status |
|-------|--------|------|-----------------|
| 90-100 | **L1 - Exemplary** | ★★★★★ | Full approval |
| 80-89 | **L2 - Strong** | ★★★★☆ | Approved |
| 70-79 | **L3 - Adequate** | ★★★☆☆ | Conditional approval |
| 60-69 | **L4 - Weak** | ★★☆☆☆ | Approval with remediation |
| <60 | **L5 - Unacceptable** | ★☆☆☆☆ | Not approved |

### Approval Decision Matrix

| Rating | Critical Risks | Decision |
|--------|---------------|----------|
| L1-L2 | 0 | Approve |
| L1-L2 | 1-2 | Approve with monitoring |
| L3 | 0 | Conditional approval |
| L3 | 1-2 | Conditional with remediation plan |
| L3 | 3+ | Not approved |
| L4-L5 | Any | Not approved |

### Output Schema

```json
{
  "composite_score": {
    "overall_score": 68,
    "rating": "L3 - Adequate",
    "tier_stars": 3,
    "approval_status": "Conditional Approval",
    "components": {
      "framework_score": {"score": 72, "weight": 0.35, "contribution": 25.2},
      "control_effectiveness": {"score": 64, "weight": 0.25, "contribution": 16.0},
      "residual_risk_score": {"score": 65, "weight": 0.25, "contribution": 16.25},
      "data_confidence": {"score": 78, "weight": 0.15, "contribution": 11.7}
    },
    "score_breakdown": {
      "strengths": ["ISO 27001 certified", "Strong data protection", "Good security posture"],
      "weaknesses": ["AI governance gaps", "BCP/DR concerns", "Audit rights limited"]
    },
    "conditions": [
      "Implement ISO 42001 roadmap within 12 months",
      "Enhance BCP testing frequency",
      "Negotiate audit rights in contract renewal"
    ],
    "next_review": "2025-06-11"
  }
}
```

---

## Agent 9: Gap Analyzer

**Purpose:** Identify, categorize, and prioritize compliance gaps

### Gap Identification Process

```
For each framework requirement:
    IF requirement_status != "Compliant":
        gap = {
            requirement: requirement_id,
            current_state: assessed_status,
            target_state: "Compliant",
            gap_severity: calculate_severity(),
            remediation_effort: estimate_effort(),
            priority_score: severity × effort_inverse
        }
        gaps.append(gap)
```

### Gap Severity Scoring

| Factor | Weight | Scoring Criteria |
|--------|--------|------------------|
| **Regulatory Impact** | 35% | Penalty exposure, enforcement risk |
| **Security Impact** | 30% | Breach potential, data exposure |
| **Operational Impact** | 20% | Business disruption, service quality |
| **Contractual Impact** | 15% | SLA breach, contract compliance |

### Gap Priority Matrix

| Severity | Effort | Priority | Action Timeline |
|----------|--------|----------|-----------------|
| Critical | Low | **P1** | Immediate (0-30 days) |
| Critical | Medium | **P1** | Urgent (30-60 days) |
| Critical | High | **P2** | High priority (60-90 days) |
| High | Low | **P2** | High priority (30-60 days) |
| High | Medium | **P3** | Medium priority (60-90 days) |
| High | High | **P3** | Planned (90-180 days) |
| Medium | Any | **P4** | Planned (90-180 days) |
| Low | Any | **P5** | Monitor (180+ days) |

### Gap Categories

| Category | Examples |
|----------|----------|
| **Documentation** | Missing policies, outdated procedures |
| **Technical** | Missing controls, configuration gaps |
| **Process** | Inadequate processes, missing reviews |
| **Contractual** | DPA gaps, SLA deficiencies |
| **Certification** | Missing certifications, expired audits |
| **Governance** | Oversight gaps, accountability issues |

### Output Schema

```json
{
  "gap_analysis": {
    "total_gaps": 28,
    "by_priority": {
      "P1": 3,
      "P2": 7,
      "P3": 10,
      "P4": 5,
      "P5": 3
    },
    "by_category": {
      "documentation": 5,
      "technical": 8,
      "process": 6,
      "contractual": 4,
      "certification": 3,
      "governance": 2
    },
    "by_framework": {
      "dora": 8,
      "iso_27001": 5,
      "gdpr": 3,
      "eu_ai_act": 7,
      "iso_42001": 5
    },
    "gaps": [
      {
        "id": "GAP-001",
        "framework": "DORA",
        "requirement": "Art. 28(2)(i) - Audit rights",
        "current_state": "No contractual audit rights",
        "target_state": "Annual audit rights with 30-day notice",
        "severity": "Critical",
        "effort": "Medium",
        "priority": "P1",
        "category": "Contractual",
        "remediation": "Negotiate audit clause in contract renewal",
        "owner": "Legal/Procurement",
        "target_date": "2025-03-01"
      }
    ],
    "gap_closure_plan": {
      "30_day": ["GAP-001", "GAP-003"],
      "60_day": ["GAP-002", "GAP-005", "GAP-007"],
      "90_day": ["GAP-004", "GAP-006", "GAP-008"]
    }
  }
}
```

---

## Agent 10: Trend Analyzer

**Purpose:** Compare current assessment with historical data

### Trend Metrics

| Metric | Calculation | Interpretation |
|--------|-------------|----------------|
| **Score Delta** | Current - Previous | + = Improved, - = Declined |
| **Risk Trend** | (Current - Previous) / Previous × 100 | % change |
| **Velocity** | Score Delta / Time Period | Rate of change |
| **Trajectory** | Linear projection | Future estimate |

### Trend Categories

| Trend | Visual | Meaning |
|-------|--------|---------|
| **Strong Improvement** | ↑↑ | >10% improvement |
| **Improvement** | ↑ | 5-10% improvement |
| **Stable** | → | -5% to +5% |
| **Decline** | ↓ | 5-10% decline |
| **Strong Decline** | ↓↓ | >10% decline |

### Historical Comparison Points

```
Compare against:
- Previous assessment (if available)
- 6-month trend
- 12-month trend
- Industry benchmark
- Peer group average
```

### Output Schema

```json
{
  "trend_analysis": {
    "current_score": 68,
    "previous_score": 62,
    "score_delta": 6,
    "trend": "Improvement",
    "trend_icon": "↑",
    "history": [
      {"date": "2024-06-11", "score": 55},
      {"date": "2024-09-11", "score": 62},
      {"date": "2024-12-11", "score": 68}
    ],
    "trajectory": {
      "6_month_projection": 74,
      "12_month_projection": 80,
      "confidence": "Medium"
    },
    "component_trends": {
      "framework_score": {"current": 72, "previous": 65, "trend": "↑"},
      "control_effectiveness": {"current": 64, "previous": 58, "trend": "↑"},
      "residual_risk": {"current": 65, "previous": 60, "trend": "↑"},
      "data_confidence": {"current": 78, "previous": 75, "trend": "→"}
    },
    "notable_changes": [
      {"area": "ISO 27001", "change": "+12%", "reason": "New certification achieved"},
      {"area": "AI Governance", "change": "-5%", "reason": "New AI systems not yet governed"}
    ],
    "benchmark_comparison": {
      "industry_average": 65,
      "position": "Above average",
      "percentile": 72
    }
  }
}
```

---

## Agent 11: Recommendation Engine

**Purpose:** Generate prioritized, actionable recommendations

### Recommendation Generation Logic

```python
def generate_recommendations(gaps, residual_risks, framework_scores):
    recommendations = []
    
    # From critical/high residual risks
    for risk in residual_risks.filter(rating__in=['Critical', 'High']):
        recommendations.append({
            'source': 'risk',
            'priority': 'P1' if risk.rating == 'Critical' else 'P2',
            'action': generate_risk_mitigation(risk),
            'impact': calculate_impact(risk),
            'effort': estimate_effort(risk)
        })
    
    # From P1/P2 gaps
    for gap in gaps.filter(priority__in=['P1', 'P2']):
        recommendations.append({
            'source': 'gap',
            'priority': gap.priority,
            'action': generate_gap_closure(gap),
            'impact': gap.severity,
            'effort': gap.effort
        })
    
    # From low framework scores
    for framework in framework_scores.filter(score__lt=60):
        recommendations.append({
            'source': 'compliance',
            'priority': 'P2',
            'action': generate_compliance_action(framework),
            'impact': 'High',
            'effort': 'High'
        })
    
    return prioritize_recommendations(recommendations)
```

### Recommendation Categories

| Category | Focus | Examples |
|----------|-------|----------|
| **Quick Wins** | Low effort, high impact | Policy updates, configuration changes |
| **Must Do** | Critical items regardless of effort | Regulatory mandates, critical risks |
| **Strategic** | High effort, high impact | Certification projects, major upgrades |
| **Monitor** | Low priority items | Future improvements, nice-to-haves |

### Recommendation Template

```markdown
## Recommendation: [Title]

**Priority:** P1 / P2 / P3 / P4 / P5
**Category:** Quick Win / Must Do / Strategic / Monitor
**Source:** Gap [ID] / Risk [ID] / Framework [Name]

### Description
[Clear description of what needs to be done]

### Business Justification
- **Regulatory Impact:** [Description]
- **Risk Reduction:** [Expected reduction in risk score]
- **Compliance Improvement:** [Expected framework score improvement]

### Implementation
- **Effort:** Low / Medium / High
- **Timeline:** [Days/Weeks/Months]
- **Owner:** [Suggested owner]
- **Resources:** [Required resources]

### Success Criteria
- [Measurable outcome 1]
- [Measurable outcome 2]

### Dependencies
- [Dependency 1]
- [Dependency 2]
```

### Output Schema

```json
{
  "recommendations": {
    "total": 15,
    "by_priority": {"P1": 2, "P2": 5, "P3": 5, "P4": 3},
    "by_category": {"quick_win": 4, "must_do": 3, "strategic": 5, "monitor": 3},
    "items": [
      {
        "id": "REC-001",
        "title": "Negotiate audit rights in DPA",
        "priority": "P1",
        "category": "Must Do",
        "source": {"type": "gap", "id": "GAP-001"},
        "description": "Amend DPA to include annual audit rights with 30-day notice provision",
        "justification": {
          "regulatory": "DORA Art. 28(2)(i) mandatory requirement",
          "risk_reduction": "Reduces audit risk score by 60%",
          "compliance_improvement": "+8% DORA compliance"
        },
        "implementation": {
          "effort": "Medium",
          "timeline": "60 days",
          "owner": "Legal/Procurement",
          "resources": ["Legal counsel", "Contract template"]
        },
        "success_criteria": [
          "Audit rights clause included in amended DPA",
          "30-day notice period documented",
          "Annual audit schedule agreed"
        ],
        "target_date": "2025-02-15"
      }
    ],
    "priority_actions": [
      {"action": "Negotiate audit rights", "deadline": "2025-02-15", "owner": "Legal"},
      {"action": "Request ISO 42001 roadmap", "deadline": "2025-01-31", "owner": "InfoSec"},
      {"action": "Review BCP documentation", "deadline": "2025-03-01", "owner": "Risk"}
    ]
  }
}
```

---

## Agent 12: Report Generator

**Purpose:** Produce final TPSRCA assessment report

### Report Structure

```
1. Executive Summary
   - Overall score and rating
   - Key findings
   - Approval recommendation
   - Priority actions

2. Supplier Classification
   - Supplier type and tier
   - Service categories
   - DORA classification
   - AI usage summary

3. Dashboard
   - KPI metrics
   - Framework compliance chart
   - Risk distribution
   - Trend indicators

4. Detailed Assessments
   - Framework-by-framework scores
   - Control effectiveness
   - Risk register (inherent + residual)

5. Gap Analysis
   - Prioritized gaps
   - Remediation roadmap

6. Recommendations
   - Priority actions
   - Strategic improvements

7. Evidence & Sources
   - Evidence inventory
   - Confidence ratings
   - Data gaps

8. Appendices
   - Methodology
   - Scoring criteria
   - Glossary
```

### Integration with HTML Template

```python
def generate_report(assessment_data):
    # Load TPSRCA HTML template
    template = load_template('tpsrca-html-template')
    
    # Populate sections
    template.set_executive_summary(assessment_data.composite_score)
    template.set_supplier_profile(assessment_data.classification)
    template.set_dashboard_kpis(assessment_data.kpis)
    template.set_framework_scores(assessment_data.framework_scores)
    template.set_risk_register(assessment_data.residual_risks)
    template.set_control_library(assessment_data.controls)
    template.set_gap_analysis(assessment_data.gaps)
    template.set_recommendations(assessment_data.recommendations)
    template.set_evidence_sources(assessment_data.evidence)
    
    # Generate file
    filename = f"TPSRCA_v8_{assessment_data.supplier_name}_{date}.html"
    template.save(filename)
    
    return filename
```

### Output Files

| File | Format | Purpose |
|------|--------|---------|
| TPSRCA Report | HTML | Executive presentation |
| Risk Register | XLSX | Editable risk tracking |
| Gap Tracker | XLSX | Remediation management |
| Evidence Pack | ZIP | Supporting documentation |
| Executive Brief | PPTX | Board presentation |

---

## Calculation Reference Card

### Quick Formulas

```
Inherent Risk = Likelihood × Impact (1-25)
Control Effectiveness = (Design×0.4) + (Operating×0.4) + (Coverage×0.2)
Residual Risk = Inherent × (1 - Control_Effectiveness%)
Framework Score = Σ(Control_Score × Weight) / Σ(Max_Score × Weight) × 100
Composite Score = (Framework×0.35) + (Controls×0.25) + (Risk×0.25) + (Confidence×0.15)
Data Confidence = (Authority×0.3) + (Freshness×0.25) + (Corroboration×0.25) + (Completeness×0.2)
```

### Rating Thresholds

| Metric | Critical | High | Medium | Low |
|--------|----------|------|--------|-----|
| **Risk Score** | 20-25 | 15-19 | 10-14 | 1-9 |
| **Framework %** | <50 | 50-69 | 70-79 | 80-100 |
| **Composite** | <60 | 60-69 | 70-79 | 80-100 |
| **Confidence** | <50 | 50-69 | 70-84 | 85-100 |
