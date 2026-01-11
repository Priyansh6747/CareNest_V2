"""
Nutrition Storage Module - CRUD operations for meal data

Manages meals as a subcollection under each user document.
Fields:
- name: str (meal name)
- desc: str (description)
- amnt: float (amount in grams)
- analysis: dict (nutrient breakdown - Protein, Fiber, Iron, Vitamin D, Omega-3, EPA, DHA)
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

class NutrientAnalysis(BaseModel):
    """Nutrient analysis data for a meal."""
    protein: float = Field(default=0.0, description="Protein in grams")
    fiber: float = Field(default=0.0, description="Fiber in grams")
    iron: float = Field(default=0.0, description="Iron in grams")
    vitamin_d: float = Field(default=0.0, description="Vitamin D in mcg")
    omega_3: float = Field(default=0.0, description="Omega-3 in grams")
    omega_3_epa: float = Field(default=0.0, description="Omega-3 EPA in grams")
    omega_3_dha: float = Field(default=0.0, description="Omega-3 DHA in grams")


class MealCreate(BaseModel):
    """Input model for creating a meal."""
    name: str = Field(..., min_length=1, description="Meal name")
    desc: Optional[str] = Field(default="", description="Meal description")
    amnt: float = Field(..., gt=0, description="Amount in grams")
    analysis: NutrientAnalysis


class MealUpdate(BaseModel):
    """Input model for updating a meal (all fields optional)."""
    name: Optional[str] = Field(default=None, min_length=1)
    desc: Optional[str] = None
    amnt: Optional[float] = Field(default=None, gt=0)
    analysis: Optional[NutrientAnalysis] = None


class Meal(BaseModel):
    """Complete meal model with ID and timestamps."""
    id: str
    name: str
    desc: str
    amnt: float
    analysis: NutrientAnalysis
    created_at: datetime
    updated_at: datetime


# ============================================================================
# Helper Functions
# ============================================================================

def _get_meals_collection(user_id: str):
    """Get the meals subcollection reference for a user."""
    return firestoreDB.collection("users").document(user_id).collection("meals")


def _doc_to_meal(doc) -> Optional[Meal]:
    """Convert a Firestore document to a Meal model."""
    if not doc.exists:
        return None
    
    data = doc.to_dict()
    return Meal(
        id=doc.id,
        name=data.get("name", ""),
        desc=data.get("desc", ""),
        amnt=data.get("amnt", 0.0),
        analysis=NutrientAnalysis(**data.get("analysis", {})),
        created_at=data.get("created_at", datetime.now(timezone.utc)),
        updated_at=data.get("updated_at", datetime.now(timezone.utc)),
    )


# ============================================================================
# CRUD Operations
# ============================================================================

async def create_meal(user_id: str, meal_data: MealCreate) -> Meal:
    """
    Create a new meal for a user.
    
    Args:
        user_id: The user's ID
        meal_data: MealCreate containing name, desc, amnt, and analysis
        
    Returns:
        Created Meal with ID and timestamps
    """
    meals_collection = _get_meals_collection(user_id)
    
    now = datetime.now(timezone.utc)
    doc_data = {
        "name": meal_data.name,
        "desc": meal_data.desc or "",
        "amnt": meal_data.amnt,
        "analysis": meal_data.analysis.model_dump(),
        "created_at": now,
        "updated_at": now,
    }
    
    _, meal_ref = meals_collection.add(doc_data)
    
    return Meal(
        id=meal_ref.id,
        name=doc_data["name"],
        desc=doc_data["desc"],
        amnt=doc_data["amnt"],
        analysis=meal_data.analysis,
        created_at=now,
        updated_at=now,
    )


async def get_meal(user_id: str, meal_id: str) -> Optional[Meal]:
    """
    Get a single meal by ID.
    
    Args:
        user_id: The user's ID
        meal_id: The meal's ID
        
    Returns:
        Meal if found, None otherwise
    """
    meals_collection = _get_meals_collection(user_id)
    doc = meals_collection.document(meal_id).get()
    return _doc_to_meal(doc)


async def get_all_meals(
    user_id: str,
    limit: int = 50,
    order_by: str = "created_at",
    descending: bool = True
) -> List[Meal]:
    """
    Get all meals for a user with optional ordering and limit.
    
    Args:
        user_id: The user's ID
        limit: Maximum number of meals to return (default: 50)
        order_by: Field to order by (default: created_at)
        descending: Sort descending if True (default: True)
        
    Returns:
        List of Meal objects
    """
    meals_collection = _get_meals_collection(user_id)
    
    from google.cloud.firestore_v1 import Query
    direction = Query.DESCENDING if descending else Query.ASCENDING
    
    query = meals_collection.order_by(order_by, direction=direction).limit(limit)
    
    meals = []
    for doc in query.stream():
        meal = _doc_to_meal(doc)
        if meal:
            meals.append(meal)
    
    return meals


async def get_meals_by_date_range(
    user_id: str,
    start_date: datetime,
    end_date: datetime
) -> List[Meal]:
    """
    Get meals within a date range.
    
    Args:
        user_id: The user's ID
        start_date: Start of date range (inclusive)
        end_date: End of date range (inclusive)
        
    Returns:
        List of Meal objects within the date range
    """
    meals_collection = _get_meals_collection(user_id)
    
    query = (
        meals_collection
        .where("created_at", ">=", start_date)
        .where("created_at", "<=", end_date)
        .order_by("created_at")
    )
    
    meals = []
    for doc in query.stream():
        meal = _doc_to_meal(doc)
        if meal:
            meals.append(meal)
    
    return meals


async def update_meal(
    user_id: str,
    meal_id: str,
    meal_data: MealUpdate
) -> Optional[Meal]:
    """
    Update an existing meal.
    
    Args:
        user_id: The user's ID
        meal_id: The meal's ID
        meal_data: MealUpdate with fields to update
        
    Returns:
        Updated Meal if found, None otherwise
    """
    meals_collection = _get_meals_collection(user_id)
    meal_ref = meals_collection.document(meal_id)
    
    # Check if meal exists
    existing_doc = meal_ref.get()
    if not existing_doc.exists:
        return None
    
    # Build update data (only non-None fields)
    update_data = {"updated_at": datetime.now(timezone.utc)}
    
    if meal_data.name is not None:
        update_data["name"] = meal_data.name
    if meal_data.desc is not None:
        update_data["desc"] = meal_data.desc
    if meal_data.amnt is not None:
        update_data["amnt"] = meal_data.amnt
    if meal_data.analysis is not None:
        update_data["analysis"] = meal_data.analysis.model_dump()
    
    meal_ref.update(update_data)
    
    # Return updated meal
    updated_doc = meal_ref.get()
    return _doc_to_meal(updated_doc)


async def delete_meal(user_id: str, meal_id: str) -> bool:
    """
    Delete a meal.
    
    Args:
        user_id: The user's ID
        meal_id: The meal's ID
        
    Returns:
        True if deleted, False if meal didn't exist
    """
    meals_collection = _get_meals_collection(user_id)
    meal_ref = meals_collection.document(meal_id)
    
    # Check if exists before deleting
    if not meal_ref.get().exists:
        return False
    
    meal_ref.delete()
    return True


async def delete_all_meals(user_id: str) -> int:
    """
    Delete all meals for a user.
    
    Args:
        user_id: The user's ID
        
    Returns:
        Number of meals deleted
    """
    meals_collection = _get_meals_collection(user_id)
    
    count = 0
    for doc in meals_collection.stream():
        doc.reference.delete()
        count += 1
    
    return count


# ============================================================================
# Aggregate Functions
# ============================================================================

async def get_daily_nutrition_summary(
    user_id: str,
    date: datetime
) -> NutrientAnalysis:
    """
    Get aggregated nutrition for a specific day.
    
    Args:
        user_id: The user's ID
        date: The date to get summary for
        
    Returns:
        NutrientAnalysis with totals for the day
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
    
    meals = await get_meals_by_date_range(user_id, start_of_day, end_of_day)
    
    # Aggregate nutrients
    totals = {
        "protein": 0.0,
        "fiber": 0.0,
        "iron": 0.0,
        "vitamin_d": 0.0,
        "omega_3": 0.0,
        "omega_3_epa": 0.0,
        "omega_3_dha": 0.0,
    }
    
    for meal in meals:
        totals["protein"] += meal.analysis.protein
        totals["fiber"] += meal.analysis.fiber
        totals["iron"] += meal.analysis.iron
        totals["vitamin_d"] += meal.analysis.vitamin_d
        totals["omega_3"] += meal.analysis.omega_3
        totals["omega_3_epa"] += meal.analysis.omega_3_epa
        totals["omega_3_dha"] += meal.analysis.omega_3_dha
    
    return NutrientAnalysis(**totals)


async def count_meals(user_id: str) -> int:
    """
    Count total meals for a user.
    
    Args:
        user_id: The user's ID
        
    Returns:
        Total number of meals
    """
    meals_collection = _get_meals_collection(user_id)
    return len(list(meals_collection.stream()))