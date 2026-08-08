"""
Integration tests for Speech Transcription REST & WebSocket Endpoints.
"""

import base64
from pathlib import Path

TESTDATA_DIR = Path(__file__).parent.parent / "testdata"


def test_health_check(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "speech_provider" in data


def test_transcribe_audio_file(client):
    audio_path = TESTDATA_DIR / "sample_audio.wav"
    with open(audio_path, "rb") as f:
        response = client.post(
            "/api/v1/speech/transcribe",
            files={"file": ("sample_audio.wav", f, "audio/wav")},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "transcript" in data
    assert data["language"] in ["en", "bn"]
    assert data["provider"] == "mock"


def test_transcribe_audio_json_success(client):
    audio_path = TESTDATA_DIR / "sample_audio.wav"
    with open(audio_path, "rb") as f:
        audio_b64 = base64.b64encode(f.read()).decode("utf-8")

    response = client.post(
        "/api/v1/speech/transcribe-json",
        json={
            "audio_base64": audio_b64,
            "filename": "sample_audio.wav",
            "language": "en",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "transcript" in data
    assert data["language"] == "en"
    assert data["detected_language"] == "English"
    assert "duration_seconds" in data
    assert "segments" in data
    assert "provider" in data
    assert data["filename"] == "sample_audio.wav"
    assert "timestamp" in data


def test_transcribe_audio_json_swagger_placeholder_language(client):
    """Test that default Swagger UI placeholder 'string' language is sanitized to auto-detect."""
    audio_path = TESTDATA_DIR / "sample_audio.wav"
    with open(audio_path, "rb") as f:
        audio_b64 = base64.b64encode(f.read()).decode("utf-8")

    response = client.post(
        "/api/v1/speech/transcribe-json",
        json={
            "audio_base64": audio_b64,
            "filename": "sample_audio.wav",
            "language": "string",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "transcript" in data
    assert data["language"] in ["en", "bn"]


def test_transcribe_audio_json_invalid_base64(client):
    response = client.post(
        "/api/v1/speech/transcribe-json",
        json={
            "audio_base64": "!!!not_valid_base64!!!",
            "filename": "sample_audio.wav",
        },
    )
    assert response.status_code == 400
    data = response.json()["detail"]
    assert data["error_code"] == "INVALID_BASE64"


def test_transcribe_invalid_format(client):
    response = client.post(
        "/api/v1/speech/transcribe",
        files={"file": ("test.txt", b"hello world", "text/plain")},
    )
    assert response.status_code == 400
    data = response.json()["detail"]
    assert data["error_code"] == "UNSUPPORTED_FORMAT"


def test_websocket_streaming(client):
    with client.websocket_connect("/api/v1/speech/stream") as websocket:
        # Send config
        websocket.send_json({"type": "config", "sample_rate": 16000, "language": "en"})
        res = websocket.receive_json()
        assert res["type"] == "info"

        # Send 16000 bytes of audio PCM data to trigger partial transcription
        websocket.send_bytes(b"\x00\x01" * 8000)
        chunk_res = websocket.receive_json()
        assert chunk_res["type"] == "partial"
        assert "text" in chunk_res

        # Send stop
        websocket.send_json({"type": "stop"})
        stop_res = websocket.receive_json()
        assert stop_res["type"] == "final"
        assert stop_res["is_final"] is True

