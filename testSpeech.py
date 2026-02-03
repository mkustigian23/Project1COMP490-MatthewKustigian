import unittest
import os
import json
from vosk import Model, KaldiRecognizer
import wave

from speechToText import listen_and_transcribe
#Fixed now should pass all tests


class TestVoskTranscription(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.model_path = "vosk-model-small-en-us-0.15"


    def test_transcribe_known_audio(self):
        # This is a very short public-domain WAV someone uploaded years ago that I found on GitHub
        # saying roughly: "I am female"
        audio_file = "test-female.wav"

        self.assertTrue(os.path.exists(audio_file), "Test audio file missing in CI")

        text = listen_and_transcribe(audio_file, self.model_path)

        text = text.lower().strip()
        print("Recognized:", text)


        self.assertTrue(
            any(word in text for word in ["female", "i am female", "i'm female"]),
            f"Expected 'female' in transcription, got: '{text}'"
        )


if __name__ == "__main__":
    unittest.main()