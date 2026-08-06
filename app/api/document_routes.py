"""
Document Extraction Routes.

Provides the REST endpoint for medical lab report extraction:
- POST /api/v1/document/extract — Upload image or PDF
"""

import logging
from typing import Optional

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas.common import ErrorResponse
from app.schemas.document import MedicalReportResponse
from app.services.document_service import DocumentService
from app.utils.file_validator import FileValidationError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/document", tags=["Document Extraction"])

# Lazily initialized service instance
_document_service: Optional[DocumentService] = None


def _get_service() -> DocumentService:
    """Get or create the document service singleton."""
    global _document_service
    if _document_service is None:
        _document_service = DocumentService()
    return _document_service


@router.post(
    "/extract",
    response_model=MedicalReportResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Extract Medical Lab Report",
    description=(
        "Upload a medical laboratory report image or PDF for extraction. "
        "Supports JPEG, PNG, BMP, TIFF, WebP images and PDF documents. "
        "Returns structured patient info, lab metadata, and test results."
    ),
)
async def extract_document(
    file: UploadFile = File(
        ...,
        description="Medical report image or PDF to extract data from",
    ),
) -> MedicalReportResponse:
    """
    Extract structured data from a medical laboratory report.

    The service validates the file, enhances the image, runs OCR,
    classifies the document, and extracts structured data including
    patient info, lab metadata, and test results with normalized values.
    """
    try:
        file_bytes = await file.read()
        filename = file.filename or "document.png"

        service = _get_service()
        result = await service.extract_report(
            file_bytes=file_bytes,
            filename=filename,
        )

        return result

    except FileValidationError as e:
        logger.warning(f"Validation error: {e.message}")
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error_code": e.error_code,
                "message": e.message,
            },
        )
    except RuntimeError as e:
        logger.error(f"Extraction error: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error_code": "EXTRACTION_ERROR",
                "message": str(e),
            },
        )
    except Exception as e:
        logger.exception(f"Unexpected error in document extraction: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error_code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred during extraction.",
            },
        )
