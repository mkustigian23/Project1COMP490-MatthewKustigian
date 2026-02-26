import speech_recognition as sr
import pyttsx3
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
    base_url="http://localhost:11434",
    # format="json",                    #for stricter json output, may end up using this
)

# ────────────────────────────────────────────────
# Tools list
# ────────────────────────────────────────────────
tools = [
    get_current_datetime,
    get_my_bookings_today,
    get_bookings_for_room,
    list_available_rooms_now_or_soon,
]


agent = create_agent(
    llm,
    tools,
)

# speech setup
_engine = None

def get_tts_engine():
    global _engine
    if _engine is None:
        import pyttsx3
        _engine = pyttsx3.init()
    return _engine
recognizer = sr.Recognizer()

def speak(text: str):
    print("\nSpeaking:", text)
    engine = get_tts_engine()
    engine.say(text)
    engine.runAndWait()


# Main voice loop
print("Voice agent started (updated LangChain/LangGraph + local Ollama).")
print("Make sure Ollama is running with your model pulled.")
print("Say 'exit' or 'quit' to stop.")
print("Example questions:")
print("  - Do I have any bookings today?")
print("  - What rooms are available right now?")
print("  - When is my reservation for Room A?")

while True:
    try:
        with sr.Microphone() as source:
            print("\nListening...")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            audio = recognizer.listen(source, timeout=8, phrase_time_limit=12)

        text = recognizer.recognize_google(audio)
        print(f"You said: {text}")

        if any(word in text.lower() for word in ["exit", "quit", "stop", "bye"]):
            speak("Goodbye!")
            break

        # Invoke agent (LangGraph style – message-based)
        response = agent.invoke({
            "messages": [HumanMessage(content=text)]
        })

        # Get final answer from last message
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