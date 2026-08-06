"""
Laboratory Reference Dataset Module.

Provides domain knowledge about medical laboratory tests, expected units,
reference ranges, and field validation capabilities (Stage 8 of Medical Pipeline).
Can load external CSV/JSON lab datasets or fallback to built-in knowledge base.
"""

import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Built-in reference dictionary of common lab tests
DEFAULT_LAB_TEST_KNOWLEDGE = {
    "hemoglobin": {"units": ["g/dL"], "synonyms": ["hb", "haemoglobin"]},
    "wbc count": {"units": ["/cumm", "/uL", "cells/uL"], "synonyms": ["wbc", "white blood cell count", "total wbc"]},
    "rbc count": {"units": ["million/uL", "million/cumm"], "synonyms": ["rbc", "red blood cell count"]},
    "platelet count": {"units": ["/cumm", "/uL", "lakhs/cumm"], "synonyms": ["platelets", "plt"]},
    "pcv": {"units": ["%"], "synonyms": ["hematocrit", "packed cell volume"]},
    "mcv": {"units": ["fL"], "synonyms": ["mean corpuscular volume"]},
    "mch": {"units": ["pg"], "synonyms": ["mean corpuscular hemoglobin"]},
    "mchc": {"units": ["g/dL"], "synonyms": ["mean corpuscular hemoglobin concentration"]},
    "esr": {"units": ["mm/hr"], "synonyms": ["erythrocyte sedimentation rate"]},
    "neutrophils": {"units": ["%"], "synonyms": ["neutrophil"]},
    "lymphocytes": {"units": ["%"], "synonyms": ["lymphocyte"]},
    "monocytes": {"units": ["%"], "synonyms": ["monocyte"]},
    "eosinophils": {"units": ["%"], "synonyms": ["eosinophil"]},
    "basophils": {"units": ["%"], "synonyms": ["basophil"]},
    "serum creatinine": {"units": ["mg/dL"], "synonyms": ["creatinine", "s.creatinine"]},
    "blood urea": {"units": ["mg/dL"], "synonyms": ["urea", "s.urea", "bun"]},
    "uric acid": {"units": ["mg/dL"], "synonyms": ["s.uric acid"]},
    "sgpt": {"units": ["U/L"], "synonyms": ["alt", "alanine aminotransferase"]},
    "sgot": {"units": ["U/L"], "synonyms": ["ast", "aspartate aminotransferase"]},
    "total bilirubin": {"units": ["mg/dL"], "synonyms": ["s.bilirubin", "bilirubin (total)"]},
    "direct bilirubin": {"units": ["mg/dL"], "synonyms": ["bilirubin (direct)"]},
    "alkaline phosphatase": {"units": ["U/L"], "synonyms": ["alp", "alk. phosphatase"]},
    "total protein": {"units": ["g/dL"], "synonyms": ["protein (total)"]},
    "serum albumin": {"units": ["g/dL"], "synonyms": ["albumin", "s.albumin"]},
    "total cholesterol": {"units": ["mg/dL"], "synonyms": ["s.cholesterol", "cholesterol"]},
    "triglycerides": {"units": ["mg/dL"], "synonyms": ["s.triglycerides", "tg"]},
    "hdl cholesterol": {"units": ["mg/dL"], "synonyms": ["hdl", "s.hdl"]},
    "ldl cholesterol": {"units": ["mg/dL"], "synonyms": ["ldl", "s.ldl"]},
    "fasting blood sugar": {"units": ["mg/dL"], "synonyms": ["fbs", "fasting glucose"]},
    "hba1c": {"units": ["%"], "synonyms": ["glycated hemoglobin", "hb a1c"]},
}


class LabDatasetValidator:
    """
    Validates extracted features against domain knowledge lab dataset.
    """

    def __init__(self, dataset_path: Optional[str] = None):
        """
        Initialize validator with custom dataset file path or default knowledge.
        """
        self.knowledge = dict(DEFAULT_LAB_TEST_KNOWLEDGE)

        if dataset_path and Path(dataset_path).exists():
            self.load_dataset(dataset_path)

    def load_dataset(self, file_path: str):
        """Load lab dataset from JSON file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    self.knowledge.update(data)
                    logger.info(f"Loaded custom lab dataset from {file_path} with {len(data)} entries.")
        except Exception as e:
            logger.warning(f"Failed to load custom lab dataset from {file_path}: {e}")

    def is_known_lab_test(self, test_name: str) -> bool:
        """
        Check if a given test name matches known lab test features.
        """
        test_name_lower = test_name.strip().lower()

        for canonical_name, info in self.knowledge.items():
            if canonical_name in test_name_lower or test_name_lower in canonical_name:
                return True
            for syn in info.get("synonyms", []):
                if syn in test_name_lower or test_name_lower in syn:
                    return True
        return False

    def validate_report_features(
        self,
        has_metadata: bool,
        extracted_tests: list[dict],
    ) -> dict:
        """
        Stage 8 dataset-assisted validation criteria:
        1. Metadata + Known Tests -> Valid Report
        2. Metadata + No Tests -> Valid Report with Empty Results
        3. No Metadata + No Known Features -> Invalid Laboratory Report
        """
        known_test_count = sum(
            1 for t in extracted_tests if self.is_known_lab_test(t.get("test_name", ""))
        )

        if has_metadata and known_test_count > 0:
            is_valid = True
            reason = f"Valid report with metadata and {known_test_count} known lab test(s)."
        elif has_metadata and known_test_count == 0:
            is_valid = True
            reason = "Valid lab report header with metadata, but no test results detected."
        elif not has_metadata and known_test_count > 0:
            is_valid = True
            reason = f"Valid lab report body detected with {known_test_count} known test(s)."
        else:
            is_valid = False
            reason = "No medical metadata or known laboratory test features recognized."

        return {
            "is_valid": is_valid,
            "known_test_count": known_test_count,
            "reason": reason,
        }
