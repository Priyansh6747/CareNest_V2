"""
DynamicLoader.py - On-demand FAISS Vector Store Loading

Loads FAISS indices dynamically when needed and manages memory
with an LRU cache to avoid loading all stores at once.
"""

import logging
import pickle
from pathlib import Path
from typing import Optional, Dict, List, Any
from collections import OrderedDict
from dataclasses import dataclass
import faiss
import numpy as np

from .VectorRegistry import get_registry, VectorStoreInfo

# Configure logging
logger = logging.getLogger(__name__)


# =============================================================================
# Data Models
# =============================================================================

@dataclass
class LoadedStore:
    """A loaded FAISS store ready for querying."""
    store_id: str
    index: faiss.Index
    chunks: List[Dict[str, Any]]  # Document chunks with text and metadata
    embedding_dim: int
    
    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search the store for similar chunks.
        
        Args:
            query_embedding: Query vector (1D or 2D array)
            top_k: Number of results to return
            
        Returns:
            List of chunks with scores
        """
        # Ensure query is 2D
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)
        
        # Search FAISS index
        distances, indices = self.index.search(query_embedding.astype('float32'), top_k)
        
        results = []
        for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            if idx < 0 or idx >= len(self.chunks):
                continue
            
            chunk = self.chunks[idx].copy()
            chunk['score'] = float(1 / (1 + dist))  # Convert distance to similarity
            chunk['rank'] = i + 1
            results.append(chunk)
        
        return results


# =============================================================================
# Dynamic Loader with LRU Cache
# =============================================================================

class DynamicLoader:
    """
    Dynamically loads and caches FAISS vector stores.
    
    Uses LRU (Least Recently Used) eviction to manage memory
    when too many stores are loaded.
    """
    
    DEFAULT_MAX_LOADED = 5  # Maximum stores to keep in memory
    
    def __init__(self, max_loaded: int = None, registry=None):
        """
        Initialize the loader.
        
        Args:
            max_loaded: Maximum number of stores to keep loaded
            registry: Optional VectorRegistry instance
        """
        self.max_loaded = max_loaded or self.DEFAULT_MAX_LOADED
        self.registry = registry or get_registry()
        
        # LRU cache using OrderedDict
        self._cache: OrderedDict[str, LoadedStore] = OrderedDict()
    
    def _load_faiss_store(self, store_info: VectorStoreInfo) -> Optional[LoadedStore]:
        """Load a FAISS store from disk."""
        store_path = Path(store_info.path)
        index_path = store_path / "index.faiss"
        pkl_path = store_path / "index.pkl"
        
        if not index_path.exists():
            logger.error(f"FAISS index not found: {index_path}")
            return None
        
        if not pkl_path.exists():
            logger.error(f"Pickle file not found: {pkl_path}")
            return None
        
        try:
            # Load FAISS index
            logger.info(f"Loading FAISS index: {store_info.store_id}")
            index = faiss.read_index(str(index_path))
            
            # Load document chunks from pickle
            with open(pkl_path, 'rb') as f:
                pkl_data = pickle.load(f)
            
            # Handle different pickle formats
            if isinstance(pkl_data, dict):
                # Format: {"texts": [...], "metadatas": [...]} or similar
                chunks = []
                texts = pkl_data.get('texts', pkl_data.get('documents', []))
                metadatas = pkl_data.get('metadatas', [{}] * len(texts))
                
                for i, (text, meta) in enumerate(zip(texts, metadatas)):
                    chunks.append({
                        'id': i,
                        'text': text if isinstance(text, str) else str(text),
                        'metadata': meta if isinstance(meta, dict) else {}
                    })
            elif isinstance(pkl_data, list):
                # Format: List of document objects
                chunks = []
                for i, item in enumerate(pkl_data):
                    if isinstance(item, dict):
                        chunks.append({
                            'id': i,
                            'text': item.get('text', item.get('page_content', str(item))),
                            'metadata': item.get('metadata', {})
                        })
                    else:
                        # Assume it's a LangChain Document or similar
                        chunks.append({
                            'id': i,
                            'text': getattr(item, 'page_content', str(item)),
                            'metadata': getattr(item, 'metadata', {})
                        })
            else:
                logger.warning(f"Unknown pickle format for {store_info.store_id}")
                chunks = []
            
            loaded = LoadedStore(
                store_id=store_info.store_id,
                index=index,
                chunks=chunks,
                embedding_dim=store_info.embedding_dim
            )
            
            logger.info(f"Loaded store {store_info.store_id}: {len(chunks)} chunks")
            return loaded
            
        except Exception as e:
            logger.error(f"Failed to load store {store_info.store_id}: {e}")
            return None
    
    def _evict_lru(self) -> None:
        """Evict the least recently used store if cache is full."""
        if len(self._cache) >= self.max_loaded:
            # Pop the oldest (first) item
            evicted_id, evicted_store = self._cache.popitem(last=False)
            logger.info(f"Evicted store from cache: {evicted_id}")
    
    def get(self, store_id: str) -> Optional[LoadedStore]:
        """
        Get a loaded store, loading it if necessary.
        
        Args:
            store_id: ID of the store to retrieve
            
        Returns:
            LoadedStore or None if not found/failed to load
        """
        # Check cache first
        if store_id in self._cache:
            # Move to end (most recently used)
            self._cache.move_to_end(store_id)
            return self._cache[store_id]
        
        # Get store info from registry
        store_info = self.registry.get_store(store_id)
        if store_info is None:
            logger.error(f"Store not found in registry: {store_id}")
            return None
        
        # Evict if necessary
        self._evict_lru()
        
        # Load store
        loaded = self._load_faiss_store(store_info)
        if loaded:
            self._cache[store_id] = loaded
        
        return loaded
    
    def preload(self, store_ids: List[str]) -> int:
        """
        Preload multiple stores into cache.
        
        Args:
            store_ids: List of store IDs to preload
            
        Returns:
            Number of stores successfully loaded
        """
        loaded_count = 0
        for store_id in store_ids:
            if self.get(store_id):
                loaded_count += 1
        return loaded_count
    
    def unload(self, store_id: str) -> bool:
        """
        Unload a store from cache.
        
        Args:
            store_id: ID of the store to unload
            
        Returns:
            True if store was unloaded, False if not in cache
        """
        if store_id in self._cache:
            del self._cache[store_id]
            logger.info(f"Unloaded store: {store_id}")
            return True
        return False
    
    def clear_cache(self) -> int:
        """
        Clear all stores from cache.
        
        Returns:
            Number of stores cleared
        """
        count = len(self._cache)
        self._cache.clear()
        logger.info(f"Cleared {count} stores from cache")
        return count
    
    def get_loaded_stores(self) -> List[str]:
        """Get list of currently loaded store IDs."""
        return list(self._cache.keys())
    
    def get_stats(self) -> Dict:
        """Get loader statistics."""
        return {
            "max_loaded": self.max_loaded,
            "currently_loaded": len(self._cache),
            "loaded_stores": list(self._cache.keys()),
            "total_chunks_in_memory": sum(
                len(s.chunks) for s in self._cache.values()
            )
        }


# =============================================================================
# Module-level singleton
# =============================================================================

_loader: Optional[DynamicLoader] = None

def get_loader(max_loaded: int = None) -> DynamicLoader:
    """Get the global DynamicLoader instance."""
    global _loader
    if _loader is None:
        _loader = DynamicLoader(max_loaded=max_loaded)
    return _loader


# =============================================================================
# CLI Testing
# =============================================================================

if __name__ == "__main__":
    loader = get_loader(max_loaded=3)
    registry = get_registry()
    
    print("\n=== Dynamic Loader Testing ===\n")
    print(f"Available stores: {[s.store_id for s in registry.list_stores()][:5]}...")
    
    # Load first store
    stores = registry.list_stores()
    if stores:
        store = loader.get(stores[0].store_id)
        if store:
            print(f"\nLoaded: {store.store_id}")
            print(f"Chunks: {len(store.chunks)}")
            if store.chunks:
                print(f"Sample chunk: {store.chunks[0]['text'][:200]}...")
    
    print(f"\n{loader.get_stats()}")
