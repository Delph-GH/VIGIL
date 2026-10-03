"""
pages/11_emotions.py

Emotions Analyzer - Vigil with real backend integration

Analyzes emotional content using real sentiment analysis.
"""

import streamlit as st
import sys
from pathlib import Path

vigil_path = Path(__file__).parent.parent
packages_path = vigil_path.parent.parent.parent / "packages"
sys.path.insert(0, str(packages_path))
sys.path.insert(0, str(vigil_path))

from utils.backend import get_backend
from shared_observability import get_logger
from shared_dashboards import TrustGaugeBuilder

logger = get_logger(__name__)

st.set_page_config(page_title="Emotions Analyzer", page_icon="😊", layout="wide")

logger.info('dashboard_view', platform='vigil', page='emotions')

st.title("😊 Emotions Analyzer")
st.markdown("**Political sentiment and emotional dynamics**")

# Get backend
backend = get_backend()

if backend.is_sample_data:
    st.warning("Sample data: no article database is connected yet. Figures are computed from synthetic articles.")

# Load real data
with st.spinner("Analyzing emotional content..."):
    articles = backend.fetch_recent_articles(days=7)
    sentiments = backend.analyze_sentiment(articles)
    analytics = backend.analyze_articles(articles)

# Overview
st.subheader("📊 Emotional Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
    dominant = max(sentiments.items(), key=lambda x: x[1])
    st.metric("Dominant Sentiment", dominant[0].capitalize(), f"{dominant[1]:.1f}%")

with col2:
    st.metric("Positive", f"{sentiments.get('positive', 0):.1f}%", "Political optimism")

with col3:
    st.metric("Negative", f"{sentiments.get('negative', 0):.1f}%", "Critical coverage")

with col4:
    st.metric("Neutral", f"{sentiments.get('neutral', 0):.1f}%", "Factual reporting")

st.markdown("---")

# Sentiment distribution
st.subheader("🎨 Sentiment Distribution")

st.bar_chart(sentiments)

st.markdown("---")

# Entity sentiment
st.subheader("👥 Entity Sentiment Analysis")
st.info("Illustrative only: per-entity sentiment is not computed yet (needs NER, which requires spaCy).")

# Compute sentiment by entity (simplified)
entity_sentiment = {
    'Macron': {'positive': 32, 'negative': 45, 'neutral': 23},
    'Borne': {'positive': 28, 'negative': 38, 'neutral': 34},
    'Le Pen': {'positive': 22, 'negative': 52, 'neutral': 26},
}

for entity, scores in entity_sentiment.items():
    with st.expander(f"📊 {entity} - Sentiment Breakdown"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Positive", f"{scores['positive']}%")
        with col2:
            st.metric("Negative", f"{scores['negative']}%")
        with col3:
            st.metric("Neutral", f"{scores['neutral']}%")
        
        # Dominant sentiment
        dominant = max(scores.items(), key=lambda x: x[1])
        if dominant[0] == 'negative':
            st.error(f"⚠️ **Predominantly negative coverage** ({dominant[1]}%)")
        elif dominant[0] == 'positive':
            st.success(f"✅ **Predominantly positive coverage** ({dominant[1]}%)")
        else:
            st.info(f"ℹ️ **Balanced coverage** ({dominant[1]}%)")

st.markdown("---")

# Trends
st.subheader("📈 Sentiment Trends")

st.markdown("**Weekly Sentiment Evolution**")
st.info("Illustrative only: no time series is computed yet.")

# Sample time series data
trend_data = {
    "Day 1": sentiments,
    "Day 3": {k: v + 5 for k, v in sentiments.items()},
    "Day 5": {k: v - 3 for k, v in sentiments.items()},
    "Day 7": sentiments,
}

st.line_chart(trend_data)

st.markdown("---")

# Trust gauges
st.subheader("🎯 Sentiment Quality Indicators")

gauge_builder = TrustGaugeBuilder()

col1, col2, col3 = st.columns(3)

with col1:
    avg_trust = sum(a['trust'] for a in analytics) / len(analytics) if analytics else 0
    gauge = gauge_builder.source_trust("All Sources", avg_trust)
    gauge_dict = gauge.to_dict()
    
    st.markdown("**Source Reliability**")
    st.progress(gauge_dict['percentage'] / 100)
    st.markdown(f"**{gauge_dict['percentage']:.0f}%** - {gauge_dict['status']}")

with col2:
    st.markdown("**Analysis Confidence**")
    st.caption("Not computed yet.")

with col3:
    # Coverage balance
    balance_score = 100 - abs(sentiments.get('positive', 0) - sentiments.get('negative', 0))
    gauge = gauge_builder.custom("Coverage Balance", balance_score / 100)
    gauge_dict = gauge.to_dict()
    
    st.markdown("**Coverage Balance**")
    st.progress(gauge_dict['percentage'] / 100)
    st.markdown(f"**{gauge_dict['percentage']:.0f}%** - {gauge_dict['status']}")

st.markdown("---")

# Insights
st.subheader("💡 Emotional Analysis Insights")

st.info(f"📊 **Sample Size:** {len(articles)} articles analyzed")

if sentiments.get('negative', 0) > 50:
    st.warning(f"⚠️ **High Negativity:** {sentiments['negative']:.1f}% negative sentiment detected")
elif sentiments.get('positive', 0) > 50:
    st.success(f"✅ **Positive Trend:** {sentiments['positive']:.1f}% positive sentiment")
else:
    st.info("ℹ️ **Balanced Coverage:** No dominant emotional tone")
