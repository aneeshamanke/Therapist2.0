# llm_service.py
# This module handles all interactions with the Google Gemini API.

import google.generativeai as genai
from dotenv import load_dotenv
load_dotenv() 
import os
from prompts import INSIGHTS_PROMPT

# --- Configuration ---
try:
    # It's recommended to set your API key as an environment variable
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
except KeyError:
    print("----------------------------------------------------------------------")
    print("API Key Not Found! Please set the GOOGLE_API_KEY environment variable.")
    print("----------------------------------------------------------------------")
    exit()

MODEL_NAME = "gemini-2.0-flash"

def initialize_model(system_prompt: str):
    """
    Initializes the GenerativeModel with a specific system prompt.
    Args:
        system_prompt: The persona and instructions for the model.
    Returns:
        An initialized GenerativeModel instance.
    """
    try:
        return genai.GenerativeModel(MODEL_NAME, system_instruction=system_prompt)
    except Exception as e:
        print(f"Error initializing model: {e}")
        return None

def start_chat(model):
    """
    Starts a new chat session with the initialized model.
    Args:
        model: The initialized GenerativeModel instance.
    Returns:
        A chat session object.
    """
    return model.start_chat(history=[])

def send_message(chat_session, message: str):
    """
    Sends a message to the chat session and gets the response.
    Args:
        chat_session: The active chat session.
        message: The user's message string.
    Returns:
        The model's text response as a string.
    """
    try:
        print("\nAI is thinking...")
        response = chat_session.send_message(message)
        return response.text
    except Exception as e:
        print(f"Error sending message to LLM: {e}")
        return "I'm sorry, an error occurred on my end. Let's try that again."

def get_insights(chat_history: list):
    """
    Analyzes a chat history to provide a summary.
    Args:
        chat_history: A list of strings representing the conversation.
    Returns:
        A summary string from the AI.
    """
    if not chat_history:
        return "There's no conversation history to analyze yet."

    # Use a fresh model instance for this specific, non-conversational task
    insights_model = genai.GenerativeModel(MODEL_NAME)
    
    # Format the history for the prompt
    full_conversation = "\n".join(chat_history)
    prompt = INSIGHTS_PROMPT + full_conversation
    
    try:
        print("\nAnalyzing your journal for insights...")
        response = insights_model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error generating insights: {e}")
        return "Sorry, I was unable to generate insights at this time."

