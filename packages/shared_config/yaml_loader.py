"""
shared_config/yaml_loader.py

YAML configuration loading with validation.

Replaces hardcoded Python configs with declarative YAML.
"""

import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional
import os


class ConfigError(Exception):
    """Configuration loading or validation error."""
    pass


def load_yaml(file_path: str | Path) -> Dict[str, Any]:
    """
    Load YAML configuration file.
    
    Args:
        file_path: Path to YAML file
        
    Returns:
        Parsed YAML as dictionary
        
    Raises:
        ConfigError: If file not found or invalid YAML
        
    Example:
        >>> config = load_yaml("config/sources.yaml")
        >>> print(config['sources'][0]['name'])
        "Le Monde"
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise ConfigError(f"Config file not found: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        if data is None:
            raise ConfigError(f"Empty config file: {file_path}")
        
        return data
    
    except yaml.YAMLError as e:
        raise ConfigError(f"Invalid YAML in {file_path}: {e}")
    
    except Exception as e:
        raise ConfigError(f"Error loading {file_path}: {e}")


def load_sources_config(file_path: str | Path) -> List[Dict[str, Any]]:
    """
    Load sources configuration from YAML.
    
    Expected structure:
    ```yaml
    sources:
      - source_id: "le_monde_001"
        name: "Le Monde"
        url: "https://lemonde.fr"
        category: "medias"
        language: "fr"
        rss_url: "https://lemonde.fr/rss"
        strategies: ["rss", "static_http"]
        rate_limit_delay: 5
    ```
    
    Args:
        file_path: Path to sources YAML file
        
    Returns:
        List of source configurations
        
    Raises:
        ConfigError: If invalid structure
    """
    data = load_yaml(file_path)
    
    if 'sources' not in data:
        raise ConfigError(f"Missing 'sources' key in {file_path}")
    
    sources = data['sources']
    
    if not isinstance(sources, list):
        raise ConfigError(f"'sources' must be a list in {file_path}")
    
    # Validate each source has required fields
    required_fields = ['source_id', 'name', 'url', 'category']
    
    for i, source in enumerate(sources):
        if not isinstance(source, dict):
            raise ConfigError(f"Source {i} is not a dictionary")
        
        missing = [f for f in required_fields if f not in source]
        if missing:
            raise ConfigError(
                f"Source {i} missing required fields: {', '.join(missing)}"
            )
    
    return sources


def save_yaml(data: Dict[str, Any], file_path: str | Path) -> None:
    """
    Save dictionary to YAML file.
    
    Args:
        data: Dictionary to save
        file_path: Output path
        
    Raises:
        ConfigError: If save fails
        
    Example:
        >>> config = {'sources': [...]}
        >>> save_yaml(config, "output/sources.yaml")
    """
    file_path = Path(file_path)
    
    try:
        # Create parent directories if needed
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(
                data,
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False
            )
    
    except Exception as e:
        raise ConfigError(f"Error saving {file_path}: {e}")


def merge_configs(*configs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge multiple configuration dictionaries.
    
    Later configs override earlier ones.
    
    Args:
        *configs: Configuration dictionaries to merge
        
    Returns:
        Merged configuration
        
    Example:
        >>> base = {'key': 'value1', 'other': 'keep'}
        >>> override = {'key': 'value2'}
        >>> merge_configs(base, override)
        {'key': 'value2', 'other': 'keep'}
    """
    result = {}
    
    for config in configs:
        if not isinstance(config, dict):
            continue
        
        for key, value in config.items():
            if isinstance(value, dict) and key in result and isinstance(result[key], dict):
                # Recursively merge nested dicts
                result[key] = merge_configs(result[key], value)
            else:
                # Override value
                result[key] = value
    
    return result


def validate_config_schema(
    config: Dict[str, Any],
    schema: Dict[str, type]
) -> None:
    """
    Validate configuration against simple schema.
    
    Args:
        config: Configuration to validate
        schema: Schema as {key: expected_type}
        
    Raises:
        ConfigError: If validation fails
        
    Example:
        >>> schema = {'name': str, 'count': int}
        >>> config = {'name': 'test', 'count': 5}
        >>> validate_config_schema(config, schema)  # Passes
    """
    for key, expected_type in schema.items():
        if key not in config:
            raise ConfigError(f"Missing required config key: {key}")
        
        value = config[key]
        if not isinstance(value, expected_type):
            raise ConfigError(
                f"Config key '{key}' should be {expected_type.__name__}, "
                f"got {type(value).__name__}"
            )


# Export all functions
__all__ = [
    'ConfigError',
    'load_yaml',
    'load_sources_config',
    'save_yaml',
    'merge_configs',
    'validate_config_schema',
]
