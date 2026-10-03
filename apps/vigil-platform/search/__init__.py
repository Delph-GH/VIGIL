"""
vigil-platform.search

Article similarity search using shared_search.

Replaces old processing/embeddings/similarity_index.py
"""

from .article_search import (
    VigilArticleSearch,
)

__all__ = [
    "VigilArticleSearch",
]
