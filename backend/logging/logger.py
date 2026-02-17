"""
Structured Logging Framework

Provides JSON-formatted structured logging for the AegisLM backend.
"""

import json
import logging
import sys
import traceback
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID

from backend.core.config import settings


class LogLevel(str, Enum):
    """Log level enumeration."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class StructuredLogger:
    """
    Structured JSON logger for AegisLM.
    
    All logs are emitted as JSON with a consistent schema.
    """

    def __init__(
        self,
        name: str,
        run_id: Optional[UUID] = None,
        component: Optional[str] = None,
    ):
        self.logger = logging.getLogger(name)
        self.run_id = run_id
        self.component = component or name
        
        # Configure logger if not already configured
        if not self.logger.handlers:
            self._configure_logger()

    def _configure_logger(self) -> None:
        """Configure the logger with JSON formatter."""
        # Set level from settings
        level = getattr(logging, settings.log_level.upper(), logging.INFO)
        self.logger.setLevel(level)
        
        # Create handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        
        # Use JSON formatter
        formatter = JSONFormatter()
        handler.setFormatter(formatter)
        
        self.logger.addHandler(handler)
        self.logger.propagate = False

    def _build_log_entry(
        self,
        level: str,
        message: str,
        extra_metadata: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None,
    ) -> Dict[str, Any]:
        """Build structured log entry."""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "run_id": str(self.run_id) if self.run_id else None,
            "component": self.component,
            "message": message,
        }
        
        # Add metadata
        if extra_metadata:
            log_entry["metadata"] = extra_metadata
        
        # Add exception info if provided
        if exception:
            log_entry["exception"] = {
                "type": type(exception).__name__,
                "message": str(exception),
                "traceback": traceback.format_exc(),
            }
        
        return log_entry

    def log(
        self,
        level: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None,
    ) -> None:
        """Emit a log entry."""
        log_entry = self._build_log_entry(level, message, metadata, exception)
        
        # Use standard logging
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        log_method(json.dumps(log_entry))

    def debug(self, message: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Log debug message."""
        self.log(LogLevel.DEBUG.value, message, metadata)

    def info(self, message: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Log info message."""
        self.log(LogLevel.INFO.value, message, metadata)

    def warning(self, message: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Log warning message."""
        self.log(LogLevel.WARNING.value, message, metadata)

    def error(
        self,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None,
    ) -> None:
        """Log error message."""
        self.log(LogLevel.ERROR.value, message, metadata, exception)

    def critical(
        self,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None,
    ) -> None:
        """Log critical message."""
        self.log(LogLevel.CRITICAL.value, message, metadata, exception)

    def set_run_id(self, run_id: UUID) -> None:
        """Set the current run ID for all subsequent logs."""
        self.run_id = run_id

    def bind(self, **kwargs) -> "StructuredLogger":
        """
        Create a new logger with additional bound context.
        
        Returns a new logger instance with merged metadata.
        """
        new_logger = StructuredLogger(
            name=self.logger.name,
            run_id=self.run_id,
            component=self.component,
        )
        return new_logger


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        try:
            # Try to parse the message as JSON
            log_data = json.loads(record.getMessage())
        except (json.JSONDecodeError, ValueError):
            # If not JSON, use as-is
            log_data = {"message": record.getMessage()}

        # Add standard fields
        log_entry = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            **log_data,
        }

        # Add extra fields from record
        if hasattr(record, "run_id") and record.run_id:
            log_entry["run_id"] = record.run_id

        if hasattr(record, "component") and record.component:
            log_entry["component"] = record.component

        if hasattr(record, "metadata") and record.metadata:
            log_entry["metadata"] = record.metadata

        # Add exception info
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
            }

        return json.dumps(log_entry)


# =============================================================================
# Logger factory functions
# =============================================================================

def get_logger(
    name: str,
    run_id: Optional[UUID] = None,
    component: Optional[str] = None,
) -> StructuredLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name (typically __name__)
        run_id: Optional run ID for correlation
        component: Optional component name
        
    Returns:
        StructuredLogger instance
    """
    return StructuredLogger(name, run_id, component)


# Default logger
default_logger = get_logger("aegislm")
