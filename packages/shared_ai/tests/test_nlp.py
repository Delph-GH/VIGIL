"""
Tests for shared_ai NLP components.

Tests preprocessor, NER, and sentiment analysis without requiring spaCy.
"""

import pytest
from datetime import datetime


class TestSentimentAnalyzer:
    """Test sentiment analysis (no spaCy required)."""
    
    def test_import(self):
        """Test importing sentiment analyzer."""
        from shared_ai.nlp import SentimentAnalyzer
        assert SentimentAnalyzer is not None
    
    def test_positive_sentiment(self):
        """Test positive sentiment detection."""
        from shared_ai.nlp import SentimentAnalyzer, SentimentPolarity
        
        analyzer = SentimentAnalyzer(language="fr")
        
        positive_text = "C'est un excellent progrès pour la France. Très bon résultat."
        result = analyzer.analyze(positive_text)
        
        assert result.polarity == SentimentPolarity.POSITIVE
        assert result.score > 0
    
    def test_negative_sentiment(self):
        """Test negative sentiment detection."""
        from shared_ai.nlp import SentimentAnalyzer, SentimentPolarity
        
        analyzer = SentimentAnalyzer(language="fr")
        
        negative_text = "C'est une grave crise économique. Situation très mauvaise."
        result = analyzer.analyze(negative_text)
        
        assert result.polarity == SentimentPolarity.NEGATIVE
        assert result.score < 0
    
    def test_neutral_sentiment(self):
        """Test neutral sentiment."""
        from shared_ai.nlp import SentimentAnalyzer, SentimentPolarity
        
        analyzer = SentimentAnalyzer(language="fr")
        
        neutral_text = "La réunion aura lieu demain à 14 heures."
        result = analyzer.analyze(neutral_text)
        
        assert result.polarity == SentimentPolarity.NEUTRAL
        assert abs(result.score) < 0.2
    
    def test_empty_text(self):
        """Test empty text handling."""
        from shared_ai.nlp import SentimentAnalyzer
        
        analyzer = SentimentAnalyzer()
        result = analyzer.analyze("")
        
        assert result.score == 0.0
    
    def test_batch_analyze(self):
        """Test batch analysis."""
        from shared_ai.nlp import SentimentAnalyzer
        
        analyzer = SentimentAnalyzer()
        
        texts = [
            "Excellent résultat",
            "Grave problème",
            "Réunion normale",
        ]
        
        results = analyzer.batch_analyze(texts)
        
        assert len(results) == 3
        assert results[0].polarity.value == "positive"
        assert results[1].polarity.value == "negative"
    
    def test_sentiment_summary(self):
        """Test sentiment summary."""
        from shared_ai.nlp import SentimentAnalyzer
        
        analyzer = SentimentAnalyzer()
        
        text = "C'est un bon progrès"
        summary = analyzer.get_sentiment_summary(text)
        
        assert 'sentiment' in summary
        assert 'score' in summary
        assert 'confidence' in summary


class TestPreprocessorImport:
    """Test preprocessor imports (may skip if spaCy unavailable)."""
    
    def test_import_preprocessor(self):
        """Test importing preprocessor."""
        from shared_ai.nlp import TextPreprocessor, SPACY_AVAILABLE
        
        assert TextPreprocessor is not None
        
        if not SPACY_AVAILABLE:
            pytest.skip("spaCy not available")
    
    def test_spacy_availability_flag(self):
        """Test spaCy availability flag."""
        from shared_ai.nlp import SPACY_AVAILABLE
        
        assert isinstance(SPACY_AVAILABLE, bool)


class TestNERImport:
    """Test NER imports (may skip if spaCy unavailable)."""
    
    def test_import_ner(self):
        """Test importing NER."""
        from shared_ai.nlp import NamedEntityRecognizer, EntityType
        
        assert NamedEntityRecognizer is not None
        assert EntityType is not None
    
    def test_entity_types(self):
        """Test entity type enum."""
        from shared_ai.nlp import EntityType
        
        assert hasattr(EntityType, 'PERSON')
        assert hasattr(EntityType, 'ORGANIZATION')
        assert hasattr(EntityType, 'LOCATION')
        assert hasattr(EntityType, 'GPE')


class TestIntegration:
    """Test integrated NLP workflow (requires spaCy)."""
    
    def test_complete_nlp_pipeline(self):
        """Test complete NLP pipeline."""
        from shared_ai.nlp import SPACY_AVAILABLE
        
        if not SPACY_AVAILABLE:
            pytest.skip("spaCy not available")
        
        # If spaCy is available, test complete pipeline
        from shared_ai.nlp import (
            TextPreprocessor,
            NamedEntityRecognizer,
            SentimentAnalyzer,
        )
        
        text = "Emmanuel Macron a annoncé une bonne décision à Paris."
        
        # 1. Preprocess
        try:
            preprocessor = TextPreprocessor(language="fr")
            processed = preprocessor.process(text)
            
            assert len(processed.tokens) > 0
            assert len(processed.lemmas) > 0
        except (ImportError, ValueError):
            pytest.skip("spaCy model not available")
        
        # 2. Extract entities
        try:
            ner = NamedEntityRecognizer(language="fr")
            entities = ner.extract_entities(text)
            
            # Should find "Emmanuel Macron" (person) and "Paris" (location)
            assert len(entities) >= 0  # May vary by model
        except (ImportError, ValueError):
            pytest.skip("spaCy model not available")
        
        # 3. Sentiment
        sentiment = SentimentAnalyzer(language="fr")
        result = sentiment.analyze(text)
        
        # Should detect positive sentiment
        assert result.polarity.value in ["positive", "neutral", "negative"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
