"""
diaspora-platform.search

Community article search using shared_search.

New capability: FAISS-based similarity search for expat content.
"""

from .community_search import (
    DiasporaCommunitySearch,
)

__all__ = [
    "DiasporaCommunitySearch",
]
