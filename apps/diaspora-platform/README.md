# Diaspora Platform

**French Expatriate Political Intelligence (Bavaria & Baden-Württemberg)**

---

## Status

⬜ **NOT MIGRATED** — Placeholder created in Session 1

**Migration:** Phase 8 (Sessions 24-29)

---

## Overview

Diaspora Intelligence Hub monitors French expatriate discourse and political sentiment in southern Germany (Bavaria and Baden-Württemberg).

**Focus Areas:**
- Cross-border taxation
- Consular services
- Housing (Munich, Stuttgart)
- Bilingual education (French/German)
- Healthcare systems (Krankenkasse vs Sécu)
- Integration challenges

---

## Key Features

### Current (Pre-Migration)
- ✅ 98 sources (9 categories)
- ✅ Multi-strategy scraping (RSS→static→headless→stealth)
- ✅ 7 diaspora-specific personas
- ✅ 8 diaspora narratives
- ✅ 22 analytical views (HTML dashboard)
- ✅ 10 reality-check indicators
- ✅ Anti-hallucination validation

### Target (Post-Migration)
- ✅ All current features preserved
- ✅ **NEW:** Production NLP stack (spaCy, CamemBERT, BERTopic)
- ✅ **NEW:** FAISS semantic search
- ✅ **NEW:** 9 advanced analytics modules (from Vigil)
- ✅ **NEW:** Streamlit multi-page dashboard (31 views)
- ✅ **NEW:** Structured logging (JSON)
- ✅ **NEW:** APScheduler

---

## Personas (7)

1. **L'Expat Précaire** (18%) — Economic fragility, housing anxiety
2. **Le Cadre Transfrontalier** (22%) — Cross-border work, taxation
3. **Le Sceptique Institutionnel** (16%) — Distrust FR+DE institutions
4. **Le Progressiste Biculturel** (14%) — Ecological values, integration
5. **Le Conservateur Nostalgique** (12%) — French identity preservation
6. **Le Parent Tranquille** (11%) — Family stability, children's education
7. **L'Entrepreneur Optimiste** (7%) — Business opportunities

---

## Data Sources (98)

**Categories:**
- Communauté (12): Reddit, forums, expat blogs
- Politique (18): Assemblée, Sénat, Élysée
- Économie (15): INSEE, Banque de France
- Social (18): CAF, Pôle Emploi, Krankenkassen
- Institutionnel (11): Consulats, Ambassade
- Médias (16): Le Monde, SZ, BR24
- Éducation (5): Écoles françaises, AEFE
- Santé (4): RKI, AOK
- Culture (3): Alliance Française

---

## Technology Stack

**Current:**
- Python 3.11
- SQLite (110 KB)
- HTML dashboard (3,077 LOC)
- `schedule` library
- `requests` (sync HTTP)

**Target:**
- All shared packages from monorepo
- Streamlit dashboard
- APScheduler
- Async scraping (optional)

---

## Directory Structure

```
diaspora-platform/
├── diaspora_personas/       # 7 personas
├── diaspora_narratives/     # 8 narratives
├── diaspora_sources/        # 98-source YAML configs
├── diaspora_analytics/      # Cross-border, consular tracking
├── diaspora_dashboards/     # Streamlit (31 pages post-migration)
├── diaspora_config/         # Bavaria/BW settings
├── data/
│   ├── diaspora.db          # SQLite
│   ├── faiss_index.pkl      # FAISS (post-migration)
│   └── snapshots/           # Raw HTML
└── tests/
```

---

## Migration Impact

**Gains:**
- Production NLP (vs lexicon-only sentiment)
- FAISS semantic search (vs SQL LIKE)
- 9 advanced modules (Contradictions, Emotions, etc.)
- Streamlit (vs 3,077-line HTML monolith)
- Structured logging (vs text files)

**Preserves:**
- All 7 diaspora personas
- All 98 sources
- Multi-strategy scraping
- Anti-hallucination policy
- Reality anchoring (10 indicators)

**Changes:**
- Dashboard technology (HTML → Streamlit)
- Scheduler (schedule → APScheduler)
- Analytics (hardcoded → computed from corpus)

---

## Quick Start (Post-Migration)

```bash
cd apps/diaspora-platform

# Install dependencies (from root)
cd ../..
pip install -e .

# Download models
python -m spacy download fr_core_news_lg

# Run dashboard
cd apps/diaspora-platform
streamlit run diaspora_dashboards/app.py
```

---

## Documentation

- Architecture: `docs/ARCHITECTURE_DIASPORA.md`
- Scope: `docs/DIASPORA_SCOPE.md`
- Feature rules: `docs/FEATURE_RULES.md`
- Migration guide: `docs/MIGRATION_GUIDE.md`

---

**Created:** 2024-05-16 (Session 1)  
**Migration Status:** Not started  
**Target Completion:** Session 29 (Phase 8)
