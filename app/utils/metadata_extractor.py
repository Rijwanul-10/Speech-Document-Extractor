"""
Metadata Extractor.

Extracts patient information and laboratory metadata from
OCR text lines using pattern matching and heuristics.
"""

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


class MetadataExtractor:
    """
    Extracts patient info and lab metadata from OCR text.

    Looks for common label patterns like "Patient Name:", "Age:",
    "Lab Name:", "Date:", etc. in OCR output lines.
    """

    def extract_patient_info(self, ocr_lines: list[str]) -> dict:
        """
        Extract patient information from OCR lines.

        Returns:
            Dict with 'name', 'age', 'sex', 'patient_id'.
        """
        info = {
            "name": None,
            "age": None,
            "sex": None,
            "patient_id": None,
        }

        full_text = "\n".join(ocr_lines)

        # Extract patient name
        info["name"] = self._extract_field(
            ocr_lines,
            patterns=[
                r'(?:patient\s*name|name\s*of\s*patient|patient)\s*[:\-]\s*(.+)',
                r'(?:name)\s*[:\-]\s*([A-Za-z\s\.]+)',
            ],
        )

        # Extract age
        age_str = self._extract_field(
            ocr_lines,
            patterns=[
                r'(?:age)\s*[:\-]\s*(\d+\s*(?:years?|yrs?|Y)?)',
                r'(\d+)\s*(?:years?|yrs?)\s*(?:old)?',
            ],
        )
        if age_str:
            # Clean age string
            age_match = re.search(r'(\d+)', age_str)
            if age_match:
                info["age"] = f"{age_match.group(1)} Years"

        # Extract sex/gender
        sex_str = self._extract_field(
            ocr_lines,
            patterns=[
                r'(?:sex|gender)\s*[:\-]\s*(male|female|m|f|other)',
                r'\b(male|female)\b',
            ],
        )
        if sex_str:
            sex_lower = sex_str.strip().lower()
            if sex_lower in ("m", "male"):
                info["sex"] = "Male"
            elif sex_lower in ("f", "female"):
                info["sex"] = "Female"
            else:
                info["sex"] = sex_str.strip().title()

        # Extract patient ID
        info["patient_id"] = self._extract_field(
            ocr_lines,
            patterns=[
                r'(?:patient\s*id|pid|uhid|mrn|reg\s*no)\s*[:\-]\s*([A-Za-z0-9\-]+)',
            ],
        )

        return info

    def extract_lab_metadata(self, ocr_lines: list[str]) -> dict:
        """
        Extract laboratory metadata from OCR lines.

        Returns:
            Dict with 'lab_name', 'report_date', 'reference_number',
            'referring_doctor'.
        """
        metadata = {
            "lab_name": None,
            "report_date": None,
            "reference_number": None,
            "referring_doctor": None,
        }

        # Lab name: typically the first non-empty line or a labeled field
        metadata["lab_name"] = self._extract_lab_name(ocr_lines)

        # Report date
        metadata["report_date"] = self._extract_field(
            ocr_lines,
            patterns=[
                r'(?:date|report\s*date|collection\s*date|sample\s*date)\s*[:\-]\s*(.+)',
            ],
        )

        # Reference number
        metadata["reference_number"] = self._extract_field(
            ocr_lines,
            patterns=[
                r'(?:ref\s*no|reference\s*no|accession\s*no|sample\s*id|lab\s*no|report\s*no)\s*[:\-]\s*([A-Za-z0-9\-\/]+)',
            ],
        )

        # Referring doctor
        metadata["referring_doctor"] = self._extract_field(
            ocr_lines,
            patterns=[
                r'(?:referred\s*by|ref\s*by|ref\.\s*by|referring\s*doctor|dr\.?)\s*[:\-]?\s*(Dr\.?\s*[A-Za-z\s\.]+)',
                r'(?:referred\s*by|ref\s*by)\s*[:\-]\s*(.+)',
            ],
        )

        return metadata

    def _extract_lab_name(self, ocr_lines: list[str]) -> Optional[str]:
        """
        Extract the laboratory name.

        Heuristic: the first substantial text line that looks like
        a name (all caps, or contains "lab", "diagnostic", "hospital",
        "clinic", "pathology", "center").
        """
        lab_keywords = [
            "laboratory", "lab", "diagnostic", "hospital",
            "clinic", "pathology", "center", "centre",
            "medical", "health",
        ]

        # First check for explicit label
        for line in ocr_lines:
            match = re.search(
                r'(?:lab\s*name|laboratory)\s*[:\-]\s*(.+)',
                line, re.IGNORECASE,
            )
            if match:
                return match.group(1).strip()

        # Then check first few lines for lab-like names
        for line in ocr_lines[:5]:
            line_stripped = line.strip()
            if not line_stripped or len(line_stripped) < 3:
                continue

            line_lower = line_stripped.lower()
            if any(kw in line_lower for kw in lab_keywords):
                return line_stripped

            # All caps line in first 3 lines is likely the lab name
            if line_stripped == line_stripped.upper() and len(line_stripped) > 5:
                return line_stripped

        return None

    def _extract_field(
        self,
        ocr_lines: list[str],
        patterns: list[str],
    ) -> Optional[str]:
        """
        Extract a field value using regex patterns.

        Tries each pattern against each line. Returns the first match.
        """
        for line in ocr_lines:
            for pattern in patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    value = match.group(1).strip()
                    if value:
                        return value
        return None
