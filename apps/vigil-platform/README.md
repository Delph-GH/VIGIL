# Vigil Platform

**French National Political Intelligence**

---

## Status

⬜ **NOT MIGRATED** — Placeholder created in Session 1

**Migration:** Phase 4-8 (Sessions 10-30)

---

## Overview

VIGIL·FR is a strategic political intelligence platform for French national politics, providing structural analysis of discourse, trust dynamics, narrative evolution, and psychographic segmentation.

**Coverage:** France métropolitaine (13 regions)

---

## Key Features

### Current (Pre-Migration)
- ✅ 30 French sources (national + regional)
- ✅ 9 national personas (60.5M French covered)
- ✅ Production NLP stack (spaCy, CamemBERT, BERTopic)
- ✅ FAISS semantic search
- ✅ 16 Streamlit dashboard pages
- ✅ 9 advanced analytics modules
- ✅ 30 institutions tracked
- ✅ YAML-driven configuration
- ✅ Async scraping (aiohttp)
- ✅ Structured logging (structlog)

### Target (Post-Migration)
- ✅ All current features preserved
- ✅ **NEW:** Multi-strategy scraping (from Diaspora)
- ✅ **NEW:** 19-code failure taxonomy
- ✅ **NEW:** Anti-hallucination validation
- ✅ **NEW:** Reliability scoring
- ✅ **NEW:** Raw HTML snapshot archiving
- ✅ **Wire:** 9 advanced modules to real data (currently demo)

---

## Personas (9)

Based on INSEE + CEVIPOF + CREDOC data:

1. **Ouvriers** (13.2M, 22%) — Economic insecurity, populist appeal
2. **Bourgeoisie diplômée** (9.6M, 16%) — Globalization winners
3. **Employés précaires** (9.0M, 15%) — Service sector instability
4. **Petits indépendants** (7.2M, 12%) — Small business owners
5. **Retraités modestes** (6.6M, 11%) — Pension anxiety
6. **Jeunes urbains** (6.0M, 10%) — Climate/social justice
7. **Classes moyennes provinciales** (5.4M, 9%) — Squeezed middle
8. **Cadres privés** (4.2M, 7%) — Corporate professionals
9. **Fonctionnaires** (3.6M, 6%) — Public sector workers

---

## Data Sources (30)

**Categories:**
- Presse nationale (10): Le Monde, Le Figaro, Libération, etc.
- Presse régionale (9): Ouest-France, Sud Ouest, etc.
- Institutionnel (3): Vie Publique, Assemblée, Sénat
- Open data (5): INSEE, data.gouv.fr, DARES, Banque de France
- Communautés (3): Reddit r/france (anonymized)

---

## Institutions Tracked (30)

- Exécutif (5): Président, Premier ministre, Gouvernement, etc.
- Juridique (2): Justice, Conseil Constitutionnel
- Régalien (3): Police, Armée, Pompiers
- Territorial (3): Maires, Conseils régionaux, départementaux
- Supranational (1): Institutions UE
- Société civile (3): Syndicats, ONG, Partis
- Médias (4): Presse nationale, audiovisuel, etc.
- Économique (3): Banques, Grandes entreprises, TPE/PME
- Social (4): Santé, Hôpitaux, Écoles, Universités
- Epistémique (2): Scientifiques, Experts

---

## Advanced Analytics (9 Modules)

**Currently demo data — will wire to backend in Phase 8:**

1. **Contradiction Mapping** — Belief tensions within personas
2. **Emotional Drivers** — 10 emotions × 9 personas + trends
3. **Tradeoff Tolerance** — Écologie vs Pouvoir d'achat, etc.
4. **Collective Memory** — 5 historical events (Gilets Jaunes, etc.)
5. **Narrative Saturation** — Lifecycle tracking (émergence → déclin)
6. **Scenario Simulation** — 5 shock scenarios (housing crisis, etc.)
7. **Cascade Chains** — Root cause → electoral consequence
8. **Trust Ecosystem Network** — Distrust propagation graph
9. **Signal/Noise Analysis** — Structural weight vs media volume

---

## Technology Stack

**Current:**
- Python 3.11
- Streamlit 1.35 (16 pages)
- spaCy + CamemBERT + BERTopic
- FAISS in-process
- aiohttp (async scraping)
- structlog (JSON logging)
- APScheduler

**Post-Migration:**
- All shared packages from monorepo
- Diaspora's superior scraping engine
- Anti-hallucination validation

---

## Directory Structure

```
vigil-platform/
├── vigil_personas/          # 9 personas
├── vigil_narratives/        # National narratives
├── vigil_sources/           # 30-source YAML configs
├── vigil_analytics/         # 9 advanced modules
├── vigil_policy_engine/     # Gap analysis, proposals
├── vigil_dashboards/        # Streamlit (16 pages)
├── vigil_config/            # French regions, institutions
├── data/
│   ├── vigil.db             # SQLite (or PostgreSQL later)
│   ├── faiss_index.pkl      # FAISS
│   └── snapshots/           # Raw HTML (post-migration)
└── tests/
```

---

## Migration Impact

**Gains:**
- Multi-strategy scraping (vs single-strategy)
- 19-code failure taxonomy (granular diagnostics)
- Anti-hallucination policy (NULL dates, raw snapshots)
- Reliability scoring (Diaspora's formula)
- Reality anchoring pattern

**Preserves:**
- All 9 personas
- All 30 sources
- All 16 dashboard pages
- All 9 advanced modules
- Production NLP stack
- YAML configuration

**Changes:**
- Scraping engine (single → multi-strategy)
- Validation (quality rules → anti-hallucination + quality)
- Analytics (demo → real computation)

---

## Quick Start (Post-Migration)

```bash
cd apps/vigil-platform

# Install dependencies (from root)
cd ../..
pip install -e .

# Download models
python -m spacy download fr_core_news_lg

# Run dashboard
cd apps/vigil-platform
streamlit run vigil_dashboards/app.py
```

---

## Ethical Framework

**Principles:**
1. **Non-manipulation** — Understand dynamics, don't exploit
2. **Transparency** — Every score has uncertainty
3. **Human supervision** — Validation structurally required
4. **Non-partisanship** — Same methods for all
5. **Traceability** — Every insight traces to sources

See `docs/VIGIL_SCOPE.md` for full ethical framework.

---

## Documentation

- Architecture: `docs/ARCHITECTURE_VIGIL.md`
- Scope & ethics: `docs/VIGIL_SCOPE.md`
- System overview: `docs/SYSTEM_OVERVIEW.md`
- Migration guide: `docs/MIGRATION_GUIDE.md`

---

**Created:** 2024-05-16 (Session 1)  
**Migration Status:** Not started  
**Target Completion:** Session 30 (Phase 8)
