"""
apps/diaspora-platform/tests/integration/test_pipeline_integration.py

Integration tests for complete Diaspora pipeline.

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

from shared_types import ScrapedArticle, ScrapeStrategy, ValidationStatus
from shared_validation import QualityScorer, HallucinationDetector
from shared_ai import SentimentAnalyzer, TextPreprocessor
from shared_analytics import DiasporaAnalyticsPipeline
from shared_search import DiasporaCommunitySearch
from shared_workflows import Pipeline


class TestDiasporaPipelineIntegration:
    """Integration tests for complete Diaspora pipeline."""
    
    @pytest.fixture
    def sample_article(self):
        """Create sample article for testing."""
        return ScrapedArticle(
            article_id="test_diaspora_001",
            url="https://example.com/test",
            source_name="Le Petit Journal Munich",
            scraped_at=datetime.now().isoformat(),
            extraction_strategy=ScrapeStrategy.STATIC_HTTP,
            title="Community event in Munich",
            body_text="The French expat community in Munich is organizing a summer festival.",
        )
    
    def test_scrape_to_validate_flow(self, sample_article):
        """Test: Scrape → Validate flow."""
        # Scrape stage (article already scraped)
        assert sample_article.article_id is not None
        assert sample_article.body_text is not None
        
        # Validate stage
        quality_scorer = QualityScorer()
        quality_result = quality_scorer.score(sample_article)
        
        assert quality_result.overall_quality >= 0
        assert quality_result.overall_quality <= 100
        assert quality_result.validation_status in [
            ValidationStatus.APPROVED,
            ValidationStatus.NEEDS_REVIEW,
            ValidationStatus.REJECTED,
        ]
        
        # Verify data flows correctly
        assert quality_result.article_id == sample_article.article_id
    
    def test_validate_to_nlp_flow(self, sample_article):
        """Test: Validate → NLP flow."""
        # Validation stage
        quality_scorer = QualityScorer()
        quality_result = quality_scorer.score(sample_article)
        
        # Only proceed with quality articles
        if quality_result.overall_quality >= 70:
            # NLP stage
            preprocessor = TextPreprocessor()
            processed_text = preprocessor.clean_text(sample_article.body_text)
            
            sentiment_analyzer = SentimentAnalyzer()
            sentiment_result = sentiment_analyzer.analyze(processed_text)
            
            assert sentiment_result.sentiment in ['positive', 'negative', 'neutral']
            assert 0 <= sentiment_result.confidence <= 1
    
    def test_nlp_to_analytics_flow(self, sample_article):
        """Test: NLP → Analytics flow."""
        # NLP stage
        sentiment_analyzer = SentimentAnalyzer()
        sentiment_result = sentiment_analyzer.analyze(sample_article.body_text)
        
        # Analytics stage
        analytics_pipeline = DiasporaAnalyticsPipeline(
            important_entities=['community', 'Munich'],
            important_topics=['event', 'festival'],
        )
        
        analytics = analytics_pipeline.process_article(sample_article)
        
        assert analytics.article_id == sample_article.article_id
        assert 0 <= analytics.salience <= 1
        assert 0 <= analytics.trust <= 1
        assert 0 <= analytics.importance <= 1
    
    def test_analytics_to_search_flow(self, sample_article):
        """Test: Analytics → Search flow."""
        # Analytics stage
        analytics_pipeline = DiasporaAnalyticsPipeline()
        analytics = analytics_pipeline.process_article(sample_article)
        
        # Search indexing
        search = DiasporaCommunitySearch()
        search.add_articles([sample_article])
        
        # Verify article is searchable
        results = search.search_by_topic("community", top_k=5)
        
        assert len(results) > 0
        assert any(r['article_id'] == sample_article.article_id for r in results)
    
    def test_complete_pipeline_execution(self, sample_article):
        """Test: Complete end-to-end pipeline."""
        # Create pipeline
        pipeline = Pipeline(pipeline_id='diaspora_integration_test')
        
        # Track results
        results = {}
        
        # Step 1: Validate
        def validate_step():
            quality_scorer = QualityScorer()
            results['quality'] = quality_scorer.score(sample_article)
            return results['quality']
        
        # Step 2: Analyze NLP
        def nlp_step():
            sentiment_analyzer = SentimentAnalyzer()
            results['sentiment'] = sentiment_analyzer.analyze(sample_article.body_text)
            return results['sentiment']
        
        # Step 3: Compute Analytics
        def analytics_step():
            analytics_pipeline = DiasporaAnalyticsPipeline()
            results['analytics'] = analytics_pipeline.process_article(sample_article)
            return results['analytics']
        
        # Step 4: Index for Search
        def search_step():
            search = DiasporaCommunitySearch()
            search.add_articles([sample_article])
            results['indexed'] = True
            return True
        
        # Add steps
        pipeline.add_step('validate', 'Validate Quality', validate_step)
        pipeline.add_step('nlp', 'NLP Analysis', nlp_step, depends_on=['validate'])
        pipeline.add_step('analytics', 'Compute Analytics', analytics_step, depends_on=['nlp'])
        pipeline.add_step('search', 'Index Search', search_step, depends_on=['analytics'])
        
        # Execute
        execution_results = pipeline.execute()
        
        # Verify all steps completed
        assert len(execution_results) == 4
        assert all(r.status.value == 'completed' for r in execution_results)
        
        # Verify data integrity
        assert 'quality' in results
        assert 'sentiment' in results
        assert 'analytics' in results
        assert results['indexed'] is True
    
    def test_error_handling_in_pipeline(self):
        """Test: Error handling across pipeline stages."""
        # Create invalid article
        invalid_article = ScrapedArticle(
            article_id="test_invalid",
            url="https://example.com/invalid",
            source_name="Invalid Source",
            scraped_at=datetime.now().isoformat(),
            extraction_strategy=ScrapeStrategy.STATIC_HTTP,
            title="",  # Empty title
            body_text="",  # Empty body
        )
        
        # Quality scorer should handle empty content
        quality_scorer = QualityScorer()
        quality_result = quality_scorer.score(invalid_article)
        
        # Should still return a result, even if low quality
        assert quality_result.overall_quality is not None
        assert quality_result.overall_quality <= 50  # Low quality expected
    
    def test_performance_benchmark(self, sample_article):
        """Test: Pipeline performance benchmark."""
        import time
        
        # Measure complete pipeline execution time
        start_time = time.time()
        
        # Execute pipeline
        quality_scorer = QualityScorer()
        _ = quality_scorer.score(sample_article)
        
        sentiment_analyzer = SentimentAnalyzer()
        _ = sentiment_analyzer.analyze(sample_article.body_text)
        
        analytics_pipeline = DiasporaAnalyticsPipeline()
        _ = analytics_pipeline.process_article(sample_article)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Pipeline should complete in reasonable time
        assert execution_time < 5.0  # Less than 5 seconds
    
    def test_data_consistency_across_stages(self, sample_article):
        """Test: Data consistency maintained across stages."""
        # Stage 1: Validation
        quality_scorer = QualityScorer()
        quality_result = quality_scorer.score(sample_article)
        
        # Stage 2: Analytics
        analytics_pipeline = DiasporaAnalyticsPipeline()
        analytics = analytics_pipeline.process_article(sample_article)
        
        # Verify article_id consistency
        assert quality_result.article_id == sample_article.article_id
        assert analytics.article_id == sample_article.article_id
        
        # Verify metadata consistency
        assert analytics.metadata['source'] == sample_article.source_name
        assert analytics.metadata['title'] == sample_article.title


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
