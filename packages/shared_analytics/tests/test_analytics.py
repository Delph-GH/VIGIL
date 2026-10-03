"""
Tests for shared_analytics.

Tests salience and trust scoring.
"""

import pytest
from datetime import datetime, timedelta


class TestSalienceScorer:
    """Test salience scoring."""
    
    def test_import(self):
        """Test importing salience scorer."""
        from shared_analytics import SalienceScorer
        
        assert SalienceScorer is not None
    
    def test_basic_scoring(self):
        """Test basic salience scoring."""
        from shared_analytics import SalienceScorer
        from shared_types import ScrapedArticle, ScrapeStrategy
        
        scorer = SalienceScorer()
        
        # Create test article
        article = ScrapedArticle(
            article_id="test_001",
            url="https://example.com/article",
            source_name="Le Monde",
            scraped_at=datetime.now().isoformat(),
            extraction_strategy=ScrapeStrategy.STATIC_HTTP,
            title="Macron annonce une réforme",
            body_text="Le président Emmanuel Macron a annoncé une réforme importante.",
        )
        
        # Score
        score = scorer.score(
            article,
            important_entities=['Macron'],
            important_topics=['réforme'],
            trusted_sources=['Le Monde'],
        )
        
        assert 0.0 <= score <= 1.0
        assert score > 0.5  # Should score high (recent, relevant entities/topics, trusted source)
    
    def test_recency_decay(self):
        """Test recency decay."""
        from shared_analytics import SalienceScorer
        from shared_types import ScrapedArticle, ScrapeStrategy
        
        scorer = SalienceScorer()
        
        # Recent article
        recent_article = ScrapedArticle(
            article_id="recent",
            url="https://example.com/recent",
            source_name="Test",
            scraped_at=datetime.now().isoformat(),
            extraction_strategy=ScrapeStrategy.STATIC_HTTP,
            title="Recent news",
        )
        
        # Old article
        old_time = datetime.now() - timedelta(days=7)
        old_article = ScrapedArticle(
            article_id="old",
            url="https://example.com/old",
            source_name="Test",
            scraped_at=old_time.isoformat(),
            extraction_strategy=ScrapeStrategy.STATIC_HTTP,
            title="Old news",
        )
        
        recent_score = scorer.score(recent_article)
        old_score = scorer.score(old_article)
        
        assert recent_score > old_score  # Recent should score higher


class TestTrustScorer:
    """Test trust scoring."""
    
    def test_import(self):
        """Test importing trust scorer."""
        from shared_analytics import TrustScorer
        
        assert TrustScorer is not None
    
    def test_basic_scoring(self):
        """Test basic trust scoring."""
        from shared_analytics import TrustScorer
        
        scorer = TrustScorer()
        
        # Score known trusted source
        score = scorer.score_source(
            source_name="Le Monde",
            accuracy_rate=0.95,
            consistency_score=0.88,
            verification_status="verified",
            hallucination_rate=0.05,
        )
        
        assert 0.0 <= score <= 1.0
        assert score > 0.7  # Should score high (trusted source, good metrics)
    
    def test_known_sources(self):
        """Test known source reputation."""
        from shared_analytics import TrustScorer
        
        scorer = TrustScorer()
        
        # Known trusted source
        trusted_score = scorer.score_source("Le Monde")
        
        # Unknown source
        unknown_score = scorer.score_source("Unknown Blog")
        
        assert trusted_score > unknown_score
    
    def test_hallucination_penalty(self):
        """Test hallucination rate penalty."""
        from shared_analytics import TrustScorer
        
        scorer = TrustScorer()
        
        # Low hallucination
        low_hallucination = scorer.score_source(
            "Test Source",
            hallucination_rate=0.05,
        )
        
        # High hallucination
        high_hallucination = scorer.score_source(
            "Test Source",
            hallucination_rate=0.50,
        )
        
        assert low_hallucination > high_hallucination


class TestIntegration:
    """Test integrated usage."""
    
    def test_score_article_with_trust(self):
        """Test scoring article with trust context."""
        from shared_analytics import SalienceScorer, TrustScorer
        from shared_types import ScrapedArticle, ScrapeStrategy
        
        salience_scorer = SalienceScorer()
        trust_scorer = TrustScorer()
        
        # Create article
        article = ScrapedArticle(
            article_id="test",
            url="https://example.com/test",
            source_name="Le Monde",
            scraped_at=datetime.now().isoformat(),
            extraction_strategy=ScrapeStrategy.STATIC_HTTP,
            title="Important political news",
            body_text="Macron announces major reform.",
        )
        
        # Score salience
        salience = salience_scorer.score(
            article,
            important_entities=['Macron'],
            trusted_sources=['Le Monde'],
        )
        
        # Score source trust
        trust = trust_scorer.score_source("Le Monde")
        
        # Combined importance
        combined = salience * trust
        
        assert 0.0 <= combined <= 1.0
        assert combined > 0.5  # Both should be high


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
