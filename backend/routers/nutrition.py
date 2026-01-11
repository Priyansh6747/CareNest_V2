"""
Nutrition router - endpoints for meal CRUD and nutrition analysis
"""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, status

from Core.Nutrition.Storage import (
    Meal,
    MealCreate,
    MealUpdate,
    NutrientAnalysis,
    create_meal,
    get_meal,
    get_all_meals,
    get_meals_by_date_range,
    update_meal,
    delete_meal,
    delete_all_meals,
    get_daily_nutrition_summary,
    count_meals,
)


router = APIRouter(prefix="/nutrition", tags=["Nutrition"])


# ============================================================================
# Meal CRUD Endpoints
# ============================================================================

@router.post(
    "/meals/{user_id}",
    response_model=Meal,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new meal",
    description="Create a new meal entry with nutritional analysis for a user.",
)
async def create_user_meal(user_id: str, meal_data: MealCreate):
    """Create a new meal for the specified user."""
    try:
        return await create_meal(user_id, meal_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create meal: {str(e)}"
        )


@router.get(
    "/meals/{user_id}/{meal_id}",
    response_model=Meal,
    summary="Get a single meal",
    description="Retrieve a specific meal by its ID.",
)
async def get_user_meal(user_id: str, meal_id: str):
    """Get a single meal by ID."""
    meal = await get_meal(user_id, meal_id)
    
    if meal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Meal not found: {meal_id}"
        )
    
    return meal


@router.get(
    "/meals/{user_id}",
    response_model=List[Meal],
    summary="Get all meals",
    description="Get all meals for a user with optional pagination and ordering.",
)
async def get_user_meals(
    user_id: str,
    limit: int = Query(default=50, ge=1, le=100, description="Max meals to return"),
    order_by: str = Query(default="created_at", description="Field to order by"),
    descending: bool = Query(default=True, description="Sort descending"),
):
    """Get all meals for a user."""
    try:
        return await get_all_meals(user_id, limit=limit, order_by=order_by, descending=descending)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch meals: {str(e)}"
        )


@router.get(
    "/meals/{user_id}/range",
    response_model=List[Meal],
    summary="Get meals by date range",
    description="Get meals within a specified date range.",
)
async def get_user_meals_by_range(
    user_id: str,
    start_date: datetime = Query(..., description="Start date (ISO format)"),
    end_date: datetime = Query(..., description="End date (ISO format)"),
):
    """Get meals within a date range."""
    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date must be before end_date"
        )
    
    try:
        return await get_meals_by_date_range(user_id, start_date, end_date)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch meals: {str(e)}"
        )


@router.patch(
    "/meals/{user_id}/{meal_id}",
    response_model=Meal,
    summary="Update a meal",
    description="Partially update an existing meal.",
)
async def update_user_meal(user_id: str, meal_id: str, meal_data: MealUpdate):
    """Update an existing meal."""
    updated = await update_meal(user_id, meal_id, meal_data)
    
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Meal not found: {meal_id}"
        )
    
    return updated


@router.delete(
    "/meals/{user_id}/{meal_id}",
    summary="Delete a meal",
    description="Delete a specific meal by ID.",
)
async def delete_user_meal(user_id: str, meal_id: str):
    """Delete a meal."""
    success = await delete_meal(user_id, meal_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Meal not found: {meal_id}"
        )
    
    return {"message": "Meal deleted successfully", "meal_id": meal_id}


@router.delete(
    "/meals/{user_id}",
    summary="Delete all meals",
    description="Delete all meals for a user.",
)
async def delete_all_user_meals(user_id: str):
    """Delete all meals for a user."""
    count = await delete_all_meals(user_id)
    return {"message": f"Deleted {count} meals", "user_id": user_id, "deleted_count": count}


# ============================================================================
# Nutrition Summary Endpoints
# ============================================================================

@router.get(
    "/summary/{user_id}/daily",
    response_model=NutrientAnalysis,
    summary="Get daily nutrition summary",
    description="Get aggregated nutritional intake for a specific date.",
)
async def get_daily_summary(
    user_id: str,
    date: datetime = Query(..., description="Date to get summary for (ISO format)"),
):
    """Get daily nutrition summary."""
    try:
        return await get_daily_nutrition_summary(user_id, date)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get summary: {str(e)}"
        )


@router.get(
    "/stats/{user_id}/count",
    summary="Get meal count",
    description="Get total number of meals for a user.",
)
async def get_meal_count(user_id: str):
    """Get total meal count."""
    try:
        total = await count_meals(user_id)
        return {"user_id": user_id, "total_meals": total}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to count meals: {str(e)}"
        )
