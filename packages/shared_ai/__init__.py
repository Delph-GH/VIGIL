"""
shared_ai

AI/NLP utilities for French intelligence analysis.

Provides:
- Text preprocessing (spaCy-based)
- Named Entity Recognition
- Sentiment analysis
- Document vectorization (future)

Usage:
    from shared_ai.nlp import (
        TextPreprocessor,
        NamedEntityRecognizer,
        SentimentAnalyzer,
    )
    
    # Preprocess text
    preprocessor = TextPreprocessor(language="fr")
    result = preprocessor.process(text)
    
    # Extract entities
    ner = NamedEntityRecognizer(language="fr")
    entities = ner.extract_entities(text)
    
    # Analyze sentiment
    sentiment = SentimentAnalyzer(language="fr")
    result = sentiment.analyze(text)
"""

__version__ = "0.1.0"

# Note: NLP components require spaCy
# Install with: pip install spacy
# Download model: python -m spacy download fr_core_news_md

__all__ = []
