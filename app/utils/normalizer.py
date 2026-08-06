"""
Value Normalizer.

Normalizes units, numeric values, and dates extracted from
medical laboratory reports. Handles common OCR misreadings
and unit format variations.
"""

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


# Standard unit mappings — maps OCR variants to canonical forms
_UNIT_MAPPINGS = {
    # Volume/Mass
    "mg/dl": "mg/dL",
    "mg/DL": "mg/dL",
    "MG/DL": "mg/dL",
    "gm/dl": "g/dL",
    "g/dl": "g/dL",
    "gm/dL": "g/dL",
    "G/DL": "g/dL",
    "g/l": "g/L",
    "gm/l": "g/L",
    "mg/l": "mg/L",
    "ug/dl": "µg/dL",
    "mcg/dl": "µg/dL",
    "ug/ml": "µg/mL",
    "mcg/ml": "µg/mL",
    "ng/ml": "ng/mL",
    "ng/dl": "ng/dL",
    "pg/ml": "pg/mL",

    # Cells
    "cells/cumm": "cells/µL",
    "/cumm": "/µL",
    "cells/ul": "cells/µL",
    "/ul": "/µL",
    "cells/mm3": "cells/µL",
    "/mm3": "/µL",
    "million/ul": "million/µL",
    "million/cumm": "million/µL",
    "mill/cumm": "million/µL",
    "thou/cumm": "×10³/µL",
    "lakhs/cumm": "×10⁵/µL",

    # Enzyme / Liver
    "u/l": "U/L",
    "U/l": "U/L",
    "iu/l": "IU/L",
    "IU/l": "IU/L",
    "iu/ml": "IU/mL",

    # ESR
    "mm/hr": "mm/hr",
    "mm/1st hr": "mm/hr",
    "mm/1sthr": "mm/hr",
    "mm /hr": "mm/hr",

    # Percentage
    "%": "%",
    "percent": "%",

    # Hemoglobin / Hematology
    "fl": "fL",
    "pg": "pg",
    "g%": "g/dL",

    # Others
    "meq/l": "mEq/L",
    "mmol/l": "mmol/L",
    "umol/l": "µmol/L",
    "mg/24hr": "mg/24hr",
    "mg/24 hr": "mg/24hr",
    "sec": "seconds",
    "secs": "seconds",
    "seconds": "seconds",
}


class ValueNormalizer:
    """
    Normalizes extracted lab report values.

    Handles unit standardization, numeric value cleaning,
    and date format normalization.
    """

    def normalize_unit(self, unit: Optional[str]) -> Optional[str]:
        """
        Normalize a unit string to its canonical form.

        Args:
            unit: Raw unit string from OCR.

        Returns:
            Normalized unit string, or the original if no mapping exists.
        """
        if not unit:
            return None

        cleaned = unit.strip()

        # Try exact match first
        if cleaned.lower() in {k.lower(): k for k in _UNIT_MAPPINGS}:
            for key, value in _UNIT_MAPPINGS.items():
                if key.lower() == cleaned.lower():
                    return value

        # Try with stripped spaces
        no_space = cleaned.replace(" ", "")
        for key, value in _UNIT_MAPPINGS.items():
            if key.replace(" ", "").lower() == no_space.lower():
                return value

        return cleaned

    def normalize_numeric(self, value: Optional[str]) -> Optional[str]:
        """
        Clean and normalize a numeric value string.

        Handles OCR artifacts like 'O' for '0', commas, spaces, etc.

        Args:
            value: Raw numeric value from OCR.

        Returns:
            Cleaned numeric string, or None if unparseable.
        """
        if not value:
            return None

        cleaned = value.strip()

        # Common OCR corrections
        cleaned = cleaned.replace("O", "0")  # Letter O → digit 0
        cleaned = cleaned.replace("l", "1")  # Lowercase L → digit 1 (only in numeric context)
        cleaned = cleaned.replace(",", "")   # Remove thousands separators
        cleaned = cleaned.replace(" ", "")   # Remove spaces

        # Preserve negative/positive signs and decimal points
        match = re.match(r'^([<>]?\s*[+-]?\d+\.?\d*)', cleaned)
        if match:
            result = match.group(1).strip()
            # Remove leading zeros except for "0.xxx"
            if "." in result:
                parts = result.split(".")
                sign = ""
                prefix = ""
                num_part = parts[0]

                # Extract sign/prefix
                for char in num_part:
                    if char in "<>+-":
                        prefix += char
                    else:
                        break
                num_part = num_part[len(prefix):]

                return f"{prefix}{num_part}.{parts[1]}"
            return result

        # If it looks like a number with comparison operators
        if cleaned.startswith(("<", ">")):
            return cleaned

        logger.debug(f"Could not normalize numeric value: '{value}'")
        return value.strip()

    def normalize_date(self, date_str: Optional[str]) -> Optional[str]:
        """
        Normalize a date string to DD/MM/YYYY format.

        Handles various date formats commonly found in lab reports.

        Args:
            date_str: Raw date string from OCR.

        Returns:
            Normalized date in DD/MM/YYYY format, or original if unparseable.
        """
        if not date_str:
            return None

        cleaned = date_str.strip()

        # Already in DD/MM/YYYY
        if re.match(r'^\d{2}/\d{2}/\d{4}$', cleaned):
            return cleaned

        # DD-MM-YYYY → DD/MM/YYYY
        match = re.match(r'^(\d{2})-(\d{2})-(\d{4})$', cleaned)
        if match:
            return f"{match.group(1)}/{match.group(2)}/{match.group(3)}"

        # YYYY-MM-DD → DD/MM/YYYY
        match = re.match(r'^(\d{4})-(\d{2})-(\d{2})$', cleaned)
        if match:
            return f"{match.group(3)}/{match.group(2)}/{match.group(1)}"

        # DD.MM.YYYY → DD/MM/YYYY
        match = re.match(r'^(\d{2})\.(\d{2})\.(\d{4})$', cleaned)
        if match:
            return f"{match.group(1)}/{match.group(2)}/{match.group(3)}"

        # Month name formats: "15 Jul 2024", "Jul 15, 2024", etc.
        months = {
            "jan": "01", "january": "01",
            "feb": "02", "february": "02",
            "mar": "03", "march": "03",
            "apr": "04", "april": "04",
            "may": "05",
            "jun": "06", "june": "06",
            "jul": "07", "july": "07",
            "aug": "08", "august": "08",
            "sep": "09", "september": "09",
            "oct": "10", "october": "10",
            "nov": "11", "november": "11",
            "dec": "12", "december": "12",
        }

        # "15 Jul 2024" or "15 July 2024"
        match = re.match(
            r'^(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})$', cleaned,
        )
        if match:
            day = match.group(1).zfill(2)
            month_name = match.group(2).lower()
            year = match.group(3)
            if month_name in months:
                return f"{day}/{months[month_name]}/{year}"

        # "Jul 15, 2024" or "July 15, 2024"
        match = re.match(
            r'^([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})$', cleaned,
        )
        if match:
            month_name = match.group(1).lower()
            day = match.group(2).zfill(2)
            year = match.group(3)
            if month_name in months:
                return f"{day}/{months[month_name]}/{year}"

        logger.debug(f"Could not normalize date: '{date_str}'")
        return cleaned

    def normalize_reference_range(self, ref_range: Optional[str]) -> Optional[str]:
        """
        Normalize a reference range string.

        Handles formats like "13.0 - 17.0", "< 200", "> 40", etc.

        Args:
            ref_range: Raw reference range from OCR.

        Returns:
            Normalized reference range string.
        """
        if not ref_range:
            return None

        cleaned = ref_range.strip()

        # Normalize dash/hyphen variants
        cleaned = re.sub(r'\s*[–—]\s*', ' - ', cleaned)

        # Normalize spaces around operators
        cleaned = re.sub(r'\s*<\s*', '< ', cleaned)
        cleaned = re.sub(r'\s*>\s*', '> ', cleaned)

        # Normalize "to" → "-"
        cleaned = re.sub(r'\s+to\s+', ' - ', cleaned, flags=re.IGNORECASE)

        return cleaned

    def determine_flag(
        self,
        value: Optional[str],
        reference_range: Optional[str],
    ) -> Optional[str]:
        """
        Determine if a test result is high, low, or normal.

        Args:
            value: Normalized numeric value.
            reference_range: Normalized reference range.

        Returns:
            'high', 'low', 'normal', or None if undeterminable.
        """
        if not value or not reference_range:
            return None

        try:
            # Extract numeric value
            num_match = re.search(r'([+-]?\d+\.?\d*)', value)
            if not num_match:
                return None
            num_value = float(num_match.group(1))

            # Handle "< X" ranges
            less_match = re.match(r'<\s*(\d+\.?\d*)', reference_range)
            if less_match:
                upper = float(less_match.group(1))
                return "high" if num_value >= upper else "normal"

            # Handle "> X" ranges
            greater_match = re.match(r'>\s*(\d+\.?\d*)', reference_range)
            if greater_match:
                lower = float(greater_match.group(1))
                return "low" if num_value <= lower else "normal"

            # Handle "X - Y" ranges
            range_match = re.match(
                r'(\d+\.?\d*)\s*-\s*(\d+\.?\d*)', reference_range,
            )
            if range_match:
                lower = float(range_match.group(1))
                upper = float(range_match.group(2))
                if num_value < lower:
                    return "low"
                elif num_value > upper:
                    return "high"
                else:
                    return "normal"

        except (ValueError, TypeError):
            logger.debug(
                f"Could not determine flag for value='{value}', "
                f"range='{reference_range}'"
            )

        return None
