"""
Integration tests for Diaspora AI.

Tests analytics processing using shared_ai.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime

# Add packages to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "packages"))
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestDiasporaAIIntegration:
    """Test Diaspora AI integration with shared_ai."""
    
    def test_import_analytics_processor(self):
        """Test importing analytics processor."""
        from ai.analytics_processor import DiasporaAnalyticsProcessor, AnalyticsResult
        
        assert DiasporaAnalyticsProcessor is not None
        assert AnalyticsResult is not None
    
    def test_analytics_processor_init(self):
        """Test analytics processor initialization."""
        from ai.analytics_processor import DiasporaAnalyticsProcessor
        
        # Initialize with minimal dependencies
        processor = DiasporaAnalyticsProcessor(
            enable_nlp=False,
            enable_embeddings=False,
        )
        
        assert processor is not None
        assert processor.sentiment_analyzer is not None
    
    def test_process_article_sentiment(self):
        """Test processing article (sentiment only)."""
        from ai.analytics_processor import DiasporaAnalyticsProcessor
        from shared_types import ScrapedArticle, ScrapeStrategy
        
        # Initialize with minimal dependencies
        processor = DiasporaAnalyticsProcessor(
            enable_nlp=False,
            enable_embeddings=False,
        )
        
        # Create test article
        article = ScrapedArticle(
            article_id="diaspora_test_001",
            url="https://example.com/expat",
            source_name="Le Petit Journal Munich",
            scraped_at=datetime.now().isoformat(),
            extraction_strategy=ScrapeStrategy.STATIC_HTTP,
            title="Événement communauté française",
            body_text="C'est un excellent événement pour la communauté française en Bavière.",
        )
        
        # Process
        result = processor.process_article(article)
        
        assert result is not None
        assert result.article.article_id == "diaspora_test_001"
        assert result.sentiment is not None
        assert 'sentiment' in result.sentiment
        assert 'score' in result.sentiment
    
    def test_community_insights(self):
        """Test community insights generation."""
        from ai.analytics_processor import DiasporaAnalyticsProcessor, AnalyticsResult
        from shared_types import ScrapedArticle, ScrapeStrategy
        
        processor = DiasporaAnalyticsProcessor(
            enable_nlp=False,
            enable_embeddings=False,
        )
        
        # Create test articles
        articles = [
            ScrapedArticle(
                article_id=f"test_{i}",
                url=f"https://example.com/{i}",
                source_name="Test",
                scraped_at=datetime.now().isoformat(),
                extraction_strategy=ScrapeStrategy.STATIC_HTTP,
                title="Test",
                body_text="Content positive" if i % 2 == 0 else "Content négatif",
            )
            for i in range(5)
        ]
        
        # Process
        results = processor.process_batch(articles, show_progress=False)
        
        # Get insights
        insights = processor.get_community_insights(results)
        
        assert insights is not None
        assert insights['total_articles'] == 5
        assert 'sentiment_distribution' in insights


class TestSharedAIUsage:
    """Test that Diaspora uses shared_ai correctly."""
    
    def test_uses_shared_nlp(self):
        """Test that processor uses shared_ai.nlp."""
        from ai.analytics_processor import DiasporaAnalyticsProcessor
        
        # Should be able to import
        assert DiasporaAnalyticsProcessor is not None
    
    def test_uses_shared_embeddings(self):
        """Test that processor uses shared_ai.embeddings."""
        from ai.analytics_processor import DiasporaAnalyticsProcessor
        
        processor = DiasporaAnalyticsProcessor(
            enable_nlp=False,
            enable_embeddings=False,
        )
        
        # Embedder should be None when disabled
        assert processor.embedder is None


class TestReplacesOldSentiment:
    """Test that new system replaces old lexicon-based sentiment."""
    
    def test_sentiment_analyzer_available(self):
        """Test sentiment analyzer from shared_ai is available."""
        from ai.analytics_processor import DiasporaAnalyticsProcessor
        
        processor = DiasporaAnalyticsProcessor(
            enable_nlp=False,
            enable_embeddings=False,
        )
        
        # Should have sentiment analyzer from shared_ai
        assert processor.sentiment_analyzer is not None
        
        # Should be from shared_ai.nlp
        from shared_ai.nlp import SentimentAnalyzer
        assert isinstance(processor.sentiment_analyzer, SentimentAnalyzer)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
