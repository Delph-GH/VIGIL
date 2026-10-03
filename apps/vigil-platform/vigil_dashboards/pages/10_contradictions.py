"""
pages/10_contradictions.py

Contradictions Detector - Vigil with real backend integration

Detects conflicting narratives using real NLP analysis.
"""

import streamlit as st
import sys
from pathlib import Path

# Add paths
vigil_path = Path(__file__).parent.parent
packages_path = vigil_path.parent.parent.parent / "packages"
sys.path.insert(0, str(packages_path))
sys.path.insert(0, str(vigil_path))

from utils.backend import get_backend
from shared_observability import get_logger, metrics
from shared_dashboards import KPICardBuilder

logger = get_logger(__name__)

st.set_page_config(page_title="Contradictions Detector", page_icon="⚠️", layout="wide")

logger.info('dashboard_view', platform='vigil', page='contradictions')
metrics.increment('vigil_dashboard_views', labels={'page': 'contradictions'})

st.title("⚠️ Contradictions Detector")
st.markdown("**Political messaging contradictions and conflicts**")

# Get backend
backend = get_backend()

if backend.is_sample_data:
    st.warning("Sample data: no article database is connected yet. Figures are computed from synthetic articles.")

# Load real data
with st.spinner("Loading articles and analyzing contradictions..."):
    articles = backend.fetch_recent_articles(days=7)
    contradictions = backend.detect_contradictions(articles)
    analytics = backend.analyze_articles(articles)

# Overview
st.subheader("📊 Contradiction Overview")

kpi_builder = KPICardBuilder()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Active Contradictions", len(contradictions))

with col2:
    st.metric("Articles Analyzed", len(articles))

with col3:
    avg_trust = sum(a['trust'] for a in analytics) / len(analytics) if analytics else 0
    st.metric("Avg Source Trust", f"{avg_trust:.2f}")

with col4:
    st.metric("Policy Topics", len(set(c['topic'] for c in contradictions)))

st.markdown("---")

# Real contradictions from analysis
st.subheader("🔍 Detected Contradictions")

if contradictions:
    for idx, contradiction in enumerate(contradictions):
        severity = "high" if contradiction['articles'] > 5 else "medium"
        severity_color = "🔴" if severity == 'high' else "🟡"
        
        with st.expander(f"{severity_color} {contradiction['topic']} - {contradiction['articles']} articles"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"**Topic:** {contradiction['topic']}")
                st.markdown(f"**Type:** {contradiction['type']}")
                st.markdown(f"**Sources:** {', '.join(contradiction['sources'])}")
                st.markdown(f"**Articles:** {contradiction['articles']}")
            
            with col2:
                st.markdown(f"**Severity:** {severity.upper()}")
                st.markdown(f"**Status:** Active")
                st.button("View Details", key=f"detail_{idx}")
else:
    st.info("✅ No major contradictions detected in recent articles")

st.markdown("---")

# Analytics insights
st.subheader("📈 Contradiction Patterns")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**By Topic**")
    topics = {}
    for c in contradictions:
        topics[c['topic']] = topics.get(c['topic'], 0) + 1
    
    if topics:
        st.bar_chart(topics)
    else:
        st.info("No data available")

with col2:
    st.markdown("**Source Reliability**")
    sources_trust = {}
    for article in articles:
        if article.source_name not in sources_trust:
            sources_trust[article.source_name] = []
        
        # Find trust score
        for a in analytics:
            if a['article_id'] == article.article_id:
                sources_trust[article.source_name].append(a['trust'])
                break
    
    avg_trust_by_source = {
        source: sum(scores) / len(scores) 
        for source, scores in sources_trust.items() 
        if scores
    }
    
    if avg_trust_by_source:
        st.bar_chart(avg_trust_by_source)

st.markdown("---")

# Recommendations
st.subheader("💡 Analysis Insights")

st.info(f"📊 **Data Coverage:** {len(articles)} articles analyzed from {len(set(a.source_name for a in articles))} sources")
st.success(f"✅ **Quality:** Average trust score {avg_trust:.2f}/1.0")

if len(contradictions) > 3:
    st.warning(f"⚠️ **Alert:** {len(contradictions)} contradictions detected - verify primary sources")
else:
    st.success("✅ **Status:** Low contradiction rate - sources aligned")

st.caption(f"Last updated: {st.session_state.get('last_refresh', 'Just now')}")
