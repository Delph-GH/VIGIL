"""
shared_utils/text_cleaner.py

Text cleaning and normalization utilities.

Extracted from:
- Vigil's processing/text_cleaner.py
- Diaspora's utils/helpers.py
"""

import re
import html
import unicodedata
from typing import Optional


def clean_html(text: str) -> str:
    """
    Remove HTML tags and entities from text.
    
    Args:
        text: Raw HTML text
        
    Returns:
        Clean text with HTML removed
        
    Example:
        >>> clean_html("<p>Hello <b>world</b>!</p>")
        "Hello world!"
    """
    if not text:
        return ""
    
    # Decode HTML entities first
    text = html.unescape(text)
    
    # Remove script and style tags with their content
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove HTML comments
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
    
    # Remove all HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    return text


def normalize_unicode(text: str, form: str = 'NFKC') -> str:
    """
    Normalize Unicode text.
    
    Args:
        text: Input text with Unicode characters
        form: Normalization form (NFC, NFD, NFKC, NFKD)
              NFKC is recommended for most use cases
        
    Returns:
        Normalized Unicode text
        
    Example:
        >>> normalize_unicode("café")  # é as single char
        "café"
    """
    if not text:
        return ""
    
    return unicodedata.normalize(form, text)


def remove_extra_whitespace(text: str) -> str:
    """
    Remove extra whitespace, tabs, newlines.
    
    Args:
        text: Text with irregular whitespace
        
    Returns:
        Text with normalized whitespace
        
    Example:
        >>> remove_extra_whitespace("Hello   \\n  world")
        "Hello world"
    """
    if not text:
        return ""
    
    # Replace tabs and newlines with spaces
    text = text.replace('\t', ' ').replace('\n', ' ').replace('\r', ' ')
    
    # Replace multiple spaces with single space
    text = re.sub(r'\s+', ' ', text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text


def remove_special_chars(text: str, keep_punctuation: bool = True) -> str:
    """
    Remove special characters, keeping only alphanumeric and optionally punctuation.
    
    Args:
        text: Input text
        keep_punctuation: If True, keep common punctuation (.,!?;:)
        
    Returns:
        Cleaned text
        
    Example:
        >>> remove_special_chars("Hello™ world®!", keep_punctuation=True)
        "Hello world!"
    """
    if not text:
        return ""
    
    if keep_punctuation:
        # Keep alphanumeric, spaces, and common punctuation
        pattern = r'[^\w\s.,!?;:\-\'"()]'
    else:
        # Keep only alphanumeric and spaces
        pattern = r'[^\w\s]'
    
    text = re.sub(pattern, '', text)
    text = remove_extra_whitespace(text)
    
    return text


def truncate_text(text: str, max_length: int = 500, suffix: str = "...") -> str:
    """
    Truncate text to maximum length, adding suffix if truncated.
    
    Args:
        text: Input text
        max_length: Maximum length (including suffix)
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated text
        
    Example:
        >>> truncate_text("A very long text...", max_length=10)
        "A very..."
    """
    if not text or len(text) <= max_length:
        return text
    
    truncate_at = max_length - len(suffix)
    if truncate_at <= 0:
        return text[:max_length]
    
    return text[:truncate_at] + suffix


def extract_sentences(text: str, max_sentences: Optional[int] = None) -> list[str]:
    """
    Extract sentences from text.
    
    Args:
        text: Input text
        max_sentences: Maximum number of sentences to return
        
    Returns:
        List of sentences
        
    Example:
        >>> extract_sentences("Hello world. How are you?")
        ["Hello world.", "How are you?"]
    """
    if not text:
        return []
    
    # Simple sentence splitting (not perfect but good enough)
    # Split on . ! ? followed by space or end of string
    sentences = re.split(r'([.!?]+(?:\s+|$))', text)
    
    # Recombine sentences with their punctuation
    result = []
    for i in range(0, len(sentences) - 1, 2):
        sentence = (sentences[i] + sentences[i + 1]).strip()
        if sentence:
            result.append(sentence)
    
    # Handle last part if no punctuation at end
    if len(sentences) % 2 == 1 and sentences[-1].strip():
        result.append(sentences[-1].strip())
    
    if max_sentences:
        result = result[:max_sentences]
    
    return result


def clean_text(
    text: str,
    remove_html: bool = True,
    normalize: bool = True,
    remove_special: bool = False,
    keep_punctuation: bool = True,
) -> str:
    """
    Comprehensive text cleaning pipeline.
    
    Args:
        text: Input text
        remove_html: Remove HTML tags
        normalize: Normalize Unicode
        remove_special: Remove special characters
        keep_punctuation: Keep punctuation (only if remove_special=True)
        
    Returns:
        Cleaned text
        
    Example:
        >>> clean_text("<p>Hello™ world</p>", remove_html=True, remove_special=True)
        "Hello world"
    """
    if not text:
        return ""
    
    # Step 1: Remove HTML if requested
    if remove_html:
        text = clean_html(text)
    
    # Step 2: Normalize Unicode if requested
    if normalize:
        text = normalize_unicode(text)
    
    # Step 3: Remove special chars if requested
    if remove_special:
        text = remove_special_chars(text, keep_punctuation=keep_punctuation)
    
    # Step 4: Always clean up whitespace
    text = remove_extra_whitespace(text)
    
    return text


# Export all functions
__all__ = [
    'clean_html',
    'normalize_unicode',
    'remove_extra_whitespace',
    'remove_special_chars',
    'truncate_text',
    'extract_sentences',
    'clean_text',
]
