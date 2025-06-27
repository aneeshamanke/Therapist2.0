# main.py
# The main entry point for the TherapistAI bot application.

import prompts
import llm_service
import voice_service
import exercises_service
import os

# This list will store the conversation for the insights feature.
# In a real app, this would be saved to a file or database.
conversation_log = []

def handle_conversation(topic: str):
    """Handles a standard conversational session on a given topic."""
    
    # 1. Get the appropriate system prompt
    system_prompt = prompts.get_prompt(topic)
    
    # 2. Initialize the model and chat session
    model = llm_service.initialize_model(system_prompt)
    if not model:
        voice_service.speak("I'm sorry, I'm having trouble getting set up right now. Please try again later.")
        return
        
    chat_session = llm_service.start_chat(model)

    # 3. Initial greeting
    voice_service.speak("We can start whenever you're ready.")
    
    # 4. Conversation loop
    while True:
        user_input = voice_service.listen()

        if user_input is None:
            # User was silent, just continue listening
            continue
            
        if 'quit' in user_input.lower():
            voice_service.speak("Thank you for talking with me. Take care.")
            break

        # Log the user's part of the conversation
        conversation_log.append(f"User: {user_input}")

        # Send to LLM and get response
        ai_response = llm_service.send_message(chat_session, user_input)
        
        # Log and speak the AI's response
        conversation_log.append(f": {ai_response}")
        voice_service.speak(ai_response)


def main_menu():
    """Displays the main menu and handles user selection."""
    while True:
        menu_text = """
Welcome to your personal wellness space. What would you like to do?
1. Talk about something on my mind.
2. Try a guided exercise.
3. Review my weekly insights.
Please say the number of your choice, or say 'quit' to exit.
        """
        print(menu_text)
        voice_service.speak("Welcome to your personal wellness space. What would you like to do? Please say, one, two, or three.")
        
        choice = voice_service.listen()

        if choice is None:
            continue
            
        if "one" in choice or "1" in choice:
            select_topic()
        elif "two" in choice or "2" in choice:
            select_exercise()
        elif "three" in choice or "3" in choice:
            insights = llm_service.get_insights(conversation_log)
            print(f"\n--- Your Weekly Insights ---\n{insights}")
            voice_service.speak(insights)
        elif "quit" in choice:
            voice_service.speak("Goodbye.")
            break
        else:
            voice_service.speak("I didn't understand that choice. Please say one, two, or three.")

def select_topic():
    """Lets the user select a conversation topic."""
    while True:
        topic_menu = """
What general topic would you like to focus on today?
1. Work or School
2. Relationships
3. Family
4. Personal Growth
5. Anxiety
6. Just a general chat
Please say the number of your choice.
        """
        print(topic_menu)
        voice_service.speak("What general topic would you like to focus on? Please say the number.")
        
        choice = voice_service.listen()
        topic_map = {"1": "work_school", "2": "relationships", "3": "family", "4": "personal_growth", "5": "anxiety", "6": "general"}
        
        # Check for numbers in the string
        chosen_topic = None
        if choice:
            for num, topic in topic_map.items():
                if num in choice:
                    chosen_topic = topic
                    break
        
        if chosen_topic:
            handle_conversation(chosen_topic)
            break
        else:
            voice_service.speak("Sorry, I didn't get that. Please say a number from one to six.")


def select_exercise():
    """Lets the user select a guided exercise."""
    while True:
        exercise_menu = """
Which guided exercise would you like to try?
1. Cognitive Reframing (to challenge negative thoughts)
2. Three Good Things (to focus on positives)
Please say one or two.
        """
        print(exercise_menu)
        voice_service.speak("Which exercise would you like to try? Please say one, or two.")

        choice = voice_service.listen()

        if choice is None:
            continue

        if "one" in choice or "1" in choice:
            exercises_service.run_cognitive_reframing()
            break
        elif "two" in choice or "2" in choice:
            exercises_service.run_three_good_things()
            break
        else:
            voice_service.speak("I didn't understand. Please say one or two.")

if __name__ == "__main__":
    # In a real application, you would load the conversation_log from a file here
    # e.g., if os.path.exists("log.txt"): with open("log.txt", "r") as f: conversation_log = f.readlines()
    main_menu()
    # And you would save the log here before exiting
    # e.g., with open("log.txt", "w") as f: f.writelines(line + '\n' for line in conversation_log)
    print("\nApplication finished.")

