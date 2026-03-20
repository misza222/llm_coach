"""
Project-level exception hierarchy for Life Coach System.

All domain exceptions inherit from LifeCoachError so callers can catch
either the base class or a specific sub-type.
"""

__all__ = [
    "LifeCoachError",
    "ConfigError",
    "LLMError",
    "PersistenceError",
    "EvaluationError",
    "AuthenticationError",
    "AnonymousLimitError",
    "SessionCompletedError",
]


class LifeCoachError(Exception):
    """Base exception for Life Coach System."""


class ConfigError(LifeCoachError):
    """Raised for configuration errors."""


class LLMError(LifeCoachError):
    """Raised when LLM API calls fail."""


class PersistenceError(LifeCoachError):
    """Raised when persistence operations fail."""


class EvaluationError(LifeCoachError):
    """Raised when evaluation fails."""


class AuthenticationError(LifeCoachError):
    """Raised when authentication fails (invalid/expired token)."""


class AnonymousLimitError(LifeCoachError):
    """Raised when an anonymous user exceeds the free message limit."""


class SessionCompletedError(LifeCoachError):
    """Raised when trying to send a message to a completed session."""
