import unittest
import os
import json
from vosk import Model, KaldiRecognizer
import wave


from speechToText import transcribe_file   # ← adjust this line


class TestVoskTranscription(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # This runs once before all tests
        cls.model_path = "vosk-model-small-en-us-0.15"
        # We'll download this in GitHub Actions — for local testing you can download it manually

    def test_transcribe_known_audio(self):
        # This is a very short public-domain WAV someone uploaded years ago
        # saying roughly: "I am female"
        audio_file = "test-female.wav"

        self.assertTrue(os.path.exists(audio_file), "Test audio file missing in CI")

        text = transcribe_file(audio_file, self.model_path)

        text = text.lower().strip()
        print("Recognized:", text)  # helpful when debugging

        # Loose check — real-life STT is not always perfect
        self.assertTrue(
            any(word in text for word in ["female", "i am female", "i'm female"]),
            f"Expected 'female' in transcription, got: '{text}'"
        )


if __name__ == "__main__":
    unittest.main()