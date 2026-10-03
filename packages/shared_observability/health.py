"""
shared_observability/health.py

Health check system.

Provides health status for system components.
"""

from typing import Dict, List, Callable, Optional
from enum import Enum
from dataclasses import dataclass
from datetime import datetime


class HealthStatus(Enum):
    """Health status."""
    HEALTHY = 'healthy'
    DEGRADED = 'degraded'
    UNHEALTHY = 'unhealthy'


@dataclass
class HealthCheck:
    """
    Health check result.
    
    Attributes:
        name: Component name
        status: Health status
        message: Status message
        checked_at: Check timestamp
    """
    name: str
    status: HealthStatus
    message: str = ""
    checked_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'status': self.status.value,
            'message': self.message,
            'checked_at': self.checked_at.isoformat() if self.checked_at else None,
        }


class HealthCheckRegistry:
    """
    Registry for health checks.
    
    Usage:
        health = HealthCheckRegistry()
        
        # Register check
        def check_database():
            # Check if DB is accessible
            return HealthCheck('database', HealthStatus.HEALTHY, 'Connected')
        
        health.register('database', check_database)
        
        # Check all
        results = health.check_all()
        
        # Get status
        status = health.get_status()
        print(status)  # HEALTHY, DEGRADED, or UNHEALTHY
    """
    
    def __init__(self):
        """Initialize registry."""
        self.checks: Dict[str, Callable] = {}
    
    def register(self, name: str, check_func: Callable):
        """
        Register health check.
        
        Args:
            name: Check name
            check_func: Function that returns HealthCheck
        """
        self.checks[name] = check_func
    
    def check_all(self) -> List[HealthCheck]:
        """
        Run all health checks.
        
        Returns:
            List of HealthCheck results
        """
        results = []
        
        for name, check_func in self.checks.items():
            try:
                result = check_func()
                result.checked_at = datetime.now()
                results.append(result)
            except Exception as e:
                results.append(HealthCheck(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Check failed: {e}",
                    checked_at=datetime.now(),
                ))
        
        return results
    
    def get_status(self) -> HealthStatus:
        """
        Get overall health status.
        
        Returns:
            Overall HealthStatus
        """
        results = self.check_all()
        
        if not results:
            return HealthStatus.HEALTHY
        
        # If any unhealthy, overall is unhealthy
        if any(r.status == HealthStatus.UNHEALTHY for r in results):
            return HealthStatus.UNHEALTHY
        
        # If any degraded, overall is degraded
        if any(r.status == HealthStatus.DEGRADED for r in results):
            return HealthStatus.DEGRADED
        
        return HealthStatus.HEALTHY
    
    def get_report(self) -> Dict:
        """
        Get health report.
        
        Returns:
            Health report dictionary
        """
        results = self.check_all()
        
        return {
            'status': self.get_status().value,
            'checks': [r.to_dict() for r in results],
            'timestamp': datetime.now().isoformat(),
        }


# Export
__all__ = [
    'HealthStatus',
    'HealthCheck',
    'HealthCheckRegistry',
]
