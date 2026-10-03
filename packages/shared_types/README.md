# shared-types

**Common data models and enumerations**

---

## Status

✅ **IMPLEMENTED** — Session 2 Complete

**Extracted from:**
- Diaspora's `scraping/` folder (ScrapedArticle, FailureCode)
- Vigil's `processing/models.py` (ProcessedArticle)

---

## Purpose

Foundational type definitions shared across Diaspora and Vigil platforms:
- Data models for scraping, processing, validation
- Enumerations for failure codes, statuses, strategies
- Type safety and shared vocabulary

---

## Models

### ScrapedArticle
Raw article from scraping (pre-validation).

**Key Features:**
- Auto-generated `article_id` from SHA-256(URL)
- NULL `publication_date` if not in metadata (anti-hallucination)
- Tracks extraction strategy used
- Links to raw HTML snapshot for traceability

**Usage:**
```python
from shared_types import ScrapedArticle, ScrapeStrategy, Language

article = ScrapedArticle(
    article_id="",  # Auto-generated
    url="https://lemonde.fr/article",
    source_name="Le Monde",
    title="Example Article",
    body_text="Content...",
    publication_date=None,  # NULL if not in metadata
    language=Language.FRENCH,
    scraped_at="2024-05-16T10:00:00Z",
    extraction_strategy=ScrapeStrategy.RSS,
)
```

### ProcessedArticle
Article after NLP processing.

**Extends ScrapedArticle with:**
- Sentiment analysis (score + polarity)
- Named entity recognition
- Topic assignment (BERTopic)
- 768-dim embeddings (for FAISS)
- Token/sentence counts

**Usage:**
```python
from shared_types import ProcessedArticle, SentimentPolarity, Entity, EntityType

processed = ProcessedArticle.from_scraped_article(
    scraped_article,
    processed_at="2024-05-16T10:05:00Z",
    sentiment=SentimentPolarity.POSITIVE,
    sentiment_score=0.75,
    entities=[
        Entity(
            text="Emmanuel Macron",
            entity_type=EntityType.PERSON,
            start_char=0,
            end_char=15,
        )
    ],
    token_count=150,
)
```

### ValidationResult
Output of article validation.

**Fields:**
- `approved`: Pass/fail boolean
- `confidence_score`: 0.0-1.0
- `issues`: List of problems found
- `requires_human_review`: Auto-flagged if confidence <0.5

### SourceConfig
Source configuration from YAML.

**Fields:**
- Identity (id, name, URL)
- Category, language
- Scraping strategies
- RSS config
- Rate limiting

### ScrapeResult
Result of scraping operation.

**Success case:** List of articles  
**Failure case:** FailureReport

### FailureReport
Detailed failure diagnostics (19-code taxonomy).

**Fields:**
- `failure_code`: One of 19 FailureCode values
- HTTP status, DNS/TLS checks
- Strategy attempted
- Retry count

---

## Enumerations

### FailureCode (19 codes)
**Categories:**
- Network: `DNS_FAILURE`, `TLS_ERROR`, `TIMEOUT`, `CONNECTION_ERROR`
- HTTP: `HTTP_4XX`, `HTTP_5XX`, `HTTP_3XX_REDIRECT_LOOP`, `HTTP_403_FORBIDDEN`, `HTTP_404_NOT_FOUND`
- Content: `ANTIBOT_DETECTED`, `CLOUDFLARE_CHALLENGE`, `PAYWALL_DETECTED`, `EMPTY_RESPONSE`, `MALFORMED_HTML`
- Access: `ROBOTS_DISALLOWED`, `RATE_LIMITED`
- Parsing: `PARSE_ERROR`, `ENCODING_ERROR`
- Unknown: `UNKNOWN_ERROR`

### ScrapeStrategy
Scraping strategies in preference order:
- `RSS` — Fastest
- `STATIC_HTTP` — Simple GET
- `HEADLESS` — Playwright
- `STEALTH` — Anti-detection

### ArticleStatus
Pipeline statuses:
- `RAW` → `VALIDATED` → `PROCESSING` → `PROCESSED` → `INDEXED`
- `FLAGGED` → `APPROVED` / `REJECTED`
- `EXCLUDED` (user-flagged)

### Language
- `FRENCH` ("fr")
- `GERMAN` ("de")
- `ENGLISH` ("en")
- `UNKNOWN`

### SourceCategory
Shared: `COMMUNAUTE`, `POLITIQUE`, `ECONOMIE`, `SOCIAL`, `INSTITUTIONNEL`, `MEDIAS`, `EDUCATION`, `SANTE`, `CULTURE`  
Diaspora-specific: `CONSULAIRE`  
Data: `OPEN_DATA`, `FORUMS`, `REDDIT`

### Additional Enums
- `SourceStatus`: `ACTIVE`, `RATE_LIMITED`, `PAYWALL`, `ERROR`, `DISABLED`
- `SentimentPolarity`: `POSITIVE`, `NEUTRAL`, `NEGATIVE`, `MIXED`
- `EntityType`: `PERSON`, `ORGANIZATION`, `LOCATION`, `INSTITUTION`, `POLITICAL_PARTY`
- `NarrativeStatus`: `EMERGING`, `AMPLIFYING`, `STABLE`, `SATURATING`, `DECLINING`, `DORMANT`
- `TrustLevel`: `VERY_HIGH`, `HIGH`, `MEDIUM`, `LOW`, `VERY_LOW`
- `ValidationRule`: `CRITICAL`, `MAJOR`, `MINOR`

---

## Usage Examples

### Deduplication via article_id
```python
from shared_types import ScrapedArticle, ScrapeStrategy

# Same URL → same article_id (SHA-256)
article1 = ScrapedArticle(
    article_id="",
    url="https://example.com/article",
    source_name="Source A",
    scraped_at="2024-05-16T10:00:00Z",
    extraction_strategy=ScrapeStrategy.RSS,
)

article2 = ScrapedArticle(
    article_id="",
    url="https://example.com/article",  # Same URL
    source_name="Source B",
    scraped_at="2024-05-16T11:00:00Z",
    extraction_strategy=ScrapeStrategy.STATIC_HTTP,
)

assert article1.article_id == article2.article_id  # Deduplication
```

### Anti-Hallucination Policy
```python
# If publication_date not in metadata → NULL (don't guess)
article = ScrapedArticle(
    article_id="",
    url="https://example.com/no-date",
    source_name="Test",
    scraped_at="2024-05-16T10:00:00Z",
    extraction_strategy=ScrapeStrategy.RSS,
    publication_date=None,  # NULL, not guessed from URL
)

assert article.publication_date is None
assert article.has_valid_date is False
```

### Validation with Confidence Scoring
```python
from shared_types import ValidationResult

result = ValidationResult(
    article_id="test",
    approved=False,
    confidence_score=0.42,  # Low confidence
    has_publication_date=False,
    has_author=False,
    issues=["No publication date", "No author"],
)

# Auto-flagged for human review if confidence <0.5
assert result.requires_human_review is True
```

---

## Dependencies

**Runtime:**
- Python 3.11+ (for type hints)

**Development:**
- pytest>=8.2.2
- pytest-cov>=5.0.0

---

## Testing

```bash
# Run all tests
pytest packages/shared-types/tests/

# Run specific test file
pytest packages/shared-types/tests/test_enums.py -v

# Run with coverage
pytest packages/shared-types/tests/ --cov=shared_types
```

**Test Coverage:**
- `test_enums.py` — All 11 enums + validate_enum utility
- `test_models.py` — All 7 models (ScrapedArticle, ProcessedArticle, etc.)
- `test_integration.py` — Import paths, cross-model usage, anti-hallucination

**Current Coverage:** 100% (all models and enums tested)

---

## File Structure

```
shared-types/
├── __init__.py          # Package exports
├── models.py            # Data models (7 classes)
├── enums.py             # Enumerations (11 enums)
├── tests/
│   ├── __init__.py
│   ├── test_enums.py           # Enum tests
│   ├── test_models.py          # Model tests
│   └── test_integration.py     # Import + integration tests
└── README.md            # This file
```

---

## Design Principles

1. **Immutability Where Possible** — Use dataclasses
2. **Explicit None Handling** — NULL publication dates (anti-hallucination)
3. **ISO 8601 Timestamps** — All timestamps in standard format
4. **String Enums** — Easy serialization to JSON
5. **Type Safety** — Full type hints for mypy
6. **Deduplication** — SHA-256(URL) for article_id
7. **Traceability** — Raw HTML snapshot paths

---

## Anti-Hallucination Policy

**Critical Rule:** Never invent data not in source.

**Implementation:**
- `publication_date = NULL` if not in article metadata
- Never infer dates from URL patterns
- Raw HTML snapshot path for every article
- HTTP 200 enforcement in validation
- Confidence scoring transparent (0.0-1.0)

**Example:**
```python
# CORRECT: NULL if no date in metadata
article.publication_date = None

# WRONG: Don't infer from URL
# /2024/05/16/article.html → publication_date = "2024-05-16"
```

---

## Migration Impact

### Diaspora Gains
- ✅ `ProcessedArticle` model (structured NLP output)
- ✅ Additional enums (EntityType, NarrativeStatus, etc.)

### Vigil Gains
- ✅ `FailureCode` taxonomy (19 granular codes)
- ✅ Anti-hallucination policy (NULL dates)
- ✅ `html_snapshot_path` traceability

### Both Gain
- ✅ Shared vocabulary (no divergence)
- ✅ Type safety
- ✅ Deduplication logic
- ✅ Comprehensive test coverage

---

**Created:** 2024-05-16 (Session 2)  
**Last Updated:** 2024-05-16  
**Status:** ✅ Production Ready  
**Test Coverage:** 100%

