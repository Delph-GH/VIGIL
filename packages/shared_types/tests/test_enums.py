"""
Tests for shared-types/enums.py

Validates all enum definitions and utility functions.
"""

import pytest
from shared_types.enums import (
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
    validate_enum,
)


class TestFailureCode:
    """Test FailureCode enum (19 codes)."""
    
    def test_all_codes_exist(self):
        """Verify all 19 failure codes are defined."""
        expected_codes = [
            # Network (4)
            "dns_failure",
            "tls_error",
            "timeout",
            "connection_error",
            # HTTP (5)
            "http_4xx",
            "http_5xx",
            "http_3xx_redirect_loop",
            "http_403_forbidden",
            "http_404_not_found",
            # Content (4)
            "antibot_detected",
            "cloudflare_challenge",
            "paywall_detected",
            "empty_response",
            "malformed_html",
            # Access (2)
            "robots_disallowed",
            "rate_limited",
            # Parsing (2)
            "parse_error",
            "encoding_error",
            # Unknown (1)
            "unknown_error",
        ]
        
        actual_codes = [code.value for code in FailureCode]
        assert len(actual_codes) == 19
        assert set(actual_codes) == set(expected_codes)
    
    def test_string_enum(self):
        """Verify FailureCode is a string enum."""
        assert isinstance(FailureCode.DNS_FAILURE.value, str)
        assert FailureCode.DNS_FAILURE == "dns_failure"
    
    def test_from_string(self):
        """Test creating FailureCode from string."""
        code = FailureCode("http_404_not_found")
        assert code == FailureCode.HTTP_NOT_FOUND


class TestScrapeStrategy:
    """Test ScrapeStrategy enum."""
    
    def test_all_strategies(self):
        """Verify all 4 strategies defined."""
        strategies = [s.value for s in ScrapeStrategy]
        assert strategies == ["rss", "static_http", "headless", "stealth"]
    
    def test_order_matters(self):
        """Verify strategies are in preference order."""
        # Order should be: RSS (fastest) → Static → Headless → Stealth (slowest)
        strategies = list(ScrapeStrategy)
        assert strategies[0] == ScrapeStrategy.RSS
        assert strategies[1] == ScrapeStrategy.STATIC_HTTP
        assert strategies[2] == ScrapeStrategy.HEADLESS
        assert strategies[3] == ScrapeStrategy.STEALTH


class TestArticleStatus:
    """Test ArticleStatus enum."""
    
    def test_pipeline_statuses(self):
        """Verify article pipeline statuses."""
        statuses = [s.value for s in ArticleStatus]
        
        # Should cover full pipeline
        assert "raw" in statuses              # Just scraped
        assert "validated" in statuses        # Anti-hallucination passed
        assert "flagged" in statuses          # Needs review
        assert "approved" in statuses         # Human approved
        assert "rejected" in statuses         # Rejected
        assert "processing" in statuses       # NLP in progress
        assert "processed" in statuses        # NLP complete
        assert "indexed" in statuses          # FAISS indexed
        assert "excluded" in statuses         # User excluded


class TestLanguage:
    """Test Language enum."""
    
    def test_supported_languages(self):
        """Verify French, German, English supported."""
        assert Language.FRENCH == "fr"
        assert Language.GERMAN == "de"
        assert Language.ENGLISH == "en"
        assert Language.UNKNOWN == "unknown"
    
    def test_diaspora_languages(self):
        """Diaspora uses FR, DE, EN."""
        diaspora_langs = [Language.FRENCH, Language.GERMAN, Language.ENGLISH]
        for lang in diaspora_langs:
            assert lang in Language
    
    def test_vigil_language(self):
        """Vigil primarily uses FR."""
        assert Language.FRENCH in Language


class TestSourceCategory:
    """Test SourceCategory enum."""
    
    def test_shared_categories(self):
        """Verify shared categories across platforms."""
        shared = [
            "communaute",
            "politique",
            "economie",
            "social",
            "institutionnel",
            "medias",
            "education",
            "sante",
            "culture",
        ]
        
        for cat in shared:
            assert cat in [c.value for c in SourceCategory]
    
    def test_diaspora_specific(self):
        """Verify diaspora-specific categories."""
        # Consulaire only exists for diaspora (cross-border)
        assert SourceCategory.CONSULAIRE.value == "consulaire"


class TestSentimentPolarity:
    """Test SentimentPolarity enum."""
    
    def test_basic_polarities(self):
        """Verify positive, neutral, negative."""
        assert SentimentPolarity.POSITIVE == "positive"
        assert SentimentPolarity.NEUTRAL == "neutral"
        assert SentimentPolarity.NEGATIVE == "negative"
    
    def test_mixed_sentiment(self):
        """Verify mixed sentiment exists."""
        assert SentimentPolarity.MIXED == "mixed"


class TestEntityType:
    """Test EntityType enum."""
    
    def test_ner_types(self):
        """Verify CamemBERT NER types."""
        assert EntityType.PERSON == "PER"
        assert EntityType.ORGANIZATION == "ORG"
        assert EntityType.LOCATION == "LOC"
        assert EntityType.INSTITUTION == "INST"
        assert EntityType.POLITICAL_PARTY == "PARTY"


class TestNarrativeStatus:
    """Test NarrativeStatus enum."""
    
    def test_lifecycle_stages(self):
        """Verify narrative lifecycle stages."""
        stages = [s.value for s in NarrativeStatus]
        
        # Should cover full lifecycle
        assert "emerging" in stages
        assert "amplifying" in stages
        assert "stable" in stages
        assert "saturating" in stages
        assert "declining" in stages
        assert "dormant" in stages
    
    def test_order(self):
        """Verify stages are in chronological order."""
        stages = list(NarrativeStatus)
        assert stages[0] == NarrativeStatus.EMERGING
        assert stages[-1] == NarrativeStatus.DORMANT


class TestValidateEnum:
    """Test validate_enum utility function."""
    
    def test_valid_values(self):
        """Test validation with valid enum values."""
        assert validate_enum("fr", Language) is True
        assert validate_enum("de", Language) is True
        assert validate_enum("dns_failure", FailureCode) is True
        assert validate_enum("rss", ScrapeStrategy) is True
    
    def test_invalid_values(self):
        """Test validation with invalid values."""
        assert validate_enum("invalid", Language) is False
        assert validate_enum("xyz", FailureCode) is False
        assert validate_enum("", ScrapeStrategy) is False
    
    def test_case_sensitive(self):
        """Verify validation is case-sensitive."""
        assert validate_enum("fr", Language) is True
        assert validate_enum("FR", Language) is False
        assert validate_enum("Fr", Language) is False
    
    def test_all_enums(self):
        """Test validate_enum works with all enum types."""
        test_cases = [
            ("fr", Language, True),
            ("active", SourceStatus, True),
            ("invalid", SourceStatus, False),
            ("positive", SentimentPolarity, True),
            ("PER", EntityType, True),
            ("INVALID", EntityType, False),
        ]
        
        for value, enum_class, expected in test_cases:
            assert validate_enum(value, enum_class) == expected


class TestEnumExhaustiveness:
    """Ensure all enums are properly tested."""
    
    def test_all_enums_imported(self):
        """Verify all enums can be imported."""
        # If this passes, all enums are accessible
        enums = [
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
        ]
        
        assert len(enums) == 11  # Total enum count


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
