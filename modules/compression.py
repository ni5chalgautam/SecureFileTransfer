# modules/compression.py
"""
Simple RLE (Run-Length Encoding) compression/decompression.
"""

def compress(data: bytes) -> bytes:
    out = bytearray()
    i = 0
    while i < len(data):
        count = 1
        while i + 1 < len(data) and data[i] == data[i+1] and count < 255:
            count += 1
            i += 1
        out.append(count)
        out.append(data[i])
        i += 1
    return bytes(out)

def decompress(data: bytes) -> bytes:
    out = bytearray()
    i = 0
    while i < len(data):
        count = data[i]
        i += 1
        out.extend([data[i]] * count)
        i += 1
    return bytes(out)
