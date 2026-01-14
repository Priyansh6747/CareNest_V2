"""
SmartRouter.py - Query-based Vector Store Routing using Groq LLM

Uses Groq's fast LLM inference to classify queries and route
to the most relevant vector stores without downloading local models.
"""

import os
import json
import logging
from typing import List, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

from .VectorRegistry import get_registry, VectorStoreInfo

# Load environment variables
load_dotenv()

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
    relevance_score: float
    confidence: str  # "high", "medium", "low"
    reasoning: str
    
    def to_dict(self) -> dict:
        return {
            "store_id": self.store_id,
            "book_name": self.store_info.book_name,
            "relevance_score": self.relevance_score,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "chunks_available": self.store_info.chunks_count,
            "path": self.store_info.path,
        }


# =============================================================================
# Groq Client
# =============================================================================

class GroqEmbedder:
    """
    Uses Groq LLM to semantically classify queries to vector stores.
    No local model download required.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Groq client.
        
        Args:
            api_key: Groq API key. Defaults to GROQ_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            logger.warning("GROQ_API_KEY not set. SmartRouter will use fallback matching.")
        
        self._client = None
    
    @property
    def client(self):
        """Lazy-load Groq client."""
        if self._client is None and self.api_key:
            try:
                from groq import Groq
                self._client = Groq(api_key=self.api_key)
                logger.info("Groq client initialized")
            except ImportError:
                logger.warning("groq package not installed. Install with: pip install groq")
        return self._client
    
    def classify_query(
        self,
        query: str,
        store_descriptions: List[dict],
        top_k: int = 3
    ) -> List[dict]:
        """
        Use Groq LLM to classify which stores are most relevant for a query.
        
        Args:
            query: User's search query
            store_descriptions: List of store metadata dicts
            top_k: Number of stores to return
            
        Returns:
            List of {store_id, score, reasoning} dicts
        """
        if not self.client:
            return self._fallback_matching(query, store_descriptions, top_k)
        
        # Build prompt with store descriptions
        stores_text = "\n".join([
            f"- ID: {s['id']}\n  Name: {s['name']}\n  Keywords: {', '.join(s['keywords'][:5])}\n  Summary: {s['summary'][:150]}"
            for s in store_descriptions
        ])
        
        prompt = f"""You are a query router for a medical knowledge base. Given a user query, determine which knowledge stores are most relevant.

Available Knowledge Stores:
{stores_text}

User Query: "{query}"

Return a JSON array of the top {top_k} most relevant stores. Each item should have:
- "store_id": the store ID
- "score": relevance score from 0.0 to 1.0
- "reasoning": brief explanation why this store is relevant

Only return the JSON array, no other text. Example format:
[{{"store_id": "example_store_1", "score": 0.95, "reasoning": "Directly covers the topic"}}]
"""

        try:
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=500,
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse JSON response
            # Handle potential markdown code blocks
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            
            results = json.loads(content)
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"Groq classification failed: {e}")
            return self._fallback_matching(query, store_descriptions, top_k)
    
    def _fallback_matching(
        self,
        query: str,
        store_descriptions: List[dict],
        top_k: int
    ) -> List[dict]:
        """Simple keyword-based fallback when Groq is unavailable."""
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        scores = []
        for store in store_descriptions:
            # Count keyword matches
            store_text = f"{store['name']} {' '.join(store['keywords'])} {store['summary']}".lower()
            matches = sum(1 for word in query_words if word in store_text)
            score = min(1.0, matches / (len(query_words) + 1))
            
            scores.append({
                "store_id": store["id"],
                "score": score,
                "reasoning": f"Keyword match ({matches} words)"
            })
        
        # Sort by score
        scores.sort(key=lambda x: x["score"], reverse=True)
        return scores[:top_k]


# =============================================================================
# Smart Router
# =============================================================================

class SmartRouter:
    """
    Routes user queries to the most relevant vector stores using Groq LLM.
    """
    
    def __init__(self, registry=None, api_key: Optional[str] = None):
        """
        Initialize the router.
        
        Args:
            registry: Optional VectorRegistry instance.
            api_key: Optional Groq API key.
        """
        self.registry = registry or get_registry()
        self.embedder = GroqEmbedder(api_key)
    
    def _get_confidence_level(self, score: float) -> str:
        """Determine confidence level from score."""
        if score >= 0.7:
            return "high"
        elif score >= 0.4:
            return "medium"
        else:
            return "low"
    
    def route_query(
        self,
        query: str,
        top_k: int = 3,
        min_score: float = 0.1
    ) -> List[RouteResult]:
        """
        Route a query to the most relevant vector stores.
        
        Args:
            query: User's search query
            top_k: Maximum number of stores to return
            min_score: Minimum relevance score
            
        Returns:
            List of RouteResult ordered by relevance
        """
        # Get store descriptions
        store_descriptions = self.registry.get_store_descriptions()
        
        if not store_descriptions:
            logger.warning("No stores available for routing")
            return []
        
        # Classify using Groq
        classifications = self.embedder.classify_query(query, store_descriptions, top_k)
        
        results = []
        for cls in classifications:
            store_id = cls.get("store_id", "")
            score = cls.get("score", 0.0)
            reasoning = cls.get("reasoning", "")
            
            if score < min_score:
                continue
            
            store_info = self.registry.get_store(store_id)
            if store_info:
                results.append(RouteResult(
                    store_id=store_id,
                    store_info=store_info,
                    relevance_score=score,
                    confidence=self._get_confidence_level(score),
                    reasoning=reasoning
                ))
        
        logger.info(f"Query '{query[:50]}...' routed to {len(results)} stores via Groq")
        return results
    
    def route_to_best(self, query: str) -> Optional[RouteResult]:
        """Route query to the single best matching store."""
        results = self.route_query(query, top_k=1)
        return results[0] if results else None
    
    def explain_routing(self, query: str, top_k: int = 5) -> dict:
        """Get detailed routing explanation."""
        results = self.route_query(query, top_k=top_k, min_score=0.0)
        
        return {
            "query": query,
            "top_k": top_k,
            "method": "groq_llm" if self.embedder.client else "keyword_fallback",
            "rankings": [
                {
                    "rank": i + 1,
                    "store_id": r.store_id,
                    "book_name": r.store_info.book_name,
                    "score": r.relevance_score,
                    "confidence": r.confidence,
                    "reasoning": r.reasoning,
                }
                for i, r in enumerate(results)
            ]
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
    ]
    
    print("\n=== Smart Router Testing (Groq) ===\n")
    
    for query in test_queries:
        print(f"Query: '{query}'")
        results = router.route_query(query, top_k=3)
        
        for i, r in enumerate(results, 1):
            print(f"  {i}. {r.store_info.book_name} (score: {r.relevance_score:.2f}, {r.confidence})")
            print(f"     Reason: {r.reasoning}")
        print()
