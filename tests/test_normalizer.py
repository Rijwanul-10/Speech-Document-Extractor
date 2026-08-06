"""
Unit tests for ValueNormalizer.
"""

from app.utils.normalizer import ValueNormalizer


def test_unit_normalization():
    normalizer = ValueNormalizer()
    assert normalizer.normalize_unit("mg/dl") == "mg/dL"
    assert normalizer.normalize_unit("gm/dl") == "g/dL"
    assert normalizer.normalize_unit("u/l") == "U/L"
    assert normalizer.normalize_unit("cells/cumm") == "cells/µL"


def test_numeric_normalization():
    normalizer = ValueNormalizer()
    assert normalizer.normalize_numeric("14.2") == "14.2"
    assert normalizer.normalize_numeric("O.9") == "0.9"  # OCR 'O' fix
    assert normalizer.normalize_numeric("245,000") == "245000"  # Remove comma
    assert normalizer.normalize_numeric("< 200") == "< 200"


def test_date_normalization():
    normalizer = ValueNormalizer()
    assert normalizer.normalize_date("15/07/2024") == "15/07/2024"
    assert normalizer.normalize_date("15-07-2024") == "15/07/2024"
    assert normalizer.normalize_date("2024-07-15") == "15/07/2024"
    assert normalizer.normalize_date("15 Jul 2024") == "15/07/2024"


def test_determine_flag():
    normalizer = ValueNormalizer()
    # High
    assert normalizer.determine_flag("210", "< 200") == "high"
    # Normal
    assert normalizer.determine_flag("14.2", "13.0 - 17.0") == "normal"
    # Low
    assert normalizer.determine_flag("10.5", "13.0 - 17.0") == "low"
