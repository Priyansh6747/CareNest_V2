"""
SRS - Smart Retrieval System

Provides dynamic vector store routing and retrieval using MiniLM
for query classification and FAISS for similarity search.
"""

from .VectorRegistry import (
    VectorRegistry,
    VectorStoreInfo,
    get_registry,
)

from .SmartRouter import (
    SmartRouter,
    RouteResult,
    get_router,
    route_query,
    route_to_best,
)

from .DynamicLoader import (
    DynamicLoader,
    LoadedStore,
    get_loader,
)

from .RetrievalChain import (
    RetrievalChain,
    RetrievalResult,
    RetrievedChunk,
    get_retrieval_chain,
    retrieve,
    get_context,
)


__all__ = [
    # Registry
    "VectorRegistry",
    "VectorStoreInfo", 
    "get_registry",
    
    # Router
    "SmartRouter",
    "RouteResult",
    "get_router",
    "route_query",
    "route_to_best",
    
    # Loader
    "DynamicLoader",
    "LoadedStore",
    "get_loader",
    
    # Chain
    "RetrievalChain",
    "RetrievalResult",
    "RetrievedChunk",
    "get_retrieval_chain",
    "retrieve",
    "get_context",
]
