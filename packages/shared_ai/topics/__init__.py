"""
shared_ai.topics

Topic modeling using BERTopic for French political content.

Modules:
- bertopic_modeler: Topic discovery and extraction
- topic_evolution: Temporal topic tracking

Requires:
- bertopic
- umap-learn
- hdbscan
"""

from .bertopic_modeler import (
    TopicModeler,
    BERTOPIC_AVAILABLE,
)
from .topic_evolution import (
    TopicEvolution,
)

__all__ = [
    # Topic modeling
    "TopicModeler",
    "BERTOPIC_AVAILABLE",
    
    # Evolution tracking
    "TopicEvolution",
]
