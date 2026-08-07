# Speech Transcription & Medical Lab Report Extraction Service

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)

An production-inspired AI backend service built with **FastAPI**, exposing two independent AI capabilities through clean REST and WebSocket APIs:
1. **Service 1 — Speech Transcription** (Bengali & English speech, audio files + real-time microphone stream via WebSocket, automatic language detection).
2. **Service 2 — Medical Laboratory Report Extraction** (Structured JSON extraction from images and multi-page PDFs, patient info, lab metadata, test results with raw OCR line preservation, and value normalization).

---

## 🌟 Architecture & Highlights

- **Clean Layered Architecture (`tests → api → services → adapters`)**: Decoupled 3-layer runtime design topped by an Automated API Testing Layer (`pytest` / `TestClient`). API endpoints handle HTTP/WebSocket routing; Service layer orchestrates business logic; Adapter layer manages AI engine abstractions.
- **Automated API Testing Layer**: Complete 3-tier testing suite (`tests/`) covering unit validation, HTTP REST API contracts, WebSocket streaming protocols, and edge cases.
- **Provider Independence & Adapter Pattern**: Configurable switching between real providers (`Faster-Whisper`, `PaddleOCR`) and lightweight offline `Mock` providers without changing a single line of application code.
- **Reviewer-Friendly Mock Mode**: Default Docker environment runs in mock mode requiring zero external API keys or large model downloads.
- **Multi-Stage Medical Report Pipeline**: Image enhancement (denoising, deskewing, CLAHE contrast, sharpening, adaptive thresholding), OCR, raw line preservation (`raw_line`), document classification, metadata & tabular result extraction, domain knowledge dataset validation, and value/unit/date normalization.

---

## 🎨 Interactive Web Frontend

The service includes a modern, responsive single-page web UI served directly at the root URL (`http://localhost:8000/`):
- **Speech Module**: Supports audio file drag-and-drop upload and **Live Microphone streaming via WebSockets**. Displays full transcripts, automatic detected language badges (Whisper detection), duration, confidence, and timed segments.
- **Medical Lab Report Module**: Supports image and multi-page PDF uploads. Displays patient information, lab metadata, structured test result tables (with High/Low/Normal flags), handles invalid/empty reports gracefully, and offers expandable raw OCR line output.

---

## 🚀 Quick Start (Docker)

Run the service locally with Docker Compose (Mock Mode by default for instant evaluation):

```bash
docker compose up --build
```

To run with **real AI models** (Whisper for speech & PaddleOCR for document extraction):

```bash
docker compose -f docker-compose.real.yml up --build
```

The service will be available at:
- **Web App (UI)**: `http://localhost:8000/`
- **Interactive Swagger Docs**: `http://localhost:8000/docs`
- **ReDoc Documentation**: `http://localhost:8000/redoc`
- **Health Check**: `http://localhost:8000/api/v1/health`

---

## 💻 Local Installation (Non-Docker)

1. **Clone Repository & Create Virtual Environment**:
   ```bash
   git clone https://github.com/Rijwanul-10/Speech-Document-Extractor.git
   cd Speech-Document-Extractor
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**:
   ```bash
   cp .env.example .env
   ```
   Set active providers in `.env`:
   ```env
   SPEECH_PROVIDER=mock      # 'mock' or 'whisper'
   OCR_PROVIDER=mock         # 'mock' or 'paddleocr'
   ```

4. **Run Server**:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

---

## 📚 API Endpoints Overview

### 1. Health Check
`GET /api/v1/health`
Returns current system health and active provider configurations.

### 2. Speech Transcription
- `POST /api/v1/speech/transcribe`  
  Upload audio file (`.wav`, `.mp3`, `.flac`, `.ogg`, `.m4a`, `.webm`, etc.). Returns transcript, detected language, duration, and timed segments.
- `WebSocket /api/v1/speech/stream`  
  Real-time audio chunk streaming from live microphone inputs.

### 3. Medical Report Extraction
- `POST /api/v1/document/extract`  
  Upload report image (`.png`, `.jpg`, `.jpeg`, `.tiff`, `.bmp`, `.webp`) or PDF (`.pdf`). Returns structured JSON containing patient info, lab metadata, test result table, normalized values, and raw OCR text lines.

---

## 🧪 Running Tests

Generate synthetic test data and execute pytest suite:

```bash
python testdata/generate_samples.py
pytest tests/ -v
```

---

## 📄 License & Assignment Note
Built as part of Celloscope AI/ML Engineer Take-Home Assignment.
