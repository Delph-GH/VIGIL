"""
pages/02_quality.py

Quality Metrics page for Diaspora dashboard.
"""

import streamlit as st
import sys
from pathlib import Path

packages_path = Path(__file__).parent.parent.parent.parent.parent / "packages"
sys.path.insert(0, str(packages_path))

from shared_dashboards import KPICardBuilder, TrustGaugeBuilder
from shared_observability import get_logger

logger = get_logger(__name__)

st.set_page_config(page_title="Quality Metrics", page_icon="✅", layout="wide")

logger.info('dashboard_view', platform='diaspora', page='quality')

st.title("✅ Quality Metrics")
st.markdown("Monitor content quality and validation")

# Overview
st.subheader("📊 Quality Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Avg Quality Score", "82.5/100", "+2.3")
with col2:
    st.metric("Pass Rate", "97.2%", "+1.5%")
with col3:
    st.metric("Hallucination Rate", "2.1%", "-0.5%")
with col4:
    st.metric("Manual Reviews", 12, "-3")

st.markdown("---")

# Quality Distribution
st.subheader("📈 Quality Score Distribution")

quality_data = {
    "90-100": 42,
    "80-89": 56,
    "70-79": 28,
    "60-69": 12,
    "<60": 4
}

st.bar_chart(quality_data)

st.markdown("---")

# Trust Gauges
st.subheader("🎯 Source Quality Indicators")

gauge_builder = TrustGaugeBuilder()

col1, col2, col3 = st.columns(3)

with col1:
    gauge = gauge_builder.article_quality(85.2)
    gauge_dict = gauge.to_dict()
    st.markdown(f"**Overall Quality**")
    st.progress(gauge_dict['percentage'] / 100)
    st.markdown(f"**{gauge_dict['percentage']:.0f}%** - {gauge_dict['status']}")

with col2:
    gauge = gauge_builder.source_trust("Le Petit Journal", 0.82)
    gauge_dict = gauge.to_dict()
    st.markdown(f"**Source Reliability**")
    st.progress(gauge_dict['percentage'] / 100)
    st.markdown(f"**{gauge_dict['percentage']:.0f}%** - {gauge_dict['status']}")

with col3:
    gauge = gauge_builder.system_health(0.95)
    gauge_dict = gauge.to_dict()
    st.markdown(f"**Validation System**")
    st.progress(gauge_dict['percentage'] / 100)
    st.markdown(f"**{gauge_dict['percentage']:.0f}%** - {gauge_dict['status']}")

st.markdown("---")

# Quality Issues
st.subheader("⚠️ Quality Issues")

issues = [
    ("Low quality content", 8, "warning"),
    ("Potential hallucinations", 3, "danger"),
    ("Manual review pending", 12, "info"),
]

for issue, count, level in issues:
    if level == "danger":
        st.error(f"🔴 {issue}: {count}")
    elif level == "warning":
        st.warning(f"🟡 {issue}: {count}")
    else:
        st.info(f"🔵 {issue}: {count}")
