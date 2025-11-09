import tkinter as tk
from tkinter import filedialog, messagebox, END, ttk
import threading
import os
from . import transfer
from PIL import Image, ImageTk


class SecureTransferGUI:
    def __init__(self, root, password, device_name):
        self.root = root
        self.password = password
        self.device_name = device_name
        self.root.title(f"Mini SHAREit - {device_name}")
        try:
            self.root.iconbitmap(os.path.join(os.getcwd(), "icon.ico"))
        except:
            pass
        self.root.geometry("600x520")
        self.root.resizable(False, False)

        # GUI setup
        top_frame = ttk.Frame(self.root, padding=(12,10))
        top_frame.pack(fill="x")
        self.logo = None
        try:
            img_path = os.path.join(os.getcwd(), "splash.png")
            if os.path.exists(img_path):
                img = Image.open(img_path)
                img = img.resize((88,88), Image.LANCZOS)
                self.logo = ImageTk.PhotoImage(img)
                ttk.Label(top_frame, image=self.logo).pack(side="left", padx=(0,12))
        except:
            ttk.Label(top_frame, text="Mini SHAREit", font=("Segoe UI", 12, "bold")).pack(side="left", padx=(0,12))
        ttk.Label(top_frame, text=f"Device: {device_name}", font=("Segoe UI", 11)).pack(anchor="w")

        # Peer list
        peers_frame = ttk.Frame(self.root, padding=(12,6))
        peers_frame.pack(fill="both")
        ttk.Label(peers_frame, text="Discovered Peers:", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        self.peer_list = tk.Listbox(peers_frame, width=72, height=8)
        self.peer_list.pack(fill="x", pady=(6,8))

        # Buttons
        btn_frame = ttk.Frame(self.root, padding=(12,6))
        btn_frame.pack(fill="x")
        self.scan_btn = ttk.Button(btn_frame, text="Scan Peers", command=self.scan_peers)
        self.scan_btn.grid(row=0,column=0,padx=6,pady=6)
        self.select_btn = ttk.Button(btn_frame, text="Select File", command=self.select_file)
        self.select_btn.grid(row=0,column=1,padx=6,pady=6)
        self.send_btn = ttk.Button(btn_frame, text="Send File", command=self.send_file)
        self.send_btn.grid(row=0,column=2,padx=6,pady=6)
        self.cancel_btn = ttk.Button(btn_frame, text="Cancel Transfer", command=self.cancel_transfer, state="disabled")
        self.cancel_btn.grid(row=0,column=3,padx=6,pady=6)
        self.receive_btn = ttk.Button(btn_frame, text="Receive File", command=self.start_receive)
        self.receive_btn.grid(row=0,column=4,padx=6,pady=6)
        self.hotspot_btn = ttk.Button(btn_frame, text="Start Hotspot", command=self.start_hotspot)
        self.hotspot_btn.grid(row=1,column=0,padx=6,pady=6)

        # Progress
        progress_frame = ttk.Frame(self.root, padding=(12,6))
        progress_frame.pack(fill="x")
        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100.0)
        self.progress_bar.pack(fill="x", pady=(6,4))
        self.percent_label = ttk.Label(progress_frame, text="Progress: 0.0%")
        self.percent_label.pack(anchor="e")

        # Status
        self.status = ttk.Label(self.root, text="Status: Ready", anchor="w")
        self.status.pack(fill="x", padx=12, pady=(6,12))

        # Server
        self.server = transfer.PeerServer(password=self.password, device_name=self.device_name)
        self.server.set_progress_callback(self._receive_progress)
        self.server.start()

        self.peers = []
        self.selected_file = None
        self.current_client = None

    # UI Helpers
    def log(self, text):
        self.root.after(0, lambda: self.status.config(text=f"Status: {text}"))

    def _progress_callback(self, percent):
        self.root.after(0, lambda: (
            self.progress_var.set(percent),
            self.percent_label.config(text=f"Progress: {percent:.1f}%"),
            self.cancel_btn.config(state="disabled") if percent>=100 else None
        ))

    def _receive_progress(self, percent, fname):
        self.root.after(0, lambda: (
            self.progress_var.set(percent),
            self.percent_label.config(text=f"Receiving {fname}: {percent:.1f}%")
        ))

    # Actions
    def scan_peers(self):
        self.log("Scanning peers...")
        messagebox.showinfo("Info","Peer scan not implemented. Use IPs manually.")
        self.peers = [("127.0.0.1","Localhost")]  # demo

    def select_file(self):
        path = filedialog.askopenfilename()
        if path:
            self.selected_file = path
            self.log(f"Selected: {os.path.basename(path)}")

    def cancel_transfer(self):
        if self.current_client:
            self.current_client.cancel()
            self.log("Cancelling transfer...")
            self.cancel_btn.config(state="disabled")

    def send_file(self):
        if not self.selected_file:
            messagebox.showwarning("Select file","Select a file first.")
            return
        if not self.peers:
            messagebox.showwarning("No peer","No peer available.")
            return

        peer_ip,_ = self.peers[0]
        self.scan_btn.config(state="disabled")
        self.select_btn.config(state="disabled")
        self.send_btn.config(state="disabled")
        self.cancel_btn.config(state="normal")
        self.progress_var.set(0.0)
        self.percent_label.config(text="Progress: 0%")
        self.log(f"Sending {os.path.basename(self.selected_file)}...")

        def worker():
            client = transfer.PeerClient(self.password)
            self.current_client = client
            ok,msg = client.send_file(peer_ip, self.selected_file, progress_callback=self._progress_callback)
            def finish_ui():
                self.current_client = None
                self.scan_btn.config(state="normal")
                self.select_btn.config(state="normal")
                self.send_btn.config(state="normal")
                self.cancel_btn.config(state="disabled")
                if ok:
                    self.log("Send complete")
                    messagebox.showinfo("Success","File sent successfully")
                else:
                    self.log("Transfer failed")
                    messagebox.showerror("Error", msg)
            self.root.after(0, finish_ui)

        threading.Thread(target=worker, daemon=True).start()

    def start_receive(self):
        self.log("Ready to receive files...")
        messagebox.showinfo("Receiver","Your device is ready to receive files.")

    def start_hotspot(self):
        self.log("Starting hotspot...")
        success = transfer.start_hotspot()
        if success:
            self.log("Hotspot started: MiniShareIt")
            messagebox.showinfo("Hotspot","Hotspot started. Connect the receiver device.")
        else:
            self.log("Failed to start hotspot")
            messagebox.showerror("Hotspot","Could not start hotspot.")
