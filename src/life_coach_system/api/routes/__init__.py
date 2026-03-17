"""
API route modules.
"""

__all__ = ["auth_router", "chat_router", "health_router", "session_router"]

from life_coach_system.api.routes.auth import router as auth_router
from life_coach_system.api.routes.chat import router as chat_router
from life_coach_system.api.routes.health import router as health_router
from life_coach_system.api.routes.sessions import router as session_router
