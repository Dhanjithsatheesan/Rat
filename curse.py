import ctypes
import subprocess
import sys
import threading
import time
import pygame
import win32api
import win32con
import win32gui
import os
import cv2

# Maximize and optionally set OpenCV window always on top
def make_cv2_window_topmost(window_name):
    def set_topmost():
        time.sleep(0.5)
        hwnd = win32gui.FindWindow(None, window_name)
        if hwnd:
            win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                                  win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
    threading.Thread(target=set_topmost, daemon=True).start()

# Lock mouse
def block_mouse():
    def lock():
        while True:
            win32api.SetCursorPos((960, 540))
            time.sleep(0.01)
    threading.Thread(target=lock, daemon=True).start()

block_mouse()

# Play sound and show ghost
def play_scare():
    ghost_path = os.path.join(os.getcwd(), "ghost.png")
    sound_path = os.path.join(os.getcwd(), "ghost.wav")

    # Set system volume to max
    subprocess.call(["nircmd.exe", "setsysvolume", "65535"])

    try:
        pygame.mixer.init()
    except Exception as e:
        print("[!] Failed to initialize sound:", e)
        return

    # Play ghost sound
    if os.path.exists(sound_path):
        try:
            pygame.mixer.music.load(sound_path)
            pygame.mixer.music.play()
        except Exception as e:
            print("[!] Failed to play sound:", e)

    # Show ghost image
    if os.path.exists(ghost_path):
        img = cv2.imread(ghost_path)
        if img is None:
            print("[!] OpenCV failed to load the image.")
            return

        cv2.namedWindow("ghost", cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty("ghost", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

        make_cv2_window_topmost("ghost")  # force image window to stay on top

        while pygame.mixer.music.get_busy():
            cv2.imshow("ghost", img)
            if cv2.waitKey(1) == 27:
                break
        cv2.destroyAllWindows()
    else:
        print("[!] Ghost image file not found.")

if __name__ == "__main__":
    play_scare()
