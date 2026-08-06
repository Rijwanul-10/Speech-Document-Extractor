"""
Synthetic Test Data Generator.

Generates mock audio WAV, image PNGs, and PDF test files in testdata/
to enable automated pytest suites without external sample files.
"""

import os
import wave
import struct
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

TESTDATA_DIR = Path(__file__).parent.parent / "testdata"


def create_synthetic_wav(filename: str = "sample_audio.wav"):
    """Generate a clean synthetic 1-second sine wave WAV file."""
    filepath = TESTDATA_DIR / filename
    TESTDATA_DIR.mkdir(parents=True, exist_ok=True)

    sample_rate = 16000
    duration = 1.0  # seconds
    n_samples = int(sample_rate * duration)

    with wave.open(str(filepath), "w") as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)

        for i in range(n_samples):
            # Generate 440 Hz tone
            val = int(32767.0 * 0.5 * (i % 36 / 36.0))
            wav_file.writeframes(struct.pack("<h", val))

    print(f"Generated synthetic audio: {filepath}")


def create_synthetic_image(filename: str = "sample_report.png", text_lines: list = None):
    """Generate a clean synthetic PNG image with text lines."""
    filepath = TESTDATA_DIR / filename
    TESTDATA_DIR.mkdir(parents=True, exist_ok=True)

    if text_lines is None:
        text_lines = [
            "CITYWIDE DIAGNOSTIC LABORATORY",
            "Patient Name: Mohammad Rahman   Age: 45   Sex: Male",
            "Date: 15/07/2024   Ref No: CDL-2024-00567",
            "",
            "Hemoglobin            14.2 g/dL         13.0 - 17.0",
            "WBC Count             7200 /cumm        4000 - 11000",
            "Platelet Count        245000 /cumm      150000 - 400000",
        ]

    img = Image.new("RGB", (800, 600), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    y = 30
    for line in text_lines:
        draw.text((40, y), line, fill=(0, 0, 0))
        y += 35

    img.save(str(filepath))
    print(f"Generated synthetic image: {filepath}")


def create_synthetic_pdf(filename: str = "sample_report.pdf"):
    """Generate a simple PDF file."""
    filepath = TESTDATA_DIR / filename
    TESTDATA_DIR.mkdir(parents=True, exist_ok=True)

    # Minimal valid PDF content
    pdf_content = (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>\nendobj\n"
        b"4 0 obj\n<< /Length 55 >>\nstream\n"
        b"BT /F1 12 Tf 100 700 Td (Laboratory Report - Hemoglobin 14.2 g/dL) Tj ET\n"
        b"endstream\nendobj\n"
        b"xref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n"
        b"0000000115 00000 n \n0000000214 00000 n \n"
        b"trailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n318\n%%EOF"
    )

    with open(filepath, "wb") as f:
        f.write(pdf_content)

    print(f"Generated synthetic PDF: {filepath}")


if __name__ == "__main__":
    create_synthetic_wav("sample_audio.wav")
    create_synthetic_image("sample_report.png")
    create_synthetic_image("non_lab_doc.png", text_lines=["PRESCRIPTION", "Rx: Tab Paracetamol"])
    create_synthetic_pdf("sample_report.pdf")
