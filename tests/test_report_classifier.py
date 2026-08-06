"""
Unit tests for ReportClassifier.
"""

from app.utils.report_classifier import ReportClassifier


def test_classify_valid_lab_report():
    classifier = ReportClassifier()
    lines = [
        "CITYWIDE DIAGNOSTIC LABORATORY",
        "LABORATORY REPORT",
        "Patient Name: Mohammad Rahman",
        "COMPLETE BLOOD COUNT (CBC)",
        "Hemoglobin 14.2 g/dL 13.0 - 17.0",
        "WBC Count 7200 /cumm 4000 - 11000",
    ]
    res = classifier.classify(lines)
    assert res["is_lab_report"] is True
    assert res["confidence"] > 0.3


def test_classify_non_lab_document():
    classifier = ReportClassifier()
    lines = [
        "PRESCRIPTION",
        "Dr. Ahmed Khan",
        "Rx:",
        "1. Tab. Amlodipine 5mg",
        "Advice: Low salt diet",
    ]
    res = classifier.classify(lines)
    assert res["is_lab_report"] is False
