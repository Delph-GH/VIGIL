"""
shared_ingestion/engine_config.py

Configuration for MultiStrategyEngine.

Replaces hardcoded settings with declarative config.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List
from shared_types import ScrapeStrategy


@dataclass
class EngineConfig:
    """
    Configuration for MultiStrategyEngine.
    
    Attributes:
        strategies: List of strategies to try in order
        enable_robots_txt: Check robots.txt before scraping
        enable_rate_limiting: Rate limit requests per domain
        rate_limit_delay: Default delay between requests (seconds)
        max_retries: Maximum retry attempts per strategy
        timeout: Request timeout (seconds)
        user_agent: User agent string
        archive_html: Save raw HTML to disk
        archive_path: Path for HTML archives
        headless_browser: Browser for headless strategy ('chromium', 'firefox', 'webkit')
        stealth_mode: Enable stealth mode features
    """
    
    # Strategy configuration
    strategies: List[ScrapeStrategy] = field(default_factory=lambda: [
        ScrapeStrategy.RSS,
        ScrapeStrategy.STATIC_HTTP,
        ScrapeStrategy.HEADLESS,
        ScrapeStrategy.STEALTH,
    ])
    
    # Access control
    enable_robots_txt: bool = True
    enable_rate_limiting: bool = True
    rate_limit_delay: int = 5  # seconds
    
    # Retry and timeout
    max_retries: int = 3
    timeout: int = 30  # seconds
    
    # Headers
    user_agent: str = "Mozilla/5.0 (compatible; FrenchIntelligenceBot/1.0)"
    
    # HTML archiving
    archive_html: bool = True
    archive_path: Optional[Path] = None
    
    # Browser configuration
    headless_browser: str = "chromium"  # chromium, firefox, webkit
    stealth_mode: bool = True
    
    def __post_init__(self):
        """Validate configuration."""
        if self.archive_html and not self.archive_path:
            self.archive_path = Path("data/html_archives")
        
        if self.archive_path:
            self.archive_path = Path(self.archive_path)
        
        # Ensure strategies list is not empty
        if not self.strategies:
            self.strategies = [ScrapeStrategy.STATIC_HTTP]
    
    def get_delay_for_source(self, source_name: str, default: Optional[int] = None) -> int:
        """
        Get rate limit delay for specific source.
        
        Args:
            source_name: Source identifier
            default: Default delay if not configured
            
        Returns:
            Delay in seconds
        """
        # Could be extended to support per-source delays
        return default if default is not None else self.rate_limit_delay


# Export
__all__ = ['EngineConfig']
