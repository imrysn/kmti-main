import shutil
import os

def save_file(file, dest_folder):
    os.makedirs(dest_folder, exist_ok=True)
    shutil.copy(file.path, os.path.join(dest_folder, file.name))
