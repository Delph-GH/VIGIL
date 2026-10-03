"""
shared_observability/metrics.py

Prometheus metrics collection.

Provides unified metrics interface for both platforms.
"""

from typing import Dict, List, Optional
from collections import defaultdict

# Optional dependency
try:
    from prometheus_client import Counter, Gauge, Histogram, Summary, Info
    from prometheus_client import CollectorRegistry, generate_latest
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    Counter = None
    Gauge = None
    Histogram = None


class MetricsCollector:
    """
    Metrics collection with Prometheus.
    
    Provides simple interface for collecting application metrics.
    Falls back to in-memory tracking if Prometheus is not available.
    
    Usage:
        from shared_observability import metrics
        
        # Counter
        metrics.increment('articles_scraped', labels={'source': 'Le Monde'})
        
        # Gauge
        metrics.set_gauge('queue_size', 42)
        
        # Histogram (timing)
        with metrics.timer('scrape_duration'):
            scrape_articles()
        
        # Or manually
        metrics.observe('scrape_duration', 1.5)
    """
    
    def __init__(self, use_prometheus: bool = True):
        """
        Initialize metrics collector.
        
        Args:
            use_prometheus: Use Prometheus if available
        """
        self._use_prometheus = use_prometheus and PROMETHEUS_AVAILABLE
        
        if self._use_prometheus:
            self.registry = CollectorRegistry()
            self._counters: Dict[str, Counter] = {}
            self._gauges: Dict[str, Gauge] = {}
            self._histograms: Dict[str, Histogram] = {}
        else:
            # Fallback to in-memory
            self._counter_values = defaultdict(float)
            self._gauge_values = {}
            self._histogram_values = defaultdict(list)
    
    def increment(
        self,
        name: str,
        value: float = 1.0,
        labels: Optional[Dict[str, str]] = None,
        help_text: Optional[str] = None,
    ):
        """
        Increment counter metric.
        
        Args:
            name: Metric name
            value: Increment value
            labels: Label values
            help_text: Metric description
        """
        if self._use_prometheus:
            # Get or create counter
            if name not in self._counters:
                label_names = list(labels.keys()) if labels else []
                self._counters[name] = Counter(
                    name,
                    help_text or f"Counter: {name}",
                    labelnames=label_names,
                    registry=self.registry,
                )
            
            # Increment
            if labels:
                self._counters[name].labels(**labels).inc(value)
            else:
                self._counters[name].inc(value)
        else:
            # Fallback
            key = self._make_key(name, labels)
            self._counter_values[key] += value
    
    def set_gauge(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
        help_text: Optional[str] = None,
    ):
        """
        Set gauge metric.
        
        Args:
            name: Metric name
            value: Gauge value
            labels: Label values
            help_text: Metric description
        """
        if self._use_prometheus:
            # Get or create gauge
            if name not in self._gauges:
                label_names = list(labels.keys()) if labels else []
                self._gauges[name] = Gauge(
                    name,
                    help_text or f"Gauge: {name}",
                    labelnames=label_names,
                    registry=self.registry,
                )
            
            # Set
            if labels:
                self._gauges[name].labels(**labels).set(value)
            else:
                self._gauges[name].set(value)
        else:
            # Fallback
            key = self._make_key(name, labels)
            self._gauge_values[key] = value
    
    def observe(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
        help_text: Optional[str] = None,
        buckets: Optional[List[float]] = None,
    ):
        """
        Observe histogram metric.
        
        Args:
            name: Metric name
            value: Observed value
            labels: Label values
            help_text: Metric description
            buckets: Histogram buckets
        """
        if self._use_prometheus:
            # Get or create histogram
            if name not in self._histograms:
                label_names = list(labels.keys()) if labels else []
                self._histograms[name] = Histogram(
                    name,
                    help_text or f"Histogram: {name}",
                    labelnames=label_names,
                    buckets=buckets,
                    registry=self.registry,
                )
            
            # Observe
            if labels:
                self._histograms[name].labels(**labels).observe(value)
            else:
                self._histograms[name].observe(value)
        else:
            # Fallback
            key = self._make_key(name, labels)
            self._histogram_values[key].append(value)
    
    def timer(self, name: str, labels: Optional[Dict[str, str]] = None):
        """
        Context manager for timing operations.
        
        Args:
            name: Metric name
            labels: Label values
            
        Returns:
            Timer context manager
        """
        return MetricTimer(self, name, labels)
    
    def get_metrics(self) -> str:
        """
        Get metrics in Prometheus format.
        
        Returns:
            Metrics string
        """
        if self._use_prometheus:
            return generate_latest(self.registry).decode('utf-8')
        else:
            # Fallback: return simple text format
            lines = []
            
            # Counters
            for key, value in self._counter_values.items():
                lines.append(f"counter_{key} {value}")
            
            # Gauges
            for key, value in self._gauge_values.items():
                lines.append(f"gauge_{key} {value}")
            
            # Histograms
            for key, values in self._histogram_values.items():
                if values:
                    avg = sum(values) / len(values)
                    lines.append(f"histogram_{key}_avg {avg}")
                    lines.append(f"histogram_{key}_count {len(values)}")
            
            return "\n".join(lines)
    
    def _make_key(self, name: str, labels: Optional[Dict[str, str]]) -> str:
        """Make key for fallback storage."""
        if not labels:
            return name
        
        label_str = "_".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}_{label_str}"


class MetricTimer:
    """Context manager for timing operations."""
    
    def __init__(
        self,
        collector: MetricsCollector,
        name: str,
        labels: Optional[Dict[str, str]] = None,
    ):
        self.collector = collector
        self.name = name
        self.labels = labels
        self.start_time = None
    
    def __enter__(self):
        import time
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        import time
        duration = time.time() - self.start_time
        self.collector.observe(self.name, duration, self.labels)


# Global metrics instance
metrics = MetricsCollector()


# Export
__all__ = [
    'MetricsCollector',
    'metrics',
    'PROMETHEUS_AVAILABLE',
]
