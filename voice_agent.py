import os
import sys
from datetime import datetime
from dotenv import load_dotenv

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama

from room_booking_client import (
    get_current_datetime,
    get_my_bookings_today,
    get_bookings_for_room,
    list_available_rooms_now_or_soon,
)

load_dotenv()

llm = ChatOllama(
    model="ibm/granite4:1b-h",
    temperature=0.1,
    base_url="http://localhost:11434"
)

tools = [
    get_current_datetime,
    get_my_bookings_today,
    get_bookings_for_room,
    list_available_rooms_now_or_soon,
]


agent = create_agent(llm, tools)



_recognizer = None
def get_recognizer():
    global _recognizer
    if _recognizer is None:
        try:
            import speech_recognition as sr
            _recognizer = sr.Recognizer()
        except Exception as e:
            print(f"Warning: Could not initialize speech recognizer: {e}")
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
            print(f"Warning: Could not initialize TTS engine: {e}")
            _engine = None
    return _engine


def speak(text: str):
    """
    Speak text only if not in CI/test environment and TTS is available.
    """
    print("\nSpeaking:", text)

    if 'CI' in os.environ or 'GITHUB_ACTIONS' in os.environ or 'PYTEST_CURRENT_TEST' in os.environ:
        return

    engine = get_tts_engine()
    if engine is None:
        return

    try:
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"TTS error: {e}")



# main voice loop
print("Voice agent started (updated LangChain/LangGraph + local Ollama).")
print("Make sure Ollama is running with your model pulled.")
print("Say 'exit' or 'quit' to stop.")
print("Example questions:")
print("  - Do I have any bookings today?")
print("  - What rooms are available right now?")
print("  - When is my reservation for Room A?")

while True:
    try:
        # In CI / tests → skip real microphone input
        if 'CI' in os.environ or 'GITHUB_ACTIONS' in os.environ or 'PYTEST_CURRENT_TEST' in os.environ:
            text = input("CI/test mode - enter text input: ").strip()
            if not text:
                text = "what time is it"  # fallback for automated testing
        else:
            recognizer = get_recognizer()
            if recognizer is None:
                print("Speech recognition not available.")
                text = input("Enter text instead: ").strip()
            else:
                import speech_recognition as sr
                with sr.Microphone() as source:
                    print("\nListening...")
                    recognizer.adjust_for_ambient_noise(source, duration=1)
                    audio = recognizer.listen(source, timeout=8, phrase_time_limit=12)
                text = recognizer.recognize_google(audio)

        print(f"You said: {text}")

        if any(word in text.lower() for word in ["exit", "quit", "stop", "bye"]):
            speak("Goodbye!")
            break

        # Invoke agent
        response = agent.invoke({
            "messages": [HumanMessage(content=text)]
        })

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