import os
import json
from datetime import datetime
from typing import Optional
from backend.utils.logger import Logger

AUDIT_LOG_FILE = os.path.join(os.path.dirname(__file__), '..', '..', 'audit_log.json')
MAX_LOG_ENTRIES = 2000  # Rotate after 2000 entries to prevent unbounded growth


class AuditLogger:
    """Persistent audit log that writes JSON entries to audit_log.json."""

    @staticmethod
    def _load() -> list:
        if os.path.exists(AUDIT_LOG_FILE):
            try:
                with open(AUDIT_LOG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    @staticmethod
    def _save(entries: list):
        try:
            with open(AUDIT_LOG_FILE, 'w', encoding='utf-8') as f:
                json.dump(entries, f, indent=2, ensure_ascii=False)
        except Exception as e:
            Logger.error(f"AuditLogger failed to write: {e}")

    @staticmethod
    def log(
        action: str,
        user: Optional[str] = "system",
        role: Optional[str] = None,
        details: Optional[str] = None,
        severity: str = "info",       # info | warning | high
        session_id: Optional[str] = None
    ):
        """
        Append an audit log entry.

        Parameters
        ----------
        action   : Short action label e.g. 'login', 'query', 'upload', 'escalate', 'delete_user'
        user     : Username (or 'system' / 'anonymous')
        role     : User's role at time of action
        details  : Human-readable description of what happened
        severity : 'info' | 'warning' | 'high'
        session_id: Optional chat session ID for traceability
        """
        entries = AuditLogger._load()

        entry = {
            "id":         len(entries) + 1,
            "timestamp":  datetime.utcnow().isoformat() + "Z",
            "action":     action,
            "user":       user or "anonymous",
            "role":       role or "unknown",
            "severity":   severity,
            "details":    details or "",
            "session_id": session_id or ""
        }

        entries.append(entry)

        # Rotate: keep only most recent MAX_LOG_ENTRIES
        if len(entries) > MAX_LOG_ENTRIES:
            entries = entries[-MAX_LOG_ENTRIES:]

        AuditLogger._save(entries)
        Logger.info(f"[AUDIT] {severity.upper()} | {user} | {action} | {details}")

    @staticmethod
    def get_entries(limit: int = 200, severity_filter: Optional[str] = None) -> list:
        """Returns the most recent `limit` log entries, optionally filtered by severity."""
        entries = AuditLogger._load()
        if severity_filter:
            entries = [e for e in entries if e.get("severity") == severity_filter]
        return list(reversed(entries[-limit:]))  # Most recent first

    @staticmethod
    def clear():
        """Clears the entire audit log (admin-only action)."""
        AuditLogger._save([])
        Logger.info("Audit log cleared by admin.")
