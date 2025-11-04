import os
import tkinter as tk
from modules.gui import SecureTransferGUI

PASSWORD = "my_secret_pass"
DEVICE_NAME = os.getenv("COMPUTERNAME", os.getenv("HOSTNAME", "MyDevice"))

def main():
    root = tk.Tk()
    app = SecureTransferGUI(root, password=PASSWORD, device_name=DEVICE_NAME)
    root.mainloop()

if __name__ == "__main__":
    main()
