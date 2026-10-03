"""
Tests for shared_ingestion package.

Tests multi-strategy engine, rate limiting, robots.txt, and diagnostics.
"""

import pytest
import time
from pathlib import Path
import tempfile

from shared_ingestion import (
    MultiStrategyEngine,
    EngineConfig,
    DomainThrottler,
    RobotsChecker,
    diagnose_http_failure,
    diagnose_network_failure,
    diagnose_content_failure,
)

from shared_types import (
    ScrapeStrategy,
    FailureCode,
)


class TestEngineConfig:
    """Test EngineConfig dataclass."""
    
    def test_default_config(self):
        """Test default configuration."""
        config = EngineConfig()
        
        assert ScrapeStrategy.RSS in config.strategies
        assert ScrapeStrategy.STATIC_HTTP in config.strategies
        assert config.enable_robots_txt is True
        assert config.enable_rate_limiting is True
        assert config.rate_limit_delay == 5
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = EngineConfig(
            strategies=[ScrapeStrategy.STATIC_HTTP],
            enable_robots_txt=False,
            rate_limit_delay=10,
            archive_html=True,
        )
        
        assert config.strategies == [ScrapeStrategy.STATIC_HTTP]
        assert config.enable_robots_txt is False
        assert config.rate_limit_delay == 10
        assert config.archive_html is True
    
    def test_archive_path_creation(self):
        """Test archive path auto-creation."""
        config = EngineConfig(archive_html=True)
        
        # Should auto-set archive_path
        assert config.archive_path is not None
        assert isinstance(config.archive_path, Path)


class TestDomainThrottler:
    """Test DomainThrottler rate limiting."""
    
    def test_first_request_no_wait(self):
        """First request to domain shouldn't wait."""
        throttler = DomainThrottler(default_delay=5)
        wait_time = throttler.wait("https://example.com/article1")
        
        assert wait_time == 0.0
    
    def test_subsequent_request_waits(self):
        """Subsequent request within delay should wait."""
        throttler = DomainThrottler(default_delay=1)  # 1 second delay
        
        # First request
        throttler.wait("https://example.com/article1")
        
        # Immediate second request should wait
        start = time.time()
        wait_time = throttler.wait("https://example.com/article2")
        elapsed = time.time() - start
        
        assert wait_time > 0
        assert elapsed >= 0.9  # Should wait ~1 second (with small margin)
    
    def test_different_domains_no_wait(self):
        """Requests to different domains shouldn't interfere."""
        throttler = DomainThrottler(default_delay=5)
        
        throttler.wait("https://example.com/article")
        wait_time = throttler.wait("https://different.com/article")
        
        # Different domain, no wait
        assert wait_time == 0.0
    
    def test_custom_delay(self):
        """Test custom delay per request."""
        throttler = DomainThrottler(default_delay=5)
        
        throttler.wait("https://example.com/article1")
        
        # Use custom delay of 0.5 seconds
        start = time.time()
        wait_time = throttler.wait("https://example.com/article2", custom_delay=1)
        elapsed = time.time() - start
        
        assert elapsed >= 0.9  # Should wait ~1 second
    
    def test_reset(self):
        """Test resetting throttle state."""
        throttler = DomainThrottler(default_delay=5)
        
        throttler.wait("https://example.com/article1")
        throttler.reset("https://example.com")
        
        # After reset, no wait
        wait_time = throttler.wait("https://example.com/article2")
        assert wait_time == 0.0


class TestRobotsChecker:
    """Test RobotsChecker compliance."""
    
    def test_can_fetch_no_robots_txt(self):
        """Test with domain that has no robots.txt."""
        checker = RobotsChecker(user_agent="TestBot/1.0")
        
        # Should allow by default if no robots.txt
        # (This will fail to load robots.txt, which is expected)
        result = checker.can_fetch("https://nonexistent-domain-12345.com/article")
        
        # Allow by default on error
        assert result is True
    
    def test_clear_cache(self):
        """Test clearing parser cache."""
        checker = RobotsChecker()
        
        # Trigger cache creation
        checker.can_fetch("https://example.com/article")
        
        # Clear cache
        checker.clear_cache()
        
        # Should work fine after clear
        result = checker.can_fetch("https://example.com/article")
        assert isinstance(result, bool)


class TestFailureDiagnostics:
    """Test failure diagnostics functions."""
    
    def test_diagnose_http_403(self):
        """Test HTTP 403 diagnosis."""
        report = diagnose_http_failure(
            source_name="Test",
            url="https://example.com/forbidden",
            status_code=403,
            strategy=ScrapeStrategy.STATIC_HTTP,
        )
        
        assert report.failure_code == FailureCode.HTTP_FORBIDDEN
        assert report.http_status == 403
        assert "403" in report.failure_detail
    
    def test_diagnose_http_404(self):
        """Test HTTP 404 diagnosis."""
        report = diagnose_http_failure(
            source_name="Test",
            url="https://example.com/notfound",
            status_code=404,
            strategy=ScrapeStrategy.STATIC_HTTP,
        )
        
        assert report.failure_code == FailureCode.HTTP_NOT_FOUND
        assert report.http_status == 404
    
    def test_diagnose_http_500(self):
        """Test HTTP 500 diagnosis."""
        report = diagnose_http_failure(
            source_name="Test",
            url="https://example.com/error",
            status_code=500,
            strategy=ScrapeStrategy.STATIC_HTTP,
        )
        
        assert report.failure_code == FailureCode.HTTP_5XX
        assert report.http_status == 500
    
    def test_diagnose_timeout(self):
        """Test timeout diagnosis."""
        error = TimeoutError("Request timed out")
        report = diagnose_network_failure(
            source_name="Test",
            url="https://example.com/slow",
            error=error,
            strategy=ScrapeStrategy.STATIC_HTTP,
        )
        
        assert report.failure_code == FailureCode.TIMEOUT
        assert "timeout" in report.failure_detail.lower()
    
    def test_diagnose_connection_error(self):
        """Test connection error diagnosis."""
        error = ConnectionError("Connection refused")
        report = diagnose_network_failure(
            source_name="Test",
            url="https://example.com/refused",
            error=error,
            strategy=ScrapeStrategy.STATIC_HTTP,
        )
        
        assert report.failure_code == FailureCode.CONNECTION_ERROR
    
    def test_diagnose_cloudflare(self):
        """Test Cloudflare challenge detection."""
        html = """
        <html>
            <body>
                <h1>Cloudflare</h1>
                <p>Checking your browser before accessing example.com</p>
            </body>
        </html>
        """
        
        report = diagnose_content_failure(
            source_name="Test",
            url="https://example.com/article",
            html_content=html,
            http_status=200,
            strategy=ScrapeStrategy.STATIC_HTTP,
        )
        
        assert report is not None
        assert report.failure_code == FailureCode.CLOUDFLARE_CHALLENGE
        assert report.body_class == "cloudflare"
    
    def test_diagnose_antibot(self):
        """Test antibot detection."""
        html = """
        <html>
            <body>
                <h1>Are you a robot?</h1>
                <div class="captcha">Please solve the CAPTCHA</div>
            </body>
        </html>
        """
        
        report = diagnose_content_failure(
            source_name="Test",
            url="https://example.com/article",
            html_content=html,
            http_status=200,
            strategy=ScrapeStrategy.STATIC_HTTP,
        )
        
        assert report is not None
        assert report.failure_code == FailureCode.ANTIBOT_DETECTED
    
    def test_diagnose_paywall(self):
        """Test paywall detection."""
        html = """
        <html>
            <body>
                <div class="paywall">
                    <p>Subscribe to read this premium content</p>
                </div>
            </body>
        </html>
        """
        
        report = diagnose_content_failure(
            source_name="Test",
            url="https://example.com/article",
            html_content=html,
            http_status=200,
            strategy=ScrapeStrategy.STATIC_HTTP,
        )
        
        assert report is not None
        assert report.failure_code == FailureCode.PAYWALL_DETECTED
    
    def test_diagnose_empty_response(self):
        """Test empty response detection."""
        report = diagnose_content_failure(
            source_name="Test",
            url="https://example.com/article",
            html_content="",
            http_status=200,
            strategy=ScrapeStrategy.STATIC_HTTP,
        )
        
        assert report is not None
        assert report.failure_code == FailureCode.EMPTY_RESPONSE
    
    def test_diagnose_no_issue(self):
        """Test with valid HTML."""
        html = """
        <html>
            <head><title>Valid Article</title></head>
            <body>
                <h1>Article Title</h1>
                <p>Article content goes here...</p>
            </body>
        </html>
        """
        
        report = diagnose_content_failure(
            source_name="Test",
            url="https://example.com/article",
            html_content=html,
            http_status=200,
            strategy=ScrapeStrategy.STATIC_HTTP,
        )
        
        # No issue detected
        assert report is None


class TestMultiStrategyEngine:
    """Test MultiStrategyEngine."""
    
    def test_engine_initialization(self):
        """Test engine initialization with config."""
        config = EngineConfig(
            strategies=[ScrapeStrategy.STATIC_HTTP],
            enable_robots_txt=True,
            rate_limit_delay=5,
        )
        
        engine = MultiStrategyEngine(config)
        
        assert engine.config == config
        assert engine.throttler is not None
        assert engine.robots_checker is not None
    
    def test_engine_without_rate_limiting(self):
        """Test engine with rate limiting disabled."""
        config = EngineConfig(enable_rate_limiting=False)
        engine = MultiStrategyEngine(config)
        
        assert engine.throttler is None
    
    def test_engine_without_robots_check(self):
        """Test engine with robots.txt check disabled."""
        config = EngineConfig(enable_robots_txt=False)
        engine = MultiStrategyEngine(config)
        
        assert engine.robots_checker is None
    
    def test_scrape_url_placeholder(self):
        """Test scrape_url (placeholder - no actual scraping)."""
        config = EngineConfig(
            strategies=[ScrapeStrategy.STATIC_HTTP],
            enable_rate_limiting=False,
            enable_robots_txt=False,
        )
        
        engine = MultiStrategyEngine(config)
        
        # This will fail since we haven't implemented actual scraping
        # but we can verify it returns a ScrapeResult
        result = engine.scrape_url(
            url="https://example.com/article",
            source_name="Test Source",
        )
        
        # Should return ScrapeResult
        assert hasattr(result, 'success')
        assert hasattr(result, 'source_name')
        
        # Will fail since scraping not implemented
        assert result.success is False


class TestPackageExports:
    """Test package exports."""
    
    def test_all_exports_accessible(self):
        """Test all __all__ exports are accessible."""
        import shared_ingestion
        
        assert hasattr(shared_ingestion, '__all__')
        
        for name in shared_ingestion.__all__:
            assert hasattr(shared_ingestion, name), f"{name} not accessible"
    
    def test_version(self):
        """Test package version."""
        import shared_ingestion
        assert hasattr(shared_ingestion, '__version__')
        assert shared_ingestion.__version__ == "0.1.0"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
