# llm_service.py

import google.generativeai as genai
from dotenv import load_dotenv
load_dotenv()
import os
import json
from prompts import (
    INSIGHTS_PROMPT, EXERCISE_RECOMMENDATION_PROMPT, GOAL_EXTRACTION_PROMPT,
    EMOTION_ANALYSIS_PROMPT, DAILY_COMPARISON_PROMPT, GOAL_FEEDBACK_PROMPT
)

MODEL_NAME = "gemini-1.5-flash"

try:
    # It's recommended to set your API key as an environment variable
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
except KeyError:
    print("API Key Not Found! Please set the GOOGLE_API_KEY environment variable.")
    exit()

def initialize_model(system_prompt: str):
    """Initializes the GenerativeModel with a specific system prompt."""
    try:
        return genai.GenerativeModel(MODEL_NAME, system_instruction=system_prompt)
    except Exception as e:
        print(f"Error initializing model: {e}")
        return None

def start_chat(model):
    """Starts a new chat session with the initialized model."""
    return model.start_chat(history=[])

def send_message(chat_session, message: str):
    """Sends a message to the chat session and gets the response."""
    try:
        response = chat_session.send_message(message)
        return response.text
    except Exception as e:
        print(f"Error sending message to LLM: {e}")
        return "I'm sorry, an error occurred on my end. Let's try that again."

def get_insights(chat_history_lines: list):
    """Analyzes a list of chat log lines to provide a summary."""
    if not chat_history_lines:
        return "There's no conversation history to analyze yet."
    insights_model = genai.GenerativeModel(MODEL_NAME)
    full_conversation = "\n".join(chat_history_lines)
    prompt = INSIGHTS_PROMPT + full_conversation
    try:
        response = insights_model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error generating insights: {e}")
        return "Sorry, I was unable to generate insights at this time."

def extract_goal_from_conversation(chat_history: list):
    """Uses the LLM to extract a structured goal from a completed conversation."""
    extraction_model = genai.GenerativeModel(MODEL_NAME)
    full_conversation = "\n".join([f"{item.role}: {item.parts[0].text}" for item in chat_history])
    prompt = GOAL_EXTRACTION_PROMPT + full_conversation
    try:
        response = extraction_model.generate_content(prompt)
        clean_json_string = response.text.strip().replace("```json", "").replace("```", "").strip()
        goal_data = json.loads(clean_json_string)
        return goal_data
    except Exception as e:
        print(f"Error extracting or parsing goal JSON: {e}")
        return None

def analyze_emotion(user_message: str):
    """Uses the LLM to classify the primary emotion of a user's text."""
    if not user_message:
        return "Neutral"
    emotion_model = genai.GenerativeModel(MODEL_NAME)
    prompt = EMOTION_ANALYSIS_PROMPT + user_message
    try:
        response = emotion_model.generate_content(prompt)
        emotion = response.text.strip().capitalize()
        valid_emotions = ['Joy', 'Sadness', 'Anger', 'Fear', 'Surprise', 'Neutral']
        if emotion in valid_emotions:
            return emotion
        return "Neutral"
    except Exception as e:
        print(f"Error analyzing emotion: {e}")
        return "Neutral"

def get_daily_comparison_summary(comparison_data: str):
    """Uses the LLM to generate a human-like summary comparing two days."""
    if not comparison_data:
        return "Not enough data for a daily comparison yet. Let's talk more!"
    trend_model = genai.GenerativeModel(MODEL_NAME)
    prompt = DAILY_COMPARISON_PROMPT + comparison_data
    try:
        response = trend_model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error generating daily comparison summary: {e}")
        return "I had trouble analyzing the daily comparison right now."

def get_goal_feedback(chat_history: list):
    """Analyzes a goal-setting conversation to provide constructive feedback."""
    feedback_model = genai.GenerativeModel(MODEL_NAME)
    full_conversation = "\n".join([f"{item.role}: {item.parts[0].text}" for item in chat_history])
    prompt = GOAL_FEEDBACK_PROMPT + full_conversation
    try:
        response = feedback_model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error generating goal feedback: {e}")
        return "You've set a wonderful goal for yourself. Taking this step is a great achievement."
