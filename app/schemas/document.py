"""
Medical document pipeline schemas.

Defines the response models for medical lab report extraction,
including patient info, lab metadata, test results, and
the complete structured report response.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class PatientInfo(BaseModel):
    """Extracted patient information from a medical report."""

    name: Optional[str] = Field(default=None, description="Patient name")
    age: Optional[str] = Field(default=None, description="Patient age")
    sex: Optional[str] = Field(default=None, description="Patient sex/gender")
    patient_id: Optional[str] = Field(default=None, description="Patient ID if present")


class LabMetadata(BaseModel):
    """Laboratory metadata extracted from a medical report."""

    lab_name: Optional[str] = Field(default=None, description="Laboratory name")
    report_date: Optional[str] = Field(default=None, description="Report date")
    reference_number: Optional[str] = Field(
        default=None,
        description="Report reference/accession number",
    )
    referring_doctor: Optional[str] = Field(
        default=None,
        description="Referring doctor if mentioned",
    )


class TestResult(BaseModel):
    """A single laboratory test result with normalized values."""

    test_name: str = Field(..., description="Name of the laboratory test")
    value: Optional[str] = Field(default=None, description="Measured value")
    unit: Optional[str] = Field(default=None, description="Unit of measurement")
    reference_range: Optional[str] = Field(
        default=None,
        description="Normal reference range",
    )
    flag: Optional[str] = Field(
        default=None,
        description="Abnormality flag: 'high', 'low', 'normal', or None",
    )
    raw_line: str = Field(
        ...,
        description="Original OCR text line this result was extracted from",
    )


class MedicalReportResponse(BaseModel):
    """Complete response for a medical report extraction request."""

    success: bool = Field(
        default=True,
        description="Whether extraction succeeded",
    )
    is_valid_lab_report: bool = Field(
        ...,
        description="Whether the document is a valid laboratory report",
    )
    patient_info: Optional[PatientInfo] = Field(
        default=None,
        description="Extracted patient information",
    )
    lab_metadata: Optional[LabMetadata] = Field(
        default=None,
        description="Extracted laboratory metadata",
    )
    test_results: list[TestResult] = Field(
        default_factory=list,
        description="Extracted test results",
    )
    raw_ocr_lines: list[str] = Field(
        default_factory=list,
        description="All raw OCR text lines as detected",
    )
    page_count: int = Field(default=1, description="Number of pages processed")
    provider: str = Field(..., description="OCR provider used")
    filename: Optional[str] = Field(
        default=None,
        description="Original filename if uploaded",
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC timestamp of the response",
    )
