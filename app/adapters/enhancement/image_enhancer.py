"""
Image Enhancement Module.

Provides preprocessing utilities for medical report images
before OCR processing. Improves OCR accuracy by applying
denoising, rotation correction, contrast enhancement, and sharpening.
"""

import logging
from typing import Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class ImageEnhancer:
    """
    Preprocesses images for improved OCR accuracy.

    Applies a pipeline of enhancements: denoising, rotation correction,
    brightness/contrast adjustment, and sharpening.
    """

    def enhance(
        self,
        image_bytes: bytes,
        binarize: bool = False,
        sharpen: bool = False,
    ) -> bytes:
        """
        Apply the full enhancement pipeline to an image.

        Args:
            image_bytes: Raw image bytes (JPEG, PNG, etc.).
            binarize: Whether to apply adaptive binarization (default False).
            sharpen: Whether to apply edge sharpening (default False).

        Returns:
            Enhanced image as PNG bytes.

        Raises:
            ValueError: If the image cannot be decoded.
        """
        image = self._decode_image(image_bytes)

        # Step 1: Convert to grayscale for processing
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        # Step 2: Denoise
        gray = self._denoise(gray)

        # Step 3: Rotation correction (deskew)
        gray = self._deskew(gray)

        # Step 4: Brightness and contrast enhancement
        gray = self._adjust_brightness_contrast(gray)

        # Step 5: Sharpening (optional)
        if sharpen:
            gray = self._sharpen(gray)

        # Step 6: Binarization (optional adaptive threshold)
        if binarize:
            gray = self._binarize(gray)

        # Encode back to PNG bytes
        success, encoded = cv2.imencode(".png", gray)
        if not success:
            raise ValueError("Failed to encode enhanced image")

        return encoded.tobytes()

    def _decode_image(self, image_bytes: bytes) -> np.ndarray:
        """Decode raw bytes into an OpenCV image array."""
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("Unable to decode image — file may be corrupted")
        return image

    def _denoise(self, gray: np.ndarray) -> np.ndarray:
        """Apply non-local means denoising."""
        try:
            return cv2.fastNlMeansDenoising(gray, h=10, templateWindowSize=7, searchWindowSize=21)
        except cv2.error:
            logger.warning("Denoising failed, returning original image")
            return gray

    def _deskew(self, gray: np.ndarray) -> np.ndarray:
        """
        Correct rotation/skew using the Hough transform.

        Detects dominant line angles and rotates to straighten.
        """
        try:
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)
            lines = cv2.HoughLinesP(
                edges, 1, np.pi / 180, threshold=100,
                minLineLength=gray.shape[1] // 4, maxLineGap=10,
            )

            if lines is None:
                return gray

            angles = []
            for line in lines:
                x1, y1, x2, y2 = line[0]
                angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
                if abs(angle) < 15:  # Only consider near-horizontal lines
                    angles.append(angle)

            if not angles:
                return gray

            median_angle = np.median(angles)

            # Only correct if skew is significant
            if abs(median_angle) < 0.5:
                return gray

            (h, w) = gray.shape[:2]
            center = (w // 2, h // 2)
            rotation_matrix = cv2.getRotationMatrix2D(center, median_angle, 1.0)
            rotated = cv2.warpAffine(
                gray, rotation_matrix, (w, h),
                flags=cv2.INTER_CUBIC,
                borderMode=cv2.BORDER_REPLICATE,
            )
            logger.info(f"Corrected skew by {median_angle:.2f} degrees")
            return rotated

        except Exception:
            logger.warning("Deskew failed, returning original image")
            return gray

    def _adjust_brightness_contrast(
        self,
        gray: np.ndarray,
        clip_limit: float = 2.0,
        tile_size: int = 8,
    ) -> np.ndarray:
        """Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)."""
        try:
            clahe = cv2.createCLAHE(
                clipLimit=clip_limit,
                tileGridSize=(tile_size, tile_size),
            )
            return clahe.apply(gray)
        except cv2.error:
            logger.warning("CLAHE failed, returning original image")
            return gray

    def _sharpen(self, gray: np.ndarray) -> np.ndarray:
        """Apply unsharp masking for sharpening."""
        try:
            blurred = cv2.GaussianBlur(gray, (0, 0), 3)
            sharpened = cv2.addWeighted(gray, 1.5, blurred, -0.5, 0)
            return sharpened
        except cv2.error:
            logger.warning("Sharpening failed, returning original image")
            return gray

    def _binarize(self, gray: np.ndarray) -> np.ndarray:
        """Apply adaptive thresholding for clean binary output."""
        try:
            return cv2.adaptiveThreshold(
                gray, 255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                blockSize=11,
                C=2,
            )
        except cv2.error:
            logger.warning("Binarization failed, returning original image")
            return gray
