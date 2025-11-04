# modules/encryption.py

def _str_to_bytes(s):
    return s.encode()

def xor_bytes(data: bytes, key: bytes) -> bytes:
    """Simple XOR encryption"""
    out = bytearray()
    key_len = len(key)
    for i, b in enumerate(data):
        out.append(b ^ key[i % key_len])
    return bytes(out)

def encrypt_bytes(data: bytes, password: str) -> bytes:
    key = _str_to_bytes(password)
    return xor_bytes(data, key)

def decrypt_bytes(data: bytes, password: str) -> bytes:
    key = _str_to_bytes(password)
    return xor_bytes(data, key)  # XOR is symmetric
