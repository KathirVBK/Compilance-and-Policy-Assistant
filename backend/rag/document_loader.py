import os
from pypdf import PdfReader
from backend.utils.logger import Logger

def load_document(file_path):
    """Loads text from PDF or text files"""
    if not os.path.exists(file_path):
        Logger.error(f"File not found: {file_path}")
        return None
        
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == '.pdf':
        Logger.info(f"Loading PDF file: {file_path}")
        try:
            reader = PdfReader(file_path)
            text = ""
            for page_num, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text += f"\n--- Page {page_num + 1} ---\n" + page_text
            return text
        except Exception as e:
            Logger.error(f"Failed to load PDF {file_path}: {e}")
            return None
    else:
        # Fallback to plain text files (.txt, .md)
        Logger.info(f"Loading text file: {file_path}")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            Logger.error(f"Failed to load text file {file_path}: {e}")
            return None
