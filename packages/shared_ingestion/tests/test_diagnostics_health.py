"""
Tests for diagnostics and health monitoring.

Tests DiagnosticsStats and SourceHealthMonitor.
"""

import pytest
import time
from shared_ingestion import (
    DiagnosticsStats,
    SourceHealthMonitor,
    HealthStatus,
    HealthMetrics,
)
from shared_types import FailureCode, SourceStatus


class TestDiagnosticsStats:
    """Test DiagnosticsStats failure tracking."""
    
    def test_initialization(self):
        """Test stats initialization."""
        stats = DiagnosticsStats(window_minutes=60)
        
        assert stats.window_minutes == 60
        assert stats.get_total_failures() == {}
    
    def test_record_single_failure(self):
        """Test recording a single failure."""
        stats = DiagnosticsStats()
        stats.record_failure("example.com", FailureCode.HTTP_403)
        
        failures = stats.get_source_failures("example.com")
        assert failures[FailureCode.HTTP_403] == 1
    
    def test_record_multiple_failures(self):
        """Test recording multiple failures."""
        stats = DiagnosticsStats()
        
        stats.record_failure("example.com", FailureCode.HTTP_403)
        stats.record_failure("example.com", FailureCode.HTTP_403)
        stats.record_failure("example.com", FailureCode.TIMEOUT)
        
        failures = stats.get_source_failures("example.com")
        assert failures[FailureCode.HTTP_403] == 2
        assert failures[FailureCode.TIMEOUT] == 1
    
    def test_multiple_sources(self):
        """Test tracking multiple sources."""
        stats = DiagnosticsStats()
        
        stats.record_failure("source1", FailureCode.HTTP_403)
        stats.record_failure("source2", FailureCode.TIMEOUT)
        
        assert stats.get_source_failures("source1") == {FailureCode.HTTP_403: 1}
        assert stats.get_source_failures("source2") == {FailureCode.TIMEOUT: 1}
    
    def test_total_failures(self):
        """Test total failure counts."""
        stats = DiagnosticsStats()
        
        stats.record_failure("source1", FailureCode.HTTP_403)
        stats.record_failure("source2", FailureCode.HTTP_403)
        stats.record_failure("source2", FailureCode.TIMEOUT)
        
        total = stats.get_total_failures()
        assert total[FailureCode.HTTP_403] == 2
        assert total[FailureCode.TIMEOUT] == 1
    
    def test_most_common_failures(self):
        """Test getting most common failures."""
        stats = DiagnosticsStats()
        
        stats.record_failure("example.com", FailureCode.HTTP_403)
        stats.record_failure("example.com", FailureCode.HTTP_403)
        stats.record_failure("example.com", FailureCode.HTTP_403)
        stats.record_failure("example.com", FailureCode.TIMEOUT)
        
        common = stats.get_most_common_failures("example.com", limit=2)
        
        assert len(common) == 2
        assert common[0] == (FailureCode.HTTP_403, 3)
        assert common[1] == (FailureCode.TIMEOUT, 1)
    
    def test_is_source_unhealthy(self):
        """Test unhealthy source detection."""
        stats = DiagnosticsStats()
        
        # Below threshold
        for _ in range(5):
            stats.record_failure("example.com", FailureCode.HTTP_403)
        
        assert stats.is_source_unhealthy("example.com", threshold=10) is False
        
        # Above threshold
        for _ in range(10):
            stats.record_failure("example.com", FailureCode.TIMEOUT)
        
        assert stats.is_source_unhealthy("example.com", threshold=10) is True
    
    def test_detect_persistent_403(self):
        """Test detecting persistent 403 pattern."""
        stats = DiagnosticsStats()
        
        # Record mostly 403 errors (>70%)
        for _ in range(8):
            stats.record_failure("example.com", FailureCode.HTTP_403)
        stats.record_failure("example.com", FailureCode.TIMEOUT)
        
        pattern = stats.detect_failure_pattern("example.com")
        assert pattern == "persistent_403"
    
    def test_detect_cloudflare_pattern(self):
        """Test detecting Cloudflare pattern."""
        stats = DiagnosticsStats()
        
        for _ in range(8):
            stats.record_failure("example.com", FailureCode.CLOUDFLARE_CHALLENGE)
        
        pattern = stats.detect_failure_pattern("example.com")
        assert pattern == "persistent_cloudflare"
    
    def test_detect_unstable_pattern(self):
        """Test detecting unstable pattern."""
        stats = DiagnosticsStats()
        
        # Mix of different errors
        stats.record_failure("example.com", FailureCode.HTTP_403)
        stats.record_failure("example.com", FailureCode.TIMEOUT)
        stats.record_failure("example.com", FailureCode.DNS_FAILURE)
        stats.record_failure("example.com", FailureCode.HTTP_5XX)
        stats.record_failure("example.com", FailureCode.CONNECTION_ERROR)
        
        pattern = stats.detect_failure_pattern("example.com")
        assert pattern == "unstable"
    
    def test_failure_rate_calculation(self):
        """Test failure rate calculation."""
        stats = DiagnosticsStats()
        
        stats.record_failure("example.com", FailureCode.HTTP_403)
        stats.record_failure("example.com", FailureCode.TIMEOUT)
        
        rate = stats.get_failure_rate("example.com", total_attempts=10)
        assert rate == 0.2  # 2 failures / 10 attempts
    
    def test_reset_source(self):
        """Test resetting source statistics."""
        stats = DiagnosticsStats()
        
        stats.record_failure("example.com", FailureCode.HTTP_403)
        stats.reset_source("example.com")
        
        assert stats.get_source_failures("example.com") == {}
    
    def test_clear_all(self):
        """Test clearing all statistics."""
        stats = DiagnosticsStats()
        
        stats.record_failure("source1", FailureCode.HTTP_403)
        stats.record_failure("source2", FailureCode.TIMEOUT)
        
        stats.clear_all()
        
        assert stats.get_total_failures() == {}
        assert stats.get_source_failures("source1") == {}


class TestHealthMetrics:
    """Test HealthMetrics dataclass."""
    
    def test_initialization(self):
        """Test metrics initialization."""
        metrics = HealthMetrics(source_name="example.com")
        
        assert metrics.source_name == "example.com"
        assert metrics.total_attempts == 0
        assert metrics.successful_scrapes == 0
        assert metrics.health_score == 100.0
    
    def test_success_rate(self):
        """Test success rate calculation."""
        metrics = HealthMetrics(source_name="example.com")
        
        metrics.total_attempts = 10
        metrics.successful_scrapes = 7
        
        assert metrics.success_rate == 0.7
    
    def test_failure_rate(self):
        """Test failure rate calculation."""
        metrics = HealthMetrics(source_name="example.com")
        
        metrics.total_attempts = 10
        metrics.successful_scrapes = 7
        
        assert metrics.failure_rate == 0.3
    
    def test_is_healthy(self):
        """Test health check."""
        metrics = HealthMetrics(source_name="example.com")
        
        metrics.health_score = 80.0
        assert metrics.is_healthy is True
        
        metrics.health_score = 60.0
        assert metrics.is_healthy is False
    
    def test_needs_attention(self):
        """Test attention needed check."""
        metrics = HealthMetrics(source_name="example.com")
        
        # Low score
        metrics.health_score = 40.0
        assert metrics.needs_attention is True
        
        # High consecutive failures
        metrics.health_score = 70.0
        metrics.consecutive_failures = 5
        assert metrics.needs_attention is True
        
        # Healthy
        metrics.health_score = 80.0
        metrics.consecutive_failures = 0
        assert metrics.needs_attention is False


class TestSourceHealthMonitor:
    """Test SourceHealthMonitor."""
    
    def test_initialization(self):
        """Test monitor initialization."""
        monitor = SourceHealthMonitor()
        
        assert monitor.get_all_sources() == []
    
    def test_record_success(self):
        """Test recording successful scrape."""
        monitor = SourceHealthMonitor()
        
        monitor.record_success("example.com", response_ms=1500)
        
        metrics = monitor.get_health("example.com")
        assert metrics.total_attempts == 1
        assert metrics.successful_scrapes == 1
        assert metrics.consecutive_failures == 0
        assert metrics.avg_response_ms == 1500.0
    
    def test_record_failure(self):
        """Test recording failed scrape."""
        monitor = SourceHealthMonitor()
        
        monitor.record_failure("example.com", FailureCode.HTTP_403)
        
        metrics = monitor.get_health("example.com")
        assert metrics.total_attempts == 1
        assert metrics.failed_scrapes == 1
        assert metrics.consecutive_failures == 1
        assert metrics.most_common_failure == FailureCode.HTTP_403
    
    def test_consecutive_failures(self):
        """Test consecutive failure tracking."""
        monitor = SourceHealthMonitor()
        
        # Record failures
        monitor.record_failure("example.com", FailureCode.TIMEOUT)
        monitor.record_failure("example.com", FailureCode.TIMEOUT)
        monitor.record_failure("example.com", FailureCode.TIMEOUT)
        
        metrics = monitor.get_health("example.com")
        assert metrics.consecutive_failures == 3
        
        # Success resets counter
        monitor.record_success("example.com", response_ms=1000)
        
        metrics = monitor.get_health("example.com")
        assert metrics.consecutive_failures == 0
    
    def test_health_score_calculation(self):
        """Test health score calculation."""
        monitor = SourceHealthMonitor()
        
        # Perfect score: all successes, fast responses
        for _ in range(10):
            monitor.record_success("example.com", response_ms=500)
        
        metrics = monitor.get_health("example.com")
        assert metrics.health_score > 90.0  # Should be EXCELLENT
        assert metrics.health_status == HealthStatus.EXCELLENT
    
    def test_health_score_degradation(self):
        """Test health score degrades with failures."""
        monitor = SourceHealthMonitor()
        
        # Mix of success and failure
        for _ in range(5):
            monitor.record_success("example.com", response_ms=1000)
        for _ in range(5):
            monitor.record_failure("example.com", FailureCode.TIMEOUT)
        
        metrics = monitor.get_health("example.com")
        assert metrics.health_score < 70.0  # Should be FAIR or lower
    
    def test_status_updates(self):
        """Test status updates based on failures."""
        monitor = SourceHealthMonitor()
        
        # Rate limited
        monitor.record_failure("example.com", FailureCode.RATE_LIMITED)
        metrics = monitor.get_health("example.com")
        assert metrics.current_status == SourceStatus.RATE_LIMITED
        
        # Paywall
        monitor.record_failure("paywall.com", FailureCode.PAYWALL_DETECTED)
        metrics = monitor.get_health("paywall.com")
        assert metrics.current_status == SourceStatus.PAYWALL
        
        # Many failures → ERROR
        for _ in range(6):
            monitor.record_failure("error.com", FailureCode.TIMEOUT)
        metrics = monitor.get_health("error.com")
        assert metrics.current_status == SourceStatus.ERROR
    
    def test_get_unhealthy_sources(self):
        """Test getting unhealthy sources."""
        monitor = SourceHealthMonitor()
        
        # Healthy source
        for _ in range(10):
            monitor.record_success("healthy.com", response_ms=500)
        
        # Unhealthy source
        for _ in range(10):
            monitor.record_failure("unhealthy.com", FailureCode.TIMEOUT)
        
        unhealthy = monitor.get_unhealthy_sources(threshold=50.0)
        assert "unhealthy.com" in unhealthy
        assert "healthy.com" not in unhealthy
    
    def test_get_sources_by_status(self):
        """Test filtering sources by status."""
        monitor = SourceHealthMonitor()
        
        monitor.record_failure("rate_limited.com", FailureCode.RATE_LIMITED)
        monitor.record_failure("paywall.com", FailureCode.PAYWALL_DETECTED)
        
        rate_limited = monitor.get_sources_by_status(SourceStatus.RATE_LIMITED)
        assert "rate_limited.com" in rate_limited
        
        paywall = monitor.get_sources_by_status(SourceStatus.PAYWALL)
        assert "paywall.com" in paywall
    
    def test_response_time_tracking(self):
        """Test response time statistics."""
        monitor = SourceHealthMonitor(response_history_limit=5)
        
        # Record varying response times
        monitor.record_success("example.com", response_ms=1000)
        monitor.record_success("example.com", response_ms=1500)
        monitor.record_success("example.com", response_ms=2000)
        monitor.record_success("example.com", response_ms=500)
        
        metrics = monitor.get_health("example.com")
        assert metrics.avg_response_ms == 1250.0  # (1000+1500+2000+500)/4
        assert metrics.min_response_ms == 500
        assert metrics.max_response_ms == 2000
    
    def test_reset_source(self):
        """Test resetting source metrics."""
        monitor = SourceHealthMonitor()
        
        monitor.record_success("example.com", response_ms=1000)
        monitor.reset_source("example.com")
        
        metrics = monitor.get_health("example.com")
        assert metrics.total_attempts == 0


class TestIntegration:
    """Test integration of diagnostics and health monitoring."""
    
    def test_combined_usage(self):
        """Test using both DiagnosticsStats and SourceHealthMonitor together."""
        stats = DiagnosticsStats()
        monitor = SourceHealthMonitor()
        
        # Simulate scraping with failures
        source = "example.com"
        
        # Some successes
        for _ in range(7):
            monitor.record_success(source, response_ms=1000)
        
        # Some failures
        for _ in range(3):
            monitor.record_failure(source, FailureCode.TIMEOUT)
            stats.record_failure(source, FailureCode.TIMEOUT)
        
        # Check health
        health = monitor.get_health(source)
        assert health.total_attempts == 10
        assert health.success_rate == 0.7
        
        # Check diagnostics
        failures = stats.get_source_failures(source)
        assert failures[FailureCode.TIMEOUT] == 3
        
        # Not unhealthy yet
        assert not stats.is_source_unhealthy(source, threshold=10)


class TestPackageExports:
    """Test new package exports."""
    
    def test_diagnostics_exports(self):
        """Test DiagnosticsStats is exported."""
        from shared_ingestion import DiagnosticsStats
        assert DiagnosticsStats is not None
    
    def test_health_exports(self):
        """Test health monitoring exports."""
        from shared_ingestion import (
            HealthStatus,
            HealthMetrics,
            SourceHealthMonitor,
        )
        
        assert HealthStatus is not None
        assert HealthMetrics is not None
        assert SourceHealthMonitor is not None
    
    def test_all_exports_accessible(self):
        """Test all __all__ exports are accessible."""
        import shared_ingestion
        
        for name in shared_ingestion.__all__:
            assert hasattr(shared_ingestion, name), f"{name} not accessible"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
