"""
Tests for shared_config package.

Tests YAML loading and settings management.
"""

import pytest
import tempfile
from pathlib import Path
from shared_config import (
    ConfigError,
    load_yaml,
    load_sources_config,
    save_yaml,
    merge_configs,
    validate_config_schema,
    Settings,
    get_setting,
    set_setting,
    load_settings_from_dict,
    get_settings,
)


class TestYAMLLoader:
    """Test YAML loading utilities."""
    
    def test_load_yaml_valid(self):
        """Test loading valid YAML."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("key: value\nnumber: 42\n")
            f.flush()
            
            data = load_yaml(f.name)
            assert data['key'] == 'value'
            assert data['number'] == 42
            
            Path(f.name).unlink()
    
    def test_load_yaml_not_found(self):
        """Test loading non-existent file."""
        with pytest.raises(ConfigError, match="not found"):
            load_yaml("nonexistent.yaml")
    
    def test_load_yaml_invalid(self):
        """Test loading invalid YAML."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: syntax:\n")
            f.flush()
            
            with pytest.raises(ConfigError, match="Invalid YAML"):
                load_yaml(f.name)
            
            Path(f.name).unlink()
    
    def test_load_sources_config_valid(self):
        """Test loading sources configuration."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
sources:
  - source_id: "test_001"
    name: "Test Source"
    url: "https://example.com"
    category: "medias"
    language: "fr"
            """)
            f.flush()
            
            sources = load_sources_config(f.name)
            assert len(sources) == 1
            assert sources[0]['source_id'] == 'test_001'
            assert sources[0]['name'] == 'Test Source'
            
            Path(f.name).unlink()
    
    def test_load_sources_config_missing_key(self):
        """Test loading sources with missing 'sources' key."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("other_key: value\n")
            f.flush()
            
            with pytest.raises(ConfigError, match="Missing 'sources'"):
                load_sources_config(f.name)
            
            Path(f.name).unlink()
    
    def test_load_sources_config_missing_required_fields(self):
        """Test sources missing required fields."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
sources:
  - source_id: "test_001"
    name: "Test Source"
    # Missing url and category
            """)
            f.flush()
            
            with pytest.raises(ConfigError, match="missing required fields"):
                load_sources_config(f.name)
            
            Path(f.name).unlink()
    
    def test_save_yaml(self):
        """Test saving YAML."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.yaml"
            data = {'key': 'value', 'number': 42}
            
            save_yaml(data, file_path)
            
            assert file_path.exists()
            loaded = load_yaml(file_path)
            assert loaded == data
    
    def test_merge_configs(self):
        """Test configuration merging."""
        base = {
            'key1': 'value1',
            'key2': 'keep',
            'nested': {'a': 1, 'b': 2}
        }
        
        override = {
            'key1': 'overridden',
            'nested': {'b': 20, 'c': 3}
        }
        
        merged = merge_configs(base, override)
        
        assert merged['key1'] == 'overridden'
        assert merged['key2'] == 'keep'
        assert merged['nested']['a'] == 1
        assert merged['nested']['b'] == 20
        assert merged['nested']['c'] == 3
    
    def test_validate_config_schema_valid(self):
        """Test schema validation with valid config."""
        config = {'name': 'test', 'count': 5, 'flag': True}
        schema = {'name': str, 'count': int, 'flag': bool}
        
        # Should not raise
        validate_config_schema(config, schema)
    
    def test_validate_config_schema_missing_key(self):
        """Test schema validation with missing key."""
        config = {'name': 'test'}
        schema = {'name': str, 'count': int}
        
        with pytest.raises(ConfigError, match="Missing required"):
            validate_config_schema(config, schema)
    
    def test_validate_config_schema_wrong_type(self):
        """Test schema validation with wrong type."""
        config = {'name': 'test', 'count': 'not an int'}
        schema = {'name': str, 'count': int}
        
        with pytest.raises(ConfigError, match="should be int"):
            validate_config_schema(config, schema)


class TestSettings:
    """Test Settings class."""
    
    def test_get_set_simple(self):
        """Test simple get/set."""
        settings = Settings()
        settings.set('key', 'value')
        assert settings.get('key') == 'value'
    
    def test_get_default(self):
        """Test get with default."""
        settings = Settings()
        assert settings.get('nonexistent', default='default') == 'default'
    
    def test_get_set_nested(self):
        """Test nested key access with dot notation."""
        settings = Settings()
        settings.set('section.key', 'value')
        assert settings.get('section.key') == 'value'
    
    def test_get_int(self):
        """Test get_int conversion."""
        settings = Settings()
        settings.set('count', 42)
        assert settings.get_int('count') == 42
        
        # String to int
        settings.set('count_str', '100')
        assert settings.get_int('count_str') == 100
    
    def test_get_float(self):
        """Test get_float conversion."""
        settings = Settings()
        settings.set('value', 3.14)
        assert settings.get_float('value') == 3.14
    
    def test_get_bool(self):
        """Test get_bool conversion."""
        settings = Settings()
        
        settings.set('flag', True)
        assert settings.get_bool('flag') is True
        
        # String conversions
        settings.set('flag_str', 'true')
        assert settings.get_bool('flag_str') is True
        
        settings.set('flag_str', 'false')
        assert settings.get_bool('flag_str') is False
        
        settings.set('flag_str', '1')
        assert settings.get_bool('flag_str') is True
    
    def test_get_path(self):
        """Test get_path conversion."""
        settings = Settings()
        settings.set('database.path', '/tmp/db.sqlite')
        
        path = settings.get_path('database.path')
        assert isinstance(path, Path)
        assert str(path) == '/tmp/db.sqlite'
    
    def test_update(self):
        """Test update from dictionary."""
        settings = Settings()
        settings.update({
            'database': {'path': '/tmp/db.sqlite'},
            'scraping': {'rate_limit': 5}
        })
        
        assert settings.get('database.path') == '/tmp/db.sqlite'
        assert settings.get('scraping.rate_limit') == 5
    
    def test_to_dict(self):
        """Test export to dictionary."""
        settings = Settings()
        settings.set('key', 'value')
        settings.set('nested.key', 'nested_value')
        
        data = settings.to_dict()
        assert data['key'] == 'value'
        assert data['nested']['key'] == 'nested_value'
    
    def test_clear(self):
        """Test clearing settings."""
        settings = Settings()
        settings.set('key', 'value')
        settings.clear()
        
        assert settings.get('key') is None


class TestGlobalSettings:
    """Test global settings functions."""
    
    def test_get_set_setting(self):
        """Test global get/set."""
        set_setting('test.key', 'test_value')
        assert get_setting('test.key') == 'test_value'
        
        # Clean up
        get_settings().clear()
    
    def test_load_settings_from_dict(self):
        """Test loading settings from dict."""
        load_settings_from_dict({
            'database': {'path': '/tmp/test.db'}
        })
        
        assert get_setting('database.path') == '/tmp/test.db'
        
        # Clean up
        get_settings().clear()


class TestCrossPackageIntegration:
    """Test shared_config with shared_types."""
    
    def test_source_config_with_enums(self):
        """Test loading source config and converting to SourceConfig model."""
        from shared_types import SourceConfig, SourceCategory, Language, ScrapeStrategy
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
sources:
  - source_id: "le_monde_001"
    name: "Le Monde"
    url: "https://lemonde.fr"
    category: "medias"
    language: "fr"
    rss_url: "https://lemonde.fr/rss"
    strategies: ["rss", "static_http"]
    rate_limit_delay: 5
            """)
            f.flush()
            
            # Load YAML
            sources = load_sources_config(f.name)
            
            # Convert to SourceConfig model
            source_data = sources[0]
            source_config = SourceConfig(
                source_id=source_data['source_id'],
                name=source_data['name'],
                url=source_data['url'],
                category=SourceCategory(source_data['category']),
                language=Language(source_data['language']),
                rss_url=source_data['rss_url'],
                strategies=[ScrapeStrategy(s) for s in source_data['strategies']],
                rate_limit_delay=source_data['rate_limit_delay'],
            )
            
            assert source_config.source_id == 'le_monde_001'
            assert source_config.category == SourceCategory.MEDIAS
            assert source_config.language == Language.FRENCH
            assert ScrapeStrategy.RSS in source_config.strategies
            
            Path(f.name).unlink()


class TestPackageExports:
    """Test package exports."""
    
    def test_all_exports_accessible(self):
        """Test all __all__ exports are accessible."""
        import shared_config
        
        assert hasattr(shared_config, '__all__')
        
        for name in shared_config.__all__:
            assert hasattr(shared_config, name), f"{name} not accessible"
    
    def test_version(self):
        """Test package version."""
        import shared_config
        assert hasattr(shared_config, '__version__')
        assert shared_config.__version__ == "0.1.0"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
