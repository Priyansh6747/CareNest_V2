"""
SmartRouter.py - Query-based Vector Store Routing

Uses MiniLM embeddings to match user queries against vector store
metadata and determine the most relevant stores to search.
"""

import logging
from typing import List, Tuple, Optional
from dataclasses import dataclass
import numpy as np

from .VectorRegistry import get_registry, VectorStoreInfo

# Configure logging
logger = logging.getLogger(__name__)


# =============================================================================
# Data Models
# =============================================================================

@dataclass
class RouteResult:
    """Result of routing a query to vector stores."""
    store_id: str
    store_info: VectorStoreInfo
    similarity_score: float
    confidence: str  # "high", "medium", "low"
    
    def to_dict(self) -> dict:
        return {
            "store_id": self.store_id,
            "book_name": self.store_info.book_name,
            "similarity": round(self.similarity_score, 4),
            "confidence": self.confidence,
            "chunks_available": self.store_info.chunks_count,
            "path": self.store_info.path,
        }


# =============================================================================
# Smart Router
# =============================================================================

class SmartRouter:
    """
    Routes user queries to the most relevant vector stores.
    
    Uses cosine similarity between query embeddings and store
    metadata embeddings to rank and select stores.
    """
    
    # Confidence thresholds
    HIGH_CONFIDENCE_THRESHOLD = 0.5
    MEDIUM_CONFIDENCE_THRESHOLD = 0.3
    MIN_SIMILARITY_THRESHOLD = 0.15
    
    def __init__(self, registry=None):
        """
        Initialize the router.
        
        Args:
            registry: Optional VectorRegistry instance. Uses global singleton if not provided.
        """
        self.registry = registry or get_registry()
    
    def _cosine_similarity(self, query_emb: np.ndarray, store_embs: np.ndarray) -> np.ndarray:
        """Compute cosine similarity between query and all stores."""
        # Normalize vectors
        query_norm = query_emb / np.linalg.norm(query_emb)
        store_norms = store_embs / np.linalg.norm(store_embs, axis=1, keepdims=True)
        
        # Compute dot product (cosine similarity for normalized vectors)
        similarities = np.dot(store_norms, query_norm)
        return similarities
    
    def _get_confidence_level(self, score: float) -> str:
        """Determine confidence level from similarity score."""
        if score >= self.HIGH_CONFIDENCE_THRESHOLD:
            return "high"
        elif score >= self.MEDIUM_CONFIDENCE_THRESHOLD:
            return "medium"
        else:
            return "low"
    
    def route_query(
        self,
        query: str,
        top_k: int = 3,
        min_similarity: Optional[float] = None
    ) -> List[RouteResult]:
        """
        Route a query to the most relevant vector stores.
        
        Args:
            query: User's search query
            top_k: Maximum number of stores to return
            min_similarity: Minimum similarity threshold (default: MIN_SIMILARITY_THRESHOLD)
            
        Returns:
            List of RouteResult ordered by relevance
        """
        if min_similarity is None:
            min_similarity = self.MIN_SIMILARITY_THRESHOLD
        
        # Get store embeddings
        store_embeddings, store_ids = self.registry.get_store_embeddings()
        
        if store_embeddings is None or len(store_ids) == 0:
            logger.warning("No stores available for routing")
            return []
        
        # Encode query
        query_embedding = self.registry.embedder.encode(query, convert_to_numpy=True)
        
        # Compute similarities
        similarities = self._cosine_similarity(query_embedding, store_embeddings)
        
        # Sort by similarity (descending)
        sorted_indices = np.argsort(similarities)[::-1]
        
        results = []
        for idx in sorted_indices[:top_k]:
            score = float(similarities[idx])
            
            # Skip if below threshold
            if score < min_similarity:
                continue
            
            store_id = store_ids[idx]
            store_info = self.registry.get_store(store_id)
            
            if store_info:
                results.append(RouteResult(
                    store_id=store_id,
                    store_info=store_info,
                    similarity_score=score,
                    confidence=self._get_confidence_level(score)
                ))
        
        logger.info(f"Query '{query[:50]}...' routed to {len(results)} stores")
        return results
    
    def route_to_best(self, query: str) -> Optional[RouteResult]:
        """
        Route query to the single best matching store.
        
        Args:
            query: User's search query
            
        Returns:
            Best RouteResult or None if no suitable store found
        """
        results = self.route_query(query, top_k=1)
        return results[0] if results else None
    
    def explain_routing(self, query: str, top_k: int = 5) -> dict:
        """
        Get detailed routing explanation for debugging.
        
        Args:
            query: User's search query
            top_k: Number of top stores to explain
            
        Returns:
            Dict with routing details
        """
        store_embeddings, store_ids = self.registry.get_store_embeddings()
        query_embedding = self.registry.embedder.encode(query, convert_to_numpy=True)
        similarities = self._cosine_similarity(query_embedding, store_embeddings)
        
        sorted_indices = np.argsort(similarities)[::-1]
        
        rankings = []
        for i, idx in enumerate(sorted_indices[:top_k]):
            store_id = store_ids[idx]
            store_info = self.registry.get_store(store_id)
            rankings.append({
                "rank": i + 1,
                "store_id": store_id,
                "book_name": store_info.book_name if store_info else "unknown",
                "similarity": round(float(similarities[idx]), 4),
                "confidence": self._get_confidence_level(similarities[idx]),
                "keywords": store_info.keywords[:5] if store_info else [],
                "context_preview": store_info.context_summary[:100] if store_info else ""
            })
        
        return {
            "query": query,
            "top_k": top_k,
            "threshold": self.MIN_SIMILARITY_THRESHOLD,
            "rankings": rankings
        }


# =============================================================================
# Module-level convenience functions
# =============================================================================

_router: Optional[SmartRouter] = None

def get_router() -> SmartRouter:
    """Get the global SmartRouter instance."""
    global _router
    if _router is None:
        _router = SmartRouter()
    return _router


def route_query(query: str, top_k: int = 3) -> List[RouteResult]:
    """Convenience function to route a query."""
    return get_router().route_query(query, top_k)


def route_to_best(query: str) -> Optional[RouteResult]:
    """Convenience function to get the best matching store."""
    return get_router().route_to_best(query)


# =============================================================================
# CLI Testing
# =============================================================================

if __name__ == "__main__":
    router = get_router()
    
    test_queries = [
        "iron deficiency during pregnancy",
        "heart palpitations and chest pain",
        "vitamin E benefits and sources",
        "bone density and calcium intake",
        "eye problems and vision issues",
    ]
    
    print("\n=== Smart Router Testing ===\n")
    
    for query in test_queries:
        print(f"Query: '{query}'")
        results = router.route_query(query, top_k=3)
        
        for i, r in enumerate(results, 1):
            print(f"  {i}. {r.store_info.book_name} (score: {r.similarity_score:.3f}, {r.confidence})")
        print()
