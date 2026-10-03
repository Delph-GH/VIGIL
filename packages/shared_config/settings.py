"""
shared_config/settings.py

Application settings management with environment variable support.
"""

import os
from typing import Any, Optional
from pathlib import Path


class Settings:
    """
    Application settings with environment variable support.
    
    Usage:
        >>> settings = Settings()
        >>> db_path = settings.get('database.path', default='data/articles.db')
        >>> settings.set('database.path', 'custom/path.db')
    """
    
    def __init__(self):
        """Initialize empty settings."""
        self._data = {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get setting value.
        
        Supports dot notation for nested keys:
        - 'key' → self._data['key']
        - 'section.key' → self._data['section']['key']
        
        Args:
            key: Setting key (supports dot notation)
            default: Default value if key not found
            
        Returns:
            Setting value or default
            
        Example:
            >>> settings.get('database.path', default='/tmp/db.sqlite')
            "/tmp/db.sqlite"
        """
        # Try environment variable first (uppercase with underscores)
        env_key = key.upper().replace('.', '_')
        env_value = os.environ.get(env_key)
        if env_value is not None:
            return env_value
        
        # Navigate nested dict
        parts = key.split('.')
        current = self._data
        
        for part in parts:
            if not isinstance(current, dict) or part not in current:
                return default
            current = current[part]
        
        return current
    
    def set(self, key: str, value: Any) -> None:
        """
        Set setting value.
        
        Supports dot notation for nested keys.
        
        Args:
            key: Setting key (supports dot notation)
            value: Value to set
            
        Example:
            >>> settings.set('database.path', '/tmp/db.sqlite')
            >>> settings.set('scraping.rate_limit', 5)
        """
        parts = key.split('.')
        current = self._data
        
        # Navigate to parent, creating dicts as needed
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            elif not isinstance(current[part], dict):
                # Can't navigate further, overwrite
                current[part] = {}
            current = current[part]
        
        # Set final value
        current[parts[-1]] = value
    
    def get_int(self, key: str, default: int = 0) -> int:
        """
        Get setting as integer.
        
        Args:
            key: Setting key
            default: Default value
            
        Returns:
            Integer value
        """
        value = self.get(key, default)
        try:
            return int(value)
        except (ValueError, TypeError):
            return default
    
    def get_float(self, key: str, default: float = 0.0) -> float:
        """
        Get setting as float.
        
        Args:
            key: Setting key
            default: Default value
            
        Returns:
            Float value
        """
        value = self.get(key, default)
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
    
    def get_bool(self, key: str, default: bool = False) -> bool:
        """
        Get setting as boolean.
        
        Treats "true", "1", "yes", "on" as True (case-insensitive).
        
        Args:
            key: Setting key
            default: Default value
            
        Returns:
            Boolean value
        """
        value = self.get(key, default)
        
        if isinstance(value, bool):
            return value
        
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        
        return bool(value)
    
    def get_path(self, key: str, default: Optional[str] = None) -> Optional[Path]:
        """
        Get setting as Path object.
        
        Args:
            key: Setting key
            default: Default path string
            
        Returns:
            Path object or None
        """
        value = self.get(key, default)
        
        if value is None:
            return None
        
        return Path(value)
    
    def update(self, data: dict) -> None:
        """
        Update settings with dictionary.
        
        Args:
            data: Dictionary to merge into settings
            
        Example:
            >>> settings.update({'database': {'path': '/tmp/db.sqlite'}})
        """
        def deep_update(target, source):
            for key, value in source.items():
                if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                    deep_update(target[key], value)
                else:
                    target[key] = value
        
        deep_update(self._data, data)
    
    def to_dict(self) -> dict:
        """
        Export settings as dictionary.
        
        Returns:
            Settings dictionary
        """
        return self._data.copy()
    
    def clear(self) -> None:
        """Clear all settings."""
        self._data = {}


# Global settings instance
_settings = Settings()


def get_setting(key: str, default: Any = None) -> Any:
    """
    Get setting from global instance.
    
    Args:
        key: Setting key
        default: Default value
        
    Returns:
        Setting value
        
    Example:
        >>> from shared_config import get_setting
        >>> db_path = get_setting('database.path', default='data/articles.db')
    """
    return _settings.get(key, default)


def set_setting(key: str, value: Any) -> None:
    """
    Set setting in global instance.
    
    Args:
        key: Setting key
        value: Value to set
        
    Example:
        >>> from shared_config import set_setting
        >>> set_setting('database.path', '/tmp/db.sqlite')
    """
    _settings.set(key, value)


def load_settings_from_dict(data: dict) -> None:
    """
    Load settings from dictionary.
    
    Args:
        data: Settings dictionary
        
    Example:
        >>> from shared_config import load_settings_from_dict
        >>> load_settings_from_dict({'database': {'path': '/tmp/db.sqlite'}})
    """
    _settings.update(data)


def get_settings() -> Settings:
    """
    Get global settings instance.
    
    Returns:
        Global Settings object
    """
    return _settings


# Export all functions and classes
__all__ = [
    'Settings',
    'get_setting',
    'set_setting',
    'load_settings_from_dict',
    'get_settings',
]
