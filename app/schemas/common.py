"""
Common schemas shared across the application.

Provides standardized error and health-check response models
used by all API endpoints.
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standardized error response returned for all API errors."""

    success: bool = Field(default=False, description="Always False for errors")
    error_code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[dict[str, Any]] = Field(
        default=None,
        description="Additional error context",
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC timestamp of the error",
    )


class HealthCheckResponse(BaseModel):
    """Response model for the health-check endpoint."""

    status: str = Field(default="healthy", description="Service status")
    app_name: str = Field(..., description="Application name")
    version: str = Field(..., description="Application version")
    speech_provider: str = Field(..., description="Active speech provider")
    ocr_provider: str = Field(..., description="Active OCR provider")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC timestamp",
    )
