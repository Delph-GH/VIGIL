"""
shared_utils/url_normalizer.py

URL normalization and hash generation utilities.

Used for deduplication and consistent URL handling.
"""

import hashlib
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
from typing import Optional


def normalize_url(url: str, remove_query: bool = False, remove_fragment: bool = True) -> str:
    """
    Normalize URL for consistent handling.
    
    Normalization steps:
    1. Parse URL components
    2. Lowercase scheme and domain
    3. Remove default ports (80 for http, 443 for https)
    4. Remove trailing slash from path
    5. Sort query parameters
    6. Optionally remove query and fragment
    
    Args:
        url: Raw URL
        remove_query: If True, remove query parameters (e.g., ?utm_source=...)
        remove_fragment: If True, remove fragment (e.g., #section)
        
    Returns:
        Normalized URL
        
    Example:
        >>> normalize_url("HTTPS://Example.com:443/path/?b=2&a=1#frag")
        "https://example.com/path?a=1&b=2"
    """
    if not url:
        return ""
    
    # Parse URL
    parsed = urlparse(url)
    
    # Normalize scheme and domain to lowercase
    scheme = parsed.scheme.lower()
    netloc = parsed.hostname.lower() if parsed.hostname else ""
    
    # Add port if non-default
    if parsed.port:
        default_ports = {'http': 80, 'https': 443}
        if parsed.port != default_ports.get(scheme):
            netloc += f":{parsed.port}"
    
    # Add username:password if present
    if parsed.username:
        auth = parsed.username
        if parsed.password:
            auth += f":{parsed.password}"
        netloc = f"{auth}@{netloc}"
    
    # Normalize path (remove trailing slash unless it's root)
    path = parsed.path
    if path.endswith('/') and len(path) > 1:
        path = path[:-1]
    
    # Handle query parameters
    query = ""
    if not remove_query and parsed.query:
        # Parse, sort, and rebuild query
        params = parse_qs(parsed.query, keep_blank_values=True)
        # Sort parameters for consistency
        sorted_params = sorted(params.items())
        # Rebuild query string
        query_parts = []
        for key, values in sorted_params:
            for value in values:
                query_parts.append(f"{key}={value}")
        query = "&".join(query_parts)
    
    # Handle fragment
    fragment = "" if remove_fragment else parsed.fragment
    
    # Rebuild URL
    normalized = urlunparse((scheme, netloc, path, '', query, fragment))
    
    return normalized


def remove_tracking_params(url: str) -> str:
    """
    Remove common tracking parameters from URL.
    
    Removes parameters like:
    - utm_source, utm_medium, utm_campaign, utm_content, utm_term
    - fbclid (Facebook)
    - gclid (Google)
    - ref, source
    
    Args:
        url: URL with tracking parameters
        
    Returns:
        URL without tracking parameters
        
    Example:
        >>> remove_tracking_params("https://example.com/article?utm_source=twitter&id=123")
        "https://example.com/article?id=123"
    """
    if not url:
        return ""
    
    # Common tracking parameters
    tracking_params = {
        'utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term',
        'fbclid', 'gclid', 'msclkid', 
        'ref', 'source', 'campaign',
        '_ga', '_gac', '_gl',
    }
    
    parsed = urlparse(url)
    
    if not parsed.query:
        return url
    
    # Parse query parameters
    params = parse_qs(parsed.query, keep_blank_values=True)
    
    # Remove tracking parameters
    filtered_params = {
        key: values
        for key, values in params.items()
        if key.lower() not in tracking_params
    }
    
    # Rebuild query string
    query_parts = []
    for key, values in sorted(filtered_params.items()):
        for value in values:
            query_parts.append(f"{key}={value}")
    query = "&".join(query_parts)
    
    # Rebuild URL
    cleaned = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        '',
        query,
        parsed.fragment
    ))
    
    return cleaned


def hash_url(url: str, algorithm: str = 'sha256') -> str:
    """
    Generate hash of URL for deduplication.
    
    Used for article_id generation in ScrapedArticle.
    
    Args:
        url: URL to hash
        algorithm: Hash algorithm ('md5', 'sha256', 'sha512')
        
    Returns:
        Hex digest of URL hash
        
    Example:
        >>> hash_url("https://example.com/article")
        "a1b2c3d4..."  # 64-char SHA-256 hex
    """
    if not url:
        return ""
    
    # Normalize URL first for consistent hashing
    normalized = normalize_url(url, remove_query=False, remove_fragment=True)
    
    # Choose hash algorithm
    if algorithm == 'md5':
        hasher = hashlib.md5()
    elif algorithm == 'sha512':
        hasher = hashlib.sha512()
    else:  # default sha256
        hasher = hashlib.sha256()
    
    # Hash normalized URL
    hasher.update(normalized.encode('utf-8'))
    
    return hasher.hexdigest()


def extract_domain(url: str) -> Optional[str]:
    """
    Extract domain from URL.
    
    Args:
        url: Full URL
        
    Returns:
        Domain (e.g., "example.com") or None if invalid
        
    Example:
        >>> extract_domain("https://www.example.com/path")
        "example.com"
    """
    if not url:
        return None
    
    try:
        parsed = urlparse(url)
        domain = parsed.hostname
        
        if domain:
            # Remove www. prefix if present
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain.lower()
        
        return None
    
    except (ValueError, AttributeError):
        return None


def is_valid_url(url: str) -> bool:
    """
    Check if string is a valid URL.
    
    Args:
        url: Potential URL string
        
    Returns:
        True if valid URL, False otherwise
        
    Example:
        >>> is_valid_url("https://example.com")
        True
        >>> is_valid_url("not a url")
        False
    """
    if not url or not isinstance(url, str):
        return False
    
    try:
        parsed = urlparse(url)
        # Must have scheme and netloc
        return bool(parsed.scheme and parsed.netloc)
    
    except (ValueError, AttributeError):
        return False


def join_url_parts(base: str, *parts: str) -> str:
    """
    Join URL parts safely.
    
    Args:
        base: Base URL
        *parts: Additional path parts
        
    Returns:
        Complete URL
        
    Example:
        >>> join_url_parts("https://example.com", "api", "v1", "users")
        "https://example.com/api/v1/users"
    """
    if not base:
        return ""
    
    # Ensure base doesn't end with /
    url = base.rstrip('/')
    
    # Add each part
    for part in parts:
        if part:
            # Remove leading/trailing slashes from part
            part = part.strip('/')
            url += f"/{part}"
    
    return url


def get_url_path(url: str) -> str:
    """
    Extract path from URL.
    
    Args:
        url: Full URL
        
    Returns:
        URL path (e.g., "/path/to/article")
        
    Example:
        >>> get_url_path("https://example.com/path/to/article?id=123")
        "/path/to/article"
    """
    if not url:
        return ""
    
    try:
        parsed = urlparse(url)
        return parsed.path
    except (ValueError, AttributeError):
        return ""


# Export all functions
__all__ = [
    'normalize_url',
    'remove_tracking_params',
    'hash_url',
    'extract_domain',
    'is_valid_url',
    'join_url_parts',
    'get_url_path',
]
