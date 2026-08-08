"""
Document Service.

Orchestrates the medical report extraction pipeline:
validate → convert PDF (if needed) → enhance image → OCR →
preserve raw lines → classify → extract metadata →
extract results → normalize → build response.

This is the service layer — it contains business logic but
never depends on specific provider implementations.
"""

import logging
from typing import Optional

from app.adapters.enhancement.image_enhancer import ImageEnhancer
from app.adapters.ocr.base import IOCRProvider
from app.schemas.document import (
    LabMetadata,
    MedicalReportResponse,
    PatientInfo,
    TestResult,
)
from app.services.provider_factory import create_ocr_provider
from app.utils.file_validator import FileValidator, FileValidationError
from app.utils.metadata_extractor import MetadataExtractor
from app.utils.normalizer import ValueNormalizer
from app.utils.pdf_converter import PDFConverter
from app.utils.report_classifier import ReportClassifier
from app.utils.result_extractor import TestResultExtractor

logger = logging.getLogger(__name__)


class DocumentService:
    """
    Medical document extraction service.

    Validates documents, performs OCR, classifies reports,
    extracts structured data, and normalizes values.
    """

    def __init__(self, provider: Optional[IOCRProvider] = None):
        """
        Initialize the document service.

        Args:
            provider: Optional OCR provider override (for testing).
                      If None, creates one from configuration.
        """
        self._provider = provider or create_ocr_provider()
        self._validator = FileValidator()
        self._enhancer = ImageEnhancer()
        self._pdf_converter = PDFConverter()
        self._classifier = ReportClassifier()
        self._metadata_extractor = MetadataExtractor()
        self._result_extractor = TestResultExtractor()
        self._normalizer = ValueNormalizer()

    async def extract_report(
        self,
        file_bytes: bytes,
        filename: str,
    ) -> MedicalReportResponse:
        """
        Extract structured data from a medical report file.

        Pipeline:
        1. Validate file (type, size, integrity)
        2. Convert PDF to images (if PDF)
        3. Enhance image for OCR
        4. Run OCR
        5. Preserve raw OCR lines
        6. Classify as lab report or not
        7. Extract metadata (patient info, lab info)
        8. Extract test results
        9. Normalize values and units
        10. Build structured response

        Args:
            file_bytes: Raw file content (image or PDF).
            filename: Original filename.

        Returns:
            MedicalReportResponse with structured extraction results.

        Raises:
            FileValidationError: If the file fails validation.
            RuntimeError: If extraction fails.
        """
        logger.info(f"Processing document: {filename} ({len(file_bytes)} bytes)")

        # Step 1: Validate
        file_type = self._validator.validate_document(file_bytes, filename)

        # Step 2: Convert PDF to images if needed
        if file_type == "pdf":
            page_images = self._pdf_converter.convert_to_images(file_bytes)
            page_count = len(page_images)
        else:
            page_images = [file_bytes]
            page_count = 1

        # Process all pages and aggregate results
        all_raw_lines = []
        all_test_results = []
        patient_info_data = None
        lab_metadata_data = None

        for page_num, image_bytes in enumerate(page_images, 1):
            logger.info(f"Processing page {page_num}/{page_count}")

            # Step 3: Enhance image
            try:
                enhanced = self._enhancer.enhance(image_bytes)
            except (ValueError, Exception) as e:
                logger.warning(f"Image enhancement failed for page {page_num}: {e}")
                enhanced = image_bytes  # Fallback to original

            # Step 4: Run OCR
            try:
                ocr_result = self._provider.extract_text(enhanced)
            except ValueError as e:
                raise FileValidationError(str(e), error_code="OCR_ERROR")
            except Exception as e:
                logger.error(f"OCR failed for page {page_num}: {e}")
                raise RuntimeError(f"OCR failed: {e}")

            # Step 5: Preserve raw OCR lines
            raw_lines = ocr_result.raw_lines
            all_raw_lines.extend(raw_lines)

            # Step 7: Extract metadata (from first page)
            if page_num == 1:
                patient_info_data = self._metadata_extractor.extract_patient_info(raw_lines)
                lab_metadata_data = self._metadata_extractor.extract_lab_metadata(raw_lines)

            # Step 8: Extract test results
            page_results = self._result_extractor.extract_results(raw_lines)
            all_test_results.extend(page_results)

        # Step 6: Classify
        classification = self._classifier.classify(all_raw_lines)
        is_valid_lab = classification["is_lab_report"]

        logger.info(
            f"Classification: is_lab_report={is_valid_lab}, "
            f"confidence={classification['confidence']}"
        )

        # If not a valid lab report, return minimal response
        if not is_valid_lab:
            return MedicalReportResponse(
                success=True,
                is_valid_lab_report=False,
                document_type="Non-Laboratory Document",
                language="English",
                patient_info=None,
                lab_metadata=None,
                test_results=[],
                raw_ocr_lines=all_raw_lines,
                page_count=page_count,
                provider=self._provider.provider_name,
                filename=filename,
            )

        # Step 9: Normalize values and build TestResult objects
        normalized_results = []
        for raw_result in all_test_results:
            normalized_name = self._normalizer.normalize_test_name(raw_result.get("test_name")) or raw_result["test_name"]
            normalized_value = self._normalizer.normalize_numeric(raw_result.get("value"))
            normalized_unit = self._normalizer.normalize_unit(raw_result.get("unit"))
            normalized_range = self._normalizer.normalize_reference_range(
                raw_result.get("reference_range")
            )
            flag = self._normalizer.determine_flag(normalized_value, normalized_range)

            normalized_results.append(
                TestResult(
                    test_name=normalized_name,
                    value=normalized_value,
                    unit=normalized_unit,
                    reference_range=normalized_range,
                    flag=flag,
                    raw_line=raw_result["raw_line"],
                )
            )

        # Normalize date in metadata
        if lab_metadata_data and lab_metadata_data.get("report_date"):
            lab_metadata_data["report_date"] = self._normalizer.normalize_date(
                lab_metadata_data["report_date"]
            )

        # Step 10: Build response
        patient_info = PatientInfo(**patient_info_data) if patient_info_data else None
        lab_metadata = LabMetadata(**lab_metadata_data) if lab_metadata_data else None

        response = MedicalReportResponse(
            success=True,
            is_valid_lab_report=True,
            document_type="Medical Laboratory Report",
            language="English",
            patient_info=patient_info,
            lab_metadata=lab_metadata,
            test_results=normalized_results,
            raw_ocr_lines=all_raw_lines,
            page_count=page_count,
            provider=self._provider.provider_name,
            filename=filename,
        )

        logger.info(
            f"Extraction complete: {len(normalized_results)} test results, "
            f"{page_count} pages"
        )

        return response
