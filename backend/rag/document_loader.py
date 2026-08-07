import os
import re
import fitz  # PyMuPDF
from backend.utils.logger import Logger

def clean_text(text):
    """Removes extra spaces and normalizes newlines to improve chunk quality"""
    if not text:
        return ""
    # Replace multiple spaces with a single space
    text = re.sub(r' +', ' ', text)
    # Replace multiple newlines with a double newline
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def load_document(file_path):
    """Loads text from PDF or text files"""
    if not os.path.exists(file_path):
        Logger.error(f"File not found: {file_path}")
        return None
        
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == '.pdf':
        Logger.info(f"Loading PDF file with PyMuPDF: {file_path}")
        try:
            doc = fitz.open(file_path)
            text = ""
            for page_num, page in enumerate(doc):
                page_text = page.get_text()
                if page_text:
                    text += f"\n--- Page {page_num + 1} ---\n" + page_text
            return clean_text(text)
        except Exception as e:
            Logger.error(f"Failed to load PDF {file_path}: {e}")
            return None
    else:
        # Fallback to plain text files (.txt, .md)
        Logger.info(f"Loading text file: {file_path}")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return clean_text(f.read())
        except Exception as e:
            Logger.error(f"Failed to load text file {file_path}: {e}")
            return None
