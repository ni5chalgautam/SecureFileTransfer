import sys
import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# Add modules folder to path
sys.path.append(os.path.join(os.path.dirname(__file__), "modules"))

# Local module imports
from modules.compression import compress_file, decompress_file
from modules.encryption import encrypt_file, decrypt_file, generate_key
from modules.hashing import hash_file
from modules.transfer import FileSender, FileReceiver
from splash import show_splash

from PIL import Image, ImageTk

# ---------- Globals ----------
root = tk.Tk()
root.title("Secure P2P File Transfer")
root.geometry("600x550")
role_var = tk.StringVar(value="sender")
file_list = []
save_folder = ""
sender_client = None
receiver_client = None
aes_key = generate_key()

# ---------- Splash ----------
show_splash()

# ---------- Icon ----------
def set_window_icon(root, icon_file):
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(__file__)
    path = os.path.join(base_path, icon_file)
    try:
        img = Image.open(path)
        icon = ImageTk.PhotoImage(img)
        root.tk.call('wm', 'iconphoto', root._w, icon)
    except Exception as e:
        print(f"Icon load failed: {e}")

set_window_icon(root, "icon.png")

# ---------- Functions ----------
def select_files():
    global file_list
    file_list = list(filedialog.askopenfilenames())
    if file_list:
        file_label.config(text=f"{len(file_list)} file(s) selected")

def select_folder():
    global file_list, save_folder
    folder = filedialog.askdirectory()
    if folder:
        save_folder = folder
        file_list = []
        for root_dir, dirs, files in os.walk(folder):
            for f in files:
                file_list.append(os.path.join(root_dir, f))
        folder_label.config(text=f"{len(file_list)} file(s) in folder selected")

def update_progress(percent):
    progress_bar['value'] = percent
    percent_label.config(text=f"{percent:.1f}%")
    root.update_idletasks()

def cancel_transfer():
    global sender_client, receiver_client
    if role_var.get() == "sender" and sender_client:
        sender_client.cancel()
    elif role_var.get() == "receiver" and receiver_client:
        receiver_client.cancel()

# ---------- Sender ----------
def start_sender():
    global sender_client
    if not file_list:
        messagebox.showwarning("Select files", "Please select files or folder to send.")
        return
    target_ip = ip_entry.get()
    if not target_ip:
        messagebox.showwarning("Enter IP", "Please enter receiver IP.")
        return

    sender_client = FileSender(aes_key)
    hash_label.config(text="Hash verification: Pending")
    
    def worker():
        ok, msg = sender_client.send_files(target_ip, file_list, progress_callback=update_progress)
        if ok:
            messagebox.showinfo("Success", "All files sent successfully!")
            hash_label.config(text="All file hashes sent ✅")
        else:
            if msg == "cancelled":
                messagebox.showinfo("Cancelled", "Transfer cancelled.")
                hash_label.config(text="Transfer cancelled ❌")
            else:
                messagebox.showerror("Error", f"Transfer failed: {msg}")
                hash_label.config(text="Error during transfer ❌")
        update_progress(0)

    threading.Thread(target=worker, daemon=True).start()

# ---------- Receiver ----------
def start_receiver():
    global receiver_client
    if not save_folder:
        messagebox.showwarning("Select folder", "Please select a folder to save the files.")
        return

    receiver_client = FileReceiver(aes_key, save_folder)
    hash_label.config(text="Hash verification: Pending")
    
    def worker():
        ok, msg = receiver_client.receive_files(progress_callback=update_progress)
        if ok:
            messagebox.showinfo("Success", "All files received successfully!")
            hash_label.config(text="All file hashes verified ✅")
        else:
            if msg == "cancelled":
                messagebox.showinfo("Cancelled", "Transfer cancelled.")
                hash_label.config(text="Transfer cancelled ❌")
            else:
                messagebox.showerror("Error", f"Transfer failed: {msg}")
                hash_label.config(text="Error during transfer ❌")
        update_progress(0)

    threading.Thread(target=worker, daemon=True).start()

# ---------- Role GUI ----------
def update_role():
    if role_var.get() == "sender":
        ip_label.pack(pady=2)
        ip_entry.pack(pady=2)
        select_file_btn.pack(pady=5)
        file_label.pack()
        select_folder_btn.pack_forget()
        folder_label.pack_forget()
        start_btn.config(text="Start Send", command=start_sender)
    else:
        ip_label.pack_forget()
        ip_entry.pack_forget()
        select_file_btn.pack_forget()
        file_label.pack_forget()
        select_folder_btn.pack(pady=5)
        folder_label.pack()
        start_btn.config(text="Start Receive", command=start_receiver)

# ---------- GUI Widgets ----------
tk.Label(root, text="Select Role:").pack(pady=5)
tk.Radiobutton(root, text="Sender", variable=role_var, value="sender", command=update_role).pack()
tk.Radiobutton(root, text="Receiver", variable=role_var, value="receiver", command=update_role).pack()

ip_label = tk.Label(root, text="Receiver IP:")
ip_entry = tk.Entry(root)

select_file_btn = tk.Button(root, text="Select Files", command=select_files, bg="#4caf50", fg="white")
file_label = tk.Label(root, text="No file selected")

select_folder_btn = tk.Button(root, text="Select Folder", command=select_folder, bg="#2196f3", fg="white")
folder_label = tk.Label(root, text="No folder selected")

progress_bar = ttk.Progressbar(root, orient='horizontal', length=500, mode='determinate')
progress_bar.pack(pady=20)
percent_label = tk.Label(root, text="0%")
percent_label.pack()

hash_label = tk.Label(root, text="Hash verification: Pending")
hash_label.pack(pady=5)

start_btn = tk.Button(root, text="Start", width=20)
start_btn.pack(pady=5)

tk.Button(root, text="Cancel", command=cancel_transfer, bg="red", fg="white").pack(pady=5)

update_role()
root.mainloop()
