import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import socket
import os

BUFFER_SIZE = 4096
SERVER_IP = "127.0.0.1"
SERVER_PORT = 21
DATA_PORT = 20

class FTPClientGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("FTP Client")
        self.sock = None
        self.dir = "/"
        
        self.login_window()
    
    def login_window(self):
        self.clear_window()
        self.root.geometry("300x150")
        frame = ttk.Frame(self.root)
        frame.pack(padx=20, pady=20, fill=tk.X)

        ttk.Label(frame, text="Username:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.username_entry = ttk.Entry(frame)
        self.username_entry.grid(row=0, column=1, pady=5, sticky=tk.EW)

        ttk.Label(frame, text="Password:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.password_entry = ttk.Entry(frame, show="*")
        self.password_entry.grid(row=1, column=1, pady=5, sticky=tk.EW)

        ttk.Button(frame, text="Login", command=self.login).grid(
            row=2, column=0, columnspan=2, pady=10
        )

        frame.columnconfigure(1, weight=1)

    def main_window(self):
        self.clear_window()

        frame = ttk.Frame(self.root)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.dir_label = ttk.Label(frame, text=f"Server Files - Current Directory: {self.dir}")
        self.dir_label.grid(row=0, column=0, sticky=tk.W)

        # --- Treeview Columns ---
        columns = ("name", "size", "time")
        self.file_list = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse")
        
        self.file_list.heading("name", text="File Name")
        self.file_list.heading("size", text="Size (Bytes)")
        self.file_list.heading("time", text="Modified")

        self.file_list.column("name", width=200, anchor=tk.W)
        self.file_list.column("size", width=100, anchor=tk.CENTER)
        self.file_list.column("time", width=150, anchor=tk.CENTER)

        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.file_list.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=self.file_list.xview)
        self.file_list.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.file_list.grid(row=1, column=0, columnspan=6, sticky="nsew", pady=5)
        vsb.grid(row=1, column=6, sticky="ns")
        hsb.grid(row=2, column=0, columnspan=6, sticky="ew")

        ttk.Button(frame, text="Refresh List", command=self.list_files).grid(row=3, column=0, pady=5)
        ttk.Button(frame, text="Upload File", command=self.upload_file).grid(row=0, column=1, pady=5)
        ttk.Button(frame, text="Download File", command=self.download_file).grid(row=0, column=2, pady=5)
        ttk.Button(frame, text="Make Directory", command=self.make_dir).grid(row=0, column=3, pady=5)
        ttk.Button(frame, text="Change Directory", command=self.change_dir).grid(row=0, column=4, pady=5)
        ttk.Button(frame, text="Base Directory", command=self.change_base_dir).grid(row=0, column=5, pady=5)

        frame.rowconfigure(1, weight=1)
        frame.columnconfigure(0, weight=1)

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
            decoded_resp = resp.decode()
            if not decoded_resp.startswith("331"):
                messagebox.showerror("Login Failed", decoded_resp)
                return
            
            self.send_command(f"PASS {password}")
            resp = self.recv_response()
            decoded_resp = resp.decode()
            if not decoded_resp.startswith("230"):
                messagebox.showerror("Login Failed", decoded_resp)
                return
            
            messagebox.showinfo("Login", "Login Successful")
            self.main_window()
            self.list_files()
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def send_command(self, cmd):
        self.sock.send((cmd + "\r\n").encode())
    
    def recv_response(self):
        self.sock.settimeout(2)
        data = b""
        try:
            while True:
                chunk = self.sock.recv(4096)
                if not chunk:
                    break
                data += chunk
        except socket.timeout:
            pass
        return data

    def list_files(self):
        self.send_command("LIST")
        
        resp = self.recv_response()
        if not resp.startswith(b"150"):
            messagebox.showerror("Error", f"LIST failed: {resp.decode()}")
            return
        
        data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        data_sock.connect((SERVER_IP, DATA_PORT))
        

        chunks = []
        while True:
            data = data_sock.recv(4096)
            if not data:
                break
            chunks.append(data)
        data_sock.close()


        listing_json = b"".join(chunks).decode()
        
        try:
            files = json.loads(listing_json)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to parse listing: {e}")
            return

        self.update_file_list(files)


        resp = self.recv_response()
        print(resp)
        if not resp.startswith(b"226"):
            messagebox.showwarning("Warning", f"Unexpected server response: {resp.decode()}")

    def update_file_list(self, files):
        for item in self.file_list.get_children():
            self.file_list.delete(item)

        for f in files:
            if "error" in f:
                self.file_list.insert("", tk.END, values=(f["error"], "", ""))
                continue

            name = f["name"]
            size = f["size"]
            time = f["time"]
            is_dir = f.get("dir", False)
            if is_dir:
                name += "/"

            self.file_list.insert("", tk.END, values=(name, size, time))

    def make_dir(self):
        dir_name = tk.simpledialog.askstring("New Directory", "Enter directory name:")
        if not dir_name:
            return

        self.send_command(f"MKD {dir_name}")
        
        resp = self.recv_response()
        if resp.startswith(b"257"):
            messagebox.showinfo("Success", f"Directory '{dir_name}' created successfully")
            self.list_files()
        else:
            messagebox.showerror("Error", resp.decode())

    def change_dir(self):
        selected = self.file_list.selection()
        if not selected:
            messagebox.showwarning("Select Directory", "Select a directory from the list to change into")
            return
        
        selected_item = self.file_list.item(selected[0])
        dir_name = selected_item['values'][0]
        if not dir_name.endswith("/"):
            messagebox.showwarning("Select Directory", "Selected item is not a directory")
            return

        dir_name = dir_name.rstrip("/")

        self.send_command(f"CWD {dir_name}")
        
        resp = self.recv_response()
        if resp.startswith(b"250"):
            messagebox.showinfo("Success", f"Changed directory to '{dir_name}'")
            self.dir = dir_name
            self.dir_label.config(text=f"Server Files - Current Directory: {self.dir}")
            self.list_files()
        else:
            messagebox.showerror("Error", resp.decode())
    def change_base_dir(self):

        self.send_command(f"CDUP")
        
        resp = self.recv_response()
        if resp.startswith(b"250"):
            messagebox.showinfo("Success", f"Changed directory to '/'")
            self.dir = "/"
            self.dir_label.config(text=f"Server Files - Current Directory: {self.dir}")
            self.list_files()
        else:
            messagebox.showerror("Error", resp.decode())

    def upload_file(self):
        file_path = filedialog.askopenfilename()
        if not file_path:
            return
        filename = os.path.basename(file_path)
        
        self.send_command(f"STOR {filename}")
        resp = self.recv_response()
        if not resp.startswith(b"150"):
            messagebox.showerror("Upload Failed", resp.decode())
            return

        data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        data_sock.connect((SERVER_IP, DATA_PORT))
        
        with open(file_path, "rb") as f:
            while chunk := f.read(BUFFER_SIZE):
                data_sock.sendall(chunk)

        data_sock.close()
        
        resp = self.recv_response()
        if resp.startswith(b"226"):
            messagebox.showinfo("Upload", "File uploaded successfully")
        else:
            messagebox.showwarning("Upload", f"Upload finished with server response:\n{resp.decode()}")

        self.list_files()

    def download_file(self):
        selected = self.file_list.selection()
        if not selected:
            messagebox.showwarning("Select File", "Select a file from the list to download")
            return
        
        selected_item = self.file_list.item(selected[0])
        filename = selected_item['values'][0]

        self.send_command(f"RETR {filename}")
        
        resp = self.recv_response()
        if resp.startswith(b"550"):
            messagebox.showerror("Download Failed", resp.decode())
            return
        elif not resp.startswith(b"150"):
            messagebox.showerror("Download Failed", "Unexpected server response:\n" + resp.decode())
            return
        
        file_path = filedialog.asksaveasfilename(initialfile=filename)
        if not file_path:
            return

        data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        data_sock.connect((SERVER_IP, DATA_PORT))

        with open(file_path, "wb") as f:
            while True:
                data = data_sock.recv(BUFFER_SIZE)
                if not data:
                    break
                f.write(data)

        data_sock.close()

        resp = self.recv_response()
        if resp.startswith(b"226"):
            messagebox.showinfo("Download", "File downloaded successfully")
        else:
            messagebox.showwarning("Download", f"File transfer finished with response: {resp.decode()}")

        # 7️⃣ Refresh file list
        self.list_files()


if __name__ == "__main__":
    root = tk.Tk()
    client_gui = FTPClientGUI(root)
    root.mainloop()
