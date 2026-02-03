import unittest
import os
import json
from vosk import Model, KaldiRecognizer
import wave

# comment to retest code
from speechToText import transcribe_file


class TestVoskTranscription(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.model_path = "vosk-model-small-en-us-0.15"


    def test_transcribe_known_audio(self):
        audio_file = "sample_audio.wav"

        self.assertTrue(os.path.exists(audio_file), "Test audio file missing in CI")

        text = transcribe_file(audio_file, self.model_path)

        text = text.lower().strip()
        print("Recognized:", text)

        self.assertTrue(
            any(word in text for word in ["hello", "hello this is", "he low this in a short sample audio file for transcription testing"]),
            f"Expected 'hello' in transcription, got: '{text}'"
        )



if __name__ == "__main__":
    unittest.main()
