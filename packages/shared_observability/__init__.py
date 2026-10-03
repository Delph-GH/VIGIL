"""
shared_observability

Observability infrastructure for monitoring and logging.

Modules:
- logging: Structured logging with structlog
- metrics: Prometheus metrics collection
- health: Health check system

Provides unified observability for both platforms.
"""

from .logging import (
    StructuredLogger,
    get_logger,
    configure_logging,
    STRUCTLOG_AVAILABLE,
)
from .metrics import (
    MetricsCollector,
    metrics,
    PROMETHEUS_AVAILABLE,
)
from .health import (
    HealthStatus,
    HealthCheck,
    HealthCheckRegistry,
)

__all__ = [
    # Logging
    "StructuredLogger",
    "get_logger",
    "configure_logging",
    "STRUCTLOG_AVAILABLE",
    
    # Metrics
    "MetricsCollector",
    "metrics",
    "PROMETHEUS_AVAILABLE",
    
    # Health
    "HealthStatus",
    "HealthCheck",
    "HealthCheckRegistry",
]
