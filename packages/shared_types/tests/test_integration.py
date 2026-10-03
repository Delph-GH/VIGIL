"""
Integration test for shared-types package.

Verifies that:
1. Package can be imported
2. All expected exports are available
3. Models and enums work together
4. Import paths are correct
"""

import pytest
import sys
from pathlib import Path


def test_package_imports():
    """Test that shared_types package can be imported."""
    try:
        import shared_types
        assert shared_types.__version__ == "0.1.0"
    except ImportError as e:
        pytest.fail(f"Cannot import shared_types: {e}")


def test_all_models_importable():
    """Test all models can be imported from package root."""
    from shared_types import (
        ScrapedArticle,
        ProcessedArticle,
        Entity,
        ScrapeResult,
        FailureReport,
        SourceConfig,
        ValidationResult,
    )
    
    # Verify they're classes/types, not None
    assert ScrapedArticle is not None
    assert ProcessedArticle is not None
    assert Entity is not None


def test_all_enums_importable():
    """Test all enums can be imported from package root."""
    from shared_types import (
        FailureCode,
        SourceStatus,
        ScrapeStrategy,
        ArticleStatus,
        Language,
        SourceCategory,
        ValidationRule,
        SentimentPolarity,
        EntityType,
        NarrativeStatus,
        TrustLevel,
    )
    
    # Verify they're enum types
    assert hasattr(FailureCode, '__members__')
    assert hasattr(Language, '__members__')


def test_create_article_with_enums():
    """Test creating article using both models and enums."""
    from shared_types import (
        ScrapedArticle,
        ScrapeStrategy,
        Language,
        SourceCategory,
    )
    
    article = ScrapedArticle(
        article_id="",
        url="https://example.com/test",
        source_name="Test Source",
        scraped_at="2024-05-16T10:00:00Z",
        extraction_strategy=ScrapeStrategy.RSS,
        language=Language.FRENCH,
        category=SourceCategory.POLITIQUE,
    )
    
    assert article.extraction_strategy == ScrapeStrategy.RSS
    assert article.language == Language.FRENCH
    assert article.category == SourceCategory.POLITIQUE


def test_create_processed_article():
    """Test creating ProcessedArticle from ScrapedArticle."""
    from shared_types import (
        ScrapedArticle,
        ProcessedArticle,
        ScrapeStrategy,
        Language,
        SentimentPolarity,
    )
    
    scraped = ScrapedArticle(
        article_id="test123",
        url="https://example.com/article",
        source_name="Le Monde",
        title="Test Article",
        body_text="Content...",
        scraped_at="2024-05-16T10:00:00Z",
        extraction_strategy=ScrapeStrategy.RSS,
        language=Language.FRENCH,
    )
    
    processed = ProcessedArticle.from_scraped_article(
        scraped,
        processed_at="2024-05-16T10:05:00Z",
        sentiment=SentimentPolarity.POSITIVE,
        sentiment_score=0.8,
        token_count=150,
    )
    
    assert processed.article_id == scraped.article_id
    assert processed.sentiment == SentimentPolarity.POSITIVE
    assert processed.language == Language.FRENCH


def test_failure_report_with_enum():
    """Test creating FailureReport with FailureCode enum."""
    from shared_types import (
        FailureReport,
        FailureCode,
        ScrapeStrategy,
    )
    
    report = FailureReport(
        source_name="Test",
        url="https://example.com/broken",
        timestamp="2024-05-16T10:00:00Z",
        failure_code=FailureCode.HTTP_404_NOT_FOUND,
        failure_detail="Page not found",
        http_status=404,
        strategy_attempted=ScrapeStrategy.STATIC_HTTP,
    )
    
    assert report.failure_code == FailureCode.HTTP_404_NOT_FOUND
    assert report.strategy_attempted == ScrapeStrategy.STATIC_HTTP


def test_validation_result():
    """Test ValidationResult model."""
    from shared_types import ValidationResult
    
    result = ValidationResult(
        article_id="test",
        approved=True,
        confidence_score=0.85,
        has_title=True,
        has_body=True,
        has_publication_date=False,  # NULL per anti-hallucination policy
    )
    
    assert result.approved is True
    assert result.confidence_score == 0.85
    assert result.has_publication_date is False


def test_source_config_with_strategies():
    """Test SourceConfig with multiple strategies."""
    from shared_types import (
        SourceConfig,
        SourceCategory,
        ScrapeStrategy,
        SourceStatus,
        Language,
    )
    
    config = SourceConfig(
        source_id="le_monde_001",
        name="Le Monde",
        url="https://lemonde.fr",
        category=SourceCategory.MEDIAS,
        language=Language.FRENCH,
        rss_url="https://lemonde.fr/rss",
        preferred_strategy=ScrapeStrategy.RSS,
        strategies=[
            ScrapeStrategy.RSS,
            ScrapeStrategy.STATIC_HTTP,
        ],
        status=SourceStatus.ACTIVE,
    )
    
    assert config.has_rss is True  # Auto-set from rss_url
    assert config.preferred_strategy == ScrapeStrategy.RSS
    assert len(config.strategies) == 2


def test_enum_to_string_conversion():
    """Test enum values are strings."""
    from shared_types import (
        Language,
        FailureCode,
        ScrapeStrategy,
    )
    
    # Enums should be string values
    assert Language.FRENCH == "fr"
    assert FailureCode.TIMEOUT == "timeout"
    assert ScrapeStrategy.RSS == "rss"
    
    # Can be serialized to JSON
    assert isinstance(Language.FRENCH.value, str)


def test_validate_enum_function():
    """Test validate_enum utility."""
    from shared_types import validate_enum, Language, FailureCode
    
    assert validate_enum("fr", Language) is True
    assert validate_enum("invalid", Language) is False
    assert validate_enum("timeout", FailureCode) is True
    assert validate_enum("xyz", FailureCode) is False


def test_article_id_generation():
    """Test article_id auto-generation from URL."""
    from shared_types import ScrapedArticle, ScrapeStrategy
    
    article1 = ScrapedArticle(
        article_id="",  # Will be auto-generated
        url="https://example.com/article",
        source_name="Test",
        scraped_at="2024-05-16T10:00:00Z",
        extraction_strategy=ScrapeStrategy.RSS,
    )
    
    article2 = ScrapedArticle(
        article_id="",
        url="https://example.com/article",  # Same URL
        source_name="Different Source",
        scraped_at="2024-05-16T11:00:00Z",
        extraction_strategy=ScrapeStrategy.STATIC_HTTP,
    )
    
    # Same URL → same ID (deduplication)
    assert article1.article_id == article2.article_id
    assert len(article1.article_id) == 64  # SHA-256 hex


def test_anti_hallucination_policy():
    """Test anti-hallucination: NULL dates preserved."""
    from shared_types import ScrapedArticle, ScrapeStrategy
    
    article = ScrapedArticle(
        article_id="",
        url="https://example.com/no-date",
        source_name="Test",
        scraped_at="2024-05-16T10:00:00Z",
        extraction_strategy=ScrapeStrategy.RSS,
        publication_date=None,  # NULL if not in metadata
    )
    
    # to_dict should preserve NULL, not invent a date
    data = article.to_dict()
    assert data["publication_date"] is None
    assert article.has_valid_date is False


def test_all_exports_accessible():
    """Test all __all__ exports are accessible."""
    import shared_types
    
    # Check __all__ is defined
    assert hasattr(shared_types, '__all__')
    
    # Check all listed exports are importable
    for name in shared_types.__all__:
        assert hasattr(shared_types, name), f"{name} not accessible"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
