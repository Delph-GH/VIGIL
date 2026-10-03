"""
shared_ingestion/domain_throttler.py

Rate limiting per domain to avoid overwhelming sources.

Extracted from Diaspora's scraping/engine.py
"""

import time
from typing import Dict
from threading import Lock
from shared_utils import extract_domain


class DomainThrottler:
    """
    Rate limiter per domain.
    
    Tracks last request time per domain and enforces minimum delay.
    
    Thread-safe for concurrent scraping.
    
    Usage:
        throttler = DomainThrottler(default_delay=5)
        throttler.wait("https://example.com/article")  # Waits if needed
    """
    
    def __init__(self, default_delay: int = 5):
        """
        Initialize throttler.
        
        Args:
            default_delay: Default delay between requests (seconds)
        """
        self.default_delay = default_delay
        self._last_request: Dict[str, float] = {}
        self._lock = Lock()
    
    def wait(self, url: str, custom_delay: int | None = None) -> float:
        """
        Wait if necessary before making request to domain.
        
        Args:
            url: URL to request
            custom_delay: Custom delay for this domain (overrides default)
            
        Returns:
            Time waited in seconds
        """
        domain = extract_domain(url)
        if not domain:
            return 0.0
        
        delay = custom_delay if custom_delay is not None else self.default_delay
        
        with self._lock:
            now = time.time()
            last_request = self._last_request.get(domain, 0)
            elapsed = now - last_request
            
            if elapsed < delay:
                wait_time = delay - elapsed
                time.sleep(wait_time)
                self._last_request[domain] = time.time()
                return wait_time
            else:
                self._last_request[domain] = now
                return 0.0
    
    def reset(self, url: str | None = None) -> None:
        """
        Reset throttling for domain or all domains.
        
        Args:
            url: URL to reset (resets specific domain), or None to reset all
        """
        with self._lock:
            if url is None:
                self._last_request.clear()
            else:
                domain = extract_domain(url)
                if domain and domain in self._last_request:
                    del self._last_request[domain]
    
    def get_last_request_time(self, url: str) -> float | None:
        """
        Get timestamp of last request to domain.
        
        Args:
            url: URL to check
            
        Returns:
            Unix timestamp or None if never requested
        """
        domain = extract_domain(url)
        if not domain:
            return None
        
        with self._lock:
            return self._last_request.get(domain)
    
    def set_delay(self, default_delay: int) -> None:
        """
        Update default delay.
        
        Args:
            default_delay: New default delay (seconds)
        """
        self.default_delay = default_delay


# Export
__all__ = ['DomainThrottler']
