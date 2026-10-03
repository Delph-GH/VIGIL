"""
shared_ai.nlp

NLP components for French text processing.

Modules:
- preprocessor: Text preprocessing with spaCy
- ner: Named Entity Recognition
- sentiment: Sentiment analysis
"""

from .preprocessor import (
    TextPreprocessor,
    ProcessedText,
    SPACY_AVAILABLE,
)
from .ner import (
    NamedEntityRecognizer,
    Entity,
    EntityType,
)
from .sentiment import (
    SentimentAnalyzer,
    SentimentResult,
    SentimentPolarity,
)

__all__ = [
    # Preprocessing
    "TextPreprocessor",
    "ProcessedText",
    "SPACY_AVAILABLE",
    
    # NER
    "NamedEntityRecognizer",
    "Entity",
    "EntityType",
    
    # Sentiment
    "SentimentAnalyzer",
    "SentimentResult",
    "SentimentPolarity",
]
