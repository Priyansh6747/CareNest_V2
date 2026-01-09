"""
User router - endpoints for user onboarding and management
"""
from typing import Optional

from fastapi import APIRouter, HTTPException, status

from schema import (
    OnboardingInitRequest,
    OnboardingInitResponse,
)
from Core.User.onbording import (
    init_onboarding,
    get_onboarding_status,
    update_onboarding_step,
    mark_onboarding_complete,
)


router = APIRouter(prefix="/user", tags=["User"])


@router.post(
    "/onboarding/init",
    response_model=OnboardingInitResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Initialize user onboarding",
    description="Creates User, MaternalProfile, UserConsent, OnboardingStatus, and optionally BabyProfile. Supports idempotent upsert by phone.",
)
async def initialize_onboarding(request: OnboardingInitRequest):
    """
    Initialize onboarding for a new user.
    
    Creates all required documents and returns created IDs,
    onboarding steps, completion status, and next action.
    """
    try:
        return await init_onboarding(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize onboarding: {str(e)}"
        )


@router.get(
    "/onboarding/status/{user_id}",
    summary="Get onboarding status",
    description="Retrieve the current onboarding status for a user.",
)
async def get_status(user_id: str):
    """
    Get the current onboarding status for a user.
    
    Returns the onboarding status document or 404 if not found.
    """
    status_doc = await get_onboarding_status(user_id)
    
    if status_doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Onboarding status not found for user: {user_id}"
        )
    
    # Convert ObjectId to string for JSON serialization
    status_doc["_id"] = str(status_doc["_id"])
    return status_doc


@router.patch(
    "/onboarding/step/{user_id}",
    summary="Update onboarding step",
    description="Update a specific onboarding step (maternal_profile, baby_profile, consent).",
)
async def update_step(user_id: str, step: str, value: bool):
    """
    Update a specific onboarding step for a user.
    
    Valid steps: maternal_profile, baby_profile, consent
    """
    success = await update_onboarding_step(user_id, step, value)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update step '{step}'. Invalid step name or user not found."
        )
    
    return {"message": f"Step '{step}' updated successfully", "user_id": user_id, "step": step, "value": value}


@router.post(
    "/onboarding/complete/{user_id}",
    summary="Mark onboarding complete",
    description="Mark onboarding as complete for a user.",
)
async def complete_onboarding(user_id: str):
    """
    Mark onboarding as complete for a user.
    
    Sets the completed_at timestamp to the current time.
    """
    success = await mark_onboarding_complete(user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found or onboarding already complete: {user_id}"
        )
    
    return {"message": "Onboarding marked as complete", "user_id": user_id}
