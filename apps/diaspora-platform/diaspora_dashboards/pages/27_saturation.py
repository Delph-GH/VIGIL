"""
pages/27_saturation.py

Saturation Detector - Diaspora adaptation

Detects information overload and content fatigue.
"""

import streamlit as st
import sys
from pathlib import Path

packages_path = Path(__file__).parent.parent.parent.parent.parent / "packages"
sys.path.insert(0, str(packages_path))

from shared_observability import get_logger

logger = get_logger(__name__)

st.set_page_config(page_title="Saturation Detector", page_icon="📊", layout="wide")

logger.info('dashboard_view', platform='diaspora', page='saturation')

st.title("📊 Saturation Detector")
st.markdown("**Monitor information overload and content fatigue**")

# Overview
st.subheader("⚠️ Saturation Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Saturated Topics", 5, "+2")
with col2:
    st.metric("Engagement Decline", "18%", "-5%")
with col3:
    st.metric("Fatigue Score", "42/100", "+8")
with col4:
    st.metric("Overload Alerts", 3, "+1")

st.markdown("---")

# Saturated topics
st.subheader("🚨 Saturated Topics")

saturated = [
    {
        "topic": "COVID-19 Updates",
        "saturation_level": 85,
        "engagement_drop": -45,
        "status": "Critical",
        "recommendation": "Reduce frequency, focus on major changes only",
    },
    {
        "topic": "Visa Process Updates",
        "saturation_level": 72,
        "engagement_drop": -32,
        "status": "High",
        "recommendation": "Consolidate into weekly summaries",
    },
    {
        "topic": "Political News",
        "saturation_level": 68,
        "engagement_drop": -28,
        "status": "Medium",
        "recommendation": "Focus on expat-relevant policies",
    },
]

for item in saturated:
    status_color = "🔴" if item['status'] == 'Critical' else "🟡" if item['status'] == 'High' else "🟢"
    
    with st.expander(f"{status_color} {item['topic']} - {item['status']} Saturation"):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"**Saturation Level:** {item['saturation_level']}%")
            st.progress(item['saturation_level'] / 100)
            
            st.markdown(f"**Engagement Drop:** {item['engagement_drop']}%")
            st.markdown(f"**Recommendation:** {item['recommendation']}")
        
        with col2:
            st.markdown("**Indicators:**")
            st.markdown("- ⬇️ Declining clicks")
            st.markdown("- 💬 Fewer comments")
            st.markdown("- 🚪 Topic avoidance")

st.markdown("---")

# Fatigue indicators
st.subheader("😴 Fatigue Indicators")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Engagement Metrics**")
    
    metrics = {
        "Article Views": -22,
        "Comment Rate": -35,
        "Share Rate": -18,
        "Time on Page": -28,
    }
    
    for metric, change in metrics.items():
        color = "🔴" if change < -25 else "🟡"
        st.markdown(f"{color} **{metric}:** {change}%")

with col2:
    st.markdown("**Behavioral Patterns**")
    
    patterns = [
        "📉 Scrolling past familiar topics",
        "⏭️ Skipping repetitive content",
        "🔇 Muting notification categories",
        "📱 Reduced app time",
    ]
    
    for pattern in patterns:
        st.markdown(pattern)

st.markdown("---")

# Trend analysis
st.subheader("📈 Saturation Trends")

st.markdown("**Topic Saturation Over Time**")

saturation_trend = {
    "Week 1": {"COVID": 45, "Visa": 38, "Politics": 35},
    "Week 2": {"COVID": 58, "Visa": 48, "Politics": 42},
    "Week 3": {"COVID": 72, "Visa": 62, "Politics": 55},
    "Week 4": {"COVID": 85, "Visa": 72, "Politics": 68},
}

st.line_chart(saturation_trend)

st.markdown("---")

# Recommendations
st.subheader("💡 Recommendations")

st.success("✅ **Diversify Content:** Introduce fresh topics and perspectives")
st.info("💡 **Content Breaks:** Space out heavy topics with lighter community content")
st.warning("⚠️ **Quality Over Quantity:** Reduce volume, increase value")
st.error("🚨 **Critical:** Pause COVID updates except for major policy changes")
