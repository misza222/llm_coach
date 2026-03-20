"""
FastAPI application factory and entry point.
"""

__all__ = ["create_app", "run"]

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from life_coach_system._logging import configure_logging, get_logger
from life_coach_system.api.routes import auth_router, chat_router, health_router, session_router
from life_coach_system.config import settings
from life_coach_system.exceptions import (
    AnonymousLimitError,
    AuthenticationError,
    LifeCoachError,
    LLMError,
    PersistenceError,
    SessionCompletedError,
)

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

    # -- Session middleware (required by Authlib OAuth) --
    app.add_middleware(SessionMiddleware, secret_key=settings.jwt_secret)

    # -- CORS (allow Vite dev server in debug mode) --
    if settings.debug:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:5173"],
            allow_methods=["*"],
            allow_headers=["*"],
            allow_credentials=True,
        )

    # -- Exception handlers --
    @app.exception_handler(AuthenticationError)
    async def _handle_auth_error(_request: Request, exc: AuthenticationError) -> JSONResponse:
        log.warning("auth_error", error=str(exc))
        return JSONResponse(status_code=401, content={"detail": str(exc)})

    @app.exception_handler(AnonymousLimitError)
    async def _handle_anon_limit(_request: Request, exc: AnonymousLimitError) -> JSONResponse:
        log.info("anonymous_limit_reached", error=str(exc))
        return JSONResponse(status_code=403, content={"detail": str(exc)})

    @app.exception_handler(SessionCompletedError)
    async def _handle_session_completed(
        _request: Request, exc: SessionCompletedError
    ) -> JSONResponse:
        log.info("session_completed_rejected", error=str(exc))
        return JSONResponse(status_code=409, content={"detail": str(exc)})

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
    app.include_router(auth_router)
    app.include_router(chat_router)
    app.include_router(session_router)

    # -- Dev UI (Gradio, debug mode only) --
    if settings.debug:
        try:
            import importlib.util
            import sys

            import gradio as gr

            dev_ui_path = Path(__file__).resolve().parent.parent.parent.parent / "dev_ui.py"
            if dev_ui_path.exists():
                spec = importlib.util.spec_from_file_location("_dev_ui", dev_ui_path)
                if spec and spec.loader:
                    mod = importlib.util.module_from_spec(spec)
                    sys.modules["_dev_ui"] = mod
                    spec.loader.exec_module(mod)
                    app = gr.mount_gradio_app(app, mod.demo, path="/devui")
                    log.info("dev_ui_mounted", path="/devui")
            else:
                log.info("dev_ui_skipped", reason="dev_ui.py not found")
        except ImportError:
            log.info("dev_ui_skipped", reason="gradio not installed")

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
