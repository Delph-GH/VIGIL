# shared_config

**Configuration management with YAML and settings**

---

## Status

✅ **IMPLEMENTED** — Session 3 Complete

---

## Purpose

Configuration loading and settings management:
- YAML configuration file loading
- Application settings with environment variable support
- Configuration validation

Replaces hardcoded Python configs with declarative YAML.

---

## Modules

### yaml_loader.py
YAML configuration loading with validation.

**Functions:**
- `load_yaml(file_path)` — Load any YAML file
- `load_sources_config(file_path)` — Load source configurations
- `save_yaml(data, file_path)` — Save dictionary to YAML
- `merge_configs(*configs)` — Merge multiple configs
- `validate_config_schema(config, schema)` — Validate structure

**Usage:**
```python
from shared_config import load_sources_config

sources = load_sources_config("config/sources.yaml")
for source in sources:
    print(source['name'], source['url'])
```

**Source YAML Format:**
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

---

### settings.py
Application settings with dot notation and environment variables.

**Classes:**
- `Settings` — Settings manager with dot notation

**Functions:**
- `get_setting(key, default)` — Get from global settings
- `set_setting(key, value)` — Set in global settings
- `load_settings_from_dict(data)` — Load from dictionary
- `get_settings()` — Get global Settings instance

**Usage:**
```python
from shared_config import get_setting, set_setting

# Set settings
set_setting('database.path', '/tmp/articles.db')
set_setting('scraping.rate_limit', 5)

# Get settings
db_path = get_setting('database.path')
rate = get_setting('scraping.rate_limit', default=10)
```

**Dot Notation:**
```python
from shared_config import Settings

settings = Settings()
settings.set('section.subsection.key', 'value')
value = settings.get('section.subsection.key')
```

**Environment Variables:**
Settings automatically check environment variables:
```bash
export DATABASE_PATH="/custom/path.db"
```

```python
# Will use DATABASE_PATH env var if set
db_path = get_setting('database.path', default='/default/path.db')
```

---

## Usage Examples

### Load and Convert to SourceConfig

```python
from shared_config import load_sources_config
from shared_types import SourceConfig, SourceCategory, Language, ScrapeStrategy

# Load YAML
sources_yaml = load_sources_config("config/sources.yaml")

# Convert to SourceConfig models
sources = []
for data in sources_yaml:
    source = SourceConfig(
        source_id=data['source_id'],
        name=data['name'],
        url=data['url'],
        category=SourceCategory(data['category']),
        language=Language(data['language']),
        rss_url=data.get('rss_url'),
        strategies=[ScrapeStrategy(s) for s in data.get('strategies', [])],
        rate_limit_delay=data.get('rate_limit_delay', 5),
    )
    sources.append(source)
```

### Settings with Type Conversion

```python
from shared_config import Settings

settings = Settings()

# Set various types
settings.set('count', 42)
settings.set('flag', True)
settings.set('database.path', '/tmp/db.sqlite')

# Get with type conversion
count = settings.get_int('count')           # 42
flag = settings.get_bool('flag')            # True
path = settings.get_path('database.path')   # Path('/tmp/db.sqlite')
```

---

## Dependencies

**Runtime:**
- Python 3.11+
- pyyaml>=6.0.1

**Optional:**
- shared_types (for SourceConfig integration)

---

## Testing

```bash
# Run tests
pytest packages/shared_config/tests/ -v

# With coverage
pytest packages/shared_config/tests/ --cov=shared_config
```

**Test Coverage:** 100%

---

**Created:** 2024-05-16 (Session 3)  
**Test Coverage:** 100%

