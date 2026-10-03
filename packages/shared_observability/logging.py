"""
shared_observability/logging.py

Structured logging with structlog.

Provides unified logging interface for both platforms.
"""

import logging
import sys
from typing import Optional, Dict, Any

# Optional dependency
try:
    import structlog
    STRUCTLOG_AVAILABLE = True
except ImportError:
    STRUCTLOG_AVAILABLE = False
    structlog = None


class StructuredLogger:
    """
    Structured logging wrapper.
    
    Provides consistent structured logging across platforms using structlog.
    Falls back to standard logging if structlog is not available.
    
    Usage:
        from shared_observability import get_logger
        
        logger = get_logger('my_module')
        
        logger.info('event_occurred', user_id='123', action='login')
        logger.error('error_occurred', error='Something failed', traceback=tb)
        
        # With context
        logger = logger.bind(request_id='req_123')
        logger.info('processing_request')
    """
    
    def __init__(self, name: str, use_structlog: bool = True):
        """
        Initialize logger.
        
        Args:
            name: Logger name (usually module name)
            use_structlog: Use structlog if available
        """
        self.name = name
        
        if use_structlog and STRUCTLOG_AVAILABLE:
            self.logger = structlog.get_logger(name)
            self._is_structured = True
        else:
            self.logger = logging.getLogger(name)
            self._is_structured = False
    
    def debug(self, event: str, **kwargs):
        """Log debug message."""
        if self._is_structured:
            self.logger.debug(event, **kwargs)
        else:
            self.logger.debug(self._format_message(event, kwargs))
    
    def info(self, event: str, **kwargs):
        """Log info message."""
        if self._is_structured:
            self.logger.info(event, **kwargs)
        else:
            self.logger.info(self._format_message(event, kwargs))
    
    def warning(self, event: str, **kwargs):
        """Log warning message."""
        if self._is_structured:
            self.logger.warning(event, **kwargs)
        else:
            self.logger.warning(self._format_message(event, kwargs))
    
    def error(self, event: str, **kwargs):
        """Log error message."""
        if self._is_structured:
            self.logger.error(event, **kwargs)
        else:
            self.logger.error(self._format_message(event, kwargs))
    
    def critical(self, event: str, **kwargs):
        """Log critical message."""
        if self._is_structured:
            self.logger.critical(event, **kwargs)
        else:
            self.logger.critical(self._format_message(event, kwargs))
    
    def bind(self, **kwargs) -> 'StructuredLogger':
        """
        Bind context to logger.
        
        Args:
            **kwargs: Context to bind
            
        Returns:
            New logger with bound context
        """
        if self._is_structured:
            new_logger = StructuredLogger(self.name)
            new_logger.logger = self.logger.bind(**kwargs)
            new_logger._is_structured = True
            return new_logger
        else:
            # Standard logging doesn't support binding
            return self
    
    def _format_message(self, event: str, kwargs: Dict[str, Any]) -> str:
        """Format message for standard logging."""
        if not kwargs:
            return event
        
        parts = [event]
        for key, value in kwargs.items():
            parts.append(f"{key}={value}")
        
        return " | ".join(parts)


def configure_logging(
    level: str = 'INFO',
    json_output: bool = False,
    console_output: bool = True,
):
    """
    Configure logging for application.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_output: Output logs as JSON
        console_output: Output to console
    """
    if STRUCTLOG_AVAILABLE:
        # Configure structlog
        processors = [
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
        ]
        
        if json_output:
            processors.append(structlog.processors.JSONRenderer())
        else:
            processors.append(structlog.dev.ConsoleRenderer())
        
        structlog.configure(
            processors=processors,
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
    
    # Configure standard logging
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout) if console_output else logging.NullHandler()
        ],
    )


def get_logger(name: str) -> StructuredLogger:
    """
    Get logger for module.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        StructuredLogger instance
    """
    return StructuredLogger(name)


# Export
__all__ = [
    'StructuredLogger',
    'get_logger',
    'configure_logging',
    'STRUCTLOG_AVAILABLE',
]
