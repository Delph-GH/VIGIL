"""
diaspora-platform.ai

AI analytics for Diaspora using shared_ai components.

Modules:
- analytics_processor: Article analytics and community insights

Integrates:
- shared_ai.nlp: Text preprocessing, NER, sentiment
- shared_ai.embeddings: Article similarity

Replaces:
- Old analysis/sentiment.py (lexicon → transformer-based)
"""

from .analytics_processor import (
    DiasporaAnalyticsProcessor,
    AnalyticsResult,
)

__all__ = [
    # Analytics
    "DiasporaAnalyticsProcessor",
    "AnalyticsResult",
]
