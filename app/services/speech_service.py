"""
Speech Service.

Orchestrates the speech transcription pipeline:
validate → select provider → transcribe → build response.

This is the service layer — it contains business logic but
never depends on specific provider implementations.
"""

import logging
from typing import Optional

from app.adapters.speech.base import ISpeechProvider
from app.schemas.speech import (
    SpeechTranscriptionResponse,
    StreamingTranscriptionChunk,
    TranscriptionSegment,
)
from app.services.provider_factory import create_speech_provider
from app.utils.file_validator import FileValidator, FileValidationError

logger = logging.getLogger(__name__)


class SpeechService:
    """
    Speech transcription service.

    Validates audio, delegates to the configured speech provider,
    and returns a structured response.
    """

    def __init__(self, provider: Optional[ISpeechProvider] = None):
        """
        Initialize the speech service.

        Args:
            provider: Optional speech provider override (for testing).
                      If None, creates one from configuration.
        """
        self._provider = provider or create_speech_provider()
        self._validator = FileValidator()

    async def transcribe_file(
        self,
        file_bytes: bytes,
        filename: str,
        language: Optional[str] = None,
    ) -> SpeechTranscriptionResponse:
        """
        Transcribe an uploaded audio file.

        Pipeline:
        1. Validate audio file
        2. Transcribe via provider
        3. Build structured response

        Args:
            file_bytes: Raw audio file content.
            filename: Original filename.
            language: Optional language hint ('en', 'bn').

        Returns:
            SpeechTranscriptionResponse with transcript and metadata.

        Raises:
            FileValidationError: If the file fails validation.
            RuntimeError: If transcription fails.
        """
        # Step 1: Validate
        logger.info(f"Processing speech file: {filename} ({len(file_bytes)} bytes)")
        self._validator.validate_audio(file_bytes, filename)

        # Step 2: Transcribe
        try:
            result = self._provider.transcribe(
                audio_bytes=file_bytes,
                filename=filename,
                language=language,
            )
        except ValueError as e:
            raise FileValidationError(str(e), error_code="INVALID_AUDIO")
        except Exception as e:
            logger.error(f"Speech transcription failed: {e}")
            raise RuntimeError(f"Transcription failed: {e}")

        # Step 3: Build response
        segments = [
            TranscriptionSegment(
                start=seg.start,
                end=seg.end,
                text=seg.text,
                confidence=seg.confidence,
            )
            for seg in result.segments
        ] if result.segments else None

        response = SpeechTranscriptionResponse(
            success=True,
            transcript=result.text,
            language=result.language,
            language_confidence=result.language_confidence,
            duration_seconds=result.duration_seconds,
            segments=segments,
            provider=result.provider_name or self._provider.provider_name,
            filename=filename,
        )

        logger.info(
            f"Transcription complete: lang={result.language}, "
            f"duration={result.duration_seconds}s, "
            f"segments={len(result.segments)}"
        )

        return response

    async def transcribe_stream_chunk(
        self,
        audio_chunk: bytes,
        sample_rate: int = 16000,
        language: Optional[str] = None,
    ) -> StreamingTranscriptionChunk:
        """
        Transcribe a single streaming audio chunk.

        Used for real-time WebSocket microphone transcription.

        Args:
            audio_chunk: Raw PCM audio data.
            sample_rate: Audio sample rate in Hz.
            language: Optional language hint.

        Returns:
            StreamingTranscriptionChunk with partial/final transcript.
        """
        try:
            result = self._provider.transcribe_stream(
                audio_chunk=audio_chunk,
                sample_rate=sample_rate,
                language=language,
            )

            return StreamingTranscriptionChunk(
                type="final",
                text=result.text,
                language=result.language,
                is_final=True,
                confidence=result.language_confidence,
            )

        except Exception as e:
            logger.error(f"Streaming transcription error: {e}")
            return StreamingTranscriptionChunk(
                type="error",
                text=f"Transcription error: {e}",
                is_final=False,
            )
