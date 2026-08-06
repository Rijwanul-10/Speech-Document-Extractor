"""
Mock OCR Provider.

Returns realistic mock OCR output mimicking a medical laboratory
report for testing and Docker-default operation without needing
actual OCR engines.
"""

from app.adapters.ocr.base import IOCRProvider, OCRLine, OCRResult


# Realistic mock laboratory report OCR output
_MOCK_LAB_REPORT_LINES = [
    "CITYWIDE DIAGNOSTIC LABORATORY",
    "123 Medical Center Road, Dhaka-1205",
    "Phone: +880-2-9876543",
    "",
    "LABORATORY REPORT",
    "",
    "Patient Name: Mohammad Rahman",
    "Age: 45 Years     Sex: Male",
    "Ref No: CDL-2024-00567",
    "Date: 15/07/2024",
    "Referred By: Dr. Kamal Hossain",
    "",
    "=== COMPLETE BLOOD COUNT (CBC) ===",
    "",
    "Hemoglobin            14.2 g/dL         13.0 - 17.0",
    "RBC Count             4.85 million/uL   4.5 - 5.5",
    "WBC Count             7200 /cumm        4000 - 11000",
    "Platelet Count        245000 /cumm      150000 - 400000",
    "PCV/Hematocrit        42.5 %            40 - 50",
    "MCV                   87.6 fL           80 - 100",
    "MCH                   29.3 pg           27 - 31",
    "MCHC                  33.4 g/dL         32 - 36",
    "ESR                   12 mm/hr          0 - 15",
    "",
    "=== DIFFERENTIAL COUNT ===",
    "",
    "Neutrophils           62 %              40 - 70",
    "Lymphocytes           30 %              20 - 40",
    "Monocytes             5 %               2 - 8",
    "Eosinophils           2 %               1 - 6",
    "Basophils             1 %               0 - 2",
    "",
    "=== LIVER FUNCTION TEST ===",
    "",
    "Bilirubin (Total)     0.9 mg/dL         0.1 - 1.2",
    "Bilirubin (Direct)    0.3 mg/dL         0.0 - 0.5",
    "SGPT (ALT)            35 U/L            7 - 56",
    "SGOT (AST)            28 U/L            10 - 40",
    "Alkaline Phosphatase  78 U/L            44 - 147",
    "Total Protein         7.2 g/dL          6.0 - 8.3",
    "Albumin               4.1 g/dL          3.5 - 5.5",
    "",
    "=== RENAL FUNCTION TEST ===",
    "",
    "Blood Urea            32 mg/dL          15 - 45",
    "Serum Creatinine      1.1 mg/dL         0.7 - 1.3",
    "Uric Acid             5.8 mg/dL         3.5 - 7.2",
    "",
    "=== LIPID PROFILE ===",
    "",
    "Total Cholesterol     210 mg/dL         < 200",
    "Triglycerides         165 mg/dL         < 150",
    "HDL Cholesterol       48 mg/dL          > 40",
    "LDL Cholesterol       129 mg/dL         < 130",
    "VLDL                  33 mg/dL          < 40",
    "",
    "=== BLOOD SUGAR ===",
    "",
    "Fasting Blood Sugar   98 mg/dL          70 - 100",
    "HbA1c                 5.6 %             < 5.7",
    "",
    "--- End of Report ---",
    "Verified by: Dr. Fatima Begum, MD Pathology",
]


_MOCK_NON_LAB_LINES = [
    "PRESCRIPTION",
    "Dr. Ahmed Khan",
    "MBBS, FCPS (Medicine)",
    "Chamber: 45 Green Road, Dhaka",
    "",
    "Patient: Karim Uddin",
    "Age: 38    Sex: Male",
    "Date: 20/07/2024",
    "",
    "Rx:",
    "1. Tab. Amlodipine 5mg - 1+0+0 - 30 days",
    "2. Tab. Omeprazole 20mg - 1+0+1 - 14 days",
    "3. Tab. Paracetamol 500mg - SOS",
    "",
    "Advice:",
    "- Low salt diet",
    "- Regular exercise",
    "- Follow up after 2 weeks",
    "",
    "Signature: Dr. Ahmed Khan",
]


class MockOCRAdapter(IOCRProvider):
    """
    Mock OCR provider for testing and offline usage.

    Returns realistic pre-defined OCR output that simulates
    a real lab report to test the downstream extraction pipeline.
    """

    def __init__(self, return_non_lab: bool = False):
        """
        Initialize the mock OCR adapter.

        Args:
            return_non_lab: If True, return non-laboratory document text
                            (used for testing invalid report detection).
        """
        self._return_non_lab = return_non_lab

    @property
    def provider_name(self) -> str:
        """Return the name of this provider."""
        return "mock"

    def extract_text(self, image_bytes: bytes) -> OCRResult:
        """
        Return mock OCR text simulating a lab report.

        The returned data mimics real OCR output to allow full
        testing of downstream extraction and classification.
        """
        if not image_bytes:
            raise ValueError("Empty image provided")

        lines_data = _MOCK_NON_LAB_LINES if self._return_non_lab else _MOCK_LAB_REPORT_LINES

        ocr_lines = []
        for i, line_text in enumerate(lines_data):
            if line_text.strip():  # Skip empty lines in OCR output
                ocr_lines.append(
                    OCRLine(
                        text=line_text,
                        confidence=0.95,
                        bbox=[[0, i * 30], [500, i * 30], [500, (i + 1) * 30], [0, (i + 1) * 30]],
                    )
                )

        full_text = "\n".join(line.text for line in ocr_lines)

        return OCRResult(
            lines=ocr_lines,
            full_text=full_text,
            provider_name=self.provider_name,
            page_number=1,
        )
