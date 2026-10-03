"""
shared_search

Vector similarity search using FAISS.

Modules:
- faiss_index: Low-level FAISS index management
- similarity: High-level semantic search

Features:
- FAISS index creation and management
- Vector similarity search
- Index persistence
- Batch operations
- GPU acceleration support

Usage:
    from shared_search import SimilaritySearch
    from shared_ai.embeddings import TextEmbedder
    
    # Initialize
    embedder = TextEmbedder()
    search = SimilaritySearch(embedder, dimension=768)
    
    # Build index
    search.build_index(documents, doc_ids)
    
    # Search
    results = search.search("query", top_k=5)
"""

from .faiss_index import (
    FAISSIndex,
    FAISS_AVAILABLE,
)
from .similarity import (
    SimilaritySearch,
)

__all__ = [
    # FAISS index
    "FAISSIndex",
    "FAISS_AVAILABLE",
    
    # Similarity search
    "SimilaritySearch",
]
