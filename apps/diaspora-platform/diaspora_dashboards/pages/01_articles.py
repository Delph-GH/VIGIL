"""
pages/01_articles.py

Articles Overview page for Diaspora dashboard.
"""

import streamlit as st
from datetime import datetime
import sys
from pathlib import Path

# Add packages to path
packages_path = Path(__file__).parent.parent.parent.parent.parent / "packages"
sys.path.insert(0, str(packages_path))

from shared_dashboards import KPICardBuilder
from shared_observability import get_logger, metrics

logger = get_logger(__name__)

st.set_page_config(page_title="Articles Overview", page_icon="📰", layout="wide")

# Log page view
logger.info('dashboard_view', platform='diaspora', page='articles')
metrics.increment('diaspora_dashboard_views', labels={'page': 'articles'})

st.title("📰 Articles Overview")
st.markdown("View and analyze scraped community articles")

# Filters
col1, col2, col3 = st.columns(3)

with col1:
    date_filter = st.date_input("Date Range Start", datetime.now())

with col2:
    source_filter = st.selectbox("Source", ["All", "Le Petit Journal", "Connexion France"])

with col3:
    quality_filter = st.slider("Min Quality Score", 0, 100, 70)

st.markdown("---")

# Metrics
st.subheader("📊 Article Metrics")

builder = KPICardBuilder()

col1, col2, col3, col4 = st.columns(4)

with col1:
    card = builder.articles_scraped(142, 135)
    st.metric("Total Articles", card.value, f"{card.trend_value:.1f}%")

with col2:
    st.metric("Validated", 138, "97.2%")

with col3:
    st.metric("Avg Quality", "82.5/100", "+2.3")

with col4:
    st.metric("Sources Active", 8, "100%")

st.markdown("---")

# Article list
st.subheader("📑 Recent Articles")

# Sample articles
for i in range(10):
    with st.expander(f"Article {i+1}: Community Event in Munich"):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown("**Source:** Le Petit Journal Munich")
            st.markdown("**Published:** 2024-05-18 10:30")
            st.markdown("**Content:** Upcoming community gathering for French expats...")
            
        with col2:
            st.metric("Quality", "85/100")
            st.metric("Trust", "0.82")
            st.button("View Details", key=f"view_{i}")

st.caption(f"Showing 10 of 142 articles • Page 1 of 15")
