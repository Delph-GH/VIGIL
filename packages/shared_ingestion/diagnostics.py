"""
shared_ingestion/diagnostics.py

Enhanced failure diagnostics with statistics and pattern detection.

Extracted from Diaspora's scraping/diagnostics.py (337 LOC)
"""

from typing import Dict, List, Optional
from collections import defaultdict, Counter
from datetime import datetime, timezone, timedelta
from shared_types import FailureCode, FailureReport
from shared_utils import get_current_timestamp


class DiagnosticsStats:
    """
    Track failure statistics for pattern detection.
    
    Maintains counters and history for:
    - Failure codes per source
    - Failure frequency
    - Recent failure patterns
    
    Usage:
        stats = DiagnosticsStats()
        stats.record_failure("example.com", FailureCode.HTTP_403)
        
        if stats.is_source_unhealthy("example.com"):
            # Take action
    """
    
    def __init__(self, window_minutes: int = 60):
        """
        Initialize diagnostics stats tracker.
        
        Args:
            window_minutes: Time window for recent failures (default: 60)
        """
        self.window_minutes = window_minutes
        
        # Per-source failure counters
        self._failures_by_source: Dict[str, Counter] = defaultdict(Counter)
        
        # Recent failure history (source, code, timestamp)
        self._recent_failures: List[tuple] = []
        
        # Total failures per code
        self._total_failures: Counter = Counter()
    
    def record_failure(
        self,
        source_name: str,
        failure_code: FailureCode,
        timestamp: Optional[str] = None,
    ) -> None:
        """
        Record a failure for statistics.
        
        Args:
            source_name: Source identifier
            failure_code: Type of failure
            timestamp: ISO 8601 timestamp (uses current if None)
        """
        if timestamp is None:
            timestamp = get_current_timestamp()
        
        # Update counters
        self._failures_by_source[source_name][failure_code] += 1
        self._total_failures[failure_code] += 1
        
        # Add to recent history
        self._recent_failures.append((source_name, failure_code, timestamp))
        
        # Clean old entries
        self._clean_old_failures()
    
    def _clean_old_failures(self) -> None:
        """Remove failures outside the time window."""
        if not self._recent_failures:
            return
        
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=self.window_minutes)
        cutoff_iso = cutoff.isoformat().replace('+00:00', 'Z')
        
        # Keep only recent failures
        self._recent_failures = [
            (source, code, ts)
            for source, code, ts in self._recent_failures
            if ts >= cutoff_iso
        ]
    
    def get_source_failures(
        self,
        source_name: str,
        recent_only: bool = False,
    ) -> Dict[FailureCode, int]:
        """
        Get failure counts for source.
        
        Args:
            source_name: Source identifier
            recent_only: Only count failures in time window
            
        Returns:
            Dictionary of {FailureCode: count}
        """
        if not recent_only:
            return dict(self._failures_by_source[source_name])
        
        # Count recent failures only
        self._clean_old_failures()
        recent = Counter()
        for source, code, _ in self._recent_failures:
            if source == source_name:
                recent[code] += 1
        
        return dict(recent)
    
    def get_total_failures(self) -> Dict[FailureCode, int]:
        """
        Get total failure counts across all sources.
        
        Returns:
            Dictionary of {FailureCode: count}
        """
        return dict(self._total_failures)
    
    def get_most_common_failures(
        self,
        source_name: Optional[str] = None,
        limit: int = 5,
    ) -> List[tuple[FailureCode, int]]:
        """
        Get most common failure types.
        
        Args:
            source_name: Specific source, or None for all sources
            limit: Maximum number to return
            
        Returns:
            List of (FailureCode, count) tuples, sorted by count
        """
        if source_name:
            counter = self._failures_by_source[source_name]
        else:
            counter = self._total_failures
        
        return counter.most_common(limit)
    
    def is_source_unhealthy(
        self,
        source_name: str,
        threshold: int = 10,
    ) -> bool:
        """
        Check if source has excessive recent failures.
        
        Args:
            source_name: Source identifier
            threshold: Failure count threshold
            
        Returns:
            True if recent failures exceed threshold
        """
        recent = self.get_source_failures(source_name, recent_only=True)
        total_recent = sum(recent.values())
        return total_recent >= threshold
    
    def detect_failure_pattern(
        self,
        source_name: str,
    ) -> Optional[str]:
        """
        Detect failure patterns for source.
        
        Patterns detected:
        - "persistent_403" — Repeated 403 errors (likely blocked)
        - "persistent_cloudflare" — Repeated Cloudflare challenges
        - "persistent_timeout" — Network timeouts
        - "paywall" — Paywall detected
        - "unstable" — Mix of different errors
        
        Args:
            source_name: Source identifier
            
        Returns:
            Pattern name or None if no clear pattern
        """
        recent = self.get_source_failures(source_name, recent_only=True)
        
        if not recent:
            return None
        
        total = sum(recent.values())
        
        # Check for dominant failure type (>70%)
        for code, count in recent.items():
            if count / total > 0.7:
                # Persistent failure type
                if code == FailureCode.HTTP_FORBIDDEN:
                    return "persistent_403"
                elif code == FailureCode.CLOUDFLARE_CHALLENGE:
                    return "persistent_cloudflare"
                elif code == FailureCode.TIMEOUT:
                    return "persistent_timeout"
                elif code == FailureCode.PAYWALL_DETECTED:
                    return "paywall"
                elif code == FailureCode.ANTIBOT_DETECTED:
                    return "antibot"
        
        # Many different failures
        if len(recent) >= 3 and total >= 5:
            return "unstable"
        
        return None
    
    def get_failure_rate(
        self,
        source_name: str,
        total_attempts: int,
    ) -> float:
        """
        Calculate failure rate for source.
        
        Args:
            source_name: Source identifier
            total_attempts: Total scraping attempts
            
        Returns:
            Failure rate (0.0 to 1.0)
        """
        if total_attempts == 0:
            return 0.0
        
        failures = sum(self._failures_by_source[source_name].values())
        return failures / total_attempts
    
    def reset_source(self, source_name: str) -> None:
        """
        Reset statistics for source.
        
        Args:
            source_name: Source to reset
        """
        if source_name in self._failures_by_source:
            del self._failures_by_source[source_name]
        
        # Remove from recent history
        self._recent_failures = [
            (source, code, ts)
            for source, code, ts in self._recent_failures
            if source != source_name
        ]
    
    def clear_all(self) -> None:
        """Clear all statistics."""
        self._failures_by_source.clear()
        self._recent_failures.clear()
        self._total_failures.clear()


# Export
__all__ = ['DiagnosticsStats']
