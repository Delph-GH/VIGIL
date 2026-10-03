"""
Tests for shared_validation package.

Tests anti-hallucination detection, quality scoring, and human validation.
"""

import pytest
from datetime import datetime, timedelta

from shared_validation import (
    HallucinationDetector,
    QualityScorer,
    QualityRule,
    ValidationQueue,
    ValidationWorkflow,
    ValidationDecision,
    ValidationReview,
    score_article,
    validate_article,
)
from shared_types import ScrapedArticle, ValidationRule, ScrapeStrategy


class TestAntiHallucination:
    """Test hallucination detection."""
    
    def test_valid_article(self):
        """Test article with no hallucinations."""
        article = ScrapedArticle(
            article_id="test_001",
            url="https://example.com/article",
            source_name="Test Source",
            scraped_at=datetime.now().isoformat(),
            extraction_strategy=ScrapeStrategy.STATIC_HTTP,
            title="Test Article",
            body_text="This is a valid article with real content.",
        )
        
        detector = HallucinationDetector()
        issues = detector.detect(article)
        
        assert len(issues) == 0
    
    def test_malformed_url(self):
        """Test detection of malformed URL."""
        article = ScrapedArticle(
            article_id="test_002",
            url="not-a-valid-url",
            source_name="Test Source",
            scraped_at=datetime.now().isoformat(),
            extraction_strategy=ScrapeStrategy.STATIC_HTTP,
            title="Test",
            body_text="Content",
        )
        
        detector = HallucinationDetector()
        issues = detector.detect(article)
        
        # Should detect malformed URL
        url_issues = [i for i in issues if i.field == "url"]
        assert len(url_issues) > 0
        assert url_issues[0].severity == "CRITICAL"
    
    def test_future_date(self):
        """Test detection of future publication date."""
        future_date = (datetime.now() + timedelta(days=365)).isoformat()
        
        article = ScrapedArticle(
            article_id="test_003",
            url="https://example.com/article",
            source_name="Test Source",
            scraped_at=datetime.now().isoformat(),
            extraction_strategy=ScrapeStrategy.STATIC_HTTP,
            title="Test",
            body_text="Content",
            publication_date=future_date,
        )
        
        detector = HallucinationDetector()
        issues = detector.detect(article)
        
        # Should detect future date
        date_issues = [i for i in issues if i.field == "publication_date"]
        assert len(date_issues) > 0
        assert date_issues[0].severity == "CRITICAL"
    
    def test_llm_artifacts(self):
        """Test detection of LLM artifacts."""
        article = ScrapedArticle(
            article_id="test_004",
            url="https://example.com/article",
            source_name="Test Source",
            scraped_at=datetime.now().isoformat(),
            extraction_strategy=ScrapeStrategy.STATIC_HTTP,
            title="Test",
            body_text="As an AI, I cannot provide information about this topic.",
        )
        
        detector = HallucinationDetector()
        issues = detector.detect(article)
        
        # Should detect LLM artifact
        llm_issues = [i for i in issues if "LLM artifact" in i.description]
        assert len(llm_issues) > 0
        assert llm_issues[0].severity == "CRITICAL"
    
    def test_placeholder_text(self):
        """Test detection of placeholder text."""
        article = ScrapedArticle(
            article_id="test_005",
            url="https://example.com/article",
            source_name="Test Source",
            scraped_at=datetime.now().isoformat(),
            extraction_strategy=ScrapeStrategy.STATIC_HTTP,
            title="Test",
            body_text="Lorem ipsum dolor sit amet [insert content here]",
        )
        
        detector = HallucinationDetector()
        issues = detector.detect(article)
        
        # Should detect placeholders
        placeholder_issues = [i for i in issues if "Placeholder" in i.description or "placeholder" in i.description.lower()]
        assert len(placeholder_issues) > 0


class TestQualityScorer:
    """Test quality scoring."""
    
    def test_perfect_article(self):
        """Test article with all fields."""
        article = ScrapedArticle(
            article_id="test_001",
            url="https://example.com/article",
            source_name="Test Source",
            scraped_at=datetime.now().isoformat(),
            extraction_strategy=ScrapeStrategy.STATIC_HTTP,
            title="Complete Article Title",
            body_text="This is a substantial article with plenty of content. " * 10,
            author="John Doe",
            summary="Article summary",
            publication_date=datetime.now().isoformat(),
        )
        
        scorer = QualityScorer()
        score, results = scorer.score(article)
        
        # Should have high score
        assert score >= 90.0
        
        # All checks should pass
        failed = [r for r in results if not r.passed]
        assert len(failed) == 0
    
    def test_missing_critical_fields(self):
        """Test article missing critical fields."""
        article = ScrapedArticle(
            article_id="test_002",
            url="https://example.com/article",
            source_name="Test Source",
            scraped_at=datetime.now().isoformat(),
            extraction_strategy=ScrapeStrategy.STATIC_HTTP,
            # Missing title and body
        )
        
        scorer = QualityScorer()
        score, results = scorer.score(article)
        
        # Should have 0 score (critical failures)
        assert score == 0.0
        
        # Should have critical failures
        critical = scorer.get_failed_rules(results, severity=ValidationRule.CRITICAL)
        assert len(critical) > 0
    
    def test_medium_quality(self):
        """Test medium quality article."""
        article = ScrapedArticle(
            article_id="test_003",
            url="https://example.com/article",
            source_name="Test Source",
            scraped_at=datetime.now().isoformat(),
            extraction_strategy=ScrapeStrategy.STATIC_HTTP,
            title="Article Title",
            body_text="Short body text",  # Too short
            # Missing author, summary, date
        )
        
        scorer = QualityScorer()
        score, results = scorer.score(article)
        
        # Should have medium score
        assert 40.0 < score < 80.0
        
        # Should have some warnings/info failures
        failed = [r for r in results if not r.passed]
        assert len(failed) > 0
    
    def test_custom_rule(self):
        """Test adding custom quality rule."""
        scorer = QualityScorer()
        
        # Add custom rule
        scorer.add_rule(QualityRule(
            name="must_be_french",
            severity=ValidationRule.WARNING,
            description="Article must be in French",
            check_function=lambda a: (
                a.language and a.language.value == "fr",
                "Is French" if a.language and a.language.value == "fr" else "Not French"
            ),
            weight=0.5,
        ))
        
        # Test with non-French article
        from shared_types import Language
        article = ScrapedArticle(
            article_id="test_004",
            url="https://example.com/article",
            source_name="Test Source",
            scraped_at=datetime.now().isoformat(),
            extraction_strategy=ScrapeStrategy.STATIC_HTTP,
            title="Test",
            body_text="Content" * 50,
            language=Language.ENGLISH,
        )
        
        score, results = scorer.score(article)
        
        # Should have failure for custom rule
        custom_failures = [r for r in results if r.rule_name == "must_be_french"]
        assert len(custom_failures) == 1
        assert not custom_failures[0].passed


class TestValidationQueue:
    """Test human validation queue."""
    
    def test_add_and_get(self):
        """Test adding and retrieving articles."""
        queue = ValidationQueue()
        
        article = ScrapedArticle(
            article_id="test_001",
            url="https://example.com/article",
            source_name="Test",
            scraped_at=datetime.now().isoformat(),
            extraction_strategy=ScrapeStrategy.STATIC_HTTP,
            title="Test",
            body_text="Content",
        )
        
        queue.add(article, quality_score=45.0, reason="Low quality")
        
        # Should be able to retrieve
        next_article, metadata = queue.get_next()
        assert next_article.article_id == "test_001"
        assert metadata.quality_score == 45.0
    
    def test_priority_ordering(self):
        """Test articles are returned by priority."""
        queue = ValidationQueue()
        
        # Add articles with different quality scores
        for i, score in enumerate([80, 30, 95, 50]):
            article = ScrapedArticle(
                article_id=f"test_{i:03d}",
                url=f"https://example.com/article{i}",
                source_name="Test",
                scraped_at=datetime.now().isoformat(),
                extraction_strategy=ScrapeStrategy.STATIC_HTTP,
                title=f"Test {i}",
                body_text="Content",
            )
            queue.add(article, quality_score=score, reason="Review needed")
        
        # Should get lowest quality first (highest priority)
        next_article, metadata = queue.get_next()
        assert metadata.quality_score == 30.0  # Lowest score
    
    def test_submit_review(self):
        """Test submitting validation review."""
        queue = ValidationQueue()
        
        article = ScrapedArticle(
            article_id="test_001",
            url="https://example.com/article",
            source_name="Test",
            scraped_at=datetime.now().isoformat(),
            extraction_strategy=ScrapeStrategy.STATIC_HTTP,
            title="Test",
            body_text="Content",
        )
        
        queue.add(article, quality_score=50.0, reason="Review needed")
        
        # Submit review
        review = ValidationReview(
            article_id="test_001",
            reviewer_id="reviewer_123",
            decision=ValidationDecision.APPROVED,
            timestamp=datetime.now().isoformat(),
            notes="Looks good",
        )
        
        queue.submit_review("test_001", review)
        
        # Should have review
        reviews = queue.get_reviews("test_001")
        assert len(reviews) == 1
        assert reviews[0].decision == ValidationDecision.APPROVED
        
        # Should be removed from queue
        next_item = queue.get_next()
        assert next_item is None


class TestValidationWorkflow:
    """Test complete validation workflow."""
    
    def test_auto_approve_high_quality(self):
        """Test auto-approval for high quality articles."""
        workflow = ValidationWorkflow(
            quality_threshold=70.0,
            auto_approve_threshold=90.0,
        )
        
        article = ScrapedArticle(
            article_id="test_001",
            url="https://example.com/article",
            source_name="Test",
            scraped_at=datetime.now().isoformat(),
            extraction_strategy=ScrapeStrategy.STATIC_HTTP,
            title="Test",
            body_text="Content",
        )
        
        # High quality, no hallucinations
        decision = workflow.process_article(
            article=article,
            quality_score=95.0,
            hallucination_issues=[],
        )
        
        assert decision.decision == ValidationDecision.APPROVED
        assert decision.auto_decision is True
        assert decision.needs_review is False
    
    def test_auto_reject_critical_hallucination(self):
        """Test auto-rejection for critical hallucinations."""
        workflow = ValidationWorkflow()
        
        article = ScrapedArticle(
            article_id="test_002",
            url="https://example.com/article",
            source_name="Test",
            scraped_at=datetime.now().isoformat(),
            extraction_strategy=ScrapeStrategy.STATIC_HTTP,
            title="Test",
            body_text="Content",
        )
        
        # Has critical hallucination
        from shared_validation import HallucinationIssue
        issues = [
            HallucinationIssue(
                severity="CRITICAL",
                field="body_text",
                description="LLM artifact detected",
            )
        ]
        
        decision = workflow.process_article(
            article=article,
            quality_score=80.0,
            hallucination_issues=issues,
        )
        
        assert decision.decision == ValidationDecision.REJECTED
        assert decision.auto_decision is True
        assert decision.needs_review is False
    
    def test_needs_review_low_quality(self):
        """Test queuing for review (low quality)."""
        workflow = ValidationWorkflow(quality_threshold=70.0)
        
        article = ScrapedArticle(
            article_id="test_003",
            url="https://example.com/article",
            source_name="Test",
            scraped_at=datetime.now().isoformat(),
            extraction_strategy=ScrapeStrategy.STATIC_HTTP,
            title="Test",
            body_text="Content",
        )
        
        # Low quality
        decision = workflow.process_article(
            article=article,
            quality_score=50.0,
            hallucination_issues=[],
        )
        
        assert decision.decision == ValidationDecision.PENDING
        assert decision.needs_review is True
        assert decision.auto_decision is False


class TestIntegration:
    """Test integrated validation flow."""
    
    def test_complete_flow(self):
        """Test complete validation flow."""
        # Create article
        article = ScrapedArticle(
            article_id="test_001",
            url="https://example.com/article",
            source_name="Test Source",
            scraped_at=datetime.now().isoformat(),
            extraction_strategy=ScrapeStrategy.STATIC_HTTP,
            title="Test Article",
            body_text="This is a test article with sufficient content. " * 10,
            author="Test Author",
        )
        
        # 1. Check hallucinations
        is_valid, hallucination_issues = validate_article(article)
        assert is_valid is True  # No critical issues
        
        # 2. Score quality
        quality_score, details = score_article(article)
        assert quality_score > 0
        
        # 3. Process through workflow
        workflow = ValidationWorkflow()
        decision = workflow.process_article(
            article=article,
            quality_score=quality_score,
            hallucination_issues=hallucination_issues,
        )
        
        # Should have decision
        assert decision.decision in [
            ValidationDecision.APPROVED,
            ValidationDecision.PENDING,
        ]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
