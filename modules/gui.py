# modules/gui.py
import tkinter as tk
from tkinter import filedialog, messagebox, END
import threading
import os
from modules import transfer

class SecureTransferGUI:
    def __init__(self, root, password, device_name):
        self.root = root
        self.password = password
        self.device_name = device_name
        self.root.title(f"Mini SHAREit - {device_name}")
        self.root.geometry("500x400")

        tk.Label(root, text="Discovered Peers:").pack()
        self.peer_list = tk.Listbox(root, width=60, height=10)
        self.peer_list.pack(pady=5)
        tk.Button(root, text="Scan Peers", command=self.scan_peers).pack(pady=4)
        tk.Button(root, text="Select File", command=self.select_file).pack(pady=4)
        tk.Button(root, text="Send File", command=self.send_file).pack(pady=4)
        self.status = tk.Label(root, text="Status: Ready")
        self.status.pack(pady=6)

        self.server = transfer.PeerServer(password=self.password, device_name=self.device_name)
        self.server.start()
        self.peers = []
        self.selected_file = None

    def log(self, text):
        self.status.config(text=f"Status: {text}")
        self.root.update_idletasks()

    def scan_peers(self):
        self.log("Scanning...")
        self.peer_list.delete(0, END)
        self.peers = transfer.broadcast_discovery()
        for ip, name in self.peers:
            self.peer_list.insert(END, f"{name} ({ip})")
        self.log(f"{len(self.peers)} peers found")

    def select_file(self):
        path = filedialog.askopenfilename()
        if path:
            self.selected_file = path
            self.log(f"Selected: {os.path.basename(path)}")

    def send_file(self):
        sel = self.peer_list.curselection()
        if not sel or not self.selected_file:
            messagebox.showwarning("Error", "Select peer and file")
            return
        idx = sel[0]
        peer_ip, peer_name = self.peers[idx]

        def worker():
            self.log(f"Sending to {peer_name}...")
            client = transfer.PeerClient(self.password)
            if client.send_file(peer_ip, self.selected_file):
                self.log("Send complete")
                messagebox.showinfo("Success", "File sent")
            else:
                self.log("Send failed")
                messagebox.showerror("Error", "Transfer failed")

        threading.Thread(target=worker, daemon=True).start()
