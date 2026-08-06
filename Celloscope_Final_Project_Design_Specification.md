# Final Project Design Specification
## Celloscope AI/ML Engineer Take-Home Assignment
### Speech Transcription & Medical Lab Report Extraction Service

> **Version:** 1.0  
> **Technology Stack:** Python 3.11+, FastAPI, Docker

---

# 1. Project Overview

The objective is to build a clean, production-inspired AI backend service that exposes two independent AI capabilities through REST APIs.

The assignment prioritizes software engineering quality, architecture, clean code, modularity, testing, documentation, maintainability, and provider-independent design over feature quantity.

The application should be simple, Dockerized, configurable, and easy for reviewers to run without external credentials.

---

# 2. Project Objectives

## Service 1 — Speech Transcription

- Bengali Speech
- English Speech
- Automatic Language Detection
- Audio File Upload
- Real-time Microphone Transcription

## Service 2 — Medical Laboratory Report Extraction

Extract structured information from:

- Medical Report Images
- Medical Report PDFs

Output includes:

- Patient Information
- Laboratory Metadata
- Test Results
- Normalized Values
- Original OCR Text (`raw_line`)

---

# 3. Design Philosophy

- Clean Architecture
- Modular Design
- Three-Layer Separation
- Testability
- Provider Independence
- Maintainability
- Graceful Error Handling
- Simple but Production-Inspired

---

# 4. High-Level Architecture

```text
                               User
                                 │
          ┌──────────────────────┴──────────────────────┐
          │                                             │
     File Upload                              Live Microphone
          │                                             │
          └──────────────────────┬──────────────────────┘
                                 │
                          FastAPI API Layer
                                 │
                    Request Validation Layer
                                 │
                     File Recognition Layer
                 (Skipped for Live Microphone)
                                 │
         ┌───────────────────────┴────────────────────────┐
         │                                                │
 Speech Processing Pipeline                 Medical Report Pipeline
         │                                                │
 Speech Service                              Document Service
         │                                                │
 Adapter Layer                               Adapter Layer
         │                                                │
 Speech Provider                              OCR Provider
         │                                                │
 Transcript                           OCR + Information Extraction
                                                 │
                                          Value Normalization
                                                 │
                                        Structured JSON Response
```

---

# 5. Workflow

## Inputs

- Audio File → Speech Pipeline
- Image → Medical Report Pipeline
- PDF → Medical Report Pipeline
- Live Microphone → Directly to Speech Pipeline

File recognition is based only on file type.

---

# 6. Speech Pipeline

1. Validate audio
2. Select provider
3. Transcribe
4. Detect language
5. Calculate duration
6. Return JSON response

Validation:

- Unsupported format
- Empty file
- Corrupted file
- File >25 MB
- Silent audio handled gracefully

---

# 7. Medical Report Pipeline

## Stage 1 — Validation

Accept:

- Images
- PDFs

Reject unsupported inputs.

## Stage 2 — Image Enhancement

- Denoising
- Rotation correction
- Perspective correction
- Brightness/contrast enhancement
- Sharpening

## Stage 3 — OCR

Recommended:

- PaddleOCR
- EasyOCR
- Google Vision
- Azure OCR

## Stage 4 — Preserve Raw OCR

Store every detected row exactly as OCR produced it in `raw_line`.

## Stage 5 — Report Classification

- Valid Laboratory Report → Continue
- Non-Laboratory Document → Return Invalid Laboratory Report

## Stage 6 — Metadata Extraction

Extract:

- Patient Name
- Age
- Sex
- Lab Name
- Report Date
- Reference Number

## Stage 7 — Test Result Extraction

Each result contains:

- Test Name
- Numeric Value
- Unit
- Reference Range
- Flag
- Raw Line

## Stage 8 — Dataset-Assisted Feature Validation

Use a laboratory dataset as domain knowledge to recognize expected laboratory fields.

Cases:

1. Metadata + Known Tests → Valid Report
2. Metadata + No Tests → Valid Report with Empty Results
3. No Metadata + No Known Features → Invalid Laboratory Report

> The dataset should improve field recognition and validation, **not train the OCR model**.

## Stage 9 — Normalization

Normalize:

- Units
- Numeric values
- Dates

Never guess uncertain values.

---

# 8. Adapter Layer

## Speech

```text
SpeechProvider
├── WhisperAdapter
├── OpenAIAdapter
├── AzureSpeechAdapter
└── MockSpeechAdapter
```

## OCR

```text
OCRProvider
├── PaddleOCRAdapter
├── GoogleOCRAdapter
├── AzureOCRAdapter
└── MockOCRAdapter
```

Benefits:

- Provider independence
- Easy testing
- Configuration-driven switching
- Cleaner architecture

---

# 9. Mock Providers

Default Docker mode uses mock providers.

Benefits:

- No API keys
- No model downloads
- Offline execution
- Fast testing
- Reviewer-friendly

---

# 10. Recommended Project Structure

```text
project/
├── app/
│   ├── api/
│   ├── services/
│   ├── adapters/
│   │   ├── speech/
│   │   ├── ocr/
│   │   ├── enhancement/
│   │   └── mock/
│   ├── schemas/
│   ├── models/
│   ├── utils/
│   ├── config/
│   └── main.py
├── tests/
├── testdata/
├── README.md
├── DECISIONS.md
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

# 11. Recommended Technology

| Layer | Recommendation |
|--------|----------------|
| Language | Python 3.11+ |
| API | FastAPI |
| Validation | Pydantic |
| Speech | Faster-Whisper / Whisper API |
| OCR | PaddleOCR |
| Image Processing | OpenCV + Pillow |
| PDF | PyMuPDF |
| Testing | Pytest |
| Configuration | Pydantic Settings |
| Container | Docker |

---

# 12. Testing

Recommended tests:

- File validation
- Invalid formats
- File size
- Silent audio
- OCR parsing
- Value normalization
- Invalid report detection
- Empty report detection
- Mock speech integration
- Mock OCR integration

---

# 13. Documentation

## README.md

- Installation
- Docker usage
- Architecture
- API documentation
- Test data
- Normalization strategy
- Limitations

## DECISIONS.md

Document:

- Model selection
- OCR selection
- Adapter pattern
- Mock provider strategy
- Rejected alternatives

---

# 14. Final Engineering Recommendations

- Use **Faster-Whisper** (or Whisper API) instead of training a speech recognition model.
- Use **PaddleOCR** (or another mature OCR engine) instead of training OCR from scratch.
- Use the laboratory dataset to improve **field recognition and validation**, not OCR.
- Keep file routing simple based on input type.
- Bypass file recognition for live microphone input.
- Strictly separate `api → services → adapters`.
- Select providers through environment variables.
- Make mock providers the default for Docker.
- Prioritize clean architecture, meaningful tests, Git history, documentation, validation, and edge-case handling.
- Never fabricate extracted values.
- Keep the implementation simple, maintainable, and aligned with the assignment's evaluation criteria.
