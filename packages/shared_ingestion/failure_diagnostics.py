"""
shared_ingestion/failure_diagnostics.py

19-code failure diagnostics system.

Extracted from Diaspora's scraping/diagnostics.py
"""

from typing import Optional
from shared_types import FailureCode, FailureReport, ScrapeStrategy
from shared_utils import get_current_timestamp


def diagnose_http_failure(
    source_name: str,
    url: str,
    status_code: int,
    strategy: ScrapeStrategy,
) -> FailureReport:
    """
    Diagnose HTTP status code failure.
    
    Args:
        source_name: Source identifier
        url: Failed URL
        status_code: HTTP status code
        strategy: Strategy attempted
        
    Returns:
        FailureReport with diagnosed code
    """
    # Determine failure code
    if status_code == 403:
        code = FailureCode.HTTP_FORBIDDEN
        detail = f"HTTP 403 Forbidden - access denied"
    elif status_code == 404:
        code = FailureCode.HTTP_NOT_FOUND
        detail = f"HTTP 404 Not Found - page does not exist"
    elif 400 <= status_code < 500:
        code = FailureCode.HTTP_4XX
        detail = f"HTTP {status_code} client error"
    elif 500 <= status_code < 600:
        code = FailureCode.HTTP_5XX
        detail = f"HTTP {status_code} server error"
    else:
        code = FailureCode.UNKNOWN_ERROR
        detail = f"Unexpected HTTP status: {status_code}"
    
    return FailureReport(
        source_name=source_name,
        url=url,
        timestamp=get_current_timestamp(),
        failure_code=code,
        failure_detail=detail,
        http_status=status_code,
        strategy_attempted=strategy,
    )


def diagnose_network_failure(
    source_name: str,
    url: str,
    error: Exception,
    strategy: ScrapeStrategy,
) -> FailureReport:
    """
    Diagnose network-level failure.
    
    Args:
        source_name: Source identifier
        url: Failed URL
        error: Exception raised
        strategy: Strategy attempted
        
    Returns:
        FailureReport with diagnosed code
    """
    error_str = str(error).lower()
    
    # Diagnose from error message
    if 'timeout' in error_str or 'timed out' in error_str:
        code = FailureCode.TIMEOUT
        detail = f"Request timeout after {30}s"
    elif 'dns' in error_str or 'name or service not known' in error_str:
        code = FailureCode.DNS_FAILURE
        detail = "DNS resolution failed"
        dns_ok = False
    elif 'ssl' in error_str or 'certificate' in error_str:
        code = FailureCode.TLS_ERROR
        detail = "TLS/SSL certificate error"
        tls_ok = False
    elif 'connection' in error_str or 'connect' in error_str:
        code = FailureCode.CONNECTION_ERROR
        detail = f"Connection failed: {error}"
    else:
        code = FailureCode.UNKNOWN_ERROR
        detail = f"Network error: {error}"
    
    return FailureReport(
        source_name=source_name,
        url=url,
        timestamp=get_current_timestamp(),
        failure_code=code,
        failure_detail=detail,
        dns_ok=locals().get('dns_ok', True),
        tls_ok=locals().get('tls_ok', True),
        strategy_attempted=strategy,
        detail_json={'exception': str(error), 'exception_type': type(error).__name__},
    )


def diagnose_content_failure(
    source_name: str,
    url: str,
    html_content: str,
    http_status: int,
    strategy: ScrapeStrategy,
) -> Optional[FailureReport]:
    """
    Diagnose content-level failures (antibot, paywall, etc).
    
    Args:
        source_name: Source identifier
        url: URL
        html_content: HTML response body
        http_status: HTTP status code
        strategy: Strategy attempted
        
    Returns:
        FailureReport if content issue detected, None otherwise
    """
    if not html_content:
        return FailureReport(
            source_name=source_name,
            url=url,
            timestamp=get_current_timestamp(),
            failure_code=FailureCode.EMPTY_RESPONSE,
            failure_detail="Empty response body",
            http_status=http_status,
            strategy_attempted=strategy,
        )
    
    content_lower = html_content.lower()
    
    # Cloudflare challenge
    if 'cloudflare' in content_lower and ('challenge' in content_lower or 'checking your browser' in content_lower):
        return FailureReport(
            source_name=source_name,
            url=url,
            timestamp=get_current_timestamp(),
            failure_code=FailureCode.CLOUDFLARE_CHALLENGE,
            failure_detail="Cloudflare challenge detected",
            http_status=http_status,
            body_class="cloudflare",
            strategy_attempted=strategy,
        )
    
    # Generic antibot detection
    if any(keyword in content_lower for keyword in ['captcha', 'recaptcha', 'bot detection', 'are you a robot']):
        return FailureReport(
            source_name=source_name,
            url=url,
            timestamp=get_current_timestamp(),
            failure_code=FailureCode.ANTIBOT_DETECTED,
            failure_detail="Anti-bot detection triggered",
            http_status=http_status,
            body_class="antibot",
            strategy_attempted=strategy,
        )
    
    # Paywall detection
    if any(keyword in content_lower for keyword in ['paywall', 'subscribe to read', 'premium content', 'subscribers only']):
        return FailureReport(
            source_name=source_name,
            url=url,
            timestamp=get_current_timestamp(),
            failure_code=FailureCode.PAYWALL_DETECTED,
            failure_detail="Paywall detected",
            http_status=http_status,
            body_class="paywall",
            strategy_attempted=strategy,
        )
    
    # Malformed HTML (basic check)
    if '<html' not in content_lower and '<body' not in content_lower:
        if len(html_content) < 100:  # Very short response
            return FailureReport(
                source_name=source_name,
                url=url,
                timestamp=get_current_timestamp(),
                failure_code=FailureCode.MALFORMED_HTML,
                failure_detail="Response too short or malformed",
                http_status=http_status,
                strategy_attempted=strategy,
            )
    
    # No content issue detected
    return None


def create_robots_disallowed_report(
    source_name: str,
    url: str,
    strategy: ScrapeStrategy,
) -> FailureReport:
    """Create report for robots.txt disallowed."""
    return FailureReport(
        source_name=source_name,
        url=url,
        timestamp=get_current_timestamp(),
        failure_code=FailureCode.ROBOTS_DISALLOWED,
        failure_detail="Disallowed by robots.txt",
        strategy_attempted=strategy,
    )


def create_rate_limit_report(
    source_name: str,
    url: str,
    strategy: ScrapeStrategy,
) -> FailureReport:
    """Create report for rate limiting."""
    return FailureReport(
        source_name=source_name,
        url=url,
        timestamp=get_current_timestamp(),
        failure_code=FailureCode.RATE_LIMITED,
        failure_detail="Rate limited - too many requests",
        http_status=429,
        strategy_attempted=strategy,
    )


# Export all
__all__ = [
    'diagnose_http_failure',
    'diagnose_network_failure',
    'diagnose_content_failure',
    'create_robots_disallowed_report',
    'create_rate_limit_report',
]
