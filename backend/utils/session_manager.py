import uuid
from typing import List, Dict, Optional
from backend.utils.logger import Logger

# Session-level in-memory store
_SESSION_STORE: Dict[str, List[Dict[str, str]]] = {}
_SESSION_SUMMARIES: Dict[str, str] = {}   # Rolling compressed summaries per session

MAX_HISTORY_TURNS    = 20   # Store last 20 turns (10 user + 10 assistant)
SUMMARY_TRIGGER_TURNS = 20  # Summarize when history exceeds this


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
    def get_session_summary(session_id: str) -> str:
        """Returns the rolling compressed summary for long sessions (empty string if none)."""
        return _SESSION_SUMMARIES.get(session_id, "")

    @staticmethod
    def add_turn(session_id: str, user_query: str, assistant_response: str):
        """Appends a completed conversation turn to the session history.
        When the window fills up, old turns are compressed into a rolling summary."""
        if not session_id:
            return
        if session_id not in _SESSION_STORE:
            _SESSION_STORE[session_id] = []

        _SESSION_STORE[session_id].append({"sender": "user",      "text": user_query})
        _SESSION_STORE[session_id].append({"sender": "assistant", "text": assistant_response})

        # Enforce sliding window: when we exceed MAX_HISTORY_TURNS * 2 messages,
        # compress the oldest half into a summary and drop them.
        if len(_SESSION_STORE[session_id]) > MAX_HISTORY_TURNS * 2:
            SessionManager._compress_old_turns(session_id)

        Logger.info(
            f"Session [{session_id[:8]}...] stored turn. "
            f"Total turns in history: {len(_SESSION_STORE[session_id]) // 2}"
        )

    @staticmethod
    def _compress_old_turns(session_id: str):
        """
        Compresses the oldest MAX_HISTORY_TURNS messages into a summary string
        and keeps the most recent MAX_HISTORY_TURNS messages in the live window.
        Uses the LLM for summarization; falls back to a simple text concat.
        """
        history = _SESSION_STORE[session_id]
        half    = MAX_HISTORY_TURNS  # Number of messages to compress (oldest half)
        old_turns  = history[:half]
        keep_turns = history[half:]

        # Build a text block from old turns
        old_text = "\n".join(
            f"{'User' if m['sender'] == 'user' else 'Assistant'}: {m['text'][:300]}"
            for m in old_turns
        )
        existing_summary = _SESSION_SUMMARIES.get(session_id, "")

        # Attempt LLM summarization
        try:
            from backend.llm import gemini
            prompt = (
                f"Prior Conversation Summary:\n{existing_summary}\n\n"
                f"New Conversation Turns to Summarize:\n{old_text}\n\n"
                "Please produce a concise factual summary (3-5 sentences) of the topics discussed "
                "so far, combining the prior summary with these new turns. "
                "Focus on: what policy questions were asked and what key answers were given. "
                "Output ONLY the summary text."
            )
            new_summary = gemini.generate_response(
                prompt,
                system_instruction="You are a conversation summarizer for an enterprise compliance assistant.",
                model_override="gemini-2.5-flash"
            )
            _SESSION_SUMMARIES[session_id] = new_summary.strip()
            Logger.info(f"Session [{session_id[:8]}...] history compressed into summary.")
        except Exception as e:
            # Fallback: just concatenate old text as the summary
            Logger.error(f"Session summarization failed: {e}. Using raw text fallback.")
            _SESSION_SUMMARIES[session_id] = (existing_summary + "\n" + old_text).strip()[-2000:]

        _SESSION_STORE[session_id] = keep_turns

    @staticmethod
    def clear_session(session_id: str):
        """Clears stored history and summary for a session."""
        if session_id in _SESSION_STORE:
            del _SESSION_STORE[session_id]
        if session_id in _SESSION_SUMMARIES:
            del _SESSION_SUMMARIES[session_id]
        Logger.info(f"Session [{session_id[:8]}...] cleared.")
