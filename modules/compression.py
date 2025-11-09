# compression.py
import zipfile
import os

def compress_file(file_path):
    zip_path = f"{file_path}.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.write(file_path, os.path.basename(file_path))
    return zip_path

def decompress_file(zip_path, extract_folder):
    import zipfile
    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(extract_folder)
    return os.path.join(extract_folder, os.path.basename(zip_path).replace('.zip', ''))
