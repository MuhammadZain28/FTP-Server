import tkinter as tk
from tkinter import ttk, scrolledtext
import socket
import threading
import os
import hashlib
from datetime import datetime
import json

class FTPServer:
    def __init__(self, host='127.0.0.1', port=21, data_port=20):
        self.host = host
        self.port = port
        self.data_port = data_port
        self.socket = None
        self.running = False
        self.clients = {}
        self.users = {
            'admin': hashlib.md5('password123'.encode()).hexdigest(),
            'user': hashlib.md5('user123'.encode()).hexdigest()
        }
        self.base_dir = './ftp_storage'
        os.makedirs(self.base_dir, exist_ok=True)
        self.log_callback = None

    def set_log_callback(self, callback):
        self.log_callback = callback

    def log(self, msg):
        if self.log_callback:
            self.log_callback(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

    def start(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)
            self.running = True
            self.log(f"FTP Server started on {self.host}:{self.port}")
            threading.Thread(target=self._accept_clients, daemon=True).start()
        except Exception as e:
            self.log(f"Error starting server: {e}")

    def _accept_clients(self):
        while self.running:
            try:
                client_socket, addr = self.socket.accept()
                self.log(f"Client connected: {addr}")
                threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, addr),
                    daemon=True
                ).start()
            except Exception as e:
                if self.running:
                    self.log(f"Accept error: {e}")

    def _handle_client(self, client_socket, addr):
        try:
            client_socket.send(b"220 Welcome to Simple FTP Server\r\n")
            authenticated = False
            current_user = None
            user_dir = None

            while True:
                cmd = client_socket.recv(1024).decode().strip()
                print(f"Received command from {addr}: {cmd}")
                if not cmd:
                    break
                parts = cmd.split(' ', 1)
                command = parts[0].upper()
                arg = parts[1] if len(parts) > 1 else ''

                if command == 'USER':
                    if arg in self.users:
                        client_socket.send(f"331 Password required for {arg}\r\n".encode())
                        current_user = arg
                    else:
                        client_socket.send(b"430 Invalid username\r\n")

                elif command == 'PASS':
                    if current_user:
                        pwd_hash = hashlib.md5(arg.encode()).hexdigest()
                        if pwd_hash == self.users[current_user]:
                            authenticated = True
                            user_dir = os.path.join(self.base_dir, current_user)
                            os.makedirs(user_dir, exist_ok=True)
                            client_socket.send(b"230 Login successful\r\n")
                            self.log(f"{addr} authenticated as {current_user}")
                        else:
                            client_socket.send(b"430 Invalid password\r\n")
                    else:
                        client_socket.send(b"503 Login with USER first\r\n")

                elif not authenticated:
                    client_socket.send(b"530 Not logged in\r\n")

                elif command == 'LIST':
                    self._send_list(client_socket, user_dir)

                elif command == 'CWD':
                    if arg:
                        new_dir = os.path.abspath(os.path.join(user_dir, arg))
                        print("NEW DIR:", new_dir)
                        if os.path.isdir(new_dir):
                            user_dir = new_dir
                            client_socket.send(b"250 Directory changed\r\n")
                        else:
                            client_socket.send(b"550 Directory not found\r\n")
                    else:
                        client_socket.send(b"500 No directory specified\r\n")

                elif command == 'CDUP':
                    print("Current user dir before CDUP:", user_dir)
                    parent = os.path.dirname(user_dir)
                    print("Parent dir:", parent)
                    user_dir = parent
                    client_socket.send(b"250 Directory changed\r\n")

                elif command == 'MKD':
                    if arg:
                        new_dir = os.path.join(user_dir, arg)
                        try:
                            os.makedirs(new_dir, exist_ok=True)
                            client_socket.send(b"257 Directory created\r\n")
                            self.log(f"Created directory: {new_dir}")
                        except Exception as e:
                            client_socket.send(f"550 Error: {e}\r\n".encode())
                            self.log(f"Error creating directory {new_dir}: {e}")

                elif command == 'DELE':
                    if arg:
                        file_path = os.path.join(user_dir, arg)
                        try:
                            if os.path.isfile(file_path):
                                os.remove(file_path)
                                client_socket.send(b"250 File deleted\r\n")
                                self.log(f"Deleted file: {file_path}")
                            else:
                                client_socket.send(b"550 File not found\r\n")
                                self.log(f"File not found for deletion: {file_path}")
                        except Exception as e:
                            client_socket.send(f"550 Error: {e}\r\n".encode())
                            self.log(f"Error deleting file {file_path}: {e}")

                elif command == 'RETR':
                    if arg:
                        self._send_file(client_socket, user_dir, arg)

                elif command == 'STOR':
                    if arg:
                        self._receive_file(client_socket, user_dir, arg)

                elif command == 'QUIT':
                    client_socket.send(b"221 Goodbye\r\n")
                    break

                elif command == 'HELP':
                    client_socket.send(b"214 Commands: LIST CWD CDUP MKD DELE RETR STOR QUIT\r\n")
                    self.log(f"Sent help to {addr}")

                else:
                    client_socket.send(b"502 Unknown command\r\n")
                    self.log(f"Unknown command from {addr}: {command}")

        except Exception as e:
            self.log(f"Client error {addr}: {e}")
        finally:
            client_socket.close()
            self.log(f"Client disconnected: {addr}")

    def _send_list(self, control_socket, path):
        try:
            control_socket.send(b"150 Opening data connection\r\n")


            data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            data_sock.bind(("0.0.0.0", 20))
            data_sock.listen(1)
            conn, addr = data_sock.accept()
            self.log(f"Sending directory listing to {addr}")


            lines = []
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                is_dir = os.path.isdir(item_path)
                size = os.path.getsize(item_path) if not is_dir else 0
                mod_time = datetime.fromtimestamp(os.path.getmtime(item_path)).strftime('%b %d %H:%M')
                lines.append({
                    "name": item,
                    "size": size,
                    "time": mod_time,
                    "dir": is_dir
                })
            listing = json.dumps(lines)


            conn.sendall(listing.encode())

            conn.close()
            data_sock.close()


            control_socket.send(b"226 Directory send complete\r\n")
            self.log("Directory listing sent successfully")

        except Exception as e:
            control_socket.send(f"550 Error: {e}\r\n".encode())
            self.log(f"Error sending directory listing: {e}")

    def _send_file(self, client_socket, user_dir, filename):
        try:
            user_dir = os.path.abspath(os.path.normpath(user_dir))
            file_path = os.path.abspath(os.path.normpath(os.path.join(user_dir, filename)))

            if not file_path.startswith(user_dir + os.sep):
                client_socket.send(b"550 Access denied\r\n")
                return

            if not os.path.isfile(file_path):
                client_socket.send(b"550 File not found\r\n")
                return
            client_socket.send(b"150 Opening data connection\r\n")
            data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            data_sock.bind(("0.0.0.0", self.data_port))
            data_sock.listen(1)
            conn, addr = data_sock.accept()

            with open(file_path, "rb") as f:
                while chunk := f.read(4096):
                    conn.sendall(chunk)

            conn.close()
            data_sock.close()

            client_socket.send(b"226 Transfer complete\r\n")
            self.log(f"Sent file: {filename}")

        except Exception as e:
            client_socket.send(f"550 Error: {e}\r\n".encode())

    def _receive_file(self, control_socket, user_dir, filename):
        try:
            user_dir = os.path.abspath(os.path.normpath(user_dir))
            file_path = os.path.abspath(os.path.normpath(os.path.join(user_dir, filename)))

            if not file_path.startswith(user_dir + os.sep):
                control_socket.send(b"550 Access denied\r\n")
                return

            control_socket.send(b"150 Opening data connection\r\n")

            data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            data_sock.bind(("0.0.0.0", self.data_port))
            data_sock.listen(1)
            conn, addr = data_sock.accept()
            self.log(f"Receiving file from {addr}")

            with open(file_path, "wb") as f:
                while True:
                    data = conn.recv(4096)
                    if not data:
                        break
                    f.write(data)

            conn.close()
            data_sock.close()

            control_socket.send(b"226 Transfer complete\r\n")
            self.log(f"Received file: {filename}")

        except Exception as e:
            control_socket.send(f"550 Error: {e}\r\n".encode())
            self.log(f"Error receiving file {filename}: {e}")


    def stop(self):
        self.running = False
        if self.socket:
            self.socket.close()
        self.log("Server stopped")


class FTPGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("FTP Server Manager")
        self.root.geometry("800x600")
        
        self.server = FTPServer()
        self.server.set_log_callback(self.add_log)
        
        ctrl_frame = ttk.Frame(root)
        ctrl_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.start_btn = ttk.Button(ctrl_frame, text="Start Server", command=self.start_server)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(ctrl_frame, text="Stop Server", command=self.stop_server, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(ctrl_frame, text="Status:").pack(side=tk.LEFT, padx=5)
        self.status_label = ttk.Label(ctrl_frame, text="Stopped", foreground="red")
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # Info Panel
        info_frame = ttk.LabelFrame(root, text="Server Info", padding=5)
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(info_frame, text="Host: 127.0.0.1").pack(anchor=tk.W)
        ttk.Label(info_frame, text="Port: 21").pack(anchor=tk.W)
        
        log_frame = ttk.LabelFrame(root, text="Server Log", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=20, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        ttk.Button(log_frame, text="Clear Log", command=self.clear_log).pack(pady=5)

    def start_server(self):
        self.server.start()
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_label.config(text="Running", foreground="green")

    def stop_server(self):
        self.server.stop()
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_label.config(text="Stopped", foreground="red")

    def add_log(self, msg):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, msg + '\n')
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def clear_log(self):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)


if __name__ == "__main__":
    root = tk.Tk()
    gui = FTPGUI(root)
    root.mainloop()