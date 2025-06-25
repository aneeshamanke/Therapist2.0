# app.py
# The main Flask web server for the TherapistAI application.

from flask import Flask, render_template, request, jsonify, session
import os
import secrets
import prompts
import llm_service

# Initialize the Flask App
app = Flask(__name__)
# Set a secret key for session management. In a production environment,
# this should be a long, random, and secret string.
app.secret_key = secrets.token_hex(16)


# --- Helper Function for Session Serialization ---

def serialize_history(history):
    """
    Converts a list of Gemini's Content objects into a JSON-serializable format.
    This is the FIX for the 'not JSON serializable' error.
    """
    serializable_history = []
    for item in history:
        # Each 'item' is a Content object with 'role' and 'parts'
        serializable_history.append({
            "role": item.role,
            # Each 'part' in 'parts' has a 'text' attribute
            "parts": [part.text for part in item.parts]
        })
    return serializable_history


# --- Routes ---

@app.route('/')
def index():
    """
    Renders the main chat page.
    """
    # Clear any previous session data when the user first visits
    session.clear()
    return render_template('index.html')


@app.route('/start_session', methods=['POST'])
def start_session():
    """
    Initializes a new chat session based on the topic selected by the user.
    """
    data = request.json
    topic = data.get('topic')

    if not topic:
        return jsonify({"error": "Topic not provided"}), 400

    system_prompt = prompts.get_prompt(topic)
    model = llm_service.initialize_model(system_prompt)
    if not model:
        return jsonify({"error": "Failed to initialize AI model"}), 500
    
    chat = llm_service.start_chat(model)
    
    # **FIX:** Instead of storing the complex object, store the *serialized* history.
    session['chat_history'] = serialize_history(chat.history)
    session['topic'] = topic

    print(f"New session started with topic: {topic}")
    return jsonify({"status": "success", "message": "Session started."})


@app.route('/send_message', methods=['POST'])
def send_message():
    """
    Handles sending a user's message to the AI and returning the response.
    """
    if 'chat_history' not in session:
        return jsonify({"error": "Session not started. Please select a topic first."}), 400

    data = request.json
    user_message = data.get('message')
    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    # **FIX:** The history from the session is already in a simple, serializable format.
    # The Gemini model can be initialized directly from this format.
    system_prompt = prompts.get_prompt(session.get('topic', 'general'))
    model = llm_service.initialize_model(system_prompt)
    chat = model.start_chat(history=session['chat_history'])

    # Send the message and get the response
    ai_response = llm_service.send_message(chat, user_message)

    # **FIX:** After getting a response, re-serialize the now-updated history
    # before saving it back to the session.
    session['chat_history'] = serialize_history(chat.history)
    
    return jsonify({"response": ai_response})


# --- Main Execution ---
if __name__ == '__main__':
    # To run this:
    # 1. Make sure you have installed Flask: pip install Flask
    # 2. Set your GOOGLE_API_KEY environment variable.
    # 3. Run this file: python app.py
    # 4. Open your web browser to http://127.0.0.1:5000
    app.run(debug=True)
