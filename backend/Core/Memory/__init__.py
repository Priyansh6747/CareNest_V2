"""
Memory Module - Context-Rich Query System

Provides three integrated components:
1. SRS - Smart Retrieval Engine with dynamic vector store routing
2. SymptomMapper - Symptom tracking with medic stones and pattern detection
3. ContextPyramid - Hierarchical context aggregation system
"""

from .SRS import (
    # Registry
    VectorRegistry,
    VectorStoreInfo,
    get_registry,
    
    # Router
    SmartRouter,
    RouteResult,
    get_router,
    route_query,
    route_to_best,
    
    # Loader
    DynamicLoader,
    LoadedStore,
    get_loader,
    
    # Chain
    RetrievalChain,
    RetrievalResult,
    RetrievedChunk,
    get_retrieval_chain,
    retrieve,
    get_context,
)

from .SymptomMapper import (
    # MedicStone
    MedicStone,
    MedicStoneCreate,
    MedicStoneUpdate,
    SymptomContext,
    SymptomFrequency,
    Severity,
    create_medic_stone,
    get_medic_stone,
    get_medic_stones_by_range,
    get_recent_medic_stones,
    update_medic_stone,
    delete_medic_stone,
    get_symptom_frequency,
    get_all_symptom_frequencies,
    
    # Timeline
    TimelineMapper,
    SymptomTimeline,
    
    # Patterns
    PatternDetector,
    PatternAnalysis,
    
    # Doctor Summary
    DoctorSummaryGenerator,
    DoctorReport,
)

from .ContextPyramid import (
    # Data Retrieval
    RetrieveData,
    
    # Pyramid
    PyramidManager,
    ContextPyramid,
    ContextLayer,
    LayerContent,
)


__all__ = [
    # === SRS ===
    "VectorRegistry",
    "VectorStoreInfo",
    "get_registry",
    "SmartRouter",
    "RouteResult",
    "get_router",
    "route_query",
    "route_to_best",
    "DynamicLoader",
    "LoadedStore",
    "get_loader",
    "RetrievalChain",
    "RetrievalResult",
    "RetrievedChunk",
    "get_retrieval_chain",
    "retrieve",
    "get_context",
    
    # === SymptomMapper ===
    "MedicStone",
    "MedicStoneCreate",
    "MedicStoneUpdate",
    "SymptomContext",
    "SymptomFrequency",
    "Severity",
    "create_medic_stone",
    "get_medic_stone",
    "get_medic_stones_by_range",
    "get_recent_medic_stones",
    "update_medic_stone",
    "delete_medic_stone",
    "get_symptom_frequency",
    "get_all_symptom_frequencies",
    "TimelineMapper",
    "SymptomTimeline",
    "PatternDetector",
    "PatternAnalysis",
    "DoctorSummaryGenerator",
    "DoctorReport",
    
    # === ContextPyramid ===
    "RetrieveData",
    "PyramidManager",
    "ContextPyramid",
    "ContextLayer",
    "LayerContent",
]
