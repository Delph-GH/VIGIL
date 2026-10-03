"""
pages/31_signal_noise.py

Signal/Noise Ratio - Diaspora adaptation

Measures content quality and value vs noise.
"""

import streamlit as st
import sys
from pathlib import Path

packages_path = Path(__file__).parent.parent.parent.parent.parent / "packages"
sys.path.insert(0, str(packages_path))

from shared_observability import get_logger

logger = get_logger(__name__)

st.set_page_config(page_title="Signal/Noise Ratio", page_icon="📶", layout="wide")

logger.info('dashboard_view', platform='diaspora', page='signal_noise')

st.title("📶 Signal/Noise Ratio")
st.markdown("**Measure content quality and filter noise**")

# Overview
st.subheader("📊 Quality Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Signal Ratio", "72%", "+5%")
with col2:
    st.metric("Noise Level", "28%", "-5%")
with col3:
    st.metric("Quality Score", "85/100", "+8")
with col4:
    st.metric("Actionability", "High", "↗️")

st.markdown("---")

# Signal vs Noise
st.subheader("📡 Signal vs Noise Breakdown")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**🟢 SIGNAL (Valuable Content)**")
    
    signals = [
        "✅ Official policy announcements",
        "✅ Verified service recommendations",
        "✅ Community event information",
        "✅ Educational content",
        "✅ Practical how-to guides",
        "✅ Time-sensitive alerts",
    ]
    
    for signal in signals:
        st.success(signal)

with col2:
    st.markdown("**🔴 NOISE (Low-Value Content)**")
    
    noises = [
        "❌ Promotional spam",
        "❌ Unverified rumors",
        "❌ Repetitive content",
        "❌ Off-topic discussions",
        "❌ Clickbait articles",
        "❌ Outdated information",
    ]
    
    for noise in noises:
        st.error(noise)

st.markdown("---")

# Content categories
st.subheader("📋 Content Category Analysis")

categories = [
    {
        "category": "Official Announcements",
        "signal": 95,
        "noise": 5,
        "actionability": "Very High",
    },
    {
        "category": "Community Events",
        "signal": 88,
        "noise": 12,
        "actionability": "High",
    },
    {
        "category": "Service Recommendations",
        "signal": 75,
        "noise": 25,
        "actionability": "High",
    },
    {
        "category": "General Discussions",
        "signal": 60,
        "noise": 40,
        "actionability": "Medium",
    },
    {
        "category": "Advertisements",
        "signal": 25,
        "noise": 75,
        "actionability": "Low",
    },
]

for cat in categories:
    with st.expander(f"📊 {cat['category']} - Signal: {cat['signal']}%"):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown("**Signal Composition:**")
            st.progress(cat['signal'] / 100, text=f"Signal: {cat['signal']}%")
            st.progress(cat['noise'] / 100, text=f"Noise: {cat['noise']}%")
        
        with col2:
            st.markdown(f"**Actionability:**")
            st.markdown(f"{cat['actionability']}")

st.markdown("---")

# Quality trends
st.subheader("📈 Quality Trends")

st.markdown("**Signal/Noise Over Time**")

trends = {
    "Week 1": {"Signal": 68, "Noise": 32},
    "Week 2": {"Signal": 70, "Noise": 30},
    "Week 3": {"Signal": 72, "Noise": 28},
    "Week 4": {"Signal": 72, "Noise": 28},
}

st.line_chart(trends)

st.markdown("---")

# Filtering recommendations
st.subheader("🎯 Filtering Recommendations")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Boost Signal:**")
    st.success("✅ Prioritize official sources")
    st.success("✅ Highlight verified content")
    st.success("✅ Feature actionable posts")

with col2:
    st.markdown("**Reduce Noise:**")
    st.warning("⚠️ Filter promotional content")
    st.warning("⚠️ Flag unverified claims")
    st.warning("⚠️ Limit repetitive posts")

st.markdown("---")

# Value metrics
st.subheader("💎 Value Metrics")

value_scores = {
    "Relevance": 88,
    "Timeliness": 82,
    "Accuracy": 90,
    "Actionability": 85,
    "Uniqueness": 75,
}

st.bar_chart(value_scores)

st.markdown("---")

# Content health
st.subheader("❤️ Content Ecosystem Health")

st.success("✅ **High Signal Ratio:** Quality content dominates (72%)")
st.info("💡 **Good Filtering:** Effective noise reduction mechanisms")
st.success("✅ **Strong Actionability:** Most content provides clear value")
st.warning("⚠️ **Watch:** Promotional content increasing slightly")
