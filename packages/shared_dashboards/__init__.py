"""
shared_dashboards

Reusable dashboard visualization components.

Provides consistent visualization across both platforms.
"""

from .components import (
    # KPI Cards
    KPICard,
    KPICardBuilder,
    TrendDirection,
    MetricStatus,
    format_kpi_value,
    
    # Trust Gauge
    TrustGauge,
    TrustGaugeBuilder,
    
    # Timeline Chart
    TimelineEvent,
    TimelineChart,
    TimelineChartBuilder,
)

__all__ = [
    # KPI Cards
    "KPICard",
    "KPICardBuilder",
    "TrendDirection",
    "MetricStatus",
    "format_kpi_value",
    
    # Trust Gauge
    "TrustGauge",
    "TrustGaugeBuilder",
    
    # Timeline Chart
    "TimelineEvent",
    "TimelineChart",
    "TimelineChartBuilder",
]
