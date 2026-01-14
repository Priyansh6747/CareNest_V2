"""
MedicStone.py - Symptom Tracking with Medic Stones

Medic Stones are time-stamped symptom records enriched with context
(nutrients, activity, etc.) that form a timeline for pattern detection.
"""

from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field

from config import firestoreDB

import logging

logger = logging.getLogger(__name__)


# =============================================================================
# Pydantic Models
# =============================================================================

class Severity(int, Enum):
    """Symptom severity scale."""
    MINIMAL = 1
    MILD = 2
    MODERATE = 3
    SEVERE = 4
    CRITICAL = 5


class SymptomContext(BaseModel):
    """Contextual data captured with the symptom."""
    # Nutritional context (from recent intake)
    protein_g: Optional[float] = None
    iron_mg: Optional[float] = None
    water_ml: Optional[float] = None
    vitamin_d_iu: Optional[float] = None
    
    # Activity/environmental
    sleep_hours: Optional[float] = None
    activity_level: Optional[str] = None  # "low", "moderate", "high"
    stress_level: Optional[int] = None    # 1-5 scale
    
    # Additional notes
    notes: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {k: v for k, v in self.model_dump().items() if v is not None}


class MedicStoneCreate(BaseModel):
    """Input model for creating a medic stone."""
    symptom_name: str = Field(..., min_length=1, description="Name of the symptom")
    severity: int = Field(..., ge=1, le=5, description="Severity (1-5)")
    description: Optional[str] = Field(default="", description="Additional description")
    context: Optional[SymptomContext] = None
    reported_at: Optional[datetime] = None  # Defaults to now if not provided


class MedicStoneUpdate(BaseModel):
    """Input model for updating a medic stone."""
    symptom_name: Optional[str] = None
    severity: Optional[int] = Field(default=None, ge=1, le=5)
    description: Optional[str] = None
    context: Optional[SymptomContext] = None


class MedicStone(BaseModel):
    """Complete medic stone model."""
    id: str
    user_id: str
    symptom_name: str
    severity: int
    description: str
    context: Dict[str, Any]
    trends: List[str]  # Computed trend indicators
    reported_at: datetime
    created_at: datetime
    updated_at: datetime
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "symptom_name": self.symptom_name,
            "severity": self.severity,
            "severity_label": Severity(self.severity).name.lower(),
            "description": self.description,
            "context": self.context,
            "trends": self.trends,
            "reported_at": self.reported_at.isoformat(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class SymptomFrequency(BaseModel):
    """Frequency analysis for a symptom."""
    symptom_name: str
    total_occurrences: int
    avg_severity: float
    first_reported: datetime
    last_reported: datetime
    frequency_per_week: float
    severity_trend: str  # "increasing", "decreasing", "stable"


# =============================================================================
# Helper Functions
# =============================================================================

def _get_medic_stones_collection(user_id: str):
    """Get the medic_stones subcollection reference for a user."""
    return firestoreDB.collection("users").document(user_id).collection("medic_stones")


def _doc_to_medic_stone(doc, user_id: str) -> Optional[MedicStone]:
    """Convert a Firestore document to a MedicStone model."""
    if not doc.exists:
        return None
    
    data = doc.to_dict()
    return MedicStone(
        id=doc.id,
        user_id=user_id,
        symptom_name=data.get("symptom_name", ""),
        severity=data.get("severity", 1),
        description=data.get("description", ""),
        context=data.get("context", {}),
        trends=data.get("trends", []),
        reported_at=data.get("reported_at", datetime.now(timezone.utc)),
        created_at=data.get("created_at", datetime.now(timezone.utc)),
        updated_at=data.get("updated_at", datetime.now(timezone.utc)),
    )


# =============================================================================
# CRUD Operations
# =============================================================================

async def create_medic_stone(
    user_id: str,
    stone_data: MedicStoneCreate,
    auto_context: Optional[Dict] = None
) -> MedicStone:
    """
    Create a new medic stone for a user.
    
    Args:
        user_id: The user's ID
        stone_data: MedicStoneCreate with symptom details
        auto_context: Optional auto-collected context (e.g., from DataExtractor)
        
    Returns:
        Created MedicStone
    """
    collection = _get_medic_stones_collection(user_id)
    
    now = datetime.now(timezone.utc)
    reported_at = stone_data.reported_at or now
    
    # Merge provided context with auto-context
    context = {}
    if auto_context:
        context.update(auto_context)
    if stone_data.context:
        context.update(stone_data.context.to_dict())
    
    # Compute initial trends (will be enriched by PatternDetector)
    trends = []
    if stone_data.severity >= 4:
        trends.append("high_severity")
    
    doc_data = {
        "symptom_name": stone_data.symptom_name.lower().strip(),
        "severity": stone_data.severity,
        "description": stone_data.description or "",
        "context": context,
        "trends": trends,
        "reported_at": reported_at,
        "created_at": now,
        "updated_at": now,
    }
    
    _, doc_ref = collection.add(doc_data)
    
    logger.info(f"Created medic stone for user {user_id}: {stone_data.symptom_name}")
    
    return MedicStone(
        id=doc_ref.id,
        user_id=user_id,
        symptom_name=doc_data["symptom_name"],
        severity=doc_data["severity"],
        description=doc_data["description"],
        context=doc_data["context"],
        trends=doc_data["trends"],
        reported_at=reported_at,
        created_at=now,
        updated_at=now,
    )


async def get_medic_stone(user_id: str, stone_id: str) -> Optional[MedicStone]:
    """Get a single medic stone by ID."""
    collection = _get_medic_stones_collection(user_id)
    doc = collection.document(stone_id).get()
    return _doc_to_medic_stone(doc, user_id)


async def get_medic_stones_by_range(
    user_id: str,
    start_date: datetime,
    end_date: datetime,
    symptom_name: Optional[str] = None
) -> List[MedicStone]:
    """
    Get medic stones within a date range.
    
    Args:
        user_id: The user's ID
        start_date: Start of date range (inclusive)
        end_date: End of date range (inclusive)
        symptom_name: Optional filter by symptom name
        
    Returns:
        List of MedicStone objects
    """
    collection = _get_medic_stones_collection(user_id)
    
    query = (
        collection
        .where("reported_at", ">=", start_date)
        .where("reported_at", "<=", end_date)
        .order_by("reported_at", direction="DESCENDING")
    )
    
    stones = []
    for doc in query.stream():
        stone = _doc_to_medic_stone(doc, user_id)
        if stone:
            if symptom_name is None or stone.symptom_name == symptom_name.lower().strip():
                stones.append(stone)
    
    return stones


async def get_recent_medic_stones(
    user_id: str,
    days: int = 7,
    limit: int = 50
) -> List[MedicStone]:
    """Get medic stones from the last N days."""
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    
    collection = _get_medic_stones_collection(user_id)
    
    query = (
        collection
        .where("reported_at", ">=", start_date)
        .order_by("reported_at", direction="DESCENDING")
        .limit(limit)
    )
    
    stones = []
    for doc in query.stream():
        stone = _doc_to_medic_stone(doc, user_id)
        if stone:
            stones.append(stone)
    
    return stones


async def update_medic_stone(
    user_id: str,
    stone_id: str,
    stone_data: MedicStoneUpdate
) -> Optional[MedicStone]:
    """Update an existing medic stone."""
    collection = _get_medic_stones_collection(user_id)
    doc_ref = collection.document(stone_id)
    
    if not doc_ref.get().exists:
        return None
    
    update_data = {"updated_at": datetime.now(timezone.utc)}
    
    if stone_data.symptom_name is not None:
        update_data["symptom_name"] = stone_data.symptom_name.lower().strip()
    if stone_data.severity is not None:
        update_data["severity"] = stone_data.severity
    if stone_data.description is not None:
        update_data["description"] = stone_data.description
    if stone_data.context is not None:
        update_data["context"] = stone_data.context.to_dict()
    
    doc_ref.update(update_data)
    
    updated_doc = doc_ref.get()
    return _doc_to_medic_stone(updated_doc, user_id)


async def delete_medic_stone(user_id: str, stone_id: str) -> bool:
    """Delete a medic stone."""
    collection = _get_medic_stones_collection(user_id)
    doc_ref = collection.document(stone_id)
    
    if not doc_ref.get().exists:
        return False
    
    doc_ref.delete()
    return True


# =============================================================================
# Analysis Functions
# =============================================================================

async def get_symptom_frequency(
    user_id: str,
    symptom_name: str,
    days: int = 30
) -> Optional[SymptomFrequency]:
    """
    Get frequency analysis for a specific symptom.
    
    Args:
        user_id: The user's ID
        symptom_name: Name of the symptom to analyze
        days: Number of days to analyze
        
    Returns:
        SymptomFrequency analysis or None if no data
    """
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    
    stones = await get_medic_stones_by_range(
        user_id, start_date, end_date, symptom_name
    )
    
    if not stones:
        return None
    
    # Calculate metrics
    total = len(stones)
    severities = [s.severity for s in stones]
    avg_severity = sum(severities) / total
    
    first_reported = min(s.reported_at for s in stones)
    last_reported = max(s.reported_at for s in stones)
    
    weeks = max(1, days / 7)
    frequency_per_week = total / weeks
    
    # Determine trend by comparing first half vs second half severities
    mid_point = len(stones) // 2
    if mid_point > 0:
        first_half_avg = sum(severities[:mid_point]) / mid_point
        second_half_avg = sum(severities[mid_point:]) / (len(severities) - mid_point)
        
        if second_half_avg > first_half_avg + 0.5:
            severity_trend = "increasing"
        elif second_half_avg < first_half_avg - 0.5:
            severity_trend = "decreasing"
        else:
            severity_trend = "stable"
    else:
        severity_trend = "stable"
    
    return SymptomFrequency(
        symptom_name=symptom_name,
        total_occurrences=total,
        avg_severity=round(avg_severity, 2),
        first_reported=first_reported,
        last_reported=last_reported,
        frequency_per_week=round(frequency_per_week, 2),
        severity_trend=severity_trend
    )


async def get_all_symptom_frequencies(
    user_id: str,
    days: int = 30
) -> List[SymptomFrequency]:
    """Get frequency analysis for all symptoms reported by user."""
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    
    all_stones = await get_medic_stones_by_range(user_id, start_date, end_date)
    
    # Group by symptom
    symptom_groups: Dict[str, List[MedicStone]] = {}
    for stone in all_stones:
        if stone.symptom_name not in symptom_groups:
            symptom_groups[stone.symptom_name] = []
        symptom_groups[stone.symptom_name].append(stone)
    
    frequencies = []
    for symptom_name in symptom_groups:
        freq = await get_symptom_frequency(user_id, symptom_name, days)
        if freq:
            frequencies.append(freq)
    
    # Sort by frequency
    frequencies.sort(key=lambda x: x.total_occurrences, reverse=True)
    
    return frequencies
