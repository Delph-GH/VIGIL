"""
apps/diaspora-platform/scraping/scrape_orchestrator.py

Diaspora scraping orchestrator using shared_ingestion.

REPLACES:
- scraping/engine.py (814 LOC)
- scraping/diagnostics.py (337 LOC)
- scraping/monitor.py (375 LOC)

Total: ~1,526 LOC → ~200 LOC (87% reduction)
"""

import logging
from pathlib import Path
from typing import List, Optional

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


class DiasporaScrapeOrchestrator:
    """
    Diaspora-specific scraping orchestrator.
    
    Uses shared_ingestion for core scraping, adds Diaspora-specific logic:
    - Source filtering by category (consulaire, communaute, etc.)
    - Bavaria/BW regional focus
    - French/German language handling
    - Health-based source prioritization
    
    Usage:
        orchestrator = DiasporaScrapeOrchestrator(
            sources_config_path="config/sources.yaml",
            archive_path="data/html_archives",
        )
        
        results = orchestrator.scrape_all_sources()
        
        # Or scrape specific categories
        results = orchestrator.scrape_category(SourceCategory.CONSULAIRE)
    """
    
    def __init__(
        self,
        sources_config_path: str = "config/sources.yaml",
        archive_path: Optional[str] = None,
        enable_health_monitoring: bool = True,
    ):
        """
        Initialize orchestrator.
        
        Args:
            sources_config_path: Path to YAML sources config
            archive_path: Path for HTML archives
            enable_health_monitoring: Enable health monitoring
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
            rate_limit_delay=get_setting('scraping.rate_limit_delay', default=5),
            archive_html=True,
            archive_path=Path(archive_path) if archive_path else Path("data/html_archives"),
        )
        
        # Create engine and monitoring
        self.engine = MultiStrategyEngine(config)
        self.health_monitor = SourceHealthMonitor() if enable_health_monitoring else None
        self.diagnostics = DiagnosticsStats() if enable_health_monitoring else None
        
        logger.info(f"Initialized orchestrator with {len(self.sources)} sources")
    
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
                rate_limit_delay=data.get('rate_limit_delay', 5),
            )
            sources.append(source)
        
        return sources
    
    def scrape_all_sources(
        self,
        skip_unhealthy: bool = True,
        health_threshold: float = 30.0,
    ) -> List[ScrapeResult]:
        """
        Scrape all configured sources.
        
        Args:
            skip_unhealthy: Skip sources with health < threshold
            health_threshold: Minimum health score to scrape
            
        Returns:
            List of ScrapeResults
        """
        results = []
        
        # Prioritize by health if monitoring enabled
        sources = self._prioritize_sources() if self.health_monitor else self.sources
        
        for source in sources:
            # Skip unhealthy sources if requested
            if skip_unhealthy and self.health_monitor:
                health = self.health_monitor.get_health(source.name)
                if health.health_score < health_threshold:
                    logger.info(f"Skipping {source.name} (health: {health.health_score:.1f})")
                    continue
            
            # Scrape source
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
    
    def scrape_category(
        self,
        category: SourceCategory,
        skip_unhealthy: bool = True,
    ) -> List[ScrapeResult]:
        """
        Scrape all sources in category.
        
        Args:
            category: Category to scrape
            skip_unhealthy: Skip unhealthy sources
            
        Returns:
            List of ScrapeResults
        """
        category_sources = [s for s in self.sources if s.category == category]
        logger.info(f"Scraping {len(category_sources)} sources in {category.value}")
        
        results = []
        for source in category_sources:
            if skip_unhealthy and self.health_monitor:
                health = self.health_monitor.get_health(source.name)
                if health.health_score < 30.0:
                    continue
            
            result = self.scrape_source(source)
            results.append(result)
        
        return results
    
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
    
    def _prioritize_sources(self) -> List[SourceConfig]:
        """Prioritize sources by health score."""
        if not self.health_monitor:
            return self.sources
        
        # Sort by health score (descending)
        return sorted(
            self.sources,
            key=lambda s: self.health_monitor.get_health(s.name).health_score,
            reverse=True
        )


# Export
__all__ = ['DiasporaScrapeOrchestrator']
