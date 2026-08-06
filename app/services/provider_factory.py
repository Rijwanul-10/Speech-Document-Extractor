"""
Provider Factory.

Instantiates the correct adapter based on configuration.
Follows the Factory Pattern to decouple service logic from
concrete provider implementations.
"""

import logging

from app.adapters.ocr.base import IOCRProvider
from app.adapters.speech.base import ISpeechProvider
from app.config.settings import get_settings

logger = logging.getLogger(__name__)


def create_speech_provider() -> ISpeechProvider:
    """
    Create and return the configured speech provider.

    Selection is driven by the SPEECH_PROVIDER environment variable.

    Returns:
        ISpeechProvider implementation.

    Raises:
        ValueError: If the configured provider is unknown.
    """
    settings = get_settings()
    provider_name = settings.speech_provider.lower()

    if provider_name == "mock":
        from app.adapters.speech.mock_adapter import MockSpeechAdapter
        logger.info("Using MockSpeechAdapter for speech transcription")
        return MockSpeechAdapter()

    elif provider_name == "whisper":
        from app.adapters.speech.whisper_adapter import WhisperAdapter
        logger.info(
            f"Using WhisperAdapter (model={settings.whisper_model_size}, "
            f"device={settings.whisper_device})"
        )
        return WhisperAdapter(
            model_size=settings.whisper_model_size,
            device=settings.whisper_device,
            compute_type=settings.whisper_compute_type,
        )

    else:
        raise ValueError(
            f"Unknown speech provider: '{provider_name}'. "
            f"Supported: 'mock', 'whisper'"
        )


def create_ocr_provider() -> IOCRProvider:
    """
    Create and return the configured OCR provider.

    Selection is driven by the OCR_PROVIDER environment variable.

    Returns:
        IOCRProvider implementation.

    Raises:
        ValueError: If the configured provider is unknown.
    """
    settings = get_settings()
    provider_name = settings.ocr_provider.lower()

    if provider_name == "mock":
        from app.adapters.ocr.mock_adapter import MockOCRAdapter
        logger.info("Using MockOCRAdapter for OCR")
        return MockOCRAdapter()

    elif provider_name == "paddleocr":
        from app.adapters.ocr.paddleocr_adapter import PaddleOCRAdapter
        logger.info("Using PaddleOCRAdapter for OCR")
        return PaddleOCRAdapter()

    else:
        raise ValueError(
            f"Unknown OCR provider: '{provider_name}'. "
            f"Supported: 'mock', 'paddleocr'"
        )
