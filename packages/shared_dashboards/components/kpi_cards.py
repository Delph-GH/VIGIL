"""
shared_dashboards/components/kpi_cards.py

KPI card components for dashboard metrics display.

Provides consistent metric visualization across both platforms.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class TrendDirection(Enum):
    """Trend direction indicator."""
    UP = 'up'
    DOWN = 'down'
    STABLE = 'stable'
    UNKNOWN = 'unknown'


class MetricStatus(Enum):
    """Metric status for color coding."""
    SUCCESS = 'success'    # Green
    WARNING = 'warning'    # Yellow
    DANGER = 'danger'      # Red
    INFO = 'info'          # Blue
    NEUTRAL = 'neutral'    # Gray


@dataclass
class KPICard:
    """
    KPI card data structure.
    
    Attributes:
        title: Card title
        value: Current metric value
        unit: Value unit (e.g., '%', 'articles', 'score')
        trend_direction: Trend direction
        trend_value: Trend percentage or value
        status: Metric status for color coding
        description: Optional description
        sparkline_data: Optional data for sparkline
        timestamp: Last update timestamp
    """
    title: str
    value: float
    unit: str = ''
    trend_direction: TrendDirection = TrendDirection.UNKNOWN
    trend_value: Optional[float] = None
    status: MetricStatus = MetricStatus.NEUTRAL
    description: Optional[str] = None
    sparkline_data: Optional[List[float]] = None
    timestamp: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for rendering."""
        return {
            'title': self.title,
            'value': self.value,
            'unit': self.unit,
            'trend_direction': self.trend_direction.value,
            'trend_value': self.trend_value,
            'status': self.status.value,
            'description': self.description,
            'sparkline_data': self.sparkline_data,
            'timestamp': self.timestamp,
        }


class KPICardBuilder:
    """
    Builder for creating KPI cards with smart defaults.
    
    Usage:
        builder = KPICardBuilder()
        
        # Article count card
        card = builder.articles_scraped(
            count=150,
            previous_count=140,
        )
        
        # Trust score card
        card = builder.trust_score(
            score=0.85,
            threshold=0.7,
        )
        
        # Custom card
        card = builder.custom(
            title='Active Users',
            value=1234,
            unit='users',
            trend_value=5.2,
            trend_direction=TrendDirection.UP,
        )
    """
    
    def articles_scraped(
        self,
        count: int,
        previous_count: Optional[int] = None,
        timestamp: Optional[str] = None,
    ) -> KPICard:
        """
        Create articles scraped KPI card.
        
        Args:
            count: Current article count
            previous_count: Previous count for trend
            timestamp: Timestamp
            
        Returns:
            KPICard
        """
        trend_direction = TrendDirection.UNKNOWN
        trend_value = None
        status = MetricStatus.INFO
        
        if previous_count is not None and previous_count > 0:
            change = count - previous_count
            trend_value = (change / previous_count) * 100
            
            if change > 0:
                trend_direction = TrendDirection.UP
                status = MetricStatus.SUCCESS
            elif change < 0:
                trend_direction = TrendDirection.DOWN
                status = MetricStatus.WARNING
            else:
                trend_direction = TrendDirection.STABLE
        
        return KPICard(
            title='Articles Scraped',
            value=count,
            unit='articles',
            trend_direction=trend_direction,
            trend_value=trend_value,
            status=status,
            timestamp=timestamp,
        )
    
    def trust_score(
        self,
        score: float,
        threshold: float = 0.7,
        timestamp: Optional[str] = None,
    ) -> KPICard:
        """
        Create trust score KPI card.
        
        Args:
            score: Trust score (0-1)
            threshold: Threshold for status
            timestamp: Timestamp
            
        Returns:
            KPICard
        """
        # Determine status based on threshold
        if score >= threshold:
            status = MetricStatus.SUCCESS
        elif score >= threshold * 0.8:
            status = MetricStatus.WARNING
        else:
            status = MetricStatus.DANGER
        
        return KPICard(
            title='Average Trust Score',
            value=score,
            unit='',
            status=status,
            description=f"Threshold: {threshold}",
            timestamp=timestamp,
        )
    
    def quality_score(
        self,
        score: float,
        threshold: float = 70.0,
        timestamp: Optional[str] = None,
    ) -> KPICard:
        """
        Create quality score KPI card.
        
        Args:
            score: Quality score (0-100)
            threshold: Threshold for status
            timestamp: Timestamp
            
        Returns:
            KPICard
        """
        if score >= threshold:
            status = MetricStatus.SUCCESS
        elif score >= threshold * 0.8:
            status = MetricStatus.WARNING
        else:
            status = MetricStatus.DANGER
        
        return KPICard(
            title='Average Quality Score',
            value=score,
            unit='/100',
            status=status,
            timestamp=timestamp,
        )
    
    def narrative_count(
        self,
        count: int,
        emerging: int = 0,
        timestamp: Optional[str] = None,
    ) -> KPICard:
        """
        Create narrative count KPI card.
        
        Args:
            count: Total narrative count
            emerging: Number of emerging narratives
            timestamp: Timestamp
            
        Returns:
            KPICard
        """
        status = MetricStatus.INFO
        
        if emerging > 0:
            status = MetricStatus.SUCCESS
        
        description = None
        if emerging > 0:
            description = f"{emerging} emerging"
        
        return KPICard(
            title='Active Narratives',
            value=count,
            unit='narratives',
            status=status,
            description=description,
            timestamp=timestamp,
        )
    
    def custom(
        self,
        title: str,
        value: float,
        unit: str = '',
        trend_direction: TrendDirection = TrendDirection.UNKNOWN,
        trend_value: Optional[float] = None,
        status: MetricStatus = MetricStatus.NEUTRAL,
        description: Optional[str] = None,
        sparkline_data: Optional[List[float]] = None,
        timestamp: Optional[str] = None,
    ) -> KPICard:
        """
        Create custom KPI card.
        
        Args:
            title: Card title
            value: Metric value
            unit: Value unit
            trend_direction: Trend direction
            trend_value: Trend value
            status: Status
            description: Description
            sparkline_data: Sparkline data
            timestamp: Timestamp
            
        Returns:
            KPICard
        """
        return KPICard(
            title=title,
            value=value,
            unit=unit,
            trend_direction=trend_direction,
            trend_value=trend_value,
            status=status,
            description=description,
            sparkline_data=sparkline_data,
            timestamp=timestamp,
        )


def format_kpi_value(value: float, unit: str = '') -> str:
    """
    Format KPI value for display.
    
    Args:
        value: Value to format
        unit: Unit string
        
    Returns:
        Formatted string
    """
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M{unit}"
    elif value >= 1_000:
        return f"{value / 1_000:.1f}K{unit}"
    elif isinstance(value, float) and value < 10:
        return f"{value:.2f}{unit}"
    else:
        return f"{value:.0f}{unit}"


# Export
__all__ = [
    'KPICard',
    'KPICardBuilder',
    'TrendDirection',
    'MetricStatus',
    'format_kpi_value',
]
