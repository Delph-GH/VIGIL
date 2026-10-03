"""
shared_dashboards/components/timeline_chart.py

Timeline chart visualization component.

Provides temporal data visualization for articles, narratives, and events.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class TimelineEvent:
    """
    Timeline event data point.
    
    Attributes:
        timestamp: Event timestamp
        value: Event value
        label: Event label
        category: Event category
        metadata: Additional metadata
    """
    timestamp: str
    value: float
    label: str
    category: Optional[str] = None
    metadata: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'timestamp': self.timestamp,
            'value': self.value,
            'label': self.label,
            'category': self.category,
            'metadata': self.metadata or {},
        }


@dataclass
class TimelineChart:
    """
    Timeline chart data structure.
    
    Attributes:
        title: Chart title
        events: List of timeline events
        x_label: X-axis label
        y_label: Y-axis label
        categories: Optional category colors
    """
    title: str
    events: List[TimelineEvent]
    x_label: str = 'Time'
    y_label: str = 'Value'
    categories: Optional[Dict[str, str]] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for rendering."""
        return {
            'title': self.title,
            'events': [e.to_dict() for e in self.events],
            'x_label': self.x_label,
            'y_label': self.y_label,
            'categories': self.categories or {},
        }
    
    def get_date_range(self) -> tuple:
        """Get date range of timeline."""
        if not self.events:
            return None, None
        
        timestamps = [e.timestamp for e in self.events]
        return min(timestamps), max(timestamps)
    
    def filter_by_category(self, category: str) -> 'TimelineChart':
        """Filter events by category."""
        filtered_events = [e for e in self.events if e.category == category]
        
        return TimelineChart(
            title=f"{self.title} - {category}",
            events=filtered_events,
            x_label=self.x_label,
            y_label=self.y_label,
            categories=self.categories,
        )


class TimelineChartBuilder:
    """
    Builder for creating timeline charts.
    
    Usage:
        builder = TimelineChartBuilder()
        
        # Article volume over time
        chart = builder.article_volume(
            articles=[...],
        )
        
        # Trust score over time
        chart = builder.trust_timeline(
            trust_data=[...],
        )
        
        # Narrative evolution
        chart = builder.narrative_evolution(
            narrative_data=[...],
        )
    """
    
    def article_volume(
        self,
        article_counts: Dict[str, int],
    ) -> TimelineChart:
        """
        Create article volume timeline.
        
        Args:
            article_counts: Dict of {timestamp: count}
            
        Returns:
            TimelineChart
        """
        events = []
        
        for timestamp, count in sorted(article_counts.items()):
            events.append(TimelineEvent(
                timestamp=timestamp,
                value=count,
                label=f"{count} articles",
                category='volume',
            ))
        
        return TimelineChart(
            title='Article Volume Over Time',
            events=events,
            x_label='Date',
            y_label='Article Count',
        )
    
    def trust_timeline(
        self,
        trust_scores: Dict[str, float],
        source_name: Optional[str] = None,
    ) -> TimelineChart:
        """
        Create trust score timeline.
        
        Args:
            trust_scores: Dict of {timestamp: score}
            source_name: Optional source name
            
        Returns:
            TimelineChart
        """
        events = []
        
        for timestamp, score in sorted(trust_scores.items()):
            events.append(TimelineEvent(
                timestamp=timestamp,
                value=score,
                label=f"Trust: {score:.2f}",
                category='trust',
            ))
        
        title = 'Trust Score Over Time'
        if source_name:
            title = f"{source_name} Trust Over Time"
        
        return TimelineChart(
            title=title,
            events=events,
            x_label='Date',
            y_label='Trust Score',
        )
    
    def narrative_evolution(
        self,
        narrative_strengths: Dict[str, Dict[str, float]],
    ) -> TimelineChart:
        """
        Create narrative evolution timeline.
        
        Args:
            narrative_strengths: Dict of {timestamp: {narrative_id: strength}}
            
        Returns:
            TimelineChart
        """
        events = []
        
        # Collect all narrative IDs
        all_narratives = set()
        for narratives in narrative_strengths.values():
            all_narratives.update(narratives.keys())
        
        # Create events
        for timestamp, narratives in sorted(narrative_strengths.items()):
            for narrative_id, strength in narratives.items():
                events.append(TimelineEvent(
                    timestamp=timestamp,
                    value=strength,
                    label=narrative_id,
                    category=narrative_id,
                ))
        
        return TimelineChart(
            title='Narrative Evolution Over Time',
            events=events,
            x_label='Date',
            y_label='Narrative Strength',
        )
    
    def salience_timeline(
        self,
        salience_scores: Dict[str, float],
    ) -> TimelineChart:
        """
        Create salience score timeline.
        
        Args:
            salience_scores: Dict of {timestamp: score}
            
        Returns:
            TimelineChart
        """
        events = []
        
        for timestamp, score in sorted(salience_scores.items()):
            events.append(TimelineEvent(
                timestamp=timestamp,
                value=score,
                label=f"Salience: {score:.2f}",
                category='salience',
            ))
        
        return TimelineChart(
            title='Article Salience Over Time',
            events=events,
            x_label='Date',
            y_label='Salience Score',
        )
    
    def custom(
        self,
        title: str,
        events: List[TimelineEvent],
        x_label: str = 'Time',
        y_label: str = 'Value',
        categories: Optional[Dict[str, str]] = None,
    ) -> TimelineChart:
        """
        Create custom timeline chart.
        
        Args:
            title: Chart title
            events: Timeline events
            x_label: X-axis label
            y_label: Y-axis label
            categories: Category colors
            
        Returns:
            TimelineChart
        """
        return TimelineChart(
            title=title,
            events=events,
            x_label=x_label,
            y_label=y_label,
            categories=categories,
        )


# Export
__all__ = [
    'TimelineEvent',
    'TimelineChart',
    'TimelineChartBuilder',
]
