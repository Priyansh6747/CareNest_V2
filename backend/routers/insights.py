"""
Insights router - endpoints for nutrition insights generation with caching

Insights are stored as a subcollection under users/{user_id}/insights
and cached for 12 hours to avoid expensive regeneration.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from config import firestoreDB
from Core.Insights.InsightEngine import get_pregnancy_insights


router = APIRouter(prefix="/insights", tags=["Insights"])


# =============================================================================
# Constants
# =============================================================================

CACHE_DURATION_HOURS = 12
INSIGHTS_SUBCOLLECTION = "insights"


# =============================================================================
# Request/Response Models
# =============================================================================

class InsightRequest(BaseModel):
    """Request body for generating insights."""
    trimester: str  # trimester_1, trimester_2, trimester_3, postpartum
    age: int
    height_cm: float
    weight_kg: float
    activity_factor: float = 1.4
    forecast_days: int = 7
    context_days: int = 30
    force_regenerate: bool = False  # Skip cache and regenerate


class InsightResponse(BaseModel):
    """Response wrapper for insights."""
    user_id: str
    from_cache: bool
    cache_expires_at: Optional[str] = None
    generated_at: str
    insights: dict


# =============================================================================
# Storage Functions
# =============================================================================

async def get_cached_insights(user_id: str) -> Optional[dict]:
    """
    Get cached insights from Firestore.
    
    Returns None if no cache exists or cache is expired (>12 hours old).
    """
    try:
        # Get the latest insight document
        insights_ref = (
            firestoreDB
            .collection("users")
            .document(user_id)
            .collection(INSIGHTS_SUBCOLLECTION)
            .order_by("generated_at", direction="DESCENDING")
            .limit(1)
        )
        
        docs = insights_ref.get()
        
        for doc in docs:
            data = doc.to_dict()
            
            # Check if cache is still valid (within 12 hours)
            generated_at = data.get("generated_at")
            if generated_at:
                # Handle both string and datetime formats
                if isinstance(generated_at, str):
                    gen_time = datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
                else:
                    gen_time = generated_at
                
                # Make timezone-aware if needed
                if gen_time.tzinfo is None:
                    gen_time = gen_time.replace(tzinfo=timezone.utc)
                
                now = datetime.now(timezone.utc)
                age_hours = (now - gen_time).total_seconds() / 3600
                
                if age_hours < CACHE_DURATION_HOURS:
                    # Cache is valid
                    data["_id"] = doc.id
                    data["cache_age_hours"] = round(age_hours, 2)
                    return data
        
        return None
        
    except Exception as e:
        # Log but don't fail - just regenerate
        print(f"Cache lookup failed: {e}")
        return None


async def store_insights(user_id: str, insights: dict) -> str:
    """
    Store insights in Firestore as a subcollection under the user.
    
    Returns the document ID of the stored insight.
    """
    try:
        # Add to insights subcollection
        insights_ref = (
            firestoreDB
            .collection("users")
            .document(user_id)
            .collection(INSIGHTS_SUBCOLLECTION)
        )
        
        # Add timestamp if not present
        if "stored_at" not in insights:
            insights["stored_at"] = datetime.now(timezone.utc).isoformat()
        
        # Store as new document
        doc_ref = insights_ref.add(insights)
        
        # doc_ref is a tuple (timestamp, DocumentReference)
        return doc_ref[1].id
        
    except Exception as e:
        print(f"Failed to store insights: {e}")
        raise


async def cleanup_old_insights(user_id: str, keep_count: int = 5):
    """
    Clean up old insight documents, keeping only the most recent ones.
    
    Args:
        user_id: User ID
        keep_count: Number of recent documents to keep (default 5)
    """
    try:
        insights_ref = (
            firestoreDB
            .collection("users")
            .document(user_id)
            .collection(INSIGHTS_SUBCOLLECTION)
            .order_by("generated_at", direction="DESCENDING")
        )
        
        docs = list(insights_ref.get())
        
        # Delete documents beyond keep_count
        if len(docs) > keep_count:
            for doc in docs[keep_count:]:
                doc.reference.delete()
                
    except Exception as e:
        # Non-critical, just log
        print(f"Cleanup failed: {e}")


# =============================================================================
# Endpoints
# =============================================================================

@router.post(
    "/{user_id}",
    response_model=InsightResponse,
    summary="Get or generate nutrition insights",
    description="""
    Get nutrition insights for a user. 

    - If cached insights exist (less than 12 hours old), returns cached version.
    - If no cache or cache expired, generates new insights and stores them.
    - Use `force_regenerate=true` to skip cache and force regeneration.
    
    Insights include:
    - Current nutrient status vs pregnancy RDAs
    - 7-day nutrient forecasts
    - Priority nutrients (biggest gaps)
    - Dietary recommendations
    - Tracking consistency score
    """,
)
async def get_or_generate_insights(user_id: str, request: InsightRequest):
    """Get cached insights or generate new ones."""
    
    # Step 1: Check cache (unless force_regenerate)
    if not request.force_regenerate:
        cached = await get_cached_insights(user_id)
        
        if cached:
            # Calculate expiry time
            generated_at = cached.get("generated_at", "")
            if isinstance(generated_at, str):
                gen_time = datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
            else:
                gen_time = generated_at
                
            if gen_time.tzinfo is None:
                gen_time = gen_time.replace(tzinfo=timezone.utc)
                
            expires_at = gen_time + timedelta(hours=CACHE_DURATION_HOURS)
            
            return InsightResponse(
                user_id=user_id,
                from_cache=True,
                cache_expires_at=expires_at.isoformat(),
                generated_at=generated_at if isinstance(generated_at, str) else generated_at.isoformat(),
                insights=cached
            )
    
    # Step 2: Generate new insights
    try:
        insights = await get_pregnancy_insights(
            user_id=user_id,
            trimester=request.trimester,
            age=request.age,
            height_cm=request.height_cm,
            weight_kg=request.weight_kg,
            activity_factor=request.activity_factor,
            forecast_days=request.forecast_days,
            context_days=request.context_days,
            use_chronos=True  # Try Chronos, fallback to simple if unavailable
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate insights: {str(e)}"
        )
    
    # Step 3: Store in Firestore
    try:
        doc_id = await store_insights(user_id, insights)
        insights["_doc_id"] = doc_id
    except Exception as e:
        # Log but don't fail - insights were generated successfully
        print(f"Warning: Failed to cache insights: {e}")
    
    # Step 4: Cleanup old documents (async, don't wait)
    try:
        await cleanup_old_insights(user_id)
    except:
        pass
    
    # Calculate expiry
    generated_at = insights.get("generated_at", datetime.now(timezone.utc).isoformat())
    if isinstance(generated_at, str):
        gen_time = datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
    else:
        gen_time = generated_at
        
    if gen_time.tzinfo is None:
        gen_time = gen_time.replace(tzinfo=timezone.utc)
        
    expires_at = gen_time + timedelta(hours=CACHE_DURATION_HOURS)
    
    return InsightResponse(
        user_id=user_id,
        from_cache=False,
        cache_expires_at=expires_at.isoformat(),
        generated_at=generated_at if isinstance(generated_at, str) else generated_at.isoformat(),
        insights=insights
    )


@router.get(
    "/{user_id}/latest",
    summary="Get latest cached insights",
    description="Get the most recent cached insights without regenerating. Returns 404 if no cache exists.",
)
async def get_latest_insights(user_id: str):
    """Get the latest cached insights without regenerating."""
    cached = await get_cached_insights(user_id)
    
    if cached is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No cached insights found for user: {user_id}. Use POST to generate."
        )
    
    # Calculate cache status
    generated_at = cached.get("generated_at", "")
    if isinstance(generated_at, str):
        gen_time = datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
    else:
        gen_time = generated_at
        
    if gen_time.tzinfo is None:
        gen_time = gen_time.replace(tzinfo=timezone.utc)
    
    now = datetime.now(timezone.utc)
    age_hours = (now - gen_time).total_seconds() / 3600
    expires_at = gen_time + timedelta(hours=CACHE_DURATION_HOURS)
    
    return {
        "user_id": user_id,
        "from_cache": True,
        "cache_age_hours": round(age_hours, 2),
        "cache_expires_at": expires_at.isoformat(),
        "cache_expired": age_hours >= CACHE_DURATION_HOURS,
        "generated_at": generated_at if isinstance(generated_at, str) else generated_at.isoformat(),
        "insights": cached
    }


@router.get(
    "/{user_id}/history",
    summary="Get insights history",
    description="Get all stored insight documents for a user (most recent first).",
)
async def get_insights_history(
    user_id: str,
    limit: int = Query(default=10, ge=1, le=50, description="Max documents to return")
):
    """Get historical insight documents."""
    try:
        insights_ref = (
            firestoreDB
            .collection("users")
            .document(user_id)
            .collection(INSIGHTS_SUBCOLLECTION)
            .order_by("generated_at", direction="DESCENDING")
            .limit(limit)
        )
        
        docs = insights_ref.get()
        
        history = []
        for doc in docs:
            data = doc.to_dict()
            data["_id"] = doc.id
            
            # Add age info
            generated_at = data.get("generated_at")
            if generated_at:
                if isinstance(generated_at, str):
                    gen_time = datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
                else:
                    gen_time = generated_at
                    
                if gen_time.tzinfo is None:
                    gen_time = gen_time.replace(tzinfo=timezone.utc)
                    
                now = datetime.now(timezone.utc)
                age_hours = (now - gen_time).total_seconds() / 3600
                data["age_hours"] = round(age_hours, 2)
            
            history.append(data)
        
        return {
            "user_id": user_id,
            "count": len(history),
            "history": history
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch insights history: {str(e)}"
        )


@router.delete(
    "/{user_id}",
    summary="Delete all cached insights",
    description="Delete all cached insight documents for a user.",
)
async def delete_all_insights(user_id: str):
    """Delete all insight documents for a user."""
    try:
        insights_ref = (
            firestoreDB
            .collection("users")
            .document(user_id)
            .collection(INSIGHTS_SUBCOLLECTION)
        )
        
        docs = insights_ref.get()
        deleted_count = 0
        
        for doc in docs:
            doc.reference.delete()
            deleted_count += 1
        
        return {
            "message": f"Deleted {deleted_count} insight documents",
            "user_id": user_id,
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete insights: {str(e)}"
        )
