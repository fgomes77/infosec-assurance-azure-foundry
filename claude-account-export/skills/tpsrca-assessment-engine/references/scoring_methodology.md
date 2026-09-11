# Scoring Methodology Reference

Comprehensive guide for framework compliance and composite score calculations.

## Framework Compliance Scoring

### General Formula

```
Framework_Score = (Σ Control_Weighted_Scores) / (Σ Max_Possible_Weighted_Scores) × 100

Where:
Control_Weighted_Score = Control_Score × Control_Weight × Applicability_Factor
Max_Possible_Weighted_Score = 100 × Control_Weight × Applicability_Factor
```

### Control Weights by Criticality

| Criticality | Weight | Rationale |
|-------------|--------|-----------|
| Critical | 3.0 | Regulatory mandate or severe impact |
| High | 2.0 | Significant compliance impact |
| Medium | 1.5 | Moderate compliance impact |
| Low | 1.0 | Minor compliance impact |

### Applicability Factor

| Applicability | Factor | Description |
|---------------|--------|-------------|
| Fully Applicable | 1.0 | Control applies to supplier |
| Partially Applicable | 0.5 | Control applies with limitations |
| Not Applicable | 0.0 | Control doesn't apply (excluded) |

---

## DORA Framework Scoring

### Article 28 Requirements Mapping

| Requirement | Article | Criticality | Weight | Max Score |
|-------------|---------|-------------|--------|-----------|
| Service description | 28(2)(a) | High | 2.0 | 200 |
| Locations (data/processing) | 28(2)(b) | Critical | 3.0 | 300 |
| Service levels | 28(2)(c) | High | 2.0 | 200 |
| Incident notification | 28(2)(d) | Critical | 3.0 | 300 |
| Subcontracting provisions | 28(2)(e) | High | 2.0 | 200 |
| Business continuity | 28(2)(f) | Critical | 3.0 | 300 |
| Data protection compliance | 28(2)(g) | High | 2.0 | 200 |
| Cooperation with authorities | 28(2)(h) | Medium | 1.5 | 150 |
| Audit rights | 28(2)(i) | Critical | 3.0 | 300 |
| Exit strategy | 28(2)(j) | Critical | 3.0 | 300 |
| **Total** | | | **24.5** | **2450** |

### DORA Score Calculation

```python
def calculate_dora_score(requirements):
    """
    Calculate DORA Article 28 compliance score.
    
    Args:
        requirements: List of dicts with 'id', 'score', 'weight'
    
    Returns:
        dict: DORA compliance metrics
    """
    total_weighted_score = 0
    total_max_score = 0
    
    article_scores = {}
    
    for req in requirements:
        weighted_score = req['score'] * req['weight']
        max_score = 100 * req['weight']
        
        total_weighted_score += weighted_score
        total_max_score += max_score
        
        article_scores[req['id']] = {
            'score': req['score'],
            'weighted': weighted_score,
            'max': max_score,
            'percentage': round(req['score'], 1)
        }
    
    overall_score = round(total_weighted_score / total_max_score * 100, 1)
    
    return {
        'overall_score': overall_score,
        'level': get_compliance_level(overall_score),
        'articles': article_scores,
        'gaps': [k for k, v in article_scores.items() if v['score'] < 70]
    }
```

---

## ISO 27001:2022 Scoring

### Annex A Control Categories

| Category | Controls | Weight | Max Score |
|----------|----------|--------|-----------|
| 5. Organizational (37) | 37 | 1.5 avg | 5550 |
| 6. People (8) | 8 | 1.5 avg | 1200 |
| 7. Physical (14) | 14 | 1.0 avg | 1400 |
| 8. Technological (34) | 34 | 2.0 avg | 6800 |
| **Total** | **93** | | **14950** |

### ISO 27001 Category Scoring

```python
def calculate_iso27001_score(controls):
    """
    Calculate ISO 27001 compliance score by category.
    
    Args:
        controls: Dict of category -> list of control scores
    
    Returns:
        dict: ISO 27001 compliance metrics
    """
    category_weights = {
        'organizational': 1.5,
        'people': 1.5,
        'physical': 1.0,
        'technological': 2.0
    }
    
    results = {}
    total_weighted = 0
    total_max = 0
    
    for category, control_scores in controls.items():
        weight = category_weights.get(category, 1.0)
        category_total = sum(control_scores) * weight
        category_max = len(control_scores) * 100 * weight
        
        results[category] = {
            'score': round(category_total / category_max * 100, 1),
            'controls_assessed': len(control_scores),
            'controls_compliant': len([c for c in control_scores if c >= 70])
        }
        
        total_weighted += category_total
        total_max += category_max
    
    overall = round(total_weighted / total_max * 100, 1)
    
    return {
        'overall_score': overall,
        'level': get_compliance_level(overall),
        'categories': results
    }
```

---

## NIST CSF 2.0 Scoring

### Function Weights

| Function | Weight | Categories | Rationale |
|----------|--------|------------|-----------|
| GOVERN | 15% | 6 | Foundation for all activities |
| IDENTIFY | 15% | 6 | Risk awareness baseline |
| PROTECT | 25% | 5 | Primary defense |
| DETECT | 15% | 2 | Continuous monitoring |
| RESPOND | 15% | 4 | Incident handling |
| RECOVER | 15% | 3 | Resilience |

### NIST CSF Scoring

```python
def calculate_nist_score(functions):
    """
    Calculate NIST CSF 2.0 compliance score.
    
    Args:
        functions: Dict of function -> score (0-100)
    
    Returns:
        dict: NIST CSF compliance metrics
    """
    weights = {
        'govern': 0.15,
        'identify': 0.15,
        'protect': 0.25,
        'detect': 0.15,
        'respond': 0.15,
        'recover': 0.15
    }
    
    weighted_total = 0
    function_results = {}
    
    for func, score in functions.items():
        weight = weights.get(func.lower(), 0)
        weighted_score = score * weight
        weighted_total += weighted_score
        
        function_results[func] = {
            'score': score,
            'weight': weight,
            'weighted': round(weighted_score, 1),
            'level': get_compliance_level(score)
        }
    
    overall = round(weighted_total, 1)
    
    return {
        'overall_score': overall,
        'level': get_compliance_level(overall),
        'functions': function_results
    }
```

---

## GDPR Scoring

### Key Requirements

| Requirement | Article | Criticality | Weight |
|-------------|---------|-------------|--------|
| Lawful basis | 6 | Critical | 3.0 |
| Data subject rights | 12-22 | Critical | 3.0 |
| Security of processing | 32 | Critical | 3.0 |
| Data protection by design | 25 | High | 2.0 |
| Records of processing | 30 | High | 2.0 |
| DPO appointment | 37-39 | Medium | 1.5 |
| DPIA | 35 | High | 2.0 |
| Breach notification | 33-34 | Critical | 3.0 |
| International transfers | 44-49 | Critical | 3.0 |
| Processor requirements | 28 | Critical | 3.0 |

### GDPR Score Calculation

```python
def calculate_gdpr_score(requirements):
    """
    Calculate GDPR compliance score.
    
    Args:
        requirements: Dict of requirement -> score
    
    Returns:
        dict: GDPR compliance metrics
    """
    weights = {
        'lawful_basis': 3.0,
        'data_subject_rights': 3.0,
        'security': 3.0,
        'privacy_by_design': 2.0,
        'records': 2.0,
        'dpo': 1.5,
        'dpia': 2.0,
        'breach_notification': 3.0,
        'international_transfers': 3.0,
        'processor_requirements': 3.0
    }
    
    total_weighted = 0
    total_max = 0
    
    for req, score in requirements.items():
        weight = weights.get(req, 1.0)
        total_weighted += score * weight
        total_max += 100 * weight
    
    overall = round(total_weighted / total_max * 100, 1)
    
    return {
        'overall_score': overall,
        'level': get_compliance_level(overall)
    }
```

---

## EU AI Act Scoring

### Risk-Based Requirements

| Requirement | Risk Level | Criticality | Weight |
|-------------|------------|-------------|--------|
| AI system registration | High | Critical | 3.0 |
| Risk management system | High | Critical | 3.0 |
| Data governance | High | Critical | 3.0 |
| Technical documentation | High | High | 2.0 |
| Record-keeping | High | High | 2.0 |
| Transparency | High/Limited | Critical | 3.0 |
| Human oversight | High | Critical | 3.0 |
| Accuracy & robustness | High | High | 2.0 |
| Cybersecurity | High | High | 2.0 |
| Post-market monitoring | High | Medium | 1.5 |

### EU AI Act Score Calculation

```python
def calculate_euai_score(requirements, ai_systems):
    """
    Calculate EU AI Act compliance score.
    
    Args:
        requirements: Dict of requirement -> score
        ai_systems: List of AI system classifications
    
    Returns:
        dict: EU AI Act compliance metrics
    """
    # Determine applicable requirements based on risk level
    high_risk_count = len([s for s in ai_systems if s['risk_level'] == 'High'])
    limited_risk_count = len([s for s in ai_systems if s['risk_level'] == 'Limited'])
    
    if high_risk_count > 0:
        # All requirements apply
        applicable_weights = {
            'registration': 3.0,
            'risk_management': 3.0,
            'data_governance': 3.0,
            'documentation': 2.0,
            'record_keeping': 2.0,
            'transparency': 3.0,
            'human_oversight': 3.0,
            'accuracy': 2.0,
            'cybersecurity': 2.0,
            'monitoring': 1.5
        }
    elif limited_risk_count > 0:
        # Only transparency applies
        applicable_weights = {
            'transparency': 3.0
        }
    else:
        # Minimal risk - no specific requirements
        return {
            'overall_score': 100,
            'level': 'Excellent',
            'note': 'No EU AI Act requirements apply to minimal risk systems'
        }
    
    total_weighted = 0
    total_max = 0
    
    for req, weight in applicable_weights.items():
        score = requirements.get(req, 0)
        total_weighted += score * weight
        total_max += 100 * weight
    
    overall = round(total_weighted / total_max * 100, 1) if total_max > 0 else 0
    
    return {
        'overall_score': overall,
        'level': get_compliance_level(overall),
        'applicable_requirements': list(applicable_weights.keys()),
        'high_risk_systems': high_risk_count,
        'limited_risk_systems': limited_risk_count
    }
```

---

## ISO 42001 Scoring

### Clause Requirements

| Clause | Requirement | Criticality | Weight |
|--------|-------------|-------------|--------|
| 4 | Context of organization | High | 2.0 |
| 5 | Leadership | High | 2.0 |
| 6 | Planning | Critical | 3.0 |
| 7 | Support | Medium | 1.5 |
| 8 | Operation | Critical | 3.0 |
| 9 | Performance evaluation | High | 2.0 |
| 10 | Improvement | Medium | 1.5 |
| A | AI-specific controls | Critical | 3.0 |

---

## Composite Score Calculation

### Component Weights

| Component | Weight | Source |
|-----------|--------|--------|
| Framework Compliance | 35% | Agent 7 output |
| Control Effectiveness | 25% | Agent 5 output |
| Residual Risk Score | 25% | Agent 6 output |
| Data Confidence | 15% | Agent 2 output |

### Framework Weight by Tier

**Tier A (Critical ICT):**
| Framework | Weight |
|-----------|--------|
| DORA | 25% |
| ISO 27001 | 20% |
| GDPR | 15% |
| NIST CSF | 15% |
| NIS2 | 10% |
| EU AI Act | 10% |
| Other | 5% |

**Tier B (Important ICT):**
| Framework | Weight |
|-----------|--------|
| DORA | 20% |
| ISO 27001 | 25% |
| GDPR | 20% |
| NIST CSF | 15% |
| NIS2 | 10% |
| EU AI Act | 5% |
| Other | 5% |

**Tier C (Standard ICT):**
| Framework | Weight |
|-----------|--------|
| ISO 27001 | 30% |
| GDPR | 25% |
| NIST CSF | 20% |
| DORA | 15% |
| NIS2 | 5% |
| Other | 5% |

### Composite Score Formula

```python
def calculate_composite_score(framework_scores, control_effectiveness, 
                              residual_risk_normalized, data_confidence, tier):
    """
    Calculate overall composite supplier score.
    
    Args:
        framework_scores: Dict of framework -> score
        control_effectiveness: Overall control effectiveness (0-100)
        residual_risk_normalized: Normalized residual risk (0-100, higher=better)
        data_confidence: Data confidence score (0-100)
        tier: Supplier tier ('A', 'B', 'C')
    
    Returns:
        dict: Composite score and rating
    """
    # Get framework weights based on tier
    framework_weights = get_framework_weights(tier)
    
    # Calculate weighted framework score
    weighted_framework = 0
    for framework, score in framework_scores.items():
        weight = framework_weights.get(framework.lower(), 0)
        weighted_framework += score * weight
    
    # Calculate composite
    composite = (
        weighted_framework * 0.35 +
        control_effectiveness * 0.25 +
        residual_risk_normalized * 0.25 +
        data_confidence * 0.15
    )
    
    # Determine rating
    if composite >= 90:
        rating = "L1 - Exemplary"
        stars = 5
        approval = "Full Approval"
    elif composite >= 80:
        rating = "L2 - Strong"
        stars = 4
        approval = "Approved"
    elif composite >= 70:
        rating = "L3 - Adequate"
        stars = 3
        approval = "Conditional Approval"
    elif composite >= 60:
        rating = "L4 - Weak"
        stars = 2
        approval = "Remediation Required"
    else:
        rating = "L5 - Unacceptable"
        stars = 1
        approval = "Not Approved"
    
    return {
        'composite_score': round(composite, 1),
        'rating': rating,
        'stars': stars,
        'approval_status': approval,
        'components': {
            'framework': round(weighted_framework, 1),
            'controls': control_effectiveness,
            'risk': residual_risk_normalized,
            'confidence': data_confidence
        }
    }
```

### Risk Score Normalization

```python
def normalize_risk_score(residual_risks):
    """
    Convert residual risk exposure to a 0-100 score where higher is better.
    
    Args:
        residual_risks: List of residual risk scores
    
    Returns:
        float: Normalized risk score (0-100)
    """
    total_exposure = sum(residual_risks)
    max_possible = len(residual_risks) * 25  # Maximum risk score per item
    
    # Invert so higher score = lower risk
    normalized = 100 - (total_exposure / max_possible * 100)
    
    return round(normalized, 1)
```

---

## Compliance Level Thresholds

### Standard Thresholds

```python
def get_compliance_level(score):
    """
    Get compliance level description for a score.
    
    Args:
        score: Compliance score (0-100)
    
    Returns:
        str: Compliance level
    """
    if score >= 90:
        return "Excellent"
    elif score >= 80:
        return "Good"
    elif score >= 70:
        return "Satisfactory"
    elif score >= 60:
        return "Needs Improvement"
    elif score >= 50:
        return "Concerning"
    else:
        return "Critical"
```

### Visual Indicators

| Score | Level | Bar | Color |
|-------|-------|-----|-------|
| 90-100 | Excellent | ████████████ | 🟢 Green |
| 80-89 | Good | █████████░░░ | 🟢 Green |
| 70-79 | Satisfactory | ████████░░░░ | 🟡 Yellow |
| 60-69 | Needs Improvement | ██████░░░░░░ | 🟠 Orange |
| 50-59 | Concerning | █████░░░░░░░ | 🟠 Orange |
| <50 | Critical | ████░░░░░░░░ | 🔴 Red |

---

## Score Interpretation Guide

### Framework Scores

| Score | Interpretation | Action |
|-------|----------------|--------|
| 90%+ | Full compliance, minor improvements only | Maintain |
| 80-89% | Strong compliance, some gaps | Address gaps |
| 70-79% | Basic compliance, multiple gaps | Remediation plan |
| 60-69% | Partial compliance, significant gaps | Priority remediation |
| <60% | Non-compliant, fundamental issues | Major intervention |

### Composite Scores

| Score | Rating | Risk Profile | Contract Recommendation |
|-------|--------|--------------|------------------------|
| 90%+ | L1 | Very Low | Standard terms |
| 80-89% | L2 | Low | Standard terms + monitoring |
| 70-79% | L3 | Medium | Enhanced terms + conditions |
| 60-69% | L4 | High | Strict terms + remediation |
| <60% | L5 | Very High | Do not contract |

### Score Delta Interpretation

| Delta | Trend | Interpretation |
|-------|-------|----------------|
| >+10% | ↑↑ Strong Improvement | Significant progress |
| +5-10% | ↑ Improvement | Positive trend |
| -5 to +5% | → Stable | Maintained position |
| -5-10% | ↓ Decline | Attention needed |
| <-10% | ↓↓ Strong Decline | Immediate attention |
