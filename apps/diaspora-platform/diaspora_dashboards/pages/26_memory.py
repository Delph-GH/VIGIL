"""
pages/26_memory.py

Memory Tracker - Diaspora adaptation

Tracks historical patterns and recurring topics in community.
"""

import streamlit as st
import sys
from pathlib import Path

packages_path = Path(__file__).parent.parent.parent.parent.parent / "packages"
sys.path.insert(0, str(packages_path))

from shared_observability import get_logger

logger = get_logger(__name__)

st.set_page_config(page_title="Memory Tracker", page_icon="🧠", layout="wide")

logger.info('dashboard_view', platform='diaspora', page='memory')

st.title("🧠 Memory Tracker")
st.markdown("**Historical patterns and community memory**")

# Overview
st.subheader("📊 Memory Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Tracked Patterns", 47, "+8")
with col2:
    st.metric("Recurring Topics", 23, "+5")
with col3:
    st.metric("Historical Events", 156, "+12")
with col4:
    st.metric("Forgotten Issues", 8, "-2")

st.markdown("---")

# Seasonal patterns
st.subheader("🗓️ Seasonal Patterns")

patterns = [
    {
        "period": "August - September",
        "pattern": "Back-to-School Questions",
        "topics": ["School enrollment", "Supplies", "Language support"],
        "frequency": "Annual",
        "intensity": "High",
    },
    {
        "period": "December",
        "pattern": "Holiday Homesickness",
        "topics": ["Family separation", "Travel plans", "Local celebrations"],
        "frequency": "Annual",
        "intensity": "Very High",
    },
    {
        "period": "March - April",
        "pattern": "Tax Season Concerns",
        "topics": ["Tax filing", "Dual taxation", "Accountant services"],
        "frequency": "Annual",
        "intensity": "High",
    },
    {
        "period": "May - June",
        "pattern": "Summer Planning",
        "topics": ["Vacation ideas", "Camps", "Home visits"],
        "frequency": "Annual",
        "intensity": "Medium",
    },
]

for pattern in patterns:
    with st.expander(f"📅 {pattern['period']}: {pattern['pattern']}"):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"**Topics:**")
            for topic in pattern['topics']:
                st.markdown(f"- {topic}")
        
        with col2:
            st.markdown(f"**Frequency:** {pattern['frequency']}")
            st.markdown(f"**Intensity:** {pattern['intensity']}")

st.markdown("---")

# Historical milestones
st.subheader("🏆 Community Milestones")

milestones = [
    {"year": "2024", "event": "Community center launched", "impact": "High"},
    {"year": "2023", "event": "Integration program expanded", "impact": "High"},
    {"year": "2022", "event": "Visa policy changes", "impact": "Critical"},
    {"year": "2021", "event": "COVID-19 support network", "impact": "Very High"},
]

for milestone in milestones:
    impact_color = "🔴" if milestone['impact'] in ['Critical', 'Very High'] else "🟡" if milestone['impact'] == 'High' else "🟢"
    st.markdown(f"{impact_color} **{milestone['year']}:** {milestone['event']} _{milestone['impact']}_")

st.markdown("---")

# Forgotten issues
st.subheader("⚠️ Resurfacing Issues")

st.warning("🔄 **Recurring Problem:** Parking permit renewals - forgotten every 2 years")
st.info("💡 **Historical Context:** Last major visa policy change was 2022 - due for review")
st.success("✅ **Resolved:** Community bus service restored after 6-month gap")

st.markdown("---")

# Trend chart
st.subheader("📈 Topic Evolution")

st.markdown("**Interest Over Time:**")

# Sample data
evolution = {
    "Q1 2024": {"Integration": 85, "Housing": 72, "Education": 65},
    "Q2 2024": {"Integration": 78, "Housing": 80, "Education": 70},
    "Q3 2024": {"Integration": 82, "Housing": 75, "Education": 85},
    "Q4 2024": {"Integration": 88, "Housing": 78, "Education": 72},
}

st.line_chart(evolution)
