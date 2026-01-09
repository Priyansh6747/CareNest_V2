
from datetime import datetime, timezone
from typing import Optional

from config import (
    users_collection,
    maternal_profiles_collection,
    baby_profiles_collection,
    user_consent_collection,
    onboarding_status_collection,
)
from schema import (
    OnboardingInitRequest,
    OnboardingInitResponse,
    OnboardingSteps,
    PregnancyStage,
)


async def init_onboarding(request: OnboardingInitRequest) -> OnboardingInitResponse:
    """
    Initialize onboarding for a new user.
    
    Creates:
    - User
    - MaternalProfile
    - UserConsent
    - OnboardingStatus
    - BabyProfile (optional, if provided)
    
    Supports idempotent upsert: if phone already exists, updates existing records.
    
    Args:
        request: OnboardingInitRequest containing user, maternal, consent, and optional baby data
        
    Returns:
        OnboardingInitResponse with created IDs, steps, completion status, and next action
    """
    
    # Check if user already exists (idempotent upsert by phone)
    existing_user = None
    user_id = None
    
    if request.user.phone:
        # Query Firestore for existing user by phone
        query = users_collection.where("phone", "==", request.user.phone).limit(1)
        docs = query.stream()
        for doc in docs:
            existing_user = doc
            user_id = doc.id
            break
    
    if existing_user:
        # Update existing user data
        users_collection.document(user_id).update({
            "email": request.user.email,
            "role": request.user.role.value,
        })
    else:
        # Create new user
        user_doc = {
            "phone": request.user.phone,
            "email": request.user.email,
            "role": request.user.role.value,
            "created_at": datetime.now(timezone.utc),
        }
        _, user_ref = users_collection.add(user_doc)
        user_id = user_ref.id
    
    # Upsert MaternalProfile
    maternal_doc = {
        "user_id": user_id,
        "personal": request.maternal.personal.model_dump(),
        "pregnancy": request.maternal.pregnancy.model_dump(mode="json"),
        "diet": request.maternal.diet.model_dump(by_alias=True),
        "created_at": datetime.now(timezone.utc),
    }
    
    # Check for existing maternal profile
    maternal_id = None
    query = maternal_profiles_collection.where("user_id", "==", user_id).limit(1)
    for doc in query.stream():
        maternal_id = doc.id
        break
    
    if maternal_id:
        maternal_profiles_collection.document(maternal_id).update(maternal_doc)
    else:
        _, maternal_ref = maternal_profiles_collection.add(maternal_doc)
        maternal_id = maternal_ref.id
    
    # Upsert UserConsent
    consent_valid = (
        request.consent.consents.data_usage and 
        request.consent.consents.medical_disclaimer
    )
    
    consent_doc = {
        "user_id": user_id,
        "consents": request.consent.consents.model_dump(),
        "accepted_at": datetime.now(timezone.utc) if consent_valid else None,
    }
    
    consent_id = None
    query = user_consent_collection.where("user_id", "==", user_id).limit(1)
    for doc in query.stream():
        consent_id = doc.id
        break
    
    if consent_id:
        user_consent_collection.document(consent_id).update(consent_doc)
    else:
        _, consent_ref = user_consent_collection.add(consent_doc)
        consent_id = consent_ref.id
    
    # Handle optional BabyProfile
    baby_id: Optional[str] = None
    if request.baby:
        baby_doc = {
            "maternal_id": maternal_id,
            "profile": request.baby.profile.model_dump(mode="json"),
            "feeding": request.baby.feeding.model_dump(by_alias=True),
            "created_at": datetime.now(timezone.utc),
        }
        
        # Check for existing baby profile
        query = baby_profiles_collection.where("maternal_id", "==", maternal_id).limit(1)
        for doc in query.stream():
            baby_id = doc.id
            break
        
        if baby_id:
            baby_profiles_collection.document(baby_id).update(baby_doc)
        else:
            _, baby_ref = baby_profiles_collection.add(baby_doc)
            baby_id = baby_ref.id
    
    # Build OnboardingSteps
    steps = OnboardingSteps(
        maternal_profile=True,  # Always true since maternal data is required
        baby_profile=baby_id is not None,
        consent=consent_valid,
    )
    
    # Determine completion status
    # Completed if: maternal profile exists + consent given
    # Baby is optional
    completed = steps.maternal_profile and steps.consent
    
    # Determine next action
    next_action = _determine_next_action(
        consent_valid=consent_valid,
        has_baby=baby_id is not None,
        pregnancy_stage=request.maternal.pregnancy.stage,
    )
    
    # Upsert OnboardingStatus
    onboarding_doc = {
        "user_id": user_id,
        "steps": steps.model_dump(),
        "completed_at": datetime.now(timezone.utc) if completed else None,
    }
    
    onboarding_status_id = None
    query = onboarding_status_collection.where("user_id", "==", user_id).limit(1)
    for doc in query.stream():
        onboarding_status_id = doc.id
        break
    
    if onboarding_status_id:
        onboarding_status_collection.document(onboarding_status_id).update(onboarding_doc)
    else:
        _, onboarding_ref = onboarding_status_collection.add(onboarding_doc)
        onboarding_status_id = onboarding_ref.id
    
    return OnboardingInitResponse(
        user_id=user_id,
        maternal_id=maternal_id,
        baby_id=baby_id,
        onboarding_status_id=onboarding_status_id,
        consent_id=consent_id,
        steps=steps,
        completed=completed,
        next_action=next_action,
    )


def _determine_next_action(
    consent_valid: bool,
    has_baby: bool,
    pregnancy_stage: PregnancyStage,
) -> str:
    """
    Determine the next action for the user based on their onboarding state.
    
    Priority:
    1. Accept consent if not given
    2. Add baby if postpartum and no baby added
    3. Go to dashboard
    """
    if not consent_valid:
        return "ACCEPT_CONSENT"
    
    # If postpartum and no baby, suggest adding baby info
    if pregnancy_stage == PregnancyStage.postpartum and not has_baby:
        return "ADD_BABY_OR_SKIP"
    
    return "GO_TO_DASHBOARD"


async def get_onboarding_status(user_id: str) -> Optional[dict]:
    """
    Get the current onboarding status for a user.
    
    Args:
        user_id: The user's ID
        
    Returns:
        Onboarding status document or None if not found
    """
    query = onboarding_status_collection.where("user_id", "==", user_id).limit(1)
    for doc in query.stream():
        data = doc.to_dict()
        data["_id"] = doc.id
        return data
    return None


async def update_onboarding_step(user_id: str, step: str, value: bool) -> bool:
    """
    Update a specific onboarding step for a user.
    
    Args:
        user_id: The user's ID
        step: The step to update (maternal_profile, baby_profile, consent)
        value: The new value for the step
        
    Returns:
        True if update was successful, False otherwise
    """
    valid_steps = {"maternal_profile", "baby_profile", "consent"}
    if step not in valid_steps:
        return False
    
    # Find the onboarding status document
    query = onboarding_status_collection.where("user_id", "==", user_id).limit(1)
    for doc in query.stream():
        onboarding_status_collection.document(doc.id).update({
            f"steps.{step}": value
        })
        return True
    
    return False


async def mark_onboarding_complete(user_id: str) -> bool:
    """
    Mark onboarding as complete for a user.
    
    Args:
        user_id: The user's ID
        
    Returns:
        True if update was successful, False otherwise
    """
    query = onboarding_status_collection.where("user_id", "==", user_id).limit(1)
    for doc in query.stream():
        onboarding_status_collection.document(doc.id).update({
            "completed_at": datetime.now(timezone.utc)
        })
        return True
    
    return False