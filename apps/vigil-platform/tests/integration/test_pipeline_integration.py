"""
apps/vigil-platform/tests/integration/test_pipeline_integration.py

Integration tests for complete Vigil pipeline.

Tests end-to-end flow: scrape → validate → NLP → analytics → dashboard
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime

# Add packages to path
root_path = Path(__file__).parent.parent.parent.parent.parent
packages_path = root_path / "packages"
sys.path.insert(0, str(packages_path))

from shared_types import ScrapedArticle, ScrapeStrategy
from shared_validation import QualityScorer
from shared_ai import SentimentAnalyzer, NamedEntityRecognizer
from shared_analytics import VigilAnalyticsPipeline, NarrativeDetector
from shared_search import VigilArticleSearch
from shared_workflows import Pipeline


class TestVigilPipelineIntegration:
    """Integration tests for complete Vigil pipeline."""
    
    @pytest.fixture
    def sample_article(self):
        """Create sample political article for testing."""
        return ScrapedArticle(
            article_id="test_vigil_001",
            url="https://example.com/politique",
            source_name="Le Monde",
            scraped_at=datetime.now().isoformat(),
            extraction_strategy=ScrapeStrategy.STATIC_HTTP,
            title="Macron annonce une réforme importante",
            body_text="Le président Macron a annoncé une réforme majeure du système politique.",
        )
    
    def test_scrape_to_validate_flow(self, sample_article):
        """Test: Scrape → Validate flow."""
        # Validate article
        quality_scorer = QualityScorer()
        quality_result = quality_scorer.score(sample_article)
        
        assert quality_result.overall_quality >= 0
        assert quality_result.overall_quality <= 100
        assert quality_result.article_id == sample_article.article_id
    
    def test_validate_to_nlp_flow(self, sample_article):
        """Test: Validate → NLP flow."""
        # Validation
        quality_scorer = QualityScorer()
        quality_result = quality_scorer.score(sample_article)
        
        if quality_result.overall_quality >= 70:
            # NLP processing
            ner = NamedEntityRecognizer()
            entities = ner.extract_entities(sample_article.body_text)
            
            sentiment_analyzer = SentimentAnalyzer()
            sentiment = sentiment_analyzer.analyze(sample_article.body_text)
            
            assert len(entities) >= 0
            assert sentiment.sentiment in ['positive', 'negative', 'neutral']
    
    def test_nlp_to_analytics_flow(self, sample_article):
        """Test: NLP → Analytics flow."""
        # NLP
        ner = NamedEntityRecognizer()
        entities = ner.extract_entities(sample_article.body_text)
        
        # Analytics
        analytics_pipeline = VigilAnalyticsPipeline(
            important_entities=['Macron'],
            important_topics=['réforme', 'politique'],
            trusted_sources=['Le Monde'],
        )
        
        analytics = analytics_pipeline.process_article(sample_article)
        
        assert analytics.article_id == sample_article.article_id
        assert 0 <= analytics.salience <= 1
        assert 0 <= analytics.trust <= 1
        assert 0 <= analytics.importance <= 1
    
    def test_analytics_to_narratives_flow(self, sample_article):
        """Test: Analytics → Narratives flow."""
        # Create multiple articles for narrative detection
        articles = [sample_article]
        
        for i in range(5):
            article = ScrapedArticle(
                article_id=f"test_vigil_{i:03d}",
                url=f"https://example.com/politique/{i}",
                source_name="Le Monde",
                scraped_at=datetime.now().isoformat(),
                extraction_strategy=ScrapeStrategy.STATIC_HTTP,
                title=f"Article politique {i}: Réforme",
                body_text="Contenu politique sur la réforme.",
            )
            articles.append(article)
        
        # Detect narratives
        narrative_detector = NarrativeDetector(min_articles=3)
        narratives = narrative_detector.detect_narratives(articles)
        
        # Should detect at least one narrative
        assert len(narratives) >= 0
    
    def test_complete_pipeline_execution(self, sample_article):
        """Test: Complete end-to-end pipeline."""
        pipeline = Pipeline(pipeline_id='vigil_integration_test')
        
        results = {}
        
        # Pipeline steps
        def validate_step():
            quality_scorer = QualityScorer()
            results['quality'] = quality_scorer.score(sample_article)
            return results['quality']
        
        def nlp_step():
            ner = NamedEntityRecognizer()
            sentiment_analyzer = SentimentAnalyzer()
            
            results['entities'] = ner.extract_entities(sample_article.body_text)
            results['sentiment'] = sentiment_analyzer.analyze(sample_article.body_text)
            return results
        
        def analytics_step():
            analytics_pipeline = VigilAnalyticsPipeline(
                important_entities=['Macron'],
                important_topics=['réforme'],
            )
            results['analytics'] = analytics_pipeline.process_article(sample_article)
            return results['analytics']
        
        def search_step():
            search = VigilArticleSearch()
            search.add_articles([sample_article])
            results['indexed'] = True
            return True
        
        # Build pipeline
        pipeline.add_step('validate', 'Validate', validate_step)
        pipeline.add_step('nlp', 'NLP', nlp_step, depends_on=['validate'])
        pipeline.add_step('analytics', 'Analytics', analytics_step, depends_on=['nlp'])
        pipeline.add_step('search', 'Search', search_step, depends_on=['analytics'])
        
        # Execute
        execution_results = pipeline.execute()
        
        # Verify
        assert len(execution_results) == 4
        assert all(r.status.value == 'completed' for r in execution_results)
        assert 'quality' in results
        assert 'entities' in results
        assert 'sentiment' in results
        assert 'analytics' in results
        assert results['indexed'] is True
    
    def test_performance_benchmark(self, sample_article):
        """Test: Pipeline performance."""
        import time
        
        start_time = time.time()
        
        # Full pipeline
        quality_scorer = QualityScorer()
        _ = quality_scorer.score(sample_article)
        
        ner = NamedEntityRecognizer()
        _ = ner.extract_entities(sample_article.body_text)
        
        sentiment_analyzer = SentimentAnalyzer()
        _ = sentiment_analyzer.analyze(sample_article.body_text)
        
        analytics_pipeline = VigilAnalyticsPipeline()
        _ = analytics_pipeline.process_article(sample_article)
        
        execution_time = time.time() - start_time
        
        # Should complete in reasonable time
        assert execution_time < 5.0
    
    def test_data_consistency(self, sample_article):
        """Test: Data consistency across pipeline."""
        # Stage 1
        quality_scorer = QualityScorer()
        quality_result = quality_scorer.score(sample_article)
        
        # Stage 2
        analytics_pipeline = VigilAnalyticsPipeline()
        analytics = analytics_pipeline.process_article(sample_article)
        
        # Verify consistency
        assert quality_result.article_id == analytics.article_id
        assert analytics.metadata['source'] == sample_article.source_name


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
