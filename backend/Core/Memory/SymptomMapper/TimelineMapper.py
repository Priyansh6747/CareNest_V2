"""
TimelineMapper.py - Symptom Timeline with Trend Correlation

Maps symptoms onto a timeline and correlates with nutritional
and behavioral data to identify potential triggers.
"""

from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict
import logging

from .MedicStone import (
    get_medic_stones_by_range,
    get_recent_medic_stones,
    MedicStone,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Data Models
# =============================================================================

@dataclass
class TimelinePoint:
    """A single point on the symptom timeline."""
    date: datetime
    symptom_name: str
    severity: int
    stone_id: str
    context: Dict[str, Any] = field(default_factory=dict)
    correlations: List[str] = field(default_factory=list)


@dataclass
class DaySymptomSummary:
    """Summary of symptoms for a single day."""
    date: datetime
    symptoms: List[TimelinePoint]
    unique_symptoms: List[str]
    max_severity: int
    avg_severity: float
    context_summary: Dict[str, Any]


@dataclass
class SymptomTimeline:
    """Complete symptom timeline for a user."""
    user_id: str
    start_date: datetime
    end_date: datetime
    total_symptoms: int
    unique_symptom_types: List[str]
    daily_summaries: List[DaySymptomSummary]
    trending_symptoms: List[Dict]
    current_trends: Dict[str, str]  # symptom -> "increasing"/"decreasing"/"stable"
    
    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "total_symptoms": self.total_symptoms,
            "unique_symptom_types": self.unique_symptom_types,
            "days_with_symptoms": len([d for d in self.daily_summaries if d.symptoms]),
            "trending_symptoms": self.trending_symptoms,
            "current_trends": self.current_trends,
            "daily_summaries": [
                {
                    "date": d.date.strftime("%Y-%m-%d"),
                    "symptom_count": len(d.symptoms),
                    "max_severity": d.max_severity,
                    "avg_severity": round(d.avg_severity, 2),
                    "symptoms": d.unique_symptoms,
                }
                for d in self.daily_summaries
            ]
        }


# =============================================================================
# Timeline Mapper
# =============================================================================

class TimelineMapper:
    """
    Maps symptoms onto a timeline and identifies correlations.
    
    Integrates with nutrition data to find potential triggers.
    """
    
    def __init__(self, user_id: str):
        """
        Initialize the timeline mapper.
        
        Args:
            user_id: The user's ID for data retrieval
        """
        self.user_id = user_id
    
    async def _fetch_nutrition_context(
        self,
        date: datetime
    ) -> Dict[str, Any]:
        """
        Fetch nutrition context for a specific date.
        
        Integrates with DataExtractor to get nutrient intake.
        """
        try:
            from Core.Insights.DataExtractor import DataExtractor
            extractor = DataExtractor(self.user_id)
            
            nutrition = extractor.fetch_daily_nutrition(date.date())
            water = extractor.fetch_daily_water(date.date())
            
            return {
                "protein_g": nutrition.get("protein_g", 0),
                "iron_mg": nutrition.get("iron_mg", 0),
                "fiber_g": nutrition.get("fiber_g", 0),
                "water_ml": water.get("water_intake_ml", 0),
                "meal_count": nutrition.get("meal_count", 0),
            }
        except Exception as e:
            logger.warning(f"Failed to fetch nutrition context: {e}")
            return {}
    
    async def build_timeline(
        self,
        days: int = 30,
        include_nutrition: bool = True
    ) -> SymptomTimeline:
        """
        Build a complete symptom timeline.
        
        Args:
            days: Number of days to include
            include_nutrition: Whether to fetch nutrition context
            
        Returns:
            SymptomTimeline with daily summaries and trends
        """
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        # Fetch all medic stones in range
        stones = await get_medic_stones_by_range(self.user_id, start_date, end_date)
        
        # Group by date
        stones_by_date: Dict[str, List[MedicStone]] = defaultdict(list)
        for stone in stones:
            date_key = stone.reported_at.strftime("%Y-%m-%d")
            stones_by_date[date_key].append(stone)
        
        # Build daily summaries
        daily_summaries = []
        all_symptoms = set()
        
        current_date = start_date
        while current_date <= end_date:
            date_key = current_date.strftime("%Y-%m-%d")
            day_stones = stones_by_date.get(date_key, [])
            
            # Build timeline points
            points = []
            for stone in day_stones:
                point = TimelinePoint(
                    date=stone.reported_at,
                    symptom_name=stone.symptom_name,
                    severity=stone.severity,
                    stone_id=stone.id,
                    context=stone.context,
                )
                points.append(point)
                all_symptoms.add(stone.symptom_name)
            
            # Compute day summary
            unique_symptoms = list(set(p.symptom_name for p in points))
            max_sev = max((p.severity for p in points), default=0)
            avg_sev = sum(p.severity for p in points) / len(points) if points else 0
            
            # Get nutrition context for days with symptoms
            context_summary = {}
            if points and include_nutrition:
                context_summary = await self._fetch_nutrition_context(current_date)
            
            summary = DaySymptomSummary(
                date=current_date,
                symptoms=points,
                unique_symptoms=unique_symptoms,
                max_severity=max_sev,
                avg_severity=avg_sev,
                context_summary=context_summary,
            )
            daily_summaries.append(summary)
            
            current_date += timedelta(days=1)
        
        # Compute trends
        trending_symptoms = self._compute_trending(stones)
        current_trends = self._compute_current_trends(stones)
        
        return SymptomTimeline(
            user_id=self.user_id,
            start_date=start_date,
            end_date=end_date,
            total_symptoms=len(stones),
            unique_symptom_types=sorted(list(all_symptoms)),
            daily_summaries=daily_summaries,
            trending_symptoms=trending_symptoms,
            current_trends=current_trends,
        )
    
    def _compute_trending(self, stones: List[MedicStone]) -> List[Dict]:
        """Identify trending symptoms (increasing frequency/severity)."""
        if len(stones) < 3:
            return []
        
        # Group by symptom
        by_symptom: Dict[str, List[MedicStone]] = defaultdict(list)
        for stone in stones:
            by_symptom[stone.symptom_name].append(stone)
        
        trending = []
        for symptom, symptom_stones in by_symptom.items():
            if len(symptom_stones) < 2:
                continue
            
            # Sort by date
            sorted_stones = sorted(symptom_stones, key=lambda s: s.reported_at)
            
            # Compare first vs last half
            mid = len(sorted_stones) // 2
            first_half = sorted_stones[:mid]
            second_half = sorted_stones[mid:]
            
            first_avg_sev = sum(s.severity for s in first_half) / len(first_half)
            second_avg_sev = sum(s.severity for s in second_half) / len(second_half)
            
            if len(second_half) > len(first_half) or second_avg_sev > first_avg_sev:
                trending.append({
                    "symptom": symptom,
                    "total_count": len(symptom_stones),
                    "severity_change": round(second_avg_sev - first_avg_sev, 2),
                    "frequency_change": len(second_half) - len(first_half),
                })
        
        trending.sort(key=lambda x: x["frequency_change"], reverse=True)
        return trending[:5]  # Top 5 trending
    
    def _compute_current_trends(self, stones: List[MedicStone]) -> Dict[str, str]:
        """Compute current trend direction for each symptom."""
        if len(stones) < 2:
            return {}
        
        by_symptom: Dict[str, List[MedicStone]] = defaultdict(list)
        for stone in stones:
            by_symptom[stone.symptom_name].append(stone)
        
        trends = {}
        for symptom, symptom_stones in by_symptom.items():
            if len(symptom_stones) < 2:
                trends[symptom] = "stable"
                continue
            
            sorted_stones = sorted(symptom_stones, key=lambda s: s.reported_at)
            severities = [s.severity for s in sorted_stones]
            
            # Simple linear trend
            first_third = severities[:len(severities)//3] or severities[:1]
            last_third = severities[-len(severities)//3:] or severities[-1:]
            
            first_avg = sum(first_third) / len(first_third)
            last_avg = sum(last_third) / len(last_third)
            
            if last_avg > first_avg + 0.5:
                trends[symptom] = "increasing"
            elif last_avg < first_avg - 0.5:
                trends[symptom] = "decreasing"
            else:
                trends[symptom] = "stable"
        
        return trends
    
    async def get_symptom_correlations(
        self,
        symptom_name: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Analyze correlations between a symptom and nutrition/context.
        
        Args:
            symptom_name: Symptom to analyze
            days: Analysis period
            
        Returns:
            Correlation analysis
        """
        timeline = await self.build_timeline(days, include_nutrition=True)
        
        symptom_days = []
        no_symptom_days = []
        
        for day in timeline.daily_summaries:
            if symptom_name.lower() in [s.lower() for s in day.unique_symptoms]:
                symptom_days.append(day)
            else:
                no_symptom_days.append(day)
        
        if not symptom_days or not no_symptom_days:
            return {
                "symptom": symptom_name,
                "analysis": "insufficient_data",
                "symptom_days": len(symptom_days),
                "no_symptom_days": len(no_symptom_days),
            }
        
        # Compare average nutrition on symptom vs non-symptom days
        def avg_context(days: List[DaySymptomSummary], key: str) -> float:
            values = [d.context_summary.get(key, 0) for d in days if d.context_summary]
            return sum(values) / len(values) if values else 0
        
        correlations = {}
        for key in ["protein_g", "iron_mg", "water_ml", "fiber_g"]:
            symptom_avg = avg_context(symptom_days, key)
            no_symptom_avg = avg_context(no_symptom_days, key)
            
            if no_symptom_avg > 0:
                diff_pct = ((symptom_avg - no_symptom_avg) / no_symptom_avg) * 100
                correlations[key] = {
                    "symptom_days_avg": round(symptom_avg, 2),
                    "normal_days_avg": round(no_symptom_avg, 2),
                    "difference_pct": round(diff_pct, 1),
                }
        
        return {
            "symptom": symptom_name,
            "symptom_days": len(symptom_days),
            "no_symptom_days": len(no_symptom_days),
            "correlations": correlations,
            "potential_triggers": [
                k for k, v in correlations.items() 
                if abs(v.get("difference_pct", 0)) > 20
            ]
        }
