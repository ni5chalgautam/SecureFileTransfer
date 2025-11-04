# modules/transfer.py
import socket
import threading
import json
import os
import time
from modules import hashing, compression

DISCOVERY_PORT = 50000
TRANSFER_PORT = 50010
DISCOVERY_MSG = "MINISHARE_DISCOVER"
CHUNK_SIZE = 8192
DISCOVERY_TIMEOUT = 2.0  # increased for reliability


# Helper function to receive exactly n bytes
def recv_all(conn, n):
    data = b""
    while len(data) < n:
        packet = conn.recv(n - len(data))
        if not packet:
            break
        data += packet
    return data


# ---------------- Peer Discovery ----------------
def broadcast_discovery(timeout=DISCOVERY_TIMEOUT):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.settimeout(timeout)

    try:
        sock.sendto(DISCOVERY_MSG.encode(), ("<broadcast>", DISCOVERY_PORT))
    except Exception:
        pass

    peers = []
    start = time.time()
    while time.time() - start < timeout:
        try:
            data, addr = sock.recvfrom(2048)
            info = json.loads(data.decode())
            peers.append((addr[0], info.get("device", addr[0])))
        except socket.timeout:
            break
        except Exception:
            peers.append((addr[0], addr[0]))
    sock.close()
    return peers


class DiscoveryListener(threading.Thread):
    """Listens for UDP discovery requests and responds with device name."""

    def __init__(self, device_name):
        super().__init__(daemon=True)
        self.device_name = device_name
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("", DISCOVERY_PORT))

    def run(self):
        while True:
            try:
                data, addr = self.sock.recvfrom(2048)
                if data.decode().startswith(DISCOVERY_MSG):
                    resp = json.dumps({"device": self.device_name})
                    self.sock.sendto(resp.encode(), addr)
            except Exception:
                pass


# ---------------- Peer Server ----------------
class PeerServer(threading.Thread):
    """Server that receives files from peers."""

    def __init__(self, password, receive_dir="received", device_name="Peer"):
        super().__init__(daemon=True)
        self.password = password
        self.receive_dir = receive_dir
        self.device_name = device_name
        os.makedirs(self.receive_dir, exist_ok=True)
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(("", TRANSFER_PORT))
        self.server.listen(4)
        self.running = True
        DiscoveryListener(device_name).start()  # start discovery responder

    def run(self):
        while self.running:
            try:
                conn, addr = self.server.accept()
                threading.Thread(
                    target=self.handle_client, args=(conn,), daemon=True
                ).start()
            except Exception:
                pass

    def handle_client(self, conn):
        try:
            # Receive metadata length
            meta_len_bytes = recv_all(conn, 4)
            if len(meta_len_bytes) < 4:
                conn.close()
                return
            meta_len = int.from_bytes(meta_len_bytes, "big")

            # Receive encrypted metadata
            meta_enc = recv_all(conn, meta_len)
            meta = json.loads(
                hashing.decrypt_bytes(meta_enc, self.password).decode()
            )
            filename = meta["filename"]
            filesize = meta["size"]

            # Receive encrypted file data
            encrypted_data = recv_all(conn, filesize)

            # Decrypt and decompress
            decrypted = hashing.decrypt_bytes(encrypted_data, self.password)
            decompressed = compression.decompress(decrypted)

            # Save file
            save_path = os.path.join(self.receive_dir, filename)
            with open(save_path, "wb") as f:
                f.write(decompressed)

            # Acknowledge
            conn.sendall(b"OK")
            conn.close()
            print(f"[+] Received file: {save_path}")
        except Exception as e:
            conn.close()
            print(f"[-] Receive error: {e}")


# ---------------- Peer Client ----------------
class PeerClient:
    """Sends files to a given peer IP."""

    def __init__(self, password):
        self.password = password

    def send_file(self, peer_ip, file_path):
        try:
            # Read, compress, encrypt
            data = open(file_path, "rb").read()
            compressed = compression.compress(data)
            encrypted = hashing.encrypt_bytes(compressed, self.password)
            filesize = len(encrypted)

            # Prepare metadata
            meta = json.dumps(
                {"filename": os.path.basename(file_path), "size": filesize}
            ).encode()
            meta_enc = hashing.encrypt_bytes(meta, self.password)

            # Connect & send
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((peer_ip, TRANSFER_PORT))
            sock.sendall(len(meta_enc).to_bytes(4, "big"))
            sock.sendall(meta_enc)

            # Send file in chunks
            offset = 0
            while offset < len(encrypted):
                sock.sendall(encrypted[offset : offset + CHUNK_SIZE])
                offset += CHUNK_SIZE

            # Wait for acknowledgement
            resp = sock.recv(32)
            sock.close()
            return resp == b"OK"
        except Exception as e:
            print(f"[-] Send error: {e}")
            return False
