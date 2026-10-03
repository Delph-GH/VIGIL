"""
shared_ingestion/multi_strategy_engine.py

Multi-strategy scraping engine with fallback.

Extracted from Diaspora's scraping/engine.py (814 LOC)

Tries strategies in order: RSS → Static HTTP → Headless → Stealth
Falls back to next strategy on failure.
"""

import logging
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from shared_types import (
    ScrapedArticle,
    ScrapeResult,
    ScrapeStrategy,
    FailureReport,
    FailureCode,
)
from shared_utils import (
    hash_url,
    get_current_timestamp,
    normalize_url,
)

from .engine_config import EngineConfig
from .domain_throttler import DomainThrottler
from .robots_checker import RobotsChecker
from .failure_diagnostics import (
    diagnose_http_failure,
    diagnose_network_failure,
    diagnose_content_failure,
    create_robots_disallowed_report,
)

logger = logging.getLogger(__name__)


class MultiStrategyEngine:
    """
    Multi-strategy scraping engine.
    
    Tries strategies in order until one succeeds:
    1. RSS (fastest, most reliable)
    2. Static HTTP (simple GET request)
    3. Headless (JavaScript rendering)
    4. Stealth (anti-detection mode)
    
    Features:
    - Rate limiting per domain
    - robots.txt compliance
    - 19-code failure diagnostics
    - Raw HTML archiving
    - Automatic fallback on failure
    
    Usage:
        config = EngineConfig(
            strategies=[ScrapeStrategy.RSS, ScrapeStrategy.STATIC_HTTP],
            enable_robots_txt=True,
            rate_limit_delay=5,
        )
        
        engine = MultiStrategyEngine(config)
        result = engine.scrape_url(
            url="https://example.com/article",
            source_name="Example Source",
        )
        
        if result.success:
            articles = result.articles
        else:
            failure = result.failure
    """
    
    def __init__(self, config: Optional[EngineConfig] = None):
        """
        Initialize engine.
        
        Args:
            config: Engine configuration (uses defaults if None)
        """
        self.config = config or EngineConfig()
        
        # Initialize components
        self.throttler = DomainThrottler(
            default_delay=self.config.rate_limit_delay
        ) if self.config.enable_rate_limiting else None
        
        self.robots_checker = RobotsChecker(
            user_agent=self.config.user_agent
        ) if self.config.enable_robots_txt else None
        
        # Ensure archive directory exists
        if self.config.archive_html and self.config.archive_path:
            self.config.archive_path.mkdir(parents=True, exist_ok=True)
    
    def scrape_url(
        self,
        url: str,
        source_name: str,
        custom_strategies: Optional[List[ScrapeStrategy]] = None,
        custom_delay: Optional[int] = None,
    ) -> ScrapeResult:
        """
        Scrape URL using multi-strategy approach.
        
        Args:
            url: URL to scrape
            source_name: Source identifier
            custom_strategies: Override default strategies for this request
            custom_delay: Override default rate limit delay
            
        Returns:
            ScrapeResult with articles or failure report
        """
        start_time = datetime.now()
        strategies = custom_strategies or self.config.strategies
        
        # Normalize URL
        url = normalize_url(url, remove_query=False, remove_fragment=True)
        
        # Check robots.txt
        if self.robots_checker and not self.robots_checker.can_fetch(url):
            logger.warning(f"Disallowed by robots.txt: {url}")
            failure = create_robots_disallowed_report(
                source_name=source_name,
                url=url,
                strategy=strategies[0] if strategies else ScrapeStrategy.STATIC_HTTP,
            )
            return ScrapeResult(
                source_name=source_name,
                timestamp=get_current_timestamp(),
                success=False,
                failure=failure,
            )
        
        # Rate limiting
        if self.throttler:
            wait_time = self.throttler.wait(url, custom_delay=custom_delay)
            if wait_time > 0:
                logger.debug(f"Rate limited {url}, waited {wait_time:.2f}s")
        
        # Try each strategy
        last_failure = None
        for strategy in strategies:
            logger.info(f"Trying {strategy.value} for {url}")
            
            try:
                # Dispatch to strategy handler
                articles = self._scrape_with_strategy(
                    url=url,
                    source_name=source_name,
                    strategy=strategy,
                )
                
                if articles:
                    # Success!
                    duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
                    logger.info(f"Success with {strategy.value}: {len(articles)} articles from {url}")
                    
                    return ScrapeResult(
                        source_name=source_name,
                        timestamp=get_current_timestamp(),
                        success=True,
                        articles=articles,
                        strategy_used=strategy,
                        duration_ms=duration_ms,
                    )
                else:
                    # Empty result, try next strategy
                    logger.warning(f"Empty result from {strategy.value} for {url}")
                    continue
            
            except Exception as e:
                # Strategy failed, diagnose and try next
                logger.warning(f"{strategy.value} failed for {url}: {e}")
                last_failure = diagnose_network_failure(
                    source_name=source_name,
                    url=url,
                    error=e,
                    strategy=strategy,
                )
                continue
        
        # All strategies failed
        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        logger.error(f"All strategies failed for {url}")
        
        return ScrapeResult(
            source_name=source_name,
            timestamp=get_current_timestamp(),
            success=False,
            failure=last_failure or FailureReport(
                source_name=source_name,
                url=url,
                timestamp=get_current_timestamp(),
                failure_code=FailureCode.UNKNOWN_ERROR,
                failure_detail="All strategies failed",
                strategy_attempted=strategies[-1] if strategies else ScrapeStrategy.STATIC_HTTP,
            ),
            duration_ms=duration_ms,
        )
    
    def _scrape_with_strategy(
        self,
        url: str,
        source_name: str,
        strategy: ScrapeStrategy,
    ) -> List[ScrapedArticle]:
        """
        Scrape using specific strategy.
        
        Args:
            url: URL to scrape
            source_name: Source identifier
            strategy: Strategy to use
            
        Returns:
            List of scraped articles (empty if none found)
            
        Raises:
            Exception: If scraping fails
        """
        if strategy == ScrapeStrategy.RSS:
            return self._scrape_rss(url, source_name)
        elif strategy == ScrapeStrategy.STATIC_HTTP:
            return self._scrape_static(url, source_name)
        elif strategy == ScrapeStrategy.HEADLESS:
            return self._scrape_headless(url, source_name)
        elif strategy == ScrapeStrategy.STEALTH:
            return self._scrape_stealth(url, source_name)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
    
    def _scrape_rss(
        self,
        url: str,
        source_name: str,
    ) -> List[ScrapedArticle]:
        """
        Scrape RSS feed.
        
        Note: This is a placeholder. Actual RSS parsing would require
        feedparser library and is left for application-specific implementation.
        
        Args:
            url: RSS feed URL
            source_name: Source identifier
            
        Returns:
            List of articles from feed
        """
        # Placeholder - would use feedparser in production
        # This is where you'd integrate feedparser to parse RSS/Atom
        logger.warning("RSS scraping not implemented - use feedparser in production")
        return []
    
    def _scrape_static(
        self,
        url: str,
        source_name: str,
    ) -> List[ScrapedArticle]:
        """
        Scrape using static HTTP request.
        
        Note: This is a placeholder. Actual HTTP requests would require
        requests/httpx library and HTML parsing with BeautifulSoup/lxml.
        
        Args:
            url: URL to scrape
            source_name: Source identifier
            
        Returns:
            List of articles (typically 1 for single-article pages)
        """
        # Placeholder - would use requests + BeautifulSoup in production
        logger.warning("Static HTTP scraping not implemented - use requests + BeautifulSoup in production")
        
        # Example of what this would return:
        # article = ScrapedArticle(
        #     article_id=hash_url(url),
        #     url=url,
        #     source_name=source_name,
        #     scraped_at=get_current_timestamp(),
        #     extraction_strategy=ScrapeStrategy.STATIC_HTTP,
        #     title="Article Title",
        #     body_text="Article content...",
        # )
        # return [article]
        
        return []
    
    def _scrape_headless(
        self,
        url: str,
        source_name: str,
    ) -> List[ScrapedArticle]:
        """
        Scrape using headless browser (Playwright/Selenium).
        
        Note: This is a placeholder. Actual headless scraping would require
        Playwright or Selenium.
        
        Args:
            url: URL to scrape
            source_name: Source identifier
            
        Returns:
            List of articles
        """
        # Placeholder - would use Playwright in production
        logger.warning("Headless scraping not implemented - use Playwright in production")
        return []
    
    def _scrape_stealth(
        self,
        url: str,
        source_name: str,
    ) -> List[ScrapedArticle]:
        """
        Scrape using stealth mode (anti-detection).
        
        Note: This is a placeholder. Actual stealth scraping would require
        Playwright + stealth plugins.
        
        Args:
            url: URL to scrape
            source_name: Source identifier
            
        Returns:
            List of articles
        """
        # Placeholder - would use Playwright + playwright-stealth in production
        logger.warning("Stealth scraping not implemented - use Playwright + stealth in production")
        return []
    
    def _archive_html(
        self,
        url: str,
        html_content: str,
        article_id: str,
    ) -> Optional[str]:
        """
        Archive raw HTML to disk.
        
        Args:
            url: Source URL
            html_content: Raw HTML
            article_id: Article ID for filename
            
        Returns:
            Path to archived file or None if archiving disabled
        """
        if not self.config.archive_html or not self.config.archive_path:
            return None
        
        try:
            # Create filename from article_id
            filename = f"{article_id}.html"
            filepath = self.config.archive_path / filename
            
            # Write HTML
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.debug(f"Archived HTML to {filepath}")
            return str(filepath)
        
        except Exception as e:
            logger.error(f"Failed to archive HTML: {e}")
            return None


# Export
__all__ = ['MultiStrategyEngine']
