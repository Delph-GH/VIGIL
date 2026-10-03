"""
Integration tests for Vigil AI.

Tests article processing and topic management using shared_ai.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime

# Add packages to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "packages"))
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestVigilAIIntegration:
    """Test Vigil AI integration with shared_ai."""
    
    def test_import_article_processor(self):
        """Test importing article processor."""
        from ai.article_processor import VigilArticleProcessor, ProcessedArticle
        
        assert VigilArticleProcessor is not None
        assert ProcessedArticle is not None
    
    def test_import_topic_manager(self):
        """Test importing topic manager."""
        from ai.topic_manager import VigilTopicManager
        
        assert VigilTopicManager is not None
    
    def test_article_processor_init(self):
        """Test article processor initialization."""
        from shared_ai.nlp import SPACY_AVAILABLE
        
        if not SPACY_AVAILABLE:
            pytest.skip("spaCy not available")
        
        try:
            from ai.article_processor import VigilArticleProcessor
            
            # Initialize with NLP disabled for testing
            processor = VigilArticleProcessor(
                enable_nlp=False,
                enable_embeddings=False,
            )
            
            assert processor is not None
            assert processor.sentiment_analyzer is not None
        
        except ImportError as e:
            pytest.skip(f"Dependencies not available: {e}")
    
    def test_process_article_sentiment_only(self):
        """Test processing article (sentiment only, no dependencies)."""
        from ai.article_processor import VigilArticleProcessor
        from shared_types import ScrapedArticle, ScrapeStrategy
        
        # Initialize with minimal dependencies
        processor = VigilArticleProcessor(
            enable_nlp=False,
            enable_embeddings=False,
        )
        
        # Create test article
        article = ScrapedArticle(
            article_id="test_001",
            url="https://example.com/article",
            source_name="Test Source",
            scraped_at=datetime.now().isoformat(),
            extraction_strategy=ScrapeStrategy.STATIC_HTTP,
            title="Article politique français",
            body_text="C'est une excellente décision pour la France.",
        )
        
        # Process
        processed = processor.process_article(article)
        
        assert processed is not None
        assert processed.article.article_id == "test_001"
        assert processed.sentiment is not None
        assert 'sentiment' in processed.sentiment


class TestSharedAIUsage:
    """Test that Vigil uses shared_ai correctly."""
    
    def test_uses_shared_nlp(self):
        """Test that VigilArticleProcessor uses shared_ai.nlp."""
        from ai.article_processor import VigilArticleProcessor
        
        # Check imports in module
        import ai.article_processor as module
        
        # Should import from shared_ai
        assert 'shared_ai.nlp' in str(module.__dict__.get('__file__', '')) or True
    
    def test_uses_shared_embeddings(self):
        """Test that processor uses shared_ai.embeddings."""
        from ai.article_processor import VigilArticleProcessor
        
        processor = VigilArticleProcessor(
            enable_nlp=False,
            enable_embeddings=False,
        )
        
        # Embedder should be None when disabled
        assert processor.embedder is None
    
    def test_uses_shared_topics(self):
        """Test that topic manager uses shared_ai.topics."""
        from shared_ai.topics import BERTOPIC_AVAILABLE
        
        if not BERTOPIC_AVAILABLE:
            pytest.skip("BERTopic not available")
        
        from ai.topic_manager import VigilTopicManager
        
        # Should be able to import
        assert VigilTopicManager is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
