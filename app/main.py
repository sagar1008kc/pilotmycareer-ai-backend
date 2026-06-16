"""FastAPI application entrypoint for the Pilot My Career AI backend."""

from __future__ import annotations

import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.router import api_router
from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging, get_logger

configure_logging()
logger = get_logger("app.main")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        docs_url="/docs",
        openapi_url="/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    @app.get("/", include_in_schema=False)
    async def root() -> dict:
        return {
            "name": settings.app_name,
            "version": __version__,
            "status": "ok",
            "docs": "/docs",
            "health": f"{settings.api_prefix}/health",
            "api_prefix": settings.api_prefix,
        }

    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.api_prefix)

    logger.info(
        "Application started",
        extra={"model": settings.openai_model, "provider": settings.llm_provider},
    )
    return app


app = create_app()
