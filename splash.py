# splash.py
import tkinter as tk
from PIL import Image, ImageTk
import sys
import os

def show_splash():
    splash_root = tk.Toplevel()
    splash_root.overrideredirect(True)
    splash_root.geometry("300x300+500+200")

    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    splash_path = os.path.join(base_path, "splash.png")
    if not os.path.exists(splash_path):
        print("Splash file not found:", splash_path)
        return

    img = Image.open(splash_path)
    img = img.resize((200, 200), Image.LANCZOS)
    photo = ImageTk.PhotoImage(img)
    label = tk.Label(splash_root, image=photo)
    label.image = photo
    label.pack(expand=True)

    splash_root.after(2000, splash_root.destroy)
    splash_root.update()
