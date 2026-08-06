"""
Test Result Extractor.

Extracts individual laboratory test results from OCR text lines.
Parses test name, numeric value, unit, and reference range from
tabular lab report data.
"""

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


class TestResultExtractor:
    """
    Extracts structured test results from OCR lines.

    Handles common lab report formats where each line contains:
    test_name  value  unit  reference_range
    """

    # Section headers to skip (not actual test results)
    _SECTION_HEADERS = {
        "complete blood count", "cbc", "differential count",
        "liver function test", "lft", "renal function test", "rft",
        "lipid profile", "blood sugar", "thyroid function",
        "urine analysis", "urinalysis", "hematology",
        "biochemistry", "serology", "immunology",
        "electrolytes", "coagulation", "iron studies",
    }

    # Patterns for lines that are definitely NOT test results
    _SKIP_PATTERNS = [
        r'^={2,}',                    # Section separators (===)
        r'^-{2,}',                    # Dashes (---)
        r'^\s*$',                     # Empty lines
        r'^(patient|name|age|sex|date|ref|lab|phone|address|verified)',
        r'^(dr\.|doctor|referred)',
        r'^(end of report|signature)',
    ]

    def extract_results(self, ocr_lines: list[str]) -> list[dict]:
        """
        Extract test results from OCR lines.

        Args:
            ocr_lines: Raw OCR text lines.

        Returns:
            List of dicts with 'test_name', 'value', 'unit',
            'reference_range', 'raw_line'.
        """
        results = []

        for line in ocr_lines:
            stripped = line.strip()

            # Skip empty lines
            if not stripped:
                continue

            # Skip section headers and non-data lines
            if self._should_skip(stripped):
                continue

            # Try to parse as a test result line
            parsed = self._parse_result_line(stripped)
            if parsed:
                parsed["raw_line"] = line
                results.append(parsed)

        logger.info(f"Extracted {len(results)} test results from {len(ocr_lines)} OCR lines")
        return results

    def _should_skip(self, line: str) -> bool:
        """Check if a line should be skipped (not a test result)."""
        line_lower = line.lower().strip()

        # Skip section headers
        # Remove leading/trailing special chars for comparison
        cleaned = re.sub(r'^[=\-\s*]+|[=\-\s*]+$', '', line_lower)
        if cleaned in self._SECTION_HEADERS:
            return True

        # Skip pattern matches
        for pattern in self._SKIP_PATTERNS:
            if re.match(pattern, line_lower):
                return True

        return False

    def _parse_result_line(self, line: str) -> Optional[dict]:
        """
        Parse a single test result line.

        Tries multiple parsing strategies to handle different
        lab report formats.
        """
        # Strategy 1: Full pattern — "TestName  Value  Unit  RefRange"
        result = self._parse_full_pattern(line)
        if result:
            return result

        # Strategy 2: Value with range — "TestName  Value  Unit  Low - High"
        result = self._parse_value_with_range(line)
        if result:
            return result

        # Strategy 3: Value with comparison — "TestName  Value  Unit  < X" or "> X"
        result = self._parse_value_with_comparison(line)
        if result:
            return result

        return None

    def _parse_full_pattern(self, line: str) -> Optional[dict]:
        """
        Parse: TestName  Value  Unit  Low - High

        Example: "Hemoglobin  14.2  g/dL  13.0 - 17.0"
        """
        pattern = (
            r'^(.+?)\s{2,}'           # Test name (followed by 2+ spaces)
            r'(\d+\.?\d*)\s+'         # Value
            r'([a-zA-Z/%µ×³⁵·]+(?:/[a-zA-Z²³µ]+)?)\s+'  # Unit
            r'(\d+\.?\d*\s*-\s*\d+\.?\d*)'  # Reference range
        )

        match = re.match(pattern, line)
        if match:
            return {
                "test_name": match.group(1).strip(),
                "value": match.group(2).strip(),
                "unit": match.group(3).strip(),
                "reference_range": match.group(4).strip(),
            }
        return None

    def _parse_value_with_range(self, line: str) -> Optional[dict]:
        """
        Parse variations with different spacing patterns.

        Also handles: "Hemoglobin            14.2 g/dL         13.0 - 17.0"
        """
        pattern = (
            r'^(.+?)\s+'             # Test name
            r'(\d+\.?\d*)\s+'        # Value
            r'([a-zA-Z/%µ×³⁵·]+(?:/[a-zA-Z²³µ]+)?)\s+'  # Unit
            r'(\d+\.?\d*\s*-\s*\d+\.?\d*)'  # Reference range
        )

        match = re.match(pattern, line)
        if match:
            test_name = match.group(1).strip()
            # Ensure the test name is actually a name (not a number)
            if test_name and not test_name[0].isdigit():
                return {
                    "test_name": test_name,
                    "value": match.group(2).strip(),
                    "unit": match.group(3).strip(),
                    "reference_range": match.group(4).strip(),
                }
        return None

    def _parse_value_with_comparison(self, line: str) -> Optional[dict]:
        """
        Parse lines with comparison reference ranges.

        Example: "Total Cholesterol  210  mg/dL  < 200"
        """
        pattern = (
            r'^(.+?)\s+'             # Test name
            r'(\d+\.?\d*)\s+'        # Value
            r'([a-zA-Z/%µ×³⁵·]+(?:/[a-zA-Z²³µ]+)?)\s+'  # Unit
            r'([<>]\s*\d+\.?\d*)'    # Comparison range
        )

        match = re.match(pattern, line)
        if match:
            test_name = match.group(1).strip()
            if test_name and not test_name[0].isdigit():
                return {
                    "test_name": test_name,
                    "value": match.group(2).strip(),
                    "unit": match.group(3).strip(),
                    "reference_range": match.group(4).strip(),
                }
        return None
