# encryption.py
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import os

KEY_SIZE = 32  # 256-bit AES key
IV_SIZE = 16

def encrypt_file(file_path, key):
    cipher = AES.new(key, AES.MODE_CFB)
    iv = cipher.iv
    enc_path = f"{file_path}.enc"
    with open(file_path, "rb") as f, open(enc_path, "wb") as fout:
        fout.write(iv)  # write IV at start
        fout.write(cipher.encrypt(f.read()))
    return enc_path

def decrypt_file(enc_path, key):
    with open(enc_path, "rb") as f:
        iv = f.read(IV_SIZE)
        cipher = AES.new(key, AES.MODE_CFB, iv=iv)
        data = cipher.decrypt(f.read())
    dec_path = enc_path.replace(".enc", ".dec")
    with open(dec_path, "wb") as fout:
        fout.write(data)
    return dec_path

def generate_key():
    return get_random_bytes(KEY_SIZE)
