"""
Unit tests for PaddleOCRAdapter spatial row reconstruction.
"""

from app.adapters.ocr.paddleocr_adapter import PaddleOCRAdapter


def test_paddleocr_row_reconstruction_logic():
    adapter = PaddleOCRAdapter(lang="en", use_gpu=False)

    # Simulated raw bounding box items from PaddleOCR
    # 2 items on Y=100 (Hemoglobin, 14.2 g/dL), 1 item on Y=200 (WBC Count)
    raw_items = [
        [[[40.0, 100.0], [100.0, 100.0], [100.0, 115.0], [40.0, 115.0]], ("Hemoglobin", 0.99)],
        [[[150.0, 100.0], [220.0, 100.0], [220.0, 115.0], [150.0, 115.0]], ("14.2 g/dL", 0.98)],
        [[[40.0, 200.0], [110.0, 200.0], [110.0, 215.0], [40.0, 215.0]], ("WBC Count", 0.97)],
    ]

    reconstructed = adapter._reconstruct_rows(raw_items)

    assert len(reconstructed) == 2
    assert reconstructed[0].text == "Hemoglobin  14.2 g/dL"
    assert reconstructed[1].text == "WBC Count"
