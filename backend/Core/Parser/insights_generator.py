import pandas as pd
from typing import Dict, List, Any
import re

def generate_clinical_insights(entities_df: pd.DataFrame, original_text: str) -> Dict[str, Any]:
    """
    Generate clinical insights from extracted entities
    """
    insights = {
        "active_conditions": [],
        "current_medications": [],
        "abnormal_findings": [],
        "critical_alerts": [],
        "pending_tests": [],
        "recommendations": [],
        "action_items": [],
        "summary": ""
    }
    
    if entities_df.empty:
        return insights
    
    # Extract conditions
    if 'CONDITION' in entities_df['entity_type'].values:
        conditions = entities_df[entities_df['entity_type'] == 'CONDITION']['text'].unique()
        insights['active_conditions'] = list(conditions[:10])  # Limit to 10
    
    # Extract medications
    if 'MEDICATION' in entities_df['entity_type'].values:
        medications = entities_df[entities_df['entity_type'] == 'MEDICATION']['text'].unique()
        insights['current_medications'] = list(medications[:10])
    
    # Extract measurements and check for abnormalities
    if 'MEASUREMENT' in entities_df['entity_type'].values:
        measurements = entities_df[entities_df['entity_type'] == 'MEASUREMENT']
        abnormal = detect_abnormal_values(measurements, original_text)
        insights['abnormal_findings'] = abnormal
    
    # Generate critical alerts
    insights['critical_alerts'] = generate_alerts(entities_df, original_text)
    
    # Look for pending tests/follow-ups
    insights['pending_tests'] = extract_pending_tests(original_text)
    
    # Generate recommendations
    insights['recommendations'] = generate_recommendations(insights)
    
    # Action items
    insights['action_items'] = [
        "Review abnormal lab values",
        "Verify medication list",
        "Check for drug interactions",
        "Schedule follow-up if needed"
    ]
    
    # Generate summary
    insights['summary'] = generate_summary(insights, original_text)
    
    return insights

def detect_abnormal_values(measurements_df: pd.DataFrame, text: str) -> List[str]:
    """Detect abnormal lab values and vital signs"""
    abnormal = []
    
    # Define normal ranges
    normal_ranges = {
        "BP": (90, 140),  # systolic
        "HR": (60, 100),
        "Temp": (97, 99),
        "Glucose": (70, 140),
        "WBC": (4.5, 11.0),
        "HGB": (12, 16),
        "Creatinine": (0.6, 1.2)
    }
    
    for _, row in measurements_df.iterrows():
        value_text = row['text']
        
        # Try to extract numeric value
        numbers = re.findall(r"(\d+\.?\d*)", value_text)
        if numbers:
            try:
                value = float(numbers[0])
                
                # Check against known ranges
                for key, (low, high) in normal_ranges.items():
                    if key in value_text:
                        if value < low or value > high:
                            abnormal.append(f"{value_text} (outside normal range: {low}-{high})")
                        break
            except:
                pass
    
    return abnormal[:5]  # Return top 5 abnormalities

def generate_alerts(entities_df: pd.DataFrame, text: str) -> List[str]:
    """Generate critical alerts"""
    alerts = []
    
    text_lower = text.lower()
    
    # Check for critical phrases
    critical_phrases = [
        ("chest pain", "Consider cardiac evaluation"),
        ("shortness of breath", "Assess oxygenation status"),
        ("fever >101", "Evaluate for infection"),
        ("severe pain", "Assess pain management"),
        ("allergy", "Verify allergy documentation"),
        ("elevated troponin", "Cardiology consultation recommended"),
        ("hypotension", "Monitor BP closely")
    ]
    
    for phrase, alert in critical_phrases:
        if phrase.lower() in text_lower:
            alerts.append(alert)
    
    # Check for medication alerts
    medications = entities_df[entities_df['entity_type'] == 'MEDICATION']['text'].tolist()
    high_risk_meds = ["warfarin", "insulin", "digoxin", "lithium"]
    
    for med in medications:
        if any(risk_med in med.lower() for risk_med in high_risk_meds):
            alerts.append(f"High-risk medication detected: {med}")
    
    return list(set(alerts))[:3]  # Return unique alerts, max 3

def extract_pending_tests(text: str) -> List[str]:
    """Extract pending tests/follow-ups"""
    pending = []
    
    patterns = [
        r"follow[-\s]?up\s+(?:in|for)\s+(\w+\s+\w+)",
        r"schedule\s+(\w+\s+test)",
        r"pending\s+(\w+)",
        r"to be\s+(?:done|scheduled)",
        r"(\w+)\s+recommended"
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        pending.extend(matches)
    
    return list(set(pending))[:5]

def generate_recommendations(insights: Dict) -> List[str]:
    """Generate clinical recommendations"""
    recommendations = []
    
    if insights['abnormal_findings']:
        recommendations.append("Review abnormal laboratory values")
    
    if insights['current_medications'] and len(insights['current_medications']) > 5:
        recommendations.append("Consider medication reconciliation")
    
    if insights['active_conditions'] and any(cond.lower() in ['diabetes', 'hypertension'] 
                                           for cond in insights['active_conditions']):
        recommendations.append("Monitor chronic condition management")
    
    if not recommendations:
        recommendations.append("Continue current management plan")
        recommendations.append("Schedule routine follow-up")
    
    return recommendations

def generate_summary(insights: Dict, original_text: str) -> str:
    """Generate a clinical summary"""
    summary_parts = []
    
    if insights['active_conditions']:
        summary_parts.append(f"Patient with {len(insights['active_conditions'])} active conditions.")
    
    if insights['current_medications']:
        summary_parts.append(f"Currently on {len(insights['current_medications'])} medications.")
    
    if insights['abnormal_findings']:
        summary_parts.append(f"{len(insights['abnormal_findings'])} abnormal findings noted.")
    
    if insights['critical_alerts']:
        summary_parts.append(f"{len(insights['critical_alerts'])} critical alerts require attention.")
    
    if not summary_parts:
        # Extract first few lines as summary
        lines = original_text.split('\n')
        summary = ' '.join(lines[:3])[:200] + "..."
        return summary
    
    return " ".join(summary_parts)