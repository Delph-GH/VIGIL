"""
pages/25_tradeoffs.py

Tradeoffs Analyzer - Diaspora adaptation

Analyzes decision tradeoffs in community contexts.
"""

import streamlit as st
import sys
from pathlib import Path

packages_path = Path(__file__).parent.parent.parent.parent.parent / "packages"
sys.path.insert(0, str(packages_path))

from shared_observability import get_logger

logger = get_logger(__name__)

st.set_page_config(page_title="Tradeoffs Analyzer", page_icon="⚖️", layout="wide")

logger.info('dashboard_view', platform='diaspora', page='tradeoffs')

st.title("⚖️ Tradeoffs Analyzer")
st.markdown("**Analyze community decision tradeoffs**")

# Overview
st.subheader("📊 Decision Analysis Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Active Decisions", 28, "+5")
with col2:
    st.metric("Analyzed Tradeoffs", 156, "+23")
with col3:
    st.metric("Community Polls", 12, "+3")
with col4:
    st.metric("Resolution Rate", "72%", "+8%")

st.markdown("---")

# Common tradeoffs
st.subheader("🔄 Common Community Tradeoffs")

tradeoffs = [
    {
        "decision": "Housing Location",
        "option_a": {"label": "City Center", "pros": "Close to work, amenities", "cons": "Higher cost, noise"},
        "option_b": {"label": "Suburbs", "pros": "Space, quiet, family-friendly", "cons": "Longer commute, less amenities"},
        "community_preference": 58,
    },
    {
        "decision": "School Choice",
        "option_a": {"label": "International School", "pros": "English language, familiar curriculum", "cons": "Expensive, less integration"},
        "option_b": {"label": "Local School", "pros": "Language immersion, integration", "cons": "Language barrier, different system"},
        "community_preference": 52,
    },
    {
        "decision": "Healthcare",
        "option_a": {"label": "Private Insurance", "pros": "English-speaking, choice", "cons": "Higher cost"},
        "option_b": {"label": "Public System", "pros": "Lower cost, comprehensive", "cons": "Language challenges"},
        "community_preference": 65,
    },
]

for tradeoff in tradeoffs:
    with st.expander(f"⚖️ {tradeoff['decision']}"):
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            st.markdown(f"**Option A: {tradeoff['option_a']['label']}**")
            st.success(f"✅ Pros: {tradeoff['option_a']['pros']}")
            st.error(f"❌ Cons: {tradeoff['option_a']['cons']}")
        
        with col2:
            st.markdown(f"**Option B: {tradeoff['option_b']['label']}**")
            st.success(f"✅ Pros: {tradeoff['option_b']['pros']}")
            st.error(f"❌ Cons: {tradeoff['option_b']['cons']}")
        
        with col3:
            st.markdown("**Community Preference**")
            st.progress(tradeoff['community_preference'] / 100)
            st.caption(f"{tradeoff['community_preference']}% favor Option A")

st.markdown("---")

# Decision framework
st.subheader("📋 Decision Framework")

st.markdown("**Key Factors to Consider:**")

factors = [
    "💰 **Cost** - Immediate and long-term financial impact",
    "⏰ **Time** - Daily time investment and convenience",
    "👨‍👩‍👧‍👦 **Family** - Impact on family integration and wellbeing",
    "🎓 **Integration** - Effect on cultural immersion and language learning",
    "💼 **Career** - Professional development and opportunities",
    "🏥 **Health** - Healthcare access and quality",
]

for factor in factors:
    st.markdown(factor)

st.markdown("---")

# Recommendations
st.subheader("💡 Community Insights")

col1, col2 = st.columns(2)

with col1:
    st.info("📊 **Popular Choice:** Suburbs for families with children (62% satisfaction)")
    st.info("🎓 **Education:** Mixed approach - local school + language support (68% success)")

with col2:
    st.success("💡 **Tip:** Consider trial periods before major commitments")
    st.warning("⚠️ **Note:** Tradeoffs vary by individual circumstances")
