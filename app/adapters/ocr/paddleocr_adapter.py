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
                for res in result[0]:
                    bbox = res[0]
                    text, confidence = res[1]

                    lines.append(
                        OCRLine(
                            text=text.strip(),
                            confidence=float(confidence),
                            bbox=bbox,
                        )
                    )

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
