#!/usr/bin/env python3
"""
TPSRCA Assessment Engine - Calculation Module
Implements all risk, control, and compliance calculations.
"""

import json
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum
from datetime import datetime

# ============================================================================
# ENUMS AND CONSTANTS
# ============================================================================

class RiskRating(Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    VERY_LOW = "Very Low"

class ComplianceLevel(Enum):
    EXCELLENT = "Excellent"
    GOOD = "Good"
    SATISFACTORY = "Satisfactory"
    NEEDS_IMPROVEMENT = "Needs Improvement"
    CONCERNING = "Concerning"
    CRITICAL = "Critical"

class SupplierRating(Enum):
    L1_EXEMPLARY = "L1 - Exemplary"
    L2_STRONG = "L2 - Strong"
    L3_ADEQUATE = "L3 - Adequate"
    L4_WEAK = "L4 - Weak"
    L5_UNACCEPTABLE = "L5 - Unacceptable"

class ControlStatus(Enum):
    IMPLEMENTED = "Implemented"
    PARTIAL = "Partial"
    PLANNED = "Planned"
    GAP = "Gap"

class ControlType(Enum):
    PREVENTIVE = "Preventive"
    DETECTIVE = "Detective"
    CORRECTIVE = "Corrective"
    COMPENSATING = "Compensating"

# Weight constants
FRAMEWORK_WEIGHTS_TIER_A = {
    'dora': 0.25, 'iso_27001': 0.20, 'gdpr': 0.15,
    'nist': 0.15, 'nis2': 0.10, 'eu_ai_act': 0.10, 'other': 0.05
}

FRAMEWORK_WEIGHTS_TIER_B = {
    'dora': 0.20, 'iso_27001': 0.25, 'gdpr': 0.20,
    'nist': 0.15, 'nis2': 0.10, 'eu_ai_act': 0.05, 'other': 0.05
}

FRAMEWORK_WEIGHTS_TIER_C = {
    'iso_27001': 0.30, 'gdpr': 0.25, 'nist': 0.20,
    'dora': 0.15, 'nis2': 0.05, 'other': 0.05
}

# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class InherentRisk:
    id: str
    category: str
    description: str
    likelihood: int  # 1-5
    impact: int  # 1-5
    score: int = field(init=False)
    rating: RiskRating = field(init=False)
    
    def __post_init__(self):
        self.score = self.likelihood * self.impact
        self.rating = self._calculate_rating()
    
    def _calculate_rating(self) -> RiskRating:
        if self.score >= 20:
            return RiskRating.CRITICAL
        elif self.score >= 15:
            return RiskRating.HIGH
        elif self.score >= 10:
            return RiskRating.MEDIUM
        elif self.score >= 5:
            return RiskRating.LOW
        else:
            return RiskRating.VERY_LOW

@dataclass
class Control:
    id: str
    name: str
    domain: str
    control_type: ControlType
    design_effectiveness: int  # 0-100
    operating_effectiveness: int  # 0-100
    coverage: int  # 0-100
    status: ControlStatus
    effectiveness: float = field(init=False)
    
    def __post_init__(self):
        self.effectiveness = self._calculate_effectiveness()
    
    def _calculate_effectiveness(self) -> float:
        base = (
            self.design_effectiveness * 0.40 +
            self.operating_effectiveness * 0.40 +
            self.coverage * 0.20
        )
        # Apply status modifier
        status_modifier = {
            ControlStatus.IMPLEMENTED: 1.0,
            ControlStatus.PARTIAL: 0.6,
            ControlStatus.PLANNED: 0.3,
            ControlStatus.GAP: 0.0
        }
        return base * status_modifier.get(self.status, 1.0)

@dataclass
class ResidualRisk:
    inherent_risk: InherentRisk
    controls: List[Control]
    residual_likelihood: float = field(init=False)
    residual_impact: float = field(init=False)
    residual_score: float = field(init=False)
    residual_rating: RiskRating = field(init=False)
    risk_reduction_percent: float = field(init=False)
    
    def __post_init__(self):
        self._calculate_residual()
    
    def _calculate_residual(self):
        if not self.controls:
            self.residual_likelihood = self.inherent_risk.likelihood
            self.residual_impact = self.inherent_risk.impact
        else:
            # Calculate combined control effectiveness
            avg_effectiveness = sum(c.effectiveness for c in self.controls) / len(self.controls)
            
            # Determine reduction factor
            reduction = self._get_reduction_factor(avg_effectiveness)
            
            # Calculate reductions based on control types
            preventive = [c for c in self.controls if c.control_type == ControlType.PREVENTIVE]
            corrective = [c for c in self.controls if c.control_type == ControlType.CORRECTIVE]
            detective = [c for c in self.controls if c.control_type == ControlType.DETECTIVE]
            
            likelihood_reduction = 0
            impact_reduction = 0
            
            if preventive:
                likelihood_reduction += reduction * 0.7
            if detective:
                likelihood_reduction += reduction * 0.3
                impact_reduction += reduction * 0.3
            if corrective:
                impact_reduction += reduction * 0.7
            
            self.residual_likelihood = max(1, self.inherent_risk.likelihood - likelihood_reduction)
            self.residual_impact = max(1, self.inherent_risk.impact - impact_reduction)
        
        self.residual_score = round(self.residual_likelihood * self.residual_impact, 1)
        self.residual_rating = self._calculate_rating()
        self.risk_reduction_percent = round(
            (1 - self.residual_score / self.inherent_risk.score) * 100, 1
        )
    
    def _get_reduction_factor(self, effectiveness: float) -> float:
        if effectiveness >= 90:
            return 2.0
        elif effectiveness >= 70:
            return 1.5
        elif effectiveness >= 50:
            return 1.0
        elif effectiveness >= 30:
            return 0.5
        else:
            return 0
    
    def _calculate_rating(self) -> RiskRating:
        score = self.residual_score
        if score >= 20:
            return RiskRating.CRITICAL
        elif score >= 15:
            return RiskRating.HIGH
        elif score >= 10:
            return RiskRating.MEDIUM
        elif score >= 5:
            return RiskRating.LOW
        else:
            return RiskRating.VERY_LOW

# ============================================================================
# CALCULATION FUNCTIONS
# ============================================================================

def calculate_inherent_risk(likelihood: int, impact: int) -> Dict:
    """Calculate inherent risk score and rating."""
    score = likelihood * impact
    
    if score >= 20:
        rating = "Critical"
        color = "red"
    elif score >= 15:
        rating = "High"
        color = "orange"
    elif score >= 10:
        rating = "Medium"
        color = "yellow"
    elif score >= 5:
        rating = "Low"
        color = "green"
    else:
        rating = "Very Low"
        color = "blue"
    
    return {
        'likelihood': likelihood,
        'impact': impact,
        'score': score,
        'rating': rating,
        'color': color
    }

def calculate_control_effectiveness(design: int, operating: int, coverage: int,
                                    status: str = "Implemented") -> Dict:
    """Calculate control effectiveness score."""
    base_score = (design * 0.40) + (operating * 0.40) + (coverage * 0.20)
    
    # Apply status modifier
    status_modifiers = {
        "Implemented": 1.0,
        "Partial": 0.6,
        "Planned": 0.3,
        "Gap": 0.0
    }
    modifier = status_modifiers.get(status, 1.0)
    final_score = base_score * modifier
    
    # Determine rating
    if final_score >= 90:
        rating = "Excellent"
    elif final_score >= 70:
        rating = "Good"
    elif final_score >= 50:
        rating = "Adequate"
    elif final_score >= 30:
        rating = "Weak"
    else:
        rating = "Ineffective"
    
    return {
        'design': design,
        'operating': operating,
        'coverage': coverage,
        'status': status,
        'base_score': round(base_score, 1),
        'final_score': round(final_score, 1),
        'rating': rating
    }

def calculate_residual_risk(inherent_likelihood: int, inherent_impact: int,
                           control_effectiveness: float, 
                           control_type: str = "Compensating") -> Dict:
    """Calculate residual risk after controls."""
    inherent_score = inherent_likelihood * inherent_impact
    
    # Determine reduction factor based on effectiveness
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
    
    # Apply reduction based on control type
    type_effects = {
        "Preventive": (reduction * 0.8, reduction * 0.2),
        "Detective": (reduction * 0.4, reduction * 0.4),
        "Corrective": (reduction * 0.2, reduction * 0.8),
        "Compensating": (reduction * 0.5, reduction * 0.5)
    }
    
    likelihood_reduction, impact_reduction = type_effects.get(control_type, (reduction * 0.5, reduction * 0.5))
    
    residual_likelihood = max(1, inherent_likelihood - likelihood_reduction)
    residual_impact = max(1, inherent_impact - impact_reduction)
    residual_score = residual_likelihood * residual_impact
    
    # Rating
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
    
    risk_reduction = round((1 - residual_score / inherent_score) * 100, 1)
    
    return {
        'inherent': {
            'likelihood': inherent_likelihood,
            'impact': inherent_impact,
            'score': inherent_score
        },
        'residual': {
            'likelihood': round(residual_likelihood, 1),
            'impact': round(residual_impact, 1),
            'score': round(residual_score, 1),
            'rating': rating
        },
        'risk_reduction_percent': risk_reduction,
        'control_effectiveness': control_effectiveness,
        'control_type': control_type
    }

def calculate_framework_score(controls: List[Dict], weights: Dict = None) -> Dict:
    """Calculate framework compliance score."""
    if not controls:
        return {'overall_score': 0, 'level': 'Critical'}
    
    total_weighted = 0
    total_max = 0
    
    for control in controls:
        score = control.get('score', 0)
        weight = control.get('weight', 1.0)
        
        if weights and control.get('id') in weights:
            weight = weights[control['id']]
        
        total_weighted += score * weight
        total_max += 100 * weight
    
    overall = round(total_weighted / total_max * 100, 1) if total_max > 0 else 0
    
    # Determine level
    if overall >= 90:
        level = "Excellent"
    elif overall >= 80:
        level = "Good"
    elif overall >= 70:
        level = "Satisfactory"
    elif overall >= 60:
        level = "Needs Improvement"
    elif overall >= 50:
        level = "Concerning"
    else:
        level = "Critical"
    
    return {
        'overall_score': overall,
        'level': level,
        'controls_assessed': len(controls),
        'controls_compliant': len([c for c in controls if c.get('score', 0) >= 70])
    }

def calculate_composite_score(framework_scores: Dict, control_effectiveness: float,
                             residual_risks: List[Dict], data_confidence: float,
                             tier: str = 'B') -> Dict:
    """Calculate overall composite supplier score."""
    # Select framework weights based on tier
    if tier.upper().startswith('A'):
        weights = FRAMEWORK_WEIGHTS_TIER_A
    elif tier.upper().startswith('C'):
        weights = FRAMEWORK_WEIGHTS_TIER_C
    else:
        weights = FRAMEWORK_WEIGHTS_TIER_B
    
    # Calculate weighted framework score
    weighted_framework = 0
    for framework, score in framework_scores.items():
        framework_key = framework.lower().replace(' ', '_').replace('-', '_')
        weight = weights.get(framework_key, weights.get('other', 0.05))
        weighted_framework += score * weight
    
    # Normalize residual risk (higher = better)
    if residual_risks:
        total_exposure = sum(r.get('residual', {}).get('score', r.get('residual_score', 0)) 
                           for r in residual_risks)
        max_exposure = len(residual_risks) * 25
        risk_normalized = 100 - (total_exposure / max_exposure * 100) if max_exposure > 0 else 100
    else:
        risk_normalized = 100
    
    # Calculate composite
    composite = (
        weighted_framework * 0.35 +
        control_effectiveness * 0.25 +
        risk_normalized * 0.25 +
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
            'framework_score': round(weighted_framework, 1),
            'control_effectiveness': round(control_effectiveness, 1),
            'risk_normalized': round(risk_normalized, 1),
            'data_confidence': round(data_confidence, 1)
        },
        'tier': tier
    }

def calculate_data_confidence(source_authority: int, data_freshness: int,
                             corroboration: int, completeness: int) -> Dict:
    """Calculate data confidence score."""
    score = (
        source_authority * 0.30 +
        data_freshness * 0.25 +
        corroboration * 0.25 +
        completeness * 0.20
    )
    
    if score >= 85:
        level = "High"
    elif score >= 70:
        level = "Medium"
    elif score >= 50:
        level = "Low"
    else:
        level = "Very Low"
    
    return {
        'score': round(score, 1),
        'level': level,
        'components': {
            'source_authority': source_authority,
            'data_freshness': data_freshness,
            'corroboration': corroboration,
            'completeness': completeness
        }
    }

def calculate_risk_distribution(risks: List[Dict]) -> Dict:
    """Calculate risk distribution metrics."""
    distribution = {
        'Critical': 0,
        'High': 0,
        'Medium': 0,
        'Low': 0,
        'Very Low': 0
    }
    
    for risk in risks:
        rating = risk.get('residual_rating') or risk.get('rating', 'Medium')
        if rating in distribution:
            distribution[rating] += 1
    
    total = len(risks)
    
    return {
        'distribution': distribution,
        'percentages': {k: round(v/total*100, 1) if total > 0 else 0 
                       for k, v in distribution.items()},
        'total_risks': total,
        'total_exposure': sum(
            risk.get('residual_score') or risk.get('score', 0) 
            for risk in risks
        )
    }

def calculate_gap_priority(severity: str, effort: str) -> str:
    """Calculate gap priority based on severity and effort."""
    priority_matrix = {
        ('Critical', 'Low'): 'P1',
        ('Critical', 'Medium'): 'P1',
        ('Critical', 'High'): 'P2',
        ('High', 'Low'): 'P2',
        ('High', 'Medium'): 'P3',
        ('High', 'High'): 'P3',
        ('Medium', 'Low'): 'P3',
        ('Medium', 'Medium'): 'P4',
        ('Medium', 'High'): 'P4',
        ('Low', 'Low'): 'P4',
        ('Low', 'Medium'): 'P5',
        ('Low', 'High'): 'P5',
    }
    return priority_matrix.get((severity, effort), 'P4')

# ============================================================================
# BATCH PROCESSING
# ============================================================================

def process_risk_register(risks_data: List[Dict]) -> Dict:
    """Process entire risk register with inherent and residual calculations."""
    inherent_risks = []
    residual_risks = []
    
    for risk in risks_data:
        # Calculate inherent
        inherent = calculate_inherent_risk(
            risk['likelihood'],
            risk['impact']
        )
        inherent['id'] = risk['id']
        inherent['category'] = risk.get('category', 'General')
        inherent['description'] = risk.get('description', '')
        inherent_risks.append(inherent)
        
        # Calculate residual if controls provided
        if 'control_effectiveness' in risk:
            residual = calculate_residual_risk(
                risk['likelihood'],
                risk['impact'],
                risk['control_effectiveness'],
                risk.get('control_type', 'Compensating')
            )
            residual['id'] = risk['id']
            residual['category'] = risk.get('category', 'General')
            residual['description'] = risk.get('description', '')
            residual_risks.append(residual)
    
    # Calculate distributions
    inherent_dist = calculate_risk_distribution([
        {'rating': r['rating'], 'score': r['score']} for r in inherent_risks
    ])
    
    residual_dist = calculate_risk_distribution([
        {'residual_rating': r['residual']['rating'], 'residual_score': r['residual']['score']} 
        for r in residual_risks
    ]) if residual_risks else None
    
    # Overall metrics
    total_inherent = sum(r['score'] for r in inherent_risks)
    total_residual = sum(r['residual']['score'] for r in residual_risks) if residual_risks else total_inherent
    overall_reduction = round((1 - total_residual / total_inherent) * 100, 1) if total_inherent > 0 else 0
    
    return {
        'inherent_risks': inherent_risks,
        'residual_risks': residual_risks,
        'inherent_distribution': inherent_dist,
        'residual_distribution': residual_dist,
        'metrics': {
            'total_risks': len(inherent_risks),
            'total_inherent_exposure': total_inherent,
            'total_residual_exposure': total_residual,
            'overall_risk_reduction': overall_reduction
        }
    }

def process_framework_assessment(frameworks: Dict) -> Dict:
    """Process all framework scores and calculate overall compliance."""
    results = {}
    
    for framework, controls in frameworks.items():
        results[framework] = calculate_framework_score(controls)
    
    # Calculate overall compliance (simple average)
    scores = [f['overall_score'] for f in results.values()]
    overall = sum(scores) / len(scores) if scores else 0
    
    return {
        'frameworks': results,
        'overall_compliance': round(overall, 1),
        'frameworks_assessed': len(results),
        'fully_compliant': len([f for f in results.values() if f['overall_score'] >= 80])
    }

# ============================================================================
# MAIN / DEMO
# ============================================================================

if __name__ == "__main__":
    # Demo calculations
    print("=" * 60)
    print("TPSRCA Assessment Engine - Calculation Demo")
    print("=" * 60)
    
    # 1. Inherent Risk
    print("\n1. INHERENT RISK CALCULATION")
    print("-" * 40)
    inherent = calculate_inherent_risk(likelihood=4, impact=4)
    print(f"   Likelihood: {inherent['likelihood']}")
    print(f"   Impact: {inherent['impact']}")
    print(f"   Score: {inherent['score']}")
    print(f"   Rating: {inherent['rating']}")
    
    # 2. Control Effectiveness
    print("\n2. CONTROL EFFECTIVENESS")
    print("-" * 40)
    control = calculate_control_effectiveness(
        design=85, operating=80, coverage=75, status="Implemented"
    )
    print(f"   Design: {control['design']}%")
    print(f"   Operating: {control['operating']}%")
    print(f"   Coverage: {control['coverage']}%")
    print(f"   Status: {control['status']}")
    print(f"   Final Score: {control['final_score']}%")
    print(f"   Rating: {control['rating']}")
    
    # 3. Residual Risk
    print("\n3. RESIDUAL RISK CALCULATION")
    print("-" * 40)
    residual = calculate_residual_risk(
        inherent_likelihood=4, inherent_impact=4,
        control_effectiveness=control['final_score'],
        control_type="Preventive"
    )
    print(f"   Inherent Score: {residual['inherent']['score']}")
    print(f"   Residual Score: {residual['residual']['score']}")
    print(f"   Residual Rating: {residual['residual']['rating']}")
    print(f"   Risk Reduction: {residual['risk_reduction_percent']}%")
    
    # 4. Data Confidence
    print("\n4. DATA CONFIDENCE")
    print("-" * 40)
    confidence = calculate_data_confidence(
        source_authority=85, data_freshness=90,
        corroboration=70, completeness=75
    )
    print(f"   Score: {confidence['score']}%")
    print(f"   Level: {confidence['level']}")
    
    # 5. Framework Scores
    print("\n5. FRAMEWORK COMPLIANCE")
    print("-" * 40)
    framework_scores = {
        'DORA': 65,
        'ISO_27001': 82,
        'GDPR': 85,
        'NIST': 75,
        'NIS2': 68
    }
    for fw, score in framework_scores.items():
        print(f"   {fw}: {score}%")
    
    # 6. Composite Score
    print("\n6. COMPOSITE SCORE")
    print("-" * 40)
    composite = calculate_composite_score(
        framework_scores=framework_scores,
        control_effectiveness=control['final_score'],
        residual_risks=[residual],
        data_confidence=confidence['score'],
        tier='B'
    )
    print(f"   Composite Score: {composite['composite_score']}%")
    print(f"   Rating: {composite['rating']}")
    print(f"   Stars: {'★' * composite['stars']}{'☆' * (5 - composite['stars'])}")
    print(f"   Approval: {composite['approval_status']}")
    
    print("\n" + "=" * 60)
    print("Demo complete. Import this module for use in assessments.")
    print("=" * 60)
