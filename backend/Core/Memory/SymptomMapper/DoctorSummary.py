"""
DoctorSummary.py - Generate Doctor Reports from Medic Stones

Creates structured, physician-friendly summaries of symptom patterns,
frequencies, and correlations for healthcare provider review.
"""

from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
import logging

from .MedicStone import (
    get_medic_stones_by_range,
    get_all_symptom_frequencies,
    SymptomFrequency,
)
from .PatternDetector import PatternDetector, PatternAnalysis
from .TimelineMapper import TimelineMapper

logger = logging.getLogger(__name__)


# =============================================================================
# Data Models
# =============================================================================

@dataclass
class SymptomSummaryItem:
    """Summary for a single symptom type."""
    symptom_name: str
    total_occurrences: int
    avg_severity: float
    max_severity: int
    frequency_per_week: float
    trend: str
    first_reported: str
    last_reported: str
    common_context: List[str]


@dataclass 
class DoctorReport:
    """Complete physician-ready report."""
    user_id: str
    generated_at: datetime
    report_period_days: int
    
    # Patient context
    patient_summary: Dict[str, Any]
    
    # Symptom overview
    total_symptoms_logged: int
    unique_symptom_types: int
    symptom_summaries: List[SymptomSummaryItem]
    
    # Patterns and insights
    key_patterns: List[Dict]
    symptom_clusters: List[Dict]
    severity_timeline: List[Dict]
    
    # Alerts and recommendations
    alerts: List[str]
    recommended_followups: List[str]
    
    # Metadata
    data_quality_score: float
    
    def to_dict(self) -> dict:
        return {
            "report_metadata": {
                "generated_at": self.generated_at.isoformat(),
                "report_period_days": self.report_period_days,
                "data_quality_score": round(self.data_quality_score, 2),
            },
            "patient_summary": self.patient_summary,
            "symptom_overview": {
                "total_logged": self.total_symptoms_logged,
                "unique_types": self.unique_symptom_types,
                "summaries": [
                    {
                        "symptom": s.symptom_name,
                        "occurrences": s.total_occurrences,
                        "avg_severity": round(s.avg_severity, 1),
                        "max_severity": s.max_severity,
                        "weekly_frequency": round(s.frequency_per_week, 1),
                        "trend": s.trend,
                        "period": f"{s.first_reported} to {s.last_reported}",
                        "context": s.common_context,
                    }
                    for s in self.symptom_summaries
                ]
            },
            "patterns": {
                "key_patterns": self.key_patterns,
                "symptom_clusters": self.symptom_clusters,
            },
            "severity_timeline": self.severity_timeline,
            "clinical_alerts": self.alerts,
            "recommended_followups": self.recommended_followups,
        }
    
    def to_markdown(self) -> str:
        """Generate a markdown-formatted report."""
        lines = [
            "# Symptom Summary Report",
            f"*Generated: {self.generated_at.strftime('%Y-%m-%d %H:%M')} UTC*",
            f"*Period: Last {self.report_period_days} days*",
            "",
        ]
        
        # Alerts section
        if self.alerts:
            lines.extend([
                "## ⚠️ Clinical Alerts",
                "",
            ])
            for alert in self.alerts:
                lines.append(f"- {alert}")
            lines.append("")
        
        # Overview
        lines.extend([
            "## Overview",
            f"- Total symptoms logged: **{self.total_symptoms_logged}**",
            f"- Unique symptom types: **{self.unique_symptom_types}**",
            f"- Data quality score: **{self.data_quality_score:.0%}**",
            "",
        ])
        
        # Symptom summaries
        if self.symptom_summaries:
            lines.extend([
                "## Symptom Details",
                "",
                "| Symptom | Occurrences | Avg Severity | Trend | Weekly Freq |",
                "|---------|-------------|--------------|-------|-------------|",
            ])
            for s in self.symptom_summaries[:10]:
                trend_icon = {"increasing": "📈", "decreasing": "📉", "stable": "➡️"}.get(s.trend, "")
                lines.append(
                    f"| {s.symptom_name.title()} | {s.total_occurrences} | "
                    f"{s.avg_severity:.1f}/5 | {trend_icon} {s.trend} | {s.frequency_per_week:.1f}/wk |"
                )
            lines.append("")
        
        # Patterns
        if self.key_patterns:
            lines.extend([
                "## Detected Patterns",
                "",
            ])
            for p in self.key_patterns[:5]:
                lines.append(f"- **{p.get('pattern_type', 'Pattern')}**: {p.get('description', '')}")
            lines.append("")
        
        # Clusters
        if self.symptom_clusters:
            lines.extend([
                "## Symptom Clusters",
                "*Symptoms that tend to occur together*",
                "",
            ])
            for c in self.symptom_clusters[:3]:
                symptoms = ", ".join(c.get("symptoms", []))
                lines.append(f"- {symptoms} (co-occurred {c.get('co_occurrence_count', 0)} times)")
            lines.append("")
        
        # Recommendations
        if self.recommended_followups:
            lines.extend([
                "## Recommended Follow-ups",
                "",
            ])
            for rec in self.recommended_followups:
                lines.append(f"- {rec}")
            lines.append("")
        
        lines.extend([
            "---",
            "*This report is generated from patient-reported symptoms and should be reviewed in context of clinical examination.*"
        ])
        
        return "\n".join(lines)


# =============================================================================
# Doctor Summary Generator
# =============================================================================

class DoctorSummaryGenerator:
    """
    Generates comprehensive doctor summaries from medic stone data.
    
    Integrates:
    - Symptom frequency analysis
    - Pattern detection
    - Timeline correlation
    """
    
    def __init__(self, user_id: str):
        """
        Initialize the generator.
        
        Args:
            user_id: The user's ID
        """
        self.user_id = user_id
        self.pattern_detector = PatternDetector(user_id)
        self.timeline_mapper = TimelineMapper(user_id)
    
    async def _get_patient_summary(self) -> Dict[str, Any]:
        """Fetch patient context from user profile."""
        try:
            from config import maternal_profiles_collection, users_collection
            
            # Get user
            user_docs = list(users_collection.where("_id", "==", self.user_id).limit(1).stream())
            
            # Get maternal profile
            maternal_docs = list(
                maternal_profiles_collection.where("user_id", "==", self.user_id).limit(1).stream()
            )
            
            context = {}
            if maternal_docs:
                maternal = maternal_docs[0].to_dict()
                personal = maternal.get("personal", {})
                pregnancy = maternal.get("pregnancy", {})
                diet = maternal.get("diet", {})
                
                context = {
                    "age": personal.get("age"),
                    "pregnancy_stage": pregnancy.get("stage"),
                    "risk_level": pregnancy.get("risk_level"),
                    "known_conditions": pregnancy.get("known_conditions", []),
                    "allergies": diet.get("allergies", []),
                }
            
            return context
            
        except Exception as e:
            logger.warning(f"Failed to fetch patient summary: {e}")
            return {}
    
    async def generate(self, days: int = 30) -> DoctorReport:
        """
        Generate a complete doctor summary.
        
        Args:
            days: Number of days to include in report
            
        Returns:
            DoctorReport ready for physician review
        """
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        # Fetch all data
        stones = await get_medic_stones_by_range(self.user_id, start_date, end_date)
        frequencies = await get_all_symptom_frequencies(self.user_id, days)
        pattern_analysis = await self.pattern_detector.analyze(days)
        patient_summary = await self._get_patient_summary()
        
        # Build symptom summaries
        symptom_summaries = []
        for freq in frequencies:
            # Find common context for this symptom
            symptom_stones = [s for s in stones if s.symptom_name == freq.symptom_name]
            common_context = self._extract_common_context(symptom_stones)
            
            symptom_summaries.append(SymptomSummaryItem(
                symptom_name=freq.symptom_name,
                total_occurrences=freq.total_occurrences,
                avg_severity=freq.avg_severity,
                max_severity=max((s.severity for s in symptom_stones), default=0),
                frequency_per_week=freq.frequency_per_week,
                trend=freq.severity_trend,
                first_reported=freq.first_reported.strftime("%Y-%m-%d"),
                last_reported=freq.last_reported.strftime("%Y-%m-%d"),
                common_context=common_context,
            ))
        
        # Build severity timeline (weekly averages)
        severity_timeline = self._build_severity_timeline(stones, days)
        
        # Generate alerts
        alerts = self._generate_alerts(stones, frequencies, pattern_analysis)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(frequencies, pattern_analysis)
        
        # Calculate data quality score
        data_quality = self._calculate_data_quality(stones, days)
        
        return DoctorReport(
            user_id=self.user_id,
            generated_at=datetime.now(timezone.utc),
            report_period_days=days,
            patient_summary=patient_summary,
            total_symptoms_logged=len(stones),
            unique_symptom_types=len(frequencies),
            symptom_summaries=symptom_summaries,
            key_patterns=[p.to_dict() for p in pattern_analysis.recurring_patterns],
            symptom_clusters=[c.to_dict() for c in pattern_analysis.symptom_clusters],
            severity_timeline=severity_timeline,
            alerts=alerts,
            recommended_followups=recommendations,
            data_quality_score=data_quality,
        )
    
    def _extract_common_context(self, stones: List) -> List[str]:
        """Extract commonly occurring context factors."""
        if not stones:
            return []
        
        context_counts: Dict[str, int] = {}
        for stone in stones:
            ctx = stone.context or {}
            
            # Check for low values that might be relevant
            if ctx.get("water_ml", 2500) < 1500:
                context_counts["low water intake"] = context_counts.get("low water intake", 0) + 1
            if ctx.get("iron_mg", 30) < 15:
                context_counts["low iron"] = context_counts.get("low iron", 0) + 1
            if ctx.get("sleep_hours", 8) < 6:
                context_counts["poor sleep"] = context_counts.get("poor sleep", 0) + 1
            if ctx.get("stress_level", 1) >= 4:
                context_counts["high stress"] = context_counts.get("high stress", 0) + 1
        
        # Return factors that appear in >30% of occurrences
        threshold = len(stones) * 0.3
        return [k for k, v in context_counts.items() if v >= threshold]
    
    def _build_severity_timeline(self, stones: List, days: int) -> List[Dict]:
        """Build weekly severity averages for timeline."""
        if not stones:
            return []
        
        # Group by week
        weeks: Dict[str, List[int]] = {}
        for stone in stones:
            week_start = stone.reported_at - timedelta(days=stone.reported_at.weekday())
            week_key = week_start.strftime("%Y-%m-%d")
            if week_key not in weeks:
                weeks[week_key] = []
            weeks[week_key].append(stone.severity)
        
        timeline = []
        for week, severities in sorted(weeks.items()):
            timeline.append({
                "week_start": week,
                "avg_severity": round(sum(severities) / len(severities), 2),
                "max_severity": max(severities),
                "symptom_count": len(severities),
            })
        
        return timeline
    
    def _generate_alerts(
        self,
        stones: List,
        frequencies: List[SymptomFrequency],
        patterns: PatternAnalysis
    ) -> List[str]:
        """Generate clinical alerts based on data."""
        alerts = []
        
        # High severity recent symptoms
        recent_high = [
            s for s in stones
            if s.severity >= 4 and s.reported_at > datetime.now(timezone.utc) - timedelta(days=7)
        ]
        if len(recent_high) >= 3:
            alerts.append(
                f"High severity symptoms ({len(recent_high)} instances) in past 7 days"
            )
        
        # Increasing severity trends
        increasing = [f for f in frequencies if f.severity_trend == "increasing" and f.avg_severity >= 3]
        for f in increasing[:3]:
            alerts.append(f"{f.symptom_name.title()}: severity trend increasing")
        
        # Add pattern-based warnings
        alerts.extend(patterns.early_warnings[:3])
        
        return alerts
    
    def _generate_recommendations(
        self,
        frequencies: List[SymptomFrequency],
        patterns: PatternAnalysis
    ) -> List[str]:
        """Generate follow-up recommendations."""
        recommendations = []
        
        # High frequency symptoms
        high_freq = [f for f in frequencies if f.frequency_per_week >= 3]
        for f in high_freq[:2]:
            recommendations.append(
                f"Investigate {f.symptom_name}: occurs {f.frequency_per_week:.1f}x/week"
            )
        
        # Pattern-based recommendations
        for pattern in patterns.recurring_patterns[:2]:
            if pattern.confidence >= 0.7:
                recommendations.append(
                    f"Review {pattern.pattern_type} pattern: {pattern.description}"
                )
        
        # Cluster recommendations
        for cluster in patterns.symptom_clusters[:1]:
            symptoms = ", ".join(cluster.symptoms)
            recommendations.append(
                f"Evaluate symptom cluster: {symptoms}"
            )
        
        if not recommendations:
            recommendations.append("Continue routine monitoring")
        
        return recommendations
    
    def _calculate_data_quality(self, stones: List, days: int) -> float:
        """Calculate data quality score (0-1) based on logging consistency."""
        if not stones:
            return 0.0
        
        # Count unique days with logs
        unique_days = len(set(s.reported_at.strftime("%Y-%m-%d") for s in stones))
        
        # Score based on coverage
        coverage = min(1.0, unique_days / (days * 0.5))  # 50% coverage = 1.0
        
        # Bonus for context data
        with_context = len([s for s in stones if s.context])
        context_score = with_context / len(stones) if stones else 0
        
        return (coverage * 0.7) + (context_score * 0.3)
