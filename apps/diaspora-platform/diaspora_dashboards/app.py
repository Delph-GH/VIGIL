"""
apps/diaspora-platform/diaspora_dashboards/app.py

Main Diaspora Dashboard Application

Integrated with all shared foundation packages.
"""

import streamlit as st
from datetime import datetime
import sys
from pathlib import Path

# Add packages to path
packages_path = Path(__file__).parent.parent.parent.parent / "packages"
sys.path.insert(0, str(packages_path))

# Import shared components
from shared_dashboards import KPICardBuilder, TrustGaugeBuilder, TimelineChartBuilder
from shared_observability import get_logger, metrics
from shared_types import ScrapedArticle

# Initialize logger
logger = get_logger(__name__)

# Page config
st.set_page_config(
    page_title="Diaspora Intelligence Dashboard",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    .status-success {
        color: #28a745;
        font-weight: 600;
    }
    .status-warning {
        color: #ffc107;
        font-weight: 600;
    }
    .status-danger {
        color: #dc3545;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


def main():
    """Main dashboard application."""
    
    # Log page view
    logger.info('dashboard_view', platform='diaspora', page='home')
    metrics.increment('diaspora_dashboard_views', labels={'page': 'home'})
    
    # Header
    st.markdown('<h1 class="main-header">🌍 Diaspora Intelligence Dashboard</h1>', 
                unsafe_allow_html=True)
    st.markdown("**Expat Community Intelligence Platform**")
    
    # Sidebar
    with st.sidebar:
        st.header("Diaspora Intelligence")
        st.caption("Pages are listed above. Values shown are demo data.")
        st.markdown("---")
        st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    # Main content
    render_home_dashboard()


def render_home_dashboard():
    """Render home dashboard with KPIs and overview."""
    
    # KPI Cards
    st.subheader("📊 Key Metrics")
    
    kpi_builder = KPICardBuilder()
    
    # Create sample KPI cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        card = kpi_builder.articles_scraped(count=142, previous_count=135)
        render_kpi_card(card)
    
    with col2:
        card = kpi_builder.trust_score(score=0.78, threshold=0.7)
        render_kpi_card(card)
    
    with col3:
        card = kpi_builder.quality_score(score=82.5, threshold=70.0)
        render_kpi_card(card)
    
    with col4:
        card = kpi_builder.narrative_count(count=8, emerging=2)
        render_kpi_card(card)
    
    st.markdown("---")
    
    # Trust Gauges
    st.subheader("🎯 Trust & Quality Indicators")
    
    gauge_builder = TrustGaugeBuilder()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        gauge = gauge_builder.source_trust("Le Petit Journal", 0.82)
        render_trust_gauge(gauge)
    
    with col2:
        gauge = gauge_builder.article_quality(82.5)
        render_trust_gauge(gauge)
    
    with col3:
        gauge = gauge_builder.system_health(0.95)
        render_trust_gauge(gauge)
    
    st.markdown("---")
    
    # Timeline
    st.subheader("📈 Article Volume Trend")
    
    timeline_builder = TimelineChartBuilder()
    
    # Sample data
    article_counts = {
        '2024-05-14': 128,
        '2024-05-15': 135,
        '2024-05-16': 142,
        '2024-05-17': 138,
        '2024-05-18': 145,
    }
    
    chart = timeline_builder.article_volume(article_counts)
    render_timeline_chart(chart)
    
    st.markdown("---")
    
    # Recent Activity
    st.subheader("📰 Recent Activity")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("**Latest Articles**")
        for i in range(5):
            with st.container():
                st.markdown(f"**Article {i+1}:** Community event announcement")
                st.caption(f"Source: Le Petit Journal • Quality: 85/100")
                st.markdown("---")
    
    with col2:
        st.markdown("**System Status**")
        st.success("✅ All systems operational")
        st.info("📊 Last scrape: 15 minutes ago")
        st.info("🔄 Next scheduled: in 45 minutes")
    
    # Footer
    st.markdown("---")
    st.caption("Diaspora Intelligence Platform • Powered by 11 shared foundation packages")


def render_kpi_card(card):
    """Render a KPI card."""
    
    # Determine status color
    status_class = f"status-{card.status.value}"
    
    # Trend arrow
    trend_arrow = ""
    if card.trend_direction.value == 'up':
        trend_arrow = "↗️"
    elif card.trend_direction.value == 'down':
        trend_arrow = "↘️"
    elif card.trend_direction.value == 'stable':
        trend_arrow = "→"
    
    trend_text = (f"{trend_arrow} {card.trend_value:+.1f}%"
                  if card.trend_value is not None else "&nbsp;")

    # Render
    st.markdown(f"""
    <div class="metric-card">
        <div style="font-size: 0.9rem; color: #666; margin-bottom: 0.5rem;">
            {card.title}
        </div>
        <div style="font-size: 2rem; font-weight: 700; margin-bottom: 0.5rem;">
            {card.value} <span style="font-size: 1rem; color: #666;">{card.unit}</span>
        </div>
        <div class="{status_class}">
            {trend_text}
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_trust_gauge(gauge):
    """Render a trust gauge."""
    
    gauge_data = gauge.to_dict()
    percentage = gauge_data['percentage']
    color = gauge_data['color']
    
    st.markdown(f"""
    <div class="metric-card" style="text-align: center;">
        <div style="font-size: 0.9rem; color: #666; margin-bottom: 1rem;">
            {gauge.label}
        </div>
        <div style="font-size: 3rem; font-weight: 700; color: {color};">
            {percentage:.0f}%
        </div>
        <div style="font-size: 0.9rem; color: {color}; font-weight: 600;">
            {gauge_data['status']}
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_timeline_chart(chart):
    """Render a timeline chart."""
    
    # Simple line chart using Streamlit
    chart_data = {}
    
    for event in chart.events:
        chart_data[event.timestamp] = event.value
    
    st.line_chart(chart_data)


if __name__ == "__main__":
    main()
