"""
FastAPI application factory and entry point.
"""

__all__ = ["create_app", "run"]

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from life_coach_system._logging import configure_logging, get_logger
from life_coach_system.api.routes import chat_router, health_router, session_router
from life_coach_system.config import settings
from life_coach_system.exceptions import LifeCoachError, LLMError, PersistenceError

log = get_logger(__name__)

_FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent.parent / "frontend" / "dist"


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Life Coach System",
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
    )

    # -- CORS (allow Vite dev server in debug mode) --
    if settings.debug:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:5173"],
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # -- Exception handlers --
    @app.exception_handler(LLMError)
    async def _handle_llm_error(_request: Request, exc: LLMError) -> JSONResponse:
        log.error("llm_error", error=str(exc))
        return JSONResponse(status_code=502, content={"detail": str(exc)})

    @app.exception_handler(PersistenceError)
    async def _handle_persistence_error(_request: Request, exc: PersistenceError) -> JSONResponse:
        log.error("persistence_error", error=str(exc))
        return JSONResponse(status_code=500, content={"detail": str(exc)})

    @app.exception_handler(LifeCoachError)
    async def _handle_generic_error(_request: Request, exc: LifeCoachError) -> JSONResponse:
        log.error("app_error", error=str(exc))
        return JSONResponse(status_code=500, content={"detail": str(exc)})

    # -- Routers --
    app.include_router(health_router)
    app.include_router(chat_router)
    app.include_router(session_router)

    # -- Static files (built React frontend) --
    if _FRONTEND_DIST.is_dir():
        app.mount("/", StaticFiles(directory=str(_FRONTEND_DIST), html=True), name="frontend")

    return app


def run() -> None:
    """Entry point for the ``life-coach-api`` console script."""
    import uvicorn

    configure_logging()
    log.info(
        "api_startup",
        model=settings.model_name,
        coach_name=settings.coach_name,
        debug=settings.debug,
        frontend=_FRONTEND_DIST.is_dir(),
    )
    uvicorn.run(
        "life_coach_system.api.app:create_app",
        factory=True,
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
