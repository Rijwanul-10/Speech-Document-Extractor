"""
File Validator.

Validates uploaded files for type, size, content integrity,
and format-specific checks (e.g., audio corruption detection).
"""

import io
import logging
from pathlib import Path
from typing import Optional

from app.config.settings import get_settings

logger = logging.getLogger(__name__)


class FileValidationError(Exception):
    """Raised when file validation fails."""

    def __init__(self, message: str, error_code: str = "VALIDATION_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class FileValidator:
    """Validates uploaded files before processing."""

    def __init__(self):
        self.settings = get_settings()

    def validate_audio(self, file_bytes: bytes, filename: str) -> None:
        """
        Validate an audio file.

        Checks: non-empty, supported extension, size limit, basic corruption.

        Args:
            file_bytes: Raw file content.
            filename: Original filename.

        Raises:
            FileValidationError: If validation fails.
        """
        self._check_empty(file_bytes, filename)
        self._check_extension(filename, self.settings.supported_audio_extensions, "audio")
        self._check_size(file_bytes, filename)
        self._check_audio_integrity(file_bytes, filename)

    def validate_document(self, file_bytes: bytes, filename: str) -> str:
        """
        Validate a document file (image or PDF).

        Returns the detected file type: 'image' or 'pdf'.

        Args:
            file_bytes: Raw file content.
            filename: Original filename.

        Returns:
            'image' or 'pdf' indicating the document type.

        Raises:
            FileValidationError: If validation fails.
        """
        self._check_empty(file_bytes, filename)
        self._check_size(file_bytes, filename)

        ext = Path(filename).suffix.lower()
        all_supported = (
            self.settings.supported_image_extensions
            + self.settings.supported_document_extensions
        )

        if ext not in all_supported:
            raise FileValidationError(
                f"Unsupported file format '{ext}'. "
                f"Supported formats: {', '.join(all_supported)}",
                error_code="UNSUPPORTED_FORMAT",
            )

        if ext in self.settings.supported_document_extensions:
            self._check_pdf_integrity(file_bytes, filename)
            return "pdf"
        else:
            self._check_image_integrity(file_bytes, filename)
            return "image"

    def _check_empty(self, file_bytes: bytes, filename: str) -> None:
        """Reject empty files."""
        if not file_bytes or len(file_bytes) == 0:
            raise FileValidationError(
                f"File '{filename}' is empty.",
                error_code="EMPTY_FILE",
            )

    def _check_extension(
        self, filename: str, allowed: list[str], file_type: str,
    ) -> None:
        """Reject files with unsupported extensions."""
        ext = Path(filename).suffix.lower()
        if ext not in allowed:
            raise FileValidationError(
                f"Unsupported {file_type} format '{ext}'. "
                f"Supported: {', '.join(allowed)}",
                error_code="UNSUPPORTED_FORMAT",
            )

    def _check_size(self, file_bytes: bytes, filename: str) -> None:
        """Reject files exceeding the maximum size."""
        max_bytes = self.settings.max_file_size_bytes
        if len(file_bytes) > max_bytes:
            size_mb = len(file_bytes) / (1024 * 1024)
            raise FileValidationError(
                f"File '{filename}' is {size_mb:.1f} MB, "
                f"exceeding the {self.settings.max_file_size_mb} MB limit.",
                error_code="FILE_TOO_LARGE",
            )

    def _check_audio_integrity(self, file_bytes: bytes, filename: str) -> None:
        """Basic audio file corruption check using magic bytes."""
        ext = Path(filename).suffix.lower()

        # Check magic bytes for common audio formats
        magic_checks = {
            ".wav": (b"RIFF", b"WAVE"),
            ".mp3": (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2", b"ID3"),
            ".flac": (b"fLaC",),
            ".ogg": (b"OggS",),
        }

        if ext in magic_checks:
            valid_headers = magic_checks[ext]
            if not any(file_bytes[:12].find(header) != -1 for header in valid_headers):
                raise FileValidationError(
                    f"File '{filename}' appears to be corrupted "
                    f"(invalid {ext} file header).",
                    error_code="CORRUPTED_FILE",
                )

    def _check_image_integrity(self, file_bytes: bytes, filename: str) -> None:
        """Basic image corruption check using magic bytes."""
        magic_checks = {
            b"\xff\xd8\xff": "JPEG",
            b"\x89PNG\r\n\x1a\n": "PNG",
            b"BM": "BMP",
            b"II\x2a\x00": "TIFF (little-endian)",
            b"MM\x00\x2a": "TIFF (big-endian)",
            b"RIFF": "WebP",
        }

        for magic, fmt in magic_checks.items():
            if file_bytes[:len(magic)] == magic:
                logger.debug(f"Detected image format: {fmt}")
                return

        # If we couldn't detect format from magic bytes, warn but allow
        logger.warning(
            f"Could not verify image format for '{filename}' from magic bytes, "
            f"proceeding anyway"
        )

    def _check_pdf_integrity(self, file_bytes: bytes, filename: str) -> None:
        """Basic PDF corruption check."""
        if not file_bytes[:5] == b"%PDF-":
            raise FileValidationError(
                f"File '{filename}' is not a valid PDF file.",
                error_code="CORRUPTED_FILE",
            )
