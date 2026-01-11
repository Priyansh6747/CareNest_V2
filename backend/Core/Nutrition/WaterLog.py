"""
Water Log Module - CRUD operations for water intake tracking

Manages water logs as a subcollection under each user document.
Fields:
- amount_ml: float (amount in milliliters)
- note: str (optional note, e.g., "morning", "with meal")
- created_at: datetime
- updated_at: datetime
"""

from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel, Field

from config import firestoreDB


# ============================================================================
# Pydantic Models
# ============================================================================

class WaterLogCreate(BaseModel):
    """Input model for creating a water log entry."""
    amount_ml: float = Field(..., gt=0, description="Amount of water in milliliters")
    note: Optional[str] = Field(default="", description="Optional note (e.g., 'morning', 'with meal')")


class WaterLogUpdate(BaseModel):
    """Input model for updating a water log entry (all fields optional)."""
    amount_ml: Optional[float] = Field(default=None, gt=0)
    note: Optional[str] = None


class WaterLog(BaseModel):
    """Complete water log model with ID and timestamps."""
    id: str
    amount_ml: float
    note: str
    created_at: datetime
    updated_at: datetime


class DailyWaterSummary(BaseModel):
    """Daily water intake summary."""
    date: datetime
    total_ml: float
    log_count: int
    goal_ml: float = Field(default=2500.0, description="Daily water intake goal in ml")
    progress_percentage: float = Field(default=0.0, description="Percentage of goal achieved")


# ============================================================================
# Helper Functions
# ============================================================================

def _get_water_logs_collection(user_id: str):
    """Get the water_logs subcollection reference for a user."""
    return firestoreDB.collection("users").document(user_id).collection("water_logs")


def _doc_to_water_log(doc) -> Optional[WaterLog]:
    """Convert a Firestore document to a WaterLog model."""
    if not doc.exists:
        return None
    
    data = doc.to_dict()
    return WaterLog(
        id=doc.id,
        amount_ml=data.get("amount_ml", 0.0),
        note=data.get("note", ""),
        created_at=data.get("created_at", datetime.now(timezone.utc)),
        updated_at=data.get("updated_at", datetime.now(timezone.utc)),
    )


# ============================================================================
# CRUD Operations
# ============================================================================

async def create_water_log(user_id: str, log_data: WaterLogCreate) -> WaterLog:
    """
    Create a new water log entry for a user.
    
    Args:
        user_id: The user's ID
        log_data: WaterLogCreate containing amount_ml and optional note
        
    Returns:
        Created WaterLog with ID and timestamps
    """
    water_logs_collection = _get_water_logs_collection(user_id)
    
    now = datetime.now(timezone.utc)
    doc_data = {
        "amount_ml": log_data.amount_ml,
        "note": log_data.note or "",
        "created_at": now,
        "updated_at": now,
    }
    
    _, log_ref = water_logs_collection.add(doc_data)
    
    return WaterLog(
        id=log_ref.id,
        amount_ml=doc_data["amount_ml"],
        note=doc_data["note"],
        created_at=now,
        updated_at=now,
    )


async def get_water_log(user_id: str, log_id: str) -> Optional[WaterLog]:
    """
    Get a single water log entry by ID.
    
    Args:
        user_id: The user's ID
        log_id: The water log's ID
        
    Returns:
        WaterLog if found, None otherwise
    """
    water_logs_collection = _get_water_logs_collection(user_id)
    doc = water_logs_collection.document(log_id).get()
    return _doc_to_water_log(doc)


async def get_all_water_logs(
    user_id: str,
    limit: int = 50,
    order_by: str = "created_at",
    descending: bool = True
) -> List[WaterLog]:
    """
    Get all water logs for a user with optional ordering and limit.
    
    Args:
        user_id: The user's ID
        limit: Maximum number of logs to return (default: 50)
        order_by: Field to order by (default: created_at)
        descending: Sort descending if True (default: True)
        
    Returns:
        List of WaterLog objects
    """
    water_logs_collection = _get_water_logs_collection(user_id)
    
    from google.cloud.firestore_v1 import Query
    direction = Query.DESCENDING if descending else Query.ASCENDING
    
    query = water_logs_collection.order_by(order_by, direction=direction).limit(limit)
    
    logs = []
    for doc in query.stream():
        log = _doc_to_water_log(doc)
        if log:
            logs.append(log)
    
    return logs


async def get_water_logs_by_date_range(
    user_id: str,
    start_date: datetime,
    end_date: datetime
) -> List[WaterLog]:
    """
    Get water logs within a date range.
    
    Args:
        user_id: The user's ID
        start_date: Start of date range (inclusive)
        end_date: End of date range (inclusive)
        
    Returns:
        List of WaterLog objects within the date range
    """
    water_logs_collection = _get_water_logs_collection(user_id)
    
    query = (
        water_logs_collection
        .where("created_at", ">=", start_date)
        .where("created_at", "<=", end_date)
        .order_by("created_at")
    )
    
    logs = []
    for doc in query.stream():
        log = _doc_to_water_log(doc)
        if log:
            logs.append(log)
    
    return logs


async def update_water_log(
    user_id: str,
    log_id: str,
    log_data: WaterLogUpdate
) -> Optional[WaterLog]:
    """
    Update an existing water log entry.
    
    Args:
        user_id: The user's ID
        log_id: The water log's ID
        log_data: WaterLogUpdate with fields to update
        
    Returns:
        Updated WaterLog if found, None otherwise
    """
    water_logs_collection = _get_water_logs_collection(user_id)
    log_ref = water_logs_collection.document(log_id)
    
    # Check if log exists
    existing_doc = log_ref.get()
    if not existing_doc.exists:
        return None
    
    # Build update data (only non-None fields)
    update_data = {"updated_at": datetime.now(timezone.utc)}
    
    if log_data.amount_ml is not None:
        update_data["amount_ml"] = log_data.amount_ml
    if log_data.note is not None:
        update_data["note"] = log_data.note
    
    log_ref.update(update_data)
    
    # Return updated log
    updated_doc = log_ref.get()
    return _doc_to_water_log(updated_doc)


async def delete_water_log(user_id: str, log_id: str) -> bool:
    """
    Delete a water log entry.
    
    Args:
        user_id: The user's ID
        log_id: The water log's ID
        
    Returns:
        True if deleted, False if log didn't exist
    """
    water_logs_collection = _get_water_logs_collection(user_id)
    log_ref = water_logs_collection.document(log_id)
    
    # Check if exists before deleting
    if not log_ref.get().exists:
        return False
    
    log_ref.delete()
    return True


async def delete_all_water_logs(user_id: str) -> int:
    """
    Delete all water logs for a user.
    
    Args:
        user_id: The user's ID
        
    Returns:
        Number of logs deleted
    """
    water_logs_collection = _get_water_logs_collection(user_id)
    
    count = 0
    for doc in water_logs_collection.stream():
        doc.reference.delete()
        count += 1
    
    return count


# ============================================================================
# Aggregate Functions
# ============================================================================

async def get_daily_water_summary(
    user_id: str,
    date: datetime,
    goal_ml: float = 2500.0
) -> DailyWaterSummary:
    """
    Get aggregated water intake for a specific day.
    
    Args:
        user_id: The user's ID
        date: The date to get summary for
        goal_ml: Daily water intake goal in ml (default: 2500ml)
        
    Returns:
        DailyWaterSummary with totals for the day
    """
    # Get start and end of day
    start_of_day = datetime(
        date.year, date.month, date.day, 
        0, 0, 0, 
        tzinfo=timezone.utc
    )
    end_of_day = datetime(
        date.year, date.month, date.day, 
        23, 59, 59, 999999,
        tzinfo=timezone.utc
    )
    
    logs = await get_water_logs_by_date_range(user_id, start_of_day, end_of_day)
    
    # Calculate totals
    total_ml = sum(log.amount_ml for log in logs)
    log_count = len(logs)
    progress_percentage = min((total_ml / goal_ml) * 100, 100.0) if goal_ml > 0 else 0.0
    
    return DailyWaterSummary(
        date=start_of_day,
        total_ml=total_ml,
        log_count=log_count,
        goal_ml=goal_ml,
        progress_percentage=round(progress_percentage, 2),
    )


async def count_water_logs(user_id: str) -> int:
    """
    Count total water log entries for a user.
    
    Args:
        user_id: The user's ID
        
    Returns:
        Total number of water logs
    """
    water_logs_collection = _get_water_logs_collection(user_id)
    return len(list(water_logs_collection.stream()))
