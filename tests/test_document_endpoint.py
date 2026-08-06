"""
Integration tests for Medical Document Extraction Endpoint.
"""

from pathlib import Path

TESTDATA_DIR = Path(__file__).parent.parent / "testdata"


def test_extract_report_image(client):
    image_path = TESTDATA_DIR / "sample_report.png"
    with open(image_path, "rb") as f:
        response = client.post(
            "/api/v1/document/extract",
            files={"file": ("sample_report.png", f, "image/png")},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["is_valid_lab_report"] is True
    assert data["patient_info"]["name"] == "Mohammad Rahman"
    assert len(data["test_results"]) > 0
    # Check raw_line preservation
    for result in data["test_results"]:
        assert "raw_line" in result
        assert len(result["raw_line"]) > 0


def test_extract_report_pdf(client):
    pdf_path = TESTDATA_DIR / "sample_report.pdf"
    with open(pdf_path, "rb") as f:
        response = client.post(
            "/api/v1/document/extract",
            files={"file": ("sample_report.pdf", f, "application/pdf")},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


def test_extract_unsupported_document(client):
    response = client.post(
        "/api/v1/document/extract",
        files={"file": ("doc.docx", b"word doc content", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )
    assert response.status_code == 400
    data = response.json()["detail"]
    assert data["error_code"] == "UNSUPPORTED_FORMAT"
