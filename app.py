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
from collections import Counter, defaultdict

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

CONVO_LOG_FILE = "conversation_log.json"
GOALS_FILE = "goals.json"

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

@app.route('/')
def index():
    """Renders the main chat page."""
    return render_template('index.html')

@app.route('/start_session', methods=['POST'])
def start_session():
    """Initializes a chat, loading previous history for the selected topic if it exists."""
    data = request.json
    topic = data.get('topic')
    if not topic:
        return jsonify({"error": "Topic not provided"}), 400
    
    logs = load_convo_logs()
    topic_history = logs.get(topic, [])

    history_for_model = [
        {"role": msg["role"], "parts": msg["parts"]} for msg in topic_history
    ]

    system_prompt = prompts.get_prompt(topic)
    model = llm_service.initialize_model(system_prompt)
    if not model:
        return jsonify({"error": "Failed to initialize AI model"}), 500
    
    chat = model.start_chat(history=history_for_model)
    
    initial_ai_message = None
    if not topic_history:
        initial_ai_message = "We can start whenever you're ready."
        if topic in ["cognitive_reframing", "three_good_things", "goal_setting"]:
            initial_ai_message = llm_service.send_message(chat, "Let's begin.")
        
        topic_history.append({"role": "model", "parts": [initial_ai_message]})
        save_history_for_topic(topic, topic_history)

    session['chat_history'] = topic_history
    session['topic'] = topic

    return jsonify({
        "status": "success",
        "history": topic_history,
        "initial_message": initial_ai_message
    })

@app.route('/send_message', methods=['POST'])
def send_message():
    """Handles sending a message, analyzes emotion, and triggers other logic."""
    if 'chat_history' not in session:
        return jsonify({"error": "Session not started."}), 400

    data = request.json
    user_message = data.get('message')
    current_topic = session.get('topic')
    current_history = session.get('chat_history', [])

    if not user_message or not current_topic:
        return jsonify({"error": "No message or topic provided"}), 400
        
    emotion = llm_service.analyze_emotion(user_message)
    user_message_entry = {
        "role": "user",
        "parts": [user_message],
        "emotion": emotion,
        "timestamp": datetime.datetime.now().isoformat()
    }
    current_history.append(user_message_entry)

    history_for_model = [
        {"role": msg["role"], "parts": msg["parts"]} for msg in current_history
    ]

    system_prompt = prompts.get_prompt(current_topic)
    model = llm_service.initialize_model(system_prompt)
    chat = model.start_chat(history=history_for_model)

    ai_response_text = llm_service.send_message(chat, user_message)

    if current_topic == "goal_setting" and "GOAL_SET_COMPLETE" in ai_response_text:
        goal_data = llm_service.extract_goal_from_conversation(chat.history)
        if goal_data:
            goal_data['id'] = str(uuid.uuid4())
            goal_data['status'] = 'active'
            goal_data['date_set'] = datetime.date.today().isoformat()
            save_goal(goal_data)
        ai_response_text = ai_response_text.replace("GOAL_SET_COMPLETE", "").strip()
    else:
        recommendation = llm_service.recommend_exercise(chat.history)
        if recommendation == "SUGGEST_COGNITIVE_REFRAMING":
            ai_response_text += "\n\nBy the way, it sounds like we're exploring some specific thought patterns..."
        elif recommendation == "SUGGEST_THREE_GOOD_THINGS":
            ai_response_text += "\n\nI hear that things feel heavy right now. Sometimes focusing on small positives can help..."

    current_history.append({"role": "model", "parts": [ai_response_text]})
    
    session['chat_history'] = current_history
    save_history_for_topic(current_topic, current_history)
    
    return jsonify({"response": ai_response_text})

@app.route('/get_insights', methods=['GET'])
def get_insights():
    """Provides a full data payload for the dashboard, including the comparison summary."""
    logs = load_convo_logs()
    goals = load_goals()

    if not logs:
        return jsonify({"error": "There's no conversation history yet to review."})

    full_convo_text = []
    for topic, history in logs.items():
        for message in history:
            parts = message.get("parts", [])
            if parts:
                full_convo_text.append(f"{message.get('role', 'unknown')}: {parts[0]}")
    summary = llm_service.get_insights(full_convo_text)

    all_emotions = []
    topic_message_counts = Counter()
    daily_emotions = defaultdict(lambda: Counter())
    
    for topic, history in logs.items():
        user_messages_in_topic = 0
        for message in history:
            if message.get('role') == 'user':
                user_messages_in_topic += 1
                emotion = message.get('emotion', 'Neutral')
                all_emotions.append(emotion)
                timestamp_str = message.get('timestamp')
                if timestamp_str:
                    date_key = timestamp_str.split('T')[0]
                    daily_emotions[date_key][emotion] += 1
        if user_messages_in_topic > 0:
            topic_message_counts[topic.replace('_', ' ').title()] = user_messages_in_topic

    comparison_summary = "Not enough data for a daily comparison yet."
    sorted_dates = sorted(daily_emotions.keys())
    
    if len(sorted_dates) >= 2:
        most_recent_day = sorted_dates[-1]
        previous_day = sorted_dates[-2]
        comparison_data_string = (
            f"Data for Previous Day ({previous_day}): {dict(daily_emotions[previous_day])}. "
            f"Data for Most Recent Day ({most_recent_day}): {dict(daily_emotions[most_recent_day])}"
        )
        comparison_summary = llm_service.get_daily_comparison_summary(comparison_data_string)
    elif len(sorted_dates) == 1:
        most_recent_day = sorted_dates[0]
        comparison_summary = f"It looks like we started our journey together on {most_recent_day}. I'm excited to see how things evolve!"

    active_goals = [goal for goal in goals if goal.get('status') == 'active']
    
    dashboard_data = {
        "summary": summary,
        "daily_comparison_summary": comparison_summary,
        "charts": {
            "emotion_distribution": dict(Counter(all_emotions)),
            "topic_distribution": dict(topic_message_counts),
        },
        "active_goals": active_goals
    }

    return jsonify(dashboard_data)

if __name__ == '__main__':
    app.run(debug=True)
