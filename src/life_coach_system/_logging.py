"""
Structured logging configuration for Life Coach System.

Call configure_logging() once at application startup (in main()).
Use get_logger(__name__) in every module that needs to log.
"""

import logging

import structlog

from life_coach_system.config import settings


def configure_logging() -> None:
    """Configure structlog for pretty (dev) or JSON (prod) output."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer()
            if settings.debug
            else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.DEBUG if settings.debug else logging.INFO
        ),
        logger_factory=structlog.PrintLoggerFactory(),
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """Return a bound structlog logger for the given module name."""
    return structlog.get_logger(name)
