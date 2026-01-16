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
    """Detect abnormal lab values and vital signs with pregnancy-adjusted ranges"""
    abnormal = []
    
    # Define normal ranges (pregnancy-adjusted where applicable)
    normal_ranges = {
        # Vital signs
        "BP": (90, 140),  # systolic - important for preeclampsia detection
        "HR": (60, 100),
        "Temp": (97, 99),
        "SpO2": (95, 100),
        # Labs - pregnancy adjusted
        "Glucose": (70, 140),
        "FBS": (70, 95),  # Stricter for gestational diabetes
        "HbA1c": (4.0, 5.6),
        "WBC": (6.0, 16.0),  # Higher upper limit in pregnancy
        "HGB": (10.5, 14.5),  # Lower threshold in pregnancy
        "Hgb": (10.5, 14.5),
        "Hemoglobin": (10.5, 14.5),
        "HCT": (31, 41),  # Adjusted for pregnancy
        "PLT": (150, 400),
        "Creatinine": (0.4, 0.9),  # Lower in pregnancy
        "Cr": (0.4, 0.9),
        # Fetal
        "FHR": (110, 160),
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
                    if key.lower() in value_text.lower():
                        if value < low:
                            abnormal.append(f"⬇️ {value_text} (below normal: {low}-{high})")
                        elif value > high:
                            abnormal.append(f"⬆️ {value_text} (above normal: {low}-{high})")
                        break
            except:
                pass
    
    return abnormal[:5]  # Return top 5 abnormalities

def generate_alerts(entities_df: pd.DataFrame, text: str) -> List[str]:
    """Generate critical alerts with maternal health focus"""
    alerts = []
    
    text_lower = text.lower()
    
    # Maternal health critical phrases
    maternal_phrases = [
        # Preeclampsia/Eclampsia warning signs
        ("preeclampsia", "⚠️ Preeclampsia detected - monitor BP and protein levels closely"),
        ("eclampsia", "🚨 Eclampsia - immediate medical attention required"),
        ("hellp", "🚨 HELLP syndrome suspected - urgent evaluation needed"),
        ("severe headache", "⚠️ Severe headache in pregnancy - rule out preeclampsia"),
        ("visual disturbance", "⚠️ Visual changes - evaluate for preeclampsia"),
        ("epigastric pain", "⚠️ Epigastric pain - consider HELLP syndrome"),
        # Bleeding concerns
        ("vaginal bleeding", "🚨 Vaginal bleeding - evaluate immediately"),
        ("placenta previa", "⚠️ Placenta previa - requires monitoring"),
        ("abruption", "🚨 Placental abruption suspected - emergency evaluation"),
        # Other pregnancy concerns
        ("decreased fetal movement", "⚠️ Reduced fetal movement - fetal assessment needed"),
        ("preterm", "⚠️ Preterm labor risk - monitor closely"),
        ("rupture of membranes", "⚠️ ROM - evaluate for labor and infection"),
    ]
    
    # General critical phrases
    general_phrases = [
        ("chest pain", "⚠️ Chest pain - consider cardiac evaluation"),
        ("shortness of breath", "⚠️ Dyspnea - assess oxygenation"),
        ("fever >101", "⚠️ Fever - evaluate for infection"),
        ("severe pain", "⚠️ Severe pain - assess management"),
        ("allergy", "ℹ️ Allergy noted - verify documentation"),
    ]
    
    all_phrases = maternal_phrases + general_phrases
    
    for phrase, alert in all_phrases:
        if phrase.lower() in text_lower:
            alerts.append(alert)
    
    # Check for high-risk medications in pregnancy
    if not entities_df.empty and 'entity_type' in entities_df.columns:
        medications = entities_df[entities_df['entity_type'] == 'MEDICATION']['text'].tolist()
        
        # Medications requiring caution in pregnancy
        caution_meds = ["warfarin", "methotrexate", "isotretinoin", "valproic", "lithium", "nsaid", "ibuprofen"]
        
        for med in medications:
            if any(caution_med in med.lower() for caution_med in caution_meds):
                alerts.append(f"⚠️ Pregnancy caution medication: {med}")
    
    # Check for abnormal vital signs suggesting preeclampsia
    bp_pattern = r'(?:BP|blood\s*pressure)\s*:?\s*(\d{2,3})\s*/\s*(\d{2,3})'
    bp_match = re.search(bp_pattern, text, re.IGNORECASE)
    if bp_match:
        systolic = int(bp_match.group(1))
        diastolic = int(bp_match.group(2))
        if systolic >= 140 or diastolic >= 90:
            alerts.append(f"🚨 Elevated BP {systolic}/{diastolic} - evaluate for hypertensive disorder")
    
    return list(set(alerts))[:5]  # Return unique alerts, max 5

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