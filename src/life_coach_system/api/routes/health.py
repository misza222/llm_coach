"""
Health check endpoint.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1", tags=["health"])


@router.get("/health")
def health_check() -> dict[str, str]:
    """Liveness check."""
    return {"status": "ok"}
