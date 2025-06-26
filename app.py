# app.py
# The main Flask web server for the TherapistAI application.

from flask import Flask, render_template, request, jsonify, session
import os
import secrets
import prompts
import llm_service
import json
import uuid
import datetime

# Initialize the Flask App
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Define log files for conversations and structured goals
CONVO_LOG_FILE = "conversation_log.json"
GOALS_FILE = "goals.json"


# --- Helper Functions for Conversation Logs ---
def load_convo_logs():
    """Reads the entire JSON conversation log file into a dictionary."""
    try:
        with open(CONVO_LOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_history_for_topic(topic, history):
    """Saves the provided chat history to the JSON conversation log."""
    logs = load_convo_logs()
    logs[topic] = history
    try:
        with open(CONVO_LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=4)
    except Exception as e:
        print(f"Error writing to convo log file: {e}")

# --- NEW: Helper Functions for Goal Management ---
def load_goals():
    """Reads the JSON goals file into a list."""
    try:
        with open(GOALS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_goal(goal_data):
    """Appends a new structured goal to the goals file."""
    goals = load_goals()
    goals.append(goal_data)
    try:
        with open(GOALS_FILE, "w", encoding="utf-8") as f:
            json.dump(goals, f, indent=4)
        print(f"Successfully saved new goal: {goal_data['id']}")
    except Exception as e:
        print(f"Error writing to goals file: {e}")


# --- Serialization Helper ---
def serialize_history(history):
    """Converts a list of Gemini's Content objects into a JSON-serializable format."""
    # ... (function is unchanged from previous step)
    serializable_history = []
    for item in history:
        serializable_history.append({
            "role": item.role,
            "parts": [part.text for part in item.parts]
        })
    return serializable_history


# --- Routes ---

@app.route('/')
def index():
    """Renders the main chat page."""
    return render_template('index.html')


@app.route('/start_session', methods=['POST'])
def start_session():
    """Initializes a chat, loading previous history for the selected topic if it exists."""
    # ... (function is unchanged from previous step)
    data = request.json
    topic = data.get('topic')
    if not topic:
        return jsonify({"error": "Topic not provided"}), 400
    
    logs = load_convo_logs()
    topic_history = logs.get(topic, [])

    system_prompt = prompts.get_prompt(topic)
    model = llm_service.initialize_model(system_prompt)
    if not model:
        return jsonify({"error": "Failed to initialize AI model"}), 500
    
    chat = model.start_chat(history=topic_history)
    
    initial_ai_message = None
    if not topic_history:
        initial_ai_message = "We can start whenever you're ready."
        if topic in ["cognitive_reframing", "three_good_things", "goal_setting"]:
            initial_ai_message = llm_service.send_message(chat, "Let's begin.")
            save_history_for_topic(topic, serialize_history(chat.history))

    session['chat_history'] = serialize_history(chat.history)
    session['topic'] = topic

    return jsonify({
        "status": "success",
        "history": session['chat_history'],
        "initial_message": initial_ai_message
    })


@app.route('/send_message', methods=['POST'])
def send_message():
    """
    MODIFIED: Handles sending a message and triggers goal extraction upon completion.
    """
    if 'chat_history' not in session:
        return jsonify({"error": "Session not started."}), 400

    data = request.json
    user_message = data.get('message')
    current_topic = session.get('topic')

    if not user_message or not current_topic:
        return jsonify({"error": "No message or topic provided"}), 400

    system_prompt = prompts.get_prompt(current_topic)
    model = llm_service.initialize_model(system_prompt)
    chat = model.start_chat(history=session['chat_history'])

    ai_response = llm_service.send_message(chat, user_message)

    # --- NEW: Logic to detect goal setting completion and save the goal ---
    if current_topic == "goal_setting" and "GOAL_SET_COMPLETE" in ai_response:
        # Extract the structured goal
        goal_data = llm_service.extract_goal_from_conversation(chat.history)
        if goal_data:
            # Add metadata to the extracted goal
            goal_data['id'] = str(uuid.uuid4())
            goal_data['status'] = 'active'
            goal_data['date_set'] = datetime.date.today().isoformat()
            save_goal(goal_data)
        
        # Clean the special phrase from the response before sending to the user
        ai_response = ai_response.replace("GOAL_SET_COMPLETE", "").strip()
    else:
        # Regular exercise recommendation logic for other topics
        recommendation = llm_service.recommend_exercise(chat.history)
        if recommendation == "SUGGEST_COGNITIVE_REFRAMING":
            ai_response += "\n\nBy the way, it sounds like we're exploring some specific thought patterns. I have a 'Cognitive Reframing' exercise that could be helpful. You can find it in the main menu if you're ever interested."
        elif recommendation == "SUGGEST_THREE_GOOD_THINGS":
            ai_response += "\n\nI hear that things feel heavy right now. Sometimes focusing on small positives can help. I have a 'Three Good Things' exercise for this, which you can find in the main menu."

    # Update session and save conversation history
    updated_history = serialize_history(chat.history)
    session['chat_history'] = updated_history
    save_history_for_topic(current_topic, updated_history)
    
    return jsonify({"response": ai_response})


@app.route('/get_insights', methods=['GET'])
def get_insights():
    """Reads all conversation logs and returns insights."""
    # ... (function is unchanged from previous step)
    logs = load_convo_logs()
    if not logs:
        return jsonify({"insights": "There's no conversation history yet to review."})
    full_history_lines = []
    for topic, history in logs.items():
        full_history_lines.append(f"--- Conversation on {topic.replace('_', ' ').title()} ---")
        for message in history:
            role = "Asha" if message["role"] == "model" else "User"
            text = message["parts"][0]
            full_history_lines.append(f"{role}: {text}")
        full_history_lines.append("\n")
    if not full_history_lines:
        return jsonify({"insights": "There's no conversation history yet to review."})
    insights = llm_service.get_insights(full_history_lines)
    return jsonify({"insights": insights})

# --- Main Execution ---
if __name__ == '__main__':
    app.run(debug=True)