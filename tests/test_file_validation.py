"""
Unit tests for FileValidator.
"""

import pytest
from app.utils.file_validator import FileValidator, FileValidationError


def test_validate_empty_audio():
    validator = FileValidator()
    with pytest.raises(FileValidationError) as exc:
        validator.validate_audio(b"", "test.wav")
    assert exc.value.error_code == "EMPTY_FILE"


def test_validate_unsupported_audio_extension():
    validator = FileValidator()
    with pytest.raises(FileValidationError) as exc:
        validator.validate_audio(b"some bytes", "test.txt")
    assert exc.value.error_code == "UNSUPPORTED_FORMAT"


def test_validate_oversized_file():
    validator = FileValidator()
    # Mock settings max file size to 1MB for test
    validator.settings.max_file_size_mb = 1
    large_bytes = b"0" * (2 * 1024 * 1024)

    with pytest.raises(FileValidationError) as exc:
        validator.validate_audio(large_bytes, "test.wav")
    assert exc.value.error_code == "FILE_TOO_LARGE"


def test_validate_document_image():
    validator = FileValidator()
    # PNG magic header
    png_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
    doc_type = validator.validate_document(png_bytes, "report.png")
    assert doc_type == "image"


def test_validate_document_pdf():
    validator = FileValidator()
    pdf_bytes = b"%PDF-1.4 header and content"
    doc_type = validator.validate_document(pdf_bytes, "report.pdf")
    assert doc_type == "pdf"
