import os
import requests
from backend.config import Config
from backend.utils.logger import Logger

def text_to_speech(text, output_audio_path):
    """Text-to-Speech: calls gpt-4o-mini-tts to synthesize audio from text"""
    if not Config.API_KEY or Config.API_KEY.strip() == "":
        Logger.warn("API_KEY missing. TTS cannot be run.")
        return False
        
    url = f"{Config.BASE_URL}v1/audio/speech"
    headers = {
        "Authorization": f"Bearer {Config.API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "gpt-4o-mini-tts",
        "input": text[:1000],  # Limit text to 1000 chars for speed
        "voice": "alloy"
    }
    
    try:
        Logger.info("Requesting TTS audio stream...")
        response = requests.post(url, headers=headers, json=payload, timeout=60, stream=True)
        if response.status_code == 200:
            os.makedirs(os.path.dirname(output_audio_path), exist_ok=True)
            with open(output_audio_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
            Logger.info(f"Saved TTS audio to {output_audio_path}")
            return True
        else:
            Logger.error(f"TTS API error {response.status_code}: {response.text}")
            return False
    except Exception as e:
        Logger.error(f"TTS request failed: {e}")
        return False
