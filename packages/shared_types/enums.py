"""
shared-types/enums.py

Common enumerations used across Diaspora and Vigil platforms.

Extracted from:
- Diaspora: scraping/diagnostics.py (FailureCode taxonomy)
- Both platforms: various status and strategy enums
"""

from enum import Enum, auto


class FailureCode(str, Enum):
    """
    19-code failure taxonomy for scraping diagnostics.
    
    Source: Diaspora's scraping/diagnostics.py
    
    Categories:
    - Network: DNS, TLS, Timeout
    - HTTP: 4XX, 5XX, Redirect issues
    - Content: Antibot, Cloudflare, Paywall, Empty, Malformed
    - Access: Robots disallowed, Rate limited
    - Parsing: Parse errors, Encoding issues
    """
    
    # Network failures
    DNS_FAILURE = "dns_failure"
    TLS_ERROR = "tls_error"
    TIMEOUT = "timeout"
    CONNECTION_ERROR = "connection_error"
    
    # HTTP failures
    HTTP_4XX = "http_4xx"
    HTTP_5XX = "http_5xx"
    HTTP_3XX_REDIRECT_LOOP = "http_3xx_redirect_loop"
    HTTP_FORBIDDEN = "http_403_forbidden"
    HTTP_NOT_FOUND = "http_404_not_found"
    
    # Content/Access failures
    ANTIBOT_DETECTED = "antibot_detected"
    CLOUDFLARE_CHALLENGE = "cloudflare_challenge"
    PAYWALL_DETECTED = "paywall_detected"
    EMPTY_RESPONSE = "empty_response"
    MALFORMED_HTML = "malformed_html"
    
    # Access control
    ROBOTS_DISALLOWED = "robots_disallowed"
    RATE_LIMITED = "rate_limited"
    
    # Parsing failures
    PARSE_ERROR = "parse_error"
    ENCODING_ERROR = "encoding_error"
    
    # Unknown
    UNKNOWN_ERROR = "unknown_error"


class SourceStatus(str, Enum):
    """
    Source operational status.
    
    Used in source health monitoring.
    """
    ACTIVE = "active"
    RATE_LIMITED = "rate_limited"
    PAYWALL = "paywall"
    ERROR = "error"
    DISABLED = "disabled"
    PENDING = "pending"


class ScrapeStrategy(str, Enum):
    """
    Scraping strategies in order of preference.
    
    MultiStrategyEngine tries these in order:
    1. RSS (fastest, most reliable)
    2. Static HTTP (simple GET request)
    3. Headless (JavaScript rendering with Playwright)
    4. Stealth (anti-detection mode)
    """
    RSS = "rss"
    STATIC_HTTP = "static_http"
    HEADLESS = "headless"
    STEALTH = "stealth"


class ArticleStatus(str, Enum):
    """
    Article processing status.
    
    Tracks article through validation → processing pipeline.
    """
    RAW = "raw"                      # Just scraped, not validated
    VALIDATED = "validated"          # Passed anti-hallucination checks
    FLAGGED = "flagged"             # Low confidence, needs human review
    APPROVED = "approved"            # Human validated
    REJECTED = "rejected"            # Human or auto-rejected
    PROCESSING = "processing"        # NLP in progress
    PROCESSED = "processed"          # NLP complete
    INDEXED = "indexed"             # Added to FAISS
    EXCLUDED = "excluded"           # User manually excluded


class Language(str, Enum):
    """
    Supported languages.
    
    Diaspora: French, German, English (Bavaria/BW context)
    Vigil: French (national politics)
    """
    FRENCH = "fr"
    GERMAN = "de"
    ENGLISH = "en"
    UNKNOWN = "unknown"


class SourceCategory(str, Enum):
    """
    Source categorization.
    
    Shared categories across platforms.
    Platform-specific categories defined in app configs.
    """
    # Shared categories
    COMMUNAUTE = "communaute"
    POLITIQUE = "politique"
    ECONOMIE = "economie"
    SOCIAL = "social"
    INSTITUTIONNEL = "institutionnel"
    MEDIAS = "medias"
    EDUCATION = "education"
    SANTE = "sante"
    CULTURE = "culture"
    
    # Diaspora-specific (cross-border)
    CONSULAIRE = "consulaire"
    
    # Vigil-specific (national politics)
    PARLIAMENTARY = "parliamentary"  # Assemblée, Sénat
    PARTIES = "parties"              # Political parties
    GOVERNMENT = "government"        # Ministries, Presidency
    THINK_TANKS = "think_tanks"      # Policy research
    
    # Data sources
    OPEN_DATA = "open_data"
    
    # Community
    FORUMS = "forums"
    REDDIT = "reddit"


class ValidationRule(str, Enum):
    """
    Validation rule severity levels.
    
    Source: Vigil's validation/quality_scorer.py
    """
    CRITICAL = "critical"      # Must pass (e.g., HTTP 200)
    MAJOR = "major"           # Should pass (e.g., has title)
    MINOR = "minor"           # Nice to have (e.g., has author)


class SentimentPolarity(str, Enum):
    """
    Sentiment classification.
    
    Used by both lexicon-based and transformer-based analyzers.
    """
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    MIXED = "mixed"


class EntityType(str, Enum):
    """
    Named entity types for political analysis.
    
    Based on CamemBERT NER model output.
    """
    PERSON = "PER"
    ORGANIZATION = "ORG"
    LOCATION = "LOC"
    INSTITUTION = "INST"
    POLITICAL_PARTY = "PARTY"
    DATE = "DATE"
    MISCELLANEOUS = "MISC"


class NarrativeStatus(str, Enum):
    """
    Narrative lifecycle stages.
    
    Source: Vigil's narratives/evolution_tracker.py
    """
    EMERGING = "emerging"          # <30 days old, growing
    AMPLIFYING = "amplifying"      # 30-60 days, accelerating
    STABLE = "stable"             # 60-90 days, plateau
    SATURATING = "saturating"      # >90 days, peak fatigue
    DECLINING = "declining"        # Volume dropping
    DORMANT = "dormant"           # <5 mentions/week


class TrustLevel(str, Enum):
    """
    Institutional trust levels.
    
    Calibrated to CEVIPOF survey data.
    """
    VERY_HIGH = "very_high"    # >70%
    HIGH = "high"              # 50-70%
    MEDIUM = "medium"          # 30-50%
    LOW = "low"                # 10-30%
    VERY_LOW = "very_low"      # <10%


# Utility function for enum validation
def validate_enum(value: str, enum_class: type[Enum]) -> bool:
    """
    Validate if a string value is a valid enum member.
    
    Args:
        value: String to validate
        enum_class: Enum class to check against
        
    Returns:
        True if valid, False otherwise
        
    Example:
        >>> validate_enum("fr", Language)
        True
        >>> validate_enum("invalid", Language)
        False
    """
    try:
        enum_class(value)
        return True
    except (ValueError, KeyError):
        return False


# Export all enums
__all__ = [
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
    "validate_enum",
]
