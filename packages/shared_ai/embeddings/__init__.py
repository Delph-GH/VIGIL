"""
shared_ai.embeddings

Text embeddings using sentence-transformers.

Modules:
- embedder: TextEmbedder for converting text to vectors
- batch_processor: Batch processing utilities

Recommended models for French:
- sentence-camembert-large (best quality)
- sentence-camembert-base (recommended)
- paraphrase-multilingual-MiniLM-L12-v2 (fast, multilingual)
"""

from .embedder import (
    TextEmbedder,
    SENTENCE_TRANSFORMERS_AVAILABLE,
)
from .batch_processor import (
    EmbeddingBatchProcessor,
    EmbeddingCache,
)

__all__ = [
    # Embedder
    "TextEmbedder",
    "SENTENCE_TRANSFORMERS_AVAILABLE",
    
    # Batch processing
    "EmbeddingBatchProcessor",
    "EmbeddingCache",
]
