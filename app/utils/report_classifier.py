"""
Report Classifier.

Classifies OCR text as a valid laboratory report or a non-laboratory
document. Uses keyword/pattern matching against known lab test fields
and report structure indicators.
"""

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


# Keywords that strongly indicate a laboratory report
_LAB_REPORT_INDICATORS = [
    # Report type headers
    "laboratory report",
    "lab report",
    "pathology report",
    "diagnostic report",
    "investigation report",
    "test report",
    "medical report",

    # Common test section headers
    "complete blood count",
    "cbc",
    "differential count",
    "liver function",
    "renal function",
    "lipid profile",
    "blood sugar",
    "thyroid function",
    "urine analysis",
    "urinalysis",
    "hematology",
    "biochemistry",
    "serology",
    "immunology",
    "blood group",

    # Common test names
    "hemoglobin",
    "haemoglobin",
    "rbc count",
    "wbc count",
    "platelet",
    "hematocrit",
    "pcv",
    "mcv",
    "mch",
    "mchc",
    "esr",
    "neutrophils",
    "lymphocytes",
    "monocytes",
    "eosinophils",
    "basophils",
    "bilirubin",
    "sgpt",
    "sgot",
    "alt",
    "ast",
    "alkaline phosphatase",
    "total protein",
    "albumin",
    "globulin",
    "creatinine",
    "blood urea",
    "urea nitrogen",
    "bun",
    "uric acid",
    "cholesterol",
    "triglycerides",
    "hdl",
    "ldl",
    "vldl",
    "fasting blood sugar",
    "fbs",
    "hba1c",
    "tsh",
    "t3",
    "t4",
    "sodium",
    "potassium",
    "chloride",
    "calcium",
    "phosphorus",
]

# Keywords indicating non-laboratory documents
_NON_LAB_INDICATORS = [
    "prescription",
    "rx:",
    "tab.",
    "capsule",
    "syrup",
    "injection",
    "discharge summary",
    "admission note",
    "progress note",
    "operative note",
    "consent form",
    "insurance claim",
    "invoice",
    "receipt",
    "bill",
]

# Structural patterns in lab reports
_LAB_STRUCTURE_PATTERNS = [
    # "value unit reference-range" pattern
    r'\d+\.?\d*\s*(mg|g|u|iu|mmol|umol|meq|ng|pg|ug|mcg|ml|dl|l|fl|%)',
    # Reference range pattern "X - Y" or "< X" or "> X"
    r'(\d+\.?\d*\s*-\s*\d+\.?\d*|[<>]\s*\d+\.?\d*)',
    # Unit patterns
    r'(mg/dL|g/dL|U/L|IU/L|mmol/L|mEq/L|/cumm|/uL|million/uL|mm/hr|fL|pg)',
]


class ReportClassifier:
    """
    Classifies OCR text as a valid laboratory report or not.

    Uses a scoring system based on:
    - Lab report keyword matches
    - Non-lab keyword matches (negative scoring)
    - Structural patterns (value-unit-range lines)
    """

    def __init__(self, threshold: float = 3.0):
        """
        Initialize the classifier.

        Args:
            threshold: Minimum score to classify as a lab report.
        """
        self.threshold = threshold

    def classify(self, ocr_lines: list[str]) -> dict:
        """
        Classify the OCR text as lab report or non-lab document.

        Args:
            ocr_lines: List of raw OCR text lines.

        Returns:
            Dict with 'is_lab_report', 'confidence', 'lab_indicators_found',
            and 'reason'.
        """
        if not ocr_lines:
            return {
                "is_lab_report": False,
                "confidence": 0.0,
                "lab_indicators_found": [],
                "reason": "No OCR text provided",
            }

        full_text = "\n".join(ocr_lines).lower()

        # Count lab indicators
        lab_score = 0.0
        lab_indicators_found = []

        for indicator in _LAB_REPORT_INDICATORS:
            if indicator.lower() in full_text:
                lab_score += 1.0
                lab_indicators_found.append(indicator)

        # Count non-lab indicators (negative scoring)
        non_lab_score = 0.0
        for indicator in _NON_LAB_INDICATORS:
            if indicator.lower() in full_text:
                non_lab_score += 1.5  # Weight non-lab indicators more

        # Check structural patterns
        structural_matches = 0
        for line in ocr_lines:
            for pattern in _LAB_STRUCTURE_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    structural_matches += 1
                    break

        # Structural matches contribute to score
        structural_score = min(structural_matches * 0.5, 5.0)

        # Final score
        total_score = lab_score + structural_score - non_lab_score

        # Determine confidence (0.0 - 1.0)
        confidence = min(max(total_score / 15.0, 0.0), 1.0)

        is_lab_report = total_score >= self.threshold

        reason = self._build_reason(
            is_lab_report, lab_score, non_lab_score,
            structural_score, lab_indicators_found,
        )

        logger.info(
            f"Report classification: is_lab={is_lab_report}, "
            f"score={total_score:.1f}, confidence={confidence:.2f}"
        )

        return {
            "is_lab_report": is_lab_report,
            "confidence": round(confidence, 2),
            "lab_indicators_found": lab_indicators_found,
            "reason": reason,
        }

    def _build_reason(
        self,
        is_lab: bool,
        lab_score: float,
        non_lab_score: float,
        structural_score: float,
        indicators: list[str],
    ) -> str:
        """Build a human-readable classification reason."""
        if is_lab:
            top_indicators = indicators[:5]
            return (
                f"Classified as laboratory report. "
                f"Found {len(indicators)} lab indicators "
                f"({', '.join(top_indicators)}{'...' if len(indicators) > 5 else ''}). "
                f"Structural score: {structural_score:.1f}."
            )
        else:
            if non_lab_score > 0:
                return (
                    f"Classified as non-laboratory document. "
                    f"Non-lab indicators detected (score: {non_lab_score:.1f}). "
                    f"Insufficient lab indicators (score: {lab_score:.1f})."
                )
            return (
                f"Classified as non-laboratory document. "
                f"Insufficient lab indicators found (score: {lab_score:.1f}, "
                f"threshold: {self.threshold})."
            )
