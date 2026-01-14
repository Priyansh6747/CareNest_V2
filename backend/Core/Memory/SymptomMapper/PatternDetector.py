"""
PatternDetector.py - Long-term Symptom Pattern Detection

Analyzes medic stone history to detect recurring patterns,
time-based correlations, and early warning signs.
"""

from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import logging

from .MedicStone import (
    get_medic_stones_by_range,
    get_all_symptom_frequencies,
    MedicStone,
    SymptomFrequency,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Data Models
# =============================================================================

@dataclass
class RecurringPattern:
    """A detected recurring symptom pattern."""
    pattern_type: str  # "weekly", "daily_time", "symptom_cluster", "severity_spike"
    symptom_name: str
    description: str
    confidence: float  # 0.0 - 1.0
    occurrences: int
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "pattern_type": self.pattern_type,
            "symptom_name": self.symptom_name,
            "description": self.description,
            "confidence": round(self.confidence, 2),
            "occurrences": self.occurrences,
            "details": self.details,
        }


@dataclass
class SymptomCluster:
    """A group of symptoms that tend to occur together."""
    symptoms: List[str]
    co_occurrence_count: int
    avg_severity: float
    typical_timing: str  # "morning", "evening", "variable"
    confidence: float
    
    def to_dict(self) -> dict:
        return {
            "symptoms": self.symptoms,
            "co_occurrence_count": self.co_occurrence_count,
            "avg_severity": round(self.avg_severity, 2),
            "typical_timing": self.typical_timing,
            "confidence": round(self.confidence, 2),
        }


@dataclass
class PatternAnalysis:
    """Complete pattern analysis for a user."""
    user_id: str
    analysis_period_days: int
    total_symptoms_analyzed: int
    recurring_patterns: List[RecurringPattern]
    symptom_clusters: List[SymptomCluster]
    severity_spikes: List[Dict]
    early_warnings: List[str]
    
    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "analysis_period_days": self.analysis_period_days,
            "total_symptoms_analyzed": self.total_symptoms_analyzed,
            "patterns_found": len(self.recurring_patterns),
            "clusters_found": len(self.symptom_clusters),
            "recurring_patterns": [p.to_dict() for p in self.recurring_patterns],
            "symptom_clusters": [c.to_dict() for c in self.symptom_clusters],
            "severity_spikes": self.severity_spikes,
            "early_warnings": self.early_warnings,
        }


# =============================================================================
# Pattern Detector
# =============================================================================

class PatternDetector:
    """
    Detects long-term patterns in symptom data.
    
    Identifies:
    - Weekly/daily recurring patterns
    - Symptom clusters (co-occurring symptoms)
    - Severity spikes
    - Early warning signs
    """
    
    MIN_OCCURRENCES_FOR_PATTERN = 3
    CLUSTER_TIME_WINDOW_HOURS = 24
    
    def __init__(self, user_id: str):
        """
        Initialize the pattern detector.
        
        Args:
            user_id: The user's ID
        """
        self.user_id = user_id
    
    async def analyze(self, days: int = 60) -> PatternAnalysis:
        """
        Run complete pattern analysis.
        
        Args:
            days: Number of days of history to analyze
            
        Returns:
            PatternAnalysis with all detected patterns
        """
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        # Fetch all medic stones
        stones = await get_medic_stones_by_range(self.user_id, start_date, end_date)
        
        if len(stones) < self.MIN_OCCURRENCES_FOR_PATTERN:
            return PatternAnalysis(
                user_id=self.user_id,
                analysis_period_days=days,
                total_symptoms_analyzed=len(stones),
                recurring_patterns=[],
                symptom_clusters=[],
                severity_spikes=[],
                early_warnings=["Insufficient data for pattern analysis"]
            )
        
        # Run various pattern detections
        weekly_patterns = self._detect_weekly_patterns(stones)
        time_patterns = self._detect_time_of_day_patterns(stones)
        clusters = self._detect_symptom_clusters(stones)
        spikes = self._detect_severity_spikes(stones)
        warnings = await self._generate_early_warnings(stones)
        
        all_patterns = weekly_patterns + time_patterns
        all_patterns.sort(key=lambda p: p.confidence, reverse=True)
        
        return PatternAnalysis(
            user_id=self.user_id,
            analysis_period_days=days,
            total_symptoms_analyzed=len(stones),
            recurring_patterns=all_patterns[:10],  # Top 10 patterns
            symptom_clusters=clusters[:5],  # Top 5 clusters
            severity_spikes=spikes[-5:],  # Last 5 spikes
            early_warnings=warnings,
        )
    
    def _detect_weekly_patterns(self, stones: List[MedicStone]) -> List[RecurringPattern]:
        """Detect patterns that recur on specific days of the week."""
        patterns = []
        
        # Group by symptom
        by_symptom: Dict[str, List[MedicStone]] = defaultdict(list)
        for stone in stones:
            by_symptom[stone.symptom_name].append(stone)
        
        for symptom, symptom_stones in by_symptom.items():
            if len(symptom_stones) < self.MIN_OCCURRENCES_FOR_PATTERN:
                continue
            
            # Count occurrences by day of week (0=Monday, 6=Sunday)
            day_counts = defaultdict(int)
            for stone in symptom_stones:
                day_counts[stone.reported_at.weekday()] += 1
            
            # Check for significant weekly pattern
            total = len(symptom_stones)
            for day, count in day_counts.items():
                expected = total / 7
                if count >= expected * 2 and count >= self.MIN_OCCURRENCES_FOR_PATTERN:
                    day_name = ["Monday", "Tuesday", "Wednesday", "Thursday", 
                               "Friday", "Saturday", "Sunday"][day]
                    confidence = min(1.0, count / (expected * 3))
                    
                    patterns.append(RecurringPattern(
                        pattern_type="weekly",
                        symptom_name=symptom,
                        description=f"{symptom.title()} tends to occur on {day_name}s",
                        confidence=confidence,
                        occurrences=count,
                        details={
                            "day_of_week": day_name,
                            "expected_count": round(expected, 1),
                            "actual_count": count,
                        }
                    ))
        
        return patterns
    
    def _detect_time_of_day_patterns(self, stones: List[MedicStone]) -> List[RecurringPattern]:
        """Detect patterns related to time of day."""
        patterns = []
        
        def get_time_period(hour: int) -> str:
            if 5 <= hour < 12:
                return "morning"
            elif 12 <= hour < 17:
                return "afternoon"
            elif 17 <= hour < 21:
                return "evening"
            else:
                return "night"
        
        # Group by symptom
        by_symptom: Dict[str, List[MedicStone]] = defaultdict(list)
        for stone in stones:
            by_symptom[stone.symptom_name].append(stone)
        
        for symptom, symptom_stones in by_symptom.items():
            if len(symptom_stones) < self.MIN_OCCURRENCES_FOR_PATTERN:
                continue
            
            # Count by time period
            period_counts = defaultdict(int)
            for stone in symptom_stones:
                period = get_time_period(stone.reported_at.hour)
                period_counts[period] += 1
            
            total = len(symptom_stones)
            for period, count in period_counts.items():
                expected = total / 4
                if count >= expected * 2 and count >= self.MIN_OCCURRENCES_FOR_PATTERN:
                    confidence = min(1.0, count / (expected * 3))
                    
                    patterns.append(RecurringPattern(
                        pattern_type="daily_time",
                        symptom_name=symptom,
                        description=f"{symptom.title()} often occurs in the {period}",
                        confidence=confidence,
                        occurrences=count,
                        details={
                            "time_period": period,
                            "percentage": round((count / total) * 100, 1),
                        }
                    ))
        
        return patterns
    
    def _detect_symptom_clusters(self, stones: List[MedicStone]) -> List[SymptomCluster]:
        """Detect symptoms that tend to occur together."""
        clusters = []
        
        # Group stones by day
        by_date: Dict[str, List[MedicStone]] = defaultdict(list)
        for stone in stones:
            date_key = stone.reported_at.strftime("%Y-%m-%d")
            by_date[date_key].append(stone)
        
        # Count co-occurrences
        co_occurrence: Dict[Tuple[str, str], int] = defaultdict(int)
        for day_stones in by_date.values():
            symptoms = list(set(s.symptom_name for s in day_stones))
            for i, s1 in enumerate(symptoms):
                for s2 in symptoms[i+1:]:
                    pair = tuple(sorted([s1, s2]))
                    co_occurrence[pair] += 1
        
        # Find significant clusters
        for (s1, s2), count in co_occurrence.items():
            if count >= self.MIN_OCCURRENCES_FOR_PATTERN:
                # Calculate average severity when co-occurring
                severities = []
                for day_stones in by_date.values():
                    symptom_names = [s.symptom_name for s in day_stones]
                    if s1 in symptom_names and s2 in symptom_names:
                        severities.extend(s.severity for s in day_stones 
                                         if s.symptom_name in [s1, s2])
                
                avg_sev = sum(severities) / len(severities) if severities else 0
                
                clusters.append(SymptomCluster(
                    symptoms=[s1, s2],
                    co_occurrence_count=count,
                    avg_severity=avg_sev,
                    typical_timing="variable",  # Could be enhanced
                    confidence=min(1.0, count / 10),
                ))
        
        clusters.sort(key=lambda c: c.co_occurrence_count, reverse=True)
        return clusters
    
    def _detect_severity_spikes(self, stones: List[MedicStone]) -> List[Dict]:
        """Detect sudden increases in severity."""
        if len(stones) < 5:
            return []
        
        # Sort by date
        sorted_stones = sorted(stones, key=lambda s: s.reported_at)
        
        # Calculate rolling average severity
        window = 5
        spikes = []
        
        for i in range(window, len(sorted_stones)):
            # Average of previous window
            prev_avg = sum(s.severity for s in sorted_stones[i-window:i]) / window
            current = sorted_stones[i]
            
            # Spike if current is significantly higher than average
            if current.severity >= prev_avg + 1.5 and current.severity >= 4:
                spikes.append({
                    "date": current.reported_at.isoformat(),
                    "symptom": current.symptom_name,
                    "severity": current.severity,
                    "previous_avg": round(prev_avg, 2),
                    "spike_magnitude": round(current.severity - prev_avg, 2),
                })
        
        return spikes
    
    async def _generate_early_warnings(self, stones: List[MedicStone]) -> List[str]:
        """Generate early warning messages based on patterns."""
        warnings = []
        
        if not stones:
            return warnings
        
        # Check for recent high severity
        recent = [s for s in stones 
                  if s.reported_at > datetime.now(timezone.utc) - timedelta(days=7)]
        
        if recent:
            high_severity = [s for s in recent if s.severity >= 4]
            if len(high_severity) >= 3:
                warnings.append(
                    f"⚠️ {len(high_severity)} high-severity symptoms in the past week. "
                    "Consider consulting a healthcare provider."
                )
        
        # Check for increasing frequency
        frequencies = await get_all_symptom_frequencies(self.user_id, days=14)
        for freq in frequencies:
            if freq.severity_trend == "increasing" and freq.avg_severity >= 3:
                warnings.append(
                    f"📈 {freq.symptom_name.title()} is increasing in severity."
                )
        
        # Check for new symptoms
        old_symptoms = set(
            s.symptom_name for s in stones 
            if s.reported_at < datetime.now(timezone.utc) - timedelta(days=14)
        )
        new_symptoms = set(
            s.symptom_name for s in stones 
            if s.reported_at >= datetime.now(timezone.utc) - timedelta(days=7)
        ) - old_symptoms
        
        if new_symptoms:
            warnings.append(
                f"🆕 New symptoms reported: {', '.join(new_symptoms)}"
            )
        
        return warnings
