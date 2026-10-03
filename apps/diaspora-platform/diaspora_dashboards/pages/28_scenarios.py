"""
pages/28_scenarios.py

Scenarios Explorer - Diaspora adaptation

Explore and plan for future community scenarios.
"""

import streamlit as st
import sys
from pathlib import Path

packages_path = Path(__file__).parent.parent.parent.parent.parent / "packages"
sys.path.insert(0, str(packages_path))

from shared_observability import get_logger

logger = get_logger(__name__)

st.set_page_config(page_title="Scenarios Explorer", page_icon="🔮", layout="wide")

logger.info('dashboard_view', platform='diaspora', page='scenarios')

st.title("🔮 Scenarios Explorer")
st.markdown("**Plan for future community scenarios**")

# Overview
st.subheader("📊 Scenario Planning Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Active Scenarios", 8, "+2")
with col2:
    st.metric("High Probability", 3, "+1")
with col3:
    st.metric("Contingency Plans", 12, "+4")
with col4:
    st.metric("Risk Level", "Medium", "Stable")

st.markdown("---")

# Key scenarios
st.subheader("🎯 Key Future Scenarios")

scenarios = [
    {
        "name": "Visa Policy Tightening",
        "probability": "High (75%)",
        "impact": "High",
        "timeframe": "6-12 months",
        "implications": [
            "Increased documentation requirements",
            "Longer processing times",
            "Need for legal assistance",
        ],
        "actions": [
            "Update documentation guides",
            "Partner with immigration lawyers",
            "Create support network",
        ],
    },
    {
        "name": "Community Center Expansion",
        "probability": "Medium (60%)",
        "impact": "Medium-High",
        "timeframe": "12-18 months",
        "implications": [
            "More services available",
            "Increased community events",
            "Need for volunteers",
        ],
        "actions": [
            "Plan programming",
            "Recruit volunteers",
            "Secure funding",
        ],
    },
    {
        "name": "Housing Cost Increase",
        "probability": "High (80%)",
        "impact": "High",
        "timeframe": "Ongoing",
        "implications": [
            "Affordability challenges",
            "Suburban migration",
            "Shared housing interest",
        ],
        "actions": [
            "Housing assistance program",
            "Cost-sharing platforms",
            "Relocation support",
        ],
    },
]

for scenario in scenarios:
    prob_color = "🔴" if "High" in scenario['probability'] else "🟡"
    
    with st.expander(f"{prob_color} {scenario['name']} - {scenario['probability']}"):
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown(f"**Probability:** {scenario['probability']}")
            st.markdown(f"**Impact:** {scenario['impact']}")
            st.markdown(f"**Timeframe:** {scenario['timeframe']}")
            
            st.markdown("**Implications:**")
            for imp in scenario['implications']:
                st.markdown(f"- {imp}")
        
        with col2:
            st.markdown("**Recommended Actions:**")
            for action in scenario['actions']:
                st.markdown(f"✅ {action}")

st.markdown("---")

# Risk matrix
st.subheader("📊 Risk Assessment Matrix")

st.markdown("**Probability vs Impact**")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**High Probability, High Impact**")
    st.error("🔴 Visa policy changes")
    st.error("🔴 Housing costs")

with col2:
    st.markdown("**Medium Probability, High Impact**")
    st.warning("🟡 Community center expansion")
    st.warning("🟡 Service disruptions")

with col3:
    st.markdown("**Low Probability, High Impact**")
    st.info("🔵 Major policy reform")
    st.info("🔵 Economic crisis")

st.markdown("---")

# Contingency planning
st.subheader("🛡️ Contingency Plans")

st.success("✅ **Plan A:** Visa policy changes - Legal network activated")
st.success("✅ **Plan B:** Service expansion - Funding secured")
st.warning("⚠️ **Plan C:** Housing crisis - Developing shared housing platform")
st.info("💡 **Plan D:** Community growth - Scaling infrastructure")

st.markdown("---")

# Monitoring
st.subheader("👁️ Scenario Monitoring")

st.markdown("**Early Warning Indicators:**")

indicators = [
    ("Government policy discussions", "Active", "🟡"),
    ("Housing market trends", "Monitoring", "🟢"),
    ("Community growth rate", "Stable", "🟢"),
    ("Economic indicators", "Watching", "🟡"),
]

for indicator, status, color in indicators:
    st.markdown(f"{color} **{indicator}:** {status}")
