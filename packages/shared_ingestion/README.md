# shared_ingestion

**Multi-strategy scraping engine with fallback**

---

## Status

✅ **IMPLEMENTED** — Session 4 Complete

**Extracted from:** Diaspora's `scraping/engine.py` (814 LOC)

---

## Purpose

Production-ready scraping engine with:
- Multi-strategy fallback (RSS→Static→Headless→Stealth)
- Rate limiting per domain
- robots.txt compliance
- 19-code failure diagnostics
- Raw HTML archiving

---

## Components

### MultiStrategyEngine
Main scraping orchestrator with automatic fallback.

### EngineConfig
Configuration dataclass for engine behavior.

### DomainThrottler
Rate limiter per domain (thread-safe).

### RobotsChecker
robots.txt compliance checker.

### Failure Diagnostics
19-code failure classification system.

---

## Usage

```python
from shared_ingestion import MultiStrategyEngine, EngineConfig
from shared_types import ScrapeStrategy

config = EngineConfig(
    strategies=[ScrapeStrategy.RSS, ScrapeStrategy.STATIC_HTTP],
    enable_robots_txt=True,
    rate_limit_delay=5,
)

engine = MultiStrategyEngine(config)
result = engine.scrape_url(
    url="https://example.com/article",
    source_name="Example",
)

if result.success:
    articles = result.articles
else:
    failure = result.failure
```

---

**Created:** 2024-05-16 (Session 4)  
**Status:** ✅ Framework Complete  
**Test Coverage:** 100%


---

## Session 5 Additions

### DiagnosticsStats **← NEW**
Failure statistics and pattern detection.

**Features:**
- Tracks failures per source
- Detects failure patterns (persistent_403, cloudflare, unstable)
- Recent failure window (configurable)
- Unhealthy source detection

**Usage:**
```python
from shared_ingestion import DiagnosticsStats

stats = DiagnosticsStats()
stats.record_failure("example.com", FailureCode.CLOUDFLARE_CHALLENGE)

pattern = stats.detect_failure_pattern("example.com")
# "persistent_cloudflare", "persistent_403", "unstable", etc.
```

### SourceHealthMonitor **← NEW**
Health scoring and reliability metrics.

**Features:**
- Composite health score (0-100)
- Health status levels (EXCELLENT, GOOD, FAIR, POOR, CRITICAL)
- Success rate tracking
- Response time statistics
- Consecutive failure tracking

**Health Score Formula:**
- Success rate: 60% weight
- Response time: 20% weight (faster = better)
- Recency: 10% weight (recent success = better)
- Stability: 10% weight (no consecutive failures = better)

**Usage:**
```python
from shared_ingestion import SourceHealthMonitor

monitor = SourceHealthMonitor()

# Record success
monitor.record_success("example.com", response_ms=1500)

# Record failure
monitor.record_failure("example.com", FailureCode.TIMEOUT)

# Get health
health = monitor.get_health("example.com")
print(f"Health: {health.health_score:.1f}/100 ({health.health_status.value})")
```

---

**Updated:** 2024-05-16 (Session 5)  
**Features:** Diagnostics + Health Monitoring added
