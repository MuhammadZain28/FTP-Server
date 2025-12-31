import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import socket
import os

BUFFER_SIZE = 4096
SERVER_IP = "127.0.0.1"
SERVER_PORT = 21

class FTPClientGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("FTP Client")
        self.sock = None
        
        self.login_window()
    
    def login_window(self):
        self.clear_window()
        ttk.Label(self.root, text="Username:").grid(row=0, column=0, pady=5, padx=5)
        self.username_entry = ttk.Entry(self.root)
        self.username_entry.grid(row=0, column=1, pady=5, padx=5)
        
        ttk.Label(self.root, text="Password:").grid(row=1, column=0, pady=5, padx=5)
        self.password_entry = ttk.Entry(self.root, show="*")
        self.password_entry.grid(row=1, column=1, pady=5, padx=5)
        
        ttk.Button(self.root, text="Login", command=self.login).grid(row=2, column=0, columnspan=2, pady=10)
    
    def main_window(self):
        self.clear_window()
        
        # Directory listing
        ttk.Label(self.root, text="Server Files:").grid(row=0, column=0, pady=5, padx=5)
        self.file_list = scrolledtext.ScrolledText(self.root, height=15, width=50, state=tk.DISABLED)
        self.file_list.grid(row=1, column=0, columnspan=2, padx=5, pady=5)
        
        # Buttons
        ttk.Button(self.root, text="Refresh List", command=self.list_files).grid(row=2, column=0, pady=5, padx=5)
        ttk.Button(self.root, text="Upload File", command=self.upload_file).grid(row=2, column=1, pady=5, padx=5)
        ttk.Button(self.root, text="Download File", command=self.download_file).grid(row=3, column=0, columnspan=2, pady=5)
    
    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()
    
    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((SERVER_IP, SERVER_PORT))
        print(self.sock.recv(BUFFER_SIZE).decode())  # welcome message
    
    def login(self):
        try:
            self.connect()
            username = self.username_entry.get()
            password = self.password_entry.get()
            
            self.send_command(f"USER {username}")
            resp = self.recv_response()
            if not resp.startswith("331"):
                messagebox.showerror("Login Failed", resp)
                return
            
            self.send_command(f"PASS {password}")
            resp = self.recv_response()
            if not resp.startswith("230"):
                messagebox.showerror("Login Failed", resp)
                return
            
            messagebox.showinfo("Login", "Login Successful")
            self.main_window()
            self.list_files()
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def send_command(self, cmd):
        self.sock.send((cmd + "\r\n").encode())
    
    def recv_response(self):
        return self.sock.recv(BUFFER_SIZE).decode()
    
    def list_files(self):
        self.send_command("LIST")
        data = self.recv_response()
        self.file_list.config(state=tk.NORMAL)
        self.file_list.delete(1.0, tk.END)
        self.file_list.insert(tk.END, data)
        self.file_list.config(state=tk.DISABLED)
    
    def upload_file(self):
        file_path = filedialog.askopenfilename()
        if not file_path:
            return
        filename = os.path.basename(file_path)
        
        self.send_command(f"STOR {filename}")
        resp = self.recv_response()
        if not resp.startswith("150"):
            messagebox.showerror("Upload Failed", resp)
            return
        
        with open(file_path, "rb") as f:
            while chunk := f.read(BUFFER_SIZE):
                self.sock.send(chunk)
        self.sock.send(b"\r\n")
        resp = self.recv_response()
        messagebox.showinfo("Upload", resp)
        self.list_files()
    
    def download_file(self):
        file_path = filedialog.asksaveasfilename()
        if not file_path:
            return

        selected = self.file_list.get(tk.SEL_FIRST, tk.SEL_LAST).strip()
        if not selected:
            messagebox.showwarning("Select File", "Select a file from the list to download")
            return
        
        self.send_command(f"RETR {selected}")
        resp = self.recv_response()
        if not resp.startswith("150"):
            messagebox.showerror("Download Failed", resp)
            return
        
        size = None
        parts = resp.split()
        if len(parts) > 1 and parts[1].isdigit():
            size = int(parts[1])
        
        received = 0
        with open(file_path, "wb") as f:
            while True:
                data = self.sock.recv(BUFFER_SIZE)
                if b"226 Transfer complete" in data:
                    f.write(data.replace(b"226 Transfer complete\r\n", b""))
                    break
                f.write(data)
                received += len(data)
        
        messagebox.showinfo("Download", "File downloaded successfully")
        self.list_files()


if __name__ == "__main__":
    root = tk.Tk()
    client_gui = FTPClientGUI(root)
    root.mainloop()
