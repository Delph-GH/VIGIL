"""
vigil-platform.ai

AI processing for Vigil using shared_ai components.

Modules:
- article_processor: Complete article processing pipeline
- topic_manager: Topic modeling and evolution

Integrates:
- shared_ai.nlp: Text preprocessing, NER, sentiment
- shared_ai.embeddings: Article embeddings
- shared_ai.topics: Topic modeling
"""

from .article_processor import (
    VigilArticleProcessor,
    ProcessedArticle,
)
from .topic_manager import (
    VigilTopicManager,
)

__all__ = [
    # Article processing
    "VigilArticleProcessor",
    "ProcessedArticle",
    
    # Topic management
    "VigilTopicManager",
]
