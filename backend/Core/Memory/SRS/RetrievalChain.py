"""
RetrievalChain.py - Complete Retrieval Orchestrator

Combines SmartRouter, DynamicLoader, and FAISS search to provide
a unified interface for context-rich retrieval.
"""

import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np

from .VectorRegistry import get_registry
from .SmartRouter import get_router, RouteResult
from .DynamicLoader import get_loader

# Configure logging
logger = logging.getLogger(__name__)


# =============================================================================
# Data Models
# =============================================================================

@dataclass
class RetrievedChunk:
    """A single retrieved chunk with metadata."""
    text: str
    score: float
    source_store: str
    source_book: str
    chunk_id: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "score": round(self.score, 4),
            "source_store": self.source_store,
            "source_book": self.source_book,
            "chunk_id": self.chunk_id,
            "metadata": self.metadata
        }


@dataclass
class RetrievalResult:
    """Complete result from the retrieval chain."""
    query: str
    chunks: List[RetrievedChunk]
    stores_searched: List[str]
    routing_info: List[Dict]
    total_chunks_found: int
    retrieval_time_ms: float
    
    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "chunks": [c.to_dict() for c in self.chunks],
            "stores_searched": self.stores_searched,
            "routing_info": self.routing_info,
            "total_chunks_found": self.total_chunks_found,
            "retrieval_time_ms": round(self.retrieval_time_ms, 2)
        }
    
    def get_context_string(self, max_chunks: int = 5, separator: str = "\n\n---\n\n") -> str:
        """Get concatenated context string for LLM input."""
        chunks_to_use = self.chunks[:max_chunks]
        
        context_parts = []
        for chunk in chunks_to_use:
            part = f"[Source: {chunk.source_book}]\n{chunk.text}"
            context_parts.append(part)
        
        return separator.join(context_parts)


# =============================================================================
# Retrieval Chain
# =============================================================================

class RetrievalChain:
    """
    End-to-end retrieval pipeline.
    
    Flow:
    1. Route query to best matching stores (SmartRouter via Groq)
    2. Load required stores dynamically (DynamicLoader)
    3. Search each store with text-based matching
    4. Merge and re-rank results
    5. Return curated context
    """
    
    DEFAULT_TOP_K_STORES = 2
    DEFAULT_TOP_K_CHUNKS = 10
    
    def __init__(
        self,
        router=None,
        loader=None,
        registry=None
    ):
        """
        Initialize the retrieval chain.
        
        Args:
            router: SmartRouter instance
            loader: DynamicLoader instance
            registry: VectorRegistry instance
        """
        self.registry = registry or get_registry()
        self.router = router or get_router()
        self.loader = loader or get_loader()
    
    def _merge_and_rerank(
        self,
        all_results: List[tuple],
        top_k: int
    ) -> List[RetrievedChunk]:
        """
        Merge results from multiple stores and re-rank.
        
        Args:
            all_results: List of (store_id, chunks) tuples
            top_k: Number of final results to return
            
        Returns:
            Re-ranked list of RetrievedChunk
        """
        merged = []
        
        for store_id, chunks in all_results:
            store_info = self.registry.get_store(store_id)
            book_name = store_info.book_name if store_info else "unknown"
            
            for chunk in chunks:
                merged.append(RetrievedChunk(
                    text=chunk.get('text', ''),
                    score=chunk.get('score', 0.0),
                    source_store=store_id,
                    source_book=book_name,
                    chunk_id=chunk.get('id', -1),
                    metadata=chunk.get('metadata', {})
                ))
        
        # Sort by score (descending)
        merged.sort(key=lambda x: x.score, reverse=True)
        
        # Remove duplicates (same text from different stores)
        seen_texts = set()
        unique_results = []
        for chunk in merged:
            text_hash = hash(chunk.text[:200])  # Hash first 200 chars
            if text_hash not in seen_texts:
                seen_texts.add(text_hash)
                unique_results.append(chunk)
        
        return unique_results[:top_k]
    
    def retrieve(
        self,
        query: str,
        top_k_stores: int = None,
        top_k_chunks: int = None,
        min_score: float = 0.1
    ) -> RetrievalResult:
        """
        Execute the full retrieval pipeline.
        
        Args:
            query: User's search query
            top_k_stores: Maximum stores to search
            top_k_chunks: Maximum chunks to return
            min_score: Minimum store routing score
            
        Returns:
            RetrievalResult with chunks and metadata
        """
        import time
        start_time = time.time()
        
        top_k_stores = top_k_stores or self.DEFAULT_TOP_K_STORES
        top_k_chunks = top_k_chunks or self.DEFAULT_TOP_K_CHUNKS
        
        # Step 1: Route to best stores using Groq LLM
        route_results = self.router.route_query(
            query,
            top_k=top_k_stores,
            min_score=min_score
        )
        
        if not route_results:
            logger.warning(f"No stores matched query: {query[:50]}...")
            return RetrievalResult(
                query=query,
                chunks=[],
                stores_searched=[],
                routing_info=[],
                total_chunks_found=0,
                retrieval_time_ms=(time.time() - start_time) * 1000
            )
        
        # Step 2: Load stores and search
        all_results = []
        stores_searched = []
        
        for route in route_results:
            store = self.loader.get(route.store_id)
            if store is None:
                logger.warning(f"Failed to load store: {route.store_id}")
                continue
            
            # Search this store using text-based matching
            # Store.search now uses keyword matching since we don't have embeddings
            chunks = store.search_by_keywords(query, top_k=top_k_chunks)
            all_results.append((route.store_id, chunks))
            stores_searched.append(route.store_id)
        
        # Step 3: Merge and re-rank
        final_chunks = self._merge_and_rerank(all_results, top_k_chunks)
        
        elapsed_ms = (time.time() - start_time) * 1000
        
        result = RetrievalResult(
            query=query,
            chunks=final_chunks,
            stores_searched=stores_searched,
            routing_info=[r.to_dict() for r in route_results],
            total_chunks_found=len(final_chunks),
            retrieval_time_ms=elapsed_ms
        )
        
        logger.info(
            f"Retrieved {len(final_chunks)} chunks from {len(stores_searched)} stores "
            f"in {elapsed_ms:.1f}ms"
        )
        
        return result
    
    def retrieve_with_context(
        self,
        query: str,
        max_context_length: int = 4000,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Retrieve and format as context string for LLM.
        
        Args:
            query: User's search query
            max_context_length: Maximum context string length
            **kwargs: Additional args passed to retrieve()
            
        Returns:
            Dict with context string and metadata
        """
        result = self.retrieve(query, **kwargs)
        
        # Build context string, respecting max length
        context_parts = []
        current_length = 0
        chunks_used = 0
        
        for chunk in result.chunks:
            chunk_text = f"[{chunk.source_book}]\n{chunk.text}\n"
            if current_length + len(chunk_text) > max_context_length:
                break
            context_parts.append(chunk_text)
            current_length += len(chunk_text)
            chunks_used += 1
        
        return {
            "context": "\n---\n".join(context_parts),
            "chunks_used": chunks_used,
            "total_chunks": result.total_chunks_found,
            "stores_searched": result.stores_searched,
            "retrieval_time_ms": result.retrieval_time_ms
        }


# =============================================================================
# Module-level singleton
# =============================================================================

_chain: Optional[RetrievalChain] = None

def get_retrieval_chain() -> RetrievalChain:
    """Get the global RetrievalChain instance."""
    global _chain
    if _chain is None:
        _chain = RetrievalChain()
    return _chain


def retrieve(query: str, **kwargs) -> RetrievalResult:
    """Convenience function for quick retrieval."""
    return get_retrieval_chain().retrieve(query, **kwargs)


def get_context(query: str, **kwargs) -> Dict[str, Any]:
    """Convenience function to get LLM-ready context."""
    return get_retrieval_chain().retrieve_with_context(query, **kwargs)


# =============================================================================
# CLI Testing
# =============================================================================

if __name__ == "__main__":
    chain = get_retrieval_chain()
    
    test_queries = [
        "What foods are high in iron during pregnancy?",
        "symptoms of heart disease",
        "vitamin deficiency effects on bones",
    ]
    
    print("\n=== Retrieval Chain Testing ===\n")
    
    for query in test_queries:
        print(f"Query: '{query}'")
        print("-" * 50)
        
        result = chain.retrieve(query, top_k_stores=2, top_k_chunks=3)
        
        print(f"Stores: {result.stores_searched}")
        print(f"Time: {result.retrieval_time_ms:.1f}ms")
        print(f"Chunks found: {result.total_chunks_found}")
        
        for i, chunk in enumerate(result.chunks[:2], 1):
            print(f"\n  {i}. [{chunk.source_book}] (score: {chunk.score:.3f})")
            print(f"     {chunk.text[:150]}...")
        
        print("\n")
