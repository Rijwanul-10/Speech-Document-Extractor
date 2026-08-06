"""
Speech Provider Interface.

Defines the abstract base class that all speech transcription
providers must implement. This ensures provider independence —
business logic depends only on this interface, never on
specific provider SDKs.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TranscriptSegment:
    """A single segment of a transcription with timing."""

    start: float
    end: float
    text: str
    confidence: Optional[float] = None


@dataclass
class TranscriptResult:
    """Result returned by any speech provider."""

    text: str
    language: str
    language_confidence: Optional[float] = None
    duration_seconds: Optional[float] = None
    segments: list[TranscriptSegment] = field(default_factory=list)
    provider_name: str = ""


class ISpeechProvider(ABC):
    """
    Abstract interface for speech transcription providers.

    All speech adapters (Whisper, OpenAI API, Azure, Mock) must
    implement this interface so the service layer can use them
    interchangeably.
    """

    @abstractmethod
    def transcribe(
        self,
        audio_bytes: bytes,
        filename: str = "audio.wav",
        language: Optional[str] = None,
    ) -> TranscriptResult:
        """
        Transcribe audio bytes into text.

        Args:
            audio_bytes: Raw audio file content.
            filename: Original filename (used to determine format).
            language: Optional language hint (e.g., 'bn', 'en').

        Returns:
            TranscriptResult with transcription text, detected language,
            duration, and segments.

        Raises:
            ValueError: If the audio is invalid or corrupted.
            RuntimeError: If the provider fails internally.
        """
        ...

    @abstractmethod
    def transcribe_stream(
        self,
        audio_chunk: bytes,
        sample_rate: int = 16000,
        language: Optional[str] = None,
    ) -> TranscriptResult:
        """
        Transcribe a streaming audio chunk.

        Used for real-time microphone transcription via WebSocket.

        Args:
            audio_chunk: A chunk of raw PCM audio data.
            sample_rate: Audio sample rate in Hz.
            language: Optional language hint.

        Returns:
            TranscriptResult for this chunk.
        """
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the name of this provider."""
        ...
