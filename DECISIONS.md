# Architectural Decisions Record (DECISIONS.md)

## 1. Speech Recognition Engine: Faster-Whisper

### Context
The requirement calls for a speech recognition service supporting Bengali and English speech, automatic language detection, and audio processing.

### Decision
We selected **Faster-Whisper** (`faster-whisper`), a CTranslate2 re-implementation of OpenAI's Whisper model.

### Rationale
- **Inference Speed**: Up to 4x faster than standard PyTorch Whisper implementation with lower memory usage.
- **Bengali & English Support**: Robust multilingual support and zero-shot language identification out of the box.
- **Offline / Local Execution**: Runs locally without depending on third-party cloud APIs.
- **Quantization Support**: Runs efficiently on CPU using `int8` quantization.

---

## 2. OCR Engine: PaddleOCR

### Context
The requirement calls for an OCR engine to extract text from medical laboratory images and PDFs.

### Decision
We selected **PaddleOCR** (`paddleocr`) with OpenCV preprocessing.

### Rationale
- **Structured Bounding Box & Angle Detection**: Provides word/line bounding boxes and text line rotation detection (`use_angle_cls=True`).
- **High Tabular & Document Accuracy**: Performs exceptionally well on printed tabular forms, invoices, and clinical lab sheets.
- **Provider Independence**: Wrapped behind `IOCRProvider` interface, allowing plug-and-play substitution with Azure Read API or Google Cloud Vision.

---

## 3. Mock Provider Strategy & Default Docker Behavior

### Context
Reviewers evaluating the take-home project should be able to run the container immediately without downloading multi-gigabyte neural models or configuring cloud secret keys.

### Decision
We implemented mock providers (`MockSpeechAdapter` and `MockOCRAdapter`) and made `SPEECH_PROVIDER=mock` and `OCR_PROVIDER=mock` the default configuration in Docker.

### Rationale
- **Zero Configuration Setup**: Evaluators can run `docker-compose up` immediately.
- **Deterministic Integration Testing**: Test suites run fast and reproducibly offline.
- **Provider Switching**: Simply changing `.env` variables switches the runtime to real Faster-Whisper or PaddleOCR adapters without modifying code.

---

## 4. Preservation of Raw OCR Lines (`raw_line`)

### Context
Section 7, Stage 4 of the Design Specification requires storing every detected row exactly as OCR produced it.

### Decision
Each `TestResult` schema explicitly mandates a non-null `raw_line: str` field containing the verbatim OCR text row.

### Rationale
- **Auditability & Traceability**: Allows clinical downstream users to trace extracted values back to original document text lines.
- **Debugging & Evaluation**: Simplifies debugging regex/normalizer extraction bugs.

---

## 5. Domain Knowledge Dataset for Stage 8 Validation

### Context
Distinguishing valid laboratory documents from general clinical prescriptions or billing receipts without relying on fragile OCR rules.

### Decision
We created `LabDatasetValidator` in `app/models/lab_dataset.py` containing a comprehensive medical knowledge base of test names, synonyms, standard units, and expected ranges.

### Rationale
- **Three-Tier Validation Criteria**:
  1. Metadata + Known Tests -> Valid Lab Report.
  2. Metadata + No Tests -> Valid Report with Empty Results.
  3. No Metadata + No Known Features -> Invalid Laboratory Report.
- **Extensible**: Allows loading user-provided CSV/JSON lab reference datasets dynamically at runtime.

---

## 6. Real-Time Streaming via WebSocket for Live Microphone Transcription

### Context
Section 2 and Section 5 of the Design Specification require support for both batch audio file uploads and real-time live microphone transcription.

### Decision
We implemented a dedicated WebSocket endpoint (`/api/v1/speech/stream`) for live microphone input alongside the standard REST POST upload endpoint (`/api/v1/speech/transcribe`).

### Rationale
- **Low Latency & Continuous Streaming**: HTTP POST is request-response based, requiring the client to complete recording, encode a full audio file, and wait for a single response. WebSocket provides a persistent full-duplex TCP connection, allowing continuous binary audio chunks (PCM bytes) to stream from the microphone to the server with near real-time incremental feedback.
- **Direct Pipeline Routing (Skipping File Recognition)**: Per Section 5 of the design specification, live microphone input bypasses file format validation and file type routing rules, sending raw PCM frames directly to the speech provider's stream processor.
- **Protocol Efficiency & Session Control**: A single WebSocket connection handles session initialization (`{"type": "config", "sample_rate": 16000, "language": "bn"}`), continuous audio transmission without HTTP header overhead, and stream lifecycle management (`{"type": "stop"}`).

