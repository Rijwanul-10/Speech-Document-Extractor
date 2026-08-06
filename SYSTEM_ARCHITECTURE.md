
# SYSTEM_ARCHITECTURE.md

# System Architecture
## Celloscope AI/ML Engineer Take-Home Assignment

Version: 1.0

---

# Purpose

This document describes the complete system architecture, component interactions, data flow, layer responsibilities, provider abstraction strategy, and scalability considerations for the AI service.

The design follows the assignment requirements while keeping the system simple, modular, testable, and production-inspired.

---

# 1. Overall Architecture

```text
                           User / Client
                                 │
                    REST API / Swagger UI
                                 │
                          FastAPI (API Layer)
                                 │
                    Request Validation Layer
                                 │
                    File Recognition Router
                   (Skipped for Live Speech)
                                 │
         ┌───────────────────────┴────────────────────────┐
         │                                                │
 Speech Transcription Pipeline              Medical Report Pipeline
         │                                                │
         ▼                                                ▼
  Speech Service                            Document Service
         │                                                │
         ▼                                                ▼
  Speech Adapter Interface                  OCR Adapter Interface
         │                                                │
   ┌─────┴────────────┐                      ┌─────────────┴────────────┐
   │                  │                      │                          │
Real Provider     Mock Provider        Real OCR                  Mock OCR
         │                                                │
         ▼                                                ▼
 Structured Transcript                    OCR Text + Image Processing
                                                      │
                                                      ▼
                                        Report Classification
                                                      │
                                                      ▼
                                      Metadata & Result Extraction
                                                      │
                                                      ▼
                                          Value Normalization
                                                      │
                                                      ▼
                                           Structured JSON Response
```

---

# 2. Layered Architecture

```
api/
│
├── HTTP Routes
├── Request Models
├── Response Models
└── Validation

↓

services/
│
├── Business Logic
├── Workflow Orchestration
└── Provider Selection

↓

adapters/
│
├── Speech Providers
├── OCR Providers
├── Image Enhancement
└── Mock Providers
```

## Responsibilities

### API Layer
- REST endpoints
- Request validation
- Response formatting
- No AI logic

### Service Layer
- Business rules
- Pipeline orchestration
- Error handling
- Calls provider interfaces only

### Adapter Layer
- External AI integration
- Whisper
- PaddleOCR
- Mock implementations
- Image preprocessing

---

# 3. Folder Structure

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
└── .env.example
```

---

# 4. Request Lifecycle

## Speech

```text
Client
  │
Upload Audio
  │
API Validation
  │
Speech Service
  │
Speech Adapter
  │
Whisper / Mock
  │
Transcript
  │
JSON Response
```

## Medical Report

```text
Client
  │
Upload Image/PDF
  │
Validation
  │
Image Enhancement
  │
OCR Adapter
  │
OCR Text
  │
Report Classification
  │
Metadata Extraction
  │
Result Extraction
  │
Normalization
  │
JSON Response
```

---

# 5. Sequence Diagram

## Speech

```text
User
 │
 │ Upload Audio
 ▼
FastAPI
 │
 ▼
Speech Service
 │
 ▼
Speech Adapter
 │
 ▼
Whisper / Mock
 │
 ▼
Transcript
 │
 ▼
Response
```

## Medical Report

```text
User
 │
 │ Upload Report
 ▼
FastAPI
 │
 ▼
Document Service
 │
 ▼
Image Enhancement
 │
 ▼
OCR Adapter
 │
 ▼
OCR Output
 │
 ▼
Extraction Engine
 │
 ▼
Normalizer
 │
 ▼
Response
```

---

# 6. Adapter Pattern

```text
                ISpeechProvider
                       ▲
      ┌────────────────┼────────────────┐
      │                │                │
WhisperAdapter  OpenAIAdapter  MockSpeechAdapter


                IOCRProvider
                       ▲
      ┌────────────────┼────────────────┐
      │                │                │
 PaddleAdapter  GoogleAdapter   MockOCRAdapter
```

Business logic never depends on provider SDKs.

---

# 7. Data Flow

## Speech

Audio
→ Validation
→ Provider
→ Transcript
→ Language Detection
→ Response

## Medical Report

Image/PDF
→ Enhancement
→ OCR
→ Classification
→ Metadata
→ Test Extraction
→ Normalization
→ JSON

---

# 8. Error Handling

Validation errors:
- Unsupported format
- File too large
- Empty file

Speech errors:
- Silent audio
- Corrupted audio

Document errors:
- Invalid laboratory report
- OCR failure
- Missing metadata
- Empty result table

Errors should always return structured JSON responses.

---

# 9. Configuration

Environment variables determine:

- Active speech provider
- Active OCR provider
- Mock mode
- API credentials
- Logging level

Changing providers must never require code changes.

---

# 10. Mock vs Real Providers

```text
            Settings (.env)
                  │
      ┌───────────┴───────────┐
      │                       │
    mock                   real
      │                       │
Mock Adapter         Whisper/PaddleOCR
```

Default Docker configuration uses mock providers.

---

# 11. Testing Strategy

Unit Tests
- Validation
- Normalization
- Classification

Integration Tests
- Speech endpoint
- OCR endpoint

Mock Tests
- Speech mock adapter
- OCR mock adapter

---

# 12. Scalability

The architecture supports future additions without modifying business logic.

Examples:
- New speech providers
- New OCR providers
- Additional document types
- Streaming transcription
- Queue-based processing
- Authentication
- Database persistence
- Monitoring & metrics

---

# 13. Engineering Principles

- Separation of Concerns
- Dependency Inversion
- Provider Independence
- Configuration over Code
- Testability
- Reusability
- Simplicity
- Maintainability
- Graceful Failure
- Production-inspired Design

---

# Conclusion

The proposed architecture intentionally favors simplicity, clean engineering, and maintainability over unnecessary complexity. It satisfies the assignment requirements while making future enhancements straightforward through provider abstraction and strict layer separation.
