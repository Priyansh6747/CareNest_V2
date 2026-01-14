"""
VectorRegistry.py - Metadata Registry for Vector Stores

Scans all vector store directories, loads metadata.json files.
Uses precomputed embeddings stored in metadata for matching.
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# Data Models
# =============================================================================

@dataclass
class VectorStoreInfo:
    """Metadata for a single vector store."""
    store_id: str                  # Unique identifier (e.g., "preg_nutri_store_1")
    book_name: str                 # Source book/document name
    store_name: str                # Store partition name
    path: str                      # Absolute path to store directory
    chunks_count: int              # Number of chunks in store
    embedding_dim: int             # Embedding dimension (384 for MiniLM)
    context_summary: str           # Content summary
    keywords: List[str]            # Extracted keywords
    storage_mb: float              # Storage size in MB
    
    def get_searchable_text(self) -> str:
        """Combine metadata into searchable text."""
        parts = [
            self.book_name,
            self.context_summary,
            " ".join(self.keywords)
        ]
        return " ".join(filter(None, parts))


# =============================================================================
# Vector Registry
# =============================================================================

class VectorRegistry:
    """
    Registry for all available vector stores.
    
    Scans the data directory and loads metadata for each store.
    No local model download - uses Groq LLM for classification.
    """
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize the registry.
        
        Args:
            data_dir: Path to the vector stores data directory.
                     Defaults to Core/Memory/SRS/data relative to this file.
        """
        if data_dir is None:
            # Default to data directory relative to this file
            self_dir = Path(__file__).parent
            data_dir = str(self_dir / "data")
        
        self.data_dir = Path(data_dir)
        self.stores: Dict[str, VectorStoreInfo] = {}
        
        # Load registry on init
        self._scan_stores()
        
    def _scan_stores(self) -> None:
        """Scan data directory and load all store metadata."""
        if not self.data_dir.exists():
            logger.warning(f"Data directory not found: {self.data_dir}")
            return
            
        logger.info(f"Scanning vector stores in: {self.data_dir}")
        
        for book_dir in self.data_dir.iterdir():
            if not book_dir.is_dir():
                continue
                
            # Each book can have multiple store partitions
            for store_dir in book_dir.iterdir():
                if not store_dir.is_dir():
                    continue
                    
                metadata_path = store_dir / "metadata.json"
                if metadata_path.exists():
                    self._load_store_metadata(store_dir, metadata_path)
        
        logger.info(f"Loaded {len(self.stores)} vector stores")
    
    def _load_store_metadata(self, store_dir: Path, metadata_path: Path) -> None:
        """Load metadata from a single store."""
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            
            # Create unique store ID
            store_id = f"{meta.get('book_name', 'unknown')}_{meta.get('store_name', 'store')}".replace(" ", "_").lower()
            
            store_info = VectorStoreInfo(
                store_id=store_id,
                book_name=meta.get("book_name", ""),
                store_name=meta.get("store_name", ""),
                path=str(store_dir.absolute()),
                chunks_count=meta.get("chunks_in_store", 0),
                embedding_dim=meta.get("embedding_dimension", 384),
                context_summary=meta.get("context_summary", ""),
                keywords=meta.get("keywords", []),
                storage_mb=meta.get("storage_mb", 0.0),
            )
            
            self.stores[store_id] = store_info
            logger.debug(f"Loaded store: {store_id} ({store_info.chunks_count} chunks)")
            
        except Exception as e:
            logger.error(f"Failed to load metadata from {metadata_path}: {e}")
    
    def get_store(self, store_id: str) -> Optional[VectorStoreInfo]:
        """Get a specific store by ID."""
        return self.stores.get(store_id)
    
    def list_stores(self) -> List[VectorStoreInfo]:
        """List all registered stores."""
        return list(self.stores.values())
    
    def get_store_descriptions(self) -> List[Dict]:
        """Get store descriptions for LLM routing."""
        return [
            {
                "id": s.store_id,
                "name": s.book_name,
                "keywords": s.keywords[:8],
                "summary": s.context_summary[:200] if s.context_summary else "",
            }
            for s in self.stores.values()
        ]
    
    def refresh(self) -> None:
        """Re-scan and reload all store metadata."""
        self.stores.clear()
        self._scan_stores()
    
    def get_stats(self) -> Dict:
        """Get registry statistics."""
        total_chunks = sum(s.chunks_count for s in self.stores.values())
        total_storage = sum(s.storage_mb for s in self.stores.values())
        
        return {
            "total_stores": len(self.stores),
            "total_chunks": total_chunks,
            "total_storage_mb": round(total_storage, 2),
            "routing_method": "groq_llm",
            "stores": [
                {
                    "id": s.store_id,
                    "book": s.book_name,
                    "chunks": s.chunks_count,
                    "size_mb": s.storage_mb
                }
                for s in self.stores.values()
            ]
        }


# =============================================================================
# Module-level singleton
# =============================================================================

_registry: Optional[VectorRegistry] = None

def get_registry(data_dir: Optional[str] = None) -> VectorRegistry:
    """
    Get the global vector registry instance.
    
    Args:
        data_dir: Optional custom data directory (only used on first call)
        
    Returns:
        VectorRegistry singleton instance
    """
    global _registry
    if _registry is None:
        _registry = VectorRegistry(data_dir)
    return _registry


# =============================================================================
# CLI Testing
# =============================================================================

if __name__ == "__main__":
    # Quick test
    registry = get_registry()
    print(f"\n=== Vector Registry Stats ===")
    stats = registry.get_stats()
    print(f"Total stores: {stats['total_stores']}")
    print(f"Total chunks: {stats['total_chunks']}")
    print(f"Total storage: {stats['total_storage_mb']} MB")
    print(f"\nStores:")
    for store in stats['stores']:
        print(f"  - {store['id']}: {store['chunks']} chunks ({store['size_mb']} MB)")
