"""
shared_ingestion/source_health.py

Source health monitoring and reliability scoring.

Extracted from Diaspora's scraping/monitor.py (375 LOC)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime, timezone, timedelta
from enum import Enum

from shared_types import SourceStatus, FailureCode
from shared_utils import get_current_timestamp


class HealthStatus(str, Enum):
    """
    Source health status levels.
    
    Based on composite health score (0-100).
    """
    EXCELLENT = "excellent"    # 90-100
    GOOD = "good"             # 70-89
    FAIR = "fair"             # 50-69
    POOR = "poor"             # 30-49
    CRITICAL = "critical"     # 0-29


@dataclass
class HealthMetrics:
    """
    Health metrics for a source.
    
    Tracks:
    - Success rate
    - Response times
    - Failure patterns
    - Last successful scrape
    """
    
    # Identity
    source_name: str
    
    # Success metrics
    total_attempts: int = 0
    successful_scrapes: int = 0
    failed_scrapes: int = 0
    
    # Response times (milliseconds)
    avg_response_ms: float = 0.0
    min_response_ms: Optional[int] = None
    max_response_ms: Optional[int] = None
    
    # Timestamps
    last_attempt: Optional[str] = None
    last_success: Optional[str] = None
    last_failure: Optional[str] = None
    
    # Failure tracking
    consecutive_failures: int = 0
    most_common_failure: Optional[FailureCode] = None
    
    # Status
    current_status: SourceStatus = SourceStatus.ACTIVE
    health_status: HealthStatus = HealthStatus.GOOD
    health_score: float = 100.0  # 0-100
    
    # History (list of recent response times)
    _response_history: List[int] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate (0.0 to 1.0)."""
        if self.total_attempts == 0:
            return 0.0
        return self.successful_scrapes / self.total_attempts
    
    @property
    def failure_rate(self) -> float:
        """Calculate failure rate (0.0 to 1.0)."""
        return 1.0 - self.success_rate
    
    @property
    def is_healthy(self) -> bool:
        """Check if source is healthy (score >= 70)."""
        return self.health_score >= 70.0
    
    @property
    def needs_attention(self) -> bool:
        """Check if source needs attention (score < 50 or 3+ consecutive failures)."""
        return self.health_score < 50.0 or self.consecutive_failures >= 3


class SourceHealthMonitor:
    """
    Monitor and score source health.
    
    Tracks:
    - Success/failure rates
    - Response times
    - Consecutive failures
    - Health scores (composite formula)
    
    Health Score Formula (0-100):
    - Success rate: 60% weight
    - Response time: 20% weight
    - Recency: 10% weight
    - Stability: 10% weight
    
    Usage:
        monitor = SourceHealthMonitor()
        
        # Record success
        monitor.record_success("example.com", response_ms=1500)
        
        # Record failure
        monitor.record_failure("example.com", FailureCode.HTTP_403)
        
        # Get health
        metrics = monitor.get_health("example.com")
        print(f"Health: {metrics.health_score:.1f}/100")
    """
    
    def __init__(self, response_history_limit: int = 20):
        """
        Initialize health monitor.
        
        Args:
            response_history_limit: Max response times to track per source
        """
        self.response_history_limit = response_history_limit
        self._metrics: Dict[str, HealthMetrics] = {}
    
    def record_success(
        self,
        source_name: str,
        response_ms: int,
        timestamp: Optional[str] = None,
    ) -> None:
        """
        Record successful scrape.
        
        Args:
            source_name: Source identifier
            response_ms: Response time in milliseconds
            timestamp: ISO 8601 timestamp (uses current if None)
        """
        if timestamp is None:
            timestamp = get_current_timestamp()
        
        metrics = self._get_or_create_metrics(source_name)
        
        # Update counters
        metrics.total_attempts += 1
        metrics.successful_scrapes += 1
        metrics.consecutive_failures = 0  # Reset
        
        # Update timestamps
        metrics.last_attempt = timestamp
        metrics.last_success = timestamp
        
        # Update response times
        metrics._response_history.append(response_ms)
        if len(metrics._response_history) > self.response_history_limit:
            metrics._response_history.pop(0)
        
        metrics.avg_response_ms = sum(metrics._response_history) / len(metrics._response_history)
        metrics.min_response_ms = min(metrics._response_history)
        metrics.max_response_ms = max(metrics._response_history)
        
        # Update status
        if metrics.current_status in [SourceStatus.ERROR, SourceStatus.RATE_LIMITED]:
            metrics.current_status = SourceStatus.ACTIVE
        
        # Recalculate health score
        self._update_health_score(metrics)
    
    def record_failure(
        self,
        source_name: str,
        failure_code: FailureCode,
        timestamp: Optional[str] = None,
    ) -> None:
        """
        Record failed scrape.
        
        Args:
            source_name: Source identifier
            failure_code: Type of failure
            timestamp: ISO 8601 timestamp (uses current if None)
        """
        if timestamp is None:
            timestamp = get_current_timestamp()
        
        metrics = self._get_or_create_metrics(source_name)
        
        # Update counters
        metrics.total_attempts += 1
        metrics.failed_scrapes += 1
        metrics.consecutive_failures += 1
        
        # Update timestamps
        metrics.last_attempt = timestamp
        metrics.last_failure = timestamp
        
        # Track most common failure
        metrics.most_common_failure = failure_code
        
        # Update status based on failure type
        if failure_code == FailureCode.RATE_LIMITED:
            metrics.current_status = SourceStatus.RATE_LIMITED
        elif failure_code == FailureCode.PAYWALL_DETECTED:
            metrics.current_status = SourceStatus.PAYWALL
        elif metrics.consecutive_failures >= 5:
            metrics.current_status = SourceStatus.ERROR
        
        # Recalculate health score
        self._update_health_score(metrics)
    
    def get_health(self, source_name: str) -> HealthMetrics:
        """
        Get health metrics for source.
        
        Args:
            source_name: Source identifier
            
        Returns:
            HealthMetrics for source
        """
        return self._get_or_create_metrics(source_name)
    
    def get_all_sources(self) -> List[str]:
        """
        Get all monitored sources.
        
        Returns:
            List of source names
        """
        return list(self._metrics.keys())
    
    def get_unhealthy_sources(self, threshold: float = 50.0) -> List[str]:
        """
        Get sources with low health scores.
        
        Args:
            threshold: Health score threshold (default: 50.0)
            
        Returns:
            List of source names with health < threshold
        """
        return [
            name
            for name, metrics in self._metrics.items()
            if metrics.health_score < threshold
        ]
    
    def get_sources_by_status(self, status: SourceStatus) -> List[str]:
        """
        Get sources with specific status.
        
        Args:
            status: Status to filter by
            
        Returns:
            List of source names
        """
        return [
            name
            for name, metrics in self._metrics.items()
            if metrics.current_status == status
        ]
    
    def reset_source(self, source_name: str) -> None:
        """
        Reset health metrics for source.
        
        Args:
            source_name: Source to reset
        """
        if source_name in self._metrics:
            del self._metrics[source_name]
    
    def _get_or_create_metrics(self, source_name: str) -> HealthMetrics:
        """Get existing metrics or create new ones."""
        if source_name not in self._metrics:
            self._metrics[source_name] = HealthMetrics(source_name=source_name)
        return self._metrics[source_name]
    
    def _update_health_score(self, metrics: HealthMetrics) -> None:
        """
        Calculate composite health score (0-100).
        
        Formula:
        - Success rate: 60% weight
        - Response time: 20% weight (faster = better)
        - Recency: 10% weight (recent success = better)
        - Stability: 10% weight (low variance = better)
        
        Args:
            metrics: Metrics to update
        """
        score = 0.0
        
        # 1. Success rate (60 points max)
        success_score = metrics.success_rate * 60.0
        score += success_score
        
        # 2. Response time (20 points max)
        if metrics.avg_response_ms > 0:
            # Faster is better
            # 0-1000ms = 20 points, 1000-5000ms = 10 points, >5000ms = 0 points
            if metrics.avg_response_ms <= 1000:
                response_score = 20.0
            elif metrics.avg_response_ms <= 5000:
                response_score = 20.0 * (1.0 - (metrics.avg_response_ms - 1000) / 4000)
            else:
                response_score = 0.0
            score += response_score
        else:
            # No data yet, assume good
            score += 20.0
        
        # 3. Recency (10 points max)
        if metrics.last_success:
            # Recent success is good
            try:
                last_success_dt = datetime.fromisoformat(metrics.last_success.replace('Z', '+00:00'))
                hours_since = (datetime.now(timezone.utc) - last_success_dt).total_seconds() / 3600
                
                if hours_since <= 1:
                    recency_score = 10.0
                elif hours_since <= 24:
                    recency_score = 10.0 * (1.0 - hours_since / 24)
                else:
                    recency_score = 0.0
                
                score += recency_score
            except (ValueError, AttributeError):
                pass
        
        # 4. Stability (10 points max)
        if metrics.consecutive_failures == 0:
            stability_score = 10.0
        elif metrics.consecutive_failures <= 2:
            stability_score = 5.0
        else:
            stability_score = 0.0
        
        score += stability_score
        
        # Clamp to 0-100
        metrics.health_score = max(0.0, min(100.0, score))
        
        # Update health status
        if metrics.health_score >= 90:
            metrics.health_status = HealthStatus.EXCELLENT
        elif metrics.health_score >= 70:
            metrics.health_status = HealthStatus.GOOD
        elif metrics.health_score >= 50:
            metrics.health_status = HealthStatus.FAIR
        elif metrics.health_score >= 30:
            metrics.health_status = HealthStatus.POOR
        else:
            metrics.health_status = HealthStatus.CRITICAL


# Export all
__all__ = [
    'HealthStatus',
    'HealthMetrics',
    'SourceHealthMonitor',
]
