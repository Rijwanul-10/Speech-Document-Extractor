"""
OCR Provider Interface.

Defines the abstract base class that all OCR providers must
implement. Ensures the document pipeline is decoupled from
any specific OCR engine.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class OCRLine:
    """A single line of text detected by OCR with position and confidence."""

    text: str
    confidence: float = 0.0
    bbox: Optional[list[list[float]]] = None  # Bounding box coordinates


@dataclass
class OCRResult:
    """Complete result from an OCR operation."""

    lines: list[OCRLine] = field(default_factory=list)
    full_text: str = ""
    provider_name: str = ""
    page_number: int = 1

    @property
    def raw_lines(self) -> list[str]:
        """Return just the text strings from all OCR lines."""
        return [line.text for line in self.lines]


class IOCRProvider(ABC):
    """
    Abstract interface for OCR providers.

    All OCR adapters (PaddleOCR, Google Vision, Azure, Mock) must
    implement this interface so the document service can use them
    interchangeably.
    """

    @abstractmethod
    def extract_text(self, image_bytes: bytes) -> OCRResult:
        """
        Extract text from an image.

        Args:
            image_bytes: Raw image file content (JPEG, PNG, etc.).

        Returns:
            OCRResult containing detected text lines with confidence
            scores and bounding boxes.

        Raises:
            ValueError: If the image is invalid or unreadable.
            RuntimeError: If the OCR engine fails internally.
        """
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the name of this provider."""
        ...
