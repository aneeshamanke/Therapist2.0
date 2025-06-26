# llm_service.py
# This module handles all interactions with the Google Gemini API.

import google.generativeai as genai
from dotenv import load_dotenv
load_dotenv() 
import os
import json
# MODIFIED: Import the new recommendation prompt
from prompts import INSIGHTS_PROMPT, EXERCISE_RECOMMENDATION_PROMPT,GOAL_EXTRACTION_PROMPT

# --- Configuration ---
try:
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
except KeyError:
    print("API Key Not Found! Please set the GOOGLE_API_KEY environment variable.")
    exit()

MODEL_NAME = "gemini-1.5-flash" # Using a powerful model

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
        print("\nAI is thinking...")
        response = chat_session.send_message(message)
        return response.text
    except Exception as e:
        print(f"Error sending message to LLM: {e}")
        return "I'm sorry, an error occurred on my end. Let's try that again."

# --- NEW: Function to analyze chat history and recommend an exercise ---
def recommend_exercise(chat_history: list):
    """
    Analyzes a chat history to recommend a guided exercise.
    Args:
        chat_history: A list of dicts representing the conversation history 
                      from the model ('role' and 'parts').
    Returns:
        A keyword string (e.g., 'SUGGEST_COGNITIVE_REFRAMING') or None.
    """
    if not chat_history or len(chat_history) < 2:  # Need at least one user/ai exchange
        return None

    # Use a fresh, un-instructed model for this specific classification task
    recommendation_model = genai.GenerativeModel(MODEL_NAME)
    
    # Format the history for the prompt. The history from app.py is a list of dicts.
    full_conversation = "\n".join([f"{item.role}: { item.parts[0].text}" for item in chat_history])
    prompt = EXERCISE_RECOMMENDATION_PROMPT + full_conversation
    
    try:
        print("\nAnalyzing for exercise recommendation...")
        response = recommendation_model.generate_content(prompt)
        # Clean up the response to ensure it's just the keyword
        keyword = response.text.strip().upper()
        if "SUGGEST_COGNITIVE_REFRAMING" in keyword:
            return "SUGGEST_COGNITIVE_REFRAMING"
        if "SUGGEST_THREE_GOOD_THINGS" in keyword:
            return "SUGGEST_THREE_GOOD_THINGS"
        return None
    except Exception as e:
        print(f"Error generating exercise recommendation: {e}")
        return None

def get_insights(chat_history_lines: list):
    """
    MODIFIED: Analyzes a list of chat log lines to provide a summary.
    """
    if not chat_history_lines:
        return "There's no conversation history to analyze yet."

    insights_model = genai.GenerativeModel(MODEL_NAME)
    
    # Format the history for the prompt
    full_conversation = "\n".join(chat_history_lines)
    prompt = INSIGHTS_PROMPT + full_conversation
    
    try:
        print("\nAnalyzing your journal for insights...")
        response = insights_model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error generating insights: {e}")
        return "Sorry, I was unable to generate insights at this time."
    
def extract_goal_from_conversation(chat_history: list):
    """
    Uses the LLM to extract a structured goal from a completed conversation.
    Args:
        chat_history: A list of 'Content' objects from the Gemini model.
    Returns:
        A dictionary with the structured goal data, or None on error.
    """
    print("\nExtracting structured goal from conversation...")
    extraction_model = genai.GenerativeModel(MODEL_NAME)
    
    full_conversation = "\n".join([f"{item.role}: {item.parts[0].text}" for item in chat_history])
    prompt = GOAL_EXTRACTION_PROMPT + full_conversation

    try:
        response = extraction_model.generate_content(prompt)
        # The response should be a clean JSON string, which we can parse
        # Clean up the response to remove markdown backticks if they exist
        clean_json_string = response.text.strip().replace("```json", "").replace("```", "").strip()
        goal_data = json.loads(clean_json_string)
        return goal_data
    except Exception as e:
        print(f"Error extracting or parsing goal JSON: {e}")
        print(f"LLM response was: {response.text}")
        return None