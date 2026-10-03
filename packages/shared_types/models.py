"""
shared-types/models.py

Core data models shared across Diaspora and Vigil platforms.

Models:
- ScrapedArticle: Raw article from scraping (pre-validation)
- ProcessedArticle: Article after NLP processing
- ValidationResult: Validation output
- SourceConfig: Source configuration
- ScrapeResult: Scraping operation result
- FailureReport: Detailed failure diagnostics

Design principles:
- Immutable where possible (use frozen dataclasses)
- Explicit None handling (anti-hallucination)
- Timestamps in ISO 8601 format
- All text fields are str (Unicode)
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path
import hashlib

from .enums import (
    FailureCode,
    SourceStatus,
    ScrapeStrategy,
    ArticleStatus,
    Language,
    SourceCategory,
    SentimentPolarity,
    EntityType,
)


# ============================================================================
# SCRAPING MODELS (Pre-Validation)
# ============================================================================

@dataclass
class ScrapedArticle:
    """
    Raw article data from scraping, before validation.
    
    Source: Diaspora's scraping/engine.py output
    
    Key principles:
    - publication_date can be NULL (anti-hallucination policy)
    - article_id is SHA-256(url) for deduplication
    - Raw HTML snapshot path for traceability
    """
    
    # Identity
    article_id: str                    # SHA-256(url), generated automatically
    url: str                           # Original URL
    
    # Source metadata
    source_name: str                   # Source identifier
    scraped_at: str                    # ISO 8601 timestamp
    extraction_strategy: ScrapeStrategy  # How it was scraped
    
    # Content
    title: Optional[str] = None
    body_text: Optional[str] = None
    
    # Metadata (can be NULL if not in source)
    publication_date: Optional[str] = None  # ISO 8601 or NULL (anti-hallucination)
    author: Optional[str] = None
    language: Language = Language.UNKNOWN
    category: Optional[SourceCategory] = None
    
    # Technical metadata
    response_ms: Optional[int] = None       # Response time in milliseconds
    http_status: int = 200
    html_snapshot_path: Optional[str] = None  # Path to raw HTML file
    
    # Validation state
    status: ArticleStatus = ArticleStatus.RAW
    confidence_score: float = 0.0           # Set by validator
    is_excluded: bool = False               # User-flagged
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Generate article_id from URL if not provided."""
        if not self.article_id:
            self.article_id = self._generate_id(self.url)
    
    @staticmethod
    def _generate_id(url: str) -> str:
        """Generate SHA-256 hash of URL for article ID."""
        return hashlib.sha256(url.encode('utf-8')).hexdigest()
    
    @property
    def has_valid_date(self) -> bool:
        """Check if article has a valid publication date."""
        return self.publication_date is not None
    
    @property
    def has_content(self) -> bool:
        """Check if article has both title and body."""
        return bool(self.title and self.body_text)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "article_id": self.article_id,
            "url": self.url,
            "source_name": self.source_name,
            "title": self.title,
            "body_text": self.body_text,
            "publication_date": self.publication_date,  # Preserve NULL
            "author": self.author,
            "language": self.language.value,
            "category": self.category.value if self.category else None,
            "scraped_at": self.scraped_at,
            "extraction_strategy": self.extraction_strategy.value,
            "response_ms": self.response_ms,
            "http_status": self.http_status,
            "html_snapshot_path": self.html_snapshot_path,
            "status": self.status.value,
            "confidence_score": self.confidence_score,
            "is_excluded": self.is_excluded,
            "metadata": self.metadata,
        }


# ============================================================================
# PROCESSING MODELS (Post-NLP)
# ============================================================================

@dataclass
class Entity:
    """Named entity extracted from text."""
    text: str                          # Entity surface form
    entity_type: EntityType            # PER, ORG, LOC, etc.
    start_char: int                    # Start position in text
    end_char: int                      # End position in text
    confidence: float = 1.0            # NER confidence score


@dataclass
class ProcessedArticle:
    """
    Article after NLP processing.
    
    Source: Vigil's processing/models.py
    
    Extends ScrapedArticle with NLP annotations:
    - Sentiment analysis
    - Named entity recognition
    - Topic assignment
    - Embeddings (for FAISS)
    """
    
    # Base article (from ScrapedArticle)
    article_id: str
    url: str
    source_name: str
    title: Optional[str]
    body_text: Optional[str]
    publication_date: Optional[str]
    author: Optional[str]
    language: Language
    category: Optional[SourceCategory]
    scraped_at: str
    
    # NLP annotations
    processed_at: str                   # ISO 8601 timestamp
    
    # Sentiment
    sentiment: SentimentPolarity = SentimentPolarity.NEUTRAL
    sentiment_score: float = 0.0        # -1.0 to +1.0
    sentiment_confidence: float = 0.0   # 0.0 to 1.0
    
    # Entities
    entities: List[Entity] = field(default_factory=list)
    
    # Topics
    topic_id: Optional[int] = None      # BERTopic cluster ID
    topic_label: Optional[str] = None   # Human-readable topic name
    topic_confidence: float = 0.0
    
    # Embeddings
    embedding: Optional[List[float]] = None  # 768-dim sentence-camembert
    
    # Token statistics
    token_count: int = 0
    sentence_count: int = 0
    
    # Processing metadata
    nlp_model_version: str = "unknown"  # e.g., "spacy-3.7.4"
    processing_errors: List[str] = field(default_factory=list)
    
    # Status
    status: ArticleStatus = ArticleStatus.PROCESSED
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "article_id": self.article_id,
            "url": self.url,
            "source_name": self.source_name,
            "title": self.title,
            "body_text": self.body_text,
            "publication_date": self.publication_date,
            "author": self.author,
            "language": self.language.value,
            "category": self.category.value if self.category else None,
            "scraped_at": self.scraped_at,
            "processed_at": self.processed_at,
            "sentiment": self.sentiment.value,
            "sentiment_score": self.sentiment_score,
            "sentiment_confidence": self.sentiment_confidence,
            "entities": [
                {
                    "text": e.text,
                    "type": e.entity_type.value,
                    "start": e.start_char,
                    "end": e.end_char,
                    "confidence": e.confidence,
                }
                for e in self.entities
            ],
            "topic_id": self.topic_id,
            "topic_label": self.topic_label,
            "topic_confidence": self.topic_confidence,
            "token_count": self.token_count,
            "sentence_count": self.sentence_count,
            "nlp_model_version": self.nlp_model_version,
            "status": self.status.value,
        }
    
    @classmethod
    def from_scraped_article(cls, scraped: ScrapedArticle, **nlp_fields) -> "ProcessedArticle":
        """
        Create ProcessedArticle from ScrapedArticle + NLP results.
        
        Args:
            scraped: Base ScrapedArticle
            **nlp_fields: NLP annotation fields
            
        Returns:
            ProcessedArticle with merged data
        """
        return cls(
            article_id=scraped.article_id,
            url=scraped.url,
            source_name=scraped.source_name,
            title=scraped.title,
            body_text=scraped.body_text,
            publication_date=scraped.publication_date,
            author=scraped.author,
            language=scraped.language,
            category=scraped.category,
            scraped_at=scraped.scraped_at,
            **nlp_fields
        )


# ============================================================================
# VALIDATION MODELS
# ============================================================================

@dataclass
class ValidationResult:
    """
    Result of article validation.
    
    Source: Diaspora's scraping/validator.py
    """
    
    article_id: str
    approved: bool                      # Pass/fail
    confidence_score: float             # 0.0-1.0
    
    # Issues found
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # Validation details
    has_http_200: bool = True
    has_title: bool = False
    has_body: bool = False
    has_publication_date: bool = False
    has_author: bool = False
    
    # Suggested action
    requires_human_review: bool = False
    
    def __post_init__(self):
        """Auto-determine if human review needed."""
        if self.confidence_score < 0.5:
            self.requires_human_review = True


# ============================================================================
# SOURCE CONFIGURATION
# ============================================================================

@dataclass
class SourceConfig:
    """
    Source configuration.
    
    Loaded from YAML files in app-specific source configs.
    """
    
    # Identity
    source_id: str                      # Unique identifier
    name: str                           # Display name
    url: str                            # Base URL
    
    # Categorization
    category: SourceCategory
    language: Language = Language.FRENCH
    
    # Scraping strategy
    preferred_strategy: ScrapeStrategy = ScrapeStrategy.RSS
    strategies: List[ScrapeStrategy] = field(default_factory=lambda: [
        ScrapeStrategy.RSS,
        ScrapeStrategy.STATIC_HTTP,
        ScrapeStrategy.HEADLESS,
    ])
    
    # RSS config
    rss_url: Optional[str] = None
    has_rss: bool = False
    
    # Scraping hints
    requires_js: bool = False           # Needs headless browser
    has_antibot: bool = False           # Has bot detection
    
    # Rate limiting
    rate_limit_delay: int = 5           # Seconds between requests
    
    # Status
    status: SourceStatus = SourceStatus.ACTIVE
    enabled: bool = True
    
    # Metadata
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Auto-set has_rss flag."""
        if self.rss_url:
            self.has_rss = True


# ============================================================================
# SCRAPING RESULTS
# ============================================================================

@dataclass
class FailureReport:
    """
    Detailed failure diagnostics.
    
    Source: Diaspora's scraping/diagnostics.py (19-code taxonomy)
    """
    
    source_name: str
    url: str
    timestamp: str                      # ISO 8601
    
    # Failure classification
    failure_code: FailureCode
    failure_detail: str                 # Human-readable explanation
    
    # Technical details
    http_status: Optional[int] = None
    dns_ok: bool = True
    tls_ok: bool = True
    
    # Detection details
    body_class: Optional[str] = None    # "antibot", "cloudflare", etc.
    strategy_attempted: ScrapeStrategy = ScrapeStrategy.STATIC_HTTP
    retry_number: int = 0
    
    # Full context
    detail_json: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "source_name": self.source_name,
            "url": self.url,
            "timestamp": self.timestamp,
            "failure_code": self.failure_code.value,
            "failure_detail": self.failure_detail,
            "http_status": self.http_status,
            "dns_ok": self.dns_ok,
            "tls_ok": self.tls_ok,
            "body_class": self.body_class,
            "strategy_attempted": self.strategy_attempted.value,
            "retry_number": self.retry_number,
            "detail_json": self.detail_json,
        }


@dataclass
class ScrapeResult:
    """
    Result of a scraping operation.
    
    Either contains articles OR a failure report.
    """
    
    source_name: str
    timestamp: str                      # ISO 8601
    success: bool
    
    # Success case
    articles: List[ScrapedArticle] = field(default_factory=list)
    articles_found: int = 0
    strategy_used: Optional[ScrapeStrategy] = None
    
    # Failure case
    failure: Optional[FailureReport] = None
    
    # Performance
    duration_ms: int = 0
    
    def __post_init__(self):
        """Auto-set articles_found."""
        if self.success:
            self.articles_found = len(self.articles)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Scraping
    "ScrapedArticle",
    "ScrapeResult",
    "FailureReport",
    "SourceConfig",
    
    # Processing
    "ProcessedArticle",
    "Entity",
    
    # Validation
    "ValidationResult",
]
