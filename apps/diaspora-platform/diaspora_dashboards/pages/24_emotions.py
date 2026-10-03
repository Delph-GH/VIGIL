"""
pages/24_emotions.py

Emotions Analyzer - Diaspora adaptation

Analyzes emotional content in community discourse.
"""

import streamlit as st
import sys
from pathlib import Path

packages_path = Path(__file__).parent.parent.parent.parent.parent / "packages"
sys.path.insert(0, str(packages_path))

from shared_observability import get_logger

logger = get_logger(__name__)

st.set_page_config(page_title="Emotions Analyzer", page_icon="😊", layout="wide")

logger.info('dashboard_view', platform='diaspora', page='emotions')

st.title("😊 Emotions Analyzer")
st.markdown("**Understand emotional dynamics in community content**")

# Overview
st.subheader("📊 Emotional Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Overall Sentiment", "Positive", "↗️ +5%")
with col2:
    st.metric("Anxiety Level", "Low", "↘️ -8%")
with col3:
    st.metric("Excitement Score", "72/100", "+12")
with col4:
    st.metric("Concerns Raised", 18, "+3")

st.markdown("---")

# Emotion distribution
st.subheader("🎨 Emotion Distribution")

emotions = {
    "😊 Joy": 35,
    "😟 Concern": 22,
    "😐 Neutral": 18,
    "😃 Excitement": 15,
    "😔 Sadness": 10,
}

st.bar_chart(emotions)

st.markdown("---")

# Emotional triggers
st.subheader("🎯 Top Emotional Triggers")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Positive Triggers**")
    positive = [
        "Community Events (+85% joy)",
        "Integration Success Stories (+72% excitement)",
        "New Services Announced (+68% satisfaction)",
    ]
    for trigger in positive:
        st.success(f"✅ {trigger}")

with col2:
    st.markdown("**Concern Triggers**")
    concerns = [
        "Visa Process Changes (45% anxiety)",
        "Cost of Living Increases (38% concern)",
        "Language Barriers (32% frustration)",
    ]
    for concern in concerns:
        st.warning(f"⚠️ {concern}")

st.markdown("---")

# Trends
st.subheader("📈 Emotional Trends")

st.markdown("**Weekly Sentiment Progression**")

trend_data = {
    "Week 1": {"Positive": 65, "Negative": 20, "Neutral": 15},
    "Week 2": {"Positive": 70, "Negative": 18, "Neutral": 12},
    "Week 3": {"Positive": 68, "Negative": 22, "Neutral": 10},
    "Week 4": {"Positive": 72, "Negative": 15, "Neutral": 13},
}

# Display as line chart
for emotion in ["Positive", "Negative", "Neutral"]:
    data = {week: values[emotion] for week, values in trend_data.items()}
    st.line_chart(data)

st.markdown("---")

# Community mood
st.subheader("🌡️ Community Mood Indicator")

mood_score = 72
mood_label = "Optimistic"

st.progress(mood_score / 100)
st.markdown(f"**Current Mood:** {mood_label} ({mood_score}/100)")

st.info("💡 **Insight:** Community sentiment is trending positively, with excitement around upcoming cultural events.")
