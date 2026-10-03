"""
shared_ingestion/robots_checker.py

robots.txt compliance checker.

Respects website crawling policies.
"""

from urllib.robotparser import RobotFileParser
from typing import Dict
from threading import Lock
from shared_utils import extract_domain, join_url_parts


class RobotsChecker:
    """
    Check robots.txt compliance before scraping.
    
    Caches robots.txt per domain for efficiency.
    
    Usage:
        checker = RobotsChecker(user_agent="MyBot/1.0")
        if checker.can_fetch("https://example.com/article"):
            # Proceed with scraping
    """
    
    def __init__(self, user_agent: str = "*"):
        """
        Initialize robots checker.
        
        Args:
            user_agent: User agent to check against robots.txt
        """
        self.user_agent = user_agent
        self._parsers: Dict[str, RobotFileParser] = {}
        self._lock = Lock()
    
    def can_fetch(self, url: str) -> bool:
        """
        Check if URL can be fetched according to robots.txt.
        
        Args:
            url: URL to check
            
        Returns:
            True if allowed, False if disallowed
        """
        domain = extract_domain(url)
        if not domain:
            # If can't extract domain, allow by default
            return True
        
        # Get or create parser for domain
        parser = self._get_parser(url, domain)
        
        if parser is None:
            # If can't load robots.txt, allow by default
            return True
        
        try:
            return parser.can_fetch(self.user_agent, url)
        except Exception:
            # On error, allow by default
            return True
    
    def _get_parser(self, url: str, domain: str) -> RobotFileParser | None:
        """
        Get cached parser or create new one.
        
        Args:
            url: Full URL (for constructing robots.txt URL)
            domain: Domain name
            
        Returns:
            RobotFileParser or None if failed to load
        """
        with self._lock:
            if domain in self._parsers:
                return self._parsers[domain]
            
            # Create new parser
            parser = RobotFileParser()
            
            try:
                # Construct robots.txt URL
                # Extract scheme from original URL
                if url.startswith('https://'):
                    scheme = 'https://'
                else:
                    scheme = 'http://'
                
                robots_url = f"{scheme}{domain}/robots.txt"
                parser.set_url(robots_url)
                parser.read()
                
                self._parsers[domain] = parser
                return parser
            
            except Exception:
                # Failed to load robots.txt, cache None
                self._parsers[domain] = None
                return None
    
    def clear_cache(self, domain: str | None = None) -> None:
        """
        Clear cached robots.txt parsers.
        
        Args:
            domain: Specific domain to clear, or None to clear all
        """
        with self._lock:
            if domain is None:
                self._parsers.clear()
            elif domain in self._parsers:
                del self._parsers[domain]


# Export
__all__ = ['RobotsChecker']
