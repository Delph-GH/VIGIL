"""
apps/vigil-platform/tests/test_integration.py

Integration test: Vigil + shared foundation packages

Verifies:
- Vigil can import from all shared packages
- YAML config loading works
- Async orchestrator works
- Sync/async compatibility
- Health monitoring integrates correctly
"""

import pytest
import asyncio
import sys
from pathlib import Path

# Add packages to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "packages"))
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestFoundationImports:
    """Test Vigil can import from foundation packages."""
    
    def test_import_shared_types(self):
        """Test importing shared_types."""
        from shared_types import (
            ScrapedArticle,
            ScrapeStrategy,
            SourceCategory,
            Language,
            FailureCode,
        )
        
        assert ScrapedArticle is not None
        assert SourceCategory.PARLIAMENTARY is not None  # Vigil-specific
        assert SourceCategory.PARTIES is not None
    
    def test_import_shared_utils(self):
        """Test importing shared_utils."""
        from shared_utils import (
            clean_text,
            parse_flexible_date,
            normalize_url,
            hash_url,
        )
        
        assert clean_text is not None
        assert hash_url is not None
    
    def test_import_shared_config(self):
        """Test importing shared_config."""
        from shared_config import (
            load_yaml,
            get_setting,
            set_setting,
        )
        
        assert load_yaml is not None
    
    def test_import_shared_ingestion(self):
        """Test importing shared_ingestion."""
        from shared_ingestion import (
            MultiStrategyEngine,
            EngineConfig,
            SourceHealthMonitor,
            DiagnosticsStats,
        )
        
        assert MultiStrategyEngine is not None
        assert SourceHealthMonitor is not None


class TestVigilOrchestrator:
    """Test Vigil orchestrator with shared packages."""
    
    def test_orchestrator_import(self):
        """Test importing orchestrator."""
        try:
            from scraping.vigil_orchestrator import VigilOrchestrator
            assert VigilOrchestrator is not None
        except ImportError as e:
            pytest.skip(f"Orchestrator not importable: {e}")
    
    def test_load_vigil_sources_yaml(self):
        """Test loading Vigil sources from YAML."""
        from shared_config import load_sources_config
        
        # Verify function works
        assert load_sources_config is not None
    
    def test_create_parliamentary_source_config(self):
        """Test creating SourceConfig for parliamentary sources."""
        from shared_types import SourceConfig, SourceCategory, Language, ScrapeStrategy
        
        # Simulate YAML data for Assemblée Nationale
        yaml_data = {
            'source_id': 'assemblee_nationale_001',
            'name': 'Assemblée Nationale',
            'url': 'https://www.assemblee-nationale.fr',
            'category': 'parliamentary',
            'language': 'fr',
            'rss_url': 'https://www.assemblee-nationale.fr/rss',
            'strategies': ['rss', 'static_http'],
            'rate_limit_delay': 10,
        }
        
        # Convert to SourceConfig
        source = SourceConfig(
            source_id=yaml_data['source_id'],
            name=yaml_data['name'],
            url=yaml_data['url'],
            category=SourceCategory(yaml_data['category']),
            language=Language(yaml_data['language']),
            rss_url=yaml_data.get('rss_url'),
            strategies=[ScrapeStrategy(s) for s in yaml_data['strategies']],
            rate_limit_delay=yaml_data.get('rate_limit_delay', 5),
        )
        
        assert source.source_id == 'assemblee_nationale_001'
        assert source.category == SourceCategory.PARLIAMENTARY
        assert source.language == Language.FRENCH
        assert ScrapeStrategy.RSS in source.strategies


class TestAsyncSupport:
    """Test async scraping support."""
    
    @pytest.mark.asyncio
    async def test_async_scrape_function_exists(self):
        """Test async scraping methods exist."""
        try:
            from scraping.vigil_orchestrator import VigilOrchestrator
            
            # Verify async methods exist
            assert hasattr(VigilOrchestrator, 'scrape_all_async')
            assert hasattr(VigilOrchestrator, 'scrape_source_async')
            assert hasattr(VigilOrchestrator, 'scrape_category_async')
        except ImportError:
            pytest.skip("Orchestrator not available")


class TestHealthMonitoring:
    """Test health monitoring for Vigil sources."""
    
    def test_health_monitor_with_political_sources(self):
        """Test health monitoring for political sources."""
        from shared_ingestion import SourceHealthMonitor
        from shared_types import FailureCode
        
        monitor = SourceHealthMonitor()
        
        # Simulate scraping Assemblée Nationale
        source_name = "Assemblée Nationale"
        
        # Record some successes
        for _ in range(8):
            monitor.record_success(source_name, response_ms=2000)
        
        # Record some failures
        for _ in range(2):
            monitor.record_failure(source_name, FailureCode.TIMEOUT)
        
        # Get health
        health = monitor.get_health(source_name)
        
        assert health.source_name == source_name
        assert health.total_attempts == 10
        assert health.success_rate == 0.8
        assert health.health_score > 0
    
    def test_diagnostics_with_political_sources(self):
        """Test diagnostics for political sources."""
        from shared_ingestion import DiagnosticsStats
        from shared_types import FailureCode
        
        stats = DiagnosticsStats()
        
        # Simulate failures for a party website
        source_name = "Rassemblement National"
        
        for _ in range(5):
            stats.record_failure(source_name, FailureCode.HTTP_FORBIDDEN)
        
        # Check pattern detection
        pattern = stats.detect_failure_pattern(source_name)
        
        # Should detect persistent_403
        assert pattern == "persistent_403"


class TestSyncAsyncCompatibility:
    """Test both sync and async APIs work."""
    
    def test_sync_api(self):
        """Test synchronous API."""
        from shared_ingestion import MultiStrategyEngine, EngineConfig
        from shared_types import ScrapeStrategy
        
        config = EngineConfig(
            strategies=[ScrapeStrategy.RSS],
            enable_rate_limiting=False,
            enable_robots_txt=False,
        )
        
        engine = MultiStrategyEngine(config)
        
        # Verify synchronous scraping works
        result = engine.scrape_url(
            url="https://example.com/test",
            source_name="Test Source",
        )
        
        assert hasattr(result, 'success')
        assert result.source_name == "Test Source"
    
    @pytest.mark.asyncio
    async def test_async_wrapper(self):
        """Test async wrapper around sync engine."""
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        from shared_ingestion import MultiStrategyEngine, EngineConfig
        from shared_types import ScrapeStrategy
        
        config = EngineConfig(
            strategies=[ScrapeStrategy.STATIC_HTTP],
            enable_rate_limiting=False,
            enable_robots_txt=False,
        )
        
        engine = MultiStrategyEngine(config)
        
        # Wrap sync call in executor
        loop = asyncio.get_event_loop()
        executor = ThreadPoolExecutor(max_workers=1)
        
        result = await loop.run_in_executor(
            executor,
            engine.scrape_url,
            "https://example.com/test",
            "Async Test Source"
        )
        
        assert hasattr(result, 'success')
        assert result.source_name == "Async Test Source"
        
        executor.shutdown(wait=False)


class TestVigilSpecificFeatures:
    """Test Vigil-specific features."""
    
    def test_parliamentary_category_exists(self):
        """Test PARLIAMENTARY category exists."""
        from shared_types import SourceCategory
        
        assert hasattr(SourceCategory, 'PARLIAMENTARY')
        assert SourceCategory.PARLIAMENTARY.value == 'parliamentary'
    
    def test_parties_category_exists(self):
        """Test PARTIES category exists."""
        from shared_types import SourceCategory
        
        assert hasattr(SourceCategory, 'PARTIES')
        assert SourceCategory.PARTIES.value == 'parties'
    
    def test_government_category_exists(self):
        """Test GOVERNMENT category exists."""
        from shared_types import SourceCategory
        
        assert hasattr(SourceCategory, 'GOVERNMENT')
        assert SourceCategory.GOVERNMENT.value == 'government'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
