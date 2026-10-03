"""
shared_ingestion

Multi-strategy scraping engine with diagnostics and health monitoring.

Provides:
- MultiStrategyEngine: Main scraping orchestrator
- EngineConfig: Configuration dataclass
- DomainThrottler: Rate limiting per domain
- RobotsChecker: robots.txt compliance
- Failure diagnostics: 19-code error system
- DiagnosticsStats: Failure statistics and pattern detection
- SourceHealthMonitor: Health scoring and reliability metrics

Usage:
    from shared_ingestion import (
        MultiStrategyEngine,
        EngineConfig,
        SourceHealthMonitor,
    )
    
    # Configure and create engine
    config = EngineConfig(
        strategies=[ScrapeStrategy.RSS, ScrapeStrategy.STATIC_HTTP],
        enable_robots_txt=True,
        rate_limit_delay=5,
    )
    engine = MultiStrategyEngine(config)
    
    # Monitor source health
    monitor = SourceHealthMonitor()
    
    # Scrape
    result = engine.scrape_url(
        url="https://example.com/article",
        source_name="Example Source",
    )
    
    # Update health
    if result.success:
        monitor.record_success("Example Source", result.duration_ms)
    else:
        monitor.record_failure("Example Source", result.failure.failure_code)
    
    # Check health
    health = monitor.get_health("Example Source")
    print(f"Health score: {health.health_score:.1f}/100")
"""

from .engine_config import EngineConfig
from .domain_throttler import DomainThrottler
from .robots_checker import RobotsChecker
from .multi_strategy_engine import MultiStrategyEngine
from .failure_diagnostics import (
    diagnose_http_failure,
    diagnose_network_failure,
    diagnose_content_failure,
    create_robots_disallowed_report,
    create_rate_limit_report,
)
from .diagnostics import DiagnosticsStats
from .source_health import (
    HealthStatus,
    HealthMetrics,
    SourceHealthMonitor,
)

__version__ = "0.1.0"

__all__ = [
    # Main engine
    "MultiStrategyEngine",
    "EngineConfig",
    
    # Components
    "DomainThrottler",
    "RobotsChecker",
    
    # Failure diagnostics
    "diagnose_http_failure",
    "diagnose_network_failure",
    "diagnose_content_failure",
    "create_robots_disallowed_report",
    "create_rate_limit_report",
    
    # Diagnostics stats
    "DiagnosticsStats",
    
    # Health monitoring
    "HealthStatus",
    "HealthMetrics",
    "SourceHealthMonitor",
]

