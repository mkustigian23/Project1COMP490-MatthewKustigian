import json
import os
import wave
from datetime import datetime
import pyaudio
from vosk import Model, KaldiRecognizer


def get_recognizer(model_path: str, sample_rate: int = 16000) -> KaldiRecognizer:
    """Create and configure Vosk recognizer."""
    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"Vosk model not found at: {model_path}\n"
            "Download from: https://alphacephei.com/vosk/models"
        )

    model = Model(model_path)
    recognizer = KaldiRecognizer(model, sample_rate)
    recognizer.SetWords(False)
    recognizer.SetMaxAlternatives(0)
    return recognizer


def transcribe_file(file_path: str, model_path: str) -> str:
    """
    Transcribes a pre-recorded WAV file using Vosk.
    Used for unit tests and batch processing.
    """
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model not found: {model_path}")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Audio file not found: {file_path}")

    model = Model(model_path)
    wf = wave.open(file_path, "rb")

    if wf.getnchannels() != 1 or wf.getsampwidth() != 2:
        raise ValueError("Audio must be mono 16-bit PCM")

    sample_rate = wf.getframerate()
    if sample_rate not in [8000, 16000, 22050, 32000, 44100, 48000]:
        raise ValueError(f"Unsupported sample rate: {sample_rate} Hz")

    recognizer = KaldiRecognizer(model, sample_rate)
    recognizer.SetWords(False)
    recognizer.SetMaxAlternatives(0)

    result_text = ""
    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if recognizer.AcceptWaveform(data):
            result = json.loads(recognizer.Result())
            result_text += result.get("text", "") + " "

    final = json.loads(recognizer.FinalResult())
    result_text += final.get("text", "")

    wf.close()
    return result_text.strip()


def listen_and_transcribe(model_path: str, sample_rate: int = 16000):
    """
    Listen to microphone indefinitely, print final recognitions to console,
    and append them to a new timestamped file for this session.
    Stops with Ctrl+C.
    """
    recognizer = get_recognizer(model_path, sample_rate)

    p = pyaudio.PyAudio()

    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=sample_rate,
        input=True,
        frames_per_buffer=8192,  # larger buffer → fewer calls, but still low latency
    )

    print("\n🎤 Listening... (Speak into the microphone.)")
    print("Press Ctrl+C to stop and save.\n")

    # Unique file per run
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_file = f"transcription_{timestamp}.txt"

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(
            f"Transcription started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        )

        stream.start_stream()

        try:
            while True:
                data = stream.read(4000, exception_on_overflow=False)

                if recognizer.AcceptWaveform(data):
                    # Final result after pause/silence
                    result = json.loads(recognizer.Result())
                    text = result.get("text", "").strip()

                    if text:
                        print(text)
                        f.write(text + "\n")
                        f.flush()  # ensure it's written immediately

        except KeyboardInterrupt:
            print("\n\nStopping...")

        # Grab any partial final phrase that wasn't ended by silence
        final = json.loads(recognizer.FinalResult())
        final_text = final.get("text", "").strip()
        if final_text:
            print(final_text)
            f.write(final_text + "\n")

    stream.stop_stream()
    stream.close()
    p.terminate()

    print(f"\nSaved to: {os.path.abspath(output_file)}")


if __name__ == "__main__":
    MODEL_PATH = "vosk-model-small-en-us-0.15"

    try:
        listen_and_transcribe(MODEL_PATH)
    except Exception as e:
        print(f"Error: {e}")
        print("Common fixes:")
        print("  • Make sure the model folder exists")
        print("  • Check microphone is not in use by another app")
        print("  • Try sample_rate=44100 if 16000 doesn't work on your system")
