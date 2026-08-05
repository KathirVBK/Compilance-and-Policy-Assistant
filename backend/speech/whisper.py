import os
import requests
from backend.config import Config
from backend.utils.logger import Logger

def transcribe_audio(audio_file_path):
    """Whisper Speech-to-Text: calls whisper-1 endpoint to transcribe audio"""
    if not Config.API_KEY or Config.API_KEY.strip() == "":
        Logger.warn("API_KEY missing. Whisper transcription cannot be run.")
        return "API key missing for audio transcription."
        
    url = f"{Config.BASE_URL}v1/audio/transcriptions"
    headers = {
        "Authorization": f"Bearer {Config.API_KEY}"
    }
    
    if not os.path.exists(audio_file_path):
        Logger.error(f"Audio file not found: {audio_file_path}")
        return "Audio file missing."
        
    try:
        Logger.info(f"Uploading audio for transcription: {audio_file_path}")
        with open(audio_file_path, 'rb') as audio_file:
            files = {
                'file': (os.path.basename(audio_file_path), audio_file, 'audio/webm')
            }
            data = {
                'model': 'whisper-1'
            }
            response = requests.post(url, headers=headers, files=files, data=data, timeout=30)
            
            if response.status_code == 200:
                transcript = response.json().get('text', '')
                Logger.info(f"Whisper transcription result: '{transcript}'")
                return transcript
            else:
                Logger.error(f"Whisper API error {response.status_code}: {response.text}")
                return f"Transcription failed (API error {response.status_code})."
    except Exception as e:
        Logger.error(f"Whisper request failed: {e}")
        return "Transcription request error."
