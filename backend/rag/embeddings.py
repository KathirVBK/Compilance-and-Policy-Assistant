import requests
from backend.config import Config
from backend.utils.logger import Logger

def get_embedding(text):
    """Fetches embedding representation for a text input"""
    if not Config.API_KEY:
        Logger.warn("API_KEY environment variable is missing. Embeddings cannot be generated.")
        return None
        
    url = f"{Config.BASE_URL}v1/embeddings"
    headers = {
        "Authorization": f"Bearer {Config.API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": Config.EMBED_MODEL,
        "input": text
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        if response.status_code == 200:
            return response.json()['data'][0]['embedding']
        else:
            Logger.error(f"Embeddings API error {response.status_code}: {response.text}")
            return None
    except Exception as e:
        Logger.error(f"Embeddings Request failed: {e}")
        return None
