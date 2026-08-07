"""
FastAPI Application Entry Point.

Creates the FastAPI application, registers routers, configures
CORS, exception handlers, and startup logging.
"""

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.document_routes import router as document_router
from app.api.health_routes import router as health_router
from app.api.speech_routes import router as speech_router
from app.config.settings import get_settings


def _setup_logging() -> None:
    """Configure application logging."""
    settings = get_settings()
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    settings = get_settings()
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info(f"  {settings.app_name} v{settings.app_version}")
    logger.info(f"  Speech Provider : {settings.speech_provider}")
    logger.info(f"  OCR Provider    : {settings.ocr_provider}")
    logger.info(f"  Debug Mode      : {settings.debug}")
    logger.info(f"  Max File Size   : {settings.max_file_size_mb} MB")
    logger.info("=" * 60)
    yield
    logger.info("Application shutting down...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    _setup_logging()
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description=(
            "AI backend service for **Speech Transcription** (Bengali & English) "
            "and **Medical Laboratory Report Extraction**.\n\n"
            "## Features\n"
            "- 🎤 Audio file transcription (WAV, MP3, FLAC, OGG, etc.)\n"
            "- 🎙️ Real-time microphone transcription via WebSocket\n"
            "- 🏥 Medical lab report extraction from images and PDFs\n"
            "- 🔄 Automatic language detection (Bengali / English)\n"
            "- 📊 Structured JSON output with normalized values\n\n"
            "## Providers\n"
            f"- Speech: **{settings.speech_provider}**\n"
            f"- OCR: **{settings.ocr_provider}**"
        ),
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    app.include_router(health_router)
    app.include_router(speech_router)
    app.include_router(document_router)

    # Root route redirect to docs
    @app.get("/", include_in_schema=False)
    async def root_redirect():
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/docs")

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Catch-all exception handler returning structured JSON."""
        logger = logging.getLogger(__name__)
        logger.exception(f"Unhandled exception: {exc}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error_code": "INTERNAL_ERROR",
                "message": "An unexpected internal error occurred.",
            },
        )

    return app


# Application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
