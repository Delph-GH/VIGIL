"""
shared_dashboards/components/trust_gauge.py

Trust gauge visualization component.

Provides visual representation of trust/reliability scores.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class TrustGauge:
    """
    Trust gauge data structure.
    
    Attributes:
        value: Trust score (0-1)
        label: Gauge label
        thresholds: List of (value, color, label) thresholds
        min_value: Minimum value (default: 0)
        max_value: Maximum value (default: 1)
        description: Optional description
    """
    value: float
    label: str
    thresholds: Optional[List[Tuple[float, str, str]]] = None
    min_value: float = 0.0
    max_value: float = 1.0
    description: Optional[str] = None
    
    def __post_init__(self):
        """Set default thresholds if not provided."""
        if self.thresholds is None:
            self.thresholds = [
                (0.0, '#dc3545', 'Low Trust'),      # Red
                (0.4, '#ffc107', 'Medium Trust'),   # Yellow
                (0.7, '#28a745', 'High Trust'),     # Green
            ]
    
    def get_color(self) -> str:
        """
        Get color for current value based on thresholds.
        
        Returns:
            Color hex code
        """
        color = self.thresholds[0][1]  # Default to first threshold
        
        for threshold_value, threshold_color, _ in sorted(self.thresholds, reverse=True):
            if self.value >= threshold_value:
                color = threshold_color
                break
        
        return color
    
    def get_status_label(self) -> str:
        """
        Get status label for current value.
        
        Returns:
            Status label
        """
        label = self.thresholds[0][2]  # Default to first threshold
        
        for threshold_value, _, threshold_label in sorted(self.thresholds, reverse=True):
            if self.value >= threshold_value:
                label = threshold_label
                break
        
        return label
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for rendering."""
        return {
            'value': self.value,
            'label': self.label,
            'color': self.get_color(),
            'status': self.get_status_label(),
            'min_value': self.min_value,
            'max_value': self.max_value,
            'description': self.description,
            'percentage': (self.value / self.max_value) * 100,
        }


class TrustGaugeBuilder:
    """
    Builder for creating trust gauges.
    
    Usage:
        builder = TrustGaugeBuilder()
        
        # Source trust gauge
        gauge = builder.source_trust(
            source_name='Le Monde',
            trust_score=0.85,
        )
        
        # Article quality gauge
        gauge = builder.article_quality(
            quality_score=78.5,
        )
        
        # Custom gauge
        gauge = builder.custom(
            label='System Health',
            value=0.95,
        )
    """
    
    def source_trust(
        self,
        source_name: str,
        trust_score: float,
    ) -> TrustGauge:
        """
        Create source trust gauge.
        
        Args:
            source_name: Source name
            trust_score: Trust score (0-1)
            
        Returns:
            TrustGauge
        """
        return TrustGauge(
            value=trust_score,
            label=f"{source_name} Trust",
            description=f"Reliability score for {source_name}",
        )
    
    def article_quality(
        self,
        quality_score: float,
    ) -> TrustGauge:
        """
        Create article quality gauge.
        
        Args:
            quality_score: Quality score (0-100)
            
        Returns:
            TrustGauge
        """
        # Convert to 0-1 scale
        normalized_score = quality_score / 100.0
        
        return TrustGauge(
            value=normalized_score,
            label='Article Quality',
            thresholds=[
                (0.0, '#dc3545', 'Poor'),
                (0.6, '#ffc107', 'Fair'),
                (0.8, '#28a745', 'Excellent'),
            ],
            description=f"Quality score: {quality_score}/100",
        )
    
    def narrative_strength(
        self,
        strength_score: float,
    ) -> TrustGauge:
        """
        Create narrative strength gauge.
        
        Args:
            strength_score: Strength score (0-1)
            
        Returns:
            TrustGauge
        """
        return TrustGauge(
            value=strength_score,
            label='Narrative Strength',
            thresholds=[
                (0.0, '#6c757d', 'Weak'),
                (0.3, '#ffc107', 'Moderate'),
                (0.6, '#28a745', 'Strong'),
            ],
            description='Narrative prominence and consistency',
        )
    
    def system_health(
        self,
        health_score: float,
    ) -> TrustGauge:
        """
        Create system health gauge.
        
        Args:
            health_score: Health score (0-1)
            
        Returns:
            TrustGauge
        """
        return TrustGauge(
            value=health_score,
            label='System Health',
            thresholds=[
                (0.0, '#dc3545', 'Unhealthy'),
                (0.5, '#ffc107', 'Degraded'),
                (0.9, '#28a745', 'Healthy'),
            ],
            description='Overall system status',
        )
    
    def custom(
        self,
        label: str,
        value: float,
        thresholds: Optional[List[Tuple[float, str, str]]] = None,
        min_value: float = 0.0,
        max_value: float = 1.0,
        description: Optional[str] = None,
    ) -> TrustGauge:
        """
        Create custom trust gauge.
        
        Args:
            label: Gauge label
            value: Value
            thresholds: Custom thresholds
            min_value: Minimum value
            max_value: Maximum value
            description: Description
            
        Returns:
            TrustGauge
        """
        return TrustGauge(
            value=value,
            label=label,
            thresholds=thresholds,
            min_value=min_value,
            max_value=max_value,
            description=description,
        )


# Export
__all__ = [
    'TrustGauge',
    'TrustGaugeBuilder',
]
