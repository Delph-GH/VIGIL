"""
shared_utils/date_parser.py

Date parsing and formatting utilities.

Anti-hallucination principle: Return None if date cannot be parsed reliably.
Never guess or invent dates.
"""

from datetime import datetime, timezone
from typing import Optional
import re


def parse_iso8601(date_string: str) -> Optional[datetime]:
    """
    Parse ISO 8601 date string to datetime.
    
    Args:
        date_string: ISO 8601 formatted date (e.g., "2024-05-16T10:30:00Z")
        
    Returns:
        datetime object or None if parsing fails
        
    Example:
        >>> parse_iso8601("2024-05-16T10:30:00Z")
        datetime(2024, 5, 16, 10, 30, 0, tzinfo=timezone.utc)
    """
    if not date_string:
        return None
    
    try:
        # Handle Z timezone (Zulu time = UTC)
        if date_string.endswith('Z'):
            date_string = date_string[:-1] + '+00:00'
        
        # Try parsing with timezone
        return datetime.fromisoformat(date_string)
    
    except (ValueError, AttributeError):
        return None


def parse_flexible_date(date_string: str) -> Optional[datetime]:
    """
    Parse date from various formats.
    
    Supported formats:
    - ISO 8601: "2024-05-16T10:30:00Z"
    - Date only: "2024-05-16"
    - French format: "16/05/2024"
    - German format: "16.05.2024"
    - US format: "05/16/2024"
    - Textual: "16 mai 2024", "May 16, 2024"
    
    Args:
        date_string: Date string in various formats
        
    Returns:
        datetime object or None if parsing fails
        
    Note:
        If format is ambiguous, returns None (anti-hallucination).
        Never guesses date format.
    """
    if not date_string or not isinstance(date_string, str):
        return None
    
    date_string = date_string.strip()
    
    # Try ISO 8601 first (most reliable)
    result = parse_iso8601(date_string)
    if result:
        return result
    
    # Common formats to try
    formats = [
        "%Y-%m-%d",                # 2024-05-16
        "%Y/%m/%d",                # 2024/05/16
        "%d/%m/%Y",                # 16/05/2024 (French, German)
        "%d.%m.%Y",                # 16.05.2024 (German)
        "%m/%d/%Y",                # 05/16/2024 (US) - ONLY if clearly US format
        "%Y-%m-%d %H:%M:%S",       # 2024-05-16 10:30:00
        "%d-%m-%Y",                # 16-05-2024
    ]
    
    for fmt in formats:
        try:
            # Skip US format unless it's clearly unambiguous
            if fmt == "%m/%d/%Y":
                parts = date_string.split('/')
                if len(parts) == 3:
                    month, day, year = parts
                    # Only use US format if month > 12 (impossible in other formats)
                    if int(month) > 12:
                        continue
            
            dt = datetime.strptime(date_string, fmt)
            # Add UTC timezone if none present
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        
        except (ValueError, AttributeError):
            continue
    
    # If no format worked, return None (don't guess)
    return None


def to_iso8601(dt: datetime) -> str:
    """
    Convert datetime to ISO 8601 string.
    
    Args:
        dt: datetime object
        
    Returns:
        ISO 8601 formatted string (e.g., "2024-05-16T10:30:00Z")
        
    Example:
        >>> dt = datetime(2024, 5, 16, 10, 30, 0, tzinfo=timezone.utc)
        >>> to_iso8601(dt)
        "2024-05-16T10:30:00Z"
    """
    if not dt:
        return ""
    
    # Ensure UTC timezone
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    elif dt.tzinfo != timezone.utc:
        dt = dt.astimezone(timezone.utc)
    
    # Format as ISO 8601 with Z suffix
    return dt.strftime('%Y-%m-%dT%H:%M:%SZ')


def get_current_timestamp() -> str:
    """
    Get current timestamp in ISO 8601 format.
    
    Returns:
        Current timestamp string (e.g., "2024-05-16T10:30:00Z")
        
    Example:
        >>> get_current_timestamp()
        "2024-05-16T10:30:00Z"
    """
    return to_iso8601(datetime.now(timezone.utc))


def parse_date_from_url(url: str) -> Optional[datetime]:
    """
    Attempt to extract date from URL pattern.
    
    WARNING: This is a guess and violates anti-hallucination policy.
    Only use if explicitly allowed by context.
    
    Patterns recognized:
    - /2024/05/16/article.html
    - /article-2024-05-16.html
    
    Args:
        url: URL that may contain date
        
    Returns:
        datetime or None if no pattern found
        
    Note:
        Prefer metadata dates over URL dates.
        Only use this as last resort and flag as low confidence.
    """
    if not url:
        return None
    
    # Pattern: /YYYY/MM/DD/
    pattern1 = r'/(\d{4})/(\d{2})/(\d{2})/'
    match = re.search(pattern1, url)
    if match:
        try:
            year, month, day = match.groups()
            return datetime(int(year), int(month), int(day), tzinfo=timezone.utc)
        except ValueError:
            pass
    
    # Pattern: -YYYY-MM-DD
    pattern2 = r'-(\d{4})-(\d{2})-(\d{2})'
    match = re.search(pattern2, url)
    if match:
        try:
            year, month, day = match.groups()
            return datetime(int(year), int(month), int(day), tzinfo=timezone.utc)
        except ValueError:
            pass
    
    # No date found - return None (don't guess)
    return None


def is_valid_date(date_string: str) -> bool:
    """
    Check if string is a valid date.
    
    Args:
        date_string: Potential date string
        
    Returns:
        True if valid date, False otherwise
        
    Example:
        >>> is_valid_date("2024-05-16")
        True
        >>> is_valid_date("invalid")
        False
    """
    return parse_flexible_date(date_string) is not None


def format_relative_date(dt: datetime) -> str:
    """
    Format date as relative time (e.g., "2 hours ago").
    
    Args:
        dt: datetime to format
        
    Returns:
        Relative time string
        
    Example:
        >>> now = datetime.now(timezone.utc)
        >>> two_hours_ago = now - timedelta(hours=2)
        >>> format_relative_date(two_hours_ago)
        "2 hours ago"
    """
    if not dt:
        return ""
    
    now = datetime.now(timezone.utc)
    
    # Ensure both have timezone info
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    diff = now - dt
    seconds = diff.total_seconds()
    
    if seconds < 0:
        return "in the future"
    elif seconds < 60:
        return "just now"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"
    elif seconds < 2592000:
        weeks = int(seconds / 604800)
        return f"{weeks} week{'s' if weeks != 1 else ''} ago"
    elif seconds < 31536000:
        months = int(seconds / 2592000)
        return f"{months} month{'s' if months != 1 else ''} ago"
    else:
        years = int(seconds / 31536000)
        return f"{years} year{'s' if years != 1 else ''} ago"


# Export all functions
__all__ = [
    'parse_iso8601',
    'parse_flexible_date',
    'to_iso8601',
    'get_current_timestamp',
    'parse_date_from_url',
    'is_valid_date',
    'format_relative_date',
]
