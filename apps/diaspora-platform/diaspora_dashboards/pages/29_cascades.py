"""
pages/29_cascades.py

Cascades Tracker - Diaspora adaptation

Tracks viral information spread in community.
"""

import streamlit as st
import sys
from pathlib import Path

packages_path = Path(__file__).parent.parent.parent.parent.parent / "packages"
sys.path.insert(0, str(packages_path))

from shared_observability import get_logger

logger = get_logger(__name__)

st.set_page_config(page_title="Cascades Tracker", page_icon="📡", layout="wide")

logger.info('dashboard_view', platform='diaspora', page='cascades')

st.title("📡 Cascades Tracker")
st.markdown("**Track information diffusion and viral spread**")

# Overview
st.subheader("📊 Cascade Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Active Cascades", 18, "+5")
with col2:
    st.metric("Viral Threshold", "250 shares", "Stable")
with col3:
    st.metric("Avg Spread Time", "4.2 hours", "-1.3h")
with col4:
    st.metric("Reach Rate", "68%", "+12%")

st.markdown("---")

# Active cascades
st.subheader("🌊 Active Information Cascades")

cascades = [
    {
        "topic": "Emergency: Pharmacy Strike Alert",
        "type": "Emergency",
        "start_time": "2 hours ago",
        "reach": 850,
        "shares": 340,
        "speed": "Very Fast",
        "status": "Active",
    },
    {
        "topic": "Community BBQ This Weekend",
        "type": "Event",
        "start_time": "12 hours ago",
        "reach": 520,
        "shares": 180,
        "speed": "Medium",
        "status": "Growing",
    },
    {
        "topic": "Great Doctor Recommendation",
        "type": "Service",
        "start_time": "2 days ago",
        "reach": 380,
        "shares": 95,
        "speed": "Slow",
        "status": "Steady",
    },
]

for cascade in cascades:
    speed_color = "🔴" if cascade['speed'] == 'Very Fast' else "🟡" if cascade['speed'] == 'Medium' else "🟢"
    
    with st.expander(f"{speed_color} {cascade['topic']} - {cascade['type']}"):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"**Type:** {cascade['type']}")
            st.markdown(f"**Started:** {cascade['start_time']}")
            st.markdown(f"**Total Reach:** {cascade['reach']} people")
            st.markdown(f"**Shares:** {cascade['shares']}")
        
        with col2:
            st.markdown(f"**Speed:** {cascade['speed']}")
            st.markdown(f"**Status:** {cascade['status']}")
            
            reach_pct = min(100, (cascade['reach'] / 1000) * 100)
            st.progress(reach_pct / 100)

st.markdown("---")

# Cascade types
st.subheader("📋 Cascade Types")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**By Type**")
    
    types = {
        "🚨 Emergency": "Immediate, critical info",
        "🎉 Events": "Scheduled, promotional",
        "💡 Services": "Gradual, word-of-mouth",
        "📰 News": "Rapid, information-driven",
    }
    
    for type_name, desc in types.items():
        st.markdown(f"{type_name}")
        st.caption(desc)

with col2:
    st.markdown("**Spread Patterns**")
    
    patterns = {
        "Emergency Alerts": 95,
        "Event Invites": 68,
        "Service Tips": 42,
        "General News": 78,
    }
    
    st.bar_chart(patterns)

st.markdown("---")

# Diffusion network
st.subheader("🕸️ Diffusion Network Analysis")

st.markdown("**Key Amplifiers:**")

amplifiers = [
    {"name": "Community Leaders", "reach": 1200, "influence": 92},
    {"name": "Official Channels", "reach": 2500, "influence": 88},
    {"name": "Parent Groups", "reach": 850, "influence": 75},
    {"name": "Local Businesses", "reach": 650, "influence": 68},
]

for amp in amplifiers:
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown(f"**{amp['name']}**")
    with col2:
        st.caption(f"Reach: {amp['reach']}")
    with col3:
        st.progress(amp['influence'] / 100)
        st.caption(f"{amp['influence']}%")

st.markdown("---")

# Viral predictions
st.subheader("🔮 Viral Potential Predictions")

st.success("✅ **High Potential:** Weekend hiking meetup announcement")
st.warning("⚠️ **Medium Potential:** New restaurant opening notification")
st.info("💡 **Low Potential:** Routine newsletter update")

st.markdown("---")

# Cascade timeline
st.subheader("📈 Cascade Timeline")

timeline = {
    "0-2h": 120,
    "2-6h": 380,
    "6-12h": 520,
    "12-24h": 680,
    "24h+": 850,
}

st.line_chart(timeline)
