"""
apps/vigil-platform/scraping/vigil_orchestrator.py

Vigil scraping orchestrator using shared_ingestion with async support.

Vigil-specific features:
- French national politics focus
- Async scraping for concurrent source collection
- Entity extraction integration
- Parliamentary source tracking

Uses shared foundation packages while maintaining Vigil's async architecture.
"""

import asyncio
import logging
from pathlib import Path
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor

# Shared foundation packages
from shared_types import (
    ScrapedArticle,
    ScrapeResult,
    ScrapeStrategy,
    SourceConfig,
    SourceCategory,
    Language,
)
from shared_utils import (
    hash_url,
    clean_text,
    get_current_timestamp,
)
from shared_config import (
    load_sources_config,
    get_setting,
)
from shared_ingestion import (
    MultiStrategyEngine,
    EngineConfig,
    SourceHealthMonitor,
    DiagnosticsStats,
    HealthStatus,
)

logger = logging.getLogger(__name__)


class VigilOrchestrator:
    """
    Vigil-specific scraping orchestrator with async support.
    
    Focuses on French national politics:
    - Assemblée Nationale
    - Sénat
    - Political parties
    - Government ministries
    - Think tanks
    
    Features:
    - Async scraping for concurrent collection
    - Health monitoring
    - Pattern detection
    - Integration with Vigil's NLP pipeline
    
    Usage:
        orchestrator = VigilOrchestrator(
            sources_config_path="config/sources.yaml",
        )
        
        # Async scraping
        results = await orchestrator.scrape_all_async()
        
        # Sync scraping (for compatibility)
        results = orchestrator.scrape_all_sources()
    """
    
    def __init__(
        self,
        sources_config_path: str = "config/sources.yaml",
        archive_path: Optional[str] = None,
        enable_health_monitoring: bool = True,
        max_concurrent: int = 5,
    ):
        """
        Initialize orchestrator.
        
        Args:
            sources_config_path: Path to YAML sources config
            archive_path: Path for HTML archives
            enable_health_monitoring: Enable health monitoring
            max_concurrent: Max concurrent async scrapes
        """
        # Load sources from YAML
        self.sources = self._load_sources(sources_config_path)
        
        # Configure engine
        config = EngineConfig(
            strategies=[
                ScrapeStrategy.RSS,
                ScrapeStrategy.STATIC_HTTP,
                ScrapeStrategy.HEADLESS,
            ],
            enable_robots_txt=True,
            enable_rate_limiting=True,
            rate_limit_delay=get_setting('scraping.rate_limit_delay', default=3),
            archive_html=True,
            archive_path=Path(archive_path) if archive_path else Path("data/html_archives"),
        )
        
        # Create engine and monitoring
        self.engine = MultiStrategyEngine(config)
        self.health_monitor = SourceHealthMonitor() if enable_health_monitoring else None
        self.diagnostics = DiagnosticsStats() if enable_health_monitoring else None
        
        # Async configuration
        self.max_concurrent = max_concurrent
        self._executor = ThreadPoolExecutor(max_workers=max_concurrent)
        
        logger.info(f"Initialized Vigil orchestrator with {len(self.sources)} sources")
    
    def _load_sources(self, config_path: str) -> List[SourceConfig]:
        """Load sources from YAML config."""
        sources_yaml = load_sources_config(config_path)
        
        sources = []
        for data in sources_yaml:
            source = SourceConfig(
                source_id=data['source_id'],
                name=data['name'],
                url=data['url'],
                category=SourceCategory(data['category']),
                language=Language(data.get('language', 'fr')),
                rss_url=data.get('rss_url'),
                strategies=[ScrapeStrategy(s) for s in data.get('strategies', ['rss', 'static_http'])],
                rate_limit_delay=data.get('rate_limit_delay', 3),
            )
            sources.append(source)
        
        return sources
    
    # ========================================
    # Synchronous API (backward compatible)
    # ========================================
    
    def scrape_all_sources(
        self,
        skip_unhealthy: bool = True,
        health_threshold: float = 30.0,
    ) -> List[ScrapeResult]:
        """
        Scrape all configured sources (synchronous).
        
        Args:
            skip_unhealthy: Skip sources with health < threshold
            health_threshold: Minimum health score to scrape
            
        Returns:
            List of ScrapeResults
        """
        results = []
        
        for source in self.sources:
            # Skip unhealthy sources if requested
            if skip_unhealthy and self.health_monitor:
                health = self.health_monitor.get_health(source.name)
                if health.health_score < health_threshold:
                    logger.info(f"Skipping {source.name} (health: {health.health_score:.1f})")
                    continue
            
            result = self.scrape_source(source)
            results.append(result)
        
        return results
    
    def scrape_source(self, source: SourceConfig) -> ScrapeResult:
        """
        Scrape single source with health monitoring.
        
        Args:
            source: Source configuration
            
        Returns:
            ScrapeResult
        """
        logger.info(f"Scraping {source.name} ({source.category.value})")
        
        # Scrape
        result = self.engine.scrape_url(
            url=source.url,
            source_name=source.name,
            custom_strategies=source.strategies,
            custom_delay=source.rate_limit_delay,
        )
        
        # Update health monitoring
        if self.health_monitor and self.diagnostics:
            if result.success:
                self.health_monitor.record_success(source.name, result.duration_ms)
            else:
                self.health_monitor.record_failure(source.name, result.failure.failure_code)
                self.diagnostics.record_failure(source.name, result.failure.failure_code)
                
                # Log pattern if detected
                pattern = self.diagnostics.detect_failure_pattern(source.name)
                if pattern:
                    logger.warning(f"Pattern detected for {source.name}: {pattern}")
        
        return result
    
    # ========================================
    # Asynchronous API (Vigil-specific)
    # ========================================
    
    async def scrape_all_async(
        self,
        skip_unhealthy: bool = True,
        health_threshold: float = 30.0,
    ) -> List[ScrapeResult]:
        """
        Scrape all sources asynchronously (concurrent).
        
        Args:
            skip_unhealthy: Skip sources with health < threshold
            health_threshold: Minimum health score to scrape
            
        Returns:
            List of ScrapeResults
        """
        # Filter sources
        sources_to_scrape = []
        for source in self.sources:
            if skip_unhealthy and self.health_monitor:
                health = self.health_monitor.get_health(source.name)
                if health.health_score < health_threshold:
                    logger.info(f"Skipping {source.name} (health: {health.health_score:.1f})")
                    continue
            sources_to_scrape.append(source)
        
        # Scrape concurrently with semaphore
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def scrape_with_semaphore(source):
            async with semaphore:
                return await self.scrape_source_async(source)
        
        # Execute all scrapes concurrently
        tasks = [scrape_with_semaphore(source) for source in sources_to_scrape]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        return [r for r in results if isinstance(r, ScrapeResult)]
    
    async def scrape_source_async(self, source: SourceConfig) -> ScrapeResult:
        """
        Scrape single source asynchronously.
        
        Wraps synchronous engine in async executor.
        
        Args:
            source: Source configuration
            
        Returns:
            ScrapeResult
        """
        loop = asyncio.get_event_loop()
        
        # Run sync scrape in executor
        result = await loop.run_in_executor(
            self._executor,
            self.scrape_source,
            source
        )
        
        return result
    
    async def scrape_category_async(
        self,
        category: SourceCategory,
        skip_unhealthy: bool = True,
    ) -> List[ScrapeResult]:
        """
        Scrape all sources in category asynchronously.
        
        Args:
            category: Category to scrape
            skip_unhealthy: Skip unhealthy sources
            
        Returns:
            List of ScrapeResults
        """
        category_sources = [s for s in self.sources if s.category == category]
        logger.info(f"Scraping {len(category_sources)} sources in {category.value} (async)")
        
        # Create temporary orchestrator with filtered sources
        temp_sources = self.sources
        self.sources = category_sources
        
        results = await self.scrape_all_async(skip_unhealthy=skip_unhealthy)
        
        # Restore original sources
        self.sources = temp_sources
        
        return results
    
    # ========================================
    # Health & Monitoring
    # ========================================
    
    def get_health_report(self) -> dict:
        """
        Get health report for all sources.
        
        Returns:
            Dictionary with health statistics
        """
        if not self.health_monitor:
            return {"error": "Health monitoring not enabled"}
        
        all_sources = [s.name for s in self.sources]
        
        # Get health for each source
        health_by_status = {
            HealthStatus.EXCELLENT: [],
            HealthStatus.GOOD: [],
            HealthStatus.FAIR: [],
            HealthStatus.POOR: [],
            HealthStatus.CRITICAL: [],
        }
        
        for source_name in all_sources:
            health = self.health_monitor.get_health(source_name)
            health_by_status[health.health_status].append({
                'name': source_name,
                'score': health.health_score,
                'success_rate': health.success_rate,
            })
        
        return {
            'total_sources': len(all_sources),
            'by_status': {
                status.value: sources
                for status, sources in health_by_status.items()
            },
            'unhealthy': self.health_monitor.get_unhealthy_sources(threshold=50.0),
        }
    
    def get_parliamentary_sources(self) -> List[SourceConfig]:
        """Get sources from parliamentary category."""
        return [s for s in self.sources if s.category == SourceCategory.PARLIAMENTARY]
    
    def get_party_sources(self) -> List[SourceConfig]:
        """Get sources from political parties category."""
        return [s for s in self.sources if s.category == SourceCategory.PARTIES]
    
    def __del__(self):
        """Cleanup executor on deletion."""
        if hasattr(self, '_executor'):
            self._executor.shutdown(wait=False)


# Export
__all__ = ['VigilOrchestrator']
