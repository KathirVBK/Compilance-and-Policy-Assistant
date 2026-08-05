import uuid
from typing import List, Dict, Optional
from backend.utils.logger import Logger

# Session-level in-memory store
_SESSION_STORE: Dict[str, List[Dict[str, str]]] = {}
MAX_HISTORY_TURNS = 10  # Store last 10 turns (5 user + 5 assistant) to prevent token bloat

class SessionManager:
    @staticmethod
    def get_or_create_session(session_id: Optional[str] = None) -> str:
        """Returns existing session_id or generates a new UUID session_id."""
        if not session_id or not session_id.strip():
            session_id = str(uuid.uuid4())
        if session_id not in _SESSION_STORE:
            _SESSION_STORE[session_id] = []
        return session_id

    @staticmethod
    def get_session_history(session_id: str, limit: int = MAX_HISTORY_TURNS) -> List[Dict[str, str]]:
        """Retrieves recent conversation turns for a session ID up to limit."""
        if not session_id or session_id not in _SESSION_STORE:
            return []
        history = _SESSION_STORE.get(session_id, [])
        return history[-limit:]

    @staticmethod
    def add_turn(session_id: str, user_query: str, assistant_response: str):
        """Appends a completed conversation turn to the session history."""
        if not session_id:
            return
        if session_id not in _SESSION_STORE:
            _SESSION_STORE[session_id] = []
            
        _SESSION_STORE[session_id].append({"sender": "user", "text": user_query})
        _SESSION_STORE[session_id].append({"sender": "assistant", "text": assistant_response})
        
        # Enforce maximum history window
        if len(_SESSION_STORE[session_id]) > MAX_HISTORY_TURNS * 2:
            _SESSION_STORE[session_id] = _SESSION_STORE[session_id][-(MAX_HISTORY_TURNS * 2):]
        
        Logger.info(f"Session [{session_id[:8]}...] stored turn. Total turns in history: {len(_SESSION_STORE[session_id]) // 2}")

    @staticmethod
    def clear_session(session_id: str):
        """Clears stored history for a session."""
        if session_id in _SESSION_STORE:
            del _SESSION_STORE[session_id]
            Logger.info(f"Session [{session_id[:8]}...] cleared.")
