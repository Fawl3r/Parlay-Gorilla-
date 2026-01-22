"""Structured logging utilities for request tracking."""

import logging
import json
from typing import Any, Dict, Optional
from fastapi import Request


class StructuredLogger:
    """Logger that includes request ID and structured data."""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def _get_request_id(self, request: Optional[Request] = None) -> Optional[str]:
        """Extract request ID from request state."""
        if request and hasattr(request, "state"):
            return getattr(request.state, "request_id", None)
        return None
    
    def _log(self, level: str, message: str, request: Optional[Request] = None, **kwargs):
        """Log with structured data."""
        request_id = self._get_request_id(request)
        log_data = {
            "message": message,
            "request_id": request_id,
            **kwargs
        }
        
        # Format as JSON for structured logging
        log_message = json.dumps(log_data)
        
        if level == "info":
            self.logger.info(log_message)
        elif level == "warning":
            self.logger.warning(log_message)
        elif level == "error":
            self.logger.error(log_message)
        elif level == "debug":
            self.logger.debug(log_message)
        else:
            self.logger.info(log_message)
    
    def info(self, message: str, request: Optional[Request] = None, **kwargs):
        """Log info message."""
        self._log("info", message, request, **kwargs)
    
    def warning(self, message: str, request: Optional[Request] = None, **kwargs):
        """Log warning message."""
        self._log("warning", message, request, **kwargs)
    
    def error(self, message: str, request: Optional[Request] = None, **kwargs):
        """Log error message."""
        self._log("error", message, request, **kwargs)
    
    def debug(self, message: str, request: Optional[Request] = None, **kwargs):
        """Log debug message."""
        self._log("debug", message, request, **kwargs)


def get_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance."""
    return StructuredLogger(name)
