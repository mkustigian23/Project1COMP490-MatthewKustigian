# voice_agent.py
# Corrected: main loop guarded with if __name__ == "__main__" → safe for pytest / CI

import os
from datetime import datetime
from dotenv import load_dotenv

# ────────────────────────────────────────────────
# LangChain / LangGraph imports
# ────────────────────────────────────────────────
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama

# Your tools
from room_booking_client import (
    get_current_datetime,
    get_my_bookings_today,
    get_bookings_for_room,
    list_available_rooms_now_or_soon,
)

load_dotenv()

# ────────────────────────────────────────────────
# LLM – local Ollama (created at import time – safe, no hardware)
# ────────────────────────────────────────────────
llm = ChatOllama(
    model="ibm/granite4:1b-h",
    temperature=0.1,
    base_url="http://localhost:11434"
)

# ────────────────────────────────────────────────
# Tools
# ────────────────────────────────────────────────
tools = [
    get_current_datetime,
    get_my_bookings_today,
    get_bookings_for_room,
    list_available_rooms_now_or_soon,
]

# ────────────────────────────────────────────────
# Agent (created at import time – safe)
# ────────────────────────────────────────────────
agent = create_agent(llm, tools)

# ────────────────────────────────────────────────
# Lazy speech recognition & TTS
# ────────────────────────────────────────────────

_recognizer = None
def get_recognizer():
    global _recognizer
    if _recognizer is None:
        try:
            import speech_recognition as sr
            _recognizer = sr.Recognizer()
        except Exception as e:
            print(f"Warning: Speech recognizer failed to load: {e}")
            _recognizer = None
    return _recognizer


_engine = None
def get_tts_engine():
    global _engine
    if _engine is None:
        try:
            import pyttsx3
            _engine = pyttsx3.init()
        except Exception as e:
            print(f"Warning: TTS engine failed to load: {e}")
            _engine = None
    return _engine


def speak(text: str, _test_force: bool = False):
    print("\nSpeaking:", text)

    # Skip in real CI / GitHub Actions, but allow override for tests
    if not _test_force and ('CI' in os.environ or 'GITHUB_ACTIONS' in os.environ):
        return

    engine = get_tts_engine()
    if engine is None:
        return

    try:
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"TTS failed: {e}")


# ────────────────────────────────────────────────
# MAIN PROGRAM – only runs when script is executed directly
# Prevents pytest from executing the loop during import/collection
# ────────────────────────────────────────────────

if __name__ == "__main__":
    print("Voice agent started (updated LangChain/LangGraph + local Ollama).")
    print("Make sure Ollama is running with your model pulled.")
    print("Say 'exit' or 'quit' to stop.")
    print("Example questions:")
    print("  - Do I have any bookings today?")
    print("  - What rooms are available right now?")
    print("  - When is my reservation for Room A?")

    import speech_recognition as sr   # only imported here – safe for normal runs

    while True:
        try:
            # CI/test fallback – never reached in pytest
            if 'CI' in os.environ or 'GITHUB_ACTIONS' in os.environ or 'PYTEST_CURRENT_TEST' in os.environ:
                text = ""  # or raise SkipTest / exit gracefully – no input() in CI
                break      # exit loop immediately in automated env
            else:
                recognizer = get_recognizer()
                if recognizer is None:
                    text = input("Speech not available - enter text: ").strip()
                else:
                    with sr.Microphone() as source:
                        print("\nListening...")
                        recognizer.adjust_for_ambient_noise(source, duration=1)
                        audio = recognizer.listen(source, timeout=8, phrase_time_limit=12)
                    text = recognizer.recognize_google(audio)

            print(f"You said: {text}")

            if any(word in text.lower() for word in ["exit", "quit", "stop", "bye"]):
                speak("Goodbye!")
                break

            # Run agent
            response = agent.invoke({"messages": [HumanMessage(content=text)]})

            messages = response.get("messages", [])
            if messages:
                final_msg = messages[-1]
                answer = final_msg.content.strip() if hasattr(final_msg, "content") else str(final_msg)
            else:
                answer = "Sorry, I couldn't generate an answer."

            print("Answer:", answer)
            speak(answer)

        except sr.WaitTimeoutError:
            continue
        except sr.UnknownValueError:
            speak("Sorry, I didn't catch that. Could you repeat?")
        except sr.RequestError as e:
            print(f"Speech recognition error: {e}")
            speak("Problem with speech recognition right now.")
        except Exception as e:
            print(f"Error: {type(e).__name__}: {str(e)}")
            speak("Something went wrong. Please try again.")