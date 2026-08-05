import os
from dotenv import load_dotenv

# Load env variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

class Config:
    PORT = int(os.getenv("PORT", 8000))
    API_KEY = os.getenv("API_KEY", "")
    BASE_URL = os.getenv("BASE_URL", "https://apidev.navigatelabsai.com/").strip()
    if not BASE_URL.endswith('/'):
        BASE_URL += '/'
        
    SELECTED_MODEL = os.getenv("SELECTED_MODEL", "gemini-2.5-flash")
    EMBED_MODEL = "text-embedding-3-small"
    EMBED_DIM = 1536
    
    # Paths
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    KNOWLEDGE_BASE_DIR = os.path.join(BASE_DIR, 'knowledge_base')
    ENTERPRISE_DOCS_DIR = os.path.join(KNOWLEDGE_BASE_DIR, 'enterprise_docs')
    
    VECTOR_DB_DIR = os.path.join(BASE_DIR, 'vector_db')
    ENTERPRISE_INDEX_DIR = os.path.join(VECTOR_DB_DIR, 'enterprise_index')
    UPLOADED_INDEX_DIR = os.path.join(VECTOR_DB_DIR, 'uploaded_index')
    
    UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads')
    
    # Ensure folders exist
    os.makedirs(ENTERPRISE_INDEX_DIR, exist_ok=True)
    os.makedirs(UPLOADED_INDEX_DIR, exist_ok=True)
    os.makedirs(UPLOAD_DIR, exist_ok=True)
