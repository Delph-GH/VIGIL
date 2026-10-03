"""
shared-types

Common data models and enumerations for French Intelligence Monorepo.

This package provides the foundational types used across:
- Diaspora Platform (French expats in Germany)
- Vigil Platform (French national politics)

Usage:
    from shared_types import ScrapedArticle, ProcessedArticle, FailureCode
    
    article = ScrapedArticle(
        article_id="",  # Auto-generated from URL
        url="https://example.com/article",
        source_name="Le Monde",
        title="Example Article",
        body_text="Content...",
        publication_date=None,  # NULL if not in metadata (anti-hallucination)
        scraped_at="2024-05-16T10:00:00Z",
        extraction_strategy=ScrapeStrategy.RSS,
    )
"""

from .models import (
    # Scraping models
    ScrapedArticle,
    ScrapeResult,
    FailureReport,
    SourceConfig,
    
    # Processing models
    ProcessedArticle,
    Entity,
    
    # Validation models
    ValidationResult,
)

from .enums import (
    # Core enums
    FailureCode,
    SourceStatus,
    ScrapeStrategy,
    ArticleStatus,
    Language,
    SourceCategory,
    
    # Analysis enums
    ValidationRule,
    SentimentPolarity,
    EntityType,
    NarrativeStatus,
    TrustLevel,
    
    # Utilities
    validate_enum,
)

__version__ = "0.1.0"

__all__ = [
    # Models
    "ScrapedArticle",
    "ProcessedArticle",
    "Entity",
    "ScrapeResult",
    "FailureReport",
    "SourceConfig",
    "ValidationResult",
    
    # Enums
    "FailureCode",
    "SourceStatus",
    "ScrapeStrategy",
    "ArticleStatus",
    "Language",
    "SourceCategory",
    "ValidationRule",
    "SentimentPolarity",
    "EntityType",
    "NarrativeStatus",
    "TrustLevel",
    
    # Utilities
    "validate_enum",
]
