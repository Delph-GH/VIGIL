"""
pages/23_contradictions.py

Contradictions Detector - Diaspora adaptation

Detects conflicting narratives in community information.
"""

import streamlit as st
import sys
from pathlib import Path

packages_path = Path(__file__).parent.parent.parent.parent.parent / "packages"
sys.path.insert(0, str(packages_path))

from shared_dashboards import KPICardBuilder
from shared_observability import get_logger, metrics

logger = get_logger(__name__)

st.set_page_config(page_title="Contradictions Detector", page_icon="⚠️", layout="wide")

logger.info('dashboard_view', platform='diaspora', page='contradictions')
metrics.increment('diaspora_dashboard_views', labels={'page': 'contradictions'})

st.title("⚠️ Contradictions Detector")
st.markdown("**Identify conflicting information in community narratives**")

# Overview
st.subheader("📊 Contradiction Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Active Contradictions", 12, "-3")
with col2:
    st.metric("Resolved This Week", 8, "+2")
with col3:
    st.metric("High Priority", 3, "-1")
with col4:
    st.metric("Average Resolution Time", "2.3 days", "-0.5")

st.markdown("---")

# Active contradictions
st.subheader("🔍 Active Contradictions")

contradictions = [
    {
        "id": 1,
        "type": "Service Info",
        "topic": "Visa Extension Process",
        "severity": "high",
        "sources": ["Le Petit Journal", "Connexion France"],
        "contradiction": "Conflicting requirements for visa renewal documentation",
        "impact": "Affects 200+ expats",
    },
    {
        "id": 2,
        "type": "Event Details",
        "topic": "Community Meetup Location",
        "severity": "medium",
        "sources": ["Munich Expat News", "Bayern Community"],
        "contradiction": "Different locations announced for same event",
        "impact": "Affects 50+ attendees",
    },
    {
        "id": 3,
        "type": "Policy Change",
        "topic": "Health Insurance Requirements",
        "severity": "high",
        "sources": ["Official Bulletin", "Community Forums"],
        "contradiction": "Conflicting interpretations of new policy",
        "impact": "Critical for all expats",
    },
]

for contradiction in contradictions:
    severity_color = "🔴" if contradiction['severity'] == 'high' else "🟡"
    
    with st.expander(f"{severity_color} {contradiction['topic']} (ID: {contradiction['id']})"):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"**Type:** {contradiction['type']}")
            st.markdown(f"**Contradiction:** {contradiction['contradiction']}")
            st.markdown(f"**Impact:** {contradiction['impact']}")
            st.markdown(f"**Sources:** {', '.join(contradiction['sources'])}")
        
        with col2:
            st.markdown(f"**Severity:** {contradiction['severity'].upper()}")
            st.button("View Details", key=f"detail_{contradiction['id']}")
            st.button("Mark Resolved", key=f"resolve_{contradiction['id']}")

st.markdown("---")

# Analysis
st.subheader("📈 Contradiction Trends")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**By Category**")
    categories = {
        "Service Info": 5,
        "Event Details": 3,
        "Policy Changes": 2,
        "Community News": 2,
    }
    st.bar_chart(categories)

with col2:
    st.markdown("**Resolution Timeline**")
    timeline = {
        "Week 1": 3,
        "Week 2": 5,
        "Week 3": 8,
        "Week 4": 6,
    }
    st.line_chart(timeline)

st.markdown("---")

# Recommendations
st.subheader("💡 Recommendations")

st.info("🔍 **Recommendation:** Review visa extension documentation from official sources")
st.warning("⚠️ **Action Required:** Clarify community meetup location with organizers")
st.success("✅ **Update:** Health insurance policy interpretation confirmed by authorities")
