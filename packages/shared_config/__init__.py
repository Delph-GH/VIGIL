"""
shared_config

Configuration management for French Intelligence Monorepo.

Provides YAML loading and application settings management.

Usage:
    from shared_config import load_yaml, load_sources_config
    from shared_config import get_setting, set_setting
    
    # Load YAML config
    sources = load_sources_config("config/sources.yaml")
    
    # Get/set application settings
    db_path = get_setting('database.path', default='data/articles.db')
    set_setting('scraping.rate_limit', 5)
"""

from .yaml_loader import (
    ConfigError,
    load_yaml,
    load_sources_config,
    save_yaml,
    merge_configs,
    validate_config_schema,
)

from .settings import (
    Settings,
    get_setting,
    set_setting,
    load_settings_from_dict,
    get_settings,
)

__version__ = "0.1.0"

__all__ = [
    # YAML utilities
    "ConfigError",
    "load_yaml",
    "load_sources_config",
    "save_yaml",
    "merge_configs",
    "validate_config_schema",
    
    # Settings
    "Settings",
    "get_setting",
    "set_setting",
    "load_settings_from_dict",
    "get_settings",
]
