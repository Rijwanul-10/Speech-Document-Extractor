"""
Health Check Routes.

Provides a simple health-check endpoint to verify
the service is running and report active configuration.
"""

from fastapi import APIRouter

from app.config.settings import get_settings
from app.schemas.common import HealthCheckResponse

router = APIRouter(prefix="/api/v1", tags=["Health"])


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="Health Check",
    description="Check if the service is running and view active configuration.",
)
async def health_check() -> HealthCheckResponse:
    """Return the current health status and active provider configuration."""
    settings = get_settings()
    return HealthCheckResponse(
        status="healthy",
        app_name=settings.app_name,
        version=settings.app_version,
        speech_provider=settings.speech_provider,
        ocr_provider=settings.ocr_provider,
    )
