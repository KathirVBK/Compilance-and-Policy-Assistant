import os
from backend.config import Config
from backend.utils.logger import Logger

def save_uploaded_file(uploaded_file, filename):
    """Saves a multipart file to uploads directory"""
    Logger.info(f"Saving uploaded file: {filename}")
    save_path = os.path.join(Config.UPLOAD_DIR, filename)
    try:
        with open(save_path, 'wb') as f:
            f.write(uploaded_file)
        Logger.info(f"File saved to {save_path}")
        return save_path
    except Exception as e:
        Logger.error(f"Failed to save file: {e}")
        return None
