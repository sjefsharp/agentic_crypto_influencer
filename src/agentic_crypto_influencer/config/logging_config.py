"""
Centralized logging configuration for the agentic crypto influencer application.

This module provides a structured logging system with:
- Environment-based log levels
- Structured JSON logging for production
- Console formatting for development
- Proper exception handling and context
- Performance monitoring capabilities
"""

import logging
import logging.config
import os
import sys
from pathlib import Path
from typing import Any, Dict

from src.agentic_crypto_influencer.config.key_constants import REDIS_URL


class StructuredFormatter(logging.Formatter):
    """Custom formatter that adds structured context to log records."""
    
    def format(self, record: logging.LogRecord) -> str:
        # Add context information
        record.service = "agentic-crypto-influencer"
        record.version = "0.1.0"
        
        # Add Redis connectivity status if available
        if hasattr(record, 'redis_connected'):
            record.redis_status = "connected" if record.redis_connected else "disconnected"
        
        return super().format(record)


def get_log_level() -> str:
    """Get log level from environment variable with sensible defaults."""
    env_level = os.getenv("LOG_LEVEL", "INFO").upper()
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    return env_level if env_level in valid_levels else "INFO"


def get_log_format() -> str:
    """Get log format based on environment (structured for production)."""
    is_development = os.getenv("ENVIRONMENT", "development").lower() == "development"
    
    if is_development:
        return (
            "%(asctime)s | %(levelname)-8s | %(name)-20s | "
            "%(funcName)-15s:%(lineno)-3d | %(message)s"
        )
    else:
        # Structured format for production/JSON logging
        return (
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
            '"service": "%(service)s", "version": "%(version)s", '
            '"logger": "%(name)s", "function": "%(funcName)s", '
            '"line": %(lineno)d, "message": "%(message)s"}'
        )


def setup_logging() -> None:
    """
    Configure centralized logging for the entire application.
    
    This function should be called once at application startup.
    """
    log_level = get_log_level()
    log_format = get_log_format()
    
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logging_config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "()": StructuredFormatter,
                "format": log_format,
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "error": {
                "()": StructuredFormatter,
                "format": log_format,
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "standard",
                "stream": sys.stdout,
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "error",
                "filename": "logs/error.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
            },
            "app_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "standard",
                "filename": "logs/app.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
            },
        },
        "loggers": {
            "agentic_crypto_influencer": {
                "level": log_level,
                "handlers": ["console", "app_file", "error_file"],
                "propagate": False,
            },
            # Third-party library loggers
            "autogen": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False,
            },
            "openai": {
                "level": "WARNING", 
                "handlers": ["console"],
                "propagate": False,
            },
            "redis": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False,
            },
            "requests": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False,
            },
        },
        "root": {
            "level": "WARNING",
            "handlers": ["console"],
        },
    }
    
    logging.config.dictConfig(logging_config)
    
    # Log the initialization
    logger = get_logger("config.logging")
    logger.info(
        "Logging system initialized",
        extra={
            "log_level": log_level,
            "environment": os.getenv("ENVIRONMENT", "development"),
            "redis_url_configured": bool(REDIS_URL),
        }
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with consistent naming.
    
    Args:
        name: Logger name, typically module path relative to src/agentic_crypto_influencer
        
    Returns:
        Configured logger instance
        
    Example:
        logger = get_logger("agents.search_agent")
        logger = get_logger("tools.redis_handler")
    """
    # Ensure consistent naming
    if not name.startswith("agentic_crypto_influencer"):
        name = f"agentic_crypto_influencer.{name}"
    
    return logging.getLogger(name)


def log_function_call(func_name: str, **kwargs: Any) -> None:
    """
    Log function calls with parameters for debugging.
    
    Args:
        func_name: Name of the function being called
        **kwargs: Function parameters to log
    """
    logger = get_logger("performance")
    logger.debug(
        f"Function call: {func_name}",
        extra={
            "function": func_name,
            "parameters": {k: str(v)[:100] for k, v in kwargs.items()},  # Truncate long values
        }
    )


def log_api_call(service: str, endpoint: str, status_code: int, duration_ms: float) -> None:
    """
    Log API calls with performance metrics.
    
    Args:
        service: Service name (e.g., "x_api", "google_api", "bitvavo")
        endpoint: API endpoint called
        status_code: HTTP status code
        duration_ms: Request duration in milliseconds
    """
    logger = get_logger("api_calls")
    level = logging.INFO if 200 <= status_code < 400 else logging.ERROR
    
    logger.log(
        level,
        f"API call to {service}",
        extra={
            "service": service,
            "endpoint": endpoint,
            "status_code": status_code,
            "duration_ms": round(duration_ms, 2),
            "success": 200 <= status_code < 400,
        }
    )


class LoggerMixin:
    """
    Mixin class to add logging capabilities to any class.
    
    Usage:
        class MyClass(LoggerMixin):
            def some_method(self):
                self.logger.info("Something happened")
    """
    
    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class."""
        class_name = self.__class__.__module__.replace("src.agentic_crypto_influencer.", "")
        class_name += f".{self.__class__.__name__}"
        return get_logger(class_name)
