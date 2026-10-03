"""
pages/30_trust_network.py

Trust Network - Diaspora adaptation

Maps trust relationships and information flow.
"""

import streamlit as st
import sys
from pathlib import Path

packages_path = Path(__file__).parent.parent.parent.parent.parent / "packages"
sys.path.insert(0, str(packages_path))

from shared_observability import get_logger

logger = get_logger(__name__)

st.set_page_config(page_title="Trust Network", page_icon="🤝", layout="wide")

logger.info('dashboard_view', platform='diaspora', page='trust_network')

st.title("🤝 Trust Network")
st.markdown("**Map trust relationships and information credibility**")

# Overview
st.subheader("📊 Network Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Network Nodes", 127, "+15")
with col2:
    st.metric("Trust Connections", 485, "+42")
with col3:
    st.metric("Avg Trust Score", "0.78", "+0.05")
with col4:
    st.metric("Credibility Chains", 28, "+6")

st.markdown("---")

# Trust tiers
st.subheader("🎯 Trust Tiers")

tiers = [
    {
        "tier": "Official Sources",
        "trust_level": 92,
        "examples": ["Government sites", "Embassy", "Official bulletins"],
        "characteristics": "Verified, authoritative, policy information",
    },
    {
        "tier": "Community Leaders",
        "trust_level": 85,
        "examples": ["Association heads", "Long-term expats", "Known moderators"],
        "characteristics": "Experienced, helpful, community-focused",
    },
    {
        "tier": "Local Businesses",
        "trust_level": 72,
        "examples": ["Established services", "Recommended vendors", "Partner orgs"],
        "characteristics": "Professional, service-oriented, reputation-based",
    },
    {
        "tier": "Peer Networks",
        "trust_level": 65,
        "examples": ["Fellow expats", "Parent groups", "Professional networks"],
        "characteristics": "Varied, personal experience, context-dependent",
    },
]

for tier in tiers:
    with st.expander(f"📊 Tier: {tier['tier']} - Trust: {tier['trust_level']}%"):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"**Trust Level:** {tier['trust_level']}%")
            st.progress(tier['trust_level'] / 100)
            
            st.markdown(f"**Characteristics:** {tier['characteristics']}")
            
            st.markdown("**Examples:**")
            for example in tier['examples']:
                st.markdown(f"- {example}")
        
        with col2:
            if tier['trust_level'] >= 85:
                st.success("✅ High Trust")
            elif tier['trust_level'] >= 70:
                st.info("💙 Good Trust")
            else:
                st.warning("⚠️ Variable Trust")

st.markdown("---")

# Information flow
st.subheader("🌊 Information Flow Patterns")

st.markdown("**Primary Pathways:**")

pathways = [
    {
        "path": "Official → Community Leaders → Members",
        "strength": 88,
        "speed": "Medium",
        "reliability": "Very High",
    },
    {
        "path": "Official → Direct to Members",
        "strength": 75,
        "speed": "Fast",
        "reliability": "High",
    },
    {
        "path": "Peer → Peer Network",
        "strength": 65,
        "speed": "Very Fast",
        "reliability": "Variable",
    },
    {
        "path": "Business → Customer Network",
        "strength": 58,
        "speed": "Slow",
        "reliability": "Medium",
    },
]

for pathway in pathways:
    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
    
    with col1:
        st.markdown(f"**{pathway['path']}**")
    with col2:
        st.caption(f"Strength: {pathway['strength']}%")
    with col3:
        st.caption(f"Speed: {pathway['speed']}")
    with col4:
        st.caption(f"Trust: {pathway['reliability']}")

st.markdown("---")

# Key influencers
st.subheader("👥 Key Network Influencers")

influencers = [
    {"name": "Embassy Communications", "type": "Official", "connections": 450, "trust": 95},
    {"name": "Community Association", "type": "Leader", "connections": 380, "trust": 88},
    {"name": "Parent Network Hub", "type": "Peer", "connections": 280, "trust": 82},
    {"name": "Service Directory", "type": "Business", "connections": 220, "trust": 78},
]

for inf in influencers:
    with st.container():
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        
        with col1:
            st.markdown(f"**{inf['name']}**")
            st.caption(inf['type'])
        
        with col2:
            st.metric("Connections", inf['connections'])
        
        with col3:
            st.metric("Trust", f"{inf['trust']}%")
        
        with col4:
            st.progress(inf['trust'] / 100)

st.markdown("---")

# Credibility chains
st.subheader("🔗 Credibility Verification Chains")

st.success("✅ **Chain 1:** Official source → Community leader verification → Member trust")
st.info("💡 **Chain 2:** Peer recommendation → Multiple confirmations → Network acceptance")
st.warning("⚠️ **Chain 3:** Business claim → Customer reviews → Cautious trust")

st.markdown("---")

# Network health
st.subheader("❤️ Network Health Indicators")

health = {
    "Trust Density": 78,
    "Connection Quality": 82,
    "Information Accuracy": 85,
    "Response Time": 72,
}

st.bar_chart(health)
