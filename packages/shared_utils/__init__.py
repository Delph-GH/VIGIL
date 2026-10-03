"""
shared_utils

Common utility functions for text, dates, and URLs.

This package provides utilities used across:
- Diaspora Platform (French expats in Germany)
- Vigil Platform (French national politics)

Usage:
    from shared_utils import clean_text, parse_flexible_date, normalize_url
    from shared_utils import hash_url  # For article_id generation
"""

from .text_cleaner import (
    clean_html,
    normalize_unicode,
    remove_extra_whitespace,
    remove_special_chars,
    truncate_text,
    extract_sentences,
    clean_text,
)

from .date_parser import (
    parse_iso8601,
    parse_flexible_date,
    to_iso8601,
    get_current_timestamp,
    parse_date_from_url,
    is_valid_date,
    format_relative_date,
)

from .url_normalizer import (
    normalize_url,
    remove_tracking_params,
    hash_url,
    extract_domain,
    is_valid_url,
    join_url_parts,
    get_url_path,
)

__version__ = "0.1.0"

__all__ = [
    # Text utilities
    "clean_html",
    "normalize_unicode",
    "remove_extra_whitespace",
    "remove_special_chars",
    "truncate_text",
    "extract_sentences",
    "clean_text",
    
    # Date utilities
    "parse_iso8601",
    "parse_flexible_date",
    "to_iso8601",
    "get_current_timestamp",
    "parse_date_from_url",
    "is_valid_date",
    "format_relative_date",
    
    # URL utilities
    "normalize_url",
    "remove_tracking_params",
    "hash_url",
    "extract_domain",
    "is_valid_url",
    "join_url_parts",
    "get_url_path",
]
