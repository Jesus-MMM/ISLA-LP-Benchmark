"""
Logging configuration for the LP solver.

This module provides a centralized logging system with configurable levels.
"""

import logging
import sys
from enum import Enum


class LogLevel(Enum):
    """Log level enumeration matching Python logging."""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


_default_level = LogLevel.WARNING


def get_logger(name: str, level: LogLevel | None = None) -> logging.Logger:
    """
    Get a configured logger instance.

    Args:
        name: Logger name (typically __name__)
        level: Log level (defaults to WARNING)

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)

    if level is None:
        level = _default_level

    logger.setLevel(level.value)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level.value)

        formatter = logging.Formatter(
            "%(asctime)s | %(name)s | %(levelname)s | %(message)s",
            datefmt="%H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def set_default_level(level: LogLevel) -> None:
    """Set the default log level for all new loggers."""
    global _default_level
    _default_level = level


def debug(logger: logging.Logger, message: str) -> None:
    """Log a debug message."""
    logger.debug(message)


def info(logger: logging.Logger, message: str) -> None:
    """Log an info message."""
    logger.info(message)


def warning(logger: logging.Logger, message: str) -> None:
    """Log a warning message."""
    logger.warning(message)


def error(logger: logging.Logger, message: str) -> None:
    """Log an error message."""
    logger.error(message)


def critical(logger: logging.Logger, message: str) -> None:
    """Log a critical message."""
    logger.critical(message)
