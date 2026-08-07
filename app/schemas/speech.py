"""
Speech pipeline schemas.

Defines the response models for speech transcription results,
including file upload and streaming transcription responses.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TranscriptionSegment(BaseModel):
    """A single transcription segment with timing information."""

    start: float = Field(..., description="Segment start time in seconds")
    end: float = Field(..., description="Segment end time in seconds")
    text: str = Field(..., description="Transcribed text for this segment")
    confidence: Optional[float] = Field(
        default=None,
        description="Confidence score (0.0 - 1.0)",
    )


class SpeechTranscriptionResponse(BaseModel):
    """Complete response for a speech transcription request."""

    success: bool = Field(default=True, description="Whether transcription succeeded")
    transcript: str = Field(..., description="Full transcription text")
    language: str = Field(..., description="Detected or specified language code")
    detected_language: Optional[str] = Field(
        default=None,
        description="Human-readable detected language name (e.g. 'English', 'বাংলা')",
    )
    language_code: Optional[str] = Field(
        default=None,
        description="ISO 639-1 language code (e.g. 'en', 'bn')",
    )
    language_confidence: Optional[float] = Field(
        default=None,
        description="Language detection confidence (0.0 - 1.0)",
    )
    duration_seconds: Optional[float] = Field(
        default=None,
        description="Audio duration in seconds",
    )
    segments: Optional[list[TranscriptionSegment]] = Field(
        default=None,
        description="Individual transcription segments with timing",
    )
    provider: str = Field(..., description="Provider used for transcription")
    filename: Optional[str] = Field(
        default=None,
        description="Original filename if uploaded",
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC timestamp of the response",
    )


class StreamingTranscriptionChunk(BaseModel):
    """A single chunk from a streaming transcription session."""

    type: str = Field(
        ...,
        description="Chunk type: 'partial', 'final', 'error', 'info'",
    )
    text: str = Field(default="", description="Transcribed text")
    language: Optional[str] = Field(
        default=None,
        description="Detected language code",
    )
    is_final: bool = Field(
        default=False,
        description="Whether this is a finalized segment",
    )
    confidence: Optional[float] = Field(
        default=None,
        description="Confidence score (0.0 - 1.0)",
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC timestamp",
    )
