"""
Faster-Whisper Speech Adapter.

Integrates faster-whisper for speech transcription, supporting
both Bengali and English language recognition with automatic language
detection and segment timing.
"""

import io
import logging
import tempfile
from typing import Optional

from app.adapters.speech.base import ISpeechProvider, TranscriptResult, TranscriptSegment

logger = logging.getLogger(__name__)


_VALID_WHISPER_LANGUAGES: set[str] = {
    "af", "am", "ar", "as", "az", "ba", "be", "bg", "bn", "bo", "br", "bs", "ca", "cs", "cy", "da", "de",
    "el", "en", "es", "et", "eu", "fa", "fi", "fo", "fr", "gl", "gu", "ha", "haw", "he", "hi", "hr", "ht",
    "hu", "hy", "id", "is", "it", "ja", "jw", "ka", "kk", "km", "kn", "ko", "la", "lb", "ln", "lo", "lt",
    "lv", "mg", "mi", "mk", "ml", "mn", "mr", "ms", "mt", "my", "ne", "nl", "nn", "no", "oc", "pa", "pl",
    "ps", "pt", "ro", "ru", "sa", "sd", "si", "sk", "sl", "sn", "so", "sq", "sr", "su", "sv", "sw", "ta",
    "te", "tg", "th", "tk", "tl", "tr", "tt", "uk", "ur", "uz", "vi", "yi", "yo", "zh", "yue",
}


def sanitize_language(language: Optional[str]) -> Optional[str]:
    """
    Sanitize and validate language code.

    Converts Swagger/OpenAPI default placeholder strings ('string', 'auto', 'null', 'none')
    or invalid language strings to None so Whisper performs auto-detection.
    """
    if not language:
        return None
    cleaned = str(language).strip().lower()
    if cleaned in ("string", "auto", "none", "null", "undefined", ""):
        return None
    if cleaned in _VALID_WHISPER_LANGUAGES:
        return cleaned
    logger.warning(f"Unrecognized language code '{language}', falling back to auto-detection.")
    return None


class WhisperAdapter(ISpeechProvider):
    """
    Faster-Whisper implementation of ISpeechProvider.

    Uses faster-whisper (CTranslate2 binding for Whisper) for fast,
    local speech transcription.
    """

    def __init__(
        self,
        model_size: str = "base",
        device: str = "cpu",
        compute_type: str = "int8",
    ):
        """
        Initialize the Whisper model.

        Args:
            model_size: Whisper model size (tiny, base, small, medium, large-v2, etc.).
            device: 'cpu' or 'cuda'.
            compute_type: Quantization compute type (int8, float16, float32).
        """
        self._model_size = model_size
        self._device = device
        self._compute_type = compute_type
        self._model = None

    def _load_model(self):
        """Lazy load the Whisper model on first transcription request."""
        if self._model is None:
            try:
                from faster_whisper import WhisperModel

                logger.info(
                    f"Loading Faster-Whisper model '{self._model_size}' "
                    f"on {self._device} ({self._compute_type})..."
                )
                self._model = WhisperModel(
                    self._model_size,
                    device=self._device,
                    compute_type=self._compute_type,
                )
                logger.info("Faster-Whisper model loaded successfully.")
            except ImportError:
                raise RuntimeError(
                    "faster-whisper is not installed. "
                    "Install it using `pip install faster-whisper`."
                )
            except Exception as e:
                logger.error(f"Failed to load Faster-Whisper model: {e}")
                raise RuntimeError(f"Failed to load Whisper model: {e}")

    @property
    def provider_name(self) -> str:
        return f"whisper-{self._model_size}"

    def transcribe(
        self,
        audio_bytes: bytes,
        filename: str = "audio.wav",
        language: Optional[str] = None,
    ) -> TranscriptResult:
        """
        Transcribe audio bytes using Faster-Whisper.

        Saves bytes to a temporary file, processes through Whisper,
        and collects segments and language metadata.
        """
        if not audio_bytes:
            raise ValueError("Empty audio file provided")

        self._load_model()

        lang = sanitize_language(language)

        # Save audio bytes to temporary file for whisper processing
        suffix = f".{filename.split('.')[-1]}" if "." in filename else ".wav"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=True) as temp_audio:
            temp_audio.write(audio_bytes)
            temp_audio.flush()

            try:
                segments_raw, info = self._model.transcribe(
                    temp_audio.name,
                    language=lang,
                    beam_size=5,
                    best_of=5,
                    vad_filter=True,  # Filter out silence
                )

                segments = []
                full_text_parts = []

                for seg in segments_raw:
                    segments.append(
                        TranscriptSegment(
                            start=round(seg.start, 2),
                            end=round(seg.end, 2),
                            text=seg.text.strip(),
                            confidence=round(getattr(seg, "avg_logprob", 0.0), 4),
                        )
                    )
                    full_text_parts.append(seg.text.strip())

                full_text = " ".join(full_text_parts)

                return TranscriptResult(
                    text=full_text,
                    language=info.language,
                    language_confidence=round(info.language_probability, 4),
                    duration_seconds=round(info.duration, 2),
                    segments=segments,
                    provider_name=self.provider_name,
                )

            except Exception as e:
                logger.error(f"Error during Whisper transcription: {e}")
                raise RuntimeError(f"Whisper transcription failed: {e}")

    def transcribe_stream(
        self,
        audio_chunk: bytes,
        sample_rate: int = 16000,
        language: Optional[str] = None,
    ) -> TranscriptResult:
        """
        Transcribe a chunk of streaming audio using Faster-Whisper.
        """
        return self.transcribe(audio_chunk, filename="stream.raw", language=language)
