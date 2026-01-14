"""
Memory Router - API Endpoints for Memory Module

Provides endpoints for:
- Smart Retrieval System queries
- Symptom logging and tracking
- Context pyramid retrieval
- Doctor summary generation
"""

from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

# SRS imports
from Core.Memory.SRS import (
    get_retrieval_chain,
    get_registry,
    get_router,
    get_loader,
)

# SymptomMapper imports
from Core.Memory.SymptomMapper import (
    MedicStoneCreate,
    MedicStoneUpdate,
    create_medic_stone,
    get_medic_stone,
    get_recent_medic_stones,
    delete_medic_stone,
    get_all_symptom_frequencies,
    TimelineMapper,
    PatternDetector,
    DoctorSummaryGenerator,
)

# ContextPyramid imports
from Core.Memory.ContextPyramid import (
    PyramidManager,
    ContextLayer,
)


router = APIRouter(prefix="/memory", tags=["Memory"])


# =============================================================================
# Request/Response Models
# =============================================================================

class QueryRequest(BaseModel):
    """Request for SRS query."""
    query: str = Field(..., min_length=3, description="Search query")
    top_k_stores: int = Field(default=2, ge=1, le=5)
    top_k_chunks: int = Field(default=5, ge=1, le=20)
    include_context: bool = Field(default=True, description="Include user context")


class QueryResponse(BaseModel):
    """Response from SRS query."""
    query: str
    chunks: List[dict]
    stores_searched: List[str]
    retrieval_time_ms: float
    context: Optional[str] = None


class SymptomLogRequest(BaseModel):
    """Request for logging a symptom."""
    symptom_name: str = Field(..., min_length=1)
    severity: int = Field(..., ge=1, le=5)
    description: Optional[str] = None
    notes: Optional[str] = None


class ContextRequest(BaseModel):
    """Request for context pyramid."""
    query: Optional[str] = None
    max_tokens: int = Field(default=2000, ge=500, le=8000)
    layers: Optional[List[int]] = None  # Layer numbers to include


# =============================================================================
# SRS Endpoints
# =============================================================================

@router.post("/query", response_model=QueryResponse)
async def query_knowledge_base(request: QueryRequest, user_id: str = Query(...)):
    """
    Query the knowledge base using Smart Retrieval System.
    
    The SRS uses MiniLM to classify and route your query to the
    most relevant vector stores, then retrieves and ranks results.
    """
    try:
        chain = get_retrieval_chain()
        result = chain.retrieve(
            query=request.query,
            top_k_stores=request.top_k_stores,
            top_k_chunks=request.top_k_chunks
        )
        
        # Optionally include user context
        context = None
        if request.include_context:
            pyramid = PyramidManager(user_id)
            context = await pyramid.get_context_for_query(request.query, max_tokens=500)
        
        return QueryResponse(
            query=result.query,
            chunks=[c.to_dict() for c in result.chunks],
            stores_searched=result.stores_searched,
            retrieval_time_ms=result.retrieval_time_ms,
            context=context
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stores")
async def list_vector_stores():
    """List all available vector stores and their metadata."""
    try:
        registry = get_registry()
        return registry.get_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stores/loaded")
async def get_loaded_stores():
    """Get currently loaded vector stores in memory."""
    try:
        loader = get_loader()
        return loader.get_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/route")
async def explain_routing(query: str = Query(..., min_length=3)):
    """
    Explain how a query would be routed to vector stores.
    
    Useful for debugging and understanding the routing logic.
    """
    try:
        router_instance = get_router()
        return router_instance.explain_routing(query, top_k=5)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Symptom Endpoints
# =============================================================================

@router.post("/symptoms")
async def log_symptom(request: SymptomLogRequest, user_id: str = Query(...)):
    """
    Log a new symptom (creates a medic stone).
    
    Symptoms are tracked over time to detect patterns
    and generate doctor summaries.
    """
    try:
        from Core.Memory.SymptomMapper import SymptomContext
        
        context = None
        if request.notes:
            context = SymptomContext(notes=request.notes)
        
        stone_data = MedicStoneCreate(
            symptom_name=request.symptom_name,
            severity=request.severity,
            description=request.description,
            context=context
        )
        
        stone = await create_medic_stone(user_id, stone_data)
        return stone.to_dict()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/symptoms/{user_id}")
async def get_symptoms(
    user_id: str,
    days: int = Query(default=7, ge=1, le=90)
):
    """Get recent symptoms for a user."""
    try:
        stones = await get_recent_medic_stones(user_id, days=days)
        return {
            "user_id": user_id,
            "period_days": days,
            "count": len(stones),
            "symptoms": [s.to_dict() for s in stones]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/symptoms/{user_id}/timeline")
async def get_symptom_timeline(
    user_id: str,
    days: int = Query(default=30, ge=7, le=90)
):
    """Get symptom timeline with trends."""
    try:
        mapper = TimelineMapper(user_id)
        timeline = await mapper.build_timeline(days=days)
        return timeline.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/symptoms/{user_id}/patterns")
async def get_symptom_patterns(
    user_id: str,
    days: int = Query(default=60, ge=14, le=180)
):
    """Detect patterns in symptom history."""
    try:
        detector = PatternDetector(user_id)
        analysis = await detector.analyze(days=days)
        return analysis.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/symptoms/{user_id}/frequencies")
async def get_symptom_frequencies(
    user_id: str,
    days: int = Query(default=30, ge=7, le=90)
):
    """Get frequency analysis for all symptoms."""
    try:
        frequencies = await get_all_symptom_frequencies(user_id, days=days)
        return {
            "user_id": user_id,
            "period_days": days,
            "symptoms": [
                {
                    "name": f.symptom_name,
                    "occurrences": f.total_occurrences,
                    "avg_severity": round(f.avg_severity, 2),
                    "weekly_frequency": round(f.frequency_per_week, 2),
                    "trend": f.severity_trend
                }
                for f in frequencies
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/symptoms/{user_id}/{stone_id}")
async def remove_symptom(user_id: str, stone_id: str):
    """Delete a symptom record."""
    try:
        success = await delete_medic_stone(user_id, stone_id)
        if not success:
            raise HTTPException(status_code=404, detail="Symptom not found")
        return {"deleted": True, "stone_id": stone_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Doctor Summary Endpoints
# =============================================================================

@router.get("/doctor-summary/{user_id}")
async def generate_doctor_summary(
    user_id: str,
    days: int = Query(default=30, ge=7, le=90),
    format: str = Query(default="json", regex="^(json|markdown)$")
):
    """
    Generate a doctor summary report.
    
    Includes symptom frequencies, patterns, and recommendations
    formatted for physician review.
    """
    try:
        generator = DoctorSummaryGenerator(user_id)
        report = await generator.generate(days=days)
        
        if format == "markdown":
            return {"markdown": report.to_markdown()}
        return report.to_dict()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Context Pyramid Endpoints
# =============================================================================

@router.post("/context/{user_id}")
async def get_context_pyramid(user_id: str, request: ContextRequest):
    """
    Get the context pyramid for a user.
    
    Returns hierarchical context optimized for the given query.
    """
    try:
        pyramid_manager = PyramidManager(user_id)
        
        # Convert layer numbers to enums if provided
        include_layers = None
        if request.layers:
            include_layers = [ContextLayer(l) for l in request.layers if 0 <= l <= 4]
        
        pyramid = await pyramid_manager.build_pyramid(
            query=request.query,
            include_layers=include_layers
        )
        
        return pyramid.to_dict()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/context/{user_id}/string")
async def get_context_string(
    user_id: str,
    query: Optional[str] = None,
    max_tokens: int = Query(default=2000, ge=500, le=8000)
):
    """
    Get LLM-ready context string.
    
    Returns a formatted string optimized for including in LLM prompts.
    """
    try:
        pyramid_manager = PyramidManager(user_id)
        context_string = await pyramid_manager.get_context_for_query(
            query=query or "",
            max_tokens=max_tokens
        )
        
        return {
            "user_id": user_id,
            "query": query,
            "max_tokens": max_tokens,
            "context": context_string,
            "char_count": len(context_string),
            "estimated_tokens": len(context_string) // 4
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/context/{user_id}/layer/{layer_id}")
async def get_specific_layer(user_id: str, layer_id: int):
    """Get a specific context layer."""
    try:
        if layer_id < 0 or layer_id > 4:
            raise HTTPException(status_code=400, detail="Layer ID must be 0-4")
        
        pyramid_manager = PyramidManager(user_id)
        layer = await pyramid_manager.get_layer(ContextLayer(layer_id))
        
        if not layer:
            raise HTTPException(status_code=404, detail="Layer not found")
        
        return layer.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
