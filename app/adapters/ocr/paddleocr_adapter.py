"""
PaddleOCR Adapter.

Integrates PaddleOCR for text extraction from medical document images.
Extracts text lines, bounding boxes, and detection confidence scores.
"""

import io
import logging
import tempfile
import numpy as np
import cv2
from typing import Optional

from app.adapters.ocr.base import IOCRProvider, OCRLine, OCRResult

logger = logging.getLogger(__name__)


class PaddleOCRAdapter(IOCRProvider):
    """
    PaddleOCR implementation of IOCRProvider.
    """

    def __init__(self, lang: str = "en", use_gpu: bool = False):
        """
        Initialize PaddleOCR instance.

        Args:
            lang: OCR language model (default 'en').
            use_gpu: Whether to use GPU acceleration.
        """
        self._lang = lang
        self._use_gpu = use_gpu
        self._ocr = None

    def _load_ocr(self):
        """Lazy load PaddleOCR on first call."""
        if self._ocr is None:
            try:
                from paddleocr import PaddleOCR

                logger.info(f"Initializing PaddleOCR (lang={self._lang}, use_gpu={self._use_gpu})...")
                self._ocr = PaddleOCR(
                    use_angle_cls=True,
                    lang=self._lang,
                    use_gpu=self._use_gpu,
                    show_log=False,
                )
                logger.info("PaddleOCR initialized successfully.")
            except ImportError:
                raise RuntimeError(
                    "paddleocr is not installed. "
                    "Install it using `pip install paddleocr paddlepaddle`."
                )
            except Exception as e:
                logger.error(f"Failed to initialize PaddleOCR: {e}")
                raise RuntimeError(f"Failed to initialize PaddleOCR: {e}")

    @property
    def provider_name(self) -> str:
        return "paddleocr"

    def extract_text(self, image_bytes: bytes) -> OCRResult:
        """
        Perform OCR on an image byte stream.
        """
        if not image_bytes:
            raise ValueError("Empty image bytes provided")

        self._load_ocr()

        # Convert image bytes to numpy array (cv2 format)
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            raise ValueError("Could not decode image for PaddleOCR")

        try:
            result = self._ocr.ocr(img, cls=True)

            lines = []
            if result and result[0]:
                lines = self._reconstruct_rows(result[0])

            full_text = "\n".join([line.text for line in lines])

            return OCRResult(
                lines=lines,
                full_text=full_text,
                provider_name=self.provider_name,
                page_number=1,
            )

        except Exception as e:
            logger.error(f"Error during PaddleOCR processing: {e}")
            raise RuntimeError(f"PaddleOCR processing failed: {e}")

    def _reconstruct_rows(self, raw_items: list) -> list[OCRLine]:
        """
        Group individual text detection bounding boxes into spatially
        reconstructed horizontal rows based on Y-center coordinates.
        """
        if not raw_items:
            return []

        parsed_boxes = []
        for res in raw_items:
            if not res or len(res) < 2:
                continue
            bbox = res[0]
            text, confidence = res[1]
            text_str = str(text).strip() if text else ""
            if not text_str:
                continue

            y_coords = [p[1] for p in bbox]
            x_coords = [p[0] for p in bbox]
            y_center = sum(y_coords) / len(y_coords)
            x_center = sum(x_coords) / len(x_coords)
            height = max(y_coords) - min(y_coords)

            parsed_boxes.append({
                "text": text_str,
                "confidence": float(confidence) if confidence is not None else 0.0,
                "bbox": bbox,
                "x_center": x_center,
                "y_center": y_center,
                "height": max(height, 10.0),
            })

        if not parsed_boxes:
            return []

        # Sort by y_center top-to-bottom
        parsed_boxes.sort(key=lambda b: b["y_center"])

        # Group boxes into horizontal rows
        rows: list[list[dict]] = []
        for box in parsed_boxes:
            matched_row = None
            for row in rows:
                row_y_center = sum(b["y_center"] for b in row) / len(row)
                avg_height = sum(b["height"] for b in row) / len(row)
                threshold = max(avg_height * 0.6, 12.0)
                if abs(box["y_center"] - row_y_center) <= threshold:
                    matched_row = row
                    break

            if matched_row is not None:
                matched_row.append(box)
            else:
                rows.append([box])

        # For each row, sort left-to-right by x_center and join text
        ocr_lines = []
        for row in rows:
            row.sort(key=lambda b: b["x_center"])
            row_text = "  ".join(b["text"] for b in row)
            avg_conf = sum(b["confidence"] for b in row) / len(row)

            ocr_lines.append(
                OCRLine(
                    text=row_text,
                    confidence=avg_conf,
                    bbox=row[0]["bbox"] if len(row) == 1 else None,
                )
            )

        return ocr_lines

