"""
Speech Transcription Routes.

Provides REST and WebSocket endpoints for speech transcription:
- POST /api/v1/speech/transcribe — Upload audio file
- WebSocket /api/v1/speech/stream — Live microphone transcription
"""

import io
import json
import logging
import wave
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, WebSocket, WebSocketDisconnect

from app.schemas.common import ErrorResponse
from app.schemas.speech import SpeechTranscriptionRequest, SpeechTranscriptionResponse
from app.services.speech_service import SpeechService
from app.utils.file_validator import FileValidationError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/speech", tags=["Speech Transcription"])

# Lazily initialized service instance
_speech_service: Optional[SpeechService] = None


def _get_service() -> SpeechService:
    """Get or create the speech service singleton."""
    global _speech_service
    if _speech_service is None:
        _speech_service = SpeechService()
    return _speech_service


@router.post(
    "/transcribe",
    response_model=SpeechTranscriptionResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Transcribe Audio File",
    description=(
        "Upload an audio file for transcription. "
        "Supports WAV, MP3, FLAC, OGG, M4A, WMA, AAC, and WebM formats. "
        "Automatically detects Bengali or English speech."
    ),
)
async def transcribe_audio(
    file: UploadFile = File(..., description="Audio file to transcribe"),
    language: Optional[str] = Form(
        default=None,
        description="Language hint: 'en' for English, 'bn' for Bengali. Auto-detected if not specified.",
    ),
) -> SpeechTranscriptionResponse:
    """
    Transcribe an uploaded audio file.

    The service validates the file, processes it through the configured
    speech provider, detects the language, and returns a structured
    transcription response.
    """
    try:
        file_bytes = await file.read()
        filename = file.filename or "audio.wav"

        service = _get_service()
        result = await service.transcribe_file(
            file_bytes=file_bytes,
            filename=filename,
            language=language,
        )

        return result

    except FileValidationError as e:
        logger.warning(f"Validation error: {e.message}")
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error_code": e.error_code,
                "message": e.message,
            },
        )
    except RuntimeError as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error_code": "TRANSCRIPTION_ERROR",
                "message": str(e),
            },
        )
    except Exception as e:
        logger.exception(f"Unexpected error in speech transcription: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error_code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred during transcription.",
            },
        )


@router.post(
    "/transcribe-json",
    response_model=SpeechTranscriptionResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Transcribe Audio from Base64 JSON",
    description=(
        "Send a JSON payload containing base64-encoded audio for transcription. "
        "Supports WAV, MP3, FLAC, OGG, M4A, WMA, AAC, and WebM formats. "
        "Returns the complete detailed transcription response in JSON format."
    ),
)
async def transcribe_audio_json(
    body: SpeechTranscriptionRequest,
) -> SpeechTranscriptionResponse:
    """
    Transcribe audio from a base64-encoded JSON payload.

    Provides direct API support for callers operating with raw JSON requests.
    Returns the exact same detailed output schema as the frontend dashboard.
    """
    try:
        service = _get_service()
        result = await service.transcribe_base64(
            audio_base64=body.audio_base64,
            filename=body.filename or "audio.wav",
            language=body.language,
        )
        return result

    except FileValidationError as e:
        logger.warning(f"Validation error in JSON transcription: {e.message}")
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error_code": e.error_code,
                "message": e.message,
            },
        )
    except RuntimeError as e:
        logger.error(f"Transcription error in JSON transcription: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error_code": "TRANSCRIPTION_ERROR",
                "message": str(e),
            },
        )
    except Exception as e:
        logger.exception(f"Unexpected error in JSON speech transcription: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error_code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred during JSON transcription.",
            },
        )


def _pcm_to_wav(pcm_bytes: bytes, sample_rate: int = 16000) -> bytes:
    """Convert raw 16-bit Mono PCM bytes into a valid in-memory WAV file."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_bytes)
    return buf.getvalue()


@router.websocket("/stream")
async def stream_transcription(websocket: WebSocket):
    """
    WebSocket endpoint for real-time microphone transcription.

    Protocol:
    1. Client connects to ws://host/api/v1/speech/stream
    2. Client sends a JSON config message:
       {"type": "config", "sample_rate": 16000, "language": "bn"}
    3. Client streams 16-bit PCM audio chunks (or WAV/Ogg chunks) as binary WebSocket messages
    4. Server responds with JSON transcription updates:
       {"type": "partial", "text": "...", "language": "bn", "is_final": false}
    5. Client sends {"type": "stop"} to finalize the session:
       {"type": "final", "text": "...", "language": "bn", "is_final": true}
    """
    await websocket.accept()
    logger.info("WebSocket connection accepted for speech streaming")

    service = _get_service()
    sample_rate = 16000
    language = None
    session_audio_buffer = bytearray()

    try:
        while True:
            message = await websocket.receive()

            # Handle text messages (config / control)
            if "text" in message:
                try:
                    data = json.loads(message["text"])
                    msg_type = data.get("type", "")

                    if msg_type == "config":
                        sample_rate = data.get("sample_rate", 16000)
                        language = data.get("language")
                        session_audio_buffer.clear()
                        await websocket.send_json({
                            "type": "info",
                            "text": f"Configured: sample_rate={sample_rate}, language={language or 'auto'}",
                            "is_final": False,
                        })
                        logger.info(f"WebSocket configured: rate={sample_rate}, lang={language}")

                    elif msg_type == "stop":
                        if len(session_audio_buffer) > 0:
                            if session_audio_buffer[:4] in (b"RIFF", b"OggS", b"\xff\xfb", b"fLaC"):
                                audio_bytes = bytes(session_audio_buffer)
                            else:
                                audio_bytes = _pcm_to_wav(bytes(session_audio_buffer), sample_rate=sample_rate)

                            try:
                                result = await service.transcribe_file(
                                    file_bytes=audio_bytes,
                                    filename="stream.wav",
                                    language=language,
                                )
                                await websocket.send_json({
                                    "type": "final",
                                    "text": result.transcript,
                                    "language": result.language,
                                    "confidence": result.language_confidence,
                                    "is_final": True,
                                })
                            except Exception as e:
                                logger.error(f"Final transcription error: {e}")
                                await websocket.send_json({
                                    "type": "final",
                                    "text": "",
                                    "is_final": True,
                                })
                        else:
                            await websocket.send_json({
                                "type": "final",
                                "text": "",
                                "is_final": True,
                            })
                        logger.info("WebSocket session ended by client")
                        break

                except json.JSONDecodeError:
                    await websocket.send_json({
                        "type": "error",
                        "text": "Invalid JSON message",
                        "is_final": False,
                    })

            # Handle binary messages (audio chunks)
            elif "bytes" in message:
                audio_chunk = message["bytes"]

                if len(audio_chunk) == 0:
                    continue

                session_audio_buffer.extend(audio_chunk)

                # Process partial transcription when buffer has accumulated enough audio (~0.5s = 16000 bytes)
                if len(session_audio_buffer) >= 16000:
                    if session_audio_buffer[:4] in (b"RIFF", b"OggS", b"\xff\xfb", b"fLaC"):
                        audio_bytes = bytes(session_audio_buffer)
                    else:
                        audio_bytes = _pcm_to_wav(bytes(session_audio_buffer), sample_rate=sample_rate)

                    try:
                        result = await service.transcribe_file(
                            file_bytes=audio_bytes,
                            filename="stream.wav",
                            language=language,
                        )
                        await websocket.send_json({
                            "type": "partial",
                            "text": result.transcript,
                            "language": result.language,
                            "confidence": result.language_confidence,
                            "is_final": False,
                        })
                    except Exception as e:
                        logger.warning(f"Streaming partial transcription error: {e}")

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "text": f"Server error: {e}",
                "is_final": True,
            })
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
