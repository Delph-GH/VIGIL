"""
Tests for shared_utils package.

Tests text cleaning, date parsing, and URL normalization.
"""

import pytest
from datetime import datetime, timezone, timedelta
from shared_utils import (
    # Text utilities
    clean_html,
    normalize_unicode,
    remove_extra_whitespace,
    clean_text,
    truncate_text,
    extract_sentences,
    
    # Date utilities
    parse_iso8601,
    parse_flexible_date,
    to_iso8601,
    get_current_timestamp,
    is_valid_date,
    format_relative_date,
    
    # URL utilities
    normalize_url,
    remove_tracking_params,
    hash_url,
    extract_domain,
    is_valid_url,
    join_url_parts,
    get_url_path,
)


class TestTextCleaner:
    """Test text cleaning utilities."""
    
    def test_clean_html(self):
        """Test HTML tag removal."""
        html = "<p>Hello <b>world</b>!</p>"
        assert clean_html(html) == "Hello world!"
        
        # With script tags
        html = "<p>Text</p><script>alert('xss')</script>"
        assert "alert" not in clean_html(html)
    
    def test_normalize_unicode(self):
        """Test Unicode normalization."""
        # é as two characters (e + combining accent) → single character
        text = "café"
        normalized = normalize_unicode(text)
        assert isinstance(normalized, str)
    
    def test_remove_extra_whitespace(self):
        """Test whitespace normalization."""
        text = "Hello   \n  world\t!"
        assert remove_extra_whitespace(text) == "Hello world !"
    
    def test_clean_text_full_pipeline(self):
        """Test full cleaning pipeline."""
        html = "<p>Hello™   <b>world</b>®!</p>"
        cleaned = clean_text(html, remove_html=True, remove_special=True)
        assert cleaned == "Hello world!"
    
    def test_truncate_text(self):
        """Test text truncation."""
        text = "A very long text that should be truncated"
        truncated = truncate_text(text, max_length=15)
        assert len(truncated) == 15
        assert truncated.endswith("...")
    
    def test_extract_sentences(self):
        """Test sentence extraction."""
        text = "First sentence. Second sentence! Third?"
        sentences = extract_sentences(text)
        assert len(sentences) == 3
        assert sentences[0] == "First sentence."


class TestDateParser:
    """Test date parsing utilities."""
    
    def test_parse_iso8601(self):
        """Test ISO 8601 parsing."""
        dt = parse_iso8601("2024-05-16T10:30:00Z")
        assert dt is not None
        assert dt.year == 2024
        assert dt.month == 5
        assert dt.day == 16
    
    def test_parse_iso8601_invalid(self):
        """Test ISO 8601 with invalid input."""
        assert parse_iso8601("invalid") is None
        assert parse_iso8601("") is None
    
    def test_parse_flexible_date_iso(self):
        """Test flexible parser with ISO format."""
        dt = parse_flexible_date("2024-05-16")
        assert dt is not None
        assert dt.year == 2024
        assert dt.month == 5
        assert dt.day == 16
    
    def test_parse_flexible_date_french(self):
        """Test French date format."""
        dt = parse_flexible_date("16/05/2024")
        assert dt is not None
        assert dt.day == 16
        assert dt.month == 5
        assert dt.year == 2024
    
    def test_parse_flexible_date_german(self):
        """Test German date format."""
        dt = parse_flexible_date("16.05.2024")
        assert dt is not None
        assert dt.day == 16
        assert dt.month == 5
    
    def test_parse_flexible_date_invalid(self):
        """Test with invalid date."""
        assert parse_flexible_date("not a date") is None
        assert parse_flexible_date("32/13/2024") is None
    
    def test_to_iso8601(self):
        """Test datetime to ISO 8601 conversion."""
        dt = datetime(2024, 5, 16, 10, 30, 0, tzinfo=timezone.utc)
        iso = to_iso8601(dt)
        assert iso == "2024-05-16T10:30:00Z"
    
    def test_get_current_timestamp(self):
        """Test current timestamp generation."""
        timestamp = get_current_timestamp()
        assert isinstance(timestamp, str)
        assert "T" in timestamp
        assert timestamp.endswith("Z")
    
    def test_is_valid_date(self):
        """Test date validation."""
        assert is_valid_date("2024-05-16") is True
        assert is_valid_date("16/05/2024") is True
        assert is_valid_date("invalid") is False
    
    def test_format_relative_date(self):
        """Test relative date formatting."""
        now = datetime.now(timezone.utc)
        
        # 2 hours ago
        two_hours_ago = now - timedelta(hours=2)
        relative = format_relative_date(two_hours_ago)
        assert "hour" in relative
        
        # Just now
        just_now = now - timedelta(seconds=30)
        relative = format_relative_date(just_now)
        assert relative == "just now"


class TestURLNormalizer:
    """Test URL normalization utilities."""
    
    def test_normalize_url_basic(self):
        """Test basic URL normalization."""
        url = "HTTPS://Example.COM/Path/"
        normalized = normalize_url(url)
        assert normalized == "https://example.com/Path"
    
    def test_normalize_url_query_params(self):
        """Test query parameter sorting."""
        url = "https://example.com/path?b=2&a=1"
        normalized = normalize_url(url)
        assert normalized == "https://example.com/path?a=1&b=2"
    
    def test_normalize_url_remove_query(self):
        """Test query parameter removal."""
        url = "https://example.com/path?key=value"
        normalized = normalize_url(url, remove_query=True)
        assert "?" not in normalized
    
    def test_normalize_url_default_port(self):
        """Test default port removal."""
        url = "https://example.com:443/path"
        normalized = normalize_url(url)
        assert ":443" not in normalized
    
    def test_remove_tracking_params(self):
        """Test tracking parameter removal."""
        url = "https://example.com/article?utm_source=twitter&id=123"
        cleaned = remove_tracking_params(url)
        assert "utm_source" not in cleaned
        assert "id=123" in cleaned
    
    def test_hash_url(self):
        """Test URL hashing."""
        url1 = "https://example.com/article"
        url2 = "https://example.com/article"
        url3 = "https://example.com/different"
        
        hash1 = hash_url(url1)
        hash2 = hash_url(url2)
        hash3 = hash_url(url3)
        
        # Same URL → same hash
        assert hash1 == hash2
        # Different URL → different hash
        assert hash1 != hash3
        # SHA-256 → 64 hex chars
        assert len(hash1) == 64
    
    def test_extract_domain(self):
        """Test domain extraction."""
        assert extract_domain("https://www.example.com/path") == "example.com"
        assert extract_domain("http://example.com") == "example.com"
        assert extract_domain("invalid") is None
    
    def test_is_valid_url(self):
        """Test URL validation."""
        assert is_valid_url("https://example.com") is True
        assert is_valid_url("http://example.com/path") is True
        assert is_valid_url("not a url") is False
        assert is_valid_url("") is False
    
    def test_join_url_parts(self):
        """Test URL joining."""
        url = join_url_parts("https://example.com", "api", "v1", "users")
        assert url == "https://example.com/api/v1/users"
    
    def test_get_url_path(self):
        """Test path extraction."""
        url = "https://example.com/path/to/article?id=123"
        path = get_url_path(url)
        assert path == "/path/to/article"


class TestCrossPackageImports:
    """Test that shared_utils can work with shared_types."""
    
    def test_hash_url_with_scraped_article(self):
        """Test using hash_url for article_id generation."""
        from shared_types import ScrapedArticle, ScrapeStrategy
        
        url = "https://example.com/article"
        article_id = hash_url(url)
        
        # Use in ScrapedArticle
        article = ScrapedArticle(
            article_id=article_id,
            url=url,
            source_name="Test",
            scraped_at=get_current_timestamp(),
            extraction_strategy=ScrapeStrategy.RSS,
        )
        
        assert article.article_id == article_id
        assert len(article.article_id) == 64
    
    def test_clean_text_for_article_body(self):
        """Test cleaning article body text."""
        from shared_types import ScrapedArticle, ScrapeStrategy
        
        raw_html = "<p>Hello <b>world</b>!</p>"
        cleaned = clean_text(raw_html, remove_html=True)
        
        article = ScrapedArticle(
            article_id="",
            url="https://example.com/test",
            source_name="Test",
            scraped_at=get_current_timestamp(),
            extraction_strategy=ScrapeStrategy.RSS,
            body_text=cleaned,
        )
        
        assert article.body_text == "Hello world!"


class TestPackageExports:
    """Test package exports."""
    
    def test_all_exports_accessible(self):
        """Test all __all__ exports are accessible."""
        import shared_utils
        
        assert hasattr(shared_utils, '__all__')
        
        for name in shared_utils.__all__:
            assert hasattr(shared_utils, name), f"{name} not accessible"
    
    def test_version(self):
        """Test package version."""
        import shared_utils
        assert hasattr(shared_utils, '__version__')
        assert shared_utils.__version__ == "0.1.0"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
