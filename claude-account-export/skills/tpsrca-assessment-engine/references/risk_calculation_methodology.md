# Risk Calculation Methodology Reference

Comprehensive guide for inherent, control, and residual risk calculations.

## Risk Assessment Framework

### The Risk Equation

```
Risk = f(Threat, Vulnerability, Impact)

Simplified:
Inherent Risk = Likelihood × Impact
Residual Risk = Inherent Risk × (1 - Control Effectiveness)
```

---

## Likelihood Assessment

### Quantitative Likelihood Scale

| Score | Level | Annual Probability | Frequency | Historical |
|-------|-------|-------------------|-----------|------------|
| 5 | Almost Certain | >90% | Multiple/year | Has occurred repeatedly |
| 4 | Likely | 60-90% | Once/year | Has occurred recently |
| 3 | Possible | 30-60% | Once/2-3 years | Could occur |
| 2 | Unlikely | 10-30% | Once/5 years | Remote possibility |
| 1 | Rare | <10% | Once/10+ years | Highly unlikely |

### Likelihood Factors

**Threat-Based Factors:**
- Threat actor capability (1-5)
- Threat actor motivation (1-5)
- Attack vector availability (1-5)
- Historical attack frequency (1-5)

**Vulnerability-Based Factors:**
- Exposure level (1-5)
- Control gaps (1-5)
- Configuration weaknesses (1-5)
- Patch status (1-5)

**Likelihood Calculation:**
```
Likelihood = (Threat_Avg + Vulnerability_Avg) / 2
Round to nearest integer (1-5)
```

---

## Impact Assessment

### Impact Dimensions

| Dimension | Weight | Description |
|-----------|--------|-------------|
| Financial | 30% | Direct costs, fines, remediation |
| Operational | 25% | Business disruption, productivity |
| Reputational | 20% | Brand damage, customer trust |
| Regulatory | 15% | Compliance penalties, restrictions |
| Strategic | 10% | Long-term competitive position |

### Financial Impact Scale

| Score | Level | Range | Examples |
|-------|-------|-------|----------|
| 5 | Catastrophic | >€10M | Major breach, class action |
| 4 | Major | €1-10M | Significant breach, regulatory fine |
| 3 | Moderate | €100K-1M | Limited breach, remediation costs |
| 2 | Minor | €10-100K | Incident response costs |
| 1 | Negligible | <€10K | Minimal direct costs |

### Operational Impact Scale

| Score | Level | Duration | Scope |
|-------|-------|----------|-------|
| 5 | Catastrophic | >1 week | Enterprise-wide failure |
| 4 | Major | 1-7 days | Multiple critical systems |
| 3 | Moderate | 4-24 hours | Single critical system |
| 2 | Minor | 1-4 hours | Non-critical systems |
| 1 | Negligible | <1 hour | Minimal disruption |

### Reputational Impact Scale

| Score | Level | Media | Customer Impact |
|-------|-------|-------|-----------------|
| 5 | Catastrophic | National/international news | Mass customer exodus |
| 4 | Major | Industry press, social media viral | Significant churn |
| 3 | Moderate | Local press, social media | Some customer complaints |
| 2 | Minor | Industry forums | Individual complaints |
| 1 | Negligible | Internal only | No external awareness |

### Regulatory Impact Scale

| Score | Level | Consequence | Examples |
|-------|-------|-------------|----------|
| 5 | Catastrophic | License revocation | Operating ban |
| 4 | Major | Major fine, restrictions | GDPR max penalty |
| 3 | Moderate | Significant fine | Regulatory order |
| 2 | Minor | Warning, minor fine | Compliance notice |
| 1 | Negligible | No action | Observation |

### Composite Impact Calculation

```
Impact = (Financial × 0.30) + (Operational × 0.25) + (Reputational × 0.20) + 
         (Regulatory × 0.15) + (Strategic × 0.10)

Round to nearest integer (1-5)
```

---

## Inherent Risk Calculation

### Risk Matrix

```
                    IMPACT
            1     2     3     4     5
         ┌─────┬─────┬─────┬─────┬─────┐
       5 │  5  │ 10  │ 15  │ 20  │ 25  │
         ├─────┼─────┼─────┼─────┼─────┤
       4 │  4  │  8  │ 12  │ 16  │ 20  │
L        ├─────┼─────┼─────┼─────┼─────┤
I      3 │  3  │  6  │  9  │ 12  │ 15  │
K        ├─────┼─────┼─────┼─────┼─────┤
E      2 │  2  │  4  │  6  │  8  │ 10  │
L        ├─────┼─────┼─────┼─────┼─────┤
I      1 │  1  │  2  │  3  │  4  │  5  │
H        └─────┴─────┴─────┴─────┴─────┘
O
O
D
```

### Risk Rating Thresholds

| Score Range | Rating | Color | Priority |
|-------------|--------|-------|----------|
| 20-25 | Critical | 🔴 Red | Immediate |
| 15-19 | High | 🟠 Orange | Urgent |
| 10-14 | Medium | 🟡 Yellow | Planned |
| 5-9 | Low | 🟢 Green | Monitor |
| 1-4 | Very Low | 🔵 Blue | Accept |

### Inherent Risk Score Formula

```python
def calculate_inherent_risk(likelihood, impact):
    """
    Calculate inherent risk score.
    
    Args:
        likelihood: Integer 1-5
        impact: Integer 1-5
    
    Returns:
        tuple: (score, rating, color)
    """
    score = likelihood * impact
    
    if score >= 20:
        return (score, "Critical", "red")
    elif score >= 15:
        return (score, "High", "orange")
    elif score >= 10:
        return (score, "Medium", "yellow")
    elif score >= 5:
        return (score, "Low", "green")
    else:
        return (score, "Very Low", "blue")
```

---

## Control Effectiveness Assessment

### Control Types

| Type | Effect | Example |
|------|--------|---------|
| **Preventive** | Reduces likelihood | Access controls, encryption |
| **Detective** | Enables response | Logging, monitoring, SIEM |
| **Corrective** | Reduces impact | Backup, incident response |
| **Compensating** | Partial mitigation | Alternative controls |

### Control Assessment Criteria

**Design Effectiveness (40%)**

| Score | Level | Criteria |
|-------|-------|----------|
| 100 | Excellent | Control addresses risk completely |
| 80 | Good | Control addresses most of risk |
| 60 | Adequate | Control addresses some risk |
| 40 | Weak | Control addresses limited risk |
| 20 | Poor | Control barely addresses risk |
| 0 | None | No relevant control |

**Operating Effectiveness (40%)**

| Score | Level | Criteria |
|-------|-------|----------|
| 100 | Excellent | Operates consistently, tested regularly |
| 80 | Good | Operates well, some testing |
| 60 | Adequate | Generally operates, limited testing |
| 40 | Weak | Inconsistent operation |
| 20 | Poor | Rarely operates correctly |
| 0 | None | Not operating |

**Coverage (20%)**

| Score | Level | Criteria |
|-------|-------|----------|
| 100 | Complete | Covers all instances |
| 80 | Substantial | Covers most instances |
| 60 | Partial | Covers some instances |
| 40 | Limited | Covers few instances |
| 20 | Minimal | Barely any coverage |
| 0 | None | No coverage |

### Control Effectiveness Formula

```python
def calculate_control_effectiveness(design, operating, coverage):
    """
    Calculate overall control effectiveness.
    
    Args:
        design: Integer 0-100 (design effectiveness)
        operating: Integer 0-100 (operating effectiveness)
        coverage: Integer 0-100 (coverage percentage)
    
    Returns:
        tuple: (score, rating)
    """
    score = (design * 0.40) + (operating * 0.40) + (coverage * 0.20)
    
    if score >= 90:
        return (score, "Excellent")
    elif score >= 70:
        return (score, "Good")
    elif score >= 50:
        return (score, "Adequate")
    elif score >= 30:
        return (score, "Weak")
    else:
        return (score, "Ineffective")
```

### Control Implementation Status

| Status | Score | Risk Reduction |
|--------|-------|----------------|
| Implemented | 100% | Full effect |
| Partial | 60% | Reduced effect |
| Planned | 30% | Minimal effect |
| Gap | 0% | No effect |

---

## Residual Risk Calculation

### Method 1: Direct Reduction

```
Residual_Risk = Inherent_Risk × (1 - Control_Effectiveness/100)

Example:
Inherent Risk = 15 (L=3 × I=5)
Control Effectiveness = 70%
Residual Risk = 15 × (1 - 0.70) = 15 × 0.30 = 4.5 ≈ 5
```

### Method 2: Component Reduction

```
Residual_Likelihood = Inherent_Likelihood - Likelihood_Reduction
Residual_Impact = Inherent_Impact - Impact_Reduction
Residual_Risk = Residual_Likelihood × Residual_Impact

Where:
- Preventive controls reduce Likelihood
- Corrective controls reduce Impact
- Detective controls reduce both (partial)
```

### Control Effect Matrix

| Effectiveness | Likelihood Reduction | Impact Reduction |
|---------------|---------------------|------------------|
| Excellent (90%+) | -2.0 | -2.0 |
| Good (70-89%) | -1.5 | -1.5 |
| Adequate (50-69%) | -1.0 | -1.0 |
| Weak (30-49%) | -0.5 | -0.5 |
| Ineffective (<30%) | 0 | 0 |

### Residual Risk Formula

```python
def calculate_residual_risk(inherent_likelihood, inherent_impact, 
                           control_effectiveness, control_type):
    """
    Calculate residual risk using component reduction method.
    
    Args:
        inherent_likelihood: Integer 1-5
        inherent_impact: Integer 1-5
        control_effectiveness: Integer 0-100
        control_type: 'preventive', 'detective', 'corrective', 'compensating'
    
    Returns:
        dict: Residual risk details
    """
    # Determine reduction factor
    if control_effectiveness >= 90:
        reduction = 2.0
    elif control_effectiveness >= 70:
        reduction = 1.5
    elif control_effectiveness >= 50:
        reduction = 1.0
    elif control_effectiveness >= 30:
        reduction = 0.5
    else:
        reduction = 0
    
    # Apply based on control type
    if control_type == 'preventive':
        likelihood_reduction = reduction
        impact_reduction = 0
    elif control_type == 'corrective':
        likelihood_reduction = 0
        impact_reduction = reduction
    elif control_type == 'detective':
        likelihood_reduction = reduction * 0.5
        impact_reduction = reduction * 0.5
    else:  # compensating
        likelihood_reduction = reduction * 0.5
        impact_reduction = reduction * 0.5
    
    # Calculate residual values (minimum 1)
    residual_likelihood = max(1, inherent_likelihood - likelihood_reduction)
    residual_impact = max(1, inherent_impact - impact_reduction)
    residual_score = residual_likelihood * residual_impact
    
    # Determine rating
    if residual_score >= 20:
        rating = "Critical"
    elif residual_score >= 15:
        rating = "High"
    elif residual_score >= 10:
        rating = "Medium"
    elif residual_score >= 5:
        rating = "Low"
    else:
        rating = "Very Low"
    
    return {
        'inherent_score': inherent_likelihood * inherent_impact,
        'residual_likelihood': round(residual_likelihood, 1),
        'residual_impact': round(residual_impact, 1),
        'residual_score': round(residual_score, 1),
        'residual_rating': rating,
        'risk_reduction_percent': round((1 - residual_score/(inherent_likelihood * inherent_impact)) * 100, 1)
    }
```

---

## Aggregated Risk Metrics

### Total Risk Exposure

```
Total_Inherent_Exposure = Σ(Inherent_Risk_Scores)
Total_Residual_Exposure = Σ(Residual_Risk_Scores)
Overall_Risk_Reduction = (1 - Total_Residual / Total_Inherent) × 100
```

### Risk Distribution Metrics

```python
def calculate_risk_distribution(risks):
    """
    Calculate risk distribution metrics.
    
    Args:
        risks: List of risk dictionaries with 'residual_score' and 'residual_rating'
    
    Returns:
        dict: Distribution metrics
    """
    distribution = {
        'critical': len([r for r in risks if r['residual_rating'] == 'Critical']),
        'high': len([r for r in risks if r['residual_rating'] == 'High']),
        'medium': len([r for r in risks if r['residual_rating'] == 'Medium']),
        'low': len([r for r in risks if r['residual_rating'] == 'Low']),
        'very_low': len([r for r in risks if r['residual_rating'] == 'Very Low'])
    }
    
    total = len(risks)
    
    return {
        'distribution': distribution,
        'percentages': {k: round(v/total*100, 1) for k, v in distribution.items()},
        'total_risks': total,
        'total_exposure': sum(r['residual_score'] for r in risks),
        'average_score': round(sum(r['residual_score'] for r in risks) / total, 1)
    }
```

### Risk Score for Composite Calculation

```
Risk_Score_Normalized = 100 - (Total_Residual_Exposure / Max_Possible_Exposure × 100)

Where:
Max_Possible_Exposure = Number_of_Risks × 25 (maximum single risk score)
```

---

## Risk Treatment Thresholds

### Risk Appetite Levels

| Level | Threshold | Treatment |
|-------|-----------|-----------|
| **Unacceptable** | Any Critical | Must remediate |
| **Above Tolerance** | >2 High | Remediate within 90 days |
| **Within Tolerance** | ≤2 High, ≤5 Medium | Monitor |
| **Acceptable** | All Low/Very Low | Accept |

### Treatment Decision Matrix

| Residual Risk | Risk Appetite | Decision | Timeline |
|---------------|---------------|----------|----------|
| Critical | Any | Remediate | Immediate |
| High | Conservative | Remediate | 30 days |
| High | Moderate | Accept with plan | 90 days |
| Medium | Any | Monitor | Quarterly |
| Low | Any | Accept | Annual review |

### Cost-Benefit Analysis

```
Remediation_Priority = Risk_Reduction_Value / Remediation_Cost

Where:
Risk_Reduction_Value = (Inherent_Risk - Residual_Risk) × Annual_Loss_Expectancy
Remediation_Cost = Implementation_Cost + Ongoing_Cost × Years

Higher ratio = Higher priority
```

---

## Worked Example

### Scenario: Data Breach Risk

**Step 1: Assess Inherent Risk**
```
Threat: External attacker targeting customer data
Vulnerability: Inadequate access controls

Likelihood factors:
- Threat capability: 4
- Threat motivation: 5
- Attack vector: 3
- Historical frequency: 3
Average: 3.75 → Round to 4 (Likely)

Impact factors:
- Financial: 4 (€1-10M potential fine)
- Operational: 3 (System lockdown required)
- Reputational: 4 (Media coverage likely)
- Regulatory: 4 (GDPR implications)
- Strategic: 3 (Customer trust impact)
Weighted: (4×0.3)+(3×0.25)+(4×0.2)+(4×0.15)+(3×0.1) = 3.75 → Round to 4 (Major)

Inherent Risk = 4 × 4 = 16 (HIGH)
```

**Step 2: Assess Control Effectiveness**
```
Controls in place:
- MFA (Preventive): Design=90, Operating=85, Coverage=80
- SIEM (Detective): Design=80, Operating=75, Coverage=90
- Encryption (Preventive): Design=95, Operating=90, Coverage=85
- Incident Response (Corrective): Design=70, Operating=60, Coverage=70

MFA Effectiveness = (90×0.4)+(85×0.4)+(80×0.2) = 86%
SIEM Effectiveness = (80×0.4)+(75×0.4)+(90×0.2) = 80%
Encryption Effectiveness = (95×0.4)+(90×0.4)+(85×0.2) = 91%
IR Effectiveness = (70×0.4)+(60×0.4)+(70×0.2) = 66%

Combined Control Effectiveness = Average = 80.75% → 81% (Good)
```

**Step 3: Calculate Residual Risk**
```
Method 1 (Direct):
Residual = 16 × (1 - 0.81) = 16 × 0.19 = 3.04 ≈ 3 (LOW)

Method 2 (Component):
Reduction factor for 81% = 1.5
Preventive controls → Likelihood: 4 - 1.5 = 2.5 → 2
Corrective controls → Impact: 4 - 0.5 = 3.5 → 4
Residual = 2 × 4 = 8 (LOW)

Final: Average = (3 + 8) / 2 = 5.5 ≈ 6 (LOW)
```

**Step 4: Treatment Decision**
```
Inherent Risk: 16 (HIGH)
Residual Risk: 6 (LOW)
Risk Reduction: 62.5%

Treatment: Accept and Monitor
Review: Annual assessment
```
