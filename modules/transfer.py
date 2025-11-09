import socket
import os
from modules.compression import compress_file, decompress_file
from modules.encryption import encrypt_file, decrypt_file
from modules.hashing import hash_file

BUFFER_SIZE = 4096

class FileSender:
    def __init__(self, key):
        self.key = key
        self.cancelled = False

    def cancel(self):
        self.cancelled = True

    def send_files(self, ip, files, progress_callback=None):
        total_bytes = sum(os.path.getsize(f) for f in files)
        sent_bytes = 0
        for filepath in files:
            if self.cancelled:
                return False, "cancelled"

            filename = os.path.basename(filepath)
            # Compress & encrypt
            temp_file = compress_file(filepath)
            encrypted_file = encrypt_file(temp_file, self.key)

            # Compute file hash
            file_hash = hash_file(filepath)

            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((ip, 5001))
            s.send(f"{filename}:{os.path.getsize(encrypted_file)}".encode())
            s.recv(1024)  # ACK

            with open(encrypted_file, "rb") as f:
                while chunk := f.read(BUFFER_SIZE):
                    if self.cancelled:
                        s.close()
                        return False, "cancelled"
                    s.sendall(chunk)
                    sent_bytes += len(chunk)
                    if progress_callback:
                        progress_callback((sent_bytes / total_bytes) * 100)

            # Send hash after file
            s.send(f"HASH:{file_hash}".encode())
            s.close()

        return True, "success"


class FileReceiver:
    def __init__(self, key, save_folder):
        self.key = key
        self.save_folder = save_folder
        self.cancelled = False

    def cancel(self):
        self.cancelled = True

    def receive_files(self, progress_callback=None):
        # For simplicity: handle files one by one
        total_bytes = 0  # can calculate if sender sends total size
        received_bytes = 0

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("", 5001))
        s.listen(1)
        conn, addr = s.accept()

        while True:
            header = conn.recv(1024).decode()
            if not header:
                break
            filename, filesize = header.split(":")
            filesize = int(filesize)
            conn.send(b"ACK")

            save_path = os.path.join(self.save_folder, filename + ".enc")
            received = 0
            with open(save_path, "wb") as f:
                while received < filesize:
                    if self.cancelled:
                        conn.close()
                        return False, "cancelled"
                    chunk = conn.recv(BUFFER_SIZE)
                    if not chunk:
                        break
                    f.write(chunk)
                    received += len(chunk)
                    if progress_callback:
                        progress_callback((received_bytes + received) / filesize * 100)
            received_bytes += received

            # Receive hash
            hash_msg = conn.recv(1024).decode()
            if hash_msg.startswith("HASH:"):
                received_hash = hash_msg.split(":")[1]
                calc_hash = hash_file(save_path)
                if received_hash == calc_hash:
                    print(f"{filename} verified ✅")
                else:
                    print(f"{filename} corrupted ❌")

            # Decrypt & decompress
            decrypted_file = decrypt_file(save_path, self.key)
            decompress_file(decrypted_file)

        conn.close()
        return True, "success"
