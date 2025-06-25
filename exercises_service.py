# exercises_service.py
# This module contains guided interactive exercises.

from voice_service import speak, listen
import time

def run_cognitive_reframing():
    """Guides the user through a Cognitive Reframing (CBT) exercise."""
    speak("Welcome to the Cognitive Reframing exercise. This helps us challenge and change unhelpful thoughts.")
    time.sleep(0.5)
    
    speak("To begin, please share a negative thought that has been on your mind recently.")
    thought = listen()
    if not thought:
        speak("That's okay. We can try this another time.")
        return

    speak(f"Thank you for sharing. Your thought is: '{thought}'. Now, let's gently examine it.")
    time.sleep(1)

    speak("What evidence do you have that supports this thought? What makes it feel true?")
    evidence_for = listen()
    if not evidence_for:
        speak("No problem. Thinking about evidence can be tough.")

    speak("Okay. Now, let's look at the other side. What evidence do you have that contradicts this thought, or suggests it might not be 100% true?")
    evidence_against = listen()
    if not evidence_against:
        speak("It's alright if nothing comes to mind right away.")

    speak("Thank you. The final step is to try and find a more balanced or alternative way of looking at the situation. Based on what we've discussed, is there a different perspective you could consider?")
    alternative_thought = listen()
    if not alternative_thought:
        speak("Finding an alternative can take time. No pressure at all.")
    else:
        speak(f"That's a great alternative: '{alternative_thought}'.")

    speak("You did a wonderful job with that exercise. Challenging our thoughts is hard work. Thank you for doing that with me.")


def run_three_good_things():
    """Guides the user through the 'Three Good Things' positive psychology exercise."""
    speak("Let's do the 'Three Good Things' exercise. This helps us notice the small joys in our day.")
    time.sleep(0.5)
    
    good_things = []
    for i in range(1, 4):
        speak(f"What is the number {i} good thing that happened today, no matter how small?")
        thing = listen()
        if thing:
            good_things.append(thing)
            speak("That's a lovely one. Thank you for sharing.")
        else:
            speak("It's okay if it's hard to think of one. Let's move to the next.")
    
    if good_things:
        speak("Thank you for sharing those positive moments with me. It's a great practice to notice the good in our lives.")
    else:
        speak("No worries at all. Some days are tougher than others. Thank you for trying the exercise with me.")

