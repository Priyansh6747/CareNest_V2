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


@router.get(
    "/profile/{user_id}",
    summary="Get user profile",
    description="Retrieve user's profile including maternal data and dietary preferences.",
)
async def get_user_profile(user_id: str):
    """
    Get the user's profile and dietary preferences.
    
    The user_id can be either:
    - Firebase Auth UID (from frontend)
    - Firestore document ID (from backend)
    
    Returns maternal profile data including:
    - Personal info (age, height, weight)
    - Pregnancy info (stage, risk level, known conditions)
    - Diet info (diet type: veg/non_veg/mixed, allergies)
    """
    from config import maternal_profiles_collection, users_collection
    
    import logging
    logger = logging.getLogger(__name__)

    try:
        profile_ref, profile_data = _get_maternal_profile_ref(user_id)
        
        # Extract key info for frontend
        personal = profile_data.get("personal", {})
        pregnancy = profile_data.get("pregnancy", {})
        diet = profile_data.get("diet", {})
        
        return {
            "user_id": user_id,
            "personal": {
                "age": personal.get("age"),
                "height_cm": personal.get("height_cm"),
                "weight_kg": personal.get("weight_kg"),
                "language": personal.get("language", "en"),
            },
            "pregnancy": {
                "stage": pregnancy.get("stage"),
                "risk_level": pregnancy.get("risk_level"),
                "known_conditions": pregnancy.get("known_conditions", []),
                "expected_delivery_date": str(pregnancy.get("expected_delivery_date", "")),
            },
            "diet": {
                "diet_type": diet.get("diet_type") or diet.get("type", "mixed"),
                "allergies": diet.get("allergies", []),
            },
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch user profile: {str(e)}"
        )


def _get_maternal_profile_ref(user_id: str):
    """
    Helper to find the maternal profile document reference and data.
    Returns (doc_ref, doc_data).
    Raises HTTPException if not found.
    """
    from config import maternal_profiles_collection, users_collection
    
    # Strategy 1: Try direct query with provided user_id
    maternal_docs = list(
        maternal_profiles_collection.where("user_id", "==", user_id).limit(1).stream()
    )
    
    # Strategy 2: If not found, try to find user doc by Firebase UID
    if not maternal_docs:
        try:
            user_doc = users_collection.document(user_id).get()
            if user_doc.exists:
                firestore_user_id = user_doc.id
                maternal_docs = list(
                    maternal_profiles_collection.where("user_id", "==", firestore_user_id).limit(1).stream()
                )
        except Exception:
            pass
    
    # Strategy 3: Check if maternal profile document ID matches user_id
    if not maternal_docs:
        try:
            maternal_doc = maternal_profiles_collection.document(user_id).get()
            if maternal_doc.exists:
                maternal_docs = [maternal_doc]
        except Exception:
            pass
    
    # Strategy 4: Search users by phone/email containing user_id pattern
    if not maternal_docs:
        user_query = list(users_collection.limit(50).stream())
        for user_doc in user_query:
            user_data = user_doc.to_dict()
            if user_data.get("firebase_uid") == user_id or user_data.get("uid") == user_id:
                maternal_docs = list(
                    maternal_profiles_collection.where("user_id", "==", user_doc.id).limit(1).stream()
                )
                if maternal_docs:
                    break
    
    if not maternal_docs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile not found for user: {user_id}"
        )
    
    return maternal_docs[0].reference, maternal_docs[0].to_dict()


# =============================================================================
# Allergy Management Endpoints
# =============================================================================

@router.get(
    "/allergies/{user_id}",
    summary="Get user allergies",
    description="Retrieve the list of allergies for a user.",
)
async def get_allergies(user_id: str):
    """Get list of allergies for a user."""
    try:
        _, profile_data = _get_maternal_profile_ref(user_id)
        diet = profile_data.get("diet", {})
        return {"allergies": diet.get("allergies", [])}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/allergies/{user_id}",
    summary="Add allergy",
    description="Add an allergy to the user's profile.",
)
async def add_allergy(user_id: str, allergy_name: str):
    """Add an allergy (prevents duplicates)."""
    try:
        doc_ref, profile_data = _get_maternal_profile_ref(user_id)
        diet = profile_data.get("diet", {})
        allergies = diet.get("allergies", [])
        
        clean_name = allergy_name.strip().title()
        if clean_name not in allergies:
            allergies.append(clean_name)
            diet["allergies"] = allergies
            doc_ref.update({"diet": diet})
            
        return {"allergies": allergies, "added": clean_name}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/allergies/{user_id}/{allergy_name}",
    summary="Remove allergy",
    description="Remove an allergy from the user's profile.",
)
async def remove_allergy(user_id: str, allergy_name: str):
    """Remove an allergy."""
    try:
        doc_ref, profile_data = _get_maternal_profile_ref(user_id)
        diet = profile_data.get("diet", {})
        allergies = diet.get("allergies", [])
        
        # Case insensitive removal
        original_len = len(allergies)
        allergies = [a for a in allergies if a.lower() != allergy_name.lower().strip()]
        
        if len(allergies) != original_len:
            diet["allergies"] = allergies
            doc_ref.update({"diet": diet})
            
        return {"allergies": allergies, "removed": allergy_name}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
