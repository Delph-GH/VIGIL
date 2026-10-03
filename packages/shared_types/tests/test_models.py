"""
Tests for shared-types/models.py

Validates ScrapedArticle, ProcessedArticle, and related models.
"""

import pytest
from datetime import datetime
from shared_types.models import (
    ScrapedArticle,
    ProcessedArticle,
    Entity,
    ValidationResult,
    SourceConfig,
    ScrapeResult,
    FailureReport,
)
from shared_types.enums import (
    FailureCode,
    ScrapeStrategy,
    ArticleStatus,
    Language,
    SourceCategory,
    SentimentPolarity,
    EntityType,
    SourceStatus,
)


class TestScrapedArticle:
    """Test ScrapedArticle model."""
    
    def test_create_minimal(self):
        """Test creating article with minimal fields."""
        article = ScrapedArticle(
            article_id="",  # Will be auto-generated
            url="https://example.com/article",
            source_name="Test Source",
            scraped_at="2024-05-16T10:00:00Z",
            extraction_strategy=ScrapeStrategy.RSS,
        )
        
        assert article.url == "https://example.com/article"
        assert article.source_name == "Test Source"
        assert article.article_id != ""  # Auto-generated
        assert len(article.article_id) == 64  # SHA-256 hex length
    
    def test_article_id_generation(self):
        """Test article_id is SHA-256 of URL."""
        url = "https://example.com/test"
        article = ScrapedArticle(
            article_id="",
            url=url,
            source_name="Test",
            scraped_at="2024-05-16T10:00:00Z",
            extraction_strategy=ScrapeStrategy.RSS,
        )
        
        # Same URL should always generate same ID
        article2 = ScrapedArticle(
            article_id="",
            url=url,
            source_name="Different Source",
            scraped_at="2024-05-16T11:00:00Z",
            extraction_strategy=ScrapeStrategy.STATIC_HTTP,
        )
        
        assert article.article_id == article2.article_id
        assert len(article.article_id) == 64
    
    def test_anti_hallucination_null_date(self):
        """Test publication_date can be NULL (anti-hallucination policy)."""
        article = ScrapedArticle(
            article_id="",
            url="https://example.com/no-date",
            source_name="Test",
            scraped_at="2024-05-16T10:00:00Z",
            extraction_strategy=ScrapeStrategy.RSS,
            publication_date=None,  # NULL if not in metadata
        )
        
        assert article.publication_date is None
        assert article.has_valid_date is False
    
    def test_with_publication_date(self):
        """Test article with valid publication date."""
        article = ScrapedArticle(
            article_id="",
            url="https://example.com/dated",
            source_name="Test",
            scraped_at="2024-05-16T10:00:00Z",
            extraction_strategy=ScrapeStrategy.RSS,
            publication_date="2024-05-15T14:30:00Z",
        )
        
        assert article.publication_date == "2024-05-15T14:30:00Z"
        assert article.has_valid_date is True
    
    def test_has_content_property(self):
        """Test has_content property."""
        # No content
        article1 = ScrapedArticle(
            article_id="",
            url="https://example.com/1",
            source_name="Test",
            scraped_at="2024-05-16T10:00:00Z",
            extraction_strategy=ScrapeStrategy.RSS,
        )
        assert article1.has_content is False
        
        # Has title only
        article2 = ScrapedArticle(
            article_id="",
            url="https://example.com/2",
            source_name="Test",
            scraped_at="2024-05-16T10:00:00Z",
            extraction_strategy=ScrapeStrategy.RSS,
            title="Test Title",
        )
        assert article2.has_content is False
        
        # Has both title and body
        article3 = ScrapedArticle(
            article_id="",
            url="https://example.com/3",
            source_name="Test",
            scraped_at="2024-05-16T10:00:00Z",
            extraction_strategy=ScrapeStrategy.RSS,
            title="Test Title",
            body_text="Test body content.",
        )
        assert article3.has_content is True
    
    def test_to_dict(self):
        """Test serialization to dictionary."""
        article = ScrapedArticle(
            article_id="",
            url="https://example.com/article",
            source_name="Le Monde",
            title="Test Article",
            body_text="Content...",
            publication_date=None,  # NULL preserved
            language=Language.FRENCH,
            category=SourceCategory.POLITIQUE,
            scraped_at="2024-05-16T10:00:00Z",
            extraction_strategy=ScrapeStrategy.RSS,
            confidence_score=0.85,
        )
        
        data = article.to_dict()
        
        assert data["url"] == "https://example.com/article"
        assert data["title"] == "Test Article"
        assert data["publication_date"] is None  # Preserves NULL
        assert data["language"] == "fr"
        assert data["category"] == "politique"
        assert data["confidence_score"] == 0.85


class TestProcessedArticle:
    """Test ProcessedArticle model."""
    
    def test_create_from_scraped(self):
        """Test creating ProcessedArticle from ScrapedArticle."""
        scraped = ScrapedArticle(
            article_id="test123",
            url="https://example.com/article",
            source_name="Test Source",
            title="Test Title",
            body_text="Test content.",
            scraped_at="2024-05-16T10:00:00Z",
            extraction_strategy=ScrapeStrategy.RSS,
        )
        
        processed = ProcessedArticle.from_scraped_article(
            scraped,
            processed_at="2024-05-16T10:05:00Z",
            sentiment=SentimentPolarity.POSITIVE,
            sentiment_score=0.75,
            token_count=100,
        )
        
        # Base fields preserved
        assert processed.article_id == "test123"
        assert processed.url == scraped.url
        assert processed.title == scraped.title
        
        # NLP fields added
        assert processed.sentiment == SentimentPolarity.POSITIVE
        assert processed.sentiment_score == 0.75
        assert processed.token_count == 100
    
    def test_entities(self):
        """Test entity extraction."""
        entities = [
            Entity(
                text="Emmanuel Macron",
                entity_type=EntityType.PERSON,
                start_char=0,
                end_char=15,
                confidence=0.98,
            ),
            Entity(
                text="Assemblée Nationale",
                entity_type=EntityType.INSTITUTION,
                start_char=20,
                end_char=39,
                confidence=0.95,
            ),
        ]
        
        processed = ProcessedArticle(
            article_id="test",
            url="https://example.com",
            source_name="Test",
            title="Test",
            body_text="Test",
            publication_date=None,
            author=None,
            language=Language.FRENCH,
            category=None,
            scraped_at="2024-05-16T10:00:00Z",
            processed_at="2024-05-16T10:05:00Z",
            entities=entities,
        )
        
        assert len(processed.entities) == 2
        assert processed.entities[0].text == "Emmanuel Macron"
        assert processed.entities[0].entity_type == EntityType.PERSON
        assert processed.entities[1].text == "Assemblée Nationale"
        assert processed.entities[1].entity_type == EntityType.INSTITUTION
    
    def test_to_dict_with_entities(self):
        """Test serialization includes entities."""
        entities = [
            Entity(
                text="Paris",
                entity_type=EntityType.LOCATION,
                start_char=0,
                end_char=5,
            )
        ]
        
        processed = ProcessedArticle(
            article_id="test",
            url="https://example.com",
            source_name="Test",
            title="Test",
            body_text="Test",
            publication_date=None,
            author=None,
            language=Language.FRENCH,
            category=None,
            scraped_at="2024-05-16T10:00:00Z",
            processed_at="2024-05-16T10:05:00Z",
            entities=entities,
        )
        
        data = processed.to_dict()
        
        assert len(data["entities"]) == 1
        assert data["entities"][0]["text"] == "Paris"
        assert data["entities"][0]["type"] == "LOC"
        assert data["entities"][0]["start"] == 0
        assert data["entities"][0]["end"] == 5


class TestValidationResult:
    """Test ValidationResult model."""
    
    def test_auto_human_review_low_confidence(self):
        """Test auto-flagging for human review at low confidence."""
        result = ValidationResult(
            article_id="test",
            approved=False,
            confidence_score=0.42,  # < 0.5
        )
        
        assert result.requires_human_review is True
    
    def test_no_human_review_high_confidence(self):
        """Test no flagging for high confidence."""
        result = ValidationResult(
            article_id="test",
            approved=True,
            confidence_score=0.85,
        )
        
        assert result.requires_human_review is False
    
    def test_with_issues(self):
        """Test validation with issues."""
        result = ValidationResult(
            article_id="test",
            approved=False,
            confidence_score=0.30,
            issues=["No publication date", "No author"],
            warnings=["Unusual content length"],
            has_publication_date=False,
            has_author=False,
        )
        
        assert len(result.issues) == 2
        assert len(result.warnings) == 1
        assert result.has_publication_date is False
        assert result.requires_human_review is True


class TestSourceConfig:
    """Test SourceConfig model."""
    
    def test_minimal_config(self):
        """Test minimal source configuration."""
        config = SourceConfig(
            source_id="test_001",
            name="Test Source",
            url="https://example.com",
            category=SourceCategory.MEDIAS,
        )
        
        assert config.source_id == "test_001"
        assert config.preferred_strategy == ScrapeStrategy.RSS
        assert config.enabled is True
        assert config.status == SourceStatus.ACTIVE
    
    def test_rss_config(self):
        """Test RSS configuration."""
        config = SourceConfig(
            source_id="test_rss",
            name="Test RSS",
            url="https://example.com",
            category=SourceCategory.MEDIAS,
            rss_url="https://example.com/feed.xml",
        )
        
        assert config.rss_url == "https://example.com/feed.xml"
        assert config.has_rss is True  # Auto-set
    
    def test_custom_strategies(self):
        """Test custom strategy list."""
        config = SourceConfig(
            source_id="test_headless",
            name="JS-Heavy Site",
            url="https://example.com",
            category=SourceCategory.MEDIAS,
            requires_js=True,
            strategies=[
                ScrapeStrategy.HEADLESS,
                ScrapeStrategy.STEALTH,
            ],
        )
        
        assert config.requires_js is True
        assert len(config.strategies) == 2
        assert ScrapeStrategy.HEADLESS in config.strategies


class TestFailureReport:
    """Test FailureReport model."""
    
    def test_create_failure_report(self):
        """Test creating failure report."""
        report = FailureReport(
            source_name="Test Source",
            url="https://example.com/broken",
            timestamp="2024-05-16T10:00:00Z",
            failure_code=FailureCode.HTTP_404_NOT_FOUND,
            failure_detail="Page not found",
            http_status=404,
        )
        
        assert report.failure_code == FailureCode.HTTP_404_NOT_FOUND
        assert report.http_status == 404
        assert report.dns_ok is True  # Default
    
    def test_to_dict(self):
        """Test serialization."""
        report = FailureReport(
            source_name="Test",
            url="https://example.com",
            timestamp="2024-05-16T10:00:00Z",
            failure_code=FailureCode.CLOUDFLARE_CHALLENGE,
            failure_detail="Cloudflare detected",
            body_class="cloudflare",
        )
        
        data = report.to_dict()
        
        assert data["failure_code"] == "cloudflare_challenge"
        assert data["body_class"] == "cloudflare"


class TestScrapeResult:
    """Test ScrapeResult model."""
    
    def test_successful_scrape(self):
        """Test successful scrape result."""
        articles = [
            ScrapedArticle(
                article_id="",
                url="https://example.com/1",
                source_name="Test",
                scraped_at="2024-05-16T10:00:00Z",
                extraction_strategy=ScrapeStrategy.RSS,
            ),
            ScrapedArticle(
                article_id="",
                url="https://example.com/2",
                source_name="Test",
                scraped_at="2024-05-16T10:00:00Z",
                extraction_strategy=ScrapeStrategy.RSS,
            ),
        ]
        
        result = ScrapeResult(
            source_name="Test",
            timestamp="2024-05-16T10:00:00Z",
            success=True,
            articles=articles,
            strategy_used=ScrapeStrategy.RSS,
            duration_ms=1500,
        )
        
        assert result.success is True
        assert result.articles_found == 2  # Auto-set
        assert result.failure is None
    
    def test_failed_scrape(self):
        """Test failed scrape result."""
        failure = FailureReport(
            source_name="Test",
            url="https://example.com",
            timestamp="2024-05-16T10:00:00Z",
            failure_code=FailureCode.TIMEOUT,
            failure_detail="Request timeout after 30s",
        )
        
        result = ScrapeResult(
            source_name="Test",
            timestamp="2024-05-16T10:00:00Z",
            success=False,
            failure=failure,
        )
        
        assert result.success is False
        assert result.articles_found == 0
        assert result.failure is not None
        assert result.failure.failure_code == FailureCode.TIMEOUT


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
