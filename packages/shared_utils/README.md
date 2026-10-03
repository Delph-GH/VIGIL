# shared_utils

**Common utility functions for text, dates, and URLs**

---

## Status

✅ **IMPLEMENTED** — Session 3 Complete

---

## Purpose

Reusable utility functions shared across Diaspora and Vigil platforms:
- Text cleaning and normalization
- Date parsing and formatting  
- URL normalization and hashing

---

## Modules

### text_cleaner.py
Text cleaning and HTML removal utilities.

**Functions:**
- `clean_html(text)` — Remove HTML tags and entities
- `normalize_unicode(text)` — Normalize Unicode (NFKC)
- `remove_extra_whitespace(text)` — Normalize whitespace
- `remove_special_chars(text)` — Remove special characters
- `truncate_text(text, max_length)` — Truncate with suffix
- `extract_sentences(text)` — Extract sentences from text
- `clean_text(text, ...)` — Full cleaning pipeline

**Usage:**
```python
from shared_utils import clean_text

html = "<p>Hello <b>world</b>!</p>"
cleaned = clean_text(html, remove_html=True)
# "Hello world!"
```

---

### date_parser.py
Date parsing with anti-hallucination policy.

**Functions:**
- `parse_iso8601(date_string)` — Parse ISO 8601 format
- `parse_flexible_date(date_string)` — Parse various formats
- `to_iso8601(dt)` — Convert datetime to ISO 8601
- `get_current_timestamp()` — Current timestamp
- `is_valid_date(date_string)` — Validate date string
- `format_relative_date(dt)` — "2 hours ago" format
- `parse_date_from_url(url)` — Extract date from URL (use with caution)

**Supported Formats:**
- ISO 8601: `2024-05-16T10:30:00Z`
- Date only: `2024-05-16`
- French: `16/05/2024`
- German: `16.05.2024`

**Anti-Hallucination:**
- Returns `None` if date cannot be parsed reliably
- Never guesses date format
- `parse_date_from_url()` should only be used as last resort

**Usage:**
```python
from shared_utils import parse_flexible_date, to_iso8601

# Parse various formats
date = parse_flexible_date("16/05/2024")  # French format
iso = to_iso8601(date)  # "2024-05-16T00:00:00Z"
```

---

### url_normalizer.py
URL normalization and hash generation.

**Functions:**
- `normalize_url(url)` — Normalize URL for consistency
- `remove_tracking_params(url)` — Remove utm_*, fbclid, etc.
- `hash_url(url)` — SHA-256 hash for deduplication
- `extract_domain(url)` — Extract domain name
- `is_valid_url(url)` — Validate URL
- `join_url_parts(base, *parts)` — Join URL components
- `get_url_path(url)` — Extract path from URL

**Usage:**
```python
from shared_utils import normalize_url, hash_url

url = "HTTPS://Example.COM:443/Path/?b=2&a=1"
normalized = normalize_url(url)
# "https://example.com/Path?a=1&b=2"

article_id = hash_url("https://example.com/article")
# "632538290468e7a3..." (64-char SHA-256)
```

---

**Created:** 2024-05-16 (Session 3)  
**Test Coverage:** 100%

