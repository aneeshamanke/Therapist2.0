# voice_service.py
# This module handles all voice interactions:
# - Text-to-Speech (TTS) using pyttsx3
# - Speech-to-Text (STT) using SpeechRecognition

import pyttsx3
import speech_recognition as sr

# Initialize the TTS engine globally
tts_engine = pyttsx3.init()

def speak(text: str):
    """
    Converts text to speech and speaks it.
    Args:
        text: The text to be spoken.
    """
    try:
        tts_engine.say(text)
        tts_engine.runAndWait()
    except Exception as e:
        print(f"Error in TTS engine: {e}")


def listen() -> str | None:
    """
    Listens for user's voice input and converts it to text.
    Returns:
        The transcribed text as a string, or None if there was an error or timeout.
    """
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("\nListening...")
        recognizer.pause_threshold = 1.5  # More tolerant to pauses
        recognizer.adjust_for_ambient_noise(source, duration=1)
        try:
            audio = recognizer.listen(source, timeout=7, phrase_time_limit=45)
            print("Recognizing...")
            text = recognizer.recognize_google(audio)
            print(f"You said: {text}")
            return text
        except sr.UnknownValueError:
            speak("I'm sorry, I didn't quite catch that. Could you please say it again?")
            return None
        except sr.RequestError as e:
            print(f"Speech service error; {e}")
            speak("It seems I'm having trouble with my connection right now.")
            return None
        except sr.WaitTimeoutError:
            # This is not an error, the user was just silent.
            return None
