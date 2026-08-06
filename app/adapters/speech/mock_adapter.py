"""
Mock Speech Provider.

Returns realistic mock transcription data for testing and
Docker-default operation without requiring model downloads
or API keys. Supports both Bengali and English mock responses.
"""

import random
from typing import Optional

from app.adapters.speech.base import ISpeechProvider, TranscriptResult, TranscriptSegment


# Realistic mock transcription samples
_MOCK_TRANSCRIPTS = {
    "en": [
        "The patient was admitted to the hospital with complaints of chest pain and shortness of breath. "
        "Initial examination revealed elevated blood pressure and irregular heart rhythm.",
        "Laboratory results indicate normal complete blood count with slightly elevated liver enzymes. "
        "The attending physician recommended further imaging studies.",
        "The follow-up appointment is scheduled for next week. "
        "The patient should continue current medication and maintain a low-sodium diet.",
    ],
    "bn": [
        "রোগীকে বুকে ব্যথা এবং শ্বাসকষ্টের অভিযোগ নিয়ে হাসপাতালে ভর্তি করা হয়েছিল। "
        "প্রাথমিক পরীক্ষায় উচ্চ রক্তচাপ এবং অনিয়মিত হৃদস্পন্দন ধরা পড়ে।",
        "পরীক্ষাগারের ফলাফলে সম্পূর্ণ রক্ত গণনা স্বাভাবিক এবং লিভারের এনজাইম সামান্য বেশি দেখা গেছে। "
        "চিকিৎসক আরও ইমেজিং পরীক্ষার পরামর্শ দিয়েছেন।",
        "পরবর্তী ফলো-আপ অ্যাপয়েন্টমেন্ট আগামী সপ্তাহে নির্ধারিত। "
        "রোগীকে বর্তমান ওষুধ চালিয়ে যেতে এবং কম লবণযুক্ত খাদ্য বজায় রাখতে হবে।",
    ],
}


class MockSpeechAdapter(ISpeechProvider):
    """
    Mock speech provider for testing and offline usage.

    Returns realistic pre-defined transcription data to simulate
    real provider behavior without requiring external dependencies.
    """

    @property
    def provider_name(self) -> str:
        """Return the name of this provider."""
        return "mock"

    def transcribe(
        self,
        audio_bytes: bytes,
        filename: str = "audio.wav",
        language: Optional[str] = None,
    ) -> TranscriptResult:
        """
        Return a mock transcription result.

        Simulates real transcription with realistic timing data.
        Language is auto-detected if not specified (randomly chosen).
        """
        if not audio_bytes:
            raise ValueError("Empty audio file provided")

        # Simulate language detection
        detected_lang = language if language in ("en", "bn") else random.choice(["en", "bn"])
        transcript_text = random.choice(_MOCK_TRANSCRIPTS[detected_lang])

        # Simulate realistic segment timing
        words = transcript_text.split()
        words_per_segment = max(5, len(words) // 3)
        segments = []
        current_time = 0.0

        for i in range(0, len(words), words_per_segment):
            segment_words = words[i : i + words_per_segment]
            segment_text = " ".join(segment_words)
            duration = len(segment_words) * 0.35  # ~0.35s per word
            segments.append(
                TranscriptSegment(
                    start=round(current_time, 2),
                    end=round(current_time + duration, 2),
                    text=segment_text,
                    confidence=round(random.uniform(0.85, 0.99), 4),
                )
            )
            current_time += duration + 0.2  # small pause between segments

        total_duration = segments[-1].end if segments else 0.0

        return TranscriptResult(
            text=transcript_text,
            language=detected_lang,
            language_confidence=round(random.uniform(0.90, 0.99), 4),
            duration_seconds=round(total_duration, 2),
            segments=segments,
            provider_name=self.provider_name,
        )

    def transcribe_stream(
        self,
        audio_chunk: bytes,
        sample_rate: int = 16000,
        language: Optional[str] = None,
    ) -> TranscriptResult:
        """
        Return a mock streaming transcription result.

        Simulates real-time transcription of an audio chunk.
        """
        detected_lang = language if language in ("en", "bn") else random.choice(["en", "bn"])

        # Shorter text for streaming chunks
        chunk_texts = {
            "en": [
                "The patient reported mild discomfort.",
                "Blood pressure reading is normal.",
                "No significant findings at this time.",
                "Recommended follow-up in two weeks.",
            ],
            "bn": [
                "রোগী হালকা অস্বস্তির কথা জানিয়েছেন।",
                "রক্তচাপের মান স্বাভাবিক।",
                "এই সময়ে কোনো উল্লেখযোগ্য ফলাফল নেই।",
                "দুই সপ্তাহের মধ্যে ফলো-আপ করার পরামর্শ দেওয়া হয়েছে।",
            ],
        }

        text = random.choice(chunk_texts[detected_lang])

        return TranscriptResult(
            text=text,
            language=detected_lang,
            language_confidence=round(random.uniform(0.90, 0.99), 4),
            duration_seconds=round(len(audio_chunk) / (sample_rate * 2), 2),
            segments=[
                TranscriptSegment(
                    start=0.0,
                    end=round(len(audio_chunk) / (sample_rate * 2), 2),
                    text=text,
                    confidence=round(random.uniform(0.85, 0.99), 4),
                )
            ],
            provider_name=self.provider_name,
        )
