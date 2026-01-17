"""
Symptoms router - endpoints for symptom reporting and tracking (MedicStones)
"""
from datetime import datetime, timezone, timedelta
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, status

from Core.Memory.SymptomMapper.MedicStone import (
    MedicStone,
    MedicStoneCreate,
    MedicStoneUpdate,
    SymptomFrequency,
    create_medic_stone,
    get_medic_stone,
    get_recent_medic_stones,
    get_medic_stones_by_range,
    update_medic_stone,
    delete_medic_stone,
    get_symptom_frequency,
    get_all_symptom_frequencies,
)


router = APIRouter(prefix="/symptoms", tags=["Symptoms"])


# ============================================================================
# Symptom CRUD Endpoints
# ============================================================================

@router.post(
    "/{user_id}",
    response_model=MedicStone,
    status_code=status.HTTP_201_CREATED,
    summary="Report a symptom",
    description="Create a new symptom report (MedicStone) for a user.",
)
async def report_symptom(user_id: str, symptom_data: MedicStoneCreate):
    """Report a new symptom with severity and optional context."""
    try:
        return await create_medic_stone(user_id, symptom_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to report symptom: {str(e)}"
        )


@router.get(
    "/{user_id}/{stone_id}",
    response_model=MedicStone,
    summary="Get a single symptom",
    description="Retrieve a specific symptom report by its ID.",
)
async def get_symptom(user_id: str, stone_id: str):
    """Get a single symptom report by ID."""
    stone = await get_medic_stone(user_id, stone_id)
    
    if stone is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Symptom not found: {stone_id}"
        )
    
    return stone


@router.get(
    "/{user_id}",
    response_model=List[MedicStone],
    summary="Get recent symptoms",
    description="Get recent symptom reports for a user.",
)
async def get_symptoms(
    user_id: str,
    days: int = Query(default=7, ge=1, le=90, description="Number of days to look back"),
    limit: int = Query(default=50, ge=1, le=100, description="Max symptoms to return"),
):
    """Get recent symptoms for a user."""
    try:
        return await get_recent_medic_stones(user_id, days=days, limit=limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch symptoms: {str(e)}"
        )


@router.get(
    "/{user_id}/range",
    response_model=List[MedicStone],
    summary="Get symptoms by date range",
    description="Get symptoms within a specified date range.",
)
async def get_symptoms_by_range(
    user_id: str,
    start_date: datetime = Query(..., description="Start date (ISO format)"),
    end_date: datetime = Query(..., description="End date (ISO format)"),
    symptom_name: Optional[str] = Query(default=None, description="Filter by symptom name"),
):
    """Get symptoms within a date range."""
    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date must be before end_date"
        )
    
    try:
        return await get_medic_stones_by_range(user_id, start_date, end_date, symptom_name)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch symptoms: {str(e)}"
        )


@router.patch(
    "/{user_id}/{stone_id}",
    response_model=MedicStone,
    summary="Update a symptom",
    description="Partially update an existing symptom report.",
)
async def update_symptom(user_id: str, stone_id: str, symptom_data: MedicStoneUpdate):
    """Update an existing symptom report."""
    updated = await update_medic_stone(user_id, stone_id, symptom_data)
    
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Symptom not found: {stone_id}"
        )
    
    return updated


@router.delete(
    "/{user_id}/{stone_id}",
    summary="Delete a symptom",
    description="Delete a specific symptom report by ID.",
)
async def delete_symptom(user_id: str, stone_id: str):
    """Delete a symptom report."""
    success = await delete_medic_stone(user_id, stone_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Symptom not found: {stone_id}"
        )
    
    return {"message": "Symptom deleted successfully", "stone_id": stone_id}


# ============================================================================
# Symptom Analysis Endpoints
# ============================================================================

@router.get(
    "/{user_id}/analysis/all",
    response_model=List[SymptomFrequency],
    summary="Get all symptom frequencies",
    description="Get frequency analysis for all symptoms reported by user.",
)
async def get_all_analysis(
    user_id: str,
    days: int = Query(default=30, ge=1, le=90, description="Number of days to analyze"),
):
    """Get frequency analysis for all symptoms."""
    try:
        return await get_all_symptom_frequencies(user_id, days=days)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze symptoms: {str(e)}"
        )


@router.get(
    "/{user_id}/analysis/{symptom_name}",
    response_model=SymptomFrequency,
    summary="Analyze specific symptom",
    description="Get frequency analysis for a specific symptom.",
)
async def get_specific_analysis(
    user_id: str,
    symptom_name: str,
    days: int = Query(default=30, ge=1, le=90, description="Number of days to analyze"),
):
    """Get frequency analysis for a specific symptom."""
    try:
        result = await get_symptom_frequency(user_id, symptom_name, days=days)
        
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No data found for symptom: {symptom_name}"
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze symptom: {str(e)}"
        )
