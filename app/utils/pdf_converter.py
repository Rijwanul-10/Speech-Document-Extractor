"""
PDF Converter.

Converts PDF documents to images for OCR processing.
Uses PyMuPDF (fitz) to render PDF pages as high-resolution images.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class PDFConverter:
    """
    Converts PDF pages to images for OCR processing.

    Renders each page at a configurable DPI for optimal OCR accuracy.
    """

    def __init__(self, dpi: int = 300):
        """
        Initialize the PDF converter.

        Args:
            dpi: Resolution for rendering PDF pages (default: 300).
        """
        self.dpi = dpi

    def convert_to_images(self, pdf_bytes: bytes) -> list[bytes]:
        """
        Convert a PDF to a list of PNG images (one per page).

        Args:
            pdf_bytes: Raw PDF file content.

        Returns:
            List of PNG image bytes, one per page.

        Raises:
            ValueError: If the PDF is invalid or empty.
            ImportError: If PyMuPDF is not installed.
        """
        try:
            import fitz  # PyMuPDF
        except ImportError:
            raise ImportError(
                "PyMuPDF is required for PDF processing. "
                "Install it with: pip install PyMuPDF"
            )

        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        except Exception as e:
            raise ValueError(f"Failed to open PDF: {e}")

        if doc.page_count == 0:
            raise ValueError("PDF file contains no pages")

        images = []
        zoom = self.dpi / 72  # 72 DPI is the PDF default

        for page_num in range(doc.page_count):
            try:
                page = doc.load_page(page_num)
                matrix = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=matrix)
                img_bytes = pix.tobytes("png")
                images.append(img_bytes)
                logger.debug(
                    f"Converted PDF page {page_num + 1}/{doc.page_count} "
                    f"({pix.width}x{pix.height})"
                )
            except Exception as e:
                logger.warning(f"Failed to convert PDF page {page_num + 1}: {e}")
                continue

        doc.close()

        if not images:
            raise ValueError("Failed to convert any PDF pages to images")

        logger.info(f"Converted {len(images)} pages from PDF ({self.dpi} DPI)")
        return images

    def get_page_count(self, pdf_bytes: bytes) -> int:
        """
        Get the number of pages in a PDF.

        Args:
            pdf_bytes: Raw PDF file content.

        Returns:
            Number of pages.
        """
        try:
            import fitz
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            count = doc.page_count
            doc.close()
            return count
        except Exception as e:
            logger.error(f"Failed to count PDF pages: {e}")
            return 0
