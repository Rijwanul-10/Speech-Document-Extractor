"""
Integration tests for Speech Transcription REST & WebSocket Endpoints.
"""

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
        websocket.send_json({"type": "config", "sample_rate": 16000, "language": "bn"})
        res = websocket.receive_json()
        assert res["type"] == "info"

        # Send audio chunk bytes
        websocket.send_bytes(b"\x00\x01" * 1000)
        chunk_res = websocket.receive_json()
        assert chunk_res["type"] == "final"
        assert len(chunk_res["text"]) > 0

        # Send stop
        websocket.send_json({"type": "stop"})
        stop_res = websocket.receive_json()
        assert stop_res["type"] == "info"
